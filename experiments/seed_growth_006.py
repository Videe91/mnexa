from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from mnexa_seed import MnexaSeed

from experiments.seed_growth import (
    grade_text,
)

from experiments.seed_growth_004 import (
    make_fidelity_reasoner,
)

from experiments.seed_growth_005 import (
    make_evidence_disciplined_consolidator,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


CLAIM_ANCESTRY_INSTRUCTION = """
CLAIM ANCESTRY CONSOLIDATION

You are converting authoritative evidence into
candidate reusable claims.

This experiment uses a CLOSED-WORLD admission rule.

Every durable claim must have explicit ancestry.

Rules:

1. The failed DECISION records what was attempted.
   It is not evidence that the attempted proposition is true.

2. The authoritative correction has already been decomposed
   into atomic evidence items E1, E2, E3, ...

3. Propose at most one claim for each evidence atom.

4. Every proposed claim must cite exactly one evidence ID.

5. COPY THE EVIDENCE ATOM TEXT EXACTLY.
   Do not paraphrase it.
   Do not expand it.
   Do not combine it with another proposition.

6. Do not create a trigger, explanation, implication,
   causal statement, generalization, or recommendation unless
   that exact proposition exists as an evidence atom.

7. If a proposition appears only in the failed decision,
   do not promote it.

8. If uncertain, omit the claim.

9. Do not include private reasoning.

Return JSON only:

{
  "claims": [
    {
      "text": "<exact evidence atom text>",
      "evidence_ids": ["E1"]
    }
  ]
}
""".strip()


def contains_any_regex(
    text: str,
    patterns,
) -> bool:

    return any(
        re.search(
            pattern,
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )
        is not None

        for pattern
        in patterns
    )


def normalize_claim_text(
    text: str,
) -> str:

    text = (
        text
        .strip()
        .lower()
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"[.!?]+$",
        "",
        text,
    )

    return text.strip()


def _strip_json_fence(
    text: str,
) -> str:

    text = text.strip()

    if text.startswith(
        "```"
    ):
        lines = (
            text
            .splitlines()
        )

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1]
            .strip()
            .startswith("```")
        ):
            lines = lines[:-1]

        text = "\n".join(
            lines
        ).strip()

    return text


def parse_claim_proposal(
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
            "Claim proposal must be "
            "a JSON object."
        )

    claims = payload.get(
        "claims"
    )

    if not isinstance(
        claims,
        list,
    ):
        raise ValueError(
            "Claim proposal must contain "
            "a claims list."
        )

    return payload


def admit_claims(
    proposal,
    evidence_atoms,
):
    """
    v0 closed-world admission.

    This intentionally does NOT attempt semantic entailment.

    The model may propose claims, but admission succeeds only
    when:

    - exactly one valid evidence parent is cited;
    - the claim text equals the canonical evidence atom
      after minimal normalization;
    - that evidence atom has not already been admitted.

    This is restrictive by design for Seed Growth 006.
    """

    by_id = {
        atom["id"]: atom
        for atom
        in evidence_atoms
    }

    admitted = []
    rejected = []

    admitted_evidence = set()

    claims = proposal.get(
        "claims",
        [],
    )

    for index, claim in enumerate(
        claims
    ):
        if not isinstance(
            claim,
            dict,
        ):
            rejected.append(
                {
                    "index": index,
                    "claim": claim,
                    "reason": (
                        "claim_not_object"
                    ),
                }
            )
            continue

        text = claim.get(
            "text"
        )

        evidence_ids = claim.get(
            "evidence_ids"
        )

        if (
            not isinstance(
                text,
                str,
            )
            or not text.strip()
        ):
            rejected.append(
                {
                    "index": index,
                    "claim": claim,
                    "reason": (
                        "missing_claim_text"
                    ),
                }
            )
            continue

        if (
            not isinstance(
                evidence_ids,
                list,
            )
            or len(
                evidence_ids
            ) != 1
        ):
            rejected.append(
                {
                    "index": index,
                    "claim": claim,
                    "reason": (
                        "non_atomic_ancestry"
                    ),
                }
            )
            continue

        evidence_id = (
            evidence_ids[0]
        )

        if evidence_id not in by_id:
            rejected.append(
                {
                    "index": index,
                    "claim": claim,
                    "reason": (
                        "unknown_evidence"
                    ),
                }
            )
            continue

        if (
            evidence_id
            in admitted_evidence
        ):
            rejected.append(
                {
                    "index": index,
                    "claim": claim,
                    "reason": (
                        "duplicate_evidence"
                    ),
                }
            )
            continue

        canonical = by_id[
            evidence_id
        ]["text"]

        if (
            normalize_claim_text(
                text
            )
            !=
            normalize_claim_text(
                canonical
            )
        ):
            rejected.append(
                {
                    "index": index,
                    "claim": claim,
                    "reason": (
                        "claim_not_equal_to_"
                        "cited_evidence"
                    ),
                }
            )
            continue

        admitted.append(
            {
                "text": (
                    canonical
                ),

                "evidence_ids": [
                    evidence_id
                ],
            }
        )

        admitted_evidence.add(
            evidence_id
        )

    total = len(
        evidence_atoms
    )

    ancestry_coverage = (
        len(
            admitted_evidence
        )
        / total

        if total
        else 1.0
    )

    return {
        "admitted": (
            admitted
        ),

        "rejected": (
            rejected
        ),

        "ancestry_coverage": (
            ancestry_coverage
        ),

        "admitted_evidence_ids": (
            sorted(
                admitted_evidence
            )
        ),

        # By construction, anything admitted has passed
        # the closed-world equality gate.
        "unsupported_claims_admitted": 0,
    }


def build_claim_ancestry_prompt(
    *,
    evidence: str,
    family,
) -> str:

    evidence_lines = "\n".join(
        (
            f"{atom['id']}: "
            f"{atom['text']}"
        )

        for atom
        in family[
            "evidence_atoms"
        ]
    )

    return f"""
{CLAIM_ANCESTRY_INSTRUCTION}

--- RAW HISTORICAL EVIDENCE START ---
{evidence}
--- RAW HISTORICAL EVIDENCE END ---

AUTHORITATIVE EVIDENCE ATOMS:

{evidence_lines}

The evidence atoms are a deterministic decomposition of the
authoritative correction above. They add no new facts.

Return JSON only.
""".strip()


def render_admitted_claims(
    admitted,
) -> str:

    if not admitted:
        return (
            "SUPPORTED CLAIMS:\n"
            "(none admitted)"
        )

    lines = [
        "SUPPORTED CLAIMS:"
    ]

    for claim in admitted:
        evidence_id = (
            claim[
                "evidence_ids"
            ][0]
        )

        lines.append(
            f"- [{evidence_id}] "
            f"{claim['text']}"
        )

    return "\n".join(
        lines
    )


def make_claim_ancestry_consolidator(
    model,
    *,
    family,
    audit,
):
    def consolidator(
        evidence: str,
    ) -> str:

        prompt = (
            build_claim_ancestry_prompt(
                evidence=evidence,
                family=family,
            )
        )

        raw = (
            model
            .generate(prompt)
            .text
            .strip()
        )

        audit[
            "raw_model_proposal"
        ] = raw

        try:
            proposal = (
                parse_claim_proposal(
                    raw
                )
            )

        except Exception as exc:
            audit[
                "parse_error"
            ] = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            audit[
                "proposed_claim_count"
            ] = 0

            audit[
                "admitted_claim_count"
            ] = 0

            audit[
                "rejected_claim_count"
            ] = 0

            audit[
                "ancestry_coverage"
            ] = 0.0

            audit[
                "unsupported_claims_admitted"
            ] = 0

            return (
                "SUPPORTED CLAIMS:\n"
                "(none admitted)"
            )

        result = admit_claims(
            proposal,
            family[
                "evidence_atoms"
            ],
        )

        audit[
            "proposal"
        ] = proposal

        audit[
            "proposed_claim_count"
        ] = len(
            proposal[
                "claims"
            ]
        )

        audit[
            "admitted_claim_count"
        ] = len(
            result[
                "admitted"
            ]
        )

        audit[
            "rejected_claim_count"
        ] = len(
            result[
                "rejected"
            ]
        )

        audit[
            "rejected_claims"
        ] = result[
            "rejected"
        ]

        audit[
            "admitted_claims"
        ] = result[
            "admitted"
        ]

        audit[
            "ancestry_coverage"
        ] = result[
            "ancestry_coverage"
        ]

        audit[
            "unsupported_claims_admitted"
        ] = result[
            "unsupported_claims_admitted"
        ]

        audit[
            "admitted_evidence_ids"
        ] = result[
            "admitted_evidence_ids"
        ]

        return render_admitted_claims(
            result[
                "admitted"
            ]
        )

    return consolidator


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


def _score_text(
    text: str,
    family,
):

    correct = grade_text(
        text,
        family[
            "correct_grader"
        ],
    )

    contaminated = (
        contains_any_regex(
            text,
            family[
                "contamination_regex"
            ],
        )
    )

    return {
        "correct_knowledge": (
            correct
        ),

        "designated_contamination": (
            contaminated
        ),

        "task_success": (
            correct
            and not contaminated
        ),
    }


def _run_memory_condition(
    *,
    condition_name,
    family,
    family_dir,
    model,
    embedder,
    meter,
    consolidator_factory,
):
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

    audit = {}

    candidate_reasoner = (
        _controlled_candidate_reasoner(
            family[
                "candidate_decision"
            ]
        )
    )

    transfer_reasoner = (
        make_fidelity_reasoner(
            model
        )
    )

    try:
        # ------------------------------------------------------------
        # Historical failed decision
        # ------------------------------------------------------------

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

                candidate_reasoner,
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
                "Controlled candidate decision changed."
            )

        # ------------------------------------------------------------
        # Authoritative correction
        # ------------------------------------------------------------

        outcome_text = (
            "EVALUATION: FAIL.\n"
            "AUTHORITATIVE CORRECTION:\n"
            + family[
                "correction"
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

        # ------------------------------------------------------------
        # Consolidation treatment
        # ------------------------------------------------------------

        consolidator = (
            consolidator_factory(
                audit
            )
        )

        lesson = (
            mnexa.consolidate(
                experience_decision.record_id,
                consolidator,
            )
        )

        lesson_score = (
            _score_text(
                lesson.text,
                family,
            )
        )

        # ------------------------------------------------------------
        # Transfer
        # ------------------------------------------------------------

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

                transfer_reasoner,
            )
        )

        transfer_score = (
            _score_text(
                transfer.text,
                family,
            )
        )

        result = {
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

            "lesson_correct_knowledge": (
                lesson_score[
                    "correct_knowledge"
                ]
            ),

            "lesson_contaminated": (
                lesson_score[
                    "designated_contamination"
                ]
            ),

            "transfer_decision": (
                transfer.text
            ),

            "transfer_correct_knowledge": (
                transfer_score[
                    "correct_knowledge"
                ]
            ),

            "transfer_contaminated": (
                transfer_score[
                    "designated_contamination"
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
        }

        result.update(
            audit
        )

        return result

    finally:
        mnexa.close()


def run_family_006(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
):
    family_dir = (
        Path(work_dir)
        / family["id"]
    )

    family_dir.mkdir(
        parents=True,
        exist_ok=True,
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

    transfer_reasoner = (
        make_fidelity_reasoner(
            model
        )
    )

    try:
        baseline_decision = (
            baseline.decide(
                family[
                    "transfer"
                ]["prompt"],

                tuple(
                    family[
                        "entities"
                    ]
                ),

                transfer_reasoner,
            )
        )

        baseline_score = (
            _score_text(
                baseline_decision.text,
                family,
            )
        )

        baseline_result = {
            "decision": (
                baseline_decision.text
            ),

            "correct_knowledge": (
                baseline_score[
                    "correct_knowledge"
                ]
            ),

            "designated_contamination": (
                baseline_score[
                    "designated_contamination"
                ]
            ),

            "task_success": (
                baseline_score[
                    "task_success"
                ]
            ),
        }

    finally:
        baseline.close()

    # ================================================================
    # B — Seed 005 evidence-disciplined consolidation
    # ================================================================

    disciplined = (
        _run_memory_condition(
            condition_name=(
                "evidence_disciplined"
            ),

            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,

            consolidator_factory=(
                lambda audit:
                make_evidence_disciplined_consolidator(
                    model
                )
            ),
        )
    )

    # ================================================================
    # C — Claim ancestry + deterministic admission
    # ================================================================

    ancestry = (
        _run_memory_condition(
            condition_name=(
                "claim_ancestry"
            ),

            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,

            consolidator_factory=(
                lambda audit:
                make_claim_ancestry_consolidator(
                    model,
                    family=family,
                    audit=audit,
                )
            ),
        )
    )

    same_source_evidence = (
        disciplined[
            "source_evidence_sha256"
        ]
        ==
        ancestry[
            "source_evidence_sha256"
        ]
    )

    if not same_source_evidence:
        raise RuntimeError(
            "006 ablation invalid: "
            "B and C received different "
            "historical source evidence."
        )

    return {
        "family_id": (
            family["id"]
        ),

        "baseline": (
            baseline_result
        ),

        "mnexa_evidence_disciplined": (
            disciplined
        ),

        "mnexa_claim_ancestry": (
            ancestry
        ),

        "same_source_evidence": (
            same_source_evidence
        ),

        "task_lift_b_to_c": (
            int(
                ancestry[
                    "task_success"
                ]
            )
            -
            int(
                disciplined[
                    "task_success"
                ]
            )
        ),

        "contamination_delta_b_to_c": (
            int(
                ancestry[
                    "lesson_contaminated"
                ]
            )
            -
            int(
                disciplined[
                    "lesson_contaminated"
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


def run_experiment_006(
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
        run_family_006(
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

    ancestry_coverages = [
        family[
            "mnexa_claim_ancestry"
        ].get(
            "ancestry_coverage",
            0.0,
        )

        for family
        in results
    ]

    report = {
        "experiment": (
            "seed-growth-006"
        ),

        "classification": (
            "exploratory-fresh-"
            "claim-ancestry-ablation"
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

        "task_count": len(
            results
        ),

        "conditions": {
            "A": (
                "baseline_no_memory"
            ),

            "B": (
                "mnexa_evidence_disciplined_"
                "consolidation"
            ),

            "C": (
                "mnexa_claim_ancestry_"
                "closed_world_admission"
            ),
        },

        "baseline_task_passes": (
            _count(
                results,
                "baseline",
                "task_success",
            )
        ),

        "disciplined_task_passes": (
            _count(
                results,
                "mnexa_evidence_disciplined",
                "task_success",
            )
        ),

        "ancestry_task_passes": (
            _count(
                results,
                "mnexa_claim_ancestry",
                "task_success",
            )
        ),

        "disciplined_lessons_with_correct_knowledge": (
            _count(
                results,
                "mnexa_evidence_disciplined",
                "lesson_correct_knowledge",
            )
        ),

        "ancestry_lessons_with_correct_knowledge": (
            _count(
                results,
                "mnexa_claim_ancestry",
                "lesson_correct_knowledge",
            )
        ),

        "disciplined_contaminated_lessons": (
            _count(
                results,
                "mnexa_evidence_disciplined",
                "lesson_contaminated",
            )
        ),

        "ancestry_contaminated_lessons": (
            _count(
                results,
                "mnexa_claim_ancestry",
                "lesson_contaminated",
            )
        ),

        "disciplined_contaminated_transfer_decisions": (
            _count(
                results,
                "mnexa_evidence_disciplined",
                "transfer_contaminated",
            )
        ),

        "ancestry_contaminated_transfer_decisions": (
            _count(
                results,
                "mnexa_claim_ancestry",
                "transfer_contaminated",
            )
        ),

        "ancestry_proposed_claims": (
            _sum_metric(
                results,
                "mnexa_claim_ancestry",
                "proposed_claim_count",
            )
        ),

        "ancestry_admitted_claims": (
            _sum_metric(
                results,
                "mnexa_claim_ancestry",
                "admitted_claim_count",
            )
        ),

        "ancestry_rejected_claims": (
            _sum_metric(
                results,
                "mnexa_claim_ancestry",
                "rejected_claim_count",
            )
        ),

        "ancestry_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "mnexa_claim_ancestry",
                "unsupported_claims_admitted",
            )
        ),

        "mean_ancestry_coverage": (
            (
                sum(
                    ancestry_coverages
                )
                /
                len(
                    ancestry_coverages
                )
            )

            if ancestry_coverages
            else 0.0
        ),

        "full_ancestry_coverage_families": sum(
            int(
                coverage == 1.0
            )

            for coverage
            in ancestry_coverages
        ),

        "all_source_evidence_equal": all(
            family[
                "same_source_evidence"
            ]

            for family
            in results
        ),

        "claim_ancestry_instruction": (
            CLAIM_ANCESTRY_INSTRUCTION
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
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_006.json"
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
        run_experiment_006(
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
        "disciplined_task_passes",
        "ancestry_task_passes",
        "disciplined_lessons_with_correct_knowledge",
        "ancestry_lessons_with_correct_knowledge",
        "disciplined_contaminated_lessons",
        "ancestry_contaminated_lessons",
        "ancestry_proposed_claims",
        "ancestry_admitted_claims",
        "ancestry_rejected_claims",
        "ancestry_unsupported_claims_admitted",
        "mean_ancestry_coverage",
        "full_ancestry_coverage_families",
        "all_source_evidence_equal",
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
