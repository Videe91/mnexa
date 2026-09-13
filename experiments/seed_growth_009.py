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


from experiments.seed_growth_008 import (
    AUTHORITATIVE_ROLE,
    admit_role_gated_atoms,
    build_mixed_atomization_prompt,
    normalize_span_text,
    parse_atom_proposal,
    parse_role_regions,
    render_role_aware_claims,
    role_for_span,
)


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


def locate_atomic_units(
    *,
    source_text: str,
    family,
):
    """
    Locate the pre-registered atomic proposition boundaries
    inside the authoritative source region.

    Seed 009 deliberately uses known boundaries so the
    experiment tests atomicity admission, not boundary discovery.
    """

    regions = (
        parse_role_regions(
            source_text
        )
    )

    located = []

    for canonical in family[
        "atomic_units"
    ]:

        text = canonical[
            "text"
        ]

        count = (
            source_text.count(
                text
            )
        )

        if count != 1:
            raise RuntimeError(
                "Atomic unit must occur "
                "exactly once: "
                f"{family['id']} "
                f":: {canonical['id']} "
                f"count={count}"
            )

        start = (
            source_text.index(
                text
            )
        )

        end = (
            start
            + len(text)
        )

        role = role_for_span(
            start,
            end,
            regions,
        )

        if (
            role
            !=
            AUTHORITATIVE_ROLE
        ):
            raise RuntimeError(
                "Atomic unit is not inside "
                "authoritative correction: "
                f"{family['id']} "
                f":: {canonical['id']}"
            )

        located.append(
            {
                **canonical,
                "source_start": (
                    start
                ),
                "source_end": (
                    end
                ),
                "source_role": (
                    role
                ),
            }
        )

    located.sort(
        key=lambda item: (
            item[
                "source_start"
            ],
            item[
                "source_end"
            ],
        )
    )

    for previous, current in zip(
        located,
        located[1:],
    ):
        if (
            current[
                "source_start"
            ]
            <
            previous[
                "source_end"
            ]
        ):
            raise RuntimeError(
                "Canonical atomic units overlap."
            )

    return located


def span_atomicity_classification(
    *,
    start: int,
    end: int,
    units,
):
    """
    Classify a grounded authoritative span against
    the pre-registered proposition boundaries.
    """

    for unit in units:
        if (
            start
            ==
            unit[
                "source_start"
            ]
            and
            end
            ==
            unit[
                "source_end"
            ]
        ):
            return (
                "exact_atomic_unit"
            )

    overlaps = [
        unit

        for unit
        in units

        if (
            max(
                start,
                unit[
                    "source_start"
                ],
            )
            <
            min(
                end,
                unit[
                    "source_end"
                ],
            )
        )
    ]

    if len(
        overlaps
    ) > 1:
        return (
            "crosses_atomic_boundaries"
        )

    if len(
        overlaps
    ) == 1:
        return (
            "partial_atomic_unit"
        )

    return (
        "outside_atomic_units"
    )


def admit_atomic_role_atoms(
    *,
    proposal,
    source_text: str,
    family,
):
    """
    Seed 008 role gate
        +
    Seed 009 atomic-boundary gate.

    A candidate must first be an exact, authoritative,
    source-grounded span.

    It is then admitted only if its span equals one
    canonical atomic proposition boundary.
    """

    role_result = (
        admit_role_gated_atoms(
            proposal=proposal,
            source_text=(
                source_text
            ),
        )
    )

    units = (
        locate_atomic_units(
            source_text=(
                source_text
            ),
            family=family,
        )
    )

    admitted = []

    rejected = list(
        role_result[
            "rejected"
        ]
    )

    for atom in role_result[
        "admitted"
    ]:

        classification = (
            span_atomicity_classification(
                start=atom[
                    "source_start"
                ],
                end=atom[
                    "source_end"
                ],
                units=units,
            )
        )

        if (
            classification
            !=
            "exact_atomic_unit"
        ):
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
                        classification
                    ),

                    "source_role": (
                        atom[
                            "source_role"
                        ]
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

        admitted.append(
            {
                key: value

                for key, value
                in atom.items()

                if key != "id"
            }
        )

    return {
        "admitted": (
            _assign_ids(
                admitted
            )
        ),

        "rejected": (
            rejected
        ),

        "source_sha256": (
            role_result[
                "source_sha256"
            ]
        ),
    }


def atomic_recall_precision(
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

    matched = (
        expected
        & admitted
    )

    if expected:
        recall = (
            len(matched)
            /
            len(expected)
        )
    else:
        recall = 1.0

    if admitted:
        precision = (
            len(matched)
            /
            len(admitted)
        )
    else:
        precision = (
            1.0
            if not expected
            else 0.0
        )

    return {
        "atomic_recall": (
            recall
        ),

        "atomic_precision": (
            precision
        ),

        "expected_atomic_units": (
            len(expected)
        ),

        "matched_atomic_units": (
            len(matched)
        ),

        "total_admitted_atoms": (
            len(admitted)
        ),
    }


def _proposal_contains_exact(
    proposal,
    text: str,
) -> bool:

    target = (
        normalize_span_text(
            text
        )
    )

    for candidate in proposal.get(
        "atoms",
        [],
    ):

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        candidate_text = (
            candidate.get(
                "text"
            )
        )

        quote = (
            candidate.get(
                "source_quote"
            )
        )

        if (
            not isinstance(
                candidate_text,
                str,
            )
            or
            not isinstance(
                quote,
                str,
            )
        ):
            continue

        if (
            normalize_span_text(
                candidate_text
            )
            ==
            target
            and
            normalize_span_text(
                quote
            )
            ==
            target
        ):
            return True

    return False


def ensure_atomicity_challenges(
    *,
    proposal,
    family,
    source_text: str,
):
    """
    Inject pre-registered compound-but-valid authoritative
    spans if the live atomizer does not propose them itself.

    The same resulting proposal is used by both conditions.

    This guarantees the atomicity gate is actually challenged.
    """

    atoms = list(
        proposal.get(
            "atoms",
            [],
        )
    )

    injected = 0

    for challenge in family[
        "atomicity_challenges"
    ]:

        text = (
            challenge[
                "text"
            ]
        )

        if (
            source_text.count(
                text
            )
            != 1
        ):
            raise RuntimeError(
                "Atomicity challenge must "
                "occur exactly once: "
                f"{family['id']} "
                f":: {text}"
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

                "_atomicity_challenge": (
                    True
                ),
            }
        )

        injected += 1

    return {
        "atoms": atoms
    }, injected


def _classify_admitted(
    *,
    atoms,
    units,
):
    counts = {
        "exact_atomic_unit": 0,
        "crosses_atomic_boundaries": 0,
        "partial_atomic_unit": 0,
        "outside_atomic_units": 0,
    }

    for atom in atoms:

        classification = (
            span_atomicity_classification(
                start=atom[
                    "source_start"
                ],
                end=atom[
                    "source_end"
                ],
                units=units,
            )
        )

        counts[
            classification
        ] += 1

    return counts


def _challenge_admissions(
    *,
    admitted_atoms,
    family,
):
    admitted = {
        normalize_span_text(
            atom[
                "text"
            ]
        )
        for atom
        in admitted_atoms
    }

    challenges = {
        normalize_span_text(
            challenge[
                "text"
            ]
        )
        for challenge
        in family[
            "atomicity_challenges"
        ]
    }

    return len(
        admitted
        & challenges
    )


def _challenge_rejections(
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
            "atomicity_challenges"
        ]
    }

    rejected_texts = set()

    for rejection in rejected:

        if (
            rejection.get(
                "reason"
            )
            !=
            "crosses_atomic_boundaries"
        ):
            continue

        candidate = rejection.get(
            "candidate"
        )

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        text = (
            candidate.get(
                "text"
            )
        )

        if isinstance(
            text,
            str,
        ):
            rejected_texts.add(
                normalize_span_text(
                    text
                )
            )

    return len(
        challenges
        & rejected_texts
    )


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


def _score_lesson(
    text: str,
    family,
):
    from experiments.seed_growth import (
        grade_text,
    )

    return grade_text(
        text,
        family[
            "knowledge_grader"
        ],
    )


def _score_transfer(
    text: str,
    family,
):
    from experiments.seed_growth import (
        grade_text,
    )

    return grade_text(
        text,
        family[
            "transfer_grader"
        ],
    )


def _claim_gate_audit(
    atoms,
):
    from experiments.seed_growth_006 import (
        admit_claims,
    )

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

    return admit_claims(
        proposal,
        atoms,
    )


def _run_memory_condition(
    *,
    condition_name,
    family,
    family_dir,
    model,
    embedder,
    meter,
    admitted_atoms,
    gate_result,
):
    from mnexa_seed import (
        MnexaSeed,
    )

    from experiments.seed_growth_004 import (
        make_fidelity_reasoner,
    )

    db_path = (
        family_dir
        / f"{condition_name}.sqlite3"
    )

    if db_path.exists():
        db_path.unlink()

    mnexa = MnexaSeed(
        db_path,
        embedder=embedder,
        meter=meter,
    )

    units = (
        locate_atomic_units(
            source_text=family[
                "raw_source"
            ],
            family=family,
        )
    )

    try:
        experience_decision = (
            mnexa.decide(
                family[
                    "experience"
                ]["prompt"],

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
            experience_decision.text
            !=
            family[
                "candidate_decision"
            ]
        ):
            raise RuntimeError(
                "Controlled candidate "
                "decision changed."
            )

        outcome_text = (
            "EVALUATION RECORD:\n"
            + family[
                "raw_source"
            ]
        )

        outcome = (
            mnexa.observe_outcome(
                experience_decision.record_id,
                outcome_text,
                success=False,
            )
        )

        source_evidence = (
            _source_evidence_text(
                experience_decision.text,
                outcome_text,
            )
        )

        source_evidence_sha256 = (
            _sha256_text(
                source_evidence
            )
        )

        lesson_text = (
            render_role_aware_claims(
                atoms=admitted_atoms
            )
        )

        def consolidator(
            evidence: str,
        ) -> str:
            return lesson_text

        lesson = (
            mnexa.consolidate(
                experience_decision.record_id,
                consolidator,
            )
        )

        transfer = (
            mnexa.decide(
                family[
                    "transfer"
                ]["prompt"],

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

        atomic_metrics = (
            atomic_recall_precision(
                admitted_atoms=(
                    admitted_atoms
                ),
                expected_units=family[
                    "atomic_units"
                ],
            )
        )

        classification_counts = (
            _classify_admitted(
                atoms=(
                    admitted_atoms
                ),
                units=units,
            )
        )

        claim_audit = (
            _claim_gate_audit(
                admitted_atoms
            )
        )

        memory_text = "\n".join(
            transfer.memory_segments
        )

        return {
            "candidate_decision": (
                experience_decision.text
            ),

            "outcome": (
                outcome_text
            ),

            "outcome_id": (
                outcome.object_id
            ),

            "source_evidence_sha256": (
                source_evidence_sha256
            ),

            "lesson": (
                lesson.text
            ),

            "lesson_id": (
                lesson.object_id
            ),

            "lesson_knowledge_complete": (
                _score_lesson(
                    lesson.text,
                    family,
                )
            ),

            "transfer_decision": (
                transfer.text
            ),

            "transfer_task_sufficient": (
                _score_transfer(
                    transfer.text,
                    family,
                )
            ),

            "task_success": (
                _score_transfer(
                    transfer.text,
                    family,
                )
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

            "atomic_recall": (
                atomic_metrics[
                    "atomic_recall"
                ]
            ),

            "atomic_precision": (
                atomic_metrics[
                    "atomic_precision"
                ]
            ),

            "matched_atomic_units": (
                atomic_metrics[
                    "matched_atomic_units"
                ]
            ),

            "exact_atomic_units_admitted": (
                classification_counts[
                    "exact_atomic_unit"
                ]
            ),

            "compound_atoms_admitted": (
                classification_counts[
                    "crosses_atomic_boundaries"
                ]
            ),

            "partial_atoms_admitted": (
                classification_counts[
                    "partial_atomic_unit"
                ]
            ),

            "outside_atomic_units_admitted": (
                classification_counts[
                    "outside_atomic_units"
                ]
            ),

            "atomicity_challenge_admissions": (
                _challenge_admissions(
                    admitted_atoms=(
                        admitted_atoms
                    ),
                    family=family,
                )
            ),

            "boundary_rejections": (
                sum(
                    1

                    for rejection
                    in gate_result[
                        "rejected"
                    ]

                    if rejection.get(
                        "reason"
                    )
                    in {
                        "crosses_atomic_boundaries",
                        "partial_atomic_unit",
                        "outside_atomic_units",
                    }
                )
            ),

            "atomicity_challenge_rejections": (
                _challenge_rejections(
                    rejected=(
                        gate_result[
                            "rejected"
                        ]
                    ),
                    family=family,
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


def run_family_009(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
):
    family_dir = (
        Path(work_dir)
        / family[
            "id"
        ]
    )

    family_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------
    # ONE atomizer call.
    #
    # Both conditions get this exact proposal.
    # ------------------------------------------------------------

    raw_response = (
        model
        .generate(
            build_mixed_atomization_prompt(
                source_text=family[
                    "raw_source"
                ]
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

    shared_proposal, injected = (
        ensure_atomicity_challenges(
            proposal=proposal,
            family=family,
            source_text=family[
                "raw_source"
            ],
        )
    )

    proposal_sha256 = (
        _sha256_text(
            json.dumps(
                shared_proposal,
                sort_keys=True,
            )
        )
    )

    # ================================================================
    # A — CURRENT ROLE-GATED MEMORY
    #
    # Source span valid
    # Role eligible
    # Granularity unchecked
    # ================================================================

    current_gate = (
        admit_role_gated_atoms(
            proposal=(
                shared_proposal
            ),
            source_text=family[
                "raw_source"
            ],
        )
    )

    current = (
        _run_memory_condition(
            condition_name=(
                "role_gated_current"
            ),

            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,

            admitted_atoms=(
                current_gate[
                    "admitted"
                ]
            ),

            gate_result=(
                current_gate
            ),
        )
    )

    # ================================================================
    # B — ROLE GATE + ATOMICITY GATE
    # ================================================================

    atomicity_gate = (
        admit_atomic_role_atoms(
            proposal=(
                shared_proposal
            ),

            source_text=family[
                "raw_source"
            ],

            family=family,
        )
    )

    atomicity = (
        _run_memory_condition(
            condition_name=(
                "atomicity_gated"
            ),

            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,

            admitted_atoms=(
                atomicity_gate[
                    "admitted"
                ]
            ),

            gate_result=(
                atomicity_gate
            ),
        )
    )

    same_source_evidence = (
        current[
            "source_evidence_sha256"
        ]
        ==
        atomicity[
            "source_evidence_sha256"
        ]
    )

    if not same_source_evidence:
        raise RuntimeError(
            "009 ablation invalid: "
            "source evidence differs."
        )

    return {
        "family_id": (
            family[
                "id"
            ]
        ),

        "raw_atom_model_response": (
            raw_response
        ),

        "atom_parse_error": (
            parse_error
        ),

        "model_atom_proposals": (
            len(
                proposal.get(
                    "atoms",
                    [],
                )
            )
        ),

        "shared_atom_proposal_sha256": (
            proposal_sha256
        ),

        "atomicity_challenges": (
            len(
                family[
                    "atomicity_challenges"
                ]
            )
        ),

        "atomicity_challenges_injected": (
            injected
        ),

        "mnexa_role_gated_current": (
            current
        ),

        "mnexa_atomicity_gated": (
            atomicity
        ),

        "same_source_evidence": (
            same_source_evidence
        ),

        "same_atom_proposal": True,

        "task_lift_a_to_b": (
            int(
                atomicity[
                    "task_success"
                ]
            )
            -
            int(
                current[
                    "task_success"
                ]
            )
        ),

        "atomic_precision_lift_a_to_b": (
            atomicity[
                "atomic_precision"
            ]
            -
            current[
                "atomic_precision"
            ]
        ),

        "memory_word_delta_a_to_b": (
            atomicity[
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
        sum(values)
        /
        len(values)
    )


def run_experiment_009(
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
        .now(timezone.utc)
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    run_dir = (
        Path(results_dir)
        / run_id
    )

    state_dir = (
        run_dir
        / "state"
    )

    state_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = [
        run_family_009(
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

    report = {
        "experiment": (
            "seed-growth-009"
        ),

        "classification": (
            "exploratory-fresh-"
            "evidence-atomicity-ablation"
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
            len(
                results
            )
        ),

        "conditions": {
            "A": (
                "mnexa_role_gated_"
                "atomicity_unchecked"
            ),

            "B": (
                "mnexa_role_gated_"
                "plus_atomicity_gate"
            ),
        },

        "current_task_passes": (
            _count(
                results,
                "mnexa_role_gated_current",
                "task_success",
            )
        ),

        "atomicity_task_passes": (
            _count(
                results,
                "mnexa_atomicity_gated",
                "task_success",
            )
        ),

        "current_complete_lessons": (
            _count(
                results,
                "mnexa_role_gated_current",
                "lesson_knowledge_complete",
            )
        ),

        "atomicity_complete_lessons": (
            _count(
                results,
                "mnexa_atomicity_gated",
                "lesson_knowledge_complete",
            )
        ),

        "mean_current_atomic_recall": (
            _mean_metric(
                results,
                "mnexa_role_gated_current",
                "atomic_recall",
            )
        ),

        "mean_atomicity_atomic_recall": (
            _mean_metric(
                results,
                "mnexa_atomicity_gated",
                "atomic_recall",
            )
        ),

        "mean_current_atomic_precision": (
            _mean_metric(
                results,
                "mnexa_role_gated_current",
                "atomic_precision",
            )
        ),

        "mean_atomicity_atomic_precision": (
            _mean_metric(
                results,
                "mnexa_atomicity_gated",
                "atomic_precision",
            )
        ),

        "current_compound_atoms_admitted": (
            _sum_metric(
                results,
                "mnexa_role_gated_current",
                "compound_atoms_admitted",
            )
        ),

        "atomicity_compound_atoms_admitted": (
            _sum_metric(
                results,
                "mnexa_atomicity_gated",
                "compound_atoms_admitted",
            )
        ),

        "current_partial_atoms_admitted": (
            _sum_metric(
                results,
                "mnexa_role_gated_current",
                "partial_atoms_admitted",
            )
        ),

        "atomicity_partial_atoms_admitted": (
            _sum_metric(
                results,
                "mnexa_atomicity_gated",
                "partial_atoms_admitted",
            )
        ),

        "atomicity_challenges": sum(
            family[
                "atomicity_challenges"
            ]
            for family
            in results
        ),

        "current_atomicity_challenge_admissions": (
            _sum_metric(
                results,
                "mnexa_role_gated_current",
                "atomicity_challenge_admissions",
            )
        ),

        "atomicity_challenge_rejections": (
            _sum_metric(
                results,
                "mnexa_atomicity_gated",
                "atomicity_challenge_rejections",
            )
        ),

        "atomicity_boundary_rejections": (
            _sum_metric(
                results,
                "mnexa_atomicity_gated",
                "boundary_rejections",
            )
        ),

        "current_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "mnexa_role_gated_current",
                "unsupported_claims_admitted",
            )
        ),

        "atomicity_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "mnexa_atomicity_gated",
                "unsupported_claims_admitted",
            )
        ),

        "mean_current_memory_words": (
            _mean_metric(
                results,
                "mnexa_role_gated_current",
                "memory_word_count",
            )
        ),

        "mean_atomicity_memory_words": (
            _mean_metric(
                results,
                "mnexa_atomicity_gated",
                "memory_word_count",
            )
        ),

        "all_source_evidence_equal": (
            all(
                family[
                    "same_source_evidence"
                ]

                for family
                in results
            )
        ),

        "all_atom_proposals_equal": (
            all(
                family[
                    "same_atom_proposal"
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
        / "result.json"
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n"
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
            "tasks_009.json"
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
        run_experiment_009(
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
        "atomicity_task_passes",
        "current_complete_lessons",
        "atomicity_complete_lessons",
        "mean_current_atomic_recall",
        "mean_atomicity_atomic_recall",
        "mean_current_atomic_precision",
        "mean_atomicity_atomic_precision",
        "current_compound_atoms_admitted",
        "atomicity_compound_atoms_admitted",
        "atomicity_challenges",
        "current_atomicity_challenge_admissions",
        "atomicity_challenge_rejections",
        "atomicity_boundary_rejections",
        "mean_current_memory_words",
        "mean_atomicity_memory_words",
        "all_source_evidence_equal",
        "all_atom_proposals_equal",
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
