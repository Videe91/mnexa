from __future__ import annotations

import argparse
import hashlib
import json
import os

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
)

from experiments.seed_growth_014 import (
    ensure_fallback_challenges,
    fallback_projection,
    reconcile_support_first,
    render_lossless_semantic_memory,
)


COMPACT_HEADER = """
COMPACT SEMANTIC MEMORY

Exact EVIDENCE text is authoritative.
Retrieval handles are not standalone claims.
Preserve negation, scope, cardinality, conditions, exceptions,
ordering, and other decision-relevant meaning from EVIDENCE.
""".strip()


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


def _support_key(
    item,
):
    """
    Exact physical support identity.

    Do not deduplicate merely by text:
    identical text at different source locations is distinct evidence.
    """

    return (
        item[
            "source_sha256"
        ],
        item[
            "source_start"
        ],
        item[
            "source_end"
        ],
        item[
            "support_span_sha256"
        ],
    )


def build_compact_memory(
    *,
    structured,
    fallback,
):
    """
    Build a deterministic support index.

    Each unique physical support span appears once.

    Structured proposition handles and unresolved fallback records
    reference that evidence by ID.
    """

    evidence_by_key = {}
    evidence_order = []

    def register(
        item,
    ):
        key = (
            _support_key(
                item
            )
        )

        if (
            key
            not in
            evidence_by_key
        ):
            evidence_id = (
                f"E{len(evidence_order) + 1}"
            )

            record = {
                "id": (
                    evidence_id
                ),
                "text": (
                    item[
                        "source_quote"
                    ]
                ),
                "source_quote": (
                    item[
                        "source_quote"
                    ]
                ),
                "source_start": (
                    item[
                        "source_start"
                    ]
                ),
                "source_end": (
                    item[
                        "source_end"
                    ]
                ),
                "source_role": (
                    item[
                        "source_role"
                    ]
                ),
                "source_sha256": (
                    item[
                        "source_sha256"
                    ]
                ),
                "support_span_sha256": (
                    item[
                        "support_span_sha256"
                    ]
                ),
            }

            evidence_by_key[
                key
            ] = (
                record
            )

            evidence_order.append(
                record
            )

        return (
            evidence_by_key[
                key
            ][
                "id"
            ]
        )

    references = []

    for proposition in structured:

        evidence_id = (
            register(
                proposition
            )
        )

        references.append(
            {
                "id": (
                    proposition[
                        "id"
                    ]
                ),
                "reference_type": (
                    "structured"
                ),
                "retrieval_handle": (
                    proposition[
                        "nucleus_quote"
                    ]
                ),
                "evidence_id": (
                    evidence_id
                ),
                "qualifiers": (
                    proposition.get(
                        "qualifiers",
                        [],
                    )
                ),
            }
        )

    for item in fallback:

        evidence_id = (
            register(
                item
            )
        )

        references.append(
            {
                "id": (
                    item[
                        "id"
                    ]
                ),
                "reference_type": (
                    "unresolved"
                ),
                "retrieval_handle": None,
                "evidence_id": (
                    evidence_id
                ),
                "qualifiers": [],
            }
        )

    return {
        "evidence": (
            evidence_order
        ),
        "references": (
            references
        ),
    }


def compact_semantic_projection(
    *,
    structured,
    fallback,
):
    """
    Reusable claim/evidence projection.

    One projected evidence atom per unique physical support span.

    No semantic rewriting.
    """

    payload = (
        build_compact_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    return [
        {
            "id": (
                item[
                    "id"
                ]
            ),
            "text": (
                item[
                    "text"
                ]
            ),
            "source_quote": (
                item[
                    "source_quote"
                ]
            ),
            "source_start": (
                item[
                    "source_start"
                ]
            ),
            "source_end": (
                item[
                    "source_end"
                ]
            ),
            "source_role": (
                item[
                    "source_role"
                ]
            ),
            "source_sha256": (
                item[
                    "source_sha256"
                ]
            ),
            "span_sha256": (
                item[
                    "support_span_sha256"
                ]
            ),
        }

        for item
        in payload[
            "evidence"
        ]
    ]


def render_compact_semantic_memory(
    *,
    structured,
    fallback,
) -> str:

    payload = (
        build_compact_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    lines = [
        COMPACT_HEADER,
        "",
        "EVIDENCE:",
    ]

    if not payload[
        "evidence"
    ]:

        lines.append(
            "(none)"
        )

    for evidence in payload[
        "evidence"
    ]:

        lines.append(
            f"[{evidence['id']} "
            f"role={evidence['source_role']} "
            f"span="
            f"{evidence['source_start']}:"
            f"{evidence['source_end']}] "
            f"{evidence['text']}"
        )

    lines.extend(
        [
            "",
            "REFERENCES:",
        ]
    )

    if not payload[
        "references"
    ]:

        lines.append(
            "(none)"
        )

    for reference in payload[
        "references"
    ]:

        if (
            reference[
                "reference_type"
            ]
            ==
            "structured"
        ):

            lines.append(
                f"[{reference['id']}] "
                f"HANDLE="
                f"{json.dumps(reference['retrieval_handle'])} "
                f"-> "
                f"{reference['evidence_id']}"
            )

            for qualifier in reference.get(
                "qualifiers",
                [],
            ):

                lines.append(
                    "  META "
                    f"{qualifier['type']}="
                    f"{json.dumps(qualifier['source_quote'])}"
                )

        else:

            lines.append(
                f"[{reference['id']}] "
                "UNRESOLVED "
                f"-> "
                f"{reference['evidence_id']}"
            )

    return "\n".join(
        lines
    )


def render_verbose_reference_fixture(
    *,
    structured,
):
    """
    Test helper representing the pre-compaction duplication pattern.
    """

    lines = []

    for proposition in structured:

        lines.append(
            "HANDLE: "
            +
            proposition[
                "nucleus_quote"
            ]
        )

        lines.append(
            "AUTHORITATIVE_SEMANTIC_PAYLOAD: "
            +
            proposition[
                "source_quote"
            ]
        )

    return "\n".join(
        lines
    )


def compaction_stats(
    *,
    structured,
    fallback,
):
    input_occurrences = (
        len(
            structured
        )
        +
        len(
            fallback
        )
    )

    payload = (
        build_compact_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    unique = (
        len(
            payload[
                "evidence"
            ]
        )
    )

    return {
        "input_support_occurrences": (
            input_occurrences
        ),
        "unique_support_records": (
            unique
        ),
        "duplicate_support_occurrences_removed": (
            input_occurrences
            -
            unique
        ),
    }


def _word_count(
    meter,
    text,
):
    return (
        meter.count(
            text
        )
    )


def run_family_015(
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

    shared_repair_sha256 = (
        _sha256_json(
            shared_repair_proposal
        )
    )

    # ================================================================
    # ONE SHARED STRUCTURED GATE + ONE SHARED FALLBACK RECONCILIATION
    #
    # Both conditions consume the exact same structure and fallback.
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
    # CONDITION A
    #
    # Seed 014 verbose lossless semantic rendering.
    # ================================================================

    verbose_lesson = (
        render_lossless_semantic_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    # Preserve 014's projection behavior:
    # structured supports are emitted per proposition,
    # fallback supports per fallback record.
    from experiments.seed_growth_013 import (
        semantic_closed_projection,
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

    verbose = (
        _run_memory_condition(
            condition_name=(
                "lossless_verbose"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
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
    # CONDITION B
    #
    # Exact same structure + exact same fallback.
    #
    # Only representation is compacted.
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

    compact = (
        _run_memory_condition(
            condition_name=(
                "lossless_compact"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
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

    same_source = (
        verbose[
            "source_evidence_sha256"
        ]
        ==
        compact[
            "source_evidence_sha256"
        ]
    )

    if not same_source:
        raise RuntimeError(
            "015 invalid: source evidence differs."
        )

    stats = (
        compaction_stats(
            structured=structured,
            fallback=fallback,
        )
    )

    verbose_words = (
        _word_count(
            meter,
            verbose_lesson,
        )
    )

    compact_words = (
        _word_count(
            meter,
            compact_lesson,
        )
    )

    if (
        verbose_words
        > 0
    ):
        reduction_fraction = (
            (
                verbose_words
                -
                compact_words
            )
            /
            verbose_words
        )

    else:
        reduction_fraction = 0.0

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
                shared_repair_sha256
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

            "hard_support_rejections": (
                reconciled[
                    "hard_rejections"
                ]
            ),
        },

        "verbose": {
            **verbose,

            "rendering": (
                "seed_014_lossless_verbose"
            ),

            "rendered_memory": (
                verbose_lesson
            ),

            "rendered_memory_words": (
                verbose_words
            ),

            "projected_evidence_count": (
                len(
                    verbose_atoms
                )
            ),
        },

        "compact": {
            **compact,

            "rendering": (
                "deduplicated_evidence_index"
            ),

            "rendered_memory": (
                compact_lesson
            ),

            "rendered_memory_words": (
                compact_words
            ),

            "projected_evidence_count": (
                len(
                    compact_atoms
                )
            ),
        },

        "compaction": {
            **stats,

            "verbose_words": (
                verbose_words
            ),

            "compact_words": (
                compact_words
            ),

            "word_reduction": (
                verbose_words
                -
                compact_words
            ),

            "word_reduction_fraction": (
                reduction_fraction
            ),
        },

        "same_source_evidence": (
            same_source
        ),

        "same_initial_structured_proposal": True,

        "same_repair_proposal": True,

        "same_structured_admissions": True,

        "same_fallback_records": True,

        "semantic_task_delta": (
            int(
                compact[
                    "semantic_task_pass"
                ]
            )
            -
            int(
                verbose[
                    "semantic_task_pass"
                ]
            )
        ),
    }


def _count(
    results,
    condition,
    metric,
):
    return sum(
        int(
            family[
                condition
            ].get(
                metric,
                False,
            )
        )

        for family
        in results
    )


def _sum_metric(
    results,
    condition,
    metric,
):
    return sum(
        int(
            family[
                condition
            ].get(
                metric,
                0,
            )
        )

        for family
        in results
    )


def _mean(
    values,
):
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


def run_experiment_015(
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
        run_family_015(
            family=family,
            work_dir=(
                state_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
        )

        for family
        in payload[
            "families"
        ]
    ]

    verbose_words = [
        family[
            "verbose"
        ][
            "rendered_memory_words"
        ]

        for family
        in results
    ]

    compact_words = [
        family[
            "compact"
        ][
            "rendered_memory_words"
        ]

        for family
        in results
    ]

    duplicate_supports_removed = [
        family[
            "compaction"
        ][
            "duplicate_support_occurrences_removed"
        ]

        for family
        in results
    ]

    input_support_occurrences = [
        family[
            "compaction"
        ][
            "input_support_occurrences"
        ]

        for family
        in results
    ]

    unique_support_records = [
        family[
            "compaction"
        ][
            "unique_support_records"
        ]

        for family
        in results
    ]

    mean_verbose = (
        _mean(
            verbose_words
        )
    )

    mean_compact = (
        _mean(
            compact_words
        )
    )

    if (
        mean_verbose
        > 0
    ):
        mean_reduction_fraction = (
            (
                mean_verbose
                -
                mean_compact
            )
            /
            mean_verbose
        )

    else:
        mean_reduction_fraction = 0.0

    report = {
        "experiment": (
            "seed-growth-015"
        ),

        "classification": (
            "exploratory-fresh-semantic-"
            "closure-compaction-ablation"
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
            len(
                results
            )
        ),

        "conditions": {
            "A": (
                "seed_014_lossless_semantic_memory_verbose"
            ),

            "B": (
                "same_structure_same_fallback_"
                "deduplicated_exact_evidence_index"
            ),
        },

        # ------------------------------------------------------------
        # Correctness
        # ------------------------------------------------------------

        "verbose_semantic_task_passes": (
            _count(
                results,
                "verbose",
                "semantic_task_pass",
            )
        ),

        "compact_semantic_task_passes": (
            _count(
                results,
                "compact",
                "semantic_task_pass",
            )
        ),

        "verbose_semantic_violations": (
            _count(
                results,
                "verbose",
                "semantic_violation",
            )
        ),

        "compact_semantic_violations": (
            _count(
                results,
                "compact",
                "semantic_violation",
            )
        ),

        "verbose_exact_semantic_clause_visible_families": (
            _count(
                results,
                "verbose",
                "semantic_clause_visible",
            )
        ),

        "compact_exact_semantic_clause_visible_families": (
            _count(
                results,
                "compact",
                "semantic_clause_visible",
            )
        ),

        "verbose_complete_lessons": (
            _count(
                results,
                "verbose",
                "lesson_knowledge_complete",
            )
        ),

        "compact_complete_lessons": (
            _count(
                results,
                "compact",
                "lesson_knowledge_complete",
            )
        ),

        # ------------------------------------------------------------
        # Closed-world safety
        # ------------------------------------------------------------

        "verbose_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "verbose",
                "unsupported_claims_admitted",
            )
        ),

        "compact_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "compact",
                "unsupported_claims_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Compaction
        # ------------------------------------------------------------

        "mean_verbose_memory_words": (
            mean_verbose
        ),

        "mean_compact_memory_words": (
            mean_compact
        ),

        "mean_memory_word_reduction": (
            mean_verbose
            -
            mean_compact
        ),

        "mean_memory_word_reduction_fraction": (
            mean_reduction_fraction
        ),

        "total_input_support_occurrences": (
            sum(
                input_support_occurrences
            )
        ),

        "total_unique_support_records": (
            sum(
                unique_support_records
            )
        ),

        "duplicate_support_occurrences_removed": (
            sum(
                duplicate_supports_removed
            )
        ),

        "families_with_smaller_compact_memory": sum(
            int(
                family[
                    "compact"
                ][
                    "rendered_memory_words"
                ]
                <
                family[
                    "verbose"
                ][
                    "rendered_memory_words"
                ]
            )

            for family
            in results
        ),

        "families_with_equal_compact_memory": sum(
            int(
                family[
                    "compact"
                ][
                    "rendered_memory_words"
                ]
                ==
                family[
                    "verbose"
                ][
                    "rendered_memory_words"
                ]
            )

            for family
            in results
        ),

        "families_with_larger_compact_memory": sum(
            int(
                family[
                    "compact"
                ][
                    "rendered_memory_words"
                ]
                >
                family[
                    "verbose"
                ][
                    "rendered_memory_words"
                ]
            )

            for family
            in results
        ),

        # ------------------------------------------------------------
        # Model-call parity
        # ------------------------------------------------------------

        "initial_extraction_model_calls": (
            len(
                results
            )
        ),

        "repair_model_calls": (
            len(
                results
            )
        ),

        "verbose_compaction_model_calls": 0,

        "compact_compaction_model_calls": 0,

        "verbose_transfer_model_calls": (
            len(
                results
            )
        ),

        "compact_transfer_model_calls": (
            len(
                results
            )
        ),

        # ------------------------------------------------------------
        # Controls
        # ------------------------------------------------------------

        "all_source_evidence_equal": (
            all(
                family[
                    "same_source_evidence"
                ]

                for family
                in results
            )
        ),

        "all_initial_structured_proposals_equal": (
            all(
                family[
                    "same_initial_structured_proposal"
                ]

                for family
                in results
            )
        ),

        "all_repair_proposals_equal": (
            all(
                family[
                    "same_repair_proposal"
                ]

                for family
                in results
            )
        ),

        "all_structured_admissions_equal": (
            all(
                family[
                    "same_structured_admissions"
                ]

                for family
                in results
            )
        ),

        "all_fallback_records_equal": (
            all(
                family[
                    "same_fallback_records"
                ]

                for family
                in results
            )
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
            "tasks_015.json"
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
        run_experiment_015(
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

        "verbose_semantic_task_passes",
        "compact_semantic_task_passes",

        "verbose_semantic_violations",
        "compact_semantic_violations",

        "verbose_exact_semantic_clause_visible_families",
        "compact_exact_semantic_clause_visible_families",

        "verbose_complete_lessons",
        "compact_complete_lessons",

        "verbose_unsupported_claims_admitted",
        "compact_unsupported_claims_admitted",

        "mean_verbose_memory_words",
        "mean_compact_memory_words",
        "mean_memory_word_reduction",
        "mean_memory_word_reduction_fraction",

        "total_input_support_occurrences",
        "total_unique_support_records",
        "duplicate_support_occurrences_removed",

        "families_with_smaller_compact_memory",
        "families_with_equal_compact_memory",
        "families_with_larger_compact_memory",

        "all_source_evidence_equal",
        "all_initial_structured_proposals_equal",
        "all_repair_proposals_equal",
        "all_structured_admissions_equal",
        "all_fallback_records_equal",
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
