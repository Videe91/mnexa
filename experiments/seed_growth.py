from __future__ import annotations

import argparse
import json
import os
import re
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any

from mnexa_seed import MnexaSeed
from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


# ---------------------------------------------------------------------
# Deterministic grader
# ---------------------------------------------------------------------


def _as_group(value):
    if isinstance(value, str):
        return (value,)

    return tuple(value)


def grade_text(
    text: str,
    grader: dict[str, Any],
) -> bool:

    low = text.lower()

    # -------------------------------------------------------------
    # V1 literal phrase groups
    # Kept for backward compatibility with Seed Growth 001.
    # -------------------------------------------------------------

    for alternatives in grader.get(
        "all_of",
        [],
    ):
        matched = any(
            str(phrase).lower() in low
            for phrase in _as_group(
                alternatives
            )
        )

        if not matched:
            return False

    for forbidden in grader.get(
        "none_of",
        [],
    ):
        if str(forbidden).lower() in low:
            return False

    # -------------------------------------------------------------
    # V2 deterministic regex groups
    #
    # This remains deterministic.
    # We are NOT using another LLM as a judge.
    # -------------------------------------------------------------

    for alternatives in grader.get(
        "all_regex",
        [],
    ):
        matched = any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
            is not None

            for pattern in _as_group(
                alternatives
            )
        )

        if not matched:
            return False

    for forbidden in grader.get(
        "none_regex",
        [],
    ):
        if re.search(
            forbidden,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            return False

    return True


# ---------------------------------------------------------------------
# Reasoning seat
# ---------------------------------------------------------------------


def make_reasoner(
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
Do not invent a runbook rule that is not present in the task or accumulated experience.
""".strip()

        return (
            model
            .generate(prompt)
            .text
            .strip()
        )

    return reasoner


# ---------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------


def build_consolidation_prompt(
    evidence: str,
) -> str:

    return f"""
You are performing lossless operational consolidation.

Study this decision and its observed outcome:

--- EVIDENCE START ---
{evidence}
--- EVIDENCE END ---

Extract a reusable lesson for future problems from the
same underlying class.

The lesson may compress wording.

It MUST NOT compress away decision-critical constraints.

Preserve exactly when present:

- numbers;
- timings;
- units;
- exact counts;
- words such as exactly, only, every, each, before, after;
- negations and prohibitions;
- identifiers and error codes;
- header names;
- protocol values;
- retry limits;
- ordering requirements;
- scope restrictions;
- required and forbidden actions.

Do not generalize away a precise rule into vague advice such as:

- check documentation;
- follow protocol;
- validate appropriately;
- retry if necessary;
- use the appropriate settings.

Do not invent constraints that are absent from the evidence.

Do not infer that an observed outcome proves causality.

Do not include private reasoning.

Return only this structure:

TRIGGER:
<the reusable condition>

REUSABLE RULE:
<the operational rule>

CRITICAL CONSTRAINTS:
- <constraint>
- <constraint>
- ...

If the evidence contains a decision-critical word such as
"exactly", "every", "each", "only", "must", "never",
"do not", a number, a unit, an identifier, or a header name,
preserve that information rather than weakening it.
""".strip()


def make_consolidator(
    model,
):

    def consolidator(
        evidence: str,
    ) -> str:

        prompt = (
            build_consolidation_prompt(
                evidence
            )
        )

        return (
            model
            .generate(prompt)
            .text
            .strip()
        )

    return consolidator


# ---------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------


def _condition_result(
    decision,
    grader,
):
    return {
        "passed": grade_text(
            decision.text,
            grader,
        ),
        "decision": (
            decision.text
        ),
        "watermark": (
            decision.watermark
        ),
        "memory_segments": list(
            decision.memory_segments
        ),
    }


# ---------------------------------------------------------------------
# One experience -> transfer family
# ---------------------------------------------------------------------


def run_family(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
    transfer_grader=None,
):
    transfer_grader = (
        transfer_grader
        or family[
            "transfer"
        ]["grader"]
    )

    family_id = family["id"]

    entities = tuple(
        family.get(
            "entities",
            (),
        )
    )

    family_dir = (
        Path(work_dir) / family_id
    )

    family_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    reasoner = make_reasoner(
        model
    )

    consolidator = make_consolidator(
        model
    )

    # ================================================================
    # CONDITION B0:
    # Frozen reasoning model, no persistent memory.
    # ================================================================

    baseline_db = (
        family_dir / "baseline.sqlite3"
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
                reasoner,
            )
        )

        baseline_result = (
            _condition_result(
                baseline_decision,
                transfer_grader,
            )
        )

    finally:
        baseline.close()

    # ================================================================
    # CONDITION MNEXA:
    #
    # experience
    #   -> outcome
    #   -> consolidation
    #   -> unseen related transfer task
    # ================================================================

    mnexa_db = (
        family_dir / "mnexa.sqlite3"
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
        # 1. EXPERIENCE
        # ------------------------------------------------------------

        experience_decision = (
            mnexa.decide(
                family[
                    "experience"
                ]["prompt"],
                entities,
                reasoner,
            )
        )

        experience_passed = (
            grade_text(
                experience_decision.text,
                family[
                    "experience"
                ]["grader"],
            )
        )

        # ------------------------------------------------------------
        # 2. REALITY / EVALUATOR FEEDBACK
        # ------------------------------------------------------------

        outcome_text = (
            "EVALUATION: "
            + (
                "PASS"
                if experience_passed
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
                    experience_passed
                ),
            )
        )

        # ------------------------------------------------------------
        # 3. CONSOLIDATE EXPERIENCE
        # ------------------------------------------------------------

        lesson = (
            mnexa.consolidate(
                experience_decision.record_id,
                consolidator,
            )
        )

        # ------------------------------------------------------------
        # 4. TRANSFER TASK
        #
        # The model does NOT receive the transfer answer.
        # It only receives whatever MNEXA recalls.
        # ------------------------------------------------------------

        transfer_decision = (
            mnexa.decide(
                family[
                    "transfer"
                ]["prompt"],
                entities,
                reasoner,
            )
        )

        mnexa_result = (
            _condition_result(
                transfer_decision,
                transfer_grader,
            )
        )

        mnexa_result[
            "lesson"
        ] = lesson.text

        mnexa_result[
            "lesson_id"
        ] = lesson.object_id

        mnexa_result[
            "outcome_id"
        ] = outcome.object_id

        experience_result = {
            "passed": (
                experience_passed
            ),
            "decision": (
                experience_decision.text
            ),
            "outcome": (
                outcome_text
            ),
        }

    finally:
        mnexa.close()

    # ================================================================
    # Family report
    # ================================================================

    return {
        "family_id": (
            family_id
        ),
        "experience": (
            experience_result
        ),
        "baseline": (
            baseline_result
        ),
        "mnexa": (
            mnexa_result
        ),
        "delta": (
            int(
                mnexa_result[
                    "passed"
                ]
            )
            - int(
                baseline_result[
                    "passed"
                ]
            )
        ),
    }


# ---------------------------------------------------------------------
# Whole exploratory experiment
# ---------------------------------------------------------------------


def run_experiment(
    *,
    tasks_path: Path,
    results_dir: Path,
    model,
    embedder,
    meter,
    experiment_name="seed-growth-001",
    grader_overrides=None,
    grader_profile_name=None,
):
    payload = json.loads(
        Path(
            tasks_path
        ).read_text()
    )

    families = payload[
        "families"
    ]

    run_id = (
        datetime
        .now(timezone.utc)
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    work_dir = (
        results_dir / run_id / "state"
    )

    work_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = [
        run_family(
            family=family,
            work_dir=work_dir,
            model=model,
            embedder=embedder,
            meter=meter,
            transfer_grader=(
                grader_overrides.get(
                    family["id"]
                )
                if grader_overrides
                else None
            ),
        )
        for family in families
    ]

    baseline_passes = sum(
        int(
            item[
                "baseline"
            ]["passed"]
        )
        for item in results
    )

    mnexa_passes = sum(
        int(
            item[
                "mnexa"
            ]["passed"]
        )
        for item in results
    )

    report = {
        "experiment": experiment_name,
        "classification": (
            "exploratory"
        ),
        "run_id": (
            run_id
        ),
        "grader_profile": (
            grader_profile_name
            or "embedded-original"
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
        "baseline_passes": (
            baseline_passes
        ),
        "mnexa_passes": (
            mnexa_passes
        ),
        "net_improvement": (
            mnexa_passes - baseline_passes
        ),
        "families": (
            results
        ),
    }

    output = (
        results_dir / run_id / "result.json"
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


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------


def main():
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks.json"
        ),
    )

    parser.add_argument(
        "--results",
        default=(
            "experiments/"
            "results"
        ),
    )

    parser.add_argument(
        "--experiment",
        default="seed-growth-001",
    )

    parser.add_argument(
        "--grader-profile",
        default=None,
    )

    args = parser.parse_args()

    model_name = os.environ.get(
        "MNEXA_MODEL"
    )

    if not model_name:
        raise SystemExit(
            "Set MNEXA_MODEL to the exact model "
            "identifier used for this experiment."
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

    meter = WordMeter()

    grader_overrides = None
    grader_profile_name = None

    if args.grader_profile:
        profile = json.loads(
            Path(
                args.grader_profile
            ).read_text()
        )

        grader_overrides = profile[
            "graders"
        ]

        grader_profile_name = profile[
            "profile"
        ]

    report, output = (
        run_experiment(
            tasks_path=Path(
                args.tasks
            ),
            results_dir=Path(
                args.results
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            experiment_name=args.experiment,
            grader_overrides=grader_overrides,
            grader_profile_name=(
                grader_profile_name
            ),
        )
    )

    print(
        json.dumps(
            {
                "experiment": (
                    report[
                        "experiment"
                    ]
                ),
                "baseline_passes": (
                    report[
                        "baseline_passes"
                    ]
                ),
                "mnexa_passes": (
                    report[
                        "mnexa_passes"
                    ]
                ),
                "net_improvement": (
                    report[
                        "net_improvement"
                    ]
                ),
                "result": (
                    str(output)
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
