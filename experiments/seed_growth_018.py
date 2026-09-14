from __future__ import annotations

import argparse
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

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


IDENTITY_ANCHOR_PREFIXES = (
    "system:",
    "code:",
)


def identity_anchors(
    entities,
):
    """
    Return exact identity-bearing entities.

    These are addressing signals, not similarity features.
    """

    anchors = {
        entity

        for entity
        in entities

        if (
            isinstance(
                entity,
                str,
            )
            and
            any(
                entity.startswith(
                    prefix
                )

                for prefix
                in IDENTITY_ANCHOR_PREFIXES
            )
        )
    }

    return tuple(
        sorted(
            anchors
        )
    )


def select_identity_candidates(
    *,
    query_entities,
    families,
):
    """
    Identity narrows. Similarity ranks.

    This function may inspect only:

    - query entities;
    - memory entities.

    It does not receive:

    - target family ID;
    - semantic clause;
    - grader;
    - correct answer;
    - canonical atoms.

    If one or more exact identity anchors match, only those
    memories become candidates for the unchanged downstream
    retrieval stack.

    If no identity match exists, fall back to the full pool.
    """

    query_anchors = set(
        identity_anchors(
            query_entities
        )
    )

    matches = {}
    matched_families = []

    if query_anchors:

        for family in families:

            family_anchors = set(
                identity_anchors(
                    family.get(
                        "entities",
                        [],
                    )
                )
            )

            overlap = sorted(
                query_anchors
                &
                family_anchors
            )

            if not overlap:
                continue

            family_id = (
                family[
                    "id"
                ]
            )

            matched_families.append(
                family_id
            )

            matches[
                family_id
            ] = (
                overlap
            )

    if matched_families:

        return {
            "query_identity_anchors": (
                sorted(
                    query_anchors
                )
            ),

            "candidate_family_ids": (
                matched_families
            ),

            "candidate_count": (
                len(
                    matched_families
                )
            ),

            "matches": (
                matches
            ),

            "fallback_used": False,

            "selection_mode": (
                "exact_identity_anchor"
            ),
        }

    all_family_ids = [
        family[
            "id"
        ]

        for family
        in families
    ]

    return {
        "query_identity_anchors": (
            sorted(
                query_anchors
            )
        ),

        "candidate_family_ids": (
            all_family_ids
        ),

        "candidate_count": (
            len(
                all_family_ids
            )
        ),

        "matches": {},

        "fallback_used": True,

        "selection_mode": (
            "full_pool_rrf_fallback"
        ),
    }


def posthoc_candidate_metrics(
    *,
    target_family_id,
    candidate_family_ids,
):
    """
    Benchmark-only post-hoc scoring.

    The target ID is never passed into candidate selection.
    """

    selected = (
        target_family_id
        in
        candidate_family_ids
    )

    count = (
        len(
            candidate_family_ids
        )
    )

    if (
        selected
        and
        count
    ):

        precision = (
            1.0
            /
            count
        )

    else:

        precision = 0.0

    return {
        "target_selected": (
            selected
        ),

        "candidate_count": (
            count
        ),

        "candidate_recall": (
            1.0
            if selected
            else 0.0
        ),

        "candidate_precision": (
            precision
        ),

        "distractor_candidates": (
            count
            -
            int(
                selected
            )
        ),
    }


def classify_activation_effect(
    *,
    current_pass,
    anchored_pass,
    current_target_visible,
    anchored_target_visible,
):
    return {
        "activation_rescue": (
            (not current_pass)
            and
            anchored_pass
        ),

        "activation_harm": (
            current_pass
            and
            (not anchored_pass)
        ),

        "visibility_rescue": (
            (not current_target_visible)
            and
            anchored_target_visible
        ),

        "visibility_harm": (
            current_target_visible
            and
            (not anchored_target_visible)
        ),
    }


def aggregate_activation_clusters(
    rows,
    condition,
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
        }
    )

    for row in rows:

        cluster = (
            row[
                "interference_cluster"
            ]
        )

        metrics = (
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

        wrong_count = int(
            metrics[
                "wrong_family_clause_count"
            ]
        )

        bucket[
            "wrong_family_clause_occurrences"
        ] += (
            wrong_count
        )

        bucket[
            "families_with_wrong_memory"
        ] += int(
            wrong_count
            > 0
        )

        bucket[
            "precision_sum"
        ] += float(
            metrics.get(
                "retrieval_precision",
                0.0,
            )
        )

        bucket[
            "recall_sum"
        ] += float(
            metrics.get(
                "retrieval_recall",
                0.0,
            )
        )

    result = {}

    for cluster, bucket in sorted(
        grouped.items()
    ):

        families = (
            bucket[
                "families"
            ]
        )

        result[
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
                if families
                else 0.0
            ),

            "target_visible_families": (
                bucket[
                    "target_visible_families"
                ]
            ),

            "wrong_family_clause_occurrences": (
                bucket[
                    "wrong_family_clause_occurrences"
                ]
            ),

            "families_with_wrong_memory": (
                bucket[
                    "families_with_wrong_memory"
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
        }

    return result


def _learned_record(
    snapshot,
    family_id,
):
    for item in snapshot[
        "learned"
    ]:

        if (
            item[
                "family_id"
            ]
            ==
            family_id
        ):

            return item

    raise KeyError(
        family_id
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


def run_family_018(
    *,
    family,
    current_snapshot,
    anchored_snapshot,
    selection,
    eval_dir,
    model,
    embedder,
    meter,
    clause_by_family,
):
    family_id = (
        family[
            "id"
        ]
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

            family=family,
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )
    )

    anchored = (
        evaluate_snapshot(
            snapshot_path=Path(
                anchored_snapshot[
                    "db_path"
                ]
            ),

            eval_db_path=(
                Path(
                    eval_dir
                )
                /
                (
                    "anchored_"
                    +
                    family_id
                    +
                    ".sqlite3"
                )
            ),

            family=family,
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )
    )

    candidate_metrics = (
        posthoc_candidate_metrics(
            target_family_id=(
                family_id
            ),
            candidate_family_ids=(
                selection[
                    "candidate_family_ids"
                ]
            ),
        )
    )

    effect = (
        classify_activation_effect(
            current_pass=(
                current[
                    "semantic_task_pass"
                ]
            ),
            anchored_pass=(
                anchored[
                    "semantic_task_pass"
                ]
            ),
            current_target_visible=(
                current[
                    "target_clause_visible"
                ]
            ),
            anchored_target_visible=(
                anchored[
                    "target_clause_visible"
                ]
            ),
        )
    )

    return {
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

        "semantic_clause": (
            family[
                "semantic_clause"
            ]
        ),

        "identity_selection": {
            **selection,
            **candidate_metrics,
        },

        "current": (
            current
        ),

        "anchored": (
            anchored
        ),

        "paired": {
            **effect,

            "task_delta": (
                int(
                    anchored[
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

            "target_visibility_delta": (
                int(
                    anchored[
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
                anchored[
                    "wrong_family_clause_count"
                ]
                -
                current[
                    "wrong_family_clause_count"
                ]
            ),

            "retrieval_precision_delta": (
                anchored[
                    "retrieval_precision"
                ]
                -
                current[
                    "retrieval_precision"
                ]
            ),

            "retrieval_recall_delta": (
                anchored[
                    "retrieval_recall"
                ]
                -
                current[
                    "retrieval_recall"
                ]
            ),

            "memory_word_delta": (
                anchored[
                    "memory_word_count"
                ]
                -
                current[
                    "memory_word_count"
                ]
            ),
        },
    }


def run_experiment_018(
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
    # STEP 1
    # Build each learned compact memory once.
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

    # ================================================================
    # STEP 2
    # Condition A: one full pooled snapshot.
    # ================================================================

    current_snapshot = (
        build_memory_snapshot(
            db_path=(
                snapshot_dir
                /
                "current_full_pool.sqlite3"
            ),
            families=(
                families
            ),
            bundles=(
                bundles
            ),
            embedder=embedder,
            meter=meter,
        )
    )

    # ================================================================
    # STEP 3
    # Condition B: deterministic identity routing.
    #
    # Importantly:
    # selection runs against the same complete family pool.
    #
    # Snapshot construction itself uses zero model calls.
    # ================================================================

    selections = {}
    anchored_snapshots = {}

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        selection = (
            select_identity_candidates(
                query_entities=(
                    family[
                        "entities"
                    ]
                ),
                families=(
                    families
                ),
            )
        )

        selections[
            family_id
        ] = (
            selection
        )

        selected_families = [
            family_by_id[
                selected_id
            ]

            for selected_id
            in selection[
                "candidate_family_ids"
            ]
        ]

        anchored_snapshots[
            family_id
        ] = (
            build_memory_snapshot(
                db_path=(
                    snapshot_dir
                    /
                    (
                        "anchored_"
                        +
                        family_id
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

    # ================================================================
    # STEP 4
    # Paired frozen evaluation.
    # ================================================================

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

    results = [
        run_family_018(
            family=family,
            current_snapshot=(
                current_snapshot
            ),
            anchored_snapshot=(
                anchored_snapshots[
                    family[
                        "id"
                    ]
                ]
            ),
            selection=(
                selections[
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

    family_count = (
        len(
            results
        )
    )

    current_passes = (
        _count(
            results,
            "current",
            "semantic_task_pass",
        )
    )

    anchored_passes = (
        _count(
            results,
            "anchored",
            "semantic_task_pass",
        )
    )

    activation_rescues = sum(
        int(
            row[
                "paired"
            ][
                "activation_rescue"
            ]
        )

        for row
        in results
    )

    activation_harms = sum(
        int(
            row[
                "paired"
            ][
                "activation_harm"
            ]
        )

        for row
        in results
    )

    visibility_rescues = sum(
        int(
            row[
                "paired"
            ][
                "visibility_rescue"
            ]
        )

        for row
        in results
    )

    fallback_queries = sum(
        int(
            row[
                "identity_selection"
            ][
                "fallback_used"
            ]
        )

        for row
        in results
    )

    target_selected = sum(
        int(
            row[
                "identity_selection"
            ][
                "target_selected"
            ]
        )

        for row
        in results
    )

    # ================================================================
    # Strict target-memory equality controls.
    # ================================================================

    target_lessons_equal = True
    target_sources_equal = True

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        current_record = (
            _learned_record(
                current_snapshot,
                family_id,
            )
        )

        anchored_record = (
            _learned_record(
                anchored_snapshots[
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
            anchored_record[
                "lesson_sha256"
            ]
        ):

            target_lessons_equal = False

        if (
            current_record[
                "source_evidence_sha256"
            ]
            !=
            anchored_record[
                "source_evidence_sha256"
            ]
        ):

            target_sources_equal = False

    report = {
        "experiment": (
            "seed-growth-018"
        ),

        "classification": (
            "exploratory-fresh-identity-"
            "anchored-activation-ablation"
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
            type(
                model
            ).__name__,
        ),

        "embedder": getattr(
            embedder,
            "name",
            type(
                embedder
            ).__name__,
        ),

        "meter": getattr(
            meter,
            "name",
            type(
                meter
            ).__name__,
        ),

        "task_count": (
            family_count
        ),

        "pool_size": (
            len(
                families
            )
        ),

        "identity_anchor_prefixes": list(
            IDENTITY_ANCHOR_PREFIXES
        ),

        "conditions": {
            "A": (
                "full_pool_current_rrf"
            ),

            "B": (
                "same_pool_exact_identity_candidate_"
                "selection_then_current_rrf"
            ),
        },

        # ------------------------------------------------------------
        # Behavior
        # ------------------------------------------------------------

        "current_task_passes": (
            current_passes
        ),

        "anchored_task_passes": (
            anchored_passes
        ),

        "current_task_pass_rate": (
            current_passes
            /
            family_count
            if family_count
            else 0.0
        ),

        "anchored_task_pass_rate": (
            anchored_passes
            /
            family_count
            if family_count
            else 0.0
        ),

        "current_semantic_violations": (
            _count(
                results,
                "current",
                "semantic_violation",
            )
        ),

        "anchored_semantic_violations": (
            _count(
                results,
                "anchored",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # Activation
        # ------------------------------------------------------------

        "current_target_clause_visible_families": (
            _count(
                results,
                "current",
                "target_clause_visible",
            )
        ),

        "anchored_target_clause_visible_families": (
            _count(
                results,
                "anchored",
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

        "anchored_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "anchored"
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

        "anchored_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "anchored",
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

        "mean_anchored_retrieval_precision": (
            _mean(
                row[
                    "anchored"
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

        "mean_anchored_retrieval_recall": (
            _mean(
                row[
                    "anchored"
                ][
                    "retrieval_recall"
                ]

                for row
                in results
            )
        ),

        "current_wrong_rule_contamination_families": (
            _count(
                results,
                "current",
                "wrong_rule_contamination",
            )
        ),

        "anchored_wrong_rule_contamination_families": (
            _count(
                results,
                "anchored",
                "wrong_rule_contamination",
            )
        ),

        # ------------------------------------------------------------
        # Paired effects
        # ------------------------------------------------------------

        "activation_rescue_families": (
            activation_rescues
        ),

        "activation_harm_families": (
            activation_harms
        ),

        "visibility_rescue_families": (
            visibility_rescues
        ),

        # ------------------------------------------------------------
        # Candidate routing
        # ------------------------------------------------------------

        "identity_target_selected_families": (
            target_selected
        ),

        "identity_fallback_queries": (
            fallback_queries
        ),

        "identity_anchor_match_queries": (
            family_count
            -
            fallback_queries
        ),

        "mean_identity_candidate_count": (
            _mean(
                row[
                    "identity_selection"
                ][
                    "candidate_count"
                ]

                for row
                in results
            )
        ),

        "mean_identity_candidate_precision": (
            _mean(
                row[
                    "identity_selection"
                ][
                    "candidate_precision"
                ]

                for row
                in results
            )
        ),

        "mean_identity_candidate_recall": (
            _mean(
                row[
                    "identity_selection"
                ][
                    "candidate_recall"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # Context cost
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

        "mean_anchored_memory_words": (
            _mean(
                row[
                    "anchored"
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

        "mean_anchored_memory_segments": (
            _mean(
                row[
                    "anchored"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # Cluster analysis
        # ------------------------------------------------------------

        "current_cluster_metrics": (
            aggregate_activation_clusters(
                results,
                "current",
            )
        ),

        "anchored_cluster_metrics": (
            aggregate_activation_clusters(
                results,
                "anchored",
            )
        ),

        # ------------------------------------------------------------
        # Memory safety
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
        # Resource accounting
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

        "anchored_transfer_model_calls": (
            family_count
        ),

        "identity_router_model_calls": 0,

        "snapshot_construction_model_calls": 0,

        # ------------------------------------------------------------
        # Controls
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

        "all_identity_selection_from_same_full_pool": True,

        "identity_router_used_family_id": False,

        "identity_router_used_semantic_clause": False,

        "identity_router_used_semantic_grader": False,

        "identity_router_used_model": False,

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
        output
    )


def main():
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_018.json"
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
        run_experiment_018(
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

        "pool_size",

        "current_task_passes",
        "anchored_task_passes",

        "current_task_pass_rate",
        "anchored_task_pass_rate",

        "current_semantic_violations",
        "anchored_semantic_violations",

        "current_target_clause_visible_families",
        "anchored_target_clause_visible_families",

        "current_families_with_wrong_memory_presented",
        "anchored_families_with_wrong_memory_presented",

        "current_wrong_family_clause_occurrences",
        "anchored_wrong_family_clause_occurrences",

        "mean_current_retrieval_precision",
        "mean_anchored_retrieval_precision",

        "mean_current_retrieval_recall",
        "mean_anchored_retrieval_recall",

        "current_wrong_rule_contamination_families",
        "anchored_wrong_rule_contamination_families",

        "activation_rescue_families",
        "activation_harm_families",
        "visibility_rescue_families",

        "identity_target_selected_families",
        "identity_anchor_match_queries",
        "identity_fallback_queries",

        "mean_identity_candidate_count",
        "mean_identity_candidate_precision",
        "mean_identity_candidate_recall",

        "mean_current_memory_words",
        "mean_anchored_memory_words",

        "mean_current_memory_segments",
        "mean_anchored_memory_segments",

        "current_cluster_metrics",
        "anchored_cluster_metrics",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "identity_router_model_calls",

        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",
        "all_transfer_queries_equal",
        "all_compact_renderers_equal",
        "all_context_budget_configuration_equal",
        "all_reasoners_equal",
        "all_identity_selection_from_same_full_pool",

        "identity_router_used_family_id",
        "identity_router_used_semantic_clause",
        "identity_router_used_semantic_grader",
        "identity_router_used_model",
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
