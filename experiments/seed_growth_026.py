from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re

from collections import defaultdict
from datetime import datetime, timezone
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
    select_conjunctive_candidates,
)

from experiments.seed_growth_021 import (
    RRF_K,
    _cosine,
    _embed,
    _entity_score,
    _lexical_score,
    classify_effect,
    rank_candidate_ids,
    rendered_memory_from_bundle,
    retrieval_index_from_compact_memory,
)

from experiments.seed_growth_022 import (
    fuse_channel_scores_abstaining,
)

from experiments.seed_growth_023 import (
    classify_assembly_effect,
)

from experiments.seed_growth_025 import (
    pareto_context_boundary,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


TOP_K = 3


_HANDLE_PATTERN = re.compile(
    r"\bHANDLE\s*(?:=|:)?\s*\"",
    re.IGNORECASE,
)

_UNRESOLVED_PATTERN = re.compile(
    r"\bUNRESOLVED_GROUNDED_SUPPORT\b",
    re.IGNORECASE,
)


def _extract_label_payload(
    line,
    label,
):
    """
    Extract either a JSON-quoted payload or the unquoted text
    following a retrieval-index label.
    """

    upper = line.upper()

    index = upper.find(
        label.upper()
    )

    if index < 0:
        raise ValueError(
            f"Missing label {label!r} in line."
        )

    tail = line[
        index
        +
        len(label):
    ].strip()

    tail = tail.lstrip(
        "=: "
    )

    if not tail:
        return ""

    if tail.startswith('"'):

        try:
            value, _ = (
                json.JSONDecoder()
                .raw_decode(
                    tail
                )
            )

            return str(
                value
            )

        except json.JSONDecodeError:
            pass

    if "->" in tail:

        tail = (
            tail.split(
                "->",
                1,
            )[0]
            .strip()
        )

    return tail.strip(
        '" '
    )


def proposition_units_from_retrieval_index(
    retrieval_index,
):
    """
    Convert one Seed-021 retrieval index into independent
    proposition-local retrieval units.

    Address metadata is intentionally not promoted into a
    proposition. Addressing remains handled by Seed 020 and
    the entity retrieval channel.

    HANDLE + following META lines form one unit.

    UNRESOLVED_GROUNDED_SUPPORT remains an exact grounded
    retrieval unit rather than being rewritten into a claim.
    """

    units = []

    current = None

    def flush():
        nonlocal current

        if current:

            units.append(
                "\n".join(
                    current
                )
            )

        current = None

    for raw_line in (
        retrieval_index.splitlines()
    ):

        line = raw_line.strip()

        if not line:
            continue

        if (
            _UNRESOLVED_PATTERN
            .search(
                line
            )
        ):

            flush()

            payload = (
                _extract_label_payload(
                    line,
                    (
                        "UNRESOLVED_GROUNDED_SUPPORT"
                    ),
                )
            )

            current = [
                (
                    "UNRESOLVED_GROUNDED_SUPPORT: "
                    +
                    payload
                )
            ]

            continue

        if (
            _HANDLE_PATTERN
            .search(
                line
            )
        ):

            flush()

            payload = (
                _extract_label_payload(
                    line,
                    "HANDLE",
                )
            )

            current = [
                (
                    "HANDLE: "
                    +
                    payload
                )
            ]

            continue

        if (
            line.upper()
            .startswith(
                "META "
            )
        ):

            if current is not None:

                current.append(
                    line
                )

            continue

    flush()

    if not units:

        raise ValueError(
            "No proposition-local retrieval units "
            "were found in retrieval index."
        )

    return units


def proposition_local_channel_scores(
    *,
    query_text,
    query_entities,
    candidate_family_ids,
    proposition_units_by_family,
    entities_by_family,
    embedder,
):
    """
    Score every proposition unit independently.

    Memory-level semantic score:
        max semantic similarity across that memory's units.

    Memory-level lexical score:
        max lexical similarity across that memory's units.

    Entity scoring remains exactly the existing Seed-021
    entity channel.

    No LLM or router is used.
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

    best_semantic_units = {}
    best_lexical_units = {}

    semantic_comparisons = 0
    lexical_comparisons = 0

    for family_id in (
        candidate_family_ids
    ):

        units = list(
            proposition_units_by_family[
                family_id
            ]
        )

        if not units:

            raise ValueError(
                "Candidate has no proposition-local "
                f"retrieval units: {family_id}"
            )

        semantic_pairs = []

        for unit in units:

            score = (
                _cosine(
                    query_vector,
                    _embed(
                        embedder,
                        unit,
                    ),
                )
            )

            semantic_comparisons += 1

            semantic_pairs.append(
                (
                    float(score),
                    unit,
                )
            )

        lexical_pairs = []

        for unit in units:

            score = (
                _lexical_score(
                    query_text,
                    unit,
                )
            )

            lexical_comparisons += 1

            lexical_pairs.append(
                (
                    float(score),
                    unit,
                )
            )

        best_semantic_score, (
            best_semantic_unit
        ) = max(
            semantic_pairs,
            key=lambda item: item[0],
        )

        best_lexical_score, (
            best_lexical_unit
        ) = max(
            lexical_pairs,
            key=lambda item: item[0],
        )

        semantic_scores[
            family_id
        ] = (
            best_semantic_score
        )

        lexical_scores[
            family_id
        ] = (
            best_lexical_score
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

        best_semantic_units[
            family_id
        ] = (
            best_semantic_unit
        )

        best_lexical_units[
            family_id
        ] = (
            best_lexical_unit
        )

    return {
        "channel_scores": {
            "semantic": (
                semantic_scores
            ),
            "lexical": (
                lexical_scores
            ),
            "entity": (
                entity_scores
            ),
        },

        "best_units": {
            "semantic": (
                best_semantic_units
            ),
            "lexical": (
                best_lexical_units
            ),
        },

        "semantic_comparisons": (
            semantic_comparisons
        ),

        "lexical_comparisons": (
            lexical_comparisons
        ),
    }


def target_rank(
    ordered_family_ids,
    target_family_id,
):
    try:
        return (
            ordered_family_ids.index(
                target_family_id
            )
            +
            1
        )

    except ValueError:
        return None


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


def _mean(
    values,
):
    values = list(
        values
    )

    if not values:
        return 0.0

    return (
        sum(values)
        /
        len(values)
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


def _assembly_count(
    rows,
    condition,
    assembly_class,
):
    return sum(
        int(
            row[
                condition
                +
                "_assembly"
            ][
                "assembly_class"
            ]
            ==
            assembly_class
        )

        for row
        in rows
    )


def _aggregate_cluster_metrics(
    rows,
    *,
    condition,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "target_top3": 0,
            "target_retained": 0,
            "task_passes": 0,
            "target_visible": 0,
            "wrong_memory_families": 0,
            "wrong_clause_occurrences": 0,
        }
    )

    for row in rows:

        cluster = (
            row[
                "interference_cluster"
            ]
        )

        bucket = (
            grouped[
                cluster
            ]
        )

        evaluation = (
            row[
                condition
            ]
        )

        bucket[
            "families"
        ] += 1

        bucket[
            "target_top3"
        ] += int(
            row[
                condition
                +
                "_target_top3"
            ]
        )

        bucket[
            "target_retained"
        ] += int(
            row[
                condition
                +
                "_target_retained"
            ]
        )

        bucket[
            "task_passes"
        ] += int(
            evaluation[
                "semantic_task_pass"
            ]
        )

        bucket[
            "target_visible"
        ] += int(
            evaluation[
                "target_clause_visible"
            ]
        )

        wrong_count = int(
            evaluation[
                "wrong_family_clause_count"
            ]
        )

        bucket[
            "wrong_memory_families"
        ] += int(
            wrong_count > 0
        )

        bucket[
            "wrong_clause_occurrences"
        ] += wrong_count

    output = {}

    for cluster, bucket in sorted(
        grouped.items()
    ):

        count = (
            bucket[
                "families"
            ]
        )

        output[
            cluster
        ] = {
            **bucket,

            "target_top3_rate": (
                bucket[
                    "target_top3"
                ]
                /
                count
            ),

            "target_retention_rate": (
                bucket[
                    "target_retained"
                ]
                /
                count
            ),

            "task_pass_rate": (
                bucket[
                    "task_passes"
                ]
                /
                count
            ),
        }

    return output


def run_experiment_026(
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
        "assembled_snapshots"
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
    # FORM MEMORY ONCE
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

    handle_documents = {}
    proposition_units_by_family = {}

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

        compact_memory = (
            rendered_memory_from_bundle(
                bundles[
                    family_id
                ]
            )
        )

        retrieval_document = (
            retrieval_index_from_compact_memory(
                compact_memory=(
                    compact_memory
                ),

                entities=(
                    family[
                        "entities"
                    ]
                ),
            )
        )

        handle_documents[
            family_id
        ] = (
            retrieval_document
        )

        proposition_units_by_family[
            family_id
        ] = (
            proposition_units_from_retrieval_index(
                retrieval_document
            )
        )

    # ================================================================
    # SNAPSHOT CACHE
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
                "Assembled context may not be empty."
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
                        "assembled_"
                        +
                        digest
                        +
                        ".sqlite3"
                    )
                ),

                families=(
                    selected_families
                ),

                bundles=bundles,

                embedder=embedder,
                meter=meter,
            )
        )

        snapshot_cache[
            key
        ] = (
            snapshot
        )

        return (
            snapshot,
            key,
        )

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

    rows = []

    # ================================================================
    # PAIRED RETRIEVAL + ASSEMBLY + TRANSFER
    # ================================================================

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        routing = (
            select_conjunctive_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),

                families=families,
            )
        )

        candidate_ids = (
            routing[
                "candidate_family_ids"
            ]
        )

        if len(
            candidate_ids
        ) != 5:

            raise RuntimeError(
                "Seed 026 candidate geometry "
                f"violated for {family_id}."
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

        # ------------------------------------------------------------
        # CONDITION A
        # Existing whole retrieval-handle document scoring.
        # ------------------------------------------------------------

        whole_raw = (
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

                top_k=5,

                rrf_k=RRF_K,
            )
        )

        whole_fused = (
            fuse_channel_scores_abstaining(
                candidate_family_ids=(
                    candidate_ids
                ),

                channel_scores=(
                    whole_raw[
                        "channel_scores"
                    ]
                ),

                top_k=5,

                rrf_k=RRF_K,
            )
        )

        whole_order = (
            whole_fused[
                "selected_family_ids"
            ]
        )

        whole_top3 = (
            whole_order[
                :TOP_K
            ]
        )

        whole_boundary = (
            pareto_context_boundary(
                ordered_family_ids=(
                    whole_order
                ),

                channel_ranks=(
                    whole_fused[
                        "channel_ranks"
                    ]
                ),

                active_channels=(
                    whole_fused[
                        "active_channels"
                    ]
                ),

                max_k=TOP_K,
            )
        )

        whole_selected = (
            whole_boundary[
                "selected_family_ids"
            ]
        )

        whole_assembly = (
            classify_assembly_effect(
                target_family_id=(
                    family_id
                ),

                fixed_selected_ids=(
                    whole_top3
                ),

                dynamic_selected_ids=(
                    whole_selected
                ),
            )
        )

        # ------------------------------------------------------------
        # CONDITION B
        # Same handles, scored proposition-by-proposition.
        # ------------------------------------------------------------

        local_raw = (
            proposition_local_channel_scores(
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

                proposition_units_by_family=(
                    proposition_units_by_family
                ),

                entities_by_family=(
                    entities_by_family
                ),

                embedder=embedder,
            )
        )

        local_fused = (
            fuse_channel_scores_abstaining(
                candidate_family_ids=(
                    candidate_ids
                ),

                channel_scores=(
                    local_raw[
                        "channel_scores"
                    ]
                ),

                top_k=5,

                rrf_k=RRF_K,
            )
        )

        local_order = (
            local_fused[
                "selected_family_ids"
            ]
        )

        local_top3 = (
            local_order[
                :TOP_K
            ]
        )

        local_boundary = (
            pareto_context_boundary(
                ordered_family_ids=(
                    local_order
                ),

                channel_ranks=(
                    local_fused[
                        "channel_ranks"
                    ]
                ),

                active_channels=(
                    local_fused[
                        "active_channels"
                    ]
                ),

                max_k=TOP_K,
            )
        )

        local_selected = (
            local_boundary[
                "selected_family_ids"
            ]
        )

        local_assembly = (
            classify_assembly_effect(
                target_family_id=(
                    family_id
                ),

                fixed_selected_ids=(
                    local_top3
                ),

                dynamic_selected_ids=(
                    local_selected
                ),
            )
        )

        whole_target_rank = (
            target_rank(
                whole_order,
                family_id,
            )
        )

        local_target_rank = (
            target_rank(
                local_order,
                family_id,
            )
        )

        whole_target_top3 = (
            family_id
            in
            whole_top3
        )

        local_target_top3 = (
            family_id
            in
            local_top3
        )

        whole_target_retained = (
            family_id
            in
            whole_selected
        )

        local_target_retained = (
            family_id
            in
            local_selected
        )

        (
            whole_snapshot,
            whole_key,
        ) = (
            snapshot_for(
                whole_selected
            )
        )

        (
            local_snapshot,
            local_key,
        ) = (
            snapshot_for(
                local_selected
            )
        )

        eval_family = (
            evaluation_family(
                family
            )
        )

        whole_eval = (
            evaluate_snapshot(
                snapshot_path=Path(
                    whole_snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    eval_dir
                    /
                    (
                        "whole_"
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

        same_context_set = (
            whole_key
            ==
            local_key
        )

        if same_context_set:

            local_eval = (
                copy.deepcopy(
                    whole_eval
                )
            )

        else:

            local_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        local_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "local_"
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

        behavioral_effect = (
            classify_effect(
                full_pass=(
                    whole_eval[
                        "semantic_task_pass"
                    ]
                ),

                handle_pass=(
                    local_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    whole_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    local_eval[
                        "target_clause_visible"
                    ]
                ),
            )
        )

        entity_scores_equal = (
            whole_raw[
                "channel_scores"
            ][
                "entity"
            ]
            ==
            local_raw[
                "channel_scores"
            ][
                "entity"
            ]
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

                "whole": (
                    whole_eval
                ),

                "local": (
                    local_eval
                ),

                "whole_channel_scores": (
                    whole_raw[
                        "channel_scores"
                    ]
                ),

                "local_channel_scores": (
                    local_raw[
                        "channel_scores"
                    ]
                ),

                "local_best_units": (
                    local_raw[
                        "best_units"
                    ]
                ),

                "whole_fusion": (
                    whole_fused
                ),

                "local_fusion": (
                    local_fused
                ),

                "whole_order": (
                    whole_order
                ),

                "local_order": (
                    local_order
                ),

                "whole_target_rank": (
                    whole_target_rank
                ),

                "local_target_rank": (
                    local_target_rank
                ),

                "whole_top3": (
                    whole_top3
                ),

                "local_top3": (
                    local_top3
                ),

                "whole_target_top3": (
                    whole_target_top3
                ),

                "local_target_top3": (
                    local_target_top3
                ),

                "whole_boundary": (
                    whole_boundary
                ),

                "local_boundary": (
                    local_boundary
                ),

                "whole_assembly": (
                    whole_assembly
                ),

                "local_assembly": (
                    local_assembly
                ),

                "whole_target_retained": (
                    whole_target_retained
                ),

                "local_target_retained": (
                    local_target_retained
                ),

                "entity_scores_equal": (
                    entity_scores_equal
                ),

                "local_semantic_comparisons": (
                    local_raw[
                        "semantic_comparisons"
                    ]
                ),

                "local_lexical_comparisons": (
                    local_raw[
                        "lexical_comparisons"
                    ]
                ),

                "paired": {
                    **behavioral_effect,

                    "ranking_rescue": (
                        (
                            not whole_target_top3
                        )
                        and
                        local_target_top3
                    ),

                    "ranking_harm": (
                        whole_target_top3
                        and
                        (
                            not local_target_top3
                        )
                    ),

                    "rank_delta": (
                        whole_target_rank
                        -
                        local_target_rank
                    ),

                    "context_sets_equal": (
                        same_context_set
                    ),

                    "evaluation_reused": (
                        same_context_set
                    ),

                    "task_delta": (
                        int(
                            local_eval[
                                "semantic_task_pass"
                            ]
                        )
                        -
                        int(
                            whole_eval[
                                "semantic_task_pass"
                            ]
                        )
                    ),

                    "visibility_delta": (
                        int(
                            local_eval[
                                "target_clause_visible"
                            ]
                        )
                        -
                        int(
                            whole_eval[
                                "target_clause_visible"
                            ]
                        )
                    ),

                    "wrong_clause_delta": (
                        local_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        whole_eval[
                            "wrong_family_clause_count"
                        ]
                    ),
                },
            }
        )

    task_count = len(
        rows
    )

    equal_context_pairs = sum(
        int(
            row[
                "paired"
            ][
                "context_sets_equal"
            ]
        )

        for row
        in rows
    )

    differing_context_pairs = (
        task_count
        -
        equal_context_pairs
    )

    total_units = sum(
        len(
            proposition_units_by_family[
                family_id
            ]
        )

        for family_id
        in proposition_units_by_family
    )

    report = {
        "experiment": (
            "seed-growth-026"
        ),

        "classification": (
            "exploratory-fresh-proposition-local-"
            "retrieval-ablation"
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
            task_count
        ),

        "pool_size": (
            len(
                families
            )
        ),

        "candidate_neighborhood_size": 5,

        "top_k": (
            TOP_K
        ),

        "rrf_k": (
            RRF_K
        ),

        "conditions": {
            "A": (
                "whole_retrieval_handle_document_scoring"
            ),

            "B": (
                "proposition_local_max_handle_scoring"
            ),
        },

        # ------------------------------------------------------------
        # RANKING
        # ------------------------------------------------------------

        "whole_target_rank1_families": sum(
            int(
                row[
                    "whole_target_rank"
                ]
                == 1
            )

            for row
            in rows
        ),

        "local_target_rank1_families": sum(
            int(
                row[
                    "local_target_rank"
                ]
                == 1
            )

            for row
            in rows
        ),

        "whole_target_top3_families": sum(
            int(
                row[
                    "whole_target_top3"
                ]
            )

            for row
            in rows
        ),

        "local_target_top3_families": sum(
            int(
                row[
                    "local_target_top3"
                ]
            )

            for row
            in rows
        ),

        "mean_whole_target_rank": (
            _mean(
                row[
                    "whole_target_rank"
                ]

                for row
                in rows
            )
        ),

        "mean_local_target_rank": (
            _mean(
                row[
                    "local_target_rank"
                ]

                for row
                in rows
            )
        ),

        "ranking_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "ranking_rescue"
                ]
            )

            for row
            in rows
        ),

        "ranking_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "ranking_harm"
                ]
            )

            for row
            in rows
        ),

        # ------------------------------------------------------------
        # PARETO ASSEMBLY
        # ------------------------------------------------------------

        "whole_pareto_target_retained_families": sum(
            int(
                row[
                    "whole_target_retained"
                ]
            )

            for row
            in rows
        ),

        "local_pareto_target_retained_families": sum(
            int(
                row[
                    "local_target_retained"
                ]
            )

            for row
            in rows
        ),

        "whole_over_pruning_families": (
            _assembly_count(
                rows,
                "whole",
                "over_pruning",
            )
        ),

        "local_over_pruning_families": (
            _assembly_count(
                rows,
                "local",
                "over_pruning",
            )
        ),

        "whole_upstream_rank_miss_families": (
            _assembly_count(
                rows,
                "whole",
                "upstream_rank_miss",
            )
        ),

        "local_upstream_rank_miss_families": (
            _assembly_count(
                rows,
                "local",
                "upstream_rank_miss",
            )
        ),

        "whole_safe_compaction_families": (
            _assembly_count(
                rows,
                "whole",
                "safe_compaction",
            )
        ),

        "local_safe_compaction_families": (
            _assembly_count(
                rows,
                "local",
                "safe_compaction",
            )
        ),

        "mean_whole_context_k": (
            _mean(
                len(
                    row[
                        "whole_boundary"
                    ][
                        "selected_family_ids"
                    ]
                )

                for row
                in rows
            )
        ),

        "mean_local_context_k": (
            _mean(
                len(
                    row[
                        "local_boundary"
                    ][
                        "selected_family_ids"
                    ]
                )

                for row
                in rows
            )
        ),

        # ------------------------------------------------------------
        # DOWNSTREAM
        # ------------------------------------------------------------

        "whole_task_passes": (
            _count(
                rows,
                "whole",
                "semantic_task_pass",
            )
        ),

        "local_task_passes": (
            _count(
                rows,
                "local",
                "semantic_task_pass",
            )
        ),

        "whole_target_visible_families": (
            _count(
                rows,
                "whole",
                "target_clause_visible",
            )
        ),

        "local_target_visible_families": (
            _count(
                rows,
                "local",
                "target_clause_visible",
            )
        ),

        "whole_families_with_wrong_memory": sum(
            int(
                row[
                    "whole"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "local_families_with_wrong_memory": sum(
            int(
                row[
                    "local"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "whole_wrong_clause_occurrences": int(
            _sum(
                rows,
                "whole",
                "wrong_family_clause_count",
            )
        ),

        "local_wrong_clause_occurrences": int(
            _sum(
                rows,
                "local",
                "wrong_family_clause_count",
            )
        ),

        "whole_wrong_rule_contamination_families": (
            _count(
                rows,
                "whole",
                "wrong_rule_contamination",
            )
        ),

        "local_wrong_rule_contamination_families": (
            _count(
                rows,
                "local",
                "wrong_rule_contamination",
            )
        ),

        "mean_whole_memory_words": (
            _mean(
                row[
                    "whole"
                ][
                    "memory_word_count"
                ]

                for row
                in rows
            )
        ),

        "mean_local_memory_words": (
            _mean(
                row[
                    "local"
                ][
                    "memory_word_count"
                ]

                for row
                in rows
            )
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
        # COST
        # ------------------------------------------------------------

        "mean_proposition_units_per_memory": (
            total_units
            /
            len(
                proposition_units_by_family
            )
        ),

        "whole_semantic_comparisons_per_query": 5,

        "mean_local_semantic_comparisons_per_query": (
            _mean(
                row[
                    "local_semantic_comparisons"
                ]

                for row
                in rows
            )
        ),

        "whole_lexical_comparisons_per_query": 5,

        "mean_local_lexical_comparisons_per_query": (
            _mean(
                row[
                    "local_lexical_comparisons"
                ]

                for row
                in rows
            )
        ),

        # ------------------------------------------------------------
        # CLUSTERS
        # ------------------------------------------------------------

        "whole_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="whole",
            )
        ),

        "local_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="local",
            )
        ),

        # ------------------------------------------------------------
        # SAME-STATE CONTROL
        # ------------------------------------------------------------

        "equal_context_set_pairs": (
            equal_context_pairs
        ),

        "differing_context_set_pairs": (
            differing_context_pairs
        ),

        "reused_equal_context_evaluations": (
            equal_context_pairs
        ),

        "whole_transfer_model_calls": (
            task_count
        ),

        "local_additional_transfer_model_calls": (
            differing_context_pairs
        ),

        "total_transfer_model_calls": (
            task_count
            +
            differing_context_pairs
        ),

        # ------------------------------------------------------------
        # MEMORY / SAFETY
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

        # ------------------------------------------------------------
        # CONTROLS
        # ------------------------------------------------------------

        "all_candidate_routes_equal_between_conditions": True,

        "all_memory_bundles_shared_between_conditions": True,

        "all_source_evidence_shared_between_conditions": True,

        "all_proposition_units_derived_from_whole_retrieval_documents": True,

        "all_entity_scores_equal_between_conditions": all(
            row[
                "entity_scores_equal"
            ]

            for row
            in rows
        ),

        "same_fusion_policy_between_conditions": True,

        "same_pareto_assembly_policy_between_conditions": True,

        "same_authoritative_presentation_representation": True,

        "same_transfer_queries": True,

        "same_reasoner": True,

        "same_context_budget_configuration": True,

        "only_semantic_lexical_scoring_granularity_differs": True,

        "whole_ranker_model_calls": 0,

        "local_ranker_model_calls": 0,

        "all_equal_context_pairs_reused_evaluation": all(
            (
                not
                row[
                    "paired"
                ][
                    "context_sets_equal"
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
            "tasks_026.json"
        ),
    )

    parser.add_argument(
        "--results",
        default=(
            "experiments/"
            "results"
        ),
    )

    args = parser.parse_args()

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
        run_experiment_026(
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

        "whole_target_rank1_families",
        "local_target_rank1_families",

        "whole_target_top3_families",
        "local_target_top3_families",

        "mean_whole_target_rank",
        "mean_local_target_rank",

        "ranking_rescue_families",
        "ranking_harm_families",

        "whole_pareto_target_retained_families",
        "local_pareto_target_retained_families",

        "whole_over_pruning_families",
        "local_over_pruning_families",

        "whole_upstream_rank_miss_families",
        "local_upstream_rank_miss_families",

        "whole_safe_compaction_families",
        "local_safe_compaction_families",

        "mean_whole_context_k",
        "mean_local_context_k",

        "whole_task_passes",
        "local_task_passes",

        "whole_target_visible_families",
        "local_target_visible_families",

        "whole_families_with_wrong_memory",
        "local_families_with_wrong_memory",

        "whole_wrong_clause_occurrences",
        "local_wrong_clause_occurrences",

        "whole_wrong_rule_contamination_families",
        "local_wrong_rule_contamination_families",

        "mean_whole_memory_words",
        "mean_local_memory_words",

        "task_rescue_families",
        "task_harm_families",

        "mean_proposition_units_per_memory",
        "whole_semantic_comparisons_per_query",
        "mean_local_semantic_comparisons_per_query",

        "whole_cluster_metrics",
        "local_cluster_metrics",

        "equal_context_set_pairs",
        "differing_context_set_pairs",
        "reused_equal_context_evaluations",

        "bundle_unsupported_claims_admitted",

        "all_candidate_routes_equal_between_conditions",
        "all_memory_bundles_shared_between_conditions",
        "all_source_evidence_shared_between_conditions",
        "all_proposition_units_derived_from_whole_retrieval_documents",
        "all_entity_scores_equal_between_conditions",

        "same_fusion_policy_between_conditions",
        "same_pareto_assembly_policy_between_conditions",
        "same_authoritative_presentation_representation",
        "same_transfer_queries",
        "same_reasoner",

        "only_semantic_lexical_scoring_granularity_differs",

        "whole_ranker_model_calls",
        "local_ranker_model_calls",

        "all_equal_context_pairs_reused_evaluation",
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
