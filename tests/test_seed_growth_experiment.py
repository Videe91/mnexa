import json
from pathlib import Path

from experiments.seed_growth import (
    build_consolidation_prompt,
    grade_text,
    run_family,
)

from experiments.regrade_seed_growth import (
    regrade_result,
)


class FakeEmbedder:
    vocab = ("r17", "retry", "header", "nebula")

    def embed(self, text):
        words = text.lower().split()
        return [
            float(
                sum(token in word for word in words)
            )
            for token in self.vocab
        ]


class WordMeter:
    name = "word-meter-v1"

    def count(self, text):
        return len(text.split())


class DeterministicModel:
    name = "deterministic-test-model"

    def generate(self, prompt):
        from model_adapter import Generation

        low = prompt.lower()

        if "extract" in low and "reusable lesson" in low:
            text = (
                "For NebulaPay R17, wait 3 seconds, "
                "retry exactly once, and set "
                "X-Nebula-Replay: safe."
            )
        elif (
            "relevant accumulated experience" in low
            and "x-nebula-replay" in low
        ):
            text = (
                "Wait 3 seconds, retry exactly once, "
                "and set X-Nebula-Replay: safe."
            )
        else:
            text = "Retry with exponential backoff."

        return Generation(
            text=text,
            input_tokens=None,
            output_tokens=None,
            response_id=None,
        )


def test_grade_text_supports_alternative_required_phrases():
    grader = {
        "all_of": [
            ["3 seconds", "3s"],
            ["retry exactly once", "retry once"],
            ["x-nebula-replay"],
        ],
        "none_of": [
            "exponential",
        ],
    }

    assert grade_text(
        "Wait 3s, retry once, set X-Nebula-Replay: safe.",
        grader,
    )

    assert not grade_text(
        "Use exponential backoff.",
        grader,
    )


def test_one_family_can_improve_after_experience(tmp_path):
    family = {
        "id": "nebulapay-r17",
        "entities": [
            "system:nebulapay",
            "code:r17",
        ],
        "experience": {
            "prompt": (
                "NebulaPay returns R17 on capture. "
                "What should the operator do?"
            ),
            "feedback": (
                "Runbook: R17 means wait 3 seconds, "
                "retry exactly once, and set "
                "X-Nebula-Replay: safe."
            ),
            "grader": {
                "all_of": [
                    ["3 seconds", "3s"],
                    [
                        "retry exactly once",
                        "retry once",
                    ],
                    ["x-nebula-replay"],
                ],
                "none_of": [
                    "exponential",
                ],
            },
        },
        "transfer": {
            "prompt": (
                "NebulaPay returns R17 while creating "
                "a refund. What should the operator do?"
            ),
            "grader": {
                "all_of": [
                    ["3 seconds", "3s"],
                    [
                        "retry exactly once",
                        "retry once",
                    ],
                    ["x-nebula-replay"],
                ],
                "none_of": [
                    "exponential",
                ],
            },
        },
    }

    result = run_family(
        family=family,
        work_dir=tmp_path,
        model=DeterministicModel(),
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    assert result["baseline"]["passed"] is False
    assert result["mnexa"]["passed"] is True
    assert result["mnexa"]["memory_segments"]


def test_grade_text_supports_regex_groups():
    grader = {
        "all_regex": [
            [r"\b3\s*(?:seconds?|s)\b"],
            [r"\bretry\b.*\b(?:exactly\s+)?once\b"],
            [r"x-nebula-replay"],
        ],
        "none_regex": [
            r"retry\s+indefinitely",
        ],
    }

    assert grade_text(
        (
            "Wait for 3 seconds, then retry the refund "
            "request exactly once with X-Nebula-Replay: safe."
        ),
        grader,
    )


def test_regex_grader_still_rejects_missing_constraints():
    grader = {
        "all_regex": [
            [r"\bmultipart\b"],
            [r"\b16\s*(?:mib|mb)\b"],
            [r"\bsha-?256\b"],
            [r"\b(?:every|each|per)\s+part\b"],
        ],
    }

    assert not grade_text(
        (
            "Use multipart upload with 16 MiB parts "
            "and validate with SHA-256 digests."
        ),
        grader,
    )


def test_regrade_uses_saved_outputs_without_model_calls(tmp_path):
    original = {
        "experiment": "seed-growth-001",
        "run_id": "test-run",
        "model": "frozen-model",
        "families": [
            {
                "family_id": "example",
                "baseline": {
                    "passed": False,
                    "decision": "Consult documentation.",
                },
                "mnexa": {
                    "passed": False,
                    "decision": (
                        "Wait 3 seconds and retry the request "
                        "exactly once."
                    ),
                },
            }
        ],
    }

    profile = {
        "profile": "diagnostic-v2",
        "graders": {
            "example": {
                "all_regex": [
                    [r"\b3\s*seconds?\b"],
                    [r"\bretry\b.*\bexactly\s+once\b"],
                ]
            }
        },
    }

    original_path = tmp_path / "result.json"
    profile_path = tmp_path / "graders.json"

    original_path.write_text(
        json.dumps(original)
    )

    profile_path.write_text(
        json.dumps(profile)
    )

    report, _ = regrade_result(
        result_path=original_path,
        grader_profile_path=profile_path,
    )

    assert report["baseline_passes"] == 0
    assert report["mnexa_passes"] == 1
    assert report["net_improvement"] == 1


def test_consolidation_prompt_protects_exact_constraints():
    prompt = build_consolidation_prompt(
        (
            "HeliosStore E62 requires multipart upload "
            "with 16 MiB parts and SHA-256 for every part."
        )
    )

    low = prompt.lower()

    assert "numbers" in low
    assert "units" in low
    assert "negations" in low
    assert "every" in low
    assert "exactly" in low
    assert "do not generalize away" in low

    assert (
        "HeliosStore E62 requires multipart upload "
        "with 16 MiB parts and SHA-256 for every part."
    ) in prompt


def test_002r_accepts_each_of_the_six_parts():
    profile = json.loads(
        Path(
            "experiments/graders_002r.json"
        ).read_text()
    )

    grader = profile["graders"][
        "heliosstore-e62"
    ]

    answer = (
        "Use multipart upload with 16 MiB parts. "
        "Attach a SHA-256 digest for each of the six "
        "parts before retrying."
    )

    assert grade_text(
        answer,
        grader,
    )


def test_seed_growth_003_has_ten_fresh_families():
    payload = json.loads(
        Path(
            "experiments/tasks_003.json"
        ).read_text()
    )

    families = payload["families"]

    assert len(families) == 10

    ids = [
        family["id"]
        for family in families
    ]

    assert len(ids) == len(set(ids))

    for family in families:
        assert (
            family["experience"]["prompt"]
            != family["transfer"]["prompt"]
        )

        assert (
            "all_regex"
            in family["experience"]["grader"]
        )

        assert (
            "all_regex"
            in family["transfer"]["grader"]
        )

        code = next(
            entity.split(":", 1)[1]
            for entity in family["entities"]
            if entity.startswith("code:")
        )

        assert (
            code.lower()
            in family["experience"]["prompt"].lower()
        )

        assert (
            code.lower()
            in family["transfer"]["prompt"].lower()
        )


def test_seed_growth_003_feedback_satisfies_its_own_grader():
    payload = json.loads(
        Path(
            "experiments/tasks_003.json"
        ).read_text()
    )

    for family in payload["families"]:
        assert grade_text(
            family["experience"]["feedback"],
            family["experience"]["grader"],
        ), family["id"]
