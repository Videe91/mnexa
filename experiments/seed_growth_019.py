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

from experiments.seed_growth_018 import (
    posthoc_candidate_metrics,
    select_identity_candidates,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


HIERARCHY = (
    (
        "code",
        "code:",
    ),
    (
        "system",
        "system:",
    ),
    (
        "cluster",
        "cluster:",
    ),
    (
        "domain",
        "domain:",
    ),
)


def _entities_for_prefix(
    entities,
    prefix,
):
    return {
        entity

        for entity
        in entities

        if (
            isinstance(
                entity,
                str,
            )
            and
            entity.startswith(
                prefix
            )
        )
    }


def select_hierarchical_candidates(
    *,
    query_entities,
    families,
):
    """
    Addressing degrades from precise to broad:

        code
        system
        cluster
        domain
        global fallback

    The first tier with at least one exact match wins.

    The selector sees only query/memory metadata.
    """

    for (
        tier_name,
        prefix,
    ) in HIERARCHY:

        query_values = (
            _entities_for_prefix(
                query_entities,
                prefix,
            )
        )

        if not query_values:
            continue

        candidate_ids = []
        matched_entities = {}

        for family in families:

            family_values = (
                _entities_for_prefix(
                    family.get(
                        "entities",
                        [],
                    ),
                    prefix,
                )
            )

            overlap = sorted(
                query_values
                &
                family_values
            )

            if not overlap:
                continue

            family_id = family[
                "id"
            ]

            candidate_ids.append(
                family_id
            )

            matched_entities[
                family_id
            ] = overlap

        if candidate_ids:

            return {
                "selection_tier": (
                    tier_name
                ),

                "candidate_family_ids": (
                    candidate_ids
                ),

                "candidate_count": (
                    len(
                        candidate_ids
                    )
                ),

                "matched_entities": (
                    matched_entities
                ),

                "fallback_used": False,
            }

    candidate_ids = [
        family["id"]

        for family
        in families
    ]

    return {
        "selection_tier": (
            "global"
        ),

        "candidate_family_ids": (
            candidate_ids
        ),

        "candidate_count": (
            len(
                candidate_ids
            )
        ),

        "matched_entities": {},

        "fallback_used": True,
    }


def classify_hierarchical_effect(
    *,
    current_pass,
    hierarchical_pass,
    current_visible,
    hierarchical_visible,
):
    return {
        "task_rescue": (
            (not current_pass)
            and
            hierarchical_pass
        ),

        "task_harm": (
            current_pass
            and
            (not hierarchical_pass)
        ),

        "visibility_rescue": (
            (not current_visible)
            and
            hierarchical_visible
        ),

        "visibility_harm": (
            current_visible
            and
            (not hierarchical_visible)
        ),
    }


def aggregate_mode_metrics(
    rows,
    *,
    condition,
    selection_key,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "task_passes": 0,
            "target_visible_families": 0,
            "wrong_family_clause_occurrences": 0,
            "families_with_wrong_memory": 0,
            "precision_sum": 0.0,
            "recall_sum": 0.0,
            "candidate_count_sum": 0.0,
            "fallback_queries": 0,
        }
    )

    for row in rows:

        mode = row[
            "degradation_mode"
        ]

        metrics = row[
            condition
        ]

        selection = row[
            selection_key
        ]

        bucket = grouped[
            mode
        ]

        bucket[
            "families"
        ] += 1

        bucket[
            "task_passes"
        ] += int(
            metrics[
                "semantic_task_pass"
            ]
        )

        bucket[
            "target_visible_families"
        ] += int(
            metrics[
                "target_clause_visible"
            ]
        )

        wrong = int(
            metrics[
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

        bucket[
            "precision_sum"
        ] += float(
            metrics[
                "retrieval_precision"
            ]
        )

        bucket[
            "recall_sum"
        ] += float(
            metrics[
                "retrieval_recall"
            ]
        )

        bucket[
            "candidate_count_sum"
        ] += float(
            selection[
                "candidate_count"
            ]
        )

        bucket[
            "fallback_queries"
        ] += int(
            selection[
                "fallback_used"
            ]
        )

    result = {}

    for (
        mode,
        bucket,
    ) in sorted(
        grouped.items()
    ):

        families = bucket[
            "families"
        ]

        result[
            mode
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
                if families
                else 0.0
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

            "mean_retrieval_precision": (
                bucket[
                    "precision_sum"
                ]
                /
                families
                if families
                else 0.0
            ),

            "mean_retrieval_recall": (
                bucket[
                    "recall_sum"
                ]
                /
                families
                if families
                else 0.0
            ),

            "mean_candidate_count": (
                bucket[
                    "candidate_count_sum"
                ]
                /
                families
                if families
                else 0.0
            ),

            "fallback_queries": (
                bucket[
                    "fallback_queries"
                ]
            ),
        }

    return result


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
    for learned in snapshot[
        "learned"
    ]:

        if (
            learned[
                "family_id"
            ]
            ==
            family_id
        ):
            return learned

    raise KeyError(
        family_id
    )


def evaluation_family(
    family,
):
    """
    Create the transfer-time view of a family.

    Learning always uses complete identity metadata.
    Evaluation uses only the identity level declared by the task.
    """

    result = copy.deepcopy(
        family
    )

    result[
        "entities"
    ] = list(
        family[
            "query_entities"
        ]
    )

    result[
        "transfer"
    ][
        "prompt"
    ] = (
        family[
            "query_prompt"
        ]
    )

    return result


def _decorate_selection(
    *,
    selection,
    family_id,
):
    return {
        **selection,

        **posthoc_candidate_metrics(
            target_family_id=(
                family_id
            ),
            candidate_family_ids=(
                selection[
                    "candidate_family_ids"
                ]
            ),
        ),
    }


def run_family_019(
    *,
    family,
    current_snapshot,
    hierarchical_snapshot,
    current_selection,
    hierarchical_selection,
    eval_dir,
    model,
    embedder,
    meter,
    clause_by_family,
):
    family_id = family[
        "id"
    ]

    eval_family = (
        evaluation_family(
            family
        )
    )

    current = (
        evaluate_snapshot(
            snapshot_path=Path(
                current_snapshot[
                    "db_path"
                ]
            ),

            eval_db_path=(
                Path(
                    eval_dir
                )
                /
                (
                    "current_"
                    +
                    family_id
                    +
                    ".sqlite3"
                )
            ),

            family=eval_family,
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )
    )

    hierarchical = (
        evaluate_snapshot(
            snapshot_path=Path(
                hierarchical_snapshot[
                    "db_path"
                ]
            ),

            eval_db_path=(
                Path(
                    eval_dir
                )
                /
                (
                    "hierarchical_"
                    +
                    family_id
                    +
                    ".sqlite3"
                )
            ),

            family=eval_family,
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )
    )

    effect = (
        classify_hierarchical_effect(
            current_pass=(
                current[
                    "semantic_task_pass"
                ]
            ),

            hierarchical_pass=(
                hierarchical[
                    "semantic_task_pass"
                ]
            ),

            current_visible=(
                current[
                    "target_clause_visible"
                ]
            ),

            hierarchical_visible=(
                hierarchical[
                    "target_clause_visible"
                ]
            ),
        )
    )

    return {
        "family_id": (
            family_id
        ),

        "system_name": (
            family[
                "system_name"
            ]
        ),

        "code_name": (
            family[
                "code_name"
            ]
        ),

        "interference_cluster": (
            family[
                "interference_cluster"
            ]
        ),

        "degradation_mode": (
            family[
                "degradation_mode"
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

        "current_selection": (
            current_selection
        ),

        "hierarchical_selection": (
            hierarchical_selection
        ),

        "current": (
            current
        ),

        "hierarchical": (
            hierarchical
        ),

        "paired": {
            **effect,

            "task_delta": (
                int(
                    hierarchical[
                        "semantic_task_pass"
                    ]
                )
                -
                int(
                    current[
                        "semantic_task_pass"
                    ]
                )
            ),

            "visibility_delta": (
                int(
                    hierarchical[
                        "target_clause_visible"
                    ]
                )
                -
                int(
                    current[
                        "target_clause_visible"
                    ]
                )
            ),

            "wrong_family_clause_delta": (
                hierarchical[
                    "wrong_family_clause_count"
                ]
                -
                current[
                    "wrong_family_clause_count"
                ]
            ),

            "candidate_count_delta": (
                hierarchical_selection[
                    "candidate_count"
                ]
                -
                current_selection[
                    "candidate_count"
                ]
            ),
        },
    }


def run_experiment_019(
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

    families = payload[
        "families"
    ]

    family_by_id = {
        family["id"]: family

        for family
        in families
    }

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
        "snapshots"
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
    # BUILD MEMORY ONCE
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

    current_selections = {}
    hierarchical_selections = {}

    current_snapshots = {}
    hierarchical_snapshots = {}

    # ================================================================
    # BOTH ROUTERS SEE THE SAME COMPLETE POOL
    # ================================================================

    for family in families:

        family_id = family[
            "id"
        ]

        query_entities = family[
            "query_entities"
        ]

        current_raw = (
            select_identity_candidates(
                query_entities=(
                    query_entities
                ),
                families=(
                    families
                ),
            )
        )

        hierarchical_raw = (
            select_hierarchical_candidates(
                query_entities=(
                    query_entities
                ),
                families=(
                    families
                ),
            )
        )

        current_selection = (
            _decorate_selection(
                selection=(
                    current_raw
                ),
                family_id=(
                    family_id
                ),
            )
        )

        hierarchical_selection = (
            _decorate_selection(
                selection=(
                    hierarchical_raw
                ),
                family_id=(
                    family_id
                ),
            )
        )

        current_selections[
            family_id
        ] = (
            current_selection
        )

        hierarchical_selections[
            family_id
        ] = (
            hierarchical_selection
        )

        current_family_set = [
            family_by_id[
                candidate_id
            ]

            for candidate_id
            in current_selection[
                "candidate_family_ids"
            ]
        ]

        hierarchical_family_set = [
            family_by_id[
                candidate_id
            ]

            for candidate_id
            in hierarchical_selection[
                "candidate_family_ids"
            ]
        ]

        current_snapshots[
            family_id
        ] = (
            build_memory_snapshot(
                db_path=(
                    snapshot_dir
                    /
                    (
                        "current_"
                        +
                        family_id
                        +
                        ".sqlite3"
                    )
                ),

                families=(
                    current_family_set
                ),

                bundles=(
                    bundles
                ),

                embedder=embedder,
                meter=meter,
            )
        )

        hierarchical_snapshots[
            family_id
        ] = (
            build_memory_snapshot(
                db_path=(
                    snapshot_dir
                    /
                    (
                        "hierarchical_"
                        +
                        family_id
                        +
                        ".sqlite3"
                    )
                ),

                families=(
                    hierarchical_family_set
                ),

                bundles=(
                    bundles
                ),

                embedder=embedder,
                meter=meter,
            )
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

    results = [
        run_family_019(
            family=family,

            current_snapshot=(
                current_snapshots[
                    family[
                        "id"
                    ]
                ]
            ),

            hierarchical_snapshot=(
                hierarchical_snapshots[
                    family[
                        "id"
                    ]
                ]
            ),

            current_selection=(
                current_selections[
                    family[
                        "id"
                    ]
                ]
            ),

            hierarchical_selection=(
                hierarchical_selections[
                    family[
                        "id"
                    ]
                ]
            ),

            eval_dir=(
                eval_dir
            ),

            model=model,
            embedder=embedder,
            meter=meter,

            clause_by_family=(
                clause_by_family
            ),
        )

        for family
        in families
    ]

    family_count = len(
        results
    )

    current_passes = (
        _count(
            results,
            "current",
            "semantic_task_pass",
        )
    )

    hierarchical_passes = (
        _count(
            results,
            "hierarchical",
            "semantic_task_pass",
        )
    )

    target_lessons_equal = True
    target_sources_equal = True

    for family in families:

        family_id = family[
            "id"
        ]

        current_record = (
            _learned_record(
                current_snapshots[
                    family_id
                ],
                family_id,
            )
        )

        hierarchical_record = (
            _learned_record(
                hierarchical_snapshots[
                    family_id
                ],
                family_id,
            )
        )

        if (
            current_record[
                "lesson_sha256"
            ]
            !=
            hierarchical_record[
                "lesson_sha256"
            ]
        ):
            target_lessons_equal = False

        if (
            current_record[
                "source_evidence_sha256"
            ]
            !=
            hierarchical_record[
                "source_evidence_sha256"
            ]
        ):
            target_sources_equal = False

    report = {
        "experiment": (
            "seed-growth-019"
        ),

        "classification": (
            "exploratory-fresh-degraded-"
            "identity-activation-ablation"
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

        "hierarchy": [
            tier
            for (
                tier,
                _
            )
            in HIERARCHY
        ]
        + [
            "global"
        ],

        "conditions": {
            "A": (
                "seed_018_exact_identity_"
                "overlap_else_global"
            ),

            "B": (
                "hierarchical_code_system_"
                "cluster_domain_global"
            ),
        },

        # ------------------------------------------------------------
        # BEHAVIOR
        # ------------------------------------------------------------

        "current_task_passes": (
            current_passes
        ),

        "hierarchical_task_passes": (
            hierarchical_passes
        ),

        "current_task_pass_rate": (
            current_passes
            /
            family_count
        ),

        "hierarchical_task_pass_rate": (
            hierarchical_passes
            /
            family_count
        ),

        "current_semantic_violations": (
            _count(
                results,
                "current",
                "semantic_violation",
            )
        ),

        "hierarchical_semantic_violations": (
            _count(
                results,
                "hierarchical",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # ACTIVATION
        # ------------------------------------------------------------

        "current_target_visible_families": (
            _count(
                results,
                "current",
                "target_clause_visible",
            )
        ),

        "hierarchical_target_visible_families": (
            _count(
                results,
                "hierarchical",
                "target_clause_visible",
            )
        ),

        "current_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "current"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in results
        ),

        "hierarchical_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "hierarchical"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in results
        ),

        "current_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "current",
                "wrong_family_clause_count",
            )
        ),

        "hierarchical_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "hierarchical",
                "wrong_family_clause_count",
            )
        ),

        "mean_current_retrieval_precision": (
            _mean(
                row[
                    "current"
                ][
                    "retrieval_precision"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_retrieval_precision": (
            _mean(
                row[
                    "hierarchical"
                ][
                    "retrieval_precision"
                ]

                for row
                in results
            )
        ),

        "mean_current_retrieval_recall": (
            _mean(
                row[
                    "current"
                ][
                    "retrieval_recall"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_retrieval_recall": (
            _mean(
                row[
                    "hierarchical"
                ][
                    "retrieval_recall"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # PAIRED EFFECTS
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
            in results
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
            in results
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
            in results
        ),

        # ------------------------------------------------------------
        # CANDIDATE ACTIVATION
        # ------------------------------------------------------------

        "mean_current_candidate_count": (
            _mean(
                row[
                    "current_selection"
                ][
                    "candidate_count"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_candidate_count": (
            _mean(
                row[
                    "hierarchical_selection"
                ][
                    "candidate_count"
                ]

                for row
                in results
            )
        ),

        "mean_current_candidate_precision": (
            _mean(
                row[
                    "current_selection"
                ][
                    "candidate_precision"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_candidate_precision": (
            _mean(
                row[
                    "hierarchical_selection"
                ][
                    "candidate_precision"
                ]

                for row
                in results
            )
        ),

        "mean_current_candidate_recall": (
            _mean(
                row[
                    "current_selection"
                ][
                    "candidate_recall"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_candidate_recall": (
            _mean(
                row[
                    "hierarchical_selection"
                ][
                    "candidate_recall"
                ]

                for row
                in results
            )
        ),

        "current_global_fallback_queries": sum(
            int(
                row[
                    "current_selection"
                ][
                    "fallback_used"
                ]
            )

            for row
            in results
        ),

        "hierarchical_global_fallback_queries": sum(
            int(
                row[
                    "hierarchical_selection"
                ][
                    "fallback_used"
                ]
            )

            for row
            in results
        ),

        "hierarchical_code_tier_queries": sum(
            int(
                row[
                    "hierarchical_selection"
                ][
                    "selection_tier"
                ]
                ==
                "code"
            )

            for row
            in results
        ),

        "hierarchical_system_tier_queries": sum(
            int(
                row[
                    "hierarchical_selection"
                ][
                    "selection_tier"
                ]
                ==
                "system"
            )

            for row
            in results
        ),

        "hierarchical_cluster_tier_queries": sum(
            int(
                row[
                    "hierarchical_selection"
                ][
                    "selection_tier"
                ]
                ==
                "cluster"
            )

            for row
            in results
        ),

        "hierarchical_domain_tier_queries": sum(
            int(
                row[
                    "hierarchical_selection"
                ][
                    "selection_tier"
                ]
                ==
                "domain"
            )

            for row
            in results
        ),

        # ------------------------------------------------------------
        # CONTEXT
        # ------------------------------------------------------------

        "mean_current_memory_words": (
            _mean(
                row[
                    "current"
                ][
                    "memory_word_count"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_memory_words": (
            _mean(
                row[
                    "hierarchical"
                ][
                    "memory_word_count"
                ]

                for row
                in results
            )
        ),

        "mean_current_memory_segments": (
            _mean(
                row[
                    "current"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        "mean_hierarchical_memory_segments": (
            _mean(
                row[
                    "hierarchical"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # DEGRADATION CURVE
        # ------------------------------------------------------------

        "current_mode_metrics": (
            aggregate_mode_metrics(
                results,
                condition="current",
                selection_key=(
                    "current_selection"
                ),
            )
        ),

        "hierarchical_mode_metrics": (
            aggregate_mode_metrics(
                results,
                condition=(
                    "hierarchical"
                ),
                selection_key=(
                    "hierarchical_selection"
                ),
            )
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
        # RESOURCE ACCOUNTING
        # ------------------------------------------------------------

        "initial_extraction_model_calls": (
            family_count
        ),

        "repair_model_calls": (
            family_count
        ),

        "current_transfer_model_calls": (
            family_count
        ),

        "hierarchical_transfer_model_calls": (
            family_count
        ),

        "current_router_model_calls": 0,

        "hierarchical_router_model_calls": 0,

        # ------------------------------------------------------------
        # CONTROLS
        # ------------------------------------------------------------

        "all_target_lessons_identical_between_conditions": (
            target_lessons_equal
        ),

        "all_target_source_evidence_equal": (
            target_sources_equal
        ),

        "all_transfer_queries_equal": True,

        "all_compact_renderers_equal": True,

        "all_context_budget_configuration_equal": True,

        "all_reasoners_equal": True,

        "all_candidate_selection_from_same_full_pool": True,

        "hierarchical_router_used_family_id": False,

        "hierarchical_router_used_semantic_clause": False,

        "hierarchical_router_used_semantic_grader": False,

        "hierarchical_router_used_model": False,

        "families": (
            results
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
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_019.json"
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

    model = OpenAIResponsesModel(
        model_name
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
        run_experiment_019(
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

        "current_task_passes",
        "hierarchical_task_passes",

        "current_target_visible_families",
        "hierarchical_target_visible_families",

        "current_families_with_wrong_memory_presented",
        "hierarchical_families_with_wrong_memory_presented",

        "mean_current_retrieval_precision",
        "mean_hierarchical_retrieval_precision",

        "mean_current_retrieval_recall",
        "mean_hierarchical_retrieval_recall",

        "task_rescue_families",
        "task_harm_families",
        "visibility_rescue_families",

        "mean_current_candidate_count",
        "mean_hierarchical_candidate_count",

        "mean_current_candidate_precision",
        "mean_hierarchical_candidate_precision",

        "mean_current_candidate_recall",
        "mean_hierarchical_candidate_recall",

        "current_global_fallback_queries",
        "hierarchical_global_fallback_queries",

        "hierarchical_code_tier_queries",
        "hierarchical_system_tier_queries",
        "hierarchical_cluster_tier_queries",
        "hierarchical_domain_tier_queries",

        "mean_current_memory_words",
        "mean_hierarchical_memory_words",

        "current_mode_metrics",
        "hierarchical_mode_metrics",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",
        "all_transfer_queries_equal",
        "all_compact_renderers_equal",
        "all_context_budget_configuration_equal",
        "all_reasoners_equal",
        "all_candidate_selection_from_same_full_pool",

        "hierarchical_router_used_family_id",
        "hierarchical_router_used_semantic_clause",
        "hierarchical_router_used_semantic_grader",
        "hierarchical_router_used_model",
    )

    summary = {
        key: report[key]
        for key in keys
    }

    summary["result"] = str(
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
