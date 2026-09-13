from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

from collections import Counter

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


from experiments.seed_growth import (
    grade_text,
)

from experiments.seed_growth_004 import (
    make_fidelity_reasoner,
)

from experiments.seed_growth_006 import (
    admit_claims,
)

from experiments.seed_growth_008 import (
    AUTHORITATIVE_ROLE,
    normalize_span_text,
)

from experiments.seed_growth_011 import (
    admit_structured_propositions,
    build_structured_proposition_prompt,
    ensure_structured_compound_challenges,
    parse_structured_proposal,
    render_structured_propositions,
    structured_source_ancestry_valid,
)

from experiments.seed_growth_012 import (
    build_structure_repair_prompt,
    parse_repair_proposal,
)

from mnexa_seed import (
    MnexaSeed,
)


SEMANTIC_DIMENSIONS = (
    "polarity",
    "scope",
    "cardinality",
    "condition",
)


SEMANTIC_CLOSED_HEADER = """
SEMANTIC-CLOSED GROUNDED KNOWLEDGE

IMPORTANT:

- RETRIEVAL_HANDLE is an indexing / retrieval handle.
- The retrieval handle is not a standalone claim.
- AUTHORITATIVE_SEMANTIC_PAYLOAD is the exact historical evidence
  whose operational meaning must be preserved.
- Do not weaken, invert, broaden, narrow, or otherwise replace the
  semantic payload with the retrieval handle.
- Pay particular attention to:
    negation,
    exclusivity,
    cardinality,
    minimum / maximum bounds,
    exceptions,
    conditions,
    ordering,
    scope.

When acting, preserve the decision-relevant semantics of
AUTHORITATIVE_SEMANTIC_PAYLOAD.
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


def current_nucleus_projection(
    propositions,
):
    """
    Seed 012 / current behavior.

    Reusable claim payload == nucleus.
    """

    return [
        {
            "id": (
                proposition[
                    "id"
                ]
            ),
            "text": (
                proposition[
                    "nucleus_quote"
                ]
            ),
            "source_quote": (
                proposition[
                    "nucleus_quote"
                ]
            ),
            "source_start": (
                proposition[
                    "nucleus_start"
                ]
            ),
            "source_end": (
                proposition[
                    "nucleus_end"
                ]
            ),
            "source_role": (
                proposition[
                    "source_role"
                ]
            ),
            "source_sha256": (
                proposition[
                    "source_sha256"
                ]
            ),
            "span_sha256": (
                proposition[
                    "nucleus_sha256"
                ]
            ),
        }

        for proposition
        in propositions
    ]


def semantic_closed_projection(
    propositions,
):
    """
    Semantic-closed projection.

    The nucleus remains the retrieval/indexing handle.

    The claim payload is instead the exact authoritative support span.

    This experiment deliberately does not infer or rewrite meaning.
    It preserves the historical support string as the reusable
    semantic payload.
    """

    return [
        {
            "id": (
                proposition[
                    "id"
                ]
            ),
            "text": (
                proposition[
                    "source_quote"
                ]
            ),
            "source_quote": (
                proposition[
                    "source_quote"
                ]
            ),
            "source_start": (
                proposition[
                    "source_start"
                ]
            ),
            "source_end": (
                proposition[
                    "source_end"
                ]
            ),
            "source_role": (
                proposition[
                    "source_role"
                ]
            ),
            "source_sha256": (
                proposition[
                    "source_sha256"
                ]
            ),
            "span_sha256": (
                proposition[
                    "support_span_sha256"
                ]
            ),
            "retrieval_handle": (
                proposition[
                    "nucleus_quote"
                ]
            ),
        }

        for proposition
        in propositions
    ]


def render_semantic_closed_propositions(
    propositions,
) -> str:

    if not propositions:
        return (
            SEMANTIC_CLOSED_HEADER
            +
            "\n\n"
            +
            "SUPPORTED SEMANTIC PAYLOADS:\n"
            +
            "(none admitted)"
        )

    lines = [
        SEMANTIC_CLOSED_HEADER,
        "",
        "SUPPORTED SEMANTIC PAYLOADS:",
    ]

    for proposition in propositions:

        lines.append(
            "- "
            f"[{proposition['id']} "
            f"role="
            f"{proposition['source_role']} "
            f"support_span="
            f"{proposition['source_start']}:"
            f"{proposition['source_end']} "
            f"handle_span="
            f"{proposition['nucleus_start']}:"
            f"{proposition['nucleus_end']}]"
        )

        lines.append(
            "  RETRIEVAL_HANDLE: "
            +
            proposition[
                "nucleus_quote"
            ]
        )

        lines.append(
            "  AUTHORITATIVE_SEMANTIC_PAYLOAD: "
            +
            proposition[
                "source_quote"
            ]
        )

        for qualifier in proposition.get(
            "qualifiers",
            [],
        ):

            lines.append(
                "  STRUCTURAL_METADATA: "
                f"{qualifier['type']}="
                f"{qualifier['source_quote']} "
                f"span="
                f"{qualifier['source_start']}:"
                f"{qualifier['source_end']}"
            )

    return "\n".join(
        lines
    )


def semantic_grade(
    text: str,
    grader,
):
    """
    Deterministic semantic-family grader.

    all_regex:
        every outer group must match at least one regex.

    forbidden_regex:
        none may match.

    A benchmark-defined semantic violation is any failure of this
    contract. This intentionally measures preservation of the
    decision-relevant operator, not just general usefulness.
    """

    required_groups = (
        grader.get(
            "all_regex",
            [],
        )
    )

    required_ok = all(
        any(
            re.search(
                pattern,
                text,
                re.IGNORECASE
                |
                re.DOTALL,
            )

            for pattern
            in alternatives
        )

        for alternatives
        in required_groups
    )

    forbidden_patterns = (
        grader.get(
            "forbidden_regex",
            [],
        )
    )

    forbidden_hits = [
        pattern

        for pattern
        in forbidden_patterns

        if re.search(
            pattern,
            text,
            re.IGNORECASE
            |
            re.DOTALL,
        )
    ]

    passed = (
        required_ok
        and
        not forbidden_hits
    )

    return {
        "passed": (
            passed
        ),
        "violation": (
            not passed
        ),
        "required_ok": (
            required_ok
        ),
        "forbidden_hits": (
            forbidden_hits
        ),
    }


def semantic_clause_supported(
    *,
    propositions,
    semantic_clause: str,
) -> bool:
    """
    Did the repaired structure retain exact historical support for the
    benchmark semantic clause?

    This distinguishes projection failure from repair-stage loss.
    """

    target = (
        normalize_span_text(
            semantic_clause
        )
        .lower()
    )

    for proposition in propositions:

        support = (
            normalize_span_text(
                proposition[
                    "source_quote"
                ]
            )
            .lower()
        )

        if target in support:
            return True

    return False


def semantic_clause_visible(
    lesson_text: str,
    semantic_clause: str,
) -> bool:

    return (
        normalize_span_text(
            semantic_clause
        )
        .lower()
        in
        normalize_span_text(
            lesson_text
        )
        .lower()
    )


def count_semantic_violations(
    families,
):
    counter = Counter()

    for family in families:

        if not family.get(
            "semantic_violation",
            False,
        ):
            continue

        dimension = (
            family[
                "semantic_dimension"
            ]
        )

        counter[
            dimension
        ] += 1

    return {
        dimension: int(
            counter.get(
                dimension,
                0,
            )
        )

        for dimension
        in SEMANTIC_DIMENSIONS
    }


def _claim_audit(
    evidence_atoms,
):
    proposal = {
        "claims": [
            {
                "text": (
                    atom[
                        "text"
                    ]
                ),
                "evidence_ids": [
                    atom[
                        "id"
                    ]
                ],
            }

            for atom
            in evidence_atoms
        ]
    }

    return admit_claims(
        proposal,
        evidence_atoms,
    )


def _source_evidence_text(
    candidate_decision: str,
    outcome_text: str,
) -> str:

    return (
        "DECISION: "
        +
        candidate_decision
        +
        "\nOUTCOME: "
        +
        outcome_text
    )


def _controlled_candidate_reasoner(
    candidate_decision: str,
):
    def reasoner(
        task: str,
        context: str,
    ) -> str:

        return (
            candidate_decision
        )

    return reasoner


def _run_memory_condition(
    *,
    condition_name: str,
    family,
    family_dir: Path,
    model,
    embedder,
    meter,
    lesson_text: str,
    evidence_atoms,
):
    db_path = (
        family_dir
        /
        f"{condition_name}.sqlite3"
    )

    if db_path.exists():
        db_path.unlink()

    mnexa = MnexaSeed(
        db_path,
        embedder=embedder,
        meter=meter,
    )

    try:

        first_decision = (
            mnexa.decide(
                family[
                    "experience"
                ][
                    "prompt"
                ],
                tuple(
                    family[
                        "entities"
                    ]
                ),
                _controlled_candidate_reasoner(
                    family[
                        "candidate_decision"
                    ]
                ),
            )
        )

        if (
            first_decision.text
            !=
            family[
                "candidate_decision"
            ]
        ):
            raise RuntimeError(
                "Controlled failed "
                "decision changed."
            )

        outcome_text = (
            "EVALUATION RECORD:\n"
            +
            family[
                "raw_source"
            ]
        )

        outcome = (
            mnexa.observe_outcome(
                first_decision.record_id,
                outcome_text,
                success=False,
            )
        )

        source_evidence = (
            _source_evidence_text(
                first_decision.text,
                outcome_text,
            )
        )

        def consolidator(
            evidence: str,
        ) -> str:
            return (
                lesson_text
            )

        lesson = (
            mnexa.consolidate(
                first_decision.record_id,
                consolidator,
            )
        )

        transfer = (
            mnexa.decide(
                family[
                    "transfer"
                ][
                    "prompt"
                ],
                tuple(
                    family[
                        "entities"
                    ]
                ),
                make_fidelity_reasoner(
                    model
                ),
            )
        )

        claim_audit = (
            _claim_audit(
                evidence_atoms
            )
        )

        semantic_result = (
            semantic_grade(
                transfer.text,
                family[
                    "semantic_grader"
                ],
            )
        )

        lesson_complete = (
            grade_text(
                lesson.text,
                family[
                    "knowledge_grader"
                ],
            )
        )

        memory_text = "\n".join(
            transfer.memory_segments
        )

        return {
            "candidate_decision": (
                first_decision.text
            ),
            "outcome": (
                outcome_text
            ),
            "outcome_id": (
                outcome.object_id
            ),
            "source_evidence_sha256": (
                _sha256_text(
                    source_evidence
                )
            ),

            "lesson": (
                lesson.text
            ),
            "lesson_id": (
                lesson.object_id
            ),
            "lesson_knowledge_complete": (
                lesson_complete
            ),

            "semantic_clause_visible": (
                semantic_clause_visible(
                    lesson.text,
                    family[
                        "semantic_clause"
                    ],
                )
            ),

            "transfer_decision": (
                transfer.text
            ),

            "semantic_task_pass": (
                semantic_result[
                    "passed"
                ]
            ),

            "semantic_violation": (
                semantic_result[
                    "violation"
                ]
            ),

            "semantic_required_ok": (
                semantic_result[
                    "required_ok"
                ]
            ),

            "semantic_forbidden_hits": (
                semantic_result[
                    "forbidden_hits"
                ]
            ),

            "memory_segments": list(
                transfer.memory_segments
            ),

            "memory_word_count": (
                meter.count(
                    memory_text
                )
            ),

            "claims_admitted": (
                len(
                    claim_audit[
                        "admitted"
                    ]
                )
            ),

            "unsupported_claims_admitted": (
                claim_audit[
                    "unsupported_claims_admitted"
                ]
            ),
        }

    finally:
        mnexa.close()


def _build_repaired_structure(
    *,
    family,
    model,
):
    """
    Initial structured extraction + one grounded repair pass.

    IMPORTANT:
    This executes once per family.

    Both projection conditions consume the exact same resulting
    repaired proposition set.
    """

    source_text = (
        family[
            "raw_source"
        ]
    )

    initial_raw_response = (
        model
        .generate(
            build_structured_proposition_prompt(
                source_text
            )
        )
        .text
        .strip()
    )

    try:

        initial_model_proposal = (
            parse_structured_proposal(
                initial_raw_response
            )
        )

        initial_parse_error = None

    except Exception as exc:

        initial_model_proposal = {
            "propositions": []
        }

        initial_parse_error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    (
        shared_initial_proposal,
        challenge_injections,
    ) = (
        ensure_structured_compound_challenges(
            proposal=(
                initial_model_proposal
            ),
            family=family,
            source_text=(
                source_text
            ),
        )
    )

    initial_gate = (
        admit_structured_propositions(
            proposal=(
                shared_initial_proposal
            ),
            source_text=(
                source_text
            ),
        )
    )

    repair_prompt = (
        build_structure_repair_prompt(
            source_text=(
                source_text
            ),
            initial_gate=(
                initial_gate
            ),
        )
    )

    repair_raw_response = (
        model
        .generate(
            repair_prompt
        )
        .text
        .strip()
    )

    try:

        repair_payload = (
            parse_repair_proposal(
                repair_raw_response
            )
        )

        repair_parse_error = None

    except Exception as exc:

        repair_payload = {
            "operations": [],
            "propositions": [],
        }

        repair_parse_error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    repaired_gate = (
        admit_structured_propositions(
            proposal={
                "propositions": (
                    repair_payload.get(
                        "propositions",
                        [],
                    )
                )
            },
            source_text=(
                source_text
            ),
        )
    )

    repaired_propositions = (
        repaired_gate[
            "admitted"
        ]
    )

    ancestry_valid = all(
        structured_source_ancestry_valid(
            proposition=(
                proposition
            ),
            source_text=(
                source_text
            ),
        )

        for proposition
        in repaired_propositions
    )

    return {
        "initial_raw_response": (
            initial_raw_response
        ),
        "initial_parse_error": (
            initial_parse_error
        ),
        "initial_model_proposal": (
            initial_model_proposal
        ),
        "shared_initial_proposal": (
            shared_initial_proposal
        ),
        "challenge_injections": (
            challenge_injections
        ),
        "initial_gate": (
            initial_gate
        ),

        "repair_raw_response": (
            repair_raw_response
        ),
        "repair_parse_error": (
            repair_parse_error
        ),
        "repair_payload": (
            repair_payload
        ),
        "repaired_gate": (
            repaired_gate
        ),
        "repaired_propositions": (
            repaired_propositions
        ),

        "repaired_propositions_sha256": (
            _sha256_json(
                repaired_propositions
            )
        ),

        "source_ancestry_valid": (
            ancestry_valid
        ),

        "semantic_clause_supported": (
            semantic_clause_supported(
                propositions=(
                    repaired_propositions
                ),
                semantic_clause=family[
                    "semantic_clause"
                ],
            )
        ),
    }


def run_family_013(
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

    repaired = (
        _build_repaired_structure(
            family=family,
            model=model,
        )
    )

    propositions = (
        repaired[
            "repaired_propositions"
        ]
    )

    repaired_hash = (
        repaired[
            "repaired_propositions_sha256"
        ]
    )

    # ================================================================
    # CONDITION A — CURRENT STRUCTURED PROJECTION
    #
    # nucleus == claim payload
    # ================================================================

    current_lesson = (
        render_structured_propositions(
            propositions
        )
    )

    current_atoms = (
        current_nucleus_projection(
            propositions
        )
    )

    current = (
        _run_memory_condition(
            condition_name=(
                "current_projection"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                current_lesson
            ),
            evidence_atoms=(
                current_atoms
            ),
        )
    )

    # ================================================================
    # CONDITION B — SEMANTIC-CLOSED PROJECTION
    #
    # nucleus == retrieval handle
    # exact support span == semantic claim payload
    #
    # NO new extraction.
    # NO second repair.
    # Same repaired proposition object.
    # ================================================================

    closed_lesson = (
        render_semantic_closed_propositions(
            propositions
        )
    )

    closed_atoms = (
        semantic_closed_projection(
            propositions
        )
    )

    closed = (
        _run_memory_condition(
            condition_name=(
                "semantic_closed_projection"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                closed_lesson
            ),
            evidence_atoms=(
                closed_atoms
            ),
        )
    )

    same_source = (
        current[
            "source_evidence_sha256"
        ]
        ==
        closed[
            "source_evidence_sha256"
        ]
    )

    if not same_source:
        raise RuntimeError(
            "013 invalid: source evidence "
            "differs between projection "
            "conditions."
        )

    # Both conditions literally consume the same in-memory proposition
    # list. Hash recorded anyway as an auditable invariant.
    current_prop_hash = (
        _sha256_json(
            propositions
        )
    )

    closed_prop_hash = (
        _sha256_json(
            propositions
        )
    )

    same_repaired = (
        current_prop_hash
        ==
        closed_prop_hash
        ==
        repaired_hash
    )

    if not same_repaired:
        raise RuntimeError(
            "013 invalid: repaired proposition "
            "set differs between conditions."
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

        "repair": {
            "initial_raw_model_response": (
                repaired[
                    "initial_raw_response"
                ]
            ),
            "initial_parse_error": (
                repaired[
                    "initial_parse_error"
                ]
            ),
            "challenge_injections": (
                repaired[
                    "challenge_injections"
                ]
            ),
            "repair_raw_model_response": (
                repaired[
                    "repair_raw_response"
                ]
            ),
            "repair_parse_error": (
                repaired[
                    "repair_parse_error"
                ]
            ),
            "repair_operations": (
                repaired[
                    "repair_payload"
                ].get(
                    "operations",
                    [],
                )
            ),
            "repair_gate_rejections": (
                repaired[
                    "repaired_gate"
                ][
                    "rejected"
                ]
            ),
            "repaired_propositions": (
                propositions
            ),
            "repaired_propositions_sha256": (
                repaired_hash
            ),
            "source_ancestry_valid": (
                repaired[
                    "source_ancestry_valid"
                ]
            ),
            "semantic_clause_supported": (
                repaired[
                    "semantic_clause_supported"
                ]
            ),
        },

        "current": {
            **current,
            "projection": (
                "nucleus_as_claim_payload"
            ),
            "projected_atoms": (
                current_atoms
            ),
        },

        "semantic_closed": {
            **closed,
            "projection": (
                "support_span_as_semantic_payload_"
                "nucleus_as_retrieval_handle"
            ),
            "projected_atoms": (
                closed_atoms
            ),
        },

        "same_source_evidence": (
            same_source
        ),

        "same_repaired_structured_propositions": (
            same_repaired
        ),

        "semantic_task_delta": (
            int(
                closed[
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

        "memory_word_delta": (
            closed[
                "memory_word_count"
            ]
            -
            current[
                "memory_word_count"
            ]
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


def _mean_metric(
    results,
    condition,
    metric,
):
    values = [
        float(
            family[
                condition
            ].get(
                metric,
                0.0,
            )
        )

        for family
        in results
    ]

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


def _condition_violation_counts(
    results,
    condition,
):
    rows = [
        {
            "semantic_dimension": (
                family[
                    "semantic_dimension"
                ]
            ),
            "semantic_violation": (
                family[
                    condition
                ][
                    "semantic_violation"
                ]
            ),
        }

        for family
        in results
    ]

    return (
        count_semantic_violations(
            rows
        )
    )


def _supported_subset(
    results,
):
    return [
        family

        for family
        in results

        if family[
            "repair"
        ][
            "semantic_clause_supported"
        ]
    ]


def _passes_in_subset(
    results,
    condition,
):
    return sum(
        int(
            family[
                condition
            ][
                "semantic_task_pass"
            ]
        )

        for family
        in results
    )


def run_experiment_013(
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
        run_family_013(
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

    supported = (
        _supported_subset(
            results
        )
    )

    current_violations = (
        _condition_violation_counts(
            results,
            "current",
        )
    )

    closed_violations = (
        _condition_violation_counts(
            results,
            "semantic_closed",
        )
    )

    report = {
        "experiment": (
            "seed-growth-013"
        ),

        "classification": (
            "exploratory-fresh-semantic-"
            "closure-projection-ablation"
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
                "same_repaired_structure_"
                "nucleus_as_claim_payload"
            ),
            "B": (
                "same_repaired_structure_"
                "support_as_semantic_payload_"
                "nucleus_as_retrieval_handle"
            ),
        },

        # ------------------------------------------------------------
        # Primary semantic outcomes
        # ------------------------------------------------------------

        "current_semantic_task_passes": (
            _count(
                results,
                "current",
                "semantic_task_pass",
            )
        ),

        "semantic_closed_task_passes": (
            _count(
                results,
                "semantic_closed",
                "semantic_task_pass",
            )
        ),

        "current_semantic_violations": (
            _count(
                results,
                "current",
                "semantic_violation",
            )
        ),

        "semantic_closed_violations": (
            _count(
                results,
                "semantic_closed",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # Violation dimensions
        # ------------------------------------------------------------

        "current_polarity_violations": (
            current_violations[
                "polarity"
            ]
        ),

        "semantic_closed_polarity_violations": (
            closed_violations[
                "polarity"
            ]
        ),

        "current_scope_loss_violations": (
            current_violations[
                "scope"
            ]
        ),

        "semantic_closed_scope_loss_violations": (
            closed_violations[
                "scope"
            ]
        ),

        "current_cardinality_loss_violations": (
            current_violations[
                "cardinality"
            ]
        ),

        "semantic_closed_cardinality_loss_violations": (
            closed_violations[
                "cardinality"
            ]
        ),

        "current_condition_loss_violations": (
            current_violations[
                "condition"
            ]
        ),

        "semantic_closed_condition_loss_violations": (
            closed_violations[
                "condition"
            ]
        ),

        # ------------------------------------------------------------
        # Was the semantic evidence still present after repair?
        #
        # This isolates projection failures from prior-stage repair loss.
        # ------------------------------------------------------------

        "repaired_semantic_clause_supported_families": (
            len(
                supported
            )
        ),

        "current_semantic_passes_on_supported_families": (
            _passes_in_subset(
                supported,
                "current",
            )
        ),

        "semantic_closed_passes_on_supported_families": (
            _passes_in_subset(
                supported,
                "semantic_closed",
            )
        ),

        # ------------------------------------------------------------
        # Model-visible semantic payload preservation
        # ------------------------------------------------------------

        "current_exact_semantic_clause_visible_families": (
            _count(
                results,
                "current",
                "semantic_clause_visible",
            )
        ),

        "semantic_closed_exact_semantic_clause_visible_families": (
            _count(
                results,
                "semantic_closed",
                "semantic_clause_visible",
            )
        ),

        # ------------------------------------------------------------
        # Knowledge / safety
        # ------------------------------------------------------------

        "current_complete_lessons": (
            _count(
                results,
                "current",
                "lesson_knowledge_complete",
            )
        ),

        "semantic_closed_complete_lessons": (
            _count(
                results,
                "semantic_closed",
                "lesson_knowledge_complete",
            )
        ),

        "repaired_source_ancestry_valid_families": sum(
            int(
                family[
                    "repair"
                ][
                    "source_ancestry_valid"
                ]
            )

            for family
            in results
        ),

        "current_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "current",
                "unsupported_claims_admitted",
            )
        ),

        "semantic_closed_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "semantic_closed",
                "unsupported_claims_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Context / cognitive cost
        # ------------------------------------------------------------

        "mean_current_memory_words": (
            _mean_metric(
                results,
                "current",
                "memory_word_count",
            )
        ),

        "mean_semantic_closed_memory_words": (
            _mean_metric(
                results,
                "semantic_closed",
                "memory_word_count",
            )
        ),

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

        "current_projection_model_calls": 0,

        "semantic_closed_projection_model_calls": 0,

        "current_transfer_model_calls": (
            len(
                results
            )
        ),

        "semantic_closed_transfer_model_calls": (
            len(
                results
            )
        ),

        # ------------------------------------------------------------
        # Strict controls
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

        "all_repaired_structured_propositions_equal": (
            all(
                family[
                    "same_repaired_structured_propositions"
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
            "tasks_013.json"
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
        run_experiment_013(
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

        "current_semantic_task_passes",
        "semantic_closed_task_passes",

        "current_semantic_violations",
        "semantic_closed_violations",

        "current_polarity_violations",
        "semantic_closed_polarity_violations",

        "current_scope_loss_violations",
        "semantic_closed_scope_loss_violations",

        "current_cardinality_loss_violations",
        "semantic_closed_cardinality_loss_violations",

        "current_condition_loss_violations",
        "semantic_closed_condition_loss_violations",

        "repaired_semantic_clause_supported_families",

        "current_semantic_passes_on_supported_families",
        "semantic_closed_passes_on_supported_families",

        "current_exact_semantic_clause_visible_families",
        "semantic_closed_exact_semantic_clause_visible_families",

        "current_complete_lessons",
        "semantic_closed_complete_lessons",

        "repaired_source_ancestry_valid_families",

        "current_unsupported_claims_admitted",
        "semantic_closed_unsupported_claims_admitted",

        "mean_current_memory_words",
        "mean_semantic_closed_memory_words",

        "all_source_evidence_equal",
        "all_repaired_structured_propositions_equal",
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
