from __future__ import annotations

import argparse
import json

from pathlib import Path

from experiments.seed_growth import (
    grade_text,
)


def regrade_result(
    *,
    result_path: Path,
    grader_profile_path: Path,
    output_path: Path | None = None,
):

    result_path = Path(
        result_path
    )

    grader_profile_path = Path(
        grader_profile_path
    )

    source = json.loads(
        result_path.read_text()
    )

    profile = json.loads(
        grader_profile_path.read_text()
    )

    graders = profile[
        "graders"
    ]

    families = []

    baseline_passes = 0
    mnexa_passes = 0

    for family in source[
        "families"
    ]:
        family_id = family[
            "family_id"
        ]

        if family_id not in graders:
            raise KeyError(
                f"No diagnostic grader for {family_id}"
            )

        grader = graders[
            family_id
        ]

        baseline_passed = grade_text(
            family[
                "baseline"
            ]["decision"],
            grader,
        )

        mnexa_passed = grade_text(
            family[
                "mnexa"
            ]["decision"],
            grader,
        )

        baseline_passes += int(
            baseline_passed
        )

        mnexa_passes += int(
            mnexa_passed
        )

        families.append(
            {
                "family_id": family_id,

                "original_baseline_passed": (
                    family[
                        "baseline"
                    ]["passed"]
                ),

                "original_mnexa_passed": (
                    family[
                        "mnexa"
                    ]["passed"]
                ),

                "regraded_baseline_passed": (
                    baseline_passed
                ),

                "regraded_mnexa_passed": (
                    mnexa_passed
                ),

                "baseline_decision": (
                    family[
                        "baseline"
                    ]["decision"]
                ),

                "mnexa_decision": (
                    family[
                        "mnexa"
                    ]["decision"]
                ),
            }
        )

    report = {
        "experiment": (
            "seed-growth-001R"
        ),

        "classification": (
            "post-hoc-diagnostic-regrade"
        ),

        "source_experiment": (
            source.get(
                "experiment"
            )
        ),

        "source_run_id": (
            source.get(
                "run_id"
            )
        ),

        "source_model": (
            source.get(
                "model"
            )
        ),

        "grader_profile": (
            profile[
                "profile"
            ]
        ),

        "baseline_passes": (
            baseline_passes
        ),

        "mnexa_passes": (
            mnexa_passes
        ),

        "net_improvement": (
            mnexa_passes
            - baseline_passes
        ),

        "families": families,

        "scientific_warning": (
            "This is a post-hoc diagnostic regrade. "
            "It does not replace or rewrite the original "
            "Seed Growth 001 score."
        ),
    }

    if output_path is None:
        output_path = (
            result_path.parent
            / "regrade-001R.json"
        )

    output_path = Path(
        output_path
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n"
    )

    return (
        report,
        output_path,
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--result",
        required=True,
    )

    parser.add_argument(
        "--graders",
        default=(
            "experiments/"
            "graders_001r.json"
        ),
    )

    parser.add_argument(
        "--output",
        default=None,
    )

    args = parser.parse_args()

    report, output = regrade_result(
        result_path=Path(
            args.result
        ),

        grader_profile_path=Path(
            args.graders
        ),

        output_path=(
            Path(args.output)
            if args.output
            else None
        ),
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

                "result": str(
                    output
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
