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
    parse_atom_proposal,
    parse_role_regions,
    render_role_aware_claims,
    role_for_span,
)

from experiments.seed_growth_009 import (
    locate_atomic_units,
)

from mnexa_seed import (
    MnexaSeed,
)


AUTONOMOUS_BOUNDARY_DISCOVERY_INSTRUCTION = """
AUTONOMOUS ATOMIC BOUNDARY DISCOVERY

You are discovering reusable atomic propositions directly from a
structured historical source.

You are NOT given canonical proposition boundaries.

Only statements inside the authoritative_correction role are eligible.

Your job is to identify the smallest source spans that still express
independently reusable operational propositions.

Rules:

1. Read only the content of authoritative_correction for proposed
   knowledge atoms.

2. Split compound language when separate operational propositions are
   present.

3. In particular, inspect:
   - conjunctions such as "and"
   - contrastive conjunctions such as "but"
   - semicolon-separated clauses
   - numbered inline clauses
   - comma-separated operational clauses
   - conditionals
   - negations
   - subordinate constraints

4. Prefer minimal independently reusable propositions.

5. Preserve every decision-critical detail:
   - numbers
   - units
   - counts
   - identifiers
   - header names
   - exact modes
   - negations
   - retry limits
   - ordering constraints
   - scope restrictions

6. Every source_quote MUST be one exact contiguous substring of the
   supplied source.

7. Set text equal to source_quote exactly.

8. Do not paraphrase.

9. Do not infer missing information.

10. Do not invent words.

11. Do not merge separate propositions merely because they occur in
    one sentence.

12. Do not include role markers.

Return JSON only:

{
  "atoms": [
    {
      "text": "<exact minimal source span>",
      "source_quote": "<same exact minimal source span>"
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


def build_autonomous_boundary_prompt(
    source_text: str,
) -> str:

    return (
        AUTONOMOUS_BOUNDARY_DISCOVERY_INSTRUCTION
        + "\n\n"
        + "SOURCE:\n"
        + source_text
    )


def _assign_ids(
    atoms,
):
    ordered = sorted(
        atoms,
        key=lambda atom: (
            atom[
                "source_start"
            ],
            atom[
                "source_end"
            ],
        ),
    )

    return [
        {
            "id": (
                f"E{index}"
            ),
            **{
                key: value
                for key, value
                in atom.items()
                if key != "id"
            },
        }

        for index, atom
        in enumerate(
            ordered,
            start=1,
        )
    ]


def _spans_overlap(
    left,
    right,
) -> bool:

    return (
        max(
            left[
                "source_start"
            ],
            right[
                "source_start"
            ],
        )
        <
        min(
            left[
                "source_end"
            ],
            right[
                "source_end"
            ],
        )
    )


def count_overlapping_pairs(
    atoms,
) -> int:

    total = 0

    for index, left in enumerate(
        atoms
    ):
        for right in atoms[
            index + 1:
        ]:
            if _spans_overlap(
                left,
                right,
            ):
                total += 1

    return total


def source_ancestry_valid(
    *,
    atom,
    source_text: str,
) -> bool:

    start = atom.get(
        "source_start"
    )

    end = atom.get(
        "source_end"
    )

    if (
        not isinstance(
            start,
            int,
        )
        or
        not isinstance(
            end,
            int,
        )
    ):
        return False

    if (
        start < 0
        or end <= start
        or end > len(
            source_text
        )
    ):
        return False

    span = (
        source_text[
            start:end
        ]
    )

    if (
        span
        !=
        atom.get(
            "source_quote"
        )
    ):
        return False

    if (
        atom.get(
            "text"
        )
        != span
    ):
        return False

    if (
        atom.get(
            "source_sha256"
        )
        !=
        _sha256_text(
            source_text
        )
    ):
        return False

    if (
        atom.get(
            "span_sha256"
        )
        !=
        _sha256_text(
            span
        )
    ):
        return False

    return True


def _ground_candidate(
    *,
    candidate,
    source_text: str,
    regions,
):
    if not isinstance(
        candidate,
        dict,
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "invalid_candidate"
            ),
        }

    text = candidate.get(
        "text"
    )

    quote = candidate.get(
        "source_quote"
    )

    if (
        not isinstance(
            text,
            str,
        )
        or
        not isinstance(
            quote,
            str,
        )
        or
        not text
        or
        not quote
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "invalid_candidate"
            ),
        }

    if text != quote:
        return None, {
            "candidate": candidate,
            "reason": (
                "text_quote_mismatch"
            ),
        }

    occurrence_count = (
        source_text.count(
            quote
        )
    )

    if occurrence_count != 1:
        return None, {
            "candidate": candidate,
            "reason": (
                "source_quote_not_unique"
            ),
            "occurrence_count": (
                occurrence_count
            ),
        }

    start = (
        source_text.index(
            quote
        )
    )

    end = (
        start
        + len(
            quote
        )
    )

    role = (
        role_for_span(
            start,
            end,
            regions,
        )
    )

    if (
        role
        !=
        AUTHORITATIVE_ROLE
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "ineligible_source_role"
            ),
            "source_role": (
                role
            ),
            "source_start": (
                start
            ),
            "source_end": (
                end
            ),
        }

    return {
        "text": (
            text
        ),
        "source_quote": (
            quote
        ),
        "source_start": (
            start
        ),
        "source_end": (
            end
        ),
        "source_role": (
            role
        ),
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
        "span_sha256": (
            _sha256_text(
                quote
            )
        ),
    }, None


def admit_autonomous_atoms(
    *,
    proposal,
    source_text: str,
):
    """
    Autonomous boundary admission.

    IMPORTANT:
    This function receives no benchmark family and no canonical atomic
    boundaries.

    It validates only properties knowable from the raw source:

    - exact source ancestry
    - authoritative role
    - uniqueness
    - no duplicate spans
    - no overlapping final atoms

    When model proposals overlap, shorter grounded spans are considered
    first. This is a generic minimality heuristic, not oracle boundary
    knowledge.
    """

    regions = (
        parse_role_regions(
            source_text
        )
    )

    rejected = []
    grounded = []

    candidates = proposal.get(
        "atoms",
        []
    )

    if not isinstance(
        candidates,
        list,
    ):
        candidates = []

    for candidate in candidates:

        atom, rejection = (
            _ground_candidate(
                candidate=candidate,
                source_text=(
                    source_text
                ),
                regions=regions,
            )
        )

        if rejection is not None:
            rejected.append(
                rejection
            )
            continue

        grounded.append(
            atom
        )

    # Generic minimum-span preference.
    #
    # No canonical unit information is available here.
    grounded.sort(
        key=lambda atom: (
            (
                atom[
                    "source_end"
                ]
                -
                atom[
                    "source_start"
                ]
            ),
            atom[
                "source_start"
            ],
            atom[
                "source_end"
            ],
            atom[
                "text"
            ],
        )
    )

    admitted = []

    seen_spans = set()

    for atom in grounded:

        span_key = (
            atom[
                "source_start"
            ],
            atom[
                "source_end"
            ],
        )

        if span_key in seen_spans:
            rejected.append(
                {
                    "candidate": {
                        "text": (
                            atom[
                                "text"
                            ]
                        ),
                        "source_quote": (
                            atom[
                                "source_quote"
                            ]
                        ),
                    },
                    "reason": (
                        "duplicate_span"
                    ),
                    "source_start": (
                        atom[
                            "source_start"
                        ]
                    ),
                    "source_end": (
                        atom[
                            "source_end"
                        ]
                    ),
                }
            )

            continue

        overlapping = [
            existing

            for existing
            in admitted

            if _spans_overlap(
                atom,
                existing,
            )
        ]

        if overlapping:

            rejected.append(
                {
                    "candidate": {
                        "text": (
                            atom[
                                "text"
                            ]
                        ),
                        "source_quote": (
                            atom[
                                "source_quote"
                            ]
                        ),
                    },
                    "reason": (
                        "overlaps_admitted_span"
                    ),
                    "source_start": (
                        atom[
                            "source_start"
                        ]
                    ),
                    "source_end": (
                        atom[
                            "source_end"
                        ]
                    ),
                    "overlaps": [
                        {
                            "source_start": (
                                existing[
                                    "source_start"
                                ]
                            ),
                            "source_end": (
                                existing[
                                    "source_end"
                                ]
                            ),
                            "text": (
                                existing[
                                    "text"
                                ]
                            ),
                        }
                        for existing
                        in overlapping
                    ],
                }
            )

            continue

        admitted.append(
            atom
        )

        seen_spans.add(
            span_key
        )

    admitted = (
        _assign_ids(
            admitted
        )
    )

    return {
        "admitted": (
            admitted
        ),
        "rejected": (
            rejected
        ),
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
    }


def oracle_atoms_from_family(
    *,
    source_text: str,
    family,
):
    """
    Oracle upper bound.

    This condition intentionally receives benchmark canonical
    boundaries.

    Seed 010 compares autonomous discovery against this ceiling.
    """

    units = (
        locate_atomic_units(
            source_text=(
                source_text
            ),
            family=family,
        )
    )

    atoms = []

    for unit in units:

        quote = (
            source_text[
                unit[
                    "source_start"
                ]:
                unit[
                    "source_end"
                ]
            ]
        )

        atoms.append(
            {
                "text": (
                    quote
                ),
                "source_quote": (
                    quote
                ),
                "source_start": (
                    unit[
                        "source_start"
                    ]
                ),
                "source_end": (
                    unit[
                        "source_end"
                    ]
                ),
                "source_role": (
                    unit[
                        "source_role"
                    ]
                ),
                "source_sha256": (
                    _sha256_text(
                        source_text
                    )
                ),
                "span_sha256": (
                    _sha256_text(
                        quote
                    )
                ),
            }
        )

    return (
        _assign_ids(
            atoms
        )
    )


def canonical_boundary_metrics(
    *,
    admitted_atoms,
    expected_units,
):
    expected = {
        normalize_span_text(
            unit[
                "text"
            ]
        )
        for unit
        in expected_units
    }

    admitted = {
        normalize_span_text(
            atom[
                "text"
            ]
        )
        for atom
        in admitted_atoms
    }

    exact = (
        expected
        & admitted
    )

    recall = (
        len(
            exact
        )
        /
        len(
            expected
        )
        if expected
        else 1.0
    )

    precision = (
        len(
            exact
        )
        /
        len(
            admitted
        )
        if admitted
        else (
            1.0
            if not expected
            else 0.0
        )
    )

    return {
        "canonical_recall": (
            recall
        ),
        "canonical_precision": (
            precision
        ),
        "exact_matches": (
            len(
                exact
            )
        ),
        "expected_units": (
            len(
                expected
            )
        ),
        "admitted_units": (
            len(
                admitted
            )
        ),
        "complete": (
            exact
            ==
            expected
        ),
    }


def _proposal_contains_exact(
    proposal,
    text: str,
) -> bool:

    for candidate in proposal.get(
        "atoms",
        []
    ):

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        if (
            candidate.get(
                "text"
            )
            ==
            text
            and
            candidate.get(
                "source_quote"
            )
            ==
            text
        ):
            return True

    return False


def ensure_overlap_challenges(
    *,
    proposal,
    family,
    source_text: str,
):
    """
    Add benchmark-generated compound spans to the autonomous proposal
    when the model did not independently propose them.

    The admission gate receives only the resulting proposal and raw
    source. It does NOT receive canonical boundaries.
    """

    atoms = list(
        proposal.get(
            "atoms",
            []
        )
    )

    injected = 0

    for challenge in family[
        "overlap_challenges"
    ]:

        text = challenge[
            "text"
        ]

        if (
            source_text.count(
                text
            )
            != 1
        ):
            raise RuntimeError(
                "Overlap challenge must "
                "occur exactly once: "
                f"{family['id']} :: "
                f"{text!r}"
            )

        if _proposal_contains_exact(
            {
                "atoms": atoms
            },
            text,
        ):
            continue

        atoms.append(
            {
                "text": (
                    text
                ),
                "source_quote": (
                    text
                ),
                "_overlap_challenge": (
                    True
                ),
            }
        )

        injected += 1

    return {
        "atoms": atoms
    }, injected


def _source_evidence_text(
    candidate_decision: str,
    outcome_text: str,
) -> str:

    return (
        "DECISION: "
        + candidate_decision
        + "\n"
        + "OUTCOME: "
        + outcome_text
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


def _claim_audit(
    atoms,
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
            in atoms
        ]
    }

    return (
        admit_claims(
            proposal,
            atoms,
        )
    )


def _run_condition(
    *,
    condition_name: str,
    family,
    family_dir: Path,
    model,
    embedder,
    meter,
    admitted_atoms,
):
    """
    IMPORTANT:

    admitted_atoms are already frozen before entering this function.

    Canonical benchmark boundaries are not used to construct the
    lesson or the transfer decision.
    """

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
                "Controlled failed decision "
                "changed."
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
            render_role_aware_claims(
                atoms=admitted_atoms
            )
            if admitted_atoms
            else
            "SUPPORTED CLAIMS:\n"
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

        memory_text = "\n".join(
            transfer.memory_segments
        )

        claim_audit = (
            _claim_audit(
                admitted_atoms
            )
        )

        # Scoring occurs after the transfer decision has already
        # been produced.
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
            "admitted_atoms": (
                admitted_atoms
            ),
            "admitted_atom_count": (
                len(
                    admitted_atoms
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


def _count_overlap_challenge_rejections(
    *,
    rejected,
    family,
):
    challenges = {
        normalize_span_text(
            challenge[
                "text"
            ]
        )
        for challenge
        in family[
            "overlap_challenges"
        ]
    }

    rejected_challenges = set()

    for rejection in rejected:

        if (
            rejection.get(
                "reason"
            )
            !=
            "overlaps_admitted_span"
        ):
            continue

        candidate = (
            rejection.get(
                "candidate"
            )
        )

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        text = candidate.get(
            "text"
        )

        if isinstance(
            text,
            str,
        ):
            rejected_challenges.add(
                normalize_span_text(
                    text
                )
            )

    return len(
        challenges
        &
        rejected_challenges
    )


def _count_invented_admissions(
    *,
    atoms,
    source_text: str,
):
    return sum(
        1

        for atom
        in atoms

        if (
            source_text.count(
                atom[
                    "source_quote"
                ]
            )
            != 1
        )
    )


def _count_nonauthoritative_admissions(
    atoms,
):
    return sum(
        1

        for atom
        in atoms

        if (
            atom.get(
                "source_role"
            )
            !=
            AUTHORITATIVE_ROLE
        )
    )


def run_family_010(
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
    # CONDITION A
    #
    # Oracle canonical boundaries.
    #
    # This is the benchmark upper bound.
    # ================================================================

    oracle_atoms = (
        oracle_atoms_from_family(
            source_text=(
                source_text
            ),
            family=family,
        )
    )

    oracle = (
        _run_condition(
            condition_name=(
                "oracle_boundaries"
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            admitted_atoms=(
                oracle_atoms
            ),
        )
    )

    oracle_boundary_metrics = (
        canonical_boundary_metrics(
            admitted_atoms=(
                oracle_atoms
            ),
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    # ================================================================
    # CONDITION B
    #
    # Autonomous boundary discovery.
    #
    # One model call sees raw source only.
    # No family canonical boundary information enters the admission
    # gate.
    # ================================================================

    raw_response = (
        model
        .generate(
            build_autonomous_boundary_prompt(
                source_text
            )
        )
        .text
        .strip()
    )

    try:

        proposal = (
            parse_atom_proposal(
                raw_response
            )
        )

        parse_error = None

    except Exception as exc:

        proposal = {
            "atoms": []
        }

        parse_error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    model_proposal_sha256 = (
        _sha256_text(
            json.dumps(
                proposal,
                sort_keys=True,
            )
        )
    )

    shared_proposal, injected = (
        ensure_overlap_challenges(
            proposal=proposal,
            family=family,
            source_text=(
                source_text
            ),
        )
    )

    shared_proposal_sha256 = (
        _sha256_text(
            json.dumps(
                shared_proposal,
                sort_keys=True,
            )
        )
    )

    autonomous_gate = (
        admit_autonomous_atoms(
            proposal=(
                shared_proposal
            ),
            source_text=(
                source_text
            ),
        )
    )

    autonomous_atoms = (
        autonomous_gate[
            "admitted"
        ]
    )

    autonomous = (
        _run_condition(
            condition_name=(
                "autonomous_boundaries"
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            admitted_atoms=(
                autonomous_atoms
            ),
        )
    )

    autonomous_boundary_metrics = (
        canonical_boundary_metrics(
            admitted_atoms=(
                autonomous_atoms
            ),
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    source_equal = (
        oracle[
            "source_evidence_sha256"
        ]
        ==
        autonomous[
            "source_evidence_sha256"
        ]
    )

    if not source_equal:
        raise RuntimeError(
            "010 invalid: source evidence "
            "differs between conditions."
        )

    ancestry_valid = all(
        source_ancestry_valid(
            atom=atom,
            source_text=(
                source_text
            ),
        )

        for atom
        in autonomous_atoms
    )

    overlap_pairs = (
        count_overlapping_pairs(
            autonomous_atoms
        )
    )

    challenge_rejections = (
        _count_overlap_challenge_rejections(
            rejected=(
                autonomous_gate[
                    "rejected"
                ]
            ),
            family=family,
        )
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
        "raw_source": (
            source_text
        ),
        "raw_boundary_model_response": (
            raw_response
        ),
        "boundary_parse_error": (
            parse_error
        ),
        "model_atom_proposals": (
            len(
                proposal.get(
                    "atoms",
                    []
                )
            )
        ),
        "model_proposal_sha256": (
            model_proposal_sha256
        ),
        "shared_proposal_sha256": (
            shared_proposal_sha256
        ),
        "overlap_challenges": (
            len(
                family[
                    "overlap_challenges"
                ]
            )
        ),
        "overlap_challenges_injected": (
            injected
        ),
        "oracle": {
            **oracle,
            **oracle_boundary_metrics,
        },
        "autonomous": {
            **autonomous,
            **autonomous_boundary_metrics,
            "source_ancestry_valid": (
                ancestry_valid
            ),
            "invented_spans_admitted": (
                _count_invented_admissions(
                    atoms=(
                        autonomous_atoms
                    ),
                    source_text=(
                        source_text
                    ),
                )
            ),
            "nonauthoritative_spans_admitted": (
                _count_nonauthoritative_admissions(
                    autonomous_atoms
                )
            ),
            "overlapping_span_pairs_admitted": (
                overlap_pairs
            ),
            "overlap_challenge_rejections": (
                challenge_rejections
            ),
            "gate_rejections": (
                autonomous_gate[
                    "rejected"
                ]
            ),
        },
        "same_source_evidence": (
            source_equal
        ),
        "task_delta_oracle_to_autonomous": (
            int(
                autonomous[
                    "task_success"
                ]
            )
            -
            int(
                oracle[
                    "task_success"
                ]
            )
        ),
        "memory_word_delta_oracle_to_autonomous": (
            autonomous[
                "memory_word_count"
            ]
            -
            oracle[
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


def run_experiment_010(
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
        run_family_010(
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

    report = {
        "experiment": (
            "seed-growth-010"
        ),
        "classification": (
            "exploratory-fresh-"
            "autonomous-atomic-boundary-discovery"
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
                "oracle_canonical_atomic_boundaries"
            ),
            "B": (
                "autonomous_model_boundary_discovery_"
                "plus_runtime_source_validation"
            ),
        },

        # ------------------------------------------------------------
        # Task performance
        # ------------------------------------------------------------

        "oracle_task_passes": (
            _count(
                results,
                "oracle",
                "task_success",
            )
        ),
        "autonomous_task_passes": (
            _count(
                results,
                "autonomous",
                "task_success",
            )
        ),
        "oracle_complete_lessons": (
            _count(
                results,
                "oracle",
                "lesson_knowledge_complete",
            )
        ),
        "autonomous_complete_lessons": (
            _count(
                results,
                "autonomous",
                "lesson_knowledge_complete",
            )
        ),

        # ------------------------------------------------------------
        # Boundary quality
        # ------------------------------------------------------------

        "mean_oracle_boundary_recall": (
            _mean_metric(
                results,
                "oracle",
                "canonical_recall",
            )
        ),
        "mean_autonomous_boundary_recall": (
            _mean_metric(
                results,
                "autonomous",
                "canonical_recall",
            )
        ),
        "mean_oracle_boundary_precision": (
            _mean_metric(
                results,
                "oracle",
                "canonical_precision",
            )
        ),
        "mean_autonomous_boundary_precision": (
            _mean_metric(
                results,
                "autonomous",
                "canonical_precision",
            )
        ),
        "oracle_exact_boundary_families": (
            _count(
                results,
                "oracle",
                "complete",
            )
        ),
        "autonomous_exact_boundary_families": (
            _count(
                results,
                "autonomous",
                "complete",
            )
        ),

        # ------------------------------------------------------------
        # Runtime safety
        # ------------------------------------------------------------

        "autonomous_source_ancestry_valid_families": (
            _count(
                results,
                "autonomous",
                "source_ancestry_valid",
            )
        ),
        "autonomous_invented_spans_admitted": (
            _sum_metric(
                results,
                "autonomous",
                "invented_spans_admitted",
            )
        ),
        "autonomous_nonauthoritative_spans_admitted": (
            _sum_metric(
                results,
                "autonomous",
                "nonauthoritative_spans_admitted",
            )
        ),
        "autonomous_overlapping_span_pairs_admitted": (
            _sum_metric(
                results,
                "autonomous",
                "overlapping_span_pairs_admitted",
            )
        ),
        "autonomous_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "autonomous",
                "unsupported_claims_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Deliberate compound challenges
        # ------------------------------------------------------------

        "overlap_challenges": sum(
            family[
                "overlap_challenges"
            ]
            for family
            in results
        ),
        "overlap_challenges_injected": sum(
            family[
                "overlap_challenges_injected"
            ]
            for family
            in results
        ),
        "autonomous_overlap_challenge_rejections": (
            _sum_metric(
                results,
                "autonomous",
                "overlap_challenge_rejections",
            )
        ),

        # ------------------------------------------------------------
        # Cost
        # ------------------------------------------------------------

        "mean_oracle_memory_words": (
            _mean_metric(
                results,
                "oracle",
                "memory_word_count",
            )
        ),
        "mean_autonomous_memory_words": (
            _mean_metric(
                results,
                "autonomous",
                "memory_word_count",
            )
        ),
        "autonomous_boundary_discovery_model_calls": (
            len(
                results
            )
        ),

        # ------------------------------------------------------------
        # Experimental invariant
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
            "tasks_010.json"
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
        run_experiment_010(
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
        "oracle_task_passes",
        "autonomous_task_passes",
        "oracle_complete_lessons",
        "autonomous_complete_lessons",
        "mean_oracle_boundary_recall",
        "mean_autonomous_boundary_recall",
        "mean_oracle_boundary_precision",
        "mean_autonomous_boundary_precision",
        "oracle_exact_boundary_families",
        "autonomous_exact_boundary_families",
        "autonomous_source_ancestry_valid_families",
        "autonomous_invented_spans_admitted",
        "autonomous_nonauthoritative_spans_admitted",
        "autonomous_overlapping_span_pairs_admitted",
        "autonomous_unsupported_claims_admitted",
        "overlap_challenges",
        "autonomous_overlap_challenge_rejections",
        "mean_oracle_memory_words",
        "mean_autonomous_memory_words",
        "all_source_evidence_equal",
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
