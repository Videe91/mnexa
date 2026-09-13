from experiments.make_tasks_004 import build_taskset
from experiments.seed_growth_004 import (
    FIDELITY_INSTRUCTION,
    make_fidelity_reasoner,
    run_family_004,
)

from model_adapter import Generation


class FakeEmbedder:
    vocab = (
        "ax9",
        "token",
        "fresh",
        "reuse",
    )

    def embed(self, text):
        words = text.lower().split()

        return [
            float(
                sum(
                    token in word
                    for word in words
                )
            )
            for token in self.vocab
        ]


class WordMeter:
    name = "word-meter-v1"

    def count(self, text):
        return len(text.split())


class AblationModel:
    name = "ablation-test-model"

    def generate(self, prompt):
        low = prompt.lower()

        if (
            "lossless operational consolidation"
            in low
        ):
            text = """
TRIGGER:
AX9 occurs.

REUSABLE RULE:
Obtain a fresh session token and never reuse
the prior session token.

CRITICAL CONSTRAINTS:
- Obtain a fresh session token.
- Never reuse the prior session token.
""".strip()

        elif (
            "decision-fidelity requirement"
            in low
        ):
            text = (
                "Obtain a fresh session token. "
                "Never reuse the prior session token."
            )

        elif (
            "relevant accumulated experience"
            in low
            and "fresh session token"
            in low
        ):
            # Current reasoning seat:
            # operationally useful but drops explicit prohibition.
            text = "Obtain a fresh session token."

        else:
            text = "Consult the documentation."

        return Generation(
            text=text,
            input_tokens=None,
            output_tokens=None,
            response_id=None,
        )


def test_fidelity_reasoner_contains_only_targeted_instruction():
    model = AblationModel()

    reasoner = make_fidelity_reasoner(
        model
    )

    result = reasoner(
        "AX9 occurred.",
        "CRITICAL CONSTRAINTS:\n"
        "- Never reuse the prior session token.",
    )

    assert (
        "never reuse"
        in result.lower()
    )

    assert (
        "decision-fidelity requirement"
        in FIDELITY_INSTRUCTION.lower()
    )


def test_three_way_ablation_separates_task_success_from_fidelity(
    tmp_path,
):
    family = {
        "id": "test-ax9",

        "entities": [
            "system:test",
            "code:ax9",
        ],

        "experience": {
            "prompt": (
                "Test system returns AX9 "
                "during operation A."
            ),

            "feedback": (
                "AX9 rule: obtain a fresh session token "
                "and never reuse the prior session token."
            ),
        },

        "transfer": {
            "prompt": (
                "Test system returns AX9 "
                "during operation B."
            ),
        },

        "task_grader": {
            "all_regex": [
                [
                    r"\b(?:fresh|new)\s+session\s+token\b"
                ]
            ]
        },

        "fidelity_grader": {
            "all_regex": [
                [
                    r"\b(?:fresh|new)\s+session\s+token\b"
                ],
                [
                    (
                        r"(?:never|do\s+not|don.t)"
                        r".*\breuse\b"
                        r".*\b(?:prior|old)\s+session\s+token\b"
                    )
                ]
            ]
        },
    }

    result = run_family_004(
        family=family,
        work_dir=tmp_path,
        model=AblationModel(),
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    assert (
        result["baseline"]["task_success"]
        is False
    )

    # Current MNEXA uses memory successfully.
    assert (
        result["mnexa_current"]["task_success"]
        is True
    )

    # But current seat dropped explicit prohibition.
    assert (
        result[
            "mnexa_current"
        ]["constraint_fidelity"]
        is False
    )

    # Fidelity condition keeps both.
    assert (
        result[
            "mnexa_fidelity"
        ]["task_success"]
        is True
    )

    assert (
        result[
            "mnexa_fidelity"
        ]["constraint_fidelity"]
        is True
    )

    # Critical ablation invariant:
    # B and C saw exactly the same persistent memory.
    assert (
        result[
            "mnexa_current"
        ]["memory_segments"]
        ==
        result[
            "mnexa_fidelity"
        ]["memory_segments"]
    )


def test_004_contains_twenty_fresh_unique_families():
    payload = build_taskset()

    families = payload[
        "families"
    ]

    assert len(families) == 20

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

        assert family["task_grader"][
            "all_regex"
        ]

        assert family[
            "fidelity_grader"
        ]["all_regex"]


def test_every_004_rule_satisfies_both_frozen_graders():
    from experiments.seed_growth import (
        grade_text,
    )

    payload = build_taskset()

    for family in payload["families"]:

        feedback = family[
            "experience"
        ]["feedback"]

        assert grade_text(
            feedback,
            family["task_grader"],
        ), (
            family["id"],
            "task_success",
        )

        assert grade_text(
            feedback,
            family[
                "fidelity_grader"
            ],
        ), (
            family["id"],
            "constraint_fidelity",
        )
