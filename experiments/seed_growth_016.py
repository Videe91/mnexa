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


from experiments.seed_growth_011 import (
    admit_structured_propositions,
)

from experiments.seed_growth_013 import (
    _build_repaired_structure,
    _run_memory_condition,
    semantic_closed_projection,
)

from experiments.seed_growth_014 import (
    ensure_fallback_challenges,
    fallback_projection,
    reconcile_support_first,
    render_lossless_semantic_memory,
)

from experiments.seed_growth_015 import (
    compact_semantic_projection,
    render_compact_semantic_memory,
)


TRANSFER_ATTEMPTS_PER_CONDITION = 3


def _sha256_text(
    text: str,
) -> str:

    return (
        hashlib
        .sha256(
            text.encode(
                "utf-8"
            )
        )
        .hexdigest()
    )


def _sha256_json(
    payload,
) -> str:

    return _sha256_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )
    )


def replicate_condition_names(
    condition_name: str,
    attempts: int,
):
    return [
        (
            f"{condition_name}"
            f"_r{index}"
        )

        for index
        in range(
            1,
            attempts + 1,
        )
    ]


def is_majority_pass(
    *,
    passes: int,
    attempts: int,
) -> bool:

    if attempts <= 0:
        return False

    return (
        passes
        >
        attempts / 2
    )


def summarize_boolean_replicates(
    values,
):
    attempts = (
        len(
            values
        )
    )

    passes = sum(
        int(
            value
        )

        for value
        in values
    )

    return {
        "attempts": (
            attempts
        ),

        "passes": (
            passes
        ),

        "failures": (
            attempts
            -
            passes
        ),

        "pass_rate": (
            passes / attempts
            if attempts
            else 0.0
        ),

        "majority_pass": (
            is_majority_pass(
                passes=passes,
                attempts=attempts,
            )
        ),

        "unanimous_pass": (
            attempts > 0
            and
            passes == attempts
        ),
    }


def replicate_memory_consistent(
    replicates,
):
    lesson_texts = {
        replicate[
            "lesson"
        ]

        for replicate
        in replicates
    }

    word_counts = {
        int(
            replicate[
                "memory_word_count"
            ]
        )

        for replicate
        in replicates
    }

    return {
        "lesson_text_equal": (
            len(
                lesson_texts
            )
            <= 1
        ),

        "memory_word_count_equal": (
            len(
                word_counts
            )
            <= 1
        ),
    }


def _aggregate_group_stability(
    rows,
    group_key,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "attempts": 0,
            "passes": 0,
            "majority_family_passes": 0,
            "unanimous_family_passes": 0,
        }
    )

    for row in rows:

        key = (
            row[
                group_key
            ]
        )

        summary = (
            row[
                "summary"
            ]
        )

        grouped[
            key
        ][
            "families"
        ] += 1

        grouped[
            key
        ][
            "attempts"
        ] += int(
            summary[
                "attempts"
            ]
        )

        grouped[
            key
        ][
            "passes"
        ] += int(
            summary[
                "passes"
            ]
        )

        grouped[
            key
        ][
            "majority_family_passes"
        ] += int(
            summary[
                "majority_pass"
            ]
        )

        grouped[
            key
        ][
            "unanimous_family_passes"
        ] += int(
            summary[
                "unanimous_pass"
            ]
        )

    result = {}

    for key, stats in sorted(
        grouped.items()
    ):

        attempts = (
            stats[
                "attempts"
            ]
        )

        result[
            key
        ] = {
            **stats,

            "failures": (
                attempts
                -
                stats[
                    "passes"
                ]
            ),

            "pass_rate": (
                stats[
                    "passes"
                ]
                /
                attempts
                if attempts
                else 0.0
            ),
        }

    return result


def aggregate_operator_stability(
    rows,
):
    return (
        _aggregate_group_stability(
            rows,
            "semantic_operator",
        )
    )


def aggregate_dimension_stability(
    rows,
):
    return (
        _aggregate_group_stability(
            rows,
            "semantic_dimension",
        )
    )


def run_transfer_replicates(
    *,
    condition_name: str,
    attempts: int,
    family,
    family_dir: Path,
    model,
    embedder,
    meter,
    lesson_text: str,
    evidence_atoms,
):
    """
    Every replicate uses a different SQLite database because
    _run_memory_condition derives the DB filename from condition_name.

    Therefore previous transfer decisions cannot contaminate later
    transfer attempts.
    """

    names = (
        replicate_condition_names(
            condition_name,
            attempts,
        )
    )

    return [
        _run_memory_condition(
            condition_name=name,
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=lesson_text,
            evidence_atoms=evidence_atoms,
        )

        for name
        in names
    ]


def _condition_family_summary(
    replicates,
):
    semantic = (
        summarize_boolean_replicates(
            [
                replicate[
                    "semantic_task_pass"
                ]

                for replicate
                in replicates
            ]
        )
    )

    violations = sum(
        int(
            replicate[
                "semantic_violation"
            ]
        )

        for replicate
        in replicates
    )

    unsupported = sum(
        int(
            replicate[
                "unsupported_claims_admitted"
            ]
        )

        for replicate
        in replicates
    )

    memory_consistency = (
        replicate_memory_consistent(
            replicates
        )
    )

    clause_visible = all(
        replicate[
            "semantic_clause_visible"
        ]

        for replicate
        in replicates
    )

    lesson_complete = all(
        replicate[
            "lesson_knowledge_complete"
        ]

        for replicate
        in replicates
    )

    mean_memory_words = (
        sum(
            float(
                replicate[
                    "memory_word_count"
                ]
            )

            for replicate
            in replicates
        )
        /
        len(
            replicates
        )
        if replicates
        else 0.0
    )

    return {
        **semantic,

        "semantic_violations": (
            violations
        ),

        "unsupported_claims_admitted": (
            unsupported
        ),

        "exact_semantic_clause_visible": (
            clause_visible
        ),

        "lesson_complete": (
            lesson_complete
        ),

        "mean_memory_words": (
            mean_memory_words
        ),

        **memory_consistency,
    }


def run_family_016(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
):
    family_dir = (
        Path(
            work_dir
        )
        /
        family[
            "id"
        ]
    )

    family_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_text = (
        family[
            "raw_source"
        ]
    )

    # ================================================================
    # ONE INITIAL EXTRACTION + ONE REPAIR
    # ================================================================

    repair_run = (
        _build_repaired_structure(
            family=family,
            model=model,
        )
    )

    raw_repair_payload = (
        repair_run[
            "repair_payload"
        ]
    )

    (
        shared_repair_proposal,
        fallback_challenge_ids,
    ) = (
        ensure_fallback_challenges(
            repair_payload=(
                raw_repair_payload
            ),
            family=family,
        )
    )

    repair_proposal_sha256 = (
        _sha256_json(
            shared_repair_proposal
        )
    )

    # ================================================================
    # ONE SHARED GROUNDING + FALLBACK RECONCILIATION
    # ================================================================

    structured_gate = (
        admit_structured_propositions(
            proposal=(
                shared_repair_proposal
            ),
            source_text=(
                source_text
            ),
        )
    )

    reconciled = (
        reconcile_support_first(
            proposal=(
                shared_repair_proposal
            ),
            source_text=(
                source_text
            ),
            structured_gate=(
                structured_gate
            ),
        )
    )

    structured = (
        reconciled[
            "structured"
        ]
    )

    fallback = (
        reconciled[
            "fallback"
        ]
    )

    structured_sha256 = (
        _sha256_json(
            structured
        )
    )

    fallback_sha256 = (
        _sha256_json(
            fallback
        )
    )

    # ================================================================
    # CONDITION A — SEED 014 VERBOSE LOSSLESS REPRESENTATION
    # ================================================================

    verbose_lesson = (
        render_lossless_semantic_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    verbose_atoms = (
        semantic_closed_projection(
            structured
        )
        +
        fallback_projection(
            fallback
        )
    )

    verbose_replicates = (
        run_transfer_replicates(
            condition_name=(
                "verbose"
            ),
            attempts=(
                TRANSFER_ATTEMPTS_PER_CONDITION
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                verbose_lesson
            ),
            evidence_atoms=(
                verbose_atoms
            ),
        )
    )

    # ================================================================
    # CONDITION B — SEED 015 COMPACT REPRESENTATION
    # ================================================================

    compact_lesson = (
        render_compact_semantic_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    compact_atoms = (
        compact_semantic_projection(
            structured=structured,
            fallback=fallback,
        )
    )

    compact_replicates = (
        run_transfer_replicates(
            condition_name=(
                "compact"
            ),
            attempts=(
                TRANSFER_ATTEMPTS_PER_CONDITION
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                compact_lesson
            ),
            evidence_atoms=(
                compact_atoms
            ),
        )
    )

    # ================================================================
    # STRICT CONTROLS
    # ================================================================

    source_hashes = {
        replicate[
            "source_evidence_sha256"
        ]

        for replicate
        in (
            verbose_replicates
            +
            compact_replicates
        )
    }

    same_source_evidence = (
        len(
            source_hashes
        )
        == 1
    )

    if not same_source_evidence:

        raise RuntimeError(
            "016 invalid: source evidence differs "
            "between transfer replicates."
        )

    verbose_summary = (
        _condition_family_summary(
            verbose_replicates
        )
    )

    compact_summary = (
        _condition_family_summary(
            compact_replicates
        )
    )

    if not (
        verbose_summary[
            "lesson_text_equal"
        ]
        and
        compact_summary[
            "lesson_text_equal"
        ]
    ):

        raise RuntimeError(
            "016 invalid: lesson text changed "
            "within transfer replicates."
        )

    if not (
        verbose_summary[
            "memory_word_count_equal"
        ]
        and
        compact_summary[
            "memory_word_count_equal"
        ]
    ):

        raise RuntimeError(
            "016 invalid: memory size changed "
            "within condition replicates."
        )

    return {
        "family_id": (
            family[
                "id"
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

        "shared": {
            "repair_proposal_sha256": (
                repair_proposal_sha256
            ),

            "structured_sha256": (
                structured_sha256
            ),

            "fallback_sha256": (
                fallback_sha256
            ),

            "fallback_challenge_ids": (
                fallback_challenge_ids
            ),

            "structured": (
                structured
            ),

            "fallback": (
                fallback
            ),
        },

        "verbose": {
            "summary": (
                verbose_summary
            ),

            "replicates": (
                verbose_replicates
            ),

            "rendered_memory": (
                verbose_lesson
            ),
        },

        "compact": {
            "summary": (
                compact_summary
            ),

            "replicates": (
                compact_replicates
            ),

            "rendered_memory": (
                compact_lesson
            ),
        },

        "same_source_evidence": (
            same_source_evidence
        ),

        "same_initial_structured_proposal": True,

        "same_repair_proposal": True,

        "same_structured_admissions": True,

        "same_fallback_records": True,

        "call_pass_delta_compact_minus_verbose": (
            compact_summary[
                "passes"
            ]
            -
            verbose_summary[
                "passes"
            ]
        ),

        "majority_delta_compact_minus_verbose": (
            int(
                compact_summary[
                    "majority_pass"
                ]
            )
            -
            int(
                verbose_summary[
                    "majority_pass"
                ]
            )
        ),
    }


def _sum_condition_metric(
    results,
    condition,
    metric,
):
    return sum(
        float(
            family[
                condition
            ][
                "summary"
            ][
                metric
            ]
        )

        for family
        in results
    )


def _count_condition_bool(
    results,
    condition,
    metric,
):
    return sum(
        int(
            family[
                condition
            ][
                "summary"
            ][
                metric
            ]
        )

        for family
        in results
    )


def _condition_group_rows(
    results,
    condition,
):
    return [
        {
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

            "summary": (
                family[
                    condition
                ][
                    "summary"
                ]
            ),
        }

        for family
        in results
    ]


def run_experiment_016(
    *,
    tasks_path: Path,
    results_dir: Path,
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

    state_dir = (
        run_dir
        /
        "state"
    )

    state_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = [
        run_family_016(
            family=family,
            work_dir=state_dir,
            model=model,
            embedder=embedder,
            meter=meter,
        )

        for family
        in payload[
            "families"
        ]
    ]

    family_count = (
        len(
            results
        )
    )

    attempts_per_condition = (
        family_count
        *
        TRANSFER_ATTEMPTS_PER_CONDITION
    )

    verbose_passes = int(
        _sum_condition_metric(
            results,
            "verbose",
            "passes",
        )
    )

    compact_passes = int(
        _sum_condition_metric(
            results,
            "compact",
            "passes",
        )
    )

    verbose_violations = int(
        _sum_condition_metric(
            results,
            "verbose",
            "semantic_violations",
        )
    )

    compact_violations = int(
        _sum_condition_metric(
            results,
            "compact",
            "semantic_violations",
        )
    )

    verbose_operator = (
        aggregate_operator_stability(
            _condition_group_rows(
                results,
                "verbose",
            )
        )
    )

    compact_operator = (
        aggregate_operator_stability(
            _condition_group_rows(
                results,
                "compact",
            )
        )
    )

    verbose_dimension = (
        aggregate_dimension_stability(
            _condition_group_rows(
                results,
                "verbose",
            )
        )
    )

    compact_dimension = (
        aggregate_dimension_stability(
            _condition_group_rows(
                results,
                "compact",
            )
        )
    )

    mean_verbose_words = (
        _sum_condition_metric(
            results,
            "verbose",
            "mean_memory_words",
        )
        /
        family_count
        if family_count
        else 0.0
    )

    mean_compact_words = (
        _sum_condition_metric(
            results,
            "compact",
            "mean_memory_words",
        )
        /
        family_count
        if family_count
        else 0.0
    )

    if mean_verbose_words:

        memory_reduction_fraction = (
            (
                mean_verbose_words
                -
                mean_compact_words
            )
            /
            mean_verbose_words
        )

    else:

        memory_reduction_fraction = 0.0

    report = {
        "experiment": (
            "seed-growth-016"
        ),

        "classification": (
            "exploratory-fresh-compact-"
            "semantic-stability-ablation"
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

        "transfer_attempts_per_condition_per_family": (
            TRANSFER_ATTEMPTS_PER_CONDITION
        ),

        "transfer_attempts_per_condition": (
            attempts_per_condition
        ),

        "conditions": {
            "A": (
                "seed_014_verbose_lossless_"
                "semantic_memory"
            ),

            "B": (
                "seed_015_compact_"
                "semantic_memory"
            ),
        },

        # ------------------------------------------------------------
        # Per-call stability
        # ------------------------------------------------------------

        "verbose_transfer_call_passes": (
            verbose_passes
        ),

        "compact_transfer_call_passes": (
            compact_passes
        ),

        "verbose_transfer_call_failures": (
            attempts_per_condition
            -
            verbose_passes
        ),

        "compact_transfer_call_failures": (
            attempts_per_condition
            -
            compact_passes
        ),

        "verbose_transfer_call_pass_rate": (
            verbose_passes
            /
            attempts_per_condition
            if attempts_per_condition
            else 0.0
        ),

        "compact_transfer_call_pass_rate": (
            compact_passes
            /
            attempts_per_condition
            if attempts_per_condition
            else 0.0
        ),

        "verbose_semantic_violations": (
            verbose_violations
        ),

        "compact_semantic_violations": (
            compact_violations
        ),

        # ------------------------------------------------------------
        # Per-family stability
        # ------------------------------------------------------------

        "verbose_majority_family_passes": (
            _count_condition_bool(
                results,
                "verbose",
                "majority_pass",
            )
        ),

        "compact_majority_family_passes": (
            _count_condition_bool(
                results,
                "compact",
                "majority_pass",
            )
        ),

        "verbose_unanimous_family_passes": (
            _count_condition_bool(
                results,
                "verbose",
                "unanimous_pass",
            )
        ),

        "compact_unanimous_family_passes": (
            _count_condition_bool(
                results,
                "compact",
                "unanimous_pass",
            )
        ),

        # ------------------------------------------------------------
        # Evidence / knowledge
        # ------------------------------------------------------------

        "verbose_exact_semantic_clause_visible_families": (
            _count_condition_bool(
                results,
                "verbose",
                "exact_semantic_clause_visible",
            )
        ),

        "compact_exact_semantic_clause_visible_families": (
            _count_condition_bool(
                results,
                "compact",
                "exact_semantic_clause_visible",
            )
        ),

        "verbose_complete_lessons": (
            _count_condition_bool(
                results,
                "verbose",
                "lesson_complete",
            )
        ),

        "compact_complete_lessons": (
            _count_condition_bool(
                results,
                "compact",
                "lesson_complete",
            )
        ),

        "verbose_unsupported_claims_admitted": int(
            _sum_condition_metric(
                results,
                "verbose",
                "unsupported_claims_admitted",
            )
        ),

        "compact_unsupported_claims_admitted": int(
            _sum_condition_metric(
                results,
                "compact",
                "unsupported_claims_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Representation cost
        # ------------------------------------------------------------

        "mean_verbose_memory_words": (
            mean_verbose_words
        ),

        "mean_compact_memory_words": (
            mean_compact_words
        ),

        "mean_memory_word_reduction": (
            mean_verbose_words
            -
            mean_compact_words
        ),

        "mean_memory_word_reduction_fraction": (
            memory_reduction_fraction
        ),

        # ------------------------------------------------------------
        # Operator / dimension stability
        # ------------------------------------------------------------

        "verbose_operator_stability": (
            verbose_operator
        ),

        "compact_operator_stability": (
            compact_operator
        ),

        "verbose_dimension_stability": (
            verbose_dimension
        ),

        "compact_dimension_stability": (
            compact_dimension
        ),

        # ------------------------------------------------------------
        # Model calls
        # ------------------------------------------------------------

        "initial_extraction_model_calls": (
            family_count
        ),

        "repair_model_calls": (
            family_count
        ),

        "verbose_projection_model_calls": 0,

        "compact_projection_model_calls": 0,

        "verbose_transfer_model_calls": (
            attempts_per_condition
        ),

        "compact_transfer_model_calls": (
            attempts_per_condition
        ),

        # ------------------------------------------------------------
        # Strict controls
        # ------------------------------------------------------------

        "all_source_evidence_equal": all(
            family[
                "same_source_evidence"
            ]

            for family
            in results
        ),

        "all_initial_structured_proposals_equal": all(
            family[
                "same_initial_structured_proposal"
            ]

            for family
            in results
        ),

        "all_repair_proposals_equal": all(
            family[
                "same_repair_proposal"
            ]

            for family
            in results
        ),

        "all_structured_admissions_equal": all(
            family[
                "same_structured_admissions"
            ]

            for family
            in results
        ),

        "all_fallback_records_equal": all(
            family[
                "same_fallback_records"
            ]

            for family
            in results
        ),

        "all_verbose_replica_lessons_equal": all(
            family[
                "verbose"
            ][
                "summary"
            ][
                "lesson_text_equal"
            ]

            for family
            in results
        ),

        "all_compact_replica_lessons_equal": all(
            family[
                "compact"
            ][
                "summary"
            ][
                "lesson_text_equal"
            ]

            for family
            in results
        ),

        "all_verbose_replica_memory_sizes_equal": all(
            family[
                "verbose"
            ][
                "summary"
            ][
                "memory_word_count_equal"
            ]

            for family
            in results
        ),

        "all_compact_replica_memory_sizes_equal": all(
            family[
                "compact"
            ][
                "summary"
            ][
                "memory_word_count_equal"
            ]

            for family
            in results
        ),

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
    from model_adapter import (
        OpenAIResponsesModel,
        SentenceTransformerEmbedder,
        WordMeter,
    )

    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_016.json"
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
        run_experiment_016(
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

        "transfer_attempts_per_condition_per_family",
        "transfer_attempts_per_condition",

        "verbose_transfer_call_passes",
        "compact_transfer_call_passes",

        "verbose_transfer_call_pass_rate",
        "compact_transfer_call_pass_rate",

        "verbose_semantic_violations",
        "compact_semantic_violations",

        "verbose_majority_family_passes",
        "compact_majority_family_passes",

        "verbose_unanimous_family_passes",
        "compact_unanimous_family_passes",

        "verbose_exact_semantic_clause_visible_families",
        "compact_exact_semantic_clause_visible_families",

        "verbose_complete_lessons",
        "compact_complete_lessons",

        "verbose_unsupported_claims_admitted",
        "compact_unsupported_claims_admitted",

        "mean_verbose_memory_words",
        "mean_compact_memory_words",
        "mean_memory_word_reduction_fraction",

        "verbose_operator_stability",
        "compact_operator_stability",

        "verbose_dimension_stability",
        "compact_dimension_stability",

        "all_source_evidence_equal",
        "all_initial_structured_proposals_equal",
        "all_repair_proposals_equal",
        "all_structured_admissions_equal",
        "all_fallback_records_equal",

        "all_verbose_replica_lessons_equal",
        "all_compact_replica_lessons_equal",
        "all_verbose_replica_memory_sizes_equal",
        "all_compact_replica_memory_sizes_equal",
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
