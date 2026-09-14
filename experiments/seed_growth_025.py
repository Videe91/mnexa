from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os

from collections import (
    Counter,
    defaultdict,
)

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

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


FIXED_TOP_K = 3
DYNAMIC_MAX_K = 3


def candidate_dominates(
    *,
    candidate_a,
    candidate_b,
    channel_ranks,
    active_channels,
):
    """
    A Pareto-dominates B iff:

    - A is at least as highly ranked as B on every active channel; and
    - A is strictly better on at least one active channel.

    Lower rank is better.
    """

    if not active_channels:
        return False

    at_least_as_good_everywhere = True
    strictly_better_somewhere = False

    for channel in active_channels:

        ranks = (
            channel_ranks[
                channel
            ]
        )

        rank_a = ranks[
            candidate_a
        ]

        rank_b = ranks[
            candidate_b
        ]

        if (
            rank_a is None
            or
            rank_b is None
        ):

            raise ValueError(
                "Active channel contains "
                "missing/abstained rank."
            )

        rank_a = float(
            rank_a
        )

        rank_b = float(
            rank_b
        )

        if rank_a > rank_b:

            at_least_as_good_everywhere = False
            break

        if rank_a < rank_b:

            strictly_better_somewhere = True

    return (
        at_least_as_good_everywhere
        and
        strictly_better_somewhere
    )


def pareto_frontier(
    *,
    candidate_family_ids,
    channel_ranks,
    active_channels,
):
    """
    Return the set of memories that are not dominated by any
    other candidate across all active retrieval channels.
    """

    candidate_family_ids = list(
        candidate_family_ids
    )

    if not active_channels:

        return {
            "frontier_family_ids": [],
            "dominated_family_ids": [],
            "dominators_by_family": {},
        }

    frontier = []
    dominated = []
    dominators_by_family = {}

    for candidate_b in (
        candidate_family_ids
    ):

        dominators = []

        for candidate_a in (
            candidate_family_ids
        ):

            if (
                candidate_a
                ==
                candidate_b
            ):
                continue

            if candidate_dominates(
                candidate_a=(
                    candidate_a
                ),
                candidate_b=(
                    candidate_b
                ),
                channel_ranks=(
                    channel_ranks
                ),
                active_channels=(
                    active_channels
                ),
            ):

                dominators.append(
                    candidate_a
                )

        if dominators:

            dominated.append(
                candidate_b
            )

            dominators_by_family[
                candidate_b
            ] = (
                dominators
            )

        else:

            frontier.append(
                candidate_b
            )

    return {
        "frontier_family_ids": (
            frontier
        ),

        "dominated_family_ids": (
            dominated
        ),

        "dominators_by_family": (
            dominators_by_family
        ),
    }


def pareto_context_boundary(
    *,
    ordered_family_ids,
    channel_ranks,
    active_channels,
    max_k=DYNAMIC_MAX_K,
):
    """
    Pareto-safe context assembly.

    Preserve every non-dominated candidate when doing so fits
    inside max_k.

    If any Pareto-frontier memory is below max_k in the fused
    ordering, conservatively keep max_k rather than expanding
    beyond the fixed baseline.

    This function does not know the target memory.
    """

    ordered_family_ids = list(
        ordered_family_ids
    )

    if len(
        ordered_family_ids
    ) < max_k:

        raise ValueError(
            "Fused ordering contains fewer "
            "candidates than max_k."
        )

    if not active_channels:

        return {
            "dynamic_k": (
                max_k
            ),

            "selected_family_ids": (
                ordered_family_ids[
                    :max_k
                ]
            ),

            "frontier_family_ids": [],

            "dominated_family_ids": [],

            "dominators_by_family": {},

            "frontier_positions": {},

            "frontier_outside_max_k": False,

            "frontier_class": (
                "no_active_channels"
            ),

            "max_k": (
                max_k
            ),

            "policy": (
                "pareto_safe_active_channel_frontier"
            ),
        }

    frontier_result = (
        pareto_frontier(
            candidate_family_ids=(
                ordered_family_ids
            ),

            channel_ranks=(
                channel_ranks
            ),

            active_channels=(
                active_channels
            ),
        )
    )

    frontier_ids = (
        frontier_result[
            "frontier_family_ids"
        ]
    )

    if not frontier_ids:

        raise RuntimeError(
            "Active-channel Pareto frontier "
            "may not be empty."
        )

    position = {
        family_id: index + 1

        for index, family_id
        in enumerate(
            ordered_family_ids
        )
    }

    frontier_positions = {
        family_id: position[
            family_id
        ]

        for family_id
        in frontier_ids
    }

    frontier_outside_max_k = any(
        rank > max_k

        for rank
        in frontier_positions.values()
    )

    if frontier_outside_max_k:

        dynamic_k = (
            max_k
        )

        frontier_class = (
            "frontier_outside_max_k"
        )

    else:

        dynamic_k = max(
            frontier_positions.values()
        )

        if len(
            frontier_ids
        ) == 1:

            frontier_class = (
                "single_nondominated_candidate"
            )

        else:

            frontier_class = (
                "multi_candidate_frontier"
            )

    return {
        "dynamic_k": (
            dynamic_k
        ),

        "selected_family_ids": (
            ordered_family_ids[
                :dynamic_k
            ]
        ),

        "frontier_family_ids": (
            frontier_ids
        ),

        "dominated_family_ids": (
            frontier_result[
                "dominated_family_ids"
            ]
        ),

        "dominators_by_family": (
            frontier_result[
                "dominators_by_family"
            ]
        ),

        "frontier_positions": (
            frontier_positions
        ),

        "frontier_outside_max_k": (
            frontier_outside_max_k
        ),

        "frontier_class": (
            frontier_class
        ),

        "max_k": (
            max_k
        ),

        "policy": (
            "pareto_safe_active_channel_frontier"
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
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "task_passes": 0,
            "target_visible": 0,
            "wrong_memory_families": 0,
            "wrong_clause_occurrences": 0,
            "memory_words": 0,
            "memory_segments": 0,
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
            "target_visible"
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
            "wrong_memory_families"
        ] += int(
            wrong > 0
        )

        bucket[
            "wrong_clause_occurrences"
        ] += wrong

        bucket[
            "memory_words"
        ] += int(
            evaluation[
                "memory_word_count"
            ]
        )

        bucket[
            "memory_segments"
        ] += int(
            evaluation[
                "memory_segment_count"
            ]
        )

    output = {}

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

        output[
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
                    "target_visible"
                ]
            ),

            "families_with_wrong_memory": (
                bucket[
                    "wrong_memory_families"
                ]
            ),

            "wrong_family_clause_occurrences": (
                bucket[
                    "wrong_clause_occurrences"
                ]
            ),

            "mean_memory_words": (
                bucket[
                    "memory_words"
                ]
                /
                count
            ),

            "mean_memory_segments": (
                bucket[
                    "memory_segments"
                ]
                /
                count
            ),
        }

    return output


def run_experiment_025(
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
    # PAIRED EVALUATION
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
                "Seed 025 frozen candidate "
                "geometry violated."
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

        raw_ranking = (
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

        fused = (
            fuse_channel_scores_abstaining(
                candidate_family_ids=(
                    candidate_ids
                ),

                channel_scores=(
                    raw_ranking[
                        "channel_scores"
                    ]
                ),

                top_k=5,

                rrf_k=RRF_K,
            )
        )

        full_order = (
            fused[
                "selected_family_ids"
            ]
        )

        fixed_selected_ids = (
            full_order[
                :FIXED_TOP_K
            ]
        )

        boundary = (
            pareto_context_boundary(
                ordered_family_ids=(
                    full_order
                ),

                channel_ranks=(
                    fused[
                        "channel_ranks"
                    ]
                ),

                active_channels=(
                    fused[
                        "active_channels"
                    ]
                ),

                max_k=(
                    DYNAMIC_MAX_K
                ),
            )
        )

        pareto_selected_ids = (
            boundary[
                "selected_family_ids"
            ]
        )

        assembly = (
            classify_assembly_effect(
                target_family_id=(
                    family_id
                ),

                fixed_selected_ids=(
                    fixed_selected_ids
                ),

                dynamic_selected_ids=(
                    pareto_selected_ids
                ),
            )
        )

        target_on_frontier = (
            family_id
            in
            boundary[
                "frontier_family_ids"
            ]
        )

        (
            fixed_snapshot,
            fixed_key,
        ) = (
            snapshot_for(
                fixed_selected_ids
            )
        )

        (
            pareto_snapshot,
            pareto_key,
        ) = (
            snapshot_for(
                pareto_selected_ids
            )
        )

        eval_family = (
            evaluation_family(
                family
            )
        )

        fixed_eval = (
            evaluate_snapshot(
                snapshot_path=Path(
                    fixed_snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    eval_dir
                    /
                    (
                        "fixed_"
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
            fixed_key
            ==
            pareto_key
        )

        if same_context_set:

            pareto_eval = (
                copy.deepcopy(
                    fixed_eval
                )
            )

        else:

            pareto_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        pareto_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "pareto_"
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
                    fixed_eval[
                        "semantic_task_pass"
                    ]
                ),

                handle_pass=(
                    pareto_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    fixed_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    pareto_eval[
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

                "channel_scores": (
                    raw_ranking[
                        "channel_scores"
                    ]
                ),

                "abstaining_fusion": (
                    fused
                ),

                "fixed_selected_family_ids": (
                    fixed_selected_ids
                ),

                "pareto_boundary": (
                    boundary
                ),

                "target_on_pareto_frontier": (
                    target_on_frontier
                ),

                "assembly_effect": (
                    assembly
                ),

                "fixed": (
                    fixed_eval
                ),

                "pareto": (
                    pareto_eval
                ),

                "paired": {
                    **behavioral_effect,

                    "context_sets_equal": (
                        same_context_set
                    ),

                    "evaluation_reused": (
                        same_context_set
                    ),

                    "task_delta": (
                        int(
                            pareto_eval[
                                "semantic_task_pass"
                            ]
                        )
                        -
                        int(
                            fixed_eval[
                                "semantic_task_pass"
                            ]
                        )
                    ),

                    "visibility_delta": (
                        int(
                            pareto_eval[
                                "target_clause_visible"
                            ]
                        )
                        -
                        int(
                            fixed_eval[
                                "target_clause_visible"
                            ]
                        )
                    ),

                    "wrong_clause_delta": (
                        pareto_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        fixed_eval[
                            "wrong_family_clause_count"
                        ]
                    ),

                    "memory_word_delta": (
                        pareto_eval[
                            "memory_word_count"
                        ]
                        -
                        fixed_eval[
                            "memory_word_count"
                        ]
                    ),

                    "memory_segment_delta": (
                        pareto_eval[
                            "memory_segment_count"
                        ]
                        -
                        fixed_eval[
                            "memory_segment_count"
                        ]
                    ),
                },
            }
        )

    target_lessons_equal = True
    target_sources_equal = True

    for row in rows:

        family_id = (
            row[
                "family_id"
            ]
        )

        fixed_ids = (
            row[
                "fixed_selected_family_ids"
            ]
        )

        pareto_ids = (
            row[
                "pareto_boundary"
            ][
                "selected_family_ids"
            ]
        )

        if (
            family_id
            not in fixed_ids
            or
            family_id
            not in pareto_ids
        ):

            continue

        fixed_snapshot, _ = (
            snapshot_for(
                fixed_ids
            )
        )

        pareto_snapshot, _ = (
            snapshot_for(
                pareto_ids
            )
        )

        fixed_record = (
            _learned_record(
                fixed_snapshot,
                family_id,
            )
        )

        pareto_record = (
            _learned_record(
                pareto_snapshot,
                family_id,
            )
        )

        if (
            fixed_record[
                "lesson_sha256"
            ]
            !=
            pareto_record[
                "lesson_sha256"
            ]
        ):

            target_lessons_equal = False

        if (
            fixed_record[
                "source_evidence_sha256"
            ]
            !=
            pareto_record[
                "source_evidence_sha256"
            ]
        ):

            target_sources_equal = False

    task_count = len(
        rows
    )

    assembly_counts = Counter(
        row[
            "assembly_effect"
        ][
            "assembly_class"
        ]

        for row
        in rows
    )

    k_counts = Counter(
        row[
            "pareto_boundary"
        ][
            "dynamic_k"
        ]

        for row
        in rows
    )

    frontier_class_counts = Counter(
        row[
            "pareto_boundary"
        ][
            "frontier_class"
        ]

        for row
        in rows
    )

    frontier_size_counts = Counter(
        len(
            row[
                "pareto_boundary"
            ][
                "frontier_family_ids"
            ]
        )

        for row
        in rows
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

    fixed_passes = (
        _count(
            rows,
            "fixed",
            "semantic_task_pass",
        )
    )

    pareto_passes = (
        _count(
            rows,
            "pareto",
            "semantic_task_pass",
        )
    )

    report = {
        "experiment": (
            "seed-growth-025"
        ),

        "classification": (
            "exploratory-fresh-pareto-safe-"
            "context-assembly-ablation"
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
            len(families)
        ),

        "candidate_neighborhood_size": 5,

        "fixed_top_k": (
            FIXED_TOP_K
        ),

        "dynamic_max_k": (
            DYNAMIC_MAX_K
        ),

        "rrf_k": (
            RRF_K
        ),

        "conditions": {
            "A": (
                "seed_022_abstaining_rrf_fixed_top3"
            ),

            "B": (
                "same_ranking_pareto_safe_"
                "active_channel_frontier_prefix"
            ),
        },

        "fixed_target_selected_families": sum(
            int(
                row[
                    "assembly_effect"
                ][
                    "target_in_fixed_top3"
                ]
            )

            for row
            in rows
        ),

        "pareto_target_retained_families": sum(
            int(
                row[
                    "assembly_effect"
                ][
                    "target_retained"
                ]
            )

            for row
            in rows
        ),

        "target_on_pareto_frontier_families": sum(
            int(
                row[
                    "target_on_pareto_frontier"
                ]
            )

            for row
            in rows
        ),

        "safe_compaction_families": (
            assembly_counts[
                "safe_compaction"
            ]
        ),

        "over_pruning_families": (
            assembly_counts[
                "over_pruning"
            ]
        ),

        "upstream_rank_miss_families": (
            assembly_counts[
                "upstream_rank_miss"
            ]
        ),

        "no_change_families": (
            assembly_counts[
                "no_change"
            ]
        ),

        "mean_pareto_k": (
            _mean(
                row[
                    "pareto_boundary"
                ][
                    "dynamic_k"
                ]

                for row
                in rows
            )
        ),

        "pareto_k_distribution": {
            str(k): (
                k_counts[k]
            )

            for k
            in (
                1,
                2,
                3,
            )
        },

        "frontier_class_distribution": (
            dict(
                sorted(
                    frontier_class_counts.items()
                )
            )
        ),

        "frontier_size_distribution": {
            str(size): count

            for size, count
            in sorted(
                frontier_size_counts.items()
            )
        },

        "frontier_outside_max_k_families": sum(
            int(
                row[
                    "pareto_boundary"
                ][
                    "frontier_outside_max_k"
                ]
            )

            for row
            in rows
        ),

        "mean_distractors_before": (
            _mean(
                row[
                    "assembly_effect"
                ][
                    "distractors_before"
                ]

                for row
                in rows
            )
        ),

        "mean_distractors_after": (
            _mean(
                row[
                    "assembly_effect"
                ][
                    "distractors_after"
                ]

                for row
                in rows
            )
        ),

        "fixed_task_passes": (
            fixed_passes
        ),

        "pareto_task_passes": (
            pareto_passes
        ),

        "fixed_task_pass_rate": (
            fixed_passes
            /
            task_count
        ),

        "pareto_task_pass_rate": (
            pareto_passes
            /
            task_count
        ),

        "fixed_target_visible_families": (
            _count(
                rows,
                "fixed",
                "target_clause_visible",
            )
        ),

        "pareto_target_visible_families": (
            _count(
                rows,
                "pareto",
                "target_clause_visible",
            )
        ),

        "fixed_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "fixed"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "pareto_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "pareto"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "fixed_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "fixed",
                "wrong_family_clause_count",
            )
        ),

        "pareto_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "pareto",
                "wrong_family_clause_count",
            )
        ),

        "fixed_wrong_rule_contamination_families": (
            _count(
                rows,
                "fixed",
                "wrong_rule_contamination",
            )
        ),

        "pareto_wrong_rule_contamination_families": (
            _count(
                rows,
                "pareto",
                "wrong_rule_contamination",
            )
        ),

        "mean_fixed_memory_words": (
            _mean(
                row[
                    "fixed"
                ][
                    "memory_word_count"
                ]

                for row
                in rows
            )
        ),

        "mean_pareto_memory_words": (
            _mean(
                row[
                    "pareto"
                ][
                    "memory_word_count"
                ]

                for row
                in rows
            )
        ),

        "mean_fixed_memory_segments": (
            _mean(
                row[
                    "fixed"
                ][
                    "memory_segment_count"
                ]

                for row
                in rows
            )
        ),

        "mean_pareto_memory_segments": (
            _mean(
                row[
                    "pareto"
                ][
                    "memory_segment_count"
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

        "fixed_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="fixed",
            )
        ),

        "pareto_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="pareto",
            )
        ),

        "equal_context_set_pairs": (
            equal_context_pairs
        ),

        "differing_context_set_pairs": (
            differing_context_pairs
        ),

        "reused_equal_context_evaluations": (
            equal_context_pairs
        ),

        "fixed_transfer_model_calls": (
            task_count
        ),

        "pareto_additional_transfer_model_calls": (
            differing_context_pairs
        ),

        "total_transfer_model_calls": (
            task_count
            +
            differing_context_pairs
        ),

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

        "all_retrieval_documents_equal_between_conditions": True,

        "all_channel_scores_equal_between_conditions": True,

        "all_rankings_equal_between_conditions": True,

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

        "only_context_assembly_policy_differs": True,

        "pareto_assembler_model_calls": 0,

        "pareto_assembler_used_family_id": False,

        "pareto_assembler_used_semantic_clause": False,

        "pareto_assembler_used_semantic_grader": False,

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
            "tasks_025.json"
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
        run_experiment_025(
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

        "fixed_target_selected_families",
        "pareto_target_retained_families",
        "target_on_pareto_frontier_families",

        "safe_compaction_families",
        "over_pruning_families",
        "upstream_rank_miss_families",
        "no_change_families",

        "mean_pareto_k",
        "pareto_k_distribution",

        "frontier_class_distribution",
        "frontier_size_distribution",
        "frontier_outside_max_k_families",

        "mean_distractors_before",
        "mean_distractors_after",

        "fixed_task_passes",
        "pareto_task_passes",

        "fixed_target_visible_families",
        "pareto_target_visible_families",

        "fixed_families_with_wrong_memory_presented",
        "pareto_families_with_wrong_memory_presented",

        "fixed_wrong_family_clause_occurrences",
        "pareto_wrong_family_clause_occurrences",

        "fixed_wrong_rule_contamination_families",
        "pareto_wrong_rule_contamination_families",

        "mean_fixed_memory_words",
        "mean_pareto_memory_words",

        "mean_fixed_memory_segments",
        "mean_pareto_memory_segments",

        "task_rescue_families",
        "task_harm_families",

        "visibility_rescue_families",
        "visibility_harm_families",

        "fixed_cluster_metrics",
        "pareto_cluster_metrics",

        "equal_context_set_pairs",
        "differing_context_set_pairs",
        "reused_equal_context_evaluations",

        "total_transfer_model_calls",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "all_candidate_routes_equal_between_conditions",
        "all_retrieval_documents_equal_between_conditions",
        "all_channel_scores_equal_between_conditions",
        "all_rankings_equal_between_conditions",

        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",

        "all_transfer_queries_equal",
        "all_presented_memory_representation_equal",
        "all_context_budget_configuration_equal",
        "all_reasoners_equal",

        "only_context_assembly_policy_differs",

        "pareto_assembler_model_calls",

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
