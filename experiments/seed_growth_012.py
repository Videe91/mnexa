from __future__ import annotations

import argparse
import hashlib
import json
import os

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
    canonical_nucleus_metrics,
    compound_span_covers_multiple_units,
    ensure_structured_compound_challenges,
    parse_structured_proposal,
    qualifier_metrics,
    render_structured_propositions,
    structured_source_ancestry_valid,
)

from mnexa_seed import (
    MnexaSeed,
)


ALLOWED_REPAIR_OPERATIONS = {
    "KEEP",
    "SPLIT",
    "REMOVE_QUALIFIER",
    "REATTACH_QUALIFIER",
}


STRUCTURE_REPAIR_INSTRUCTION = """
GROUNDED STRUCTURE REPAIR

You are reviewing a first-pass structured memory proposal before it is
allowed to become durable memory.

You receive:

1. the original historical source;
2. runtime-admitted first-pass propositions;
3. runtime-rejected first-pass candidates and rejection reasons.

Your job is NOT to invent new knowledge.

Your job is to repair the STRUCTURE of knowledge already physically
present in the authoritative source.

PRIMARY AUDIT 1 — COMPOUND NUCLEI

Ask whether each nucleus contains more than one independently reusable
operational proposition.

Examples:

BAD:
"refresh the lease and wait 8 seconds"

BETTER:
"refresh the lease"
"wait 8 seconds"

BAD:
"retry exactly once, but never reuse the prior nonce"

BETTER:
"retry exactly once"
"never reuse the prior nonce"

Do not blindly split every conjunction.

For example, a phrase such as:

"read and write permission"

may represent one semantic unit.

Split only where the source contains independently reusable
operational propositions.

PRIMARY AUDIT 2 — QUALIFIER ATTACHMENT

A qualifier must be attached only to the proposition it actually
governs.

Do not copy a condition, ordering marker, scope marker, or negation
onto unrelated propositions merely because it appears nearby.

Examples:

Source:
"When ZX-12 occurs, refresh the lease. Wait 8 seconds."

Correct:
- "refresh the lease"
  condition = "When ZX-12 occurs"
- "Wait 8 seconds"
  no condition

Source:
"refresh the lease; then wait 8 seconds"

Correct:
- "refresh the lease"
- "wait 8 seconds"
  ordering = "then"

IMPORTANT NEGATION/SCOPE RULE

If a word such as "only", "never", or "exactly" is part of the
operational meaning of the proposition itself, keep it inside the
nucleus.

Do not redundantly attach that same word as a qualifier when doing so
would overlap the nucleus.

SOURCE-GROUNDING RULES

Every repaired proposition must still satisfy:

- source_quote is an exact contiguous substring of the original source;
- source_quote is inside authoritative_correction;
- nucleus_quote is an exact contiguous substring inside source_quote;
- every qualifier source_quote is an exact contiguous substring inside
  source_quote;
- do not paraphrase;
- no invented text;
- no external knowledge.

You MAY use these audit operations:

KEEP
SPLIT
REMOVE_QUALIFIER
REATTACH_QUALIFIER

The operations are audit metadata only.

The final "propositions" array is authoritative for the repair result.

Return JSON only:

{
  "operations": [
    {
      "op": "KEEP|SPLIT|REMOVE_QUALIFIER|REATTACH_QUALIFIER",
      "target": "<first-pass proposition id or short source reference>"
    }
  ],
  "propositions": [
    {
      "source_quote": "<exact source substring>",
      "nucleus_quote": "<exact source substring inside source_quote>",
      "qualifiers": [
        {
          "type": "condition|ordering|scope|negation",
          "source_quote": "<exact substring inside source_quote>"
        }
      ]
    }
  ]
}
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


def _strip_json_fence(
    text: str,
) -> str:

    text = text.strip()

    if not text.startswith(
        "```"
    ):
        return text

    lines = (
        text.splitlines()
    )

    if lines:
        lines = lines[
            1:
        ]

    if (
        lines
        and
        lines[-1]
        .strip()
        .startswith(
            "```"
        )
    ):
        lines = lines[
            :-1
        ]

    return (
        "\n"
        .join(
            lines
        )
        .strip()
    )


def parse_repair_proposal(
    text: str,
):
    payload = json.loads(
        _strip_json_fence(
            text
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Repair proposal must "
            "be a JSON object."
        )

    operations = (
        payload.get(
            "operations",
            [],
        )
    )

    propositions = (
        payload.get(
            "propositions"
        )
    )

    if not isinstance(
        operations,
        list,
    ):
        raise ValueError(
            "operations must be a list."
        )

    if not isinstance(
        propositions,
        list,
    ):
        raise ValueError(
            "propositions must be a list."
        )

    for operation in operations:

        if not isinstance(
            operation,
            dict,
        ):
            raise ValueError(
                "Repair operation must "
                "be an object."
            )

        op = (
            operation.get(
                "op"
            )
        )

        if (
            op
            not in
            ALLOWED_REPAIR_OPERATIONS
        ):
            raise ValueError(
                "Unsupported repair "
                f"operation: {op!r}"
            )

    return payload


def _concise_initial_gate(
    initial_gate,
):
    admitted = []

    for proposition in initial_gate.get(
        "admitted",
        [],
    ):

        admitted.append(
            {
                "id": (
                    proposition.get(
                        "id"
                    )
                ),
                "source_quote": (
                    proposition.get(
                        "source_quote"
                    )
                ),
                "nucleus_quote": (
                    proposition.get(
                        "nucleus_quote"
                    )
                ),
                "qualifiers": [
                    {
                        "type": (
                            qualifier.get(
                                "type"
                            )
                        ),
                        "source_quote": (
                            qualifier.get(
                                "source_quote"
                            )
                        ),
                    }

                    for qualifier
                    in proposition.get(
                        "qualifiers",
                        [],
                    )
                ],
                "source_start": (
                    proposition.get(
                        "source_start"
                    )
                ),
                "source_end": (
                    proposition.get(
                        "source_end"
                    )
                ),
                "nucleus_start": (
                    proposition.get(
                        "nucleus_start"
                    )
                ),
                "nucleus_end": (
                    proposition.get(
                        "nucleus_end"
                    )
                ),
            }
        )

    rejected = []

    for rejection in initial_gate.get(
        "rejected",
        [],
    ):

        candidate = (
            rejection.get(
                "candidate"
            )
        )

        rejected.append(
            {
                "reason": (
                    rejection.get(
                        "reason"
                    )
                ),
                "candidate": (
                    candidate
                ),
            }
        )

    return {
        "admitted": (
            admitted
        ),
        "rejected": (
            rejected
        ),
    }


def build_structure_repair_prompt(
    *,
    source_text: str,
    initial_gate,
) -> str:

    state = (
        _concise_initial_gate(
            initial_gate
        )
    )

    return (
        STRUCTURE_REPAIR_INSTRUCTION
        + "\n\n"
        + "ORIGINAL SOURCE:\n"
        + source_text
        + "\n\n"
        + "FIRST-PASS RUNTIME STATE:\n"
        + json.dumps(
            state,
            indent=2,
            sort_keys=True,
        )
    )


def count_repair_operations(
    repair_payload,
):
    counts = Counter(
        operation.get(
            "op"
        )

        for operation
        in repair_payload.get(
            "operations",
            []
        )

        if isinstance(
            operation,
            dict,
        )
    )

    return {
        operation: int(
            counts.get(
                operation,
                0,
            )
        )

        for operation
        in sorted(
            ALLOWED_REPAIR_OPERATIONS
        )
    }


def micro_qualifier_metrics(
    *,
    expected: int,
    admitted: int,
    matched: int,
):
    if expected:
        recall = (
            matched
            /
            expected
        )
    else:
        recall = 1.0

    if admitted:
        precision = (
            matched
            /
            admitted
        )
    else:
        precision = (
            1.0
            if expected == 0
            else 0.0
        )

    return {
        "recall": (
            recall
        ),
        "precision": (
            precision
        ),
        "expected": (
            expected
        ),
        "admitted": (
            admitted
        ),
        "matched": (
            matched
        ),
    }


def count_compound_challenge_survivors(
    *,
    propositions,
    family,
):
    challenge_texts = {
        normalize_span_text(
            challenge[
                "text"
            ]
        )

        for challenge
        in family[
            "structured_compound_challenges"
        ]
    }

    admitted = {
        normalize_span_text(
            proposition[
                "nucleus_quote"
            ]
        )

        for proposition
        in propositions
    }

    return len(
        challenge_texts
        &
        admitted
    )


def count_compound_nuclei(
    *,
    propositions,
    family,
):
    return sum(
        1

        for proposition
        in propositions

        if compound_span_covers_multiple_units(
            span_text=(
                proposition[
                    "nucleus_quote"
                ]
            ),
            source_text=family[
                "raw_source"
            ],
            expected_units=family[
                "atomic_units"
            ],
        )
    )


def _nucleus_atom_projection(
    propositions,
):
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
    propositions,
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

        lesson_text = (
            render_structured_propositions(
                propositions
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

        evidence_atoms = (
            _nucleus_atom_projection(
                propositions
            )
        )

        claim_audit = (
            _claim_audit(
                evidence_atoms
            )
        )

        memory_text = "\n".join(
            transfer.memory_segments
        )

        lesson_complete = (
            grade_text(
                lesson.text,
                family[
                    "knowledge_grader"
                ],
            )
        )

        transfer_sufficient = (
            grade_text(
                transfer.text,
                family[
                    "transfer_grader"
                ],
            )
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
            "transfer_decision": (
                transfer.text
            ),
            "transfer_task_sufficient": (
                transfer_sufficient
            ),
            "task_success": (
                transfer_sufficient
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


def _score_structure(
    *,
    propositions,
    family,
):
    nucleus = (
        canonical_nucleus_metrics(
            admitted_propositions=(
                propositions
            ),
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    qualifiers = (
        qualifier_metrics(
            admitted_propositions=(
                propositions
            ),
            expected_units=family[
                "atomic_units"
            ],
            expected_qualifiers=family[
                "expected_qualifiers"
            ],
        )
    )

    ancestry_valid = all(
        structured_source_ancestry_valid(
            proposition=(
                proposition
            ),
            source_text=family[
                "raw_source"
            ],
        )

        for proposition
        in propositions
    )

    invented_nuclei = sum(
        1

        for proposition
        in propositions

        if (
            family[
                "raw_source"
            ].count(
                proposition[
                    "nucleus_quote"
                ]
            )
            != 1
        )
    )

    invented_qualifiers = sum(
        1

        for proposition
        in propositions

        for qualifier
        in proposition.get(
            "qualifiers",
            [],
        )

        if (
            family[
                "raw_source"
            ].count(
                qualifier[
                    "source_quote"
                ]
            )
            != 1
        )
    )

    nonauthoritative = sum(
        1

        for proposition
        in propositions

        if (
            proposition.get(
                "source_role"
            )
            !=
            AUTHORITATIVE_ROLE
        )
    )

    compound = (
        count_compound_nuclei(
            propositions=(
                propositions
            ),
            family=family,
        )
    )

    challenge_survivors = (
        count_compound_challenge_survivors(
            propositions=(
                propositions
            ),
            family=family,
        )
    )

    return {
        "nucleus_recall": (
            nucleus[
                "nucleus_recall"
            ]
        ),
        "nucleus_precision": (
            nucleus[
                "nucleus_precision"
            ]
        ),
        "exact_nucleus_matches": (
            nucleus[
                "exact_nucleus_matches"
            ]
        ),
        "nuclei_complete": (
            nucleus[
                "complete"
            ]
        ),

        "qualifier_recall": (
            qualifiers[
                "qualifier_recall"
            ]
        ),
        "qualifier_precision": (
            qualifiers[
                "qualifier_precision"
            ]
        ),
        "qualifier_expected": (
            qualifiers[
                "expected_qualifiers"
            ]
        ),
        "qualifier_admitted": (
            qualifiers[
                "admitted_qualifiers"
            ]
        ),
        "qualifier_matched": (
            qualifiers[
                "matched_qualifiers"
            ]
        ),
        "qualifiers_complete": (
            qualifiers[
                "complete"
            ]
        ),

        "source_ancestry_valid": (
            ancestry_valid
        ),
        "invented_nuclei_admitted": (
            invented_nuclei
        ),
        "invented_qualifiers_admitted": (
            invented_qualifiers
        ),
        "nonauthoritative_propositions_admitted": (
            nonauthoritative
        ),
        "compound_nuclei_admitted": (
            compound
        ),
        "compound_challenge_survivors": (
            challenge_survivors
        ),
    }


def run_family_012(
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
    # ONE INITIAL STRUCTURED EXTRACTION
    #
    # Both conditions originate from this exact proposal.
    # ================================================================

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

    initial_proposal_sha256 = (
        _sha256_text(
            json.dumps(
                shared_initial_proposal,
                sort_keys=True,
            )
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

    initial_propositions = (
        initial_gate[
            "admitted"
        ]
    )

    # ================================================================
    # CONDITION A
    #
    # Seed 011 one-pass structured memory.
    # ================================================================

    initial_memory = (
        _run_memory_condition(
            condition_name=(
                "initial_structured"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            propositions=(
                initial_propositions
            ),
        )
    )

    initial_structure = (
        _score_structure(
            propositions=(
                initial_propositions
            ),
            family=family,
        )
    )

    # ================================================================
    # CONDITION B
    #
    # Same initial extraction
    # +
    # one structure-audit / repair model call.
    # ================================================================

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
                    repair_payload[
                        "propositions"
                    ]
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

    repaired_memory = (
        _run_memory_condition(
            condition_name=(
                "repaired_structured"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            propositions=(
                repaired_propositions
            ),
        )
    )

    repaired_structure = (
        _score_structure(
            propositions=(
                repaired_propositions
            ),
            family=family,
        )
    )

    source_equal = (
        initial_memory[
            "source_evidence_sha256"
        ]
        ==
        repaired_memory[
            "source_evidence_sha256"
        ]
    )

    if not source_equal:
        raise RuntimeError(
            "012 invalid: source evidence "
            "differs between conditions."
        )

    repair_operation_counts = (
        count_repair_operations(
            repair_payload
        )
    )

    initial_challenges = len(
        family[
            "structured_compound_challenges"
        ]
    )

    repaired_challenge_survivors = (
        repaired_structure[
            "compound_challenge_survivors"
        ]
    )

    return {
        "family_id": (
            family[
                "id"
            ]
        ),
        "style": (
            family[
                "style"
            ]
        ),

        "initial_raw_model_response": (
            initial_raw_response
        ),
        "initial_parse_error": (
            initial_parse_error
        ),
        "initial_model_proposal_count": (
            len(
                initial_model_proposal.get(
                    "propositions",
                    [],
                )
            )
        ),
        "challenge_injections": (
            challenge_injections
        ),
        "initial_structured_proposal_sha256": (
            initial_proposal_sha256
        ),

        "initial": {
            **initial_memory,
            **initial_structure,
            "admitted_propositions": (
                initial_propositions
            ),
            "gate_rejections": (
                initial_gate[
                    "rejected"
                ]
            ),
        },

        "repair": {
            "raw_model_response": (
                repair_raw_response
            ),
            "parse_error": (
                repair_parse_error
            ),
            "operations": (
                repair_payload[
                    "operations"
                ]
            ),
            "operation_counts": (
                repair_operation_counts
            ),
            "proposal_count": (
                len(
                    repair_payload[
                        "propositions"
                    ]
                )
            ),
            "gate_rejections": (
                repaired_gate[
                    "rejected"
                ]
            ),
        },

        "repaired": {
            **repaired_memory,
            **repaired_structure,
            "admitted_propositions": (
                repaired_propositions
            ),
            "compound_challenges_total": (
                initial_challenges
            ),
            "compound_challenges_removed": (
                initial_challenges
                -
                repaired_challenge_survivors
            ),
        },

        "same_source_evidence": (
            source_equal
        ),

        # Both branches originate from the one
        # shared initial structured proposal.
        "same_initial_structured_proposal": (
            True
        ),

        "task_delta_initial_to_repaired": (
            int(
                repaired_memory[
                    "task_success"
                ]
            )
            -
            int(
                initial_memory[
                    "task_success"
                ]
            )
        ),

        "nucleus_recall_delta": (
            repaired_structure[
                "nucleus_recall"
            ]
            -
            initial_structure[
                "nucleus_recall"
            ]
        ),

        "nucleus_precision_delta": (
            repaired_structure[
                "nucleus_precision"
            ]
            -
            initial_structure[
                "nucleus_precision"
            ]
        ),

        "memory_word_delta_initial_to_repaired": (
            repaired_memory[
                "memory_word_count"
            ]
            -
            initial_memory[
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


def _aggregate_micro_qualifiers(
    results,
    condition,
):
    expected = (
        _sum_metric(
            results,
            condition,
            "qualifier_expected",
        )
    )

    admitted = (
        _sum_metric(
            results,
            condition,
            "qualifier_admitted",
        )
    )

    matched = (
        _sum_metric(
            results,
            condition,
            "qualifier_matched",
        )
    )

    return (
        micro_qualifier_metrics(
            expected=(
                expected
            ),
            admitted=(
                admitted
            ),
            matched=(
                matched
            ),
        )
    )


def _sum_repair_operation(
    results,
    operation,
):
    return sum(
        int(
            family[
                "repair"
            ][
                "operation_counts"
            ].get(
                operation,
                0,
            )
        )

        for family
        in results
    )


def run_experiment_012(
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
        run_family_012(
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

    initial_micro = (
        _aggregate_micro_qualifiers(
            results,
            "initial",
        )
    )

    repaired_micro = (
        _aggregate_micro_qualifiers(
            results,
            "repaired",
        )
    )

    total_challenges = sum(
        len(
            family[
                "structured_compound_challenges"
            ]
        )

        for family
        in payload[
            "families"
        ]
    )

    repaired_challenge_survivors = (
        _sum_metric(
            results,
            "repaired",
            "compound_challenge_survivors",
        )
    )

    report = {
        "experiment": (
            "seed-growth-012"
        ),
        "classification": (
            "exploratory-fresh-grounded-"
            "structure-repair-ablation"
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
                "seed011_one_pass_"
                "structured_extraction"
            ),
            "B": (
                "same_initial_structured_proposal_"
                "plus_grounded_structure_repair"
            ),
        },

        # ------------------------------------------------------------
        # Downstream performance
        # ------------------------------------------------------------

        "initial_task_passes": (
            _count(
                results,
                "initial",
                "task_success",
            )
        ),
        "repaired_task_passes": (
            _count(
                results,
                "repaired",
                "task_success",
            )
        ),

        "initial_complete_lessons": (
            _count(
                results,
                "initial",
                "lesson_knowledge_complete",
            )
        ),
        "repaired_complete_lessons": (
            _count(
                results,
                "repaired",
                "lesson_knowledge_complete",
            )
        ),

        # ------------------------------------------------------------
        # Nucleus quality
        # ------------------------------------------------------------

        "mean_initial_nucleus_recall": (
            _mean_metric(
                results,
                "initial",
                "nucleus_recall",
            )
        ),
        "mean_repaired_nucleus_recall": (
            _mean_metric(
                results,
                "repaired",
                "nucleus_recall",
            )
        ),

        "mean_initial_nucleus_precision": (
            _mean_metric(
                results,
                "initial",
                "nucleus_precision",
            )
        ),
        "mean_repaired_nucleus_precision": (
            _mean_metric(
                results,
                "repaired",
                "nucleus_precision",
            )
        ),

        "initial_exact_nucleus_families": (
            _count(
                results,
                "initial",
                "nuclei_complete",
            )
        ),
        "repaired_exact_nucleus_families": (
            _count(
                results,
                "repaired",
                "nuclei_complete",
            )
        ),

        "initial_compound_nuclei_admitted": (
            _sum_metric(
                results,
                "initial",
                "compound_nuclei_admitted",
            )
        ),
        "repaired_compound_nuclei_admitted": (
            _sum_metric(
                results,
                "repaired",
                "compound_nuclei_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Qualifier quality — macro
        # ------------------------------------------------------------

        "mean_initial_qualifier_recall": (
            _mean_metric(
                results,
                "initial",
                "qualifier_recall",
            )
        ),
        "mean_repaired_qualifier_recall": (
            _mean_metric(
                results,
                "repaired",
                "qualifier_recall",
            )
        ),

        "mean_initial_qualifier_precision": (
            _mean_metric(
                results,
                "initial",
                "qualifier_precision",
            )
        ),
        "mean_repaired_qualifier_precision": (
            _mean_metric(
                results,
                "repaired",
                "qualifier_precision",
            )
        ),

        # ------------------------------------------------------------
        # Qualifier quality — MICRO
        # ------------------------------------------------------------

        "initial_qualifier_relations_expected": (
            initial_micro[
                "expected"
            ]
        ),
        "initial_qualifier_relations_admitted": (
            initial_micro[
                "admitted"
            ]
        ),
        "initial_qualifier_relations_matched": (
            initial_micro[
                "matched"
            ]
        ),
        "initial_qualifier_micro_recall": (
            initial_micro[
                "recall"
            ]
        ),
        "initial_qualifier_micro_precision": (
            initial_micro[
                "precision"
            ]
        ),

        "repaired_qualifier_relations_expected": (
            repaired_micro[
                "expected"
            ]
        ),
        "repaired_qualifier_relations_admitted": (
            repaired_micro[
                "admitted"
            ]
        ),
        "repaired_qualifier_relations_matched": (
            repaired_micro[
                "matched"
            ]
        ),
        "repaired_qualifier_micro_recall": (
            repaired_micro[
                "recall"
            ]
        ),
        "repaired_qualifier_micro_precision": (
            repaired_micro[
                "precision"
            ]
        ),

        # ------------------------------------------------------------
        # Pre-registered compound attacks
        # ------------------------------------------------------------

        "structured_compound_challenges": (
            total_challenges
        ),
        "initial_compound_challenge_survivors": (
            _sum_metric(
                results,
                "initial",
                "compound_challenge_survivors",
            )
        ),
        "repaired_compound_challenge_survivors": (
            repaired_challenge_survivors
        ),
        "repaired_compound_challenges_removed": (
            total_challenges
            -
            repaired_challenge_survivors
        ),

        # ------------------------------------------------------------
        # Constitutional safety
        # ------------------------------------------------------------

        "repaired_source_ancestry_valid_families": (
            _count(
                results,
                "repaired",
                "source_ancestry_valid",
            )
        ),

        "repaired_invented_nuclei_admitted": (
            _sum_metric(
                results,
                "repaired",
                "invented_nuclei_admitted",
            )
        ),

        "repaired_invented_qualifiers_admitted": (
            _sum_metric(
                results,
                "repaired",
                "invented_qualifiers_admitted",
            )
        ),

        "repaired_nonauthoritative_propositions_admitted": (
            _sum_metric(
                results,
                "repaired",
                "nonauthoritative_propositions_admitted",
            )
        ),

        "repaired_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "repaired",
                "unsupported_claims_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Repair behavior
        # ------------------------------------------------------------

        "repair_keep_operations": (
            _sum_repair_operation(
                results,
                "KEEP",
            )
        ),
        "repair_split_operations": (
            _sum_repair_operation(
                results,
                "SPLIT",
            )
        ),
        "repair_remove_qualifier_operations": (
            _sum_repair_operation(
                results,
                "REMOVE_QUALIFIER",
            )
        ),
        "repair_reattach_qualifier_operations": (
            _sum_repair_operation(
                results,
                "REATTACH_QUALIFIER",
            )
        ),

        # ------------------------------------------------------------
        # Cognitive / context cost
        # ------------------------------------------------------------

        "mean_initial_memory_words": (
            _mean_metric(
                results,
                "initial",
                "memory_word_count",
            )
        ),
        "mean_repaired_memory_words": (
            _mean_metric(
                results,
                "repaired",
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
            "tasks_012.json"
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
        run_experiment_012(
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

        "initial_task_passes",
        "repaired_task_passes",

        "initial_complete_lessons",
        "repaired_complete_lessons",

        "mean_initial_nucleus_recall",
        "mean_repaired_nucleus_recall",

        "mean_initial_nucleus_precision",
        "mean_repaired_nucleus_precision",

        "initial_exact_nucleus_families",
        "repaired_exact_nucleus_families",

        "initial_compound_nuclei_admitted",
        "repaired_compound_nuclei_admitted",

        "initial_qualifier_micro_recall",
        "repaired_qualifier_micro_recall",

        "initial_qualifier_micro_precision",
        "repaired_qualifier_micro_precision",

        "initial_qualifier_relations_expected",
        "initial_qualifier_relations_admitted",
        "initial_qualifier_relations_matched",

        "repaired_qualifier_relations_expected",
        "repaired_qualifier_relations_admitted",
        "repaired_qualifier_relations_matched",

        "structured_compound_challenges",
        "initial_compound_challenge_survivors",
        "repaired_compound_challenge_survivors",
        "repaired_compound_challenges_removed",

        "repaired_source_ancestry_valid_families",
        "repaired_invented_nuclei_admitted",
        "repaired_invented_qualifiers_admitted",
        "repaired_nonauthoritative_propositions_admitted",
        "repaired_unsupported_claims_admitted",

        "mean_initial_memory_words",
        "mean_repaired_memory_words",

        "all_source_evidence_equal",
        "all_initial_structured_proposals_equal",
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
