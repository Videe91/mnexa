from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re

from collections import defaultdict

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


from experiments.seed_growth_017 import (
    build_memory_bundle,
    build_memory_snapshot,
    evaluate_snapshot,
)

from experiments.seed_growth_019 import (
    evaluation_family,
)

from experiments.seed_growth_020 import (
    canonical_candidate_key,
    select_conjunctive_candidates,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


RRF_K = 60
RETRIEVAL_TOP_K = 3


TOKEN_RE = re.compile(
    r"[A-Za-z0-9_-]+"
)

EVIDENCE_RE = re.compile(
    r"^\[(E\d+)\b[^\]]*\]\s*(.*)$"
)

HANDLE_RE = re.compile(
    r'^\[(P\d+)\]\s+HANDLE="(.*?)"\s*->\s*(E\d+)\s*$'
)

UNRESOLVED_RE = re.compile(
    r"^\[(G\d+)\]\s+UNRESOLVED\s+->\s*(E\d+)\s*$"
)


def rendered_memory_from_bundle(
    bundle,
):
    """
    Locate the final compact rendered memory without depending on
    a historical bundle key name.

    This experiment intentionally consumes the existing Seed 015+
    compact representation rather than creating a new knowledge object.
    """

    candidates = []

    def walk(
        value,
    ):
        if isinstance(
            value,
            str,
        ):
            if (
                "COMPACT SEMANTIC MEMORY"
                in value
            ):
                candidates.append(
                    value
                )

            return

        if isinstance(
            value,
            dict,
        ):
            for child in value.values():
                walk(
                    child
                )

            return

        if isinstance(
            value,
            (
                list,
                tuple,
            ),
        ):
            for child in value:
                walk(
                    child
                )

    walk(
        bundle
    )

    unique = list(
        dict.fromkeys(
            candidates
        )
    )

    if not unique:
        raise ValueError(
            "No COMPACT SEMANTIC MEMORY "
            "rendering found in bundle."
        )

    # Prefer the richest rendering if the bundle retains more than
    # one equivalent/intermediate representation.
    return max(
        unique,
        key=len,
    )


def retrieval_index_from_compact_memory(
    *,
    compact_memory,
    entities,
):
    """
    Build retrieval-only text.

    Normalized propositions contribute HANDLE + META.

    If a valid grounded support survived only as an unresolved fallback,
    index its exact authoritative evidence text. We do not manufacture a
    replacement proposition.

    The resulting text is NEVER shown to the transfer reasoner as the
    authoritative semantic payload.
    """

    lines = [
        line.rstrip()

        for line
        in compact_memory.splitlines()
    ]

    evidence = {}

    for line in lines:

        stripped = (
            line.strip()
        )

        match = (
            EVIDENCE_RE.match(
                stripped
            )
        )

        if not match:
            continue

        evidence_id = (
            match.group(1)
        )

        evidence_text = (
            match.group(2)
            .strip()
        )

        evidence[
            evidence_id
        ] = (
            evidence_text
        )

    retrieval_lines = [
        "RETRIEVAL HANDLE INDEX",
        "",
        "ADDRESS:",
    ]

    retrieval_lines.extend(
        sorted(
            {
                entity

                for entity
                in entities

                if isinstance(
                    entity,
                    str,
                )
            }
        )
    )

    retrieval_lines.extend(
        [
            "",
            "HANDLES:",
        ]
    )

    in_references = False

    for index, line in enumerate(
        lines
    ):

        stripped = (
            line.strip()
        )

        if stripped == "REFERENCES:":
            in_references = True
            continue

        if not in_references:
            continue

        handle_match = (
            HANDLE_RE.match(
                stripped
            )
        )

        if handle_match:

            proposition_id = (
                handle_match.group(1)
            )

            handle = (
                handle_match.group(2)
            )

            evidence_id = (
                handle_match.group(3)
            )

            retrieval_lines.append(
                (
                    f'[{proposition_id}] '
                    f'HANDLE="{handle}" '
                    f"-> {evidence_id}"
                )
            )

            # Structural META immediately following this P-record
            # belongs to the retrieval handle.
            next_index = (
                index
                +
                1
            )

            while (
                next_index
                <
                len(lines)
            ):

                next_line = (
                    lines[
                        next_index
                    ].strip()
                )

                if not next_line:
                    next_index += 1
                    continue

                if next_line.startswith(
                    "META "
                ):

                    retrieval_lines.append(
                        next_line
                    )

                    next_index += 1
                    continue

                break

            continue

        unresolved_match = (
            UNRESOLVED_RE.match(
                stripped
            )
        )

        if unresolved_match:

            group_id = (
                unresolved_match.group(1)
            )

            evidence_id = (
                unresolved_match.group(2)
            )

            retrieval_lines.append(
                (
                    f"[{group_id}] "
                    f"UNRESOLVED -> "
                    f"{evidence_id}"
                )
            )

            support = (
                evidence.get(
                    evidence_id
                )
            )

            if support:

                retrieval_lines.append(
                    (
                        "UNRESOLVED_GROUNDED_SUPPORT="
                        +
                        json.dumps(
                            support,
                            ensure_ascii=False,
                        )
                    )
                )

    return (
        "\n".join(
            retrieval_lines
        )
        .strip()
    )


def _tokens(
    text,
):
    return [
        token.lower()

        for token
        in TOKEN_RE.findall(
            text
        )
    ]


def _lexical_score(
    query,
    document,
):
    """
    Small deterministic lexical channel.

    Cosine over bag-of-word term-frequency vectors.
    """

    query_tokens = (
        _tokens(
            query
        )
    )

    document_tokens = (
        _tokens(
            document
        )
    )

    if (
        not query_tokens
        or
        not document_tokens
    ):
        return 0.0

    query_counts = defaultdict(
        int
    )

    document_counts = defaultdict(
        int
    )

    for token in query_tokens:
        query_counts[
            token
        ] += 1

    for token in document_tokens:
        document_counts[
            token
        ] += 1

    dot = sum(
        count
        *
        document_counts.get(
            token,
            0,
        )

        for token, count
        in query_counts.items()
    )

    q_norm = math.sqrt(
        sum(
            value
            *
            value

            for value
            in query_counts.values()
        )
    )

    d_norm = math.sqrt(
        sum(
            value
            *
            value

            for value
            in document_counts.values()
        )
    )

    if (
        q_norm == 0.0
        or
        d_norm == 0.0
    ):
        return 0.0

    return (
        dot
        /
        (
            q_norm
            *
            d_norm
        )
    )


def _flatten_vector(
    vector,
):
    if hasattr(
        vector,
        "tolist",
    ):
        vector = (
            vector.tolist()
        )

    if (
        isinstance(
            vector,
            (
                list,
                tuple,
            ),
        )
        and
        len(vector) == 1
        and
        isinstance(
            vector[0],
            (
                list,
                tuple,
            ),
        )
    ):
        vector = (
            vector[0]
        )

    return [
        float(value)

        for value
        in vector
    ]


def _embed(
    embedder,
    text,
):
    if hasattr(
        embedder,
        "embed",
    ):
        try:
            return (
                _flatten_vector(
                    embedder.embed(
                        text
                    )
                )
            )
        except TypeError:
            return (
                _flatten_vector(
                    embedder.embed(
                        [text]
                    )
                )
            )

    if hasattr(
        embedder,
        "encode",
    ):
        return (
            _flatten_vector(
                embedder.encode(
                    text
                )
            )
        )

    raise TypeError(
        "Embedder exposes neither "
        "embed() nor encode()."
    )


def _cosine(
    left,
    right,
):
    if (
        not left
        or
        not right
    ):
        return 0.0

    if (
        len(left)
        !=
        len(right)
    ):
        raise ValueError(
            "Embedding dimensions differ."
        )

    dot = sum(
        a * b

        for a, b
        in zip(
            left,
            right,
        )
    )

    left_norm = math.sqrt(
        sum(
            value * value

            for value
            in left
        )
    )

    right_norm = math.sqrt(
        sum(
            value * value

            for value
            in right
        )
    )

    if (
        left_norm == 0.0
        or
        right_norm == 0.0
    ):
        return 0.0

    return (
        dot
        /
        (
            left_norm
            *
            right_norm
        )
    )


def _entity_score(
    query_entities,
    memory_entities,
):
    query = set(
        query_entities
    )

    memory = set(
        memory_entities
    )

    return float(
        len(
            query
            &
            memory
        )
    )


def _rank_positions(
    *,
    candidate_family_ids,
    scores,
):
    """
    Deterministic ranking with canonical family order as the final
    tie-breaker.
    """

    canonical_index = {
        family_id: index

        for index, family_id
        in enumerate(
            candidate_family_ids
        )
    }

    ordered = sorted(
        candidate_family_ids,

        key=lambda family_id: (
            -float(
                scores[
                    family_id
                ]
            ),
            canonical_index[
                family_id
            ],
        ),
    )

    return {
        family_id: rank

        for rank, family_id
        in enumerate(
            ordered,
            start=1,
        )
    }


def rank_candidate_ids(
    *,
    query_text,
    query_entities,
    candidate_family_ids,
    documents,
    entities_by_family,
    embedder,
    top_k=RETRIEVAL_TOP_K,
    rrf_k=RRF_K,
):
    """
    Shared three-channel retrieval ranking.

    A and B call this exact same function.

    The only input that changes between conditions is `documents`:

    A -> full compact semantic memory
    B -> retrieval-handle index
    """

    query_vector = (
        _embed(
            embedder,
            query_text,
        )
    )

    semantic_scores = {}
    lexical_scores = {}
    entity_scores = {}

    for family_id in (
        candidate_family_ids
    ):

        document = (
            documents[
                family_id
            ]
        )

        document_vector = (
            _embed(
                embedder,
                document,
            )
        )

        semantic_scores[
            family_id
        ] = (
            _cosine(
                query_vector,
                document_vector,
            )
        )

        lexical_scores[
            family_id
        ] = (
            _lexical_score(
                query_text,
                document,
            )
        )

        entity_scores[
            family_id
        ] = (
            _entity_score(
                query_entities,
                entities_by_family[
                    family_id
                ],
            )
        )

    channel_scores = {
        "semantic": (
            semantic_scores
        ),
        "lexical": (
            lexical_scores
        ),
        "entity": (
            entity_scores
        ),
    }

    channel_ranks = {
        channel: (
            _rank_positions(
                candidate_family_ids=(
                    candidate_family_ids
                ),
                scores=scores,
            )
        )

        for channel, scores
        in channel_scores.items()
    }

    rrf_scores = {
        family_id: 0.0

        for family_id
        in candidate_family_ids
    }

    for ranks in (
        channel_ranks.values()
    ):

        for (
            family_id,
            rank,
        ) in ranks.items():

            rrf_scores[
                family_id
            ] += (
                1.0
                /
                (
                    rrf_k
                    +
                    rank
                )
            )

    canonical_index = {
        family_id: index

        for index, family_id
        in enumerate(
            candidate_family_ids
        )
    }

    fused = sorted(
        candidate_family_ids,

        key=lambda family_id: (
            -rrf_scores[
                family_id
            ],
            canonical_index[
                family_id
            ],
        ),
    )

    selected = (
        fused[
            :top_k
        ]
    )

    return {
        "selected_family_ids": (
            selected
        ),

        "rrf_scores": (
            rrf_scores
        ),

        "channel_scores": (
            channel_scores
        ),

        "channel_ranks": (
            channel_ranks
        ),

        "top_k": (
            top_k
        ),

        "rrf_k": (
            rrf_k
        ),
    }


def canonical_selection_key(
    *,
    selected_family_ids,
    canonical_family_ids,
):
    selected = set(
        selected_family_ids
    )

    return tuple(
        family_id

        for family_id
        in canonical_family_ids

        if family_id
        in selected
    )


def requires_second_evaluation(
    *,
    full_selected_ids,
    handle_selected_ids,
    canonical_family_ids,
):
    return (
        canonical_selection_key(
            selected_family_ids=(
                full_selected_ids
            ),
            canonical_family_ids=(
                canonical_family_ids
            ),
        )
        !=
        canonical_selection_key(
            selected_family_ids=(
                handle_selected_ids
            ),
            canonical_family_ids=(
                canonical_family_ids
            ),
        )
    )


def posthoc_selection_metrics(
    *,
    target_family_id,
    selected_family_ids,
):
    selected = (
        target_family_id
        in selected_family_ids
    )

    count = len(
        selected_family_ids
    )

    return {
        "target_selected": (
            selected
        ),

        "selection_recall": (
            1.0
            if selected
            else 0.0
        ),

        "selection_precision": (
            (
                1.0
                /
                count
            )
            if (
                selected
                and
                count
            )
            else 0.0
        ),

        "selected_count": (
            count
        ),

        "selected_distractor_count": (
            count
            -
            int(
                selected
            )
        ),
    }


def classify_effect(
    *,
    full_pass,
    handle_pass,
    full_visible,
    handle_visible,
):
    return {
        "task_rescue": (
            (not full_pass)
            and
            handle_pass
        ),

        "task_harm": (
            full_pass
            and
            (not handle_pass)
        ),

        "visibility_rescue": (
            (not full_visible)
            and
            handle_visible
        ),

        "visibility_harm": (
            full_visible
            and
            (not handle_visible)
        ),
    }


def _word_count(
    text,
):
    return len(
        text.split()
    )


def _mean(
    values,
):
    values = list(
        values
    )

    if not values:
        return 0.0

    return (
        sum(
            values
        )
        /
        len(
            values
        )
    )


def _learned_record(
    snapshot,
    family_id,
):
    for record in snapshot[
        "learned"
    ]:

        if (
            record[
                "family_id"
            ]
            ==
            family_id
        ):
            return record

    raise KeyError(
        family_id
    )


def _count(
    rows,
    condition,
    metric,
):
    return sum(
        int(
            row[
                condition
            ][
                metric
            ]
        )

        for row
        in rows
    )


def _sum(
    rows,
    condition,
    metric,
):
    return sum(
        float(
            row[
                condition
            ][
                metric
            ]
        )

        for row
        in rows
    )


def _aggregate_cluster_metrics(
    rows,
    *,
    condition,
    ranking_key,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "task_passes": 0,
            "target_visible_families": 0,
            "wrong_family_clause_occurrences": 0,
            "families_with_wrong_memory": 0,
            "selection_target_present": 0,
            "selection_precision_sum": 0.0,
            "selection_recall_sum": 0.0,
        }
    )

    for row in rows:

        cluster = (
            row[
                "interference_cluster"
            ]
        )

        result = (
            row[
                condition
            ]
        )

        ranking = (
            row[
                ranking_key
            ]
        )

        bucket = (
            grouped[
                cluster
            ]
        )

        bucket[
            "families"
        ] += 1

        bucket[
            "task_passes"
        ] += int(
            result[
                "semantic_task_pass"
            ]
        )

        bucket[
            "target_visible_families"
        ] += int(
            result[
                "target_clause_visible"
            ]
        )

        wrong = int(
            result[
                "wrong_family_clause_count"
            ]
        )

        bucket[
            "wrong_family_clause_occurrences"
        ] += wrong

        bucket[
            "families_with_wrong_memory"
        ] += int(
            wrong > 0
        )

        selection = (
            ranking[
                "selection_metrics"
            ]
        )

        bucket[
            "selection_target_present"
        ] += int(
            selection[
                "target_selected"
            ]
        )

        bucket[
            "selection_precision_sum"
        ] += float(
            selection[
                "selection_precision"
            ]
        )

        bucket[
            "selection_recall_sum"
        ] += float(
            selection[
                "selection_recall"
            ]
        )

    output = {}

    for (
        cluster,
        bucket,
    ) in sorted(
        grouped.items()
    ):

        families = (
            bucket[
                "families"
            ]
        )

        output[
            cluster
        ] = {
            "families": (
                families
            ),

            "task_passes": (
                bucket[
                    "task_passes"
                ]
            ),

            "task_pass_rate": (
                bucket[
                    "task_passes"
                ]
                /
                families
            ),

            "target_visible_families": (
                bucket[
                    "target_visible_families"
                ]
            ),

            "families_with_wrong_memory": (
                bucket[
                    "families_with_wrong_memory"
                ]
            ),

            "wrong_family_clause_occurrences": (
                bucket[
                    "wrong_family_clause_occurrences"
                ]
            ),

            "selection_target_present": (
                bucket[
                    "selection_target_present"
                ]
            ),

            "mean_selection_precision": (
                bucket[
                    "selection_precision_sum"
                ]
                /
                families
            ),

            "mean_selection_recall": (
                bucket[
                    "selection_recall_sum"
                ]
                /
                families
            ),
        }

    return output


def run_experiment_021(
    *,
    tasks_path,
    results_dir,
    model,
    embedder,
    meter,
):
    tasks_path = Path(
        tasks_path
    )

    payload = json.loads(
        tasks_path.read_text()
    )

    families = (
        payload[
            "families"
        ]
    )

    family_by_id = {
        family[
            "id"
        ]: family

        for family
        in families
    }

    canonical_family_ids = [
        family[
            "id"
        ]

        for family
        in families
    ]

    taskset_sha256 = (
        hashlib
        .sha256(
            tasks_path.read_bytes()
        )
        .hexdigest()
    )

    run_id = (
        datetime
        .now(
            timezone.utc
        )
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    run_dir = (
        Path(
            results_dir
        )
        /
        run_id
    )

    snapshot_dir = (
        run_dir
        /
        "state"
        /
        "selected_snapshots"
    )

    eval_dir = (
        run_dir
        /
        "state"
        /
        "evaluations"
    )

    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    eval_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ================================================================
    # LEARN EACH MEMORY ONCE
    # ================================================================

    bundles = {
        family[
            "id"
        ]: (
            build_memory_bundle(
                family=family,
                model=model,
            )
        )

        for family
        in families
    }

    full_documents = {}

    handle_documents = {}

    entities_by_family = {
        family[
            "id"
        ]: list(
            family[
                "entities"
            ]
        )

        for family
        in families
    }

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        compact = (
            rendered_memory_from_bundle(
                bundles[
                    family_id
                ]
            )
        )

        full_documents[
            family_id
        ] = (
            compact
        )

        handle_documents[
            family_id
        ] = (
            retrieval_index_from_compact_memory(
                compact_memory=compact,
                entities=(
                    family[
                        "entities"
                    ]
                ),
            )
        )

    # ================================================================
    # SHARED AUTHORITATIVE-PAYLOAD SNAPSHOT CACHE
    #
    # Ranking documents are NEVER stored here.
    #
    # Every snapshot is constructed from the unchanged original
    # memory bundle.
    # ================================================================

    snapshot_cache = {}

    def snapshot_for(
        selected_family_ids,
    ):
        key = (
            canonical_selection_key(
                selected_family_ids=(
                    selected_family_ids
                ),
                canonical_family_ids=(
                    canonical_family_ids
                ),
            )
        )

        if not key:
            raise RuntimeError(
                "Retrieval may not produce an empty "
                "presentation set."
            )

        if key in snapshot_cache:
            return (
                snapshot_cache[
                    key
                ],
                key,
            )

        digest = (
            hashlib
            .sha256(
                "|".join(
                    key
                )
                .encode(
                    "utf-8"
                )
            )
            .hexdigest()[:16]
        )

        selected_families = [
            family_by_id[
                family_id
            ]

            for family_id
            in key
        ]

        snapshot = (
            build_memory_snapshot(
                db_path=(
                    snapshot_dir
                    /
                    (
                        "selected_"
                        +
                        digest
                        +
                        ".sqlite3"
                    )
                ),

                families=(
                    selected_families
                ),

                bundles=(
                    bundles
                ),

                embedder=embedder,
                meter=meter,
            )
        )

        snapshot_cache[
            key
        ] = snapshot

        return (
            snapshot,
            key,
        )

    rows = []

    clause_by_family = {
        family[
            "id"
        ]: (
            family[
                "semantic_clause"
            ]
        )

        for family
        in families
    }

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        # ============================================================
        # ROUTING — IDENTICAL A/B
        # ============================================================

        routing = (
            select_conjunctive_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),
                families=(
                    families
                ),
            )
        )

        candidate_ids = (
            routing[
                "candidate_family_ids"
            ]
        )

        if (
            routing[
                "candidate_count"
            ]
            != 5
        ):
            raise RuntimeError(
                "Seed 021 frozen geometry violated: "
                f"{family_id} routed to "
                f"{routing['candidate_count']} candidates."
            )

        query_text = (
            family[
                "query_prompt"
            ]
            +
            "\n"
            +
            " ".join(
                family[
                    "query_entities"
                ]
            )
        )

        # ============================================================
        # CONDITION A
        # Full compact-memory retrieval representation.
        # ============================================================

        full_rank = (
            rank_candidate_ids(
                query_text=(
                    query_text
                ),

                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),

                candidate_family_ids=(
                    candidate_ids
                ),

                documents=(
                    full_documents
                ),

                entities_by_family=(
                    entities_by_family
                ),

                embedder=embedder,

                top_k=(
                    RETRIEVAL_TOP_K
                ),

                rrf_k=(
                    RRF_K
                ),
            )
        )

        # ============================================================
        # CONDITION B
        # Same ranking implementation, handles instead of full memory.
        # ============================================================

        handle_rank = (
            rank_candidate_ids(
                query_text=(
                    query_text
                ),

                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),

                candidate_family_ids=(
                    candidate_ids
                ),

                documents=(
                    handle_documents
                ),

                entities_by_family=(
                    entities_by_family
                ),

                embedder=embedder,

                top_k=(
                    RETRIEVAL_TOP_K
                ),

                rrf_k=(
                    RRF_K
                ),
            )
        )

        full_selection_metrics = (
            posthoc_selection_metrics(
                target_family_id=(
                    family_id
                ),

                selected_family_ids=(
                    full_rank[
                        "selected_family_ids"
                    ]
                ),
            )
        )

        handle_selection_metrics = (
            posthoc_selection_metrics(
                target_family_id=(
                    family_id
                ),

                selected_family_ids=(
                    handle_rank[
                        "selected_family_ids"
                    ]
                ),
            )
        )

        full_rank[
            "selection_metrics"
        ] = (
            full_selection_metrics
        )

        handle_rank[
            "selection_metrics"
        ] = (
            handle_selection_metrics
        )

        (
            full_snapshot,
            full_key,
        ) = (
            snapshot_for(
                full_rank[
                    "selected_family_ids"
                ]
            )
        )

        (
            handle_snapshot,
            handle_key,
        ) = (
            snapshot_for(
                handle_rank[
                    "selected_family_ids"
                ]
            )
        )

        eval_family = (
            evaluation_family(
                family
            )
        )

        full_eval = (
            evaluate_snapshot(
                snapshot_path=Path(
                    full_snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    eval_dir
                    /
                    (
                        "full_"
                        +
                        family_id
                        +
                        ".sqlite3"
                    )
                ),

                family=(
                    eval_family
                ),

                model=model,
                embedder=embedder,
                meter=meter,

                clause_by_family=(
                    clause_by_family
                ),
            )
        )

        same_selection = (
            full_key
            ==
            handle_key
        )

        if same_selection:

            # Noise-free control.
            handle_eval = (
                copy.deepcopy(
                    full_eval
                )
            )

        else:

            handle_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        handle_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "handle_"
                            +
                            family_id
                            +
                            ".sqlite3"
                        )
                    ),

                    family=(
                        eval_family
                    ),

                    model=model,
                    embedder=embedder,
                    meter=meter,

                    clause_by_family=(
                        clause_by_family
                    ),
                )
            )

        effect = (
            classify_effect(
                full_pass=(
                    full_eval[
                        "semantic_task_pass"
                    ]
                ),

                handle_pass=(
                    handle_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    full_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    handle_eval[
                        "target_clause_visible"
                    ]
                ),
            )
        )

        rows.append(
            {
                "family_id": (
                    family_id
                ),

                "interference_cluster": (
                    family[
                        "interference_cluster"
                    ]
                ),

                "semantic_operator": (
                    family[
                        "semantic_operator"
                    ]
                ),

                "semantic_dimension": (
                    family[
                        "semantic_dimension"
                    ]
                ),

                "query_prompt": (
                    family[
                        "query_prompt"
                    ]
                ),

                "query_entities": (
                    family[
                        "query_entities"
                    ]
                ),

                "routing": (
                    routing
                ),

                "full_memory_ranking": (
                    full_rank
                ),

                "handle_ranking": (
                    handle_rank
                ),

                "full_memory_index_words": (
                    sum(
                        _word_count(
                            full_documents[
                                candidate_id
                            ]
                        )

                        for candidate_id
                        in candidate_ids
                    )
                ),

                "handle_index_words": (
                    sum(
                        _word_count(
                            handle_documents[
                                candidate_id
                            ]
                        )

                        for candidate_id
                        in candidate_ids
                    )
                ),

                "full": (
                    full_eval
                ),

                "handle": (
                    handle_eval
                ),

                "paired": {
                    **effect,

                    "selected_sets_equal": (
                        same_selection
                    ),

                    "evaluation_reused": (
                        same_selection
                    ),

                    "selection_target_delta": (
                        int(
                            handle_selection_metrics[
                                "target_selected"
                            ]
                        )
                        -
                        int(
                            full_selection_metrics[
                                "target_selected"
                            ]
                        )
                    ),

                    "task_delta": (
                        int(
                            handle_eval[
                                "semantic_task_pass"
                            ]
                        )
                        -
                        int(
                            full_eval[
                                "semantic_task_pass"
                            ]
                        )
                    ),

                    "visibility_delta": (
                        int(
                            handle_eval[
                                "target_clause_visible"
                            ]
                        )
                        -
                        int(
                            full_eval[
                                "target_clause_visible"
                            ]
                        )
                    ),

                    "wrong_family_clause_delta": (
                        handle_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        full_eval[
                            "wrong_family_clause_count"
                        ]
                    ),
                },
            }
        )

    # ================================================================
    # CONTROLS
    # ================================================================

    target_lessons_equal = True
    target_sources_equal = True

    for row in rows:

        family_id = (
            row[
                "family_id"
            ]
        )

        full_selected = (
            row[
                "full_memory_ranking"
            ][
                "selected_family_ids"
            ]
        )

        handle_selected = (
            row[
                "handle_ranking"
            ][
                "selected_family_ids"
            ]
        )

        # Only compare target record hashes where the target is present
        # in both selected conditions.
        if (
            family_id
            not in full_selected
            or
            family_id
            not in handle_selected
        ):
            continue

        full_snapshot, _ = (
            snapshot_for(
                full_selected
            )
        )

        handle_snapshot, _ = (
            snapshot_for(
                handle_selected
            )
        )

        full_record = (
            _learned_record(
                full_snapshot,
                family_id,
            )
        )

        handle_record = (
            _learned_record(
                handle_snapshot,
                family_id,
            )
        )

        if (
            full_record[
                "lesson_sha256"
            ]
            !=
            handle_record[
                "lesson_sha256"
            ]
        ):
            target_lessons_equal = False

        if (
            full_record[
                "source_evidence_sha256"
            ]
            !=
            handle_record[
                "source_evidence_sha256"
            ]
        ):
            target_sources_equal = False

    family_count = len(
        rows
    )

    full_task_passes = (
        _count(
            rows,
            "full",
            "semantic_task_pass",
        )
    )

    handle_task_passes = (
        _count(
            rows,
            "handle",
            "semantic_task_pass",
        )
    )

    full_selection_recall = (
        _mean(
            row[
                "full_memory_ranking"
            ][
                "selection_metrics"
            ][
                "selection_recall"
            ]

            for row
            in rows
        )
    )

    handle_selection_recall = (
        _mean(
            row[
                "handle_ranking"
            ][
                "selection_metrics"
            ][
                "selection_recall"
            ]

            for row
            in rows
        )
    )

    full_selection_precision = (
        _mean(
            row[
                "full_memory_ranking"
            ][
                "selection_metrics"
            ][
                "selection_precision"
            ]

            for row
            in rows
        )
    )

    handle_selection_precision = (
        _mean(
            row[
                "handle_ranking"
            ][
                "selection_metrics"
            ][
                "selection_precision"
            ]

            for row
            in rows
        )
    )

    equal_selection_pairs = sum(
        int(
            row[
                "paired"
            ][
                "selected_sets_equal"
            ]
        )

        for row
        in rows
    )

    differing_selection_pairs = (
        family_count
        -
        equal_selection_pairs
    )

    report = {
        "experiment": (
            "seed-growth-021"
        ),

        "classification": (
            "exploratory-fresh-retrieval-"
            "handle-separation-ablation"
        ),

        "run_id": (
            run_id
        ),

        "taskset_sha256": (
            taskset_sha256
        ),

        "model": getattr(
            model,
            "name",
            type(model).__name__,
        ),

        "embedder": getattr(
            embedder,
            "name",
            type(embedder).__name__,
        ),

        "meter": getattr(
            meter,
            "name",
            type(meter).__name__,
        ),

        "task_count": (
            family_count
        ),

        "pool_size": (
            len(
                families
            )
        ),

        "candidate_neighborhood_size": 5,

        "retrieval_top_k": (
            RETRIEVAL_TOP_K
        ),

        "rrf_k": (
            RRF_K
        ),

        "conditions": {
            "A": (
                "conjunctive_routed_candidates_"
                "ranked_by_full_compact_memory"
            ),

            "B": (
                "same_candidates_same_ranker_"
                "ranked_by_retrieval_handle_index"
            ),
        },

        # ------------------------------------------------------------
        # SELECTION STAGE
        # ------------------------------------------------------------

        "full_selection_target_families": sum(
            int(
                row[
                    "full_memory_ranking"
                ][
                    "selection_metrics"
                ][
                    "target_selected"
                ]
            )

            for row
            in rows
        ),

        "handle_selection_target_families": sum(
            int(
                row[
                    "handle_ranking"
                ][
                    "selection_metrics"
                ][
                    "target_selected"
                ]
            )

            for row
            in rows
        ),

        "mean_full_selection_precision": (
            full_selection_precision
        ),

        "mean_handle_selection_precision": (
            handle_selection_precision
        ),

        "mean_full_selection_recall": (
            full_selection_recall
        ),

        "mean_handle_selection_recall": (
            handle_selection_recall
        ),

        # ------------------------------------------------------------
        # DOWNSTREAM
        # ------------------------------------------------------------

        "full_task_passes": (
            full_task_passes
        ),

        "handle_task_passes": (
            handle_task_passes
        ),

        "full_task_pass_rate": (
            full_task_passes
            /
            family_count
        ),

        "handle_task_pass_rate": (
            handle_task_passes
            /
            family_count
        ),

        "full_target_visible_families": (
            _count(
                rows,
                "full",
                "target_clause_visible",
            )
        ),

        "handle_target_visible_families": (
            _count(
                rows,
                "handle",
                "target_clause_visible",
            )
        ),

        "full_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "full"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "handle_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "handle"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "full_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "full",
                "wrong_family_clause_count",
            )
        ),

        "handle_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "handle",
                "wrong_family_clause_count",
            )
        ),

        "full_wrong_rule_contamination_families": (
            _count(
                rows,
                "full",
                "wrong_rule_contamination",
            )
        ),

        "handle_wrong_rule_contamination_families": (
            _count(
                rows,
                "handle",
                "wrong_rule_contamination",
            )
        ),

        "mean_full_retrieval_precision": (
            _mean(
                row[
                    "full"
                ][
                    "retrieval_precision"
                ]

                for row
                in rows
            )
        ),

        "mean_handle_retrieval_precision": (
            _mean(
                row[
                    "handle"
                ][
                    "retrieval_precision"
                ]

                for row
                in rows
            )
        ),

        "mean_full_retrieval_recall": (
            _mean(
                row[
                    "full"
                ][
                    "retrieval_recall"
                ]

                for row
                in rows
            )
        ),

        "mean_handle_retrieval_recall": (
            _mean(
                row[
                    "handle"
                ][
                    "retrieval_recall"
                ]

                for row
                in rows
            )
        ),

        # ------------------------------------------------------------
        # PAIRED EFFECT
        # ------------------------------------------------------------

        "selection_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "selection_target_delta"
                ]
                > 0
            )

            for row
            in rows
        ),

        "selection_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "selection_target_delta"
                ]
                < 0
            )

            for row
            in rows
        ),

        "task_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "task_rescue"
                ]
            )

            for row
            in rows
        ),

        "task_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "task_harm"
                ]
            )

            for row
            in rows
        ),

        "visibility_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "visibility_rescue"
                ]
            )

            for row
            in rows
        ),

        "visibility_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "visibility_harm"
                ]
            )

            for row
            in rows
        ),

        # ------------------------------------------------------------
        # INDEX COST
        # ------------------------------------------------------------

        "mean_full_index_words_per_query": (
            _mean(
                row[
                    "full_memory_index_words"
                ]

                for row
                in rows
            )
        ),

        "mean_handle_index_words_per_query": (
            _mean(
                row[
                    "handle_index_words"
                ]

                for row
                in rows
            )
        ),

        "mean_handle_index_word_reduction_fraction": (
            _mean(
                (
                    row[
                        "full_memory_index_words"
                    ]
                    -
                    row[
                        "handle_index_words"
                    ]
                )
                /
                row[
                    "full_memory_index_words"
                ]

                for row
                in rows

                if row[
                    "full_memory_index_words"
                ]
                > 0
            )
        ),

        # ------------------------------------------------------------
        # CLUSTER ANALYSIS
        # ------------------------------------------------------------

        "full_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="full",
                ranking_key=(
                    "full_memory_ranking"
                ),
            )
        ),

        "handle_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="handle",
                ranking_key=(
                    "handle_ranking"
                ),
            )
        ),

        # ------------------------------------------------------------
        # SAME-STATE CONTROL
        # ------------------------------------------------------------

        "equal_selected_set_pairs": (
            equal_selection_pairs
        ),

        "differing_selected_set_pairs": (
            differing_selection_pairs
        ),

        "reused_equal_selected_evaluations": (
            equal_selection_pairs
        ),

        "full_transfer_model_calls": (
            family_count
        ),

        "handle_additional_transfer_model_calls": (
            differing_selection_pairs
        ),

        "total_transfer_model_calls": (
            family_count
            +
            differing_selection_pairs
        ),

        # ------------------------------------------------------------
        # MEMORY SAFETY / CONTROL
        # ------------------------------------------------------------

        "compact_memory_bundles": (
            len(
                bundles
            )
        ),

        "bundles_with_exact_semantic_clause_visible": sum(
            int(
                bundle[
                    "semantic_clause_visible"
                ]
            )

            for bundle
            in bundles.values()
        ),

        "bundle_unsupported_claims_admitted": sum(
            int(
                bundle[
                    "unsupported_claims_admitted"
                ]
            )

            for bundle
            in bundles.values()
        ),

        "all_candidate_routes_equal_between_conditions": True,

        "all_target_lessons_identical_between_conditions": (
            target_lessons_equal
        ),

        "all_target_source_evidence_equal": (
            target_sources_equal
        ),

        "all_transfer_queries_equal": True,

        "all_presented_memory_representation_equal": True,

        "all_context_budget_configuration_equal": True,

        "all_reasoners_equal": True,

        "ranking_algorithm_equal_between_conditions": True,

        "only_ranking_document_representation_differs": True,

        "handle_ranker_model_calls": 0,

        "handle_ranker_used_family_id": False,

        "handle_ranker_used_semantic_clause": False,

        "handle_ranker_used_semantic_grader": False,

        "all_equal_selected_pairs_reused_evaluation": all(
            (
                not row[
                    "paired"
                ][
                    "selected_sets_equal"
                ]
            )
            or
            row[
                "paired"
            ][
                "evaluation_reused"
            ]

            for row
            in rows
        ),

        "families": (
            rows
        ),
    }

    output = (
        run_dir
        /
        "result.json"
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
        )
        +
        "\n"
    )

    return (
        report,
        output,
    )


def main():
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_021.json"
        ),
    )

    parser.add_argument(
        "--results",
        default=(
            "experiments/"
            "results"
        ),
    )

    args = (
        parser.parse_args()
    )

    model_name = (
        os.environ.get(
            "MNEXA_MODEL"
        )
    )

    if not model_name:
        raise SystemExit(
            "Set MNEXA_MODEL."
        )

    model = (
        OpenAIResponsesModel(
            model_name
        )
    )

    embedder = (
        SentenceTransformerEmbedder(
            os.environ.get(
                "MNEXA_EMBED_MODEL",
                (
                    "sentence-transformers/"
                    "all-MiniLM-L6-v2"
                ),
            )
        )
    )

    report, output = (
        run_experiment_021(
            tasks_path=Path(
                args.tasks
            ),
            results_dir=Path(
                args.results
            ),
            model=model,
            embedder=embedder,
            meter=WordMeter(),
        )
    )

    keys = (
        "experiment",
        "taskset_sha256",

        "candidate_neighborhood_size",
        "retrieval_top_k",

        "full_selection_target_families",
        "handle_selection_target_families",

        "mean_full_selection_precision",
        "mean_handle_selection_precision",

        "mean_full_selection_recall",
        "mean_handle_selection_recall",

        "full_task_passes",
        "handle_task_passes",

        "full_target_visible_families",
        "handle_target_visible_families",

        "full_families_with_wrong_memory_presented",
        "handle_families_with_wrong_memory_presented",

        "full_wrong_family_clause_occurrences",
        "handle_wrong_family_clause_occurrences",

        "full_wrong_rule_contamination_families",
        "handle_wrong_rule_contamination_families",

        "mean_full_retrieval_precision",
        "mean_handle_retrieval_precision",

        "mean_full_retrieval_recall",
        "mean_handle_retrieval_recall",

        "selection_rescue_families",
        "selection_harm_families",

        "task_rescue_families",
        "task_harm_families",

        "visibility_rescue_families",
        "visibility_harm_families",

        "mean_full_index_words_per_query",
        "mean_handle_index_words_per_query",
        "mean_handle_index_word_reduction_fraction",

        "full_cluster_metrics",
        "handle_cluster_metrics",

        "equal_selected_set_pairs",
        "differing_selected_set_pairs",
        "reused_equal_selected_evaluations",

        "total_transfer_model_calls",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "all_candidate_routes_equal_between_conditions",
        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",
        "all_transfer_queries_equal",
        "all_presented_memory_representation_equal",
        "all_context_budget_configuration_equal",
        "all_reasoners_equal",
        "ranking_algorithm_equal_between_conditions",
        "only_ranking_document_representation_differs",

        "handle_ranker_model_calls",
        "all_equal_selected_pairs_reused_evaluation",
    )

    summary = {
        key: report[
            key
        ]

        for key
        in keys
    }

    summary[
        "result"
    ] = str(
        output
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
