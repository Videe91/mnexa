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


def channel_top_winners(
    *,
    channel_ranks,
    active_channels,
):
    """
    Return every top-ranked candidate for each active channel.

    Exact ties are preserved.

    Example:

        semantic ranks:
            A = 1.5
            B = 1.5
            C = 3

        winners:
            [A, B]

    Abstained channels are excluded by active_channels.
    """

    winners = {}

    for channel in active_channels:

        ranks = (
            channel_ranks[
                channel
            ]
        )

        valid = {
            family_id: float(rank)

            for family_id, rank
            in ranks.items()

            if rank is not None
        }

        if not valid:
            continue

        best_rank = min(
            valid.values()
        )

        winners[
            channel
        ] = [
            family_id

            for family_id, rank
            in valid.items()

            if rank == best_rank
        ]

    return winners


def consensus_context_boundary(
    *,
    ordered_family_ids,
    channel_ranks,
    active_channels,
    max_k=DYNAMIC_MAX_K,
):
    """
    Channel-consensus context assembly.

    Principle:

        Agreement permits compression.
        Disagreement preserves breadth.

    Procedure:

    1. Determine the top winner(s) of each active retrieval channel.
    2. Find those winners' positions in the frozen fused ordering.
    3. Select the smallest fused prefix that preserves all winners
       when they are within max_k.
    4. If a winner is outside max_k, conservatively retain max_k.
    5. If no active channel exists, retain max_k.

    No score threshold, model call, target ID, grader, or expected
    answer is used.
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

    position = {
        family_id: index + 1

        for index, family_id
        in enumerate(
            ordered_family_ids
        )
    }

    winners_by_channel = (
        channel_top_winners(
            channel_ranks=(
                channel_ranks
            ),
            active_channels=(
                active_channels
            ),
        )
    )

    winner_ids = []

    for channel in active_channels:

        for family_id in (
            winners_by_channel.get(
                channel,
                []
            )
        ):

            if family_id not in position:

                raise ValueError(
                    "Channel winner absent from "
                    "fused ordering: "
                    f"{family_id}"
                )

            if family_id not in winner_ids:

                winner_ids.append(
                    family_id
                )

    if not winner_ids:

        dynamic_k = max_k

        consensus_class = (
            "no_active_channels"
        )

        winner_outside_max_k = False

    else:

        winner_positions = [
            position[
                family_id
            ]

            for family_id
            in winner_ids
        ]

        winner_outside_max_k = any(
            winner_position
            >
            max_k

            for winner_position
            in winner_positions
        )

        if winner_outside_max_k:

            dynamic_k = max_k

            consensus_class = (
                "winner_outside_max_k"
            )

        else:

            dynamic_k = max(
                winner_positions
            )

            if len(
                winner_ids
            ) == 1:

                consensus_class = (
                    "full_agreement"
                )

            else:

                consensus_class = (
                    "channel_disagreement"
                )

    selected = (
        ordered_family_ids[
            :dynamic_k
        ]
    )

    return {
        "dynamic_k": (
            dynamic_k
        ),

        "selected_family_ids": (
            selected
        ),

        "channel_winners": (
            winners_by_channel
        ),

        "channel_winner_family_ids": (
            winner_ids
        ),

        "channel_winner_positions": {
            family_id: position[
                family_id
            ]

            for family_id
            in winner_ids
        },

        "active_channel_count": (
            len(
                active_channels
            )
        ),

        "winner_outside_max_k": (
            winner_outside_max_k
        ),

        "consensus_class": (
            consensus_class
        ),

        "max_k": (
            max_k
        ),

        "policy": (
            "smallest_fused_prefix_containing_"
            "all_active_channel_top_winners"
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

        if family_id in selected
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

        bucket = grouped[
            cluster
        ]

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


def run_experiment_024(
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

    # ================================================================
    # AUTHORITATIVE PRESENTATION SNAPSHOT CACHE
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
                "Assembled memory context "
                "may not be empty."
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

        # ------------------------------------------------------------
        # Seed 020 routing — frozen
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

        if len(
            candidate_ids
        ) != 5:

            raise RuntimeError(
                "Seed 024 candidate geometry "
                f"violated for {family_id}: "
                f"{len(candidate_ids)}"
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
        # Seed 021 channel scoring — frozen
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # Seed 022 abstaining fusion — frozen
        # ------------------------------------------------------------

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

        if len(
            full_order
        ) != 5:

            raise RuntimeError(
                "Expected complete five-memory "
                "fused ordering."
            )

        fixed_selected_ids = (
            full_order[
                :FIXED_TOP_K
            ]
        )

        # ------------------------------------------------------------
        # Seed 024 mechanism
        # ------------------------------------------------------------

        boundary = (
            consensus_context_boundary(
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

        consensus_selected_ids = (
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
                    consensus_selected_ids
                ),
            )
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
            consensus_snapshot,
            consensus_key,
        ) = (
            snapshot_for(
                consensus_selected_ids
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
            consensus_key
        )

        if same_context_set:

            consensus_eval = (
                copy.deepcopy(
                    fixed_eval
                )
            )

        else:

            consensus_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        consensus_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "consensus_"
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
                    consensus_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    fixed_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    consensus_eval[
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

                "consensus_boundary": (
                    boundary
                ),

                "assembly_effect": (
                    assembly
                ),

                "fixed": (
                    fixed_eval
                ),

                "consensus": (
                    consensus_eval
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
                            consensus_eval[
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
                            consensus_eval[
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
                        consensus_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        fixed_eval[
                            "wrong_family_clause_count"
                        ]
                    ),

                    "memory_word_delta": (
                        consensus_eval[
                            "memory_word_count"
                        ]
                        -
                        fixed_eval[
                            "memory_word_count"
                        ]
                    ),

                    "memory_segment_delta": (
                        consensus_eval[
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

    # ================================================================
    # TARGET MEMORY CONTROLS
    # ================================================================

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

        consensus_ids = (
            row[
                "consensus_boundary"
            ][
                "selected_family_ids"
            ]
        )

        if (
            family_id not in fixed_ids
            or
            family_id not in consensus_ids
        ):

            continue

        fixed_snapshot, _ = (
            snapshot_for(
                fixed_ids
            )
        )

        consensus_snapshot, _ = (
            snapshot_for(
                consensus_ids
            )
        )

        fixed_record = (
            _learned_record(
                fixed_snapshot,
                family_id,
            )
        )

        consensus_record = (
            _learned_record(
                consensus_snapshot,
                family_id,
            )
        )

        if (
            fixed_record[
                "lesson_sha256"
            ]
            !=
            consensus_record[
                "lesson_sha256"
            ]
        ):

            target_lessons_equal = False

        if (
            fixed_record[
                "source_evidence_sha256"
            ]
            !=
            consensus_record[
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

    consensus_classes = Counter(
        row[
            "consensus_boundary"
        ][
            "consensus_class"
        ]

        for row
        in rows
    )

    k_counts = Counter(
        row[
            "consensus_boundary"
        ][
            "dynamic_k"
        ]

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

    consensus_passes = (
        _count(
            rows,
            "consensus",
            "semantic_task_pass",
        )
    )

    report = {
        "experiment": (
            "seed-growth-024"
        ),

        "classification": (
            "exploratory-fresh-channel-consensus-"
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
            len(
                families
            )
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
                "same_ranking_channel_winner_"
                "preserving_consensus_prefix"
            ),
        },

        # ------------------------------------------------------------
        # ASSEMBLY
        # ------------------------------------------------------------

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

        "consensus_target_retained_families": sum(
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

        "mean_consensus_k": (
            _mean(
                row[
                    "consensus_boundary"
                ][
                    "dynamic_k"
                ]

                for row
                in rows
            )
        ),

        "consensus_k_distribution": {
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

        "consensus_class_distribution": (
            dict(
                sorted(
                    consensus_classes.items()
                )
            )
        ),

        "winner_outside_max_k_families": sum(
            int(
                row[
                    "consensus_boundary"
                ][
                    "winner_outside_max_k"
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

        # ------------------------------------------------------------
        # DOWNSTREAM
        # ------------------------------------------------------------

        "fixed_task_passes": (
            fixed_passes
        ),

        "consensus_task_passes": (
            consensus_passes
        ),

        "fixed_task_pass_rate": (
            fixed_passes
            /
            task_count
        ),

        "consensus_task_pass_rate": (
            consensus_passes
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

        "consensus_target_visible_families": (
            _count(
                rows,
                "consensus",
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

        "consensus_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "consensus"
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

        "consensus_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "consensus",
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

        "consensus_wrong_rule_contamination_families": (
            _count(
                rows,
                "consensus",
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

        "mean_consensus_memory_words": (
            _mean(
                row[
                    "consensus"
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

        "mean_consensus_memory_segments": (
            _mean(
                row[
                    "consensus"
                ][
                    "memory_segment_count"
                ]

                for row
                in rows
            )
        ),

        # ------------------------------------------------------------
        # PAIRED BEHAVIOR
        # ------------------------------------------------------------

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
        # CLUSTERS
        # ------------------------------------------------------------

        "fixed_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="fixed",
            )
        ),

        "consensus_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="consensus",
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

        "fixed_transfer_model_calls": (
            task_count
        ),

        "consensus_additional_transfer_model_calls": (
            differing_context_pairs
        ),

        "total_transfer_model_calls": (
            task_count
            +
            differing_context_pairs
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
        # CONTROLS
        # ------------------------------------------------------------

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

        "consensus_assembler_model_calls": 0,

        "consensus_assembler_used_family_id": False,

        "consensus_assembler_used_semantic_clause": False,

        "consensus_assembler_used_semantic_grader": False,

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
            "tasks_024.json"
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
        run_experiment_024(
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
        "consensus_target_retained_families",

        "safe_compaction_families",
        "over_pruning_families",
        "upstream_rank_miss_families",
        "no_change_families",

        "mean_consensus_k",
        "consensus_k_distribution",
        "consensus_class_distribution",
        "winner_outside_max_k_families",

        "mean_distractors_before",
        "mean_distractors_after",

        "fixed_task_passes",
        "consensus_task_passes",

        "fixed_target_visible_families",
        "consensus_target_visible_families",

        "fixed_families_with_wrong_memory_presented",
        "consensus_families_with_wrong_memory_presented",

        "fixed_wrong_family_clause_occurrences",
        "consensus_wrong_family_clause_occurrences",

        "fixed_wrong_rule_contamination_families",
        "consensus_wrong_rule_contamination_families",

        "mean_fixed_memory_words",
        "mean_consensus_memory_words",

        "mean_fixed_memory_segments",
        "mean_consensus_memory_segments",

        "task_rescue_families",
        "task_harm_families",

        "visibility_rescue_families",
        "visibility_harm_families",

        "fixed_cluster_metrics",
        "consensus_cluster_metrics",

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

        "consensus_assembler_model_calls",

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
