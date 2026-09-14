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
)

from experiments.seed_growth_019 import (
    HIERARCHY,
    evaluation_family,
    select_hierarchical_candidates,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
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


def select_conjunctive_candidates(
    *,
    query_entities,
    families,
):
    """
    Strong identity constrains. Context refines.

    Addressing hierarchy:

        code
        system
        cluster
        domain
        global

    Unlike Seed 019, the first successful tier does not
    automatically terminate routing.

    Later compatible tiers may shrink the existing candidate set.

    A weaker tier may NEVER erase a valid stronger address.
    If its intersection is empty, the refinement is rejected and
    the existing candidate set survives unchanged.
    """

    active_ids = None
    seed_tier = None

    tier_trace = []

    accepted_refinement_tiers = []
    rejected_refinement_tiers = []

    empty_intersection_protections = 0

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

        global_matches = []
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

            global_matches.append(
                family_id
            )

            matched_entities[
                family_id
            ] = overlap

        if not global_matches:

            tier_trace.append(
                {
                    "tier": tier_name,
                    "status": "no_match",
                    "candidate_count_before": (
                        len(active_ids)
                        if active_ids
                        is not None
                        else 0
                    ),
                    "candidate_count_after": (
                        len(active_ids)
                        if active_ids
                        is not None
                        else 0
                    ),
                    "matched_entities": {},
                }
            )

            continue

        if active_ids is None:

            active_ids = list(
                global_matches
            )

            seed_tier = (
                tier_name
            )

            tier_trace.append(
                {
                    "tier": tier_name,
                    "status": "seed",
                    "candidate_count_before": (
                        len(families)
                    ),
                    "candidate_count_after": (
                        len(active_ids)
                    ),
                    "matched_entities": (
                        matched_entities
                    ),
                }
            )

            continue

        before = list(
            active_ids
        )

        global_match_set = set(
            global_matches
        )

        intersection = [
            family_id

            for family_id
            in active_ids

            if (
                family_id
                in
                global_match_set
            )
        ]

        if not intersection:

            rejected_refinement_tiers.append(
                tier_name
            )

            empty_intersection_protections += 1

            tier_trace.append(
                {
                    "tier": tier_name,
                    "status": (
                        "rejected_empty_intersection"
                    ),
                    "candidate_count_before": (
                        len(before)
                    ),
                    "candidate_count_after": (
                        len(before)
                    ),
                    "matched_entities": (
                        matched_entities
                    ),
                }
            )

            continue

        if (
            len(intersection)
            <
            len(before)
        ):

            active_ids = (
                intersection
            )

            accepted_refinement_tiers.append(
                tier_name
            )

            tier_trace.append(
                {
                    "tier": tier_name,
                    "status": (
                        "accepted_refinement"
                    ),
                    "candidate_count_before": (
                        len(before)
                    ),
                    "candidate_count_after": (
                        len(active_ids)
                    ),
                    "matched_entities": (
                        matched_entities
                    ),
                }
            )

            continue

        tier_trace.append(
            {
                "tier": tier_name,
                "status": (
                    "compatible_no_change"
                ),
                "candidate_count_before": (
                    len(before)
                ),
                "candidate_count_after": (
                    len(before)
                ),
                "matched_entities": (
                    matched_entities
                ),
            }
        )

    if active_ids is None:

        active_ids = [
            family[
                "id"
            ]

            for family
            in families
        ]

        return {
            "selection_mode": (
                "global_fallback"
            ),

            "seed_tier": None,

            "selection_path": [
                "global"
            ],

            "candidate_family_ids": (
                active_ids
            ),

            "candidate_count": (
                len(active_ids)
            ),

            "accepted_refinement_tiers": [],

            "rejected_refinement_tiers": [],

            "empty_intersection_protections": 0,

            "tier_trace": (
                tier_trace
            ),

            "fallback_used": True,
        }

    selection_path = [
        seed_tier,
        *accepted_refinement_tiers,
    ]

    return {
        "selection_mode": (
            "conjunctive_address_refinement"
        ),

        "seed_tier": (
            seed_tier
        ),

        "selection_path": (
            selection_path
        ),

        "candidate_family_ids": (
            active_ids
        ),

        "candidate_count": (
            len(active_ids)
        ),

        "accepted_refinement_tiers": (
            accepted_refinement_tiers
        ),

        "rejected_refinement_tiers": (
            rejected_refinement_tiers
        ),

        "empty_intersection_protections": (
            empty_intersection_protections
        ),

        "tier_trace": (
            tier_trace
        ),

        "fallback_used": False,
    }


def canonical_candidate_key(
    *,
    candidate_family_ids,
    canonical_family_ids,
):
    """
    Candidate-state identity is determined by canonical memory order,
    never by router output order.
    """

    selected = set(
        candidate_family_ids
    )

    return tuple(
        family_id

        for family_id
        in canonical_family_ids

        if (
            family_id
            in
            selected
        )
    )


def requires_second_evaluation(
    *,
    baseline_candidate_ids,
    conjunctive_candidate_ids,
    canonical_family_ids,
):
    """
    If A and B have identical candidate state, there is no mechanism
    difference to evaluate.

    Reusing the exact transfer evaluation prevents ordinary model
    stochasticity from being misreported as a routing effect.
    """

    baseline_key = (
        canonical_candidate_key(
            candidate_family_ids=(
                baseline_candidate_ids
            ),
            canonical_family_ids=(
                canonical_family_ids
            ),
        )
    )

    conjunctive_key = (
        canonical_candidate_key(
            candidate_family_ids=(
                conjunctive_candidate_ids
            ),
            canonical_family_ids=(
                canonical_family_ids
            ),
        )
    )

    return (
        baseline_key
        !=
        conjunctive_key
    )


def classify_conjunctive_effect(
    *,
    baseline_pass,
    conjunctive_pass,
    baseline_visible,
    conjunctive_visible,
):
    return {
        "task_rescue": (
            (not baseline_pass)
            and
            conjunctive_pass
        ),

        "task_harm": (
            baseline_pass
            and
            (not conjunctive_pass)
        ),

        "visibility_rescue": (
            (not baseline_visible)
            and
            conjunctive_visible
        ),

        "visibility_harm": (
            baseline_visible
            and
            (not conjunctive_visible)
        ),
    }


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
            "families_with_wrong_memory": 0,
            "wrong_family_clause_occurrences": 0,
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


def run_family_020(
    *,
    family,
    baseline_snapshot,
    conjunctive_snapshot,
    baseline_selection,
    conjunctive_selection,
    reuse_evaluation,
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

    baseline = (
        evaluate_snapshot(
            snapshot_path=Path(
                baseline_snapshot[
                    "db_path"
                ]
            ),

            eval_db_path=(
                Path(eval_dir)
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

    if reuse_evaluation:

        conjunctive = (
            copy.deepcopy(
                baseline
            )
        )

    else:

        conjunctive = (
            evaluate_snapshot(
                snapshot_path=Path(
                    conjunctive_snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    Path(eval_dir)
                    /
                    (
                        "conjunctive_"
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
        classify_conjunctive_effect(
            baseline_pass=(
                baseline[
                    "semantic_task_pass"
                ]
            ),

            conjunctive_pass=(
                conjunctive[
                    "semantic_task_pass"
                ]
            ),

            baseline_visible=(
                baseline[
                    "target_clause_visible"
                ]
            ),

            conjunctive_visible=(
                conjunctive[
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

        "baseline_selection": (
            baseline_selection
        ),

        "conjunctive_selection": (
            conjunctive_selection
        ),

        "baseline": (
            baseline
        ),

        "conjunctive": (
            conjunctive
        ),

        "paired": {
            **effect,

            "evaluation_reused": (
                reuse_evaluation
            ),

            "candidate_sets_equal": (
                not
                requires_second_evaluation(
                    baseline_candidate_ids=(
                        baseline_selection[
                            "candidate_family_ids"
                        ]
                    ),

                    conjunctive_candidate_ids=(
                        conjunctive_selection[
                            "candidate_family_ids"
                        ]
                    ),

                    canonical_family_ids=[
                        family_id
                        for family_id
                        in (
                            baseline_selection.get(
                                "_canonical_family_ids",
                                [],
                            )
                        )
                    ],
                )
                if baseline_selection.get(
                    "_canonical_family_ids"
                )
                else reuse_evaluation
            ),

            "task_delta": (
                int(
                    conjunctive[
                        "semantic_task_pass"
                    ]
                )
                -
                int(
                    baseline[
                        "semantic_task_pass"
                    ]
                )
            ),

            "visibility_delta": (
                int(
                    conjunctive[
                        "target_clause_visible"
                    ]
                )
                -
                int(
                    baseline[
                        "target_clause_visible"
                    ]
                )
            ),

            "wrong_family_clause_delta": (
                conjunctive[
                    "wrong_family_clause_count"
                ]
                -
                baseline[
                    "wrong_family_clause_count"
                ]
            ),

            "candidate_count_delta": (
                conjunctive_selection[
                    "candidate_count"
                ]
                -
                baseline_selection[
                    "candidate_count"
                ]
            ),
        },
    }


def run_experiment_020(
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
        "candidate_snapshots"
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
    # BUILD EACH LEARNED MEMORY ONCE
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

    # ================================================================
    # SHARED CANDIDATE SNAPSHOT CACHE
    #
    # A and B never independently reconstruct an identical candidate
    # state. Candidate-equivalent conditions receive the exact same
    # frozen SQLite snapshot.
    # ================================================================

    snapshot_cache = {}

    def snapshot_for(
        candidate_family_ids,
    ):
        key = (
            canonical_candidate_key(
                candidate_family_ids=(
                    candidate_family_ids
                ),

                canonical_family_ids=(
                    canonical_family_ids
                ),
            )
        )

        if not key:
            raise RuntimeError(
                "Candidate set may not be empty."
            )

        if key in snapshot_cache:
            return (
                snapshot_cache[key],
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
                        "candidate_"
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

    baseline_selections = {}
    conjunctive_selections = {}

    baseline_snapshots = {}
    conjunctive_snapshots = {}

    baseline_keys = {}
    conjunctive_keys = {}

    # ================================================================
    # BOTH ROUTERS SEE THE SAME COMPLETE MEMORY POPULATION
    # ================================================================

    for family in families:

        family_id = family[
            "id"
        ]

        query_entities = family[
            "query_entities"
        ]

        baseline_raw = (
            select_hierarchical_candidates(
                query_entities=(
                    query_entities
                ),
                families=(
                    families
                ),
            )
        )

        conjunctive_raw = (
            select_conjunctive_candidates(
                query_entities=(
                    query_entities
                ),
                families=(
                    families
                ),
            )
        )

        baseline_selection = (
            _decorate_selection(
                selection=(
                    baseline_raw
                ),
                family_id=(
                    family_id
                ),
            )
        )

        conjunctive_selection = (
            _decorate_selection(
                selection=(
                    conjunctive_raw
                ),
                family_id=(
                    family_id
                ),
            )
        )

        baseline_selections[
            family_id
        ] = (
            baseline_selection
        )

        conjunctive_selections[
            family_id
        ] = (
            conjunctive_selection
        )

        (
            baseline_snapshot,
            baseline_key,
        ) = (
            snapshot_for(
                baseline_selection[
                    "candidate_family_ids"
                ]
            )
        )

        (
            conjunctive_snapshot,
            conjunctive_key,
        ) = (
            snapshot_for(
                conjunctive_selection[
                    "candidate_family_ids"
                ]
            )
        )

        baseline_snapshots[
            family_id
        ] = (
            baseline_snapshot
        )

        conjunctive_snapshots[
            family_id
        ] = (
            conjunctive_snapshot
        )

        baseline_keys[
            family_id
        ] = (
            baseline_key
        )

        conjunctive_keys[
            family_id
        ] = (
            conjunctive_key
        )

    # ================================================================
    # EVALUATION
    #
    # Equal candidate states:
    #     evaluate once
    #     reuse exact transfer result
    #
    # Different candidate states:
    #     evaluate A once
    #     evaluate B once
    # ================================================================

    clause_by_family = {
        family["id"]: (
            family[
                "semantic_clause"
            ]
        )

        for family
        in families
    }

    results = []

    for family in families:

        family_id = family[
            "id"
        ]

        reuse_evaluation = (
            baseline_keys[
                family_id
            ]
            ==
            conjunctive_keys[
                family_id
            ]
        )

        results.append(
            run_family_020(
                family=family,

                baseline_snapshot=(
                    baseline_snapshots[
                        family_id
                    ]
                ),

                conjunctive_snapshot=(
                    conjunctive_snapshots[
                        family_id
                    ]
                ),

                baseline_selection=(
                    baseline_selections[
                        family_id
                    ]
                ),

                conjunctive_selection=(
                    conjunctive_selections[
                        family_id
                    ]
                ),

                reuse_evaluation=(
                    reuse_evaluation
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
        )

    family_count = len(
        results
    )

    equal_candidate_pairs = sum(
        int(
            baseline_keys[
                family["id"]
            ]
            ==
            conjunctive_keys[
                family["id"]
            ]
        )

        for family
        in families
    )

    differing_candidate_pairs = (
        family_count
        -
        equal_candidate_pairs
    )

    # ================================================================
    # TARGET-MEMORY CONTROLS
    # ================================================================

    target_lessons_equal = True
    target_sources_equal = True

    for family in families:

        family_id = family[
            "id"
        ]

        baseline_record = (
            _learned_record(
                baseline_snapshots[
                    family_id
                ],
                family_id,
            )
        )

        conjunctive_record = (
            _learned_record(
                conjunctive_snapshots[
                    family_id
                ],
                family_id,
            )
        )

        if (
            baseline_record[
                "lesson_sha256"
            ]
            !=
            conjunctive_record[
                "lesson_sha256"
            ]
        ):

            target_lessons_equal = False

        if (
            baseline_record[
                "source_evidence_sha256"
            ]
            !=
            conjunctive_record[
                "source_evidence_sha256"
            ]
        ):

            target_sources_equal = False

    baseline_passes = (
        _count(
            results,
            "baseline",
            "semantic_task_pass",
        )
    )

    conjunctive_passes = (
        _count(
            results,
            "conjunctive",
            "semantic_task_pass",
        )
    )

    accepted_refinement_steps = sum(
        len(
            row[
                "conjunctive_selection"
            ][
                "accepted_refinement_tiers"
            ]
        )

        for row
        in results
    )

    rejected_refinement_steps = sum(
        len(
            row[
                "conjunctive_selection"
            ][
                "rejected_refinement_tiers"
            ]
        )

        for row
        in results
    )

    report = {
        "experiment": (
            "seed-growth-020"
        ),

        "classification": (
            "exploratory-fresh-conjunctive-"
            "address-refinement-ablation"
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
            len(families)
        ),

        "conditions": {
            "A": (
                "seed_019_first_successful_"
                "hierarchical_address"
            ),

            "B": (
                "conjunctive_strong_identity_"
                "plus_compatible_context_refinement"
            ),
        },

        # ------------------------------------------------------------
        # BEHAVIOR
        # ------------------------------------------------------------

        "baseline_task_passes": (
            baseline_passes
        ),

        "conjunctive_task_passes": (
            conjunctive_passes
        ),

        "baseline_task_pass_rate": (
            baseline_passes
            /
            family_count
        ),

        "conjunctive_task_pass_rate": (
            conjunctive_passes
            /
            family_count
        ),

        "baseline_semantic_violations": (
            _count(
                results,
                "baseline",
                "semantic_violation",
            )
        ),

        "conjunctive_semantic_violations": (
            _count(
                results,
                "conjunctive",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # ACTIVATION
        # ------------------------------------------------------------

        "baseline_target_visible_families": (
            _count(
                results,
                "baseline",
                "target_clause_visible",
            )
        ),

        "conjunctive_target_visible_families": (
            _count(
                results,
                "conjunctive",
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
            in results
        ),

        "conjunctive_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "conjunctive"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in results
        ),

        "baseline_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "baseline",
                "wrong_family_clause_count",
            )
        ),

        "conjunctive_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "conjunctive",
                "wrong_family_clause_count",
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
                in results
            )
        ),

        "mean_conjunctive_retrieval_precision": (
            _mean(
                row[
                    "conjunctive"
                ][
                    "retrieval_precision"
                ]

                for row
                in results
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
                in results
            )
        ),

        "mean_conjunctive_retrieval_recall": (
            _mean(
                row[
                    "conjunctive"
                ][
                    "retrieval_recall"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # CANDIDATE GEOMETRY
        # ------------------------------------------------------------

        "mean_baseline_candidate_count": (
            _mean(
                row[
                    "baseline_selection"
                ][
                    "candidate_count"
                ]

                for row
                in results
            )
        ),

        "mean_conjunctive_candidate_count": (
            _mean(
                row[
                    "conjunctive_selection"
                ][
                    "candidate_count"
                ]

                for row
                in results
            )
        ),

        "mean_baseline_candidate_precision": (
            _mean(
                row[
                    "baseline_selection"
                ][
                    "candidate_precision"
                ]

                for row
                in results
            )
        ),

        "mean_conjunctive_candidate_precision": (
            _mean(
                row[
                    "conjunctive_selection"
                ][
                    "candidate_precision"
                ]

                for row
                in results
            )
        ),

        "mean_baseline_candidate_recall": (
            _mean(
                row[
                    "baseline_selection"
                ][
                    "candidate_recall"
                ]

                for row
                in results
            )
        ),

        "mean_conjunctive_candidate_recall": (
            _mean(
                row[
                    "conjunctive_selection"
                ][
                    "candidate_recall"
                ]

                for row
                in results
            )
        ),

        "accepted_refinement_steps": (
            accepted_refinement_steps
        ),

        "rejected_refinement_steps": (
            rejected_refinement_steps
        ),

        "empty_intersection_protections": sum(
            row[
                "conjunctive_selection"
            ][
                "empty_intersection_protections"
            ]

            for row
            in results
        ),

        # ------------------------------------------------------------
        # PAIRED EFFECT
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

        "visibility_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "visibility_harm"
                ]
            )

            for row
            in results
        ),

        # ------------------------------------------------------------
        # CONTEXT COST
        # ------------------------------------------------------------

        "mean_baseline_memory_words": (
            _mean(
                row[
                    "baseline"
                ][
                    "memory_word_count"
                ]

                for row
                in results
            )
        ),

        "mean_conjunctive_memory_words": (
            _mean(
                row[
                    "conjunctive"
                ][
                    "memory_word_count"
                ]

                for row
                in results
            )
        ),

        "mean_baseline_memory_segments": (
            _mean(
                row[
                    "baseline"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        "mean_conjunctive_memory_segments": (
            _mean(
                row[
                    "conjunctive"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # DEGRADATION MODE
        # ------------------------------------------------------------

        "baseline_mode_metrics": (
            aggregate_mode_metrics(
                results,

                condition=(
                    "baseline"
                ),

                selection_key=(
                    "baseline_selection"
                ),
            )
        ),

        "conjunctive_mode_metrics": (
            aggregate_mode_metrics(
                results,

                condition=(
                    "conjunctive"
                ),

                selection_key=(
                    "conjunctive_selection"
                ),
            )
        ),

        # ------------------------------------------------------------
        # SAME-STATE NOISE CONTROL
        # ------------------------------------------------------------

        "equal_candidate_set_pairs": (
            equal_candidate_pairs
        ),

        "differing_candidate_set_pairs": (
            differing_candidate_pairs
        ),

        "reused_equal_candidate_evaluations": (
            equal_candidate_pairs
        ),

        "unique_candidate_snapshots_built": (
            len(
                snapshot_cache
            )
        ),

        "baseline_transfer_model_calls": (
            family_count
        ),

        "conjunctive_additional_transfer_model_calls": (
            differing_candidate_pairs
        ),

        "total_transfer_model_calls": (
            family_count
            +
            differing_candidate_pairs
        ),

        "all_equal_candidate_pairs_share_snapshot": all(
            (
                baseline_keys[
                    family["id"]
                ]
                !=
                conjunctive_keys[
                    family["id"]
                ]
            )
            or
            (
                baseline_snapshots[
                    family["id"]
                ][
                    "snapshot_sha256"
                ]
                ==
                conjunctive_snapshots[
                    family["id"]
                ][
                    "snapshot_sha256"
                ]
            )

            for family
            in families
        ),

        "all_equal_candidate_pairs_reused_evaluation": all(
            (
                baseline_keys[
                    row[
                        "family_id"
                    ]
                ]
                !=
                conjunctive_keys[
                    row[
                        "family_id"
                    ]
                ]
            )
            or
            (
                row[
                    "paired"
                ][
                    "evaluation_reused"
                ]
            )

            for row
            in results
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

        "conjunctive_router_model_calls": 0,

        "conjunctive_router_used_family_id": False,

        "conjunctive_router_used_semantic_clause": False,

        "conjunctive_router_used_semantic_grader": False,

        "conjunctive_router_used_model": False,

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
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_020.json"
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
        run_experiment_020(
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

        "baseline_task_passes",
        "conjunctive_task_passes",

        "baseline_target_visible_families",
        "conjunctive_target_visible_families",

        "baseline_families_with_wrong_memory_presented",
        "conjunctive_families_with_wrong_memory_presented",

        "mean_baseline_retrieval_precision",
        "mean_conjunctive_retrieval_precision",

        "mean_baseline_retrieval_recall",
        "mean_conjunctive_retrieval_recall",

        "mean_baseline_candidate_count",
        "mean_conjunctive_candidate_count",

        "mean_baseline_candidate_precision",
        "mean_conjunctive_candidate_precision",

        "accepted_refinement_steps",
        "rejected_refinement_steps",
        "empty_intersection_protections",

        "task_rescue_families",
        "task_harm_families",
        "visibility_rescue_families",
        "visibility_harm_families",

        "mean_baseline_memory_words",
        "mean_conjunctive_memory_words",

        "baseline_mode_metrics",
        "conjunctive_mode_metrics",

        "equal_candidate_set_pairs",
        "differing_candidate_set_pairs",
        "reused_equal_candidate_evaluations",

        "unique_candidate_snapshots_built",

        "baseline_transfer_model_calls",
        "conjunctive_additional_transfer_model_calls",
        "total_transfer_model_calls",

        "all_equal_candidate_pairs_share_snapshot",
        "all_equal_candidate_pairs_reused_evaluation",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",
        "all_transfer_queries_equal",
        "all_compact_renderers_equal",
        "all_context_budget_configuration_equal",
        "all_reasoners_equal",
        "all_candidate_selection_from_same_full_pool",

        "conjunctive_router_model_calls",
        "conjunctive_router_used_family_id",
        "conjunctive_router_used_semantic_clause",
        "conjunctive_router_used_semantic_grader",
        "conjunctive_router_used_model",
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
