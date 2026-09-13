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

from mnexa_seed import MnexaSeed

from experiments.seed_growth import (
    grade_text,
    make_consolidator,
    make_reasoner,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


FIDELITY_INSTRUCTION = """
DECISION-FIDELITY REQUIREMENT:

When accumulated MNEXA experience contains
CRITICAL CONSTRAINTS, preserve every
decision-critical constraint in the final answer.

In particular:

- explicitly preserve prohibitions such as
  "never", "do not", and "must not";
- preserve "only", "every", "each", "before",
  "after", and ordering requirements;
- preserve exact retry limits and counts;
- preserve numbers and units;
- preserve identifiers, protocol values,
  headers, tokens, and modes;
- do not silently replace an explicit prohibition
  with an implied positive action.

Example:

Memory:
"Use a fresh correlation ID.
Never reuse the prior correlation ID."

Insufficient:
"Use a fresh correlation ID."

Faithful:
"Use a fresh correlation ID and never reuse
the prior correlation ID."

Do not add constraints that are absent from memory.
Do not merely repeat irrelevant memory.
""".strip()


def make_fidelity_reasoner(
    model,
):
    def reasoner(
        task: str,
        memory_context: str,
    ) -> str:

        prompt = f"""
You are solving one operational task.

Task:
{task}

Relevant accumulated experience from MNEXA:
{memory_context if memory_context else "(none)"}

Give the action you would take.

Be concise and specific.

Do not invent a runbook rule that is not present
in the task or accumulated experience.

{FIDELITY_INSTRUCTION}
""".strip()

        return (
            model
            .generate(prompt)
            .text
            .strip()
        )

    return reasoner


def _score(
    decision,
    *,
    task_grader,
    fidelity_grader,
):
    return {
        "decision": (
            decision.text
        ),

        "task_success": grade_text(
            decision.text,
            task_grader,
        ),

        "constraint_fidelity": grade_text(
            decision.text,
            fidelity_grader,
        ),

        "watermark": (
            decision.watermark
        ),

        "memory_segments": list(
            decision.memory_segments
        ),
    }


def run_family_004(
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

    task_grader = family[
        "task_grader"
    ]

    fidelity_grader = family[
        "fidelity_grader"
    ]

    current_reasoner = (
        make_reasoner(model)
    )

    fidelity_reasoner = (
        make_fidelity_reasoner(
            model
        )
    )

    consolidator = (
        make_consolidator(model)
    )

    # ================================================================
    # A — BASELINE
    # Same model. No persistent memory.
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
                current_reasoner,
            )
        )

        baseline_result = _score(
            baseline_decision,
            task_grader=task_grader,
            fidelity_grader=(
                fidelity_grader
            ),
        )

    finally:
        baseline.close()

    # ================================================================
    # B/C — ONE SHARED MNEXA MEMORY STATE
    # ================================================================

    mnexa_db = (
        family_dir
        / "mnexa.sqlite3"
    )

    if mnexa_db.exists():
        mnexa_db.unlink()

    mnexa = MnexaSeed(
        mnexa_db,
        embedder=embedder,
        meter=meter,
    )

    try:
        # ------------------------------------------------------------
        # Experience
        # ------------------------------------------------------------

        experience_decision = (
            mnexa.decide(
                family[
                    "experience"
                ]["prompt"],
                entities,
                current_reasoner,
            )
        )

        experience_task_success = (
            grade_text(
                experience_decision.text,
                task_grader,
            )
        )

        outcome_text = (
            "EVALUATION: "
            + (
                "PASS"
                if experience_task_success
                else "FAIL"
            )
            + ". "
            + family[
                "experience"
            ]["feedback"]
        )

        outcome = (
            mnexa.observe_outcome(
                experience_decision.record_id,
                outcome_text,
                success=(
                    experience_task_success
                ),
            )
        )

        lesson = (
            mnexa.consolidate(
                experience_decision.record_id,
                consolidator,
            )
        )

        # ------------------------------------------------------------
        # B — CURRENT MNEXA
        # ------------------------------------------------------------

        current_decision = (
            mnexa.decide(
                family[
                    "transfer"
                ]["prompt"],
                entities,
                current_reasoner,
            )
        )

        current_result = _score(
            current_decision,
            task_grader=task_grader,
            fidelity_grader=(
                fidelity_grader
            ),
        )

        # ------------------------------------------------------------
        # C — SAME MNEXA MEMORY,
        #     FIDELITY INSTRUCTION ONLY
        #
        # ContextAssembled / DecisionMade from B are historical
        # evidence, but are not normal searchable memory candidates
        # in the current seed. Therefore the recalled persistent
        # memory should remain identical.
        # ------------------------------------------------------------

        fidelity_decision = (
            mnexa.decide(
                family[
                    "transfer"
                ]["prompt"],
                entities,
                fidelity_reasoner,
            )
        )

        fidelity_result = _score(
            fidelity_decision,
            task_grader=task_grader,
            fidelity_grader=(
                fidelity_grader
            ),
        )

        if (
            current_result[
                "memory_segments"
            ]
            !=
            fidelity_result[
                "memory_segments"
            ]
        ):
            raise RuntimeError(
                "004 ablation invalid: "
                "B and C did not receive identical "
                "persistent-memory segments."
            )

        experience_result = {
            "decision": (
                experience_decision.text
            ),

            "task_success": (
                experience_task_success
            ),

            "outcome": (
                outcome_text
            ),

            "outcome_id": (
                outcome.object_id
            ),

            "lesson": (
                lesson.text
            ),

            "lesson_id": (
                lesson.object_id
            ),
        }

    finally:
        mnexa.close()

    return {
        "family_id": (
            family["id"]
        ),

        "experience": (
            experience_result
        ),

        "baseline": (
            baseline_result
        ),

        "mnexa_current": (
            current_result
        ),

        "mnexa_fidelity": (
            fidelity_result
        ),

        "same_memory_b_c": (
            current_result[
                "memory_segments"
            ]
            ==
            fidelity_result[
                "memory_segments"
            ]
        ),

        "memory_lift": (
            int(
                current_result[
                    "task_success"
                ]
            )
            -
            int(
                baseline_result[
                    "task_success"
                ]
            )
        ),

        "fidelity_instruction_task_lift": (
            int(
                fidelity_result[
                    "task_success"
                ]
            )
            -
            int(
                current_result[
                    "task_success"
                ]
            )
        ),

        "fidelity_instruction_constraint_lift": (
            int(
                fidelity_result[
                    "constraint_fidelity"
                ]
            )
            -
            int(
                current_result[
                    "constraint_fidelity"
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
        for family in results
    )


def run_experiment_004(
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

    taskset_hash = (
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
        run_family_004(
            family=family,
            work_dir=state_dir,
            model=model,
            embedder=embedder,
            meter=meter,
        )
        for family
        in payload["families"]
    ]

    report = {
        "experiment": (
            "seed-growth-004"
        ),

        "classification": (
            "exploratory-fresh-ablation"
        ),

        "run_id": (
            run_id
        ),

        "taskset_sha256": (
            taskset_hash
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
                "baseline_no_persistent_memory"
            ),

            "B": (
                "current_mnexa"
            ),

            "C": (
                "same_mnexa_memory_plus_"
                "constraint_fidelity_instruction"
            ),
        },

        "baseline_task_passes": _count(
            results,
            "baseline",
            "task_success",
        ),

        "current_mnexa_task_passes": _count(
            results,
            "mnexa_current",
            "task_success",
        ),

        "fidelity_mnexa_task_passes": _count(
            results,
            "mnexa_fidelity",
            "task_success",
        ),

        "baseline_constraint_fidelity_passes": _count(
            results,
            "baseline",
            "constraint_fidelity",
        ),

        "current_mnexa_constraint_fidelity_passes": _count(
            results,
            "mnexa_current",
            "constraint_fidelity",
        ),

        "fidelity_mnexa_constraint_fidelity_passes": _count(
            results,
            "mnexa_fidelity",
            "constraint_fidelity",
        ),

        "all_b_c_memory_equal": all(
            family[
                "same_memory_b_c"
            ]
            for family
            in results
        ),

        "fidelity_instruction": (
            FIDELITY_INSTRUCTION
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
            "tasks_004.json"
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
        run_experiment_004(
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

    summary = {
        key: report[key]
        for key in (
            "experiment",
            "taskset_sha256",
            "baseline_task_passes",
            "current_mnexa_task_passes",
            "fidelity_mnexa_task_passes",
            "baseline_constraint_fidelity_passes",
            "current_mnexa_constraint_fidelity_passes",
            "fidelity_mnexa_constraint_fidelity_passes",
            "all_b_c_memory_equal",
        )
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
