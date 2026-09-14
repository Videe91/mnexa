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

from experiments.seed_growth_026 import (
    proposition_local_channel_scores,
    proposition_units_from_retrieval_index,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


TOP_K = 3
MIN_ACTIVE_CHANNELS = 2


def quorum_context_boundary(
    *,
    ordered_family_ids,
    channel_ranks,
    active_channels,
    max_k=TOP_K,
    min_active_channels=MIN_ACTIVE_CHANNELS,
):
    """
    Evidence-quorum attention guard.

    Principle:

        One signal may rank.
        Multiple distinct active signals are required to prune.

    If fewer than min_active_channels remain active after channel
    abstention, preserve the fused Top-K baseline.

    Otherwise delegate unchanged to Seed 025 Pareto-safe assembly.

    No target identity, grader, answer, model call, or confidence
    threshold is used.
    """

    ordered_family_ids = list(
        ordered_family_ids
    )

    active_channels = list(
        active_channels
    )

    if len(
        ordered_family_ids
    ) < max_k:

        raise ValueError(
            "Fused ordering contains fewer "
            "candidates than max_k."
        )

    if min_active_channels < 1:

        raise ValueError(
            "min_active_channels must be >= 1."
        )

    active_channel_count = len(
        active_channels
    )

    quorum_met = (
        active_channel_count
        >=
        min_active_channels
    )

    if not quorum_met:

        return {
            "dynamic_k": (
                max_k
            ),

            "selected_family_ids": (
                ordered_family_ids[
                    :max_k
                ]
            ),

            "active_channel_count": (
                active_channel_count
            ),

            "active_channels": (
                active_channels
            ),

            "min_active_channels": (
                min_active_channels
            ),

            "quorum_met": False,

            "guard_mode": (
                "insufficient_channel_quorum"
            ),

            "pareto_delegated": False,

            "frontier_family_ids": [],

            "dominated_family_ids": [],

            "dominators_by_family": {},

            "frontier_positions": {},

            "frontier_outside_max_k": False,

            "frontier_class": (
                "quorum_guard_preserved_top_k"
            ),

            "max_k": (
                max_k
            ),

            "policy": (
                "evidence_quorum_guarded_pareto"
            ),
        }

    pareto = (
        pareto_context_boundary(
            ordered_family_ids=(
                ordered_family_ids
            ),

            channel_ranks=(
                channel_ranks
            ),

            active_channels=(
                active_channels
            ),

            max_k=(
                max_k
            ),
        )
    )

    return {
        **pareto,

        "active_channel_count": (
            active_channel_count
        ),

        "active_channels": (
            active_channels
        ),

        "min_active_channels": (
            min_active_channels
        ),

        "quorum_met": True,

        "guard_mode": (
            "pareto_with_channel_quorum"
        ),

        "pareto_delegated": True,

        "policy": (
            "evidence_quorum_guarded_pareto"
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


def _assembly_count(
    rows,
    condition,
    assembly_class,
):
    key = (
        condition
        +
        "_assembly"
    )

    return sum(
        int(
            row[
                key
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
            "subquorum_families": 0,
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
                "target_in_top3"
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
            "subquorum_families"
        ] += int(
            row[
                "active_channel_count"
            ]
            <
            MIN_ACTIVE_CHANNELS
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


def run_experiment_027(
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
    # ONE SHARED RANKING, TWO ASSEMBLY POLICIES
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
                "Seed 027 candidate geometry "
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
        # Seed 026 proposition-local scoring — shared by A and B
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

        fused = (
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

        fixed_top3 = (
            full_order[
                :TOP_K
            ]
        )

        target_in_top3 = (
            family_id
            in fixed_top3
        )

        active_channels = list(
            fused[
                "active_channels"
            ]
        )

        active_channel_count = len(
            active_channels
        )

        # ------------------------------------------------------------
        # CONDITION A
        # Existing Seed 025 Pareto assembly.
        # ------------------------------------------------------------

        pareto_boundary = (
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
                    active_channels
                ),

                max_k=TOP_K,
            )
        )

        pareto_selected = (
            pareto_boundary[
                "selected_family_ids"
            ]
        )

        pareto_assembly = (
            classify_assembly_effect(
                target_family_id=(
                    family_id
                ),

                fixed_selected_ids=(
                    fixed_top3
                ),

                dynamic_selected_ids=(
                    pareto_selected
                ),
            )
        )

        # ------------------------------------------------------------
        # CONDITION B
        # Same Pareto rule, but only when active-channel quorum exists.
        # ------------------------------------------------------------

        quorum_boundary = (
            quorum_context_boundary(
                ordered_family_ids=(
                    full_order
                ),

                channel_ranks=(
                    fused[
                        "channel_ranks"
                    ]
                ),

                active_channels=(
                    active_channels
                ),

                max_k=TOP_K,

                min_active_channels=(
                    MIN_ACTIVE_CHANNELS
                ),
            )
        )

        quorum_selected = (
            quorum_boundary[
                "selected_family_ids"
            ]
        )

        quorum_assembly = (
            classify_assembly_effect(
                target_family_id=(
                    family_id
                ),

                fixed_selected_ids=(
                    fixed_top3
                ),

                dynamic_selected_ids=(
                    quorum_selected
                ),
            )
        )

        pareto_target_retained = (
            family_id
            in pareto_selected
        )

        quorum_target_retained = (
            family_id
            in quorum_selected
        )

        (
            pareto_snapshot,
            pareto_key,
        ) = (
            snapshot_for(
                pareto_selected
            )
        )

        (
            quorum_snapshot,
            quorum_key,
        ) = (
            snapshot_for(
                quorum_selected
            )
        )

        eval_family = (
            evaluation_family(
                family
            )
        )

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

        same_context_set = (
            pareto_key
            ==
            quorum_key
        )

        if same_context_set:

            quorum_eval = (
                copy.deepcopy(
                    pareto_eval
                )
            )

        else:

            quorum_eval = (
                evaluate_snapshot(
                    snapshot_path=Path(
                        quorum_snapshot[
                            "db_path"
                        ]
                    ),

                    eval_db_path=(
                        eval_dir
                        /
                        (
                            "quorum_"
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
                    pareto_eval[
                        "semantic_task_pass"
                    ]
                ),

                handle_pass=(
                    quorum_eval[
                        "semantic_task_pass"
                    ]
                ),

                full_visible=(
                    pareto_eval[
                        "target_clause_visible"
                    ]
                ),

                handle_visible=(
                    quorum_eval[
                        "target_clause_visible"
                    ]
                ),
            )
        )

        subquorum = (
            active_channel_count
            <
            MIN_ACTIVE_CHANNELS
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
                    local_raw[
                        "channel_scores"
                    ]
                ),

                "best_proposition_units": (
                    local_raw[
                        "best_units"
                    ]
                ),

                "fusion": (
                    fused
                ),

                "full_order": (
                    full_order
                ),

                "fixed_top3": (
                    fixed_top3
                ),

                "target_in_top3": (
                    target_in_top3
                ),

                "active_channels": (
                    active_channels
                ),

                "active_channel_count": (
                    active_channel_count
                ),

                "subquorum": (
                    subquorum
                ),

                "pareto_boundary": (
                    pareto_boundary
                ),

                "quorum_boundary": (
                    quorum_boundary
                ),

                "pareto_assembly": (
                    pareto_assembly
                ),

                "quorum_assembly": (
                    quorum_assembly
                ),

                "pareto_target_retained": (
                    pareto_target_retained
                ),

                "quorum_target_retained": (
                    quorum_target_retained
                ),

                "pareto": (
                    pareto_eval
                ),

                "quorum": (
                    quorum_eval
                ),

                "paired": {
                    **behavioral_effect,

                    "context_sets_equal": (
                        same_context_set
                    ),

                    "evaluation_reused": (
                        same_context_set
                    ),

                    "quorum_context_expansion": (
                        len(
                            quorum_selected
                        )
                        >
                        len(
                            pareto_selected
                        )
                    ),

                    "quorum_target_rescue": (
                        target_in_top3
                        and
                        (
                            not
                            pareto_target_retained
                        )
                        and
                        quorum_target_retained
                    ),

                    "quorum_target_harm": (
                        pareto_target_retained
                        and
                        (
                            not
                            quorum_target_retained
                        )
                    ),

                    "task_delta": (
                        int(
                            quorum_eval[
                                "semantic_task_pass"
                            ]
                        )
                        -
                        int(
                            pareto_eval[
                                "semantic_task_pass"
                            ]
                        )
                    ),

                    "visibility_delta": (
                        int(
                            quorum_eval[
                                "target_clause_visible"
                            ]
                        )
                        -
                        int(
                            pareto_eval[
                                "target_clause_visible"
                            ]
                        )
                    ),

                    "wrong_clause_delta": (
                        quorum_eval[
                            "wrong_family_clause_count"
                        ]
                        -
                        pareto_eval[
                            "wrong_family_clause_count"
                        ]
                    ),

                    "memory_word_delta": (
                        quorum_eval[
                            "memory_word_count"
                        ]
                        -
                        pareto_eval[
                            "memory_word_count"
                        ]
                    ),

                    "memory_segment_delta": (
                        quorum_eval[
                            "memory_segment_count"
                        ]
                        -
                        pareto_eval[
                            "memory_segment_count"
                        ]
                    ),
                },
            }
        )

    # ================================================================
    # AGGREGATE
    # ================================================================

    task_count = len(
        rows
    )

    active_channel_distribution = Counter(
        row[
            "active_channel_count"
        ]

        for row
        in rows
    )

    pareto_k_distribution = Counter(
        len(
            row[
                "pareto_boundary"
            ][
                "selected_family_ids"
            ]
        )

        for row
        in rows
    )

    quorum_k_distribution = Counter(
        len(
            row[
                "quorum_boundary"
            ][
                "selected_family_ids"
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

    subquorum_rows = [
        row

        for row
        in rows

        if row[
            "subquorum"
        ]
    ]

    report = {
        "experiment": (
            "seed-growth-027"
        ),

        "classification": (
            "exploratory-fresh-evidence-quorum-"
            "attention-ablation"
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

        "min_active_channels_for_pruning": (
            MIN_ACTIVE_CHANNELS
        ),

        "conditions": {
            "A": (
                "seed_026_proposition_local_"
                "plus_pareto"
            ),

            "B": (
                "same_ranking_plus_evidence_"
                "quorum_guarded_pareto"
            ),
        },

        # ------------------------------------------------------------
        # SHARED RANKING
        # ------------------------------------------------------------

        "target_top3_families": sum(
            int(
                row[
                    "target_in_top3"
                ]
            )

            for row
            in rows
        ),

        "active_channel_count_distribution": {
            str(
                count
            ): (
                active_channel_distribution[
                    count
                ]
            )

            for count
            in sorted(
                active_channel_distribution
            )
        },

        "subquorum_families": (
            len(
                subquorum_rows
            )
        ),

        "quorum_met_families": (
            task_count
            -
            len(
                subquorum_rows
            )
        ),

        # ------------------------------------------------------------
        # TARGET RETENTION
        # ------------------------------------------------------------

        "pareto_target_retained_families": sum(
            int(
                row[
                    "pareto_target_retained"
                ]
            )

            for row
            in rows
        ),

        "quorum_target_retained_families": sum(
            int(
                row[
                    "quorum_target_retained"
                ]
            )

            for row
            in rows
        ),

        "pareto_over_pruning_families": (
            _assembly_count(
                rows,
                "pareto",
                "over_pruning",
            )
        ),

        "quorum_over_pruning_families": (
            _assembly_count(
                rows,
                "quorum",
                "over_pruning",
            )
        ),

        "pareto_upstream_rank_miss_families": (
            _assembly_count(
                rows,
                "pareto",
                "upstream_rank_miss",
            )
        ),

        "quorum_upstream_rank_miss_families": (
            _assembly_count(
                rows,
                "quorum",
                "upstream_rank_miss",
            )
        ),

        "pareto_safe_compaction_families": (
            _assembly_count(
                rows,
                "pareto",
                "safe_compaction",
            )
        ),

        "quorum_safe_compaction_families": (
            _assembly_count(
                rows,
                "quorum",
                "safe_compaction",
            )
        ),

        "quorum_target_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "quorum_target_rescue"
                ]
            )

            for row
            in rows
        ),

        "quorum_target_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "quorum_target_harm"
                ]
            )

            for row
            in rows
        ),

        # ------------------------------------------------------------
        # SUBQUORUM MECHANISM
        # ------------------------------------------------------------

        "subquorum_target_top3_families": sum(
            int(
                row[
                    "target_in_top3"
                ]
            )

            for row
            in subquorum_rows
        ),

        "subquorum_pareto_target_retained_families": sum(
            int(
                row[
                    "pareto_target_retained"
                ]
            )

            for row
            in subquorum_rows
        ),

        "subquorum_quorum_target_retained_families": sum(
            int(
                row[
                    "quorum_target_retained"
                ]
            )

            for row
            in subquorum_rows
        ),

        "subquorum_pareto_task_passes": sum(
            int(
                row[
                    "pareto"
                ][
                    "semantic_task_pass"
                ]
            )

            for row
            in subquorum_rows
        ),

        "subquorum_quorum_task_passes": sum(
            int(
                row[
                    "quorum"
                ][
                    "semantic_task_pass"
                ]
            )

            for row
            in subquorum_rows
        ),

        # ------------------------------------------------------------
        # CONTEXT SIZE
        # ------------------------------------------------------------

        "mean_pareto_context_k": (
            _mean(
                len(
                    row[
                        "pareto_boundary"
                    ][
                        "selected_family_ids"
                    ]
                )

                for row
                in rows
            )
        ),

        "mean_quorum_context_k": (
            _mean(
                len(
                    row[
                        "quorum_boundary"
                    ][
                        "selected_family_ids"
                    ]
                )

                for row
                in rows
            )
        ),

        "pareto_k_distribution": {
            str(k): (
                pareto_k_distribution[
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

        "quorum_k_distribution": {
            str(k): (
                quorum_k_distribution[
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

        "quorum_context_expansion_families": sum(
            int(
                row[
                    "paired"
                ][
                    "quorum_context_expansion"
                ]
            )

            for row
            in rows
        ),

        # ------------------------------------------------------------
        # DOWNSTREAM
        # ------------------------------------------------------------

        "pareto_task_passes": (
            _count(
                rows,
                "pareto",
                "semantic_task_pass",
            )
        ),

        "quorum_task_passes": (
            _count(
                rows,
                "quorum",
                "semantic_task_pass",
            )
        ),

        "pareto_target_visible_families": (
            _count(
                rows,
                "pareto",
                "target_clause_visible",
            )
        ),

        "quorum_target_visible_families": (
            _count(
                rows,
                "quorum",
                "target_clause_visible",
            )
        ),

        "pareto_families_with_wrong_memory": sum(
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

        "quorum_families_with_wrong_memory": sum(
            int(
                row[
                    "quorum"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "pareto_wrong_clause_occurrences": int(
            _sum(
                rows,
                "pareto",
                "wrong_family_clause_count",
            )
        ),

        "quorum_wrong_clause_occurrences": int(
            _sum(
                rows,
                "quorum",
                "wrong_family_clause_count",
            )
        ),

        "pareto_wrong_rule_contamination_families": (
            _count(
                rows,
                "pareto",
                "wrong_rule_contamination",
            )
        ),

        "quorum_wrong_rule_contamination_families": (
            _count(
                rows,
                "quorum",
                "wrong_rule_contamination",
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

        "mean_quorum_memory_words": (
            _mean(
                row[
                    "quorum"
                ][
                    "memory_word_count"
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

        "mean_quorum_memory_segments": (
            _mean(
                row[
                    "quorum"
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

        # ------------------------------------------------------------
        # CLUSTERS
        # ------------------------------------------------------------

        "pareto_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="pareto",
            )
        ),

        "quorum_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="quorum",
            )
        ),

        # ------------------------------------------------------------
        # SAME STATE
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

        "pareto_transfer_model_calls": (
            task_count
        ),

        "quorum_additional_transfer_model_calls": (
            differing_context_pairs
        ),

        "total_transfer_model_calls": (
            task_count
            +
            differing_context_pairs
        ),

        # ------------------------------------------------------------
        # SAFETY
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

        "all_proposition_units_shared_between_conditions": True,

        "all_channel_scores_equal_between_conditions": True,

        "all_channel_abstentions_equal_between_conditions": True,

        "all_fused_rankings_equal_between_conditions": True,

        "same_retrieval_policy_between_conditions": True,

        "same_fusion_policy_between_conditions": True,

        "same_authoritative_presentation_representation": True,

        "same_transfer_queries": True,

        "same_reasoner": True,

        "same_context_budget_configuration": True,

        "only_context_assembly_safety_rule_differs": True,

        "ranker_model_calls": 0,

        "pareto_assembler_model_calls": 0,

        "quorum_assembler_model_calls": 0,

        "quorum_assembler_used_family_id": False,

        "quorum_assembler_used_semantic_clause": False,

        "quorum_assembler_used_semantic_grader": False,

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
            "tasks_027.json"
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
        run_experiment_027(
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

        "target_top3_families",

        "active_channel_count_distribution",
        "subquorum_families",
        "quorum_met_families",

        "pareto_target_retained_families",
        "quorum_target_retained_families",

        "pareto_over_pruning_families",
        "quorum_over_pruning_families",

        "pareto_upstream_rank_miss_families",
        "quorum_upstream_rank_miss_families",

        "pareto_safe_compaction_families",
        "quorum_safe_compaction_families",

        "quorum_target_rescue_families",
        "quorum_target_harm_families",

        "subquorum_target_top3_families",
        "subquorum_pareto_target_retained_families",
        "subquorum_quorum_target_retained_families",

        "subquorum_pareto_task_passes",
        "subquorum_quorum_task_passes",

        "mean_pareto_context_k",
        "mean_quorum_context_k",

        "pareto_k_distribution",
        "quorum_k_distribution",

        "quorum_context_expansion_families",

        "pareto_task_passes",
        "quorum_task_passes",

        "pareto_target_visible_families",
        "quorum_target_visible_families",

        "pareto_families_with_wrong_memory",
        "quorum_families_with_wrong_memory",

        "pareto_wrong_clause_occurrences",
        "quorum_wrong_clause_occurrences",

        "pareto_wrong_rule_contamination_families",
        "quorum_wrong_rule_contamination_families",

        "mean_pareto_memory_words",
        "mean_quorum_memory_words",

        "mean_pareto_memory_segments",
        "mean_quorum_memory_segments",

        "task_rescue_families",
        "task_harm_families",

        "visibility_rescue_families",
        "visibility_harm_families",

        "pareto_cluster_metrics",
        "quorum_cluster_metrics",

        "equal_context_set_pairs",
        "differing_context_set_pairs",
        "reused_equal_context_evaluations",

        "bundle_unsupported_claims_admitted",

        "all_candidate_routes_equal_between_conditions",
        "all_memory_bundles_shared_between_conditions",
        "all_source_evidence_shared_between_conditions",
        "all_proposition_units_shared_between_conditions",
        "all_channel_scores_equal_between_conditions",
        "all_channel_abstentions_equal_between_conditions",
        "all_fused_rankings_equal_between_conditions",

        "same_retrieval_policy_between_conditions",
        "same_fusion_policy_between_conditions",
        "same_authoritative_presentation_representation",
        "same_transfer_queries",
        "same_reasoner",

        "only_context_assembly_safety_rule_differs",

        "ranker_model_calls",
        "quorum_assembler_model_calls",

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
