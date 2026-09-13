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
    make_consolidator,
)

from experiments.seed_growth_004 import (
    make_fidelity_reasoner,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


EVIDENCE_DISCIPLINE_INSTRUCTION = """
EPISTEMICALLY DISCIPLINED CONSOLIDATION

The evidence contains two importantly different things:

1. DECISION
   This records what was attempted or believed.
   A failed decision is NOT evidence of truth.

2. OUTCOME
   When the outcome contains an
   AUTHORITATIVE CORRECTION, that correction is
   the evidence basis for reusable operational knowledge.

Your job is to learn from the evidence without converting
unsupported content from the failed decision into knowledge.

Rules:

- Treat the failed DECISION as historical evidence of what
  was attempted, not as a source of truth.

- Treat the AUTHORITATIVE CORRECTION as the grounding source
  for the reusable rule in this experiment.

- Promote a proposition only when it is supported by the
  authoritative correction.

- Do not preserve an assumption merely because it appeared
  in the failed decision.

- If a statement appears in the decision but is unsupported
  by the correction, omit it from the reusable lesson.

- If the correction contradicts the decision, prefer the
  correction for the reusable operational lesson.

- Preserve all decision-critical constraints that ARE
  supported by the correction: numbers, units, exact counts,
  ordering, identifiers, headers, modes, limits, and
  explicit prohibitions.

- Do not invent new facts.

- Do not infer causality beyond the supplied evidence.

- Do not include private reasoning.

Historical preservation of the failed decision is handled
elsewhere by MNEXA. The reusable lesson does not need to
repeat unsupported failed assumptions.
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


def build_evidence_disciplined_prompt(
    evidence: str,
) -> str:

    return f"""
{EVIDENCE_DISCIPLINE_INSTRUCTION}

--- EVIDENCE START ---
{evidence}
--- EVIDENCE END ---

Return only:

TRIGGER:
<condition that activates the supported rule>

REUSABLE RULE:
<only the reusable operational rule supported by
the authoritative correction>

CRITICAL CONSTRAINTS:
- <supported constraint>
- <supported constraint>
- ...

Do not preserve unsupported content from the failed decision.
""".strip()


def make_evidence_disciplined_consolidator(
    model,
):
    def consolidator(
        evidence: str,
    ) -> str:

        response = model.generate(
            build_evidence_disciplined_prompt(
                evidence
            )
        )

        return response.text.strip()

    return consolidator


def _score_text(
    text,
    family,
):
    correct = grade_text(
        text,
        family[
            "correct_grader"
        ],
    )

    contaminated = contains_any_regex(
        text,
        family[
            "contamination_regex"
        ],
    )

    return {
        "correct_knowledge": (
            correct
        ),

        "contaminated": (
            contaminated
        ),

        # For Seed Growth 005, success means:
        # learned required protocol AND did not
        # prescribe unsupported failed-decision content.
        "task_success": (
            correct
            and not contaminated
        ),
    }


def _source_evidence_text(
    candidate_decision: str,
    outcome_text: str,
):
    # Must match the construction currently used
    # inside MnexaSeed.consolidate().
    return (
        "DECISION: "
        + candidate_decision
        + "\n"
        + "OUTCOME: "
        + outcome_text
    )


def _sha256_text(
    text: str,
):
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
    """
    Experiment fixture.

    We intentionally control the failed historical decision
    so Conditions B and C receive exactly the same source
    evidence.

    The experiment is testing consolidation, not whether the
    model happens to hallucinate a particular wrong action.
    """

    def reasoner(
        task: str,
        context: str,
    ) -> str:
        return candidate_decision

    return reasoner


def _run_memory_condition(
    *,
    condition_name,
    family,
    family_dir,
    model,
    embedder,
    meter,
    consolidator,
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

    entities = tuple(
        family["entities"]
    )

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
        # 1. Controlled failed decision
        # ------------------------------------------------------------

        experience_decision = (
            mnexa.decide(
                family[
                    "experience"
                ]["prompt"],
                entities,
                candidate_reasoner,
            )
        )

        if (
            experience_decision.text
            != family[
                "candidate_decision"
            ]
        ):
            raise RuntimeError(
                "Controlled candidate decision changed."
            )

        # ------------------------------------------------------------
        # 2. Authoritative correction
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
        # 3. Consolidation under the condition being tested
        # ------------------------------------------------------------

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
        # 4. Unseen transfer
        #
        # Both B and C use the same fidelity-preserving reasoning seat.
        # Only the consolidation policy differs.
        # ------------------------------------------------------------

        transfer = (
            mnexa.decide(
                family[
                    "transfer"
                ]["prompt"],
                entities,
                transfer_reasoner,
            )
        )

        transfer_score = (
            _score_text(
                transfer.text,
                family,
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

            "lesson_correct_knowledge": (
                lesson_score[
                    "correct_knowledge"
                ]
            ),

            "lesson_contaminated": (
                lesson_score[
                    "contaminated"
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
                    "contaminated"
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

    finally:
        mnexa.close()


def run_family_005(
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

    entities = tuple(
        family["entities"]
    )

    transfer_reasoner = (
        make_fidelity_reasoner(
            model
        )
    )

    # ================================================================
    # A — NO MEMORY BASELINE
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
        baseline_decision = (
            baseline.decide(
                family[
                    "transfer"
                ]["prompt"],
                entities,
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

            "contaminated": (
                baseline_score[
                    "contaminated"
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
    # B — CURRENT LOSSLESS CONSOLIDATION
    # ================================================================

    current = (
        _run_memory_condition(
            condition_name=(
                "current"
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            consolidator=(
                make_consolidator(
                    model
                )
            ),
        )
    )

    # ================================================================
    # C — EVIDENCE-DISCIPLINED CONSOLIDATION
    # ================================================================

    disciplined = (
        _run_memory_condition(
            condition_name=(
                "disciplined"
            ),
            family=family,
            family_dir=family_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            consolidator=(
                make_evidence_disciplined_consolidator(
                    model
                )
            ),
        )
    )

    same_source_evidence = (
        current[
            "source_evidence_sha256"
        ]
        ==
        disciplined[
            "source_evidence_sha256"
        ]
    )

    if not same_source_evidence:
        raise RuntimeError(
            "005 ablation invalid: "
            "B and C received different source evidence."
        )

    return {
        "family_id": (
            family["id"]
        ),

        "baseline": (
            baseline_result
        ),

        "mnexa_current_consolidation": (
            current
        ),

        "mnexa_disciplined_consolidation": (
            disciplined
        ),

        "same_source_evidence": (
            same_source_evidence
        ),

        "current_to_disciplined_task_lift": (
            int(
                disciplined[
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

        "current_to_disciplined_lesson_contamination_delta": (
            int(
                disciplined[
                    "lesson_contaminated"
                ]
            )
            -
            int(
                current[
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
            ][metric]
        )
        for family
        in results
    )


def run_experiment_005(
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
        run_family_005(
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
            "seed-growth-005"
        ),

        "classification": (
            "exploratory-fresh-"
            "consolidation-ablation"
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
                "mnexa_current_lossless_consolidation"
            ),

            "C": (
                "mnexa_evidence_disciplined_consolidation"
            ),
        },

        "baseline_task_passes": _count(
            results,
            "baseline",
            "task_success",
        ),

        "current_task_passes": _count(
            results,
            "mnexa_current_consolidation",
            "task_success",
        ),

        "disciplined_task_passes": _count(
            results,
            "mnexa_disciplined_consolidation",
            "task_success",
        ),

        "current_lessons_with_correct_knowledge": _count(
            results,
            "mnexa_current_consolidation",
            "lesson_correct_knowledge",
        ),

        "disciplined_lessons_with_correct_knowledge": _count(
            results,
            "mnexa_disciplined_consolidation",
            "lesson_correct_knowledge",
        ),

        "current_contaminated_lessons": _count(
            results,
            "mnexa_current_consolidation",
            "lesson_contaminated",
        ),

        "disciplined_contaminated_lessons": _count(
            results,
            "mnexa_disciplined_consolidation",
            "lesson_contaminated",
        ),

        "current_contaminated_transfer_decisions": _count(
            results,
            "mnexa_current_consolidation",
            "transfer_contaminated",
        ),

        "disciplined_contaminated_transfer_decisions": _count(
            results,
            "mnexa_disciplined_consolidation",
            "transfer_contaminated",
        ),

        "all_source_evidence_equal": all(
            family[
                "same_source_evidence"
            ]
            for family
            in results
        ),

        "evidence_discipline_instruction": (
            EVIDENCE_DISCIPLINE_INSTRUCTION
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
            "tasks_005.json"
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

    model = OpenAIResponsesModel(
        model_name
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
        run_experiment_005(
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
        "current_task_passes",
        "disciplined_task_passes",
        "current_lessons_with_correct_knowledge",
        "disciplined_lessons_with_correct_knowledge",
        "current_contaminated_lessons",
        "disciplined_contaminated_lessons",
        "current_contaminated_transfer_decisions",
        "disciplined_contaminated_transfer_decisions",
        "all_source_evidence_equal",
    )

    summary = {
        key: report[key]
        for key in keys
    }

    summary["result"] = str(
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
