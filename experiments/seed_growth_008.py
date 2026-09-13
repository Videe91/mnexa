from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


AUTHORITATIVE_ROLE = "authoritative_correction"
INELIGIBLE_ROLES = (
    "status",
    "failed_decision",
    "operator_note",
    "diagnostic_metadata",
)
ALL_ROLES = (
    "status",
    "failed_decision",
    AUTHORITATIVE_ROLE,
    "operator_note",
    "diagnostic_metadata",
)

ROLE_START_TEMPLATE = "<<<ROLE:{role}>>>"
ROLE_END_TEMPLATE = "<<<END_ROLE:{role}>>>"


MIXED_ATOMIZATION_INSTRUCTION = """
MIXED-EVIDENCE ATOMIZATION

You are extracting atomic statements from a structured historical source.

IMPORTANT: atomization and epistemic admission are separate jobs.
Do NOT decide which statements deserve promotion to reusable knowledge.
Extract distinct atomic statements from ALL source sections.

Rules:

1. Extract explicit atomic statements from every role section.
2. For each candidate provide:
   - "text": the exact atomic statement
   - "source_quote": the exact matching substring from the source
3. COPY the source_quote exactly.
4. Set text equal to that exact source_quote.
5. Do not paraphrase, infer, generalize, or combine statements.
6. Do not copy role markers themselves.
7. Do not include private reasoning.

Return JSON only:

{
  "atoms": [
    {
      "text": "<exact source statement>",
      "source_quote": "<exact source statement>"
    }
  ]
}
""".strip()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_span_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.!?]+$", "", text)
    return text.strip()


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if lines:
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_atom_proposal(text: str):
    payload = json.loads(_strip_json_fence(text))
    if not isinstance(payload, dict):
        raise ValueError("Atom proposal must be a JSON object.")

    atoms = payload.get("atoms")
    if not isinstance(atoms, list):
        raise ValueError("Atom proposal must contain an atoms list.")

    return payload


def parse_role_regions(source_text: str):
    """Return deterministic role-content spans, excluding role markers."""

    regions = []
    previous_end = -1

    for role in ALL_ROLES:
        start_marker = ROLE_START_TEMPLATE.format(role=role)
        end_marker = ROLE_END_TEMPLATE.format(role=role)

        if source_text.count(start_marker) != 1:
            raise ValueError(
                f"Expected exactly one start marker for role {role}."
            )

        if source_text.count(end_marker) != 1:
            raise ValueError(
                f"Expected exactly one end marker for role {role}."
            )

        marker_start = source_text.index(start_marker)
        content_start = marker_start + len(start_marker)

        if (
            source_text[
                content_start:content_start + 1
            ]
            == "\n"
        ):
            content_start += 1

        marker_end = source_text.index(
            end_marker,
            content_start,
        )

        content_end = marker_end

        if (
            content_end > content_start
            and source_text[
                content_end - 1:content_end
            ]
            == "\n"
        ):
            content_end -= 1

        if marker_start <= previous_end:
            raise ValueError(
                "Role regions are not strictly ordered."
            )

        regions.append(
            {
                "role": role,
                "content_start": content_start,
                "content_end": content_end,
                "marker_start": marker_start,
                "marker_end": (
                    marker_end
                    + len(end_marker)
                ),
            }
        )

        previous_end = (
            marker_end
            + len(end_marker)
        )

    return regions


def role_for_span(
    start: int,
    end: int,
    regions,
):
    if (
        start < 0
        or end <= start
    ):
        return None

    matches = [
        region["role"]
        for region in regions
        if (
            start
            >= region[
                "content_start"
            ]
            and end
            <= region[
                "content_end"
            ]
        )
    ]

    if len(matches) == 1:
        return matches[0]

    return None


def _validate_span_candidate(
    *,
    index,
    candidate,
    source_text,
    regions,
):
    if not isinstance(
        candidate,
        dict,
    ):
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "atom_not_object"
            ),
        }

    text = candidate.get(
        "text"
    )

    source_quote = candidate.get(
        "source_quote"
    )

    if (
        not isinstance(
            text,
            str,
        )
        or not text.strip()
    ):
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "missing_atom_text"
            ),
        }

    if (
        not isinstance(
            source_quote,
            str,
        )
        or not source_quote.strip()
    ):
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "missing_source_quote"
            ),
        }

    count = source_text.count(
        source_quote
    )

    if count == 0:
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "source_quote_not_found"
            ),
        }

    if count > 1:
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "source_quote_ambiguous"
            ),
        }

    if (
        normalize_span_text(
            text
        )
        !=
        normalize_span_text(
            source_quote
        )
    ):
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "atom_not_equal_to_"
                "source_quote"
            ),
        }

    start = source_text.index(
        source_quote
    )

    end = (
        start
        + len(source_quote)
    )

    role = role_for_span(
        start,
        end,
        regions,
    )

    if role is None:
        return None, {
            "index": index,
            "candidate": candidate,
            "reason": (
                "source_span_outside_"
                "role_content"
            ),
            "source_start": start,
            "source_end": end,
        }

    return {
        "text": source_quote,
        "source_quote": source_quote,
        "source_start": start,
        "source_end": end,
        "source_role": role,
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
        "span_sha256": (
            _sha256_text(
                source_quote
            )
        ),
    }, None


def _assign_atom_ids(
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
            "id": f"E{ordinal}",
            **atom,
        }
        for ordinal, atom
        in enumerate(
            ordered,
            start=1,
        )
    ]


def ground_span_atoms(
    *,
    proposal,
    source_text: str,
):
    """
    Seed-007-style exact span gate.

    Any exact atomic statement inside a recognized role region can pass.
    This intentionally does NOT distinguish epistemic role.
    """

    regions = parse_role_regions(
        source_text
    )

    admitted_pre_id = []
    rejected = []
    seen_spans = set()

    for index, candidate in enumerate(
        proposal.get(
            "atoms",
            [],
        )
    ):
        atom, error = (
            _validate_span_candidate(
                index=index,
                candidate=candidate,
                source_text=(
                    source_text
                ),
                regions=regions,
            )
        )

        if error is not None:
            rejected.append(
                error
            )
            continue

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
                    "index": index,
                    "candidate": (
                        candidate
                    ),
                    "reason": (
                        "duplicate_source_span"
                    ),
                    "source_role": (
                        atom[
                            "source_role"
                        ]
                    ),
                }
            )
            continue

        seen_spans.add(
            span_key
        )

        admitted_pre_id.append(
            atom
        )

    return {
        "admitted": (
            _assign_atom_ids(
                admitted_pre_id
            )
        ),
        "rejected": rejected,
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
    }


def admit_role_gated_atoms(
    *,
    proposal,
    source_text: str,
    eligible_roles=(
        AUTHORITATIVE_ROLE,
    ),
):
    """
    Exact span grounding plus deterministic evidence-role eligibility.

    A statement can be physically grounded in history and still be ineligible
    for promotion to reusable knowledge.
    """

    span_result = (
        ground_span_atoms(
            proposal=proposal,
            source_text=(
                source_text
            ),
        )
    )

    admitted_pre_id = []
    rejected = list(
        span_result[
            "rejected"
        ]
    )

    for atom in span_result[
        "admitted"
    ]:
        if (
            atom[
                "source_role"
            ]
            not in eligible_roles
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
                        "ineligible_evidence_role"
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

        admitted_pre_id.append(
            {
                key: value
                for key, value
                in atom.items()
                if key != "id"
            }
        )

    return {
        "admitted": (
            _assign_atom_ids(
                admitted_pre_id
            )
        ),
        "rejected": rejected,
        "source_sha256": (
            span_result[
                "source_sha256"
            ]
        ),
    }


def authoritative_recall_precision(
    *,
    admitted_atoms,
    expected_authoritative_texts,
):
    expected = {
        normalize_span_text(
            text
        )
        for text
        in expected_authoritative_texts
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

    recall = (
        len(matched)
        /
        len(expected)

        if expected
        else 1.0
    )

    precision = (
        len(matched)
        /
        len(admitted)

        if admitted
        else 1.0
    )

    return {
        "authoritative_recall": (
            recall
        ),
        "authoritative_precision": (
            precision
        ),
        "authoritative_expected_count": (
            len(expected)
        ),
        "authoritative_matched_count": (
            len(matched)
        ),
        "total_admitted_count": (
            len(admitted)
        ),
    }


def _proposal_contains_exact_quote(
    proposal,
    text: str,
) -> bool:
    target = normalize_span_text(
        text
    )

    for atom in proposal.get(
        "atoms",
        [],
    ):
        if not isinstance(
            atom,
            dict,
        ):
            continue

        quote = atom.get(
            "source_quote"
        )

        atom_text = atom.get(
            "text"
        )

        if (
            not isinstance(
                quote,
                str,
            )
            or not isinstance(
                atom_text,
                str,
            )
        ):
            continue

        if (
            normalize_span_text(
                quote
            )
            == target
            and
            normalize_span_text(
                atom_text
            )
            == target
        ):
            return True

    return False


def ensure_role_challenges(
    *,
    proposal,
    family,
    source_text: str,
):
    """
    Ensure each pre-registered ineligible, but physically grounded, statement
    is present in the shared B/C proposal at least once.

    This is analogous to Seed 007's injected adversarial span challenges: the
    experiment must exercise the role gate even if the model omits a distractor.
    """

    atoms = list(
        proposal.get(
            "atoms",
            [],
        )
    )

    added = 0

    for challenge in family.get(
        "role_challenges",
        [],
    ):
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
                "Role challenge must occur "
                "exactly once: "
                f"{family.get('id')} "
                f":: {text}"
            )

        if _proposal_contains_exact_quote(
            {
                "atoms": atoms
            },
            text,
        ):
            continue

        atoms.append(
            {
                "text": text,
                "source_quote": (
                    text
                ),
                "_role_challenge": (
                    True
                ),
            }
        )

        added += 1

    return {
        "atoms": atoms
    }, added


def build_mixed_atomization_prompt(
    *,
    source_text: str,
) -> str:
    return f"""
{MIXED_ATOMIZATION_INSTRUCTION}

--- MIXED HISTORICAL SOURCE START ---
{source_text}
--- MIXED HISTORICAL SOURCE END ---

Return JSON only.
""".strip()


def _claims_from_atoms(
    atoms,
):
    return {
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
            for atom in atoms
        ]
    }


def _admit_claims_runtime(
    atoms,
):
    from experiments.seed_growth_006 import (
        admit_claims,
    )

    proposal = (
        _claims_from_atoms(
            atoms
        )
    )

    result = admit_claims(
        proposal,
        atoms,
    )

    if result[
        "rejected"
    ]:
        raise RuntimeError(
            "008 deterministic 1:1 "
            "claim proposal unexpectedly "
            "failed ancestry admission."
        )

    return result


def render_role_aware_claims(
    *,
    atoms,
) -> str:
    claim_result = (
        _admit_claims_runtime(
            atoms
        )
    )

    by_id = {
        atom[
            "id"
        ]: atom
        for atom in atoms
    }

    if not claim_result[
        "admitted"
    ]:
        return (
            "SUPPORTED CLAIMS:\n"
            "(none admitted)"
        )

    lines = [
        "SUPPORTED CLAIMS:"
    ]

    for claim in claim_result[
        "admitted"
    ]:
        evidence_id = (
            claim[
                "evidence_ids"
            ][0]
        )

        atom = by_id[
            evidence_id
        ]

        lines.append(
            "- "
            f"[{evidence_id} "
            f"role={atom['source_role']} "
            f"source_span="
            f"{atom['source_start']}:"
            f"{atom['source_end']} "
            f"span_sha256="
            f"{atom['span_sha256']}] "
            f"{claim['text']}"
        )

    return "\n".join(
        lines
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


def _role_counts(
    atoms,
):
    counts = {
        role: 0
        for role in ALL_ROLES
    }

    for atom in atoms:
        role = atom.get(
            "source_role"
        )

        if role in counts:
            counts[
                role
            ] += 1

    return counts


def _challenge_rejections(
    *,
    gate_result,
    family,
):
    challenge_keys = {
        (
            challenge[
                "role"
            ],
            normalize_span_text(
                challenge[
                    "text"
                ]
            ),
        )
        for challenge
        in family.get(
            "role_challenges",
            [],
        )
    }

    rejected_keys = {
        (
            rejection.get(
                "source_role"
            ),
            normalize_span_text(
                rejection
                .get(
                    "candidate",
                    {},
                )
                .get(
                    "text",
                    "",
                )
            ),
        )
        for rejection
        in gate_result.get(
            "rejected",
            [],
        )
        if (
            rejection.get(
                "reason"
            )
            ==
            "ineligible_evidence_role"
            and isinstance(
                rejection.get(
                    "candidate"
                ),
                dict,
            )
        )
    }

    return len(
        challenge_keys
        & rejected_keys
    )


def _score_transfer(
    text: str,
    family,
):
    from experiments.seed_growth import (
        grade_text,
    )

    sufficient = grade_text(
        text,
        family[
            "transfer_grader"
        ],
    )

    leaked_nonknowledge = any(
        re.search(
            pattern,
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )
        for pattern
        in family.get(
            "nonknowledge_regex",
            [],
        )
    )

    return {
        "task_sufficient": (
            sufficient
        ),
        "nonknowledge_leak": (
            leaked_nonknowledge
        ),
        "task_success": (
            sufficient
            and
            not leaked_nonknowledge
        ),
    }


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


def _run_memory_condition(
    *,
    condition_name,
    family,
    family_dir,
    model,
    embedder,
    meter,
    admitted_atoms,
    admission_audit,
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

        transfer_score = (
            _score_transfer(
                transfer.text,
                family,
            )
        )

        expected_authoritative = [
            atom[
                "text"
            ]
            for atom
            in family[
                "authoritative_atoms"
            ]
        ]

        rp = (
            authoritative_recall_precision(
                admitted_atoms=(
                    admitted_atoms
                ),
                expected_authoritative_texts=(
                    expected_authoritative
                ),
            )
        )

        claim_result = (
            _admit_claims_runtime(
                admitted_atoms
            )
        )

        role_counts = (
            _role_counts(
                admitted_atoms
            )
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
                transfer_score[
                    "task_sufficient"
                ]
            ),

            "transfer_nonknowledge_leak": (
                transfer_score[
                    "nonknowledge_leak"
                ]
            ),

            "task_success": (
                transfer_score[
                    "task_success"
                ]
            ),

            "memory_segments": list(
                transfer.memory_segments
            ),

            "admitted_atoms": (
                admitted_atoms
            ),

            "admitted_atom_count": (
                len(
                    admitted_atoms
                )
            ),

            "authoritative_recall": (
                rp[
                    "authoritative_recall"
                ]
            ),

            "authoritative_precision": (
                rp[
                    "authoritative_precision"
                ]
            ),

            "authoritative_matched_count": (
                rp[
                    "authoritative_matched_count"
                ]
            ),

            "ineligible_atoms_admitted": (
                sum(
                    count
                    for role, count
                    in role_counts.items()
                    if role
                    in INELIGIBLE_ROLES
                )
            ),

            "role_counts": (
                role_counts
            ),

            "claims_admitted": (
                len(
                    claim_result[
                        "admitted"
                    ]
                )
            ),

            "unsupported_claims_admitted": (
                claim_result[
                    "unsupported_claims_admitted"
                ]
            ),

            **admission_audit,
        }

    finally:
        mnexa.close()


def run_family_008(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
):
    from mnexa_seed import (
        MnexaSeed,
    )

    from experiments.seed_growth_004 import (
        make_fidelity_reasoner,
    )

    family_dir = (
        Path(work_dir)
        / family["id"]
    )

    family_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # One atomization call only.
    # Both B and C consume the identical proposal.
    raw_atom_response = (
        model
        .generate(
            build_mixed_atomization_prompt(
                source_text=(
                    family[
                        "raw_source"
                    ]
                )
            )
        )
        .text
        .strip()
    )

    try:
        model_proposal = (
            parse_atom_proposal(
                raw_atom_response
            )
        )

    except Exception as exc:
        model_proposal = {
            "atoms": []
        }

        atom_parse_error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    else:
        atom_parse_error = None

    shared_proposal, injected_challenge_count = (
        ensure_role_challenges(
            proposal=(
                model_proposal
            ),
            family=family,
            source_text=(
                family[
                    "raw_source"
                ]
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

    # ================================================================
    # A — NO MEMORY
    # ================================================================

    baseline_db = (
        family_dir
        / "baseline.sqlite3"
    )

    if baseline_db.exists():
        baseline_db.unlink()

    baseline = MnexaSeed(
        baseline_db,
        embedder=embedder,
        meter=meter,
    )

    try:
        decision = (
            baseline.decide(
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

        score = (
            _score_transfer(
                decision.text,
                family,
            )
        )

        baseline_result = {
            "decision": (
                decision.text
            ),

            "transfer_task_sufficient": (
                score[
                    "task_sufficient"
                ]
            ),

            "transfer_nonknowledge_leak": (
                score[
                    "nonknowledge_leak"
                ]
            ),

            "task_success": (
                score[
                    "task_success"
                ]
            ),
        }

    finally:
        baseline.close()

    # ================================================================
    # B — EXACT SOURCE-SPAN GROUNDING ONLY
    # ================================================================

    span_only_gate = (
        ground_span_atoms(
            proposal=(
                shared_proposal
            ),
            source_text=(
                family[
                    "raw_source"
                ]
            ),
        )
    )

    span_only_audit = {
        "raw_atom_model_response": (
            raw_atom_response
        ),

        "atom_parse_error": (
            atom_parse_error
        ),

        "model_atom_proposals": (
            len(
                model_proposal.get(
                    "atoms",
                    [],
                )
            )
        ),

        "shared_atom_proposal_sha256": (
            shared_proposal_sha256
        ),

        "role_challenges": (
            len(
                family.get(
                    "role_challenges",
                    [],
                )
            )
        ),

        "role_challenges_injected": (
            injected_challenge_count
        ),

        "span_gate_rejections": (
            len(
                span_only_gate[
                    "rejected"
                ]
            )
        ),
    }

    span_only = (
        _run_memory_condition(
            condition_name=(
                "span_only"
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            admitted_atoms=(
                span_only_gate[
                    "admitted"
                ]
            ),
            admission_audit=(
                span_only_audit
            ),
        )
    )

    # ================================================================
    # C — EXACT SOURCE SPAN + EVIDENCE ROLE
    # ================================================================

    role_gate = (
        admit_role_gated_atoms(
            proposal=(
                shared_proposal
            ),
            source_text=(
                family[
                    "raw_source"
                ]
            ),
        )
    )

    role_gate_audit = {
        "raw_atom_model_response": (
            raw_atom_response
        ),

        "atom_parse_error": (
            atom_parse_error
        ),

        "model_atom_proposals": (
            len(
                model_proposal.get(
                    "atoms",
                    [],
                )
            )
        ),

        "shared_atom_proposal_sha256": (
            shared_proposal_sha256
        ),

        "role_challenges": (
            len(
                family.get(
                    "role_challenges",
                    [],
                )
            )
        ),

        "role_challenges_injected": (
            injected_challenge_count
        ),

        "role_gate_rejections": (
            sum(
                1
                for rejection
                in role_gate[
                    "rejected"
                ]
                if (
                    rejection.get(
                        "reason"
                    )
                    ==
                    "ineligible_evidence_role"
                )
            )
        ),

        "role_challenge_rejections": (
            _challenge_rejections(
                gate_result=(
                    role_gate
                ),
                family=family,
            )
        ),

        "span_gate_rejections": (
            sum(
                1
                for rejection
                in role_gate[
                    "rejected"
                ]
                if (
                    rejection.get(
                        "reason"
                    )
                    !=
                    "ineligible_evidence_role"
                )
            )
        ),
    }

    role_gated = (
        _run_memory_condition(
            condition_name=(
                "role_gated"
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            admitted_atoms=(
                role_gate[
                    "admitted"
                ]
            ),
            admission_audit=(
                role_gate_audit
            ),
        )
    )

    same_source_evidence = (
        span_only[
            "source_evidence_sha256"
        ]
        ==
        role_gated[
            "source_evidence_sha256"
        ]
    )

    same_atom_proposal = (
        span_only[
            "shared_atom_proposal_sha256"
        ]
        ==
        role_gated[
            "shared_atom_proposal_sha256"
        ]
    )

    if not same_source_evidence:
        raise RuntimeError(
            "008 ablation invalid: "
            "B and C received different "
            "historical source evidence."
        )

    if not same_atom_proposal:
        raise RuntimeError(
            "008 ablation invalid: "
            "B and C received different "
            "atom proposals."
        )

    return {
        "family_id": (
            family[
                "id"
            ]
        ),

        "baseline": (
            baseline_result
        ),

        "mnexa_span_only": (
            span_only
        ),

        "mnexa_role_gated": (
            role_gated
        ),

        "same_source_evidence": (
            same_source_evidence
        ),

        "same_atom_proposal": (
            same_atom_proposal
        ),

        "task_lift_b_to_c": (
            int(
                role_gated[
                    "task_success"
                ]
            )
            -
            int(
                span_only[
                    "task_success"
                ]
            )
        ),

        "precision_lift_b_to_c": (
            role_gated[
                "authoritative_precision"
            ]
            -
            span_only[
                "authoritative_precision"
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

    return (
        sum(values)
        /
        len(values)

        if values
        else 0.0
    )


def run_experiment_008(
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
        run_family_008(
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
            "seed-growth-008"
        ),

        "classification": (
            "exploratory-fresh-"
            "evidence-role-ablation"
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
            len(results)
        ),

        "conditions": {
            "A": (
                "baseline_no_memory"
            ),
            "B": (
                "mnexa_exact_span_"
                "grounding_without_role_gate"
            ),
            "C": (
                "mnexa_exact_span_"
                "grounding_plus_"
                "authoritative_role_gate"
            ),
        },

        "baseline_task_passes": (
            _count(
                results,
                "baseline",
                "task_success",
            )
        ),

        "span_only_task_passes": (
            _count(
                results,
                "mnexa_span_only",
                "task_success",
            )
        ),

        "role_gated_task_passes": (
            _count(
                results,
                "mnexa_role_gated",
                "task_success",
            )
        ),

        "span_only_complete_lessons": (
            _count(
                results,
                "mnexa_span_only",
                "lesson_knowledge_complete",
            )
        ),

        "role_gated_complete_lessons": (
            _count(
                results,
                "mnexa_role_gated",
                "lesson_knowledge_complete",
            )
        ),

        "span_only_ineligible_atoms_admitted": (
            _sum_metric(
                results,
                "mnexa_span_only",
                "ineligible_atoms_admitted",
            )
        ),

        "role_gated_ineligible_atoms_admitted": (
            _sum_metric(
                results,
                "mnexa_role_gated",
                "ineligible_atoms_admitted",
            )
        ),

        "mean_span_only_authoritative_recall": (
            _mean_metric(
                results,
                "mnexa_span_only",
                "authoritative_recall",
            )
        ),

        "mean_role_gated_authoritative_recall": (
            _mean_metric(
                results,
                "mnexa_role_gated",
                "authoritative_recall",
            )
        ),

        "mean_span_only_authoritative_precision": (
            _mean_metric(
                results,
                "mnexa_span_only",
                "authoritative_precision",
            )
        ),

        "mean_role_gated_authoritative_precision": (
            _mean_metric(
                results,
                "mnexa_role_gated",
                "authoritative_precision",
            )
        ),

        "role_challenges": (
            _sum_metric(
                results,
                "mnexa_role_gated",
                "role_challenges",
            )
        ),

        "role_challenge_rejections": (
            _sum_metric(
                results,
                "mnexa_role_gated",
                "role_challenge_rejections",
            )
        ),

        "role_gate_rejections": (
            _sum_metric(
                results,
                "mnexa_role_gated",
                "role_gate_rejections",
            )
        ),

        "span_only_transfer_nonknowledge_leaks": (
            _count(
                results,
                "mnexa_span_only",
                "transfer_nonknowledge_leak",
            )
        ),

        "role_gated_transfer_nonknowledge_leaks": (
            _count(
                results,
                "mnexa_role_gated",
                "transfer_nonknowledge_leak",
            )
        ),

        "span_only_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "mnexa_span_only",
                "unsupported_claims_admitted",
            )
        ),

        "role_gated_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "mnexa_role_gated",
                "unsupported_claims_admitted",
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

        "mixed_atomization_instruction": (
            MIXED_ATOMIZATION_INSTRUCTION
        ),

        "families": (
            results
        ),
    }

    for role in ALL_ROLES:
        report[
            f"span_only_{role}_"
            "atoms_admitted"
        ] = sum(
            family[
                "mnexa_span_only"
            ][
                "role_counts"
            ].get(
                role,
                0,
            )
            for family
            in results
        )

        report[
            f"role_gated_{role}_"
            "atoms_admitted"
        ] = sum(
            family[
                "mnexa_role_gated"
            ][
                "role_counts"
            ].get(
                role,
                0,
            )
            for family
            in results
        )

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
            "tasks_008.json"
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
        run_experiment_008(
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
        "span_only_task_passes",
        "role_gated_task_passes",
        "span_only_complete_lessons",
        "role_gated_complete_lessons",
        "span_only_ineligible_atoms_admitted",
        "role_gated_ineligible_atoms_admitted",
        "mean_span_only_authoritative_recall",
        "mean_role_gated_authoritative_recall",
        "mean_span_only_authoritative_precision",
        "mean_role_gated_authoritative_precision",
        "role_challenges",
        "role_challenge_rejections",
        "role_gate_rejections",
        "span_only_transfer_nonknowledge_leaks",
        "role_gated_transfer_nonknowledge_leaks",
        "span_only_unsupported_claims_admitted",
        "role_gated_unsupported_claims_admitted",
        "all_source_evidence_equal",
        "all_atom_proposals_equal",
    )

    summary = {
        key: report[key]
        for key in keys
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
