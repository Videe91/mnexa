from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os

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
    select_conjunctive_candidates,
)

from experiments.seed_growth_021 import (
    RRF_K,
    RETRIEVAL_TOP_K,
    classify_effect,
    posthoc_selection_metrics,
    rank_candidate_ids,
    rendered_memory_from_bundle,
    retrieval_index_from_compact_memory,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


def channel_is_non_discriminative(
    scores,
):
    """
    Exact equality only.

    Seed 022 deliberately does not introduce a tolerance hyperparameter.
    Near-tie handling is outside this experiment.
    """

    values = [
        float(value)
        for value
        in scores.values()
    ]

    if len(values) <= 1:
        return True

    return (
        len(
            set(values)
        )
        == 1
    )


def average_tie_ranks(
    *,
    candidate_family_ids,
    scores,
):
    """
    Descending score rank using statistical mid-ranks.

    Example:

        scores:
            a = 10
            b = 10
            c = 5
            d = 1
            e = 1

        ranks:
            a = 1.5
            b = 1.5
            c = 3.0
            d = 4.5
            e = 4.5

    Equal evidence receives equal RRF influence.
    """

    grouped = defaultdict(
        list
    )

    for family_id in (
        candidate_family_ids
    ):

        grouped[
            float(
                scores[
                    family_id
                ]
            )
        ].append(
            family_id
        )

    descending_scores = sorted(
        grouped.keys(),
        reverse=True,
    )

    ranks = {}

    next_position = 1

    for score in descending_scores:

        members = (
            grouped[
                score
            ]
        )

        first_position = (
            next_position
        )

        last_position = (
            next_position
            +
            len(members)
            -
            1
        )

        average_rank = (
            first_position
            +
            last_position
        ) / 2.0

        for family_id in members:

            ranks[
                family_id
            ] = (
                average_rank
            )

        next_position = (
            last_position
            +
            1
        )

    return ranks


def channel_has_artificial_sequential_tie(
    *,
    scores,
    ranks,
):
    """
    Diagnostic for the Seed 021 behavior:

    identical channel scores but unequal downstream ranks.
    """

    if not channel_is_non_discriminative(
        scores
    ):
        return False

    rank_values = [
        value

        for value
        in ranks.values()

        if value is not None
    ]

    return (
        len(
            set(
                rank_values
            )
        )
        > 1
    )


def fuse_channel_scores_abstaining(
    *,
    candidate_family_ids,
    channel_scores,
    top_k=RETRIEVAL_TOP_K,
    rrf_k=RRF_K,
):
    """
    Seed 022 fusion rule.

    1. A completely non-discriminative channel abstains.
    2. Partial exact ties receive equal mid-ranks.
    3. Discriminative channels contribute ordinary RRF terms.
    4. Final total-score ties use canonical candidate order only as
       the final deterministic fallback.

    No query, target, semantic clause, grader, or model is used here.
    """

    candidate_family_ids = list(
        candidate_family_ids
    )

    canonical_index = {
        family_id: index

        for index, family_id
        in enumerate(
            candidate_family_ids
        )
    }

    rrf_scores = {
        family_id: 0.0

        for family_id
        in candidate_family_ids
    }

    active_channels = []
    abstained_channels = []

    channel_ranks = {}
    channel_contributions = {}

    for (
        channel,
        scores,
    ) in channel_scores.items():

        missing = [
            family_id

            for family_id
            in candidate_family_ids

            if family_id
            not in scores
        ]

        if missing:

            raise ValueError(
                f"Channel {channel!r} "
                f"is missing candidate scores: "
                f"{missing}"
            )

        if channel_is_non_discriminative(
            scores
        ):

            abstained_channels.append(
                channel
            )

            channel_ranks[
                channel
            ] = {
                family_id: None

                for family_id
                in candidate_family_ids
            }

            channel_contributions[
                channel
            ] = {
                family_id: 0.0

                for family_id
                in candidate_family_ids
            }

            continue

        active_channels.append(
            channel
        )

        ranks = (
            average_tie_ranks(
                candidate_family_ids=(
                    candidate_family_ids
                ),
                scores=scores,
            )
        )

        contributions = {}

        for family_id in (
            candidate_family_ids
        ):

            contribution = (
                1.0
                /
                (
                    rrf_k
                    +
                    ranks[
                        family_id
                    ]
                )
            )

            contributions[
                family_id
            ] = (
                contribution
            )

            rrf_scores[
                family_id
            ] += (
                contribution
            )

        channel_ranks[
            channel
        ] = (
            ranks
        )

        channel_contributions[
            channel
        ] = (
            contributions
        )

    all_channels_abstained = (
        len(
            active_channels
        )
        == 0
    )

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
            copy.deepcopy(
                channel_scores
            )
        ),

        "channel_ranks": (
            channel_ranks
        ),

        "channel_contributions": (
            channel_contributions
        ),

        "active_channels": (
            active_channels
        ),

        "abstained_channels": (
            abstained_channels
        ),

        "active_channel_count": (
            len(
                active_channels
            )
        ),

        "abstained_channel_count": (
            len(
                abstained_channels
            )
        ),

        "all_channels_abstained": (
            all_channels_abstained
        ),

        "top_k": (
            top_k
        ),

        "rrf_k": (
            rrf_k
        ),

        "tie_policy": (
            "exact-tie-midrank"
        ),

        "abstention_policy": (
            "full-channel-exact-tie-abstains"
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
    baseline_selected_ids,
    abstaining_selected_ids,
    canonical_family_ids,
):
    return (
        canonical_selection_key(
            selected_family_ids=(
                baseline_selected_ids
            ),
            canonical_family_ids=(
                canonical_family_ids
            ),
        )
        !=
        canonical_selection_key(
            selected_family_ids=(
                abstaining_selected_ids
            ),
            canonical_family_ids=(
                canonical_family_ids
            ),
        )
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
            "wrong_clause_occurrences": 0,
            "families_with_wrong_memory": 0,
            "target_selected": 0,
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

        evaluation = (
            row[
                condition
            ]
        )

        ranking = (
            row[
                ranking_key
            ]
        )

        selection = (
            ranking[
                "selection_metrics"
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
            evaluation[
                "semantic_task_pass"
            ]
        )

        bucket[
            "target_visible_families"
        ] += int(
            evaluation[
                "target_clause_visible"
            ]
        )

        wrong = int(
            evaluation[
                "wrong_family_clause_count"
            ]
        )

        bucket[
            "wrong_clause_occurrences"
        ] += (
            wrong
        )

        bucket[
            "families_with_wrong_memory"
        ] += int(
            wrong > 0
        )

        bucket[
            "target_selected"
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

    result = {}

    for (
        cluster,
        bucket,
    ) in sorted(
        grouped.items()
    ):

        count = (
            bucket[
                "families"
            ]
        )

        result[
            cluster
        ] = {
            "families": (
                count
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
                count
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
                    "wrong_clause_occurrences"
                ]
            ),

            "selection_target_present": (
                bucket[
                    "target_selected"
                ]
            ),

            "mean_selection_precision": (
                bucket[
                    "selection_precision_sum"
                ]
                /
                count
            ),

            "mean_selection_recall": (
                bucket[
                    "selection_recall_sum"
                ]
                /
                count
            ),
        }

    return result


def run_experiment_022(
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
        family["id"]: family

        for family
        in families
    }

    canonical_family_ids = [
        family["id"]

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
        family["id"]: (
            build_memory_bundle(
                family=family,
                model=model,
            )
        )

        for family
        in families
    }

    handle_documents = {}

    entities_by_family = {
        family["id"]: list(
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
    # AUTHORITATIVE SNAPSHOT CACHE
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
                "Selected memory set may not be empty."
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
        ] = (
            snapshot
        )

        return (
            snapshot,
            key,
        )

    clause_by_family = {
        family["id"]: (
            family[
                "semantic_clause"
            ]
        )

        for family
        in families
    }

    rows = []

    # ================================================================
    # PAIRED EVALUATION
    # ================================================================

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        # ------------------------------------------------------------
        # IDENTICAL SEED 020 ROUTING
        # ------------------------------------------------------------

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

        if (
            len(candidate_ids)
            != 5
        ):

            raise RuntimeError(
                "Seed 022 frozen candidate geometry "
                f"violated for {family_id}: "
                f"{len(candidate_ids)} candidates"
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
        #
        # Exact Seed 021 handle-index ranking.
        # This also produces the channel scores reused by B.
        # ------------------------------------------------------------

        baseline_rank = (
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

        # ------------------------------------------------------------
        # CONDITION B
        #
        # NO SCORE RECOMPUTATION.
        #
        # Reuse exact A channel scores.
        # Only tie/abstention fusion differs.
        # ------------------------------------------------------------

        abstaining_rank = (
            fuse_channel_scores_abstaining(
                candidate_family_ids=(
                    candidate_ids
                ),

                channel_scores=(
                    baseline_rank[
                        "channel_scores"
                    ]
                ),

                top_k=(
                    RETRIEVAL_TOP_K
                ),

                rrf_k=(
                    RRF_K
                ),
            )
        )

        baseline_selection = (
            posthoc_selection_metrics(
                target_family_id=(
                    family_id
                ),

                selected_family_ids=(
                    baseline_rank[
                        "selected_family_ids"
                    ]
                ),
            )
        )

        abstaining_selection = (
            posthoc_selection_metrics(
                target_family_id=(
                    family_id
                ),

                selected_family_ids=(
                    abstaining_rank[
                        "selected_family_ids"
                    ]
                ),
            )
        )

        baseline_rank[
            "selection_metrics"
        ] = (
            baseline_selection
        )

        abstaining_rank[
            "selection_metrics"
        ] = (
            abstaining_selection
        )

        (
            baseline_snapshot,
            baseline_key,
        ) = (
            snapshot_for(
                baseline_rank[
                    "selected_family_ids"
                ]
            )
        )

        (
            abstaining_snapshot,
            abstaining_key,
        ) = (
            snapshot_for(
                abstaining_rank[
                    "selected_family_ids"
                ]
            )
        )

        eval_family = (
            evaluation_family(
                family
            )
        )

        baseline_eval = (
            evaluate_snapshot(
                snapshot_path=Path(
                    baseline_snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    eval_dir
                    /
                    (
                        "baseline_"
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

        same_selected_set = (
            baseline_key
            ==
            abstaining_key
        )

        if same_selected_set:

            abstaining_eval = (
                copy.deepcopy(
                    baseline_eval
                )
            )

        else:

            abstaining_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        abstaining_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "abstaining_"
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
                    baseline_eval[
                        "semantic_task_pass"
                    ]
                ),

                handle_pass=(
                    abstaining_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    baseline_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    abstaining_eval[
                        "target_clause_visible"
                    ]
                ),
            )
        )

        artificial_channels = []

        for channel in (
            baseline_rank[
                "channel_scores"
            ]
        ):

            if channel_has_artificial_sequential_tie(
                scores=(
                    baseline_rank[
                        "channel_scores"
                    ][
                        channel
                    ]
                ),

                ranks=(
                    baseline_rank[
                        "channel_ranks"
                    ][
                        channel
                    ]
                ),
            ):

                artificial_channels.append(
                    channel
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

                "baseline_ranking": (
                    baseline_rank
                ),

                "abstaining_ranking": (
                    abstaining_rank
                ),

                "baseline_artificial_sequential_tie_channels": (
                    artificial_channels
                ),

                "baseline": (
                    baseline_eval
                ),

                "abstaining": (
                    abstaining_eval
                ),

                "paired": {
                    **effect,

                    "selected_sets_equal": (
                        same_selected_set
                    ),

                    "evaluation_reused": (
                        same_selected_set
                    ),

                    "selection_target_delta": (
                        int(
                            abstaining_selection[
                                "target_selected"
                            ]
                        )
                        -
                        int(
                            baseline_selection[
                                "target_selected"
                            ]
                        )
                    ),

                    "task_delta": (
                        int(
                            abstaining_eval[
                                "semantic_task_pass"
                            ]
                        )
                        -
                        int(
                            baseline_eval[
                                "semantic_task_pass"
                            ]
                        )
                    ),

                    "visibility_delta": (
                        int(
                            abstaining_eval[
                                "target_clause_visible"
                            ]
                        )
                        -
                        int(
                            baseline_eval[
                                "target_clause_visible"
                            ]
                        )
                    ),

                    "wrong_family_clause_delta": (
                        abstaining_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        baseline_eval[
                            "wrong_family_clause_count"
                        ]
                    ),
                },
            }
        )

    # ================================================================
    # TARGET-MEMORY CONTROL
    # ================================================================

    target_lessons_equal = True
    target_sources_equal = True

    for row in rows:

        family_id = (
            row[
                "family_id"
            ]
        )

        baseline_ids = (
            row[
                "baseline_ranking"
            ][
                "selected_family_ids"
            ]
        )

        abstaining_ids = (
            row[
                "abstaining_ranking"
            ][
                "selected_family_ids"
            ]
        )

        if (
            family_id
            not in baseline_ids
            or
            family_id
            not in abstaining_ids
        ):
            continue

        baseline_snapshot, _ = (
            snapshot_for(
                baseline_ids
            )
        )

        abstaining_snapshot, _ = (
            snapshot_for(
                abstaining_ids
            )
        )

        baseline_record = (
            _learned_record(
                baseline_snapshot,
                family_id,
            )
        )

        abstaining_record = (
            _learned_record(
                abstaining_snapshot,
                family_id,
            )
        )

        if (
            baseline_record[
                "lesson_sha256"
            ]
            !=
            abstaining_record[
                "lesson_sha256"
            ]
        ):

            target_lessons_equal = False

        if (
            baseline_record[
                "source_evidence_sha256"
            ]
            !=
            abstaining_record[
                "source_evidence_sha256"
            ]
        ):

            target_sources_equal = False

    task_count = len(
        rows
    )

    baseline_passes = (
        _count(
            rows,
            "baseline",
            "semantic_task_pass",
        )
    )

    abstaining_passes = (
        _count(
            rows,
            "abstaining",
            "semantic_task_pass",
        )
    )

    equal_selected_pairs = sum(
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

    differing_selected_pairs = (
        task_count
        -
        equal_selected_pairs
    )

    channel_names = sorted(
        {
            channel

            for row
            in rows

            for channel
            in row[
                "baseline_ranking"
            ][
                "channel_scores"
            ]
        }
    )

    abstention_counts = {
        channel: sum(
            int(
                channel
                in
                row[
                    "abstaining_ranking"
                ][
                    "abstained_channels"
                ]
            )

            for row
            in rows
        )

        for channel
        in channel_names
    }

    artificial_tie_counts = {
        channel: sum(
            int(
                channel
                in
                row[
                    "baseline_artificial_sequential_tie_channels"
                ]
            )

            for row
            in rows
        )

        for channel
        in channel_names
    }

    report = {
        "experiment": (
            "seed-growth-022"
        ),

        "classification": (
            "exploratory-fresh-non-discriminative-"
            "channel-abstention-ablation"
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

        "retrieval_top_k": (
            RETRIEVAL_TOP_K
        ),

        "rrf_k": (
            RRF_K
        ),

        "conditions": {
            "A": (
                "seed_021_handle_index_with_"
                "sequential_deterministic_tie_ranking"
            ),

            "B": (
                "same_scores_non_discriminative_channels_"
                "abstain_partial_ties_use_midranks"
            ),
        },

        # ------------------------------------------------------------
        # SELECTION
        # ------------------------------------------------------------

        "baseline_selection_target_families": sum(
            int(
                row[
                    "baseline_ranking"
                ][
                    "selection_metrics"
                ][
                    "target_selected"
                ]
            )

            for row
            in rows
        ),

        "abstaining_selection_target_families": sum(
            int(
                row[
                    "abstaining_ranking"
                ][
                    "selection_metrics"
                ][
                    "target_selected"
                ]
            )

            for row
            in rows
        ),

        "mean_baseline_selection_precision": (
            _mean(
                row[
                    "baseline_ranking"
                ][
                    "selection_metrics"
                ][
                    "selection_precision"
                ]

                for row
                in rows
            )
        ),

        "mean_abstaining_selection_precision": (
            _mean(
                row[
                    "abstaining_ranking"
                ][
                    "selection_metrics"
                ][
                    "selection_precision"
                ]

                for row
                in rows
            )
        ),

        "mean_baseline_selection_recall": (
            _mean(
                row[
                    "baseline_ranking"
                ][
                    "selection_metrics"
                ][
                    "selection_recall"
                ]

                for row
                in rows
            )
        ),

        "mean_abstaining_selection_recall": (
            _mean(
                row[
                    "abstaining_ranking"
                ][
                    "selection_metrics"
                ][
                    "selection_recall"
                ]

                for row
                in rows
            )
        ),

        # ------------------------------------------------------------
        # DOWNSTREAM
        # ------------------------------------------------------------

        "baseline_task_passes": (
            baseline_passes
        ),

        "abstaining_task_passes": (
            abstaining_passes
        ),

        "baseline_task_pass_rate": (
            baseline_passes
            /
            task_count
        ),

        "abstaining_task_pass_rate": (
            abstaining_passes
            /
            task_count
        ),

        "baseline_target_visible_families": (
            _count(
                rows,
                "baseline",
                "target_clause_visible",
            )
        ),

        "abstaining_target_visible_families": (
            _count(
                rows,
                "abstaining",
                "target_clause_visible",
            )
        ),

        "baseline_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "baseline"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "abstaining_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "abstaining"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "baseline_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "baseline",
                "wrong_family_clause_count",
            )
        ),

        "abstaining_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "abstaining",
                "wrong_family_clause_count",
            )
        ),

        "baseline_wrong_rule_contamination_families": (
            _count(
                rows,
                "baseline",
                "wrong_rule_contamination",
            )
        ),

        "abstaining_wrong_rule_contamination_families": (
            _count(
                rows,
                "abstaining",
                "wrong_rule_contamination",
            )
        ),

        "mean_baseline_retrieval_precision": (
            _mean(
                row[
                    "baseline"
                ][
                    "retrieval_precision"
                ]

                for row
                in rows
            )
        ),

        "mean_abstaining_retrieval_precision": (
            _mean(
                row[
                    "abstaining"
                ][
                    "retrieval_precision"
                ]

                for row
                in rows
            )
        ),

        "mean_baseline_retrieval_recall": (
            _mean(
                row[
                    "baseline"
                ][
                    "retrieval_recall"
                ]

                for row
                in rows
            )
        ),

        "mean_abstaining_retrieval_recall": (
            _mean(
                row[
                    "abstaining"
                ][
                    "retrieval_recall"
                ]

                for row
                in rows
            )
        ),

        # ------------------------------------------------------------
        # FUSION DIAGNOSTICS
        # ------------------------------------------------------------

        "baseline_artificial_sequential_tie_counts": (
            artificial_tie_counts
        ),

        "abstention_counts_by_channel": (
            abstention_counts
        ),

        "mean_active_channel_count": (
            _mean(
                row[
                    "abstaining_ranking"
                ][
                    "active_channel_count"
                ]

                for row
                in rows
            )
        ),

        "families_all_channels_abstained": sum(
            int(
                row[
                    "abstaining_ranking"
                ][
                    "all_channels_abstained"
                ]
            )

            for row
            in rows
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
        # CLUSTER ANALYSIS
        # ------------------------------------------------------------

        "baseline_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="baseline",
                ranking_key=(
                    "baseline_ranking"
                ),
            )
        ),

        "abstaining_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="abstaining",
                ranking_key=(
                    "abstaining_ranking"
                ),
            )
        ),

        # ------------------------------------------------------------
        # SAME-STATE NOISE CONTROL
        # ------------------------------------------------------------

        "equal_selected_set_pairs": (
            equal_selected_pairs
        ),

        "differing_selected_set_pairs": (
            differing_selected_pairs
        ),

        "reused_equal_selected_evaluations": (
            equal_selected_pairs
        ),

        "baseline_transfer_model_calls": (
            task_count
        ),

        "abstaining_additional_transfer_model_calls": (
            differing_selected_pairs
        ),

        "total_transfer_model_calls": (
            task_count
            +
            differing_selected_pairs
        ),

        # ------------------------------------------------------------
        # MEMORY SAFETY
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
        # ABLATION CONTROLS
        # ------------------------------------------------------------

        "all_candidate_routes_equal_between_conditions": True,

        "all_retrieval_documents_equal_between_conditions": True,

        "all_channel_scores_equal_between_conditions": True,

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

        "only_fusion_policy_differs": True,

        "baseline_ranker_model_calls": 0,

        "abstaining_ranker_model_calls": 0,

        "abstaining_ranker_used_family_id": False,

        "abstaining_ranker_used_semantic_clause": False,

        "abstaining_ranker_used_semantic_grader": False,

        "all_equal_selected_pairs_reused_evaluation": all(
            (
                not
                row[
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
            "tasks_022.json"
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
        run_experiment_022(
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

        "baseline_selection_target_families",
        "abstaining_selection_target_families",

        "mean_baseline_selection_precision",
        "mean_abstaining_selection_precision",

        "mean_baseline_selection_recall",
        "mean_abstaining_selection_recall",

        "baseline_task_passes",
        "abstaining_task_passes",

        "baseline_target_visible_families",
        "abstaining_target_visible_families",

        "baseline_families_with_wrong_memory_presented",
        "abstaining_families_with_wrong_memory_presented",

        "baseline_wrong_family_clause_occurrences",
        "abstaining_wrong_family_clause_occurrences",

        "baseline_wrong_rule_contamination_families",
        "abstaining_wrong_rule_contamination_families",

        "mean_baseline_retrieval_precision",
        "mean_abstaining_retrieval_precision",

        "mean_baseline_retrieval_recall",
        "mean_abstaining_retrieval_recall",

        "baseline_artificial_sequential_tie_counts",
        "abstention_counts_by_channel",
        "mean_active_channel_count",
        "families_all_channels_abstained",

        "selection_rescue_families",
        "selection_harm_families",

        "task_rescue_families",
        "task_harm_families",

        "visibility_rescue_families",
        "visibility_harm_families",

        "baseline_cluster_metrics",
        "abstaining_cluster_metrics",

        "equal_selected_set_pairs",
        "differing_selected_set_pairs",
        "reused_equal_selected_evaluations",

        "total_transfer_model_calls",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "all_candidate_routes_equal_between_conditions",
        "all_retrieval_documents_equal_between_conditions",
        "all_channel_scores_equal_between_conditions",
        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",
        "all_transfer_queries_equal",
        "all_presented_memory_representation_equal",
        "all_context_budget_configuration_equal",
        "all_reasoners_equal",
        "only_fusion_policy_differs",

        "baseline_ranker_model_calls",
        "abstaining_ranker_model_calls",

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
