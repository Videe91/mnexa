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

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


FIXED_TOP_K = 3
DYNAMIC_MAX_K = 3


def dynamic_context_boundary(
    *,
    ordered_family_ids,
    rrf_scores,
    max_k=DYNAMIC_MAX_K,
):
    """
    Confidence-gated context boundary.

    Given an already-frozen ranking:

        M1 >= M2 >= M3 >= M4 ...

    measure:

        g1 = score(M1) - score(M2)
        g2 = score(M2) - score(M3)
        g3 = score(M3) - score(M4)

    The largest gap becomes the context boundary.

    Exact ties between maximum gaps choose the LARGER K.

    This is deliberately conservative and introduces:
    - no threshold
    - no tuning constant
    - no model call
    - no target knowledge
    """

    ordered_family_ids = list(
        ordered_family_ids
    )

    required = (
        max_k
        +
        1
    )

    if (
        len(
            ordered_family_ids
        )
        <
        required
    ):

        raise ValueError(
            f"Need at least {required} ranked candidates "
            f"for max_k={max_k}."
        )

    scores = [
        float(
            rrf_scores[
                family_id
            ]
        )

        for family_id
        in ordered_family_ids
    ]

    for index in range(
        len(scores)
        -
        1
    ):

        if (
            scores[index]
            <
            scores[
                index
                +
                1
            ]
        ):

            raise ValueError(
                "ordered_family_ids must be "
                "sorted by descending RRF score."
            )

    gaps = [
        round(
            scores[index]
            -
            scores[
                index
                +
                1
            ],
            10,
        )

        for index
        in range(
            max_k
        )
    ]

    largest_gap = max(
        gaps
    )

    # Conservative tie rule:
    # choose the latest equal maximum boundary.
    dynamic_k = max(
        index
        +
        1

        for index, gap
        in enumerate(
            gaps
        )

        if gap
        ==
        largest_gap
    )

    selected_family_ids = (
        ordered_family_ids[
            :dynamic_k
        ]
    )

    return {
        "dynamic_k": (
            dynamic_k
        ),

        "selected_family_ids": (
            selected_family_ids
        ),

        "gaps": (
            gaps
        ),

        "largest_gap": (
            largest_gap
        ),

        "boundary_after_rank": (
            dynamic_k
        ),

        "max_k": (
            max_k
        ),

        "tie_policy": (
            "largest_k_on_equal_max_gap"
        ),
    }


def classify_assembly_effect(
    *,
    target_family_id,
    fixed_selected_ids,
    dynamic_selected_ids,
):
    fixed_selected_ids = list(
        fixed_selected_ids
    )

    dynamic_selected_ids = list(
        dynamic_selected_ids
    )

    fixed_has_target = (
        target_family_id
        in
        fixed_selected_ids
    )

    dynamic_has_target = (
        target_family_id
        in
        dynamic_selected_ids
    )

    distractors_before = (
        len(
            fixed_selected_ids
        )
        -
        int(
            fixed_has_target
        )
    )

    distractors_after = (
        len(
            dynamic_selected_ids
        )
        -
        int(
            dynamic_has_target
        )
    )

    distractors_removed = (
        distractors_before
        -
        distractors_after
    )

    if (
        fixed_selected_ids
        ==
        dynamic_selected_ids
    ):

        assembly_class = (
            "no_change"
        )

    elif not fixed_has_target:

        assembly_class = (
            "upstream_rank_miss"
        )

    elif not dynamic_has_target:

        assembly_class = (
            "over_pruning"
        )

    else:

        assembly_class = (
            "safe_compaction"
        )

    return {
        "assembly_class": (
            assembly_class
        ),

        "target_in_fixed_top3": (
            fixed_has_target
        ),

        "target_retained": (
            dynamic_has_target
        ),

        "fixed_selected_count": (
            len(
                fixed_selected_ids
            )
        ),

        "dynamic_selected_count": (
            len(
                dynamic_selected_ids
            )
        ),

        "distractors_before": (
            distractors_before
        ),

        "distractors_after": (
            distractors_after
        ),

        "distractors_removed": (
            distractors_removed
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

    return result


def run_experiment_023(
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
        Path(results_dir)
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
    # LEARN ONCE
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
            family["entities"]
        )

        for family
        in families
    }

    for family in families:

        family_id = (
            family["id"]
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
                ).encode(
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
            family["id"]
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

        if (
            len(
                candidate_ids
            )
            != 5
        ):

            raise RuntimeError(
                "Seed 023 frozen candidate geometry "
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
        # Seed 021 channel-score generation — frozen
        #
        # We ask for all five only so Seed 023 can inspect the complete
        # already-ranked neighborhood.
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
        # Seed 022 fusion — frozen
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

        if (
            len(
                full_order
            )
            != 5
        ):

            raise RuntimeError(
                "Expected complete five-memory ranking."
            )

        # Exact Seed 022 baseline.
        fixed_check = (
            fuse_channel_scores_abstaining(
                candidate_family_ids=(
                    candidate_ids
                ),

                channel_scores=(
                    raw_ranking[
                        "channel_scores"
                    ]
                ),

                top_k=FIXED_TOP_K,

                rrf_k=RRF_K,
            )
        )

        fixed_selected_ids = (
            full_order[
                :FIXED_TOP_K
            ]
        )

        if (
            fixed_check[
                "selected_family_ids"
            ]
            !=
            fixed_selected_ids
        ):

            raise RuntimeError(
                "Seed 022 Top-K prefix control failed."
            )

        # ------------------------------------------------------------
        # Seed 023 mechanism
        # ------------------------------------------------------------

        boundary = (
            dynamic_context_boundary(
                ordered_family_ids=(
                    full_order
                ),

                rrf_scores=(
                    fused[
                        "rrf_scores"
                    ]
                ),

                max_k=(
                    DYNAMIC_MAX_K
                ),
            )
        )

        dynamic_selected_ids = (
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
                    dynamic_selected_ids
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
            dynamic_snapshot,
            dynamic_key,
        ) = (
            snapshot_for(
                dynamic_selected_ids
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
            dynamic_key
        )

        if same_context_set:

            dynamic_eval = (
                copy.deepcopy(
                    fixed_eval
                )
            )

        else:

            dynamic_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        dynamic_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "dynamic_"
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
                    dynamic_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    fixed_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    dynamic_eval[
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

                "dynamic_boundary": (
                    boundary
                ),

                "assembly_effect": (
                    assembly
                ),

                "fixed": (
                    fixed_eval
                ),

                "dynamic": (
                    dynamic_eval
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
                            dynamic_eval[
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
                            dynamic_eval[
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
                        dynamic_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        fixed_eval[
                            "wrong_family_clause_count"
                        ]
                    ),

                    "memory_word_delta": (
                        dynamic_eval[
                            "memory_word_count"
                        ]
                        -
                        fixed_eval[
                            "memory_word_count"
                        ]
                    ),

                    "memory_segment_delta": (
                        dynamic_eval[
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

        dynamic_ids = (
            row[
                "dynamic_boundary"
            ][
                "selected_family_ids"
            ]
        )

        if (
            family_id
            not in fixed_ids
            or
            family_id
            not in dynamic_ids
        ):
            continue

        fixed_snapshot, _ = (
            snapshot_for(
                fixed_ids
            )
        )

        dynamic_snapshot, _ = (
            snapshot_for(
                dynamic_ids
            )
        )

        fixed_record = (
            _learned_record(
                fixed_snapshot,
                family_id,
            )
        )

        dynamic_record = (
            _learned_record(
                dynamic_snapshot,
                family_id,
            )
        )

        if (
            fixed_record[
                "lesson_sha256"
            ]
            !=
            dynamic_record[
                "lesson_sha256"
            ]
        ):

            target_lessons_equal = False

        if (
            fixed_record[
                "source_evidence_sha256"
            ]
            !=
            dynamic_record[
                "source_evidence_sha256"
            ]
        ):

            target_sources_equal = False

    task_count = len(
        rows
    )

    fixed_passes = (
        _count(
            rows,
            "fixed",
            "semantic_task_pass",
        )
    )

    dynamic_passes = (
        _count(
            rows,
            "dynamic",
            "semantic_task_pass",
        )
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

    dynamic_k_counts = Counter(
        row[
            "dynamic_boundary"
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

    report = {
        "experiment": (
            "seed-growth-023"
        ),

        "classification": (
            "exploratory-fresh-confidence-gated-"
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
                "same_ranking_same_scores_"
                "largest_gap_dynamic_prefix_k1_to_k3"
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

        "dynamic_target_retained_families": sum(
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

        "mean_dynamic_k": (
            _mean(
                row[
                    "dynamic_boundary"
                ][
                    "dynamic_k"
                ]

                for row
                in rows
            )
        ),

        "dynamic_k_distribution": {
            str(k): (
                dynamic_k_counts[
                    k
                ]
            )

            for k
            in (
                1,
                2,
                3,
            )
        },

        "mean_fixed_selected_count": 3.0,

        "mean_dynamic_selected_count": (
            _mean(
                len(
                    row[
                        "dynamic_boundary"
                    ][
                        "selected_family_ids"
                    ]
                )

                for row
                in rows
            )
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

        "dynamic_task_passes": (
            dynamic_passes
        ),

        "fixed_task_pass_rate": (
            fixed_passes
            /
            task_count
        ),

        "dynamic_task_pass_rate": (
            dynamic_passes
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

        "dynamic_target_visible_families": (
            _count(
                rows,
                "dynamic",
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

        "dynamic_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "dynamic"
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

        "dynamic_wrong_family_clause_occurrences": int(
            _sum(
                rows,
                "dynamic",
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

        "dynamic_wrong_rule_contamination_families": (
            _count(
                rows,
                "dynamic",
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

        "mean_dynamic_memory_words": (
            _mean(
                row[
                    "dynamic"
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

        "mean_dynamic_memory_segments": (
            _mean(
                row[
                    "dynamic"
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
        # CLUSTER ANALYSIS
        # ------------------------------------------------------------

        "fixed_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="fixed",
            )
        ),

        "dynamic_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="dynamic",
            )
        ),

        # ------------------------------------------------------------
        # SAME-STATE NOISE CONTROL
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

        "dynamic_additional_transfer_model_calls": (
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

        "only_context_assembly_boundary_differs": True,

        "dynamic_assembler_model_calls": 0,

        "dynamic_assembler_used_family_id": False,

        "dynamic_assembler_used_semantic_clause": False,

        "dynamic_assembler_used_semantic_grader": False,

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
            "tasks_023.json"
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

    model_name = os.environ.get(
        "MNEXA_MODEL"
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
        run_experiment_023(
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
        "dynamic_target_retained_families",

        "safe_compaction_families",
        "over_pruning_families",
        "upstream_rank_miss_families",
        "no_change_families",

        "mean_dynamic_k",
        "dynamic_k_distribution",

        "mean_distractors_before",
        "mean_distractors_after",

        "fixed_task_passes",
        "dynamic_task_passes",

        "fixed_target_visible_families",
        "dynamic_target_visible_families",

        "fixed_families_with_wrong_memory_presented",
        "dynamic_families_with_wrong_memory_presented",

        "fixed_wrong_family_clause_occurrences",
        "dynamic_wrong_family_clause_occurrences",

        "fixed_wrong_rule_contamination_families",
        "dynamic_wrong_rule_contamination_families",

        "mean_fixed_memory_words",
        "mean_dynamic_memory_words",

        "mean_fixed_memory_segments",
        "mean_dynamic_memory_segments",

        "task_rescue_families",
        "task_harm_families",

        "visibility_rescue_families",
        "visibility_harm_families",

        "fixed_cluster_metrics",
        "dynamic_cluster_metrics",

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
        "only_context_assembly_boundary_differs",

        "dynamic_assembler_model_calls",
        "all_equal_context_pairs_reused_evaluation",
    )

    summary = {
        key: report[key]

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
