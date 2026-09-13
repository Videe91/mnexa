from experiments.make_tasks_005 import build_taskset

from experiments.seed_growth_005 import (
    EVIDENCE_DISCIPLINE_INSTRUCTION,
    build_evidence_disciplined_prompt,
    contains_any_regex,
    run_family_005,
)

from model_adapter import Generation


class FakeEmbedder:
    vocab = (
        "ax9",
        "lease",
        "restart",
        "recover",
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


class ContaminationModel:
    """
    Deterministic test model.

    Current consolidation carries an unsupported
    failed-decision assumption forward.

    Evidence-disciplined consolidation does not.
    """

    name = "contamination-test-model"

    def generate(self, prompt):
        low = prompt.lower()

        if (
            "epistemically disciplined consolidation"
            in low
        ):
            text = """
TRIGGER:
AX9 occurs.

REUSABLE RULE:
Refresh the recovery lease, wait 4 seconds,
retry exactly once, and include
X-Test-Recover: blue.

CRITICAL CONSTRAINTS:
- Refresh the recovery lease.
- Wait 4 seconds.
- Retry exactly once.
- Include X-Test-Recover: blue.
""".strip()

        elif (
            "lossless operational consolidation"
            in low
        ):
            text = """
TRIGGER:
AX9 occurs.

REUSABLE RULE:
Restart the service, then refresh the recovery lease,
wait 4 seconds, retry exactly once, and include
X-Test-Recover: blue.

CRITICAL CONSTRAINTS:
- Restart the service.
- Refresh the recovery lease.
- Wait 4 seconds.
- Retry exactly once.
- Include X-Test-Recover: blue.
""".strip()

        elif (
            "decision-fidelity requirement"
            in low
            and "x-test-recover" in low
        ):
            if "restart the service" in low:
                text = (
                    "Restart the service. "
                    "Refresh the recovery lease, wait 4 seconds, "
                    "retry exactly once, and include "
                    "X-Test-Recover: blue."
                )
            else:
                text = (
                    "Refresh the recovery lease, wait 4 seconds, "
                    "retry exactly once, and include "
                    "X-Test-Recover: blue."
                )

        else:
            text = "Consult documentation."

        return Generation(
            text=text,
            input_tokens=None,
            output_tokens=None,
            response_id=None,
        )


def _test_family():
    return {
        "id": "test-ax9",

        "entities": [
            "system:test",
            "code:ax9",
        ],

        "experience": {
            "prompt": (
                "TestSystem returns AX9 "
                "during operation A."
            ),
        },

        "transfer": {
            "prompt": (
                "TestSystem returns AX9 "
                "during operation B."
            ),
        },

        "candidate_decision": (
            "Restart the service and then retry."
        ),

        "correction": (
            "AX9 requires refreshing the recovery lease, "
            "waiting 4 seconds, retrying exactly once, "
            "and including X-Test-Recover: blue."
        ),

        "correct_grader": {
            "all_regex": [
                [r"refresh.*recovery\s+lease"],
                [r"\b4\s*seconds?\b"],
                [r"retry.*exactly\s+once"],
                [r"x-test-recover.*blue"],
            ]
        },

        "contamination_regex": [
            r"restart.*service",
        ],
    }


def test_evidence_prompt_marks_failed_decision_as_untrusted():
    prompt = build_evidence_disciplined_prompt(
        "DECISION: Restart the service.\n"
        "OUTCOME: AUTHORITATIVE CORRECTION: "
        "Refresh the lease."
    )

    low = prompt.lower()

    assert "failed decision" in low
    assert "not evidence of truth" in low
    assert "authoritative correction" in low
    assert "unsupported" in low
    assert "do not preserve" in low


def test_contamination_matcher():
    assert contains_any_regex(
        "Restart the payment service.",
        [r"restart.*service"],
    )

    assert not contains_any_regex(
        "Refresh the recovery lease.",
        [r"restart.*service"],
    )


def test_disciplined_consolidation_removes_unsupported_decision_content(
    tmp_path,
):
    result = run_family_005(
        family=_test_family(),
        work_dir=tmp_path,
        model=ContaminationModel(),
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    current = result[
        "mnexa_current_consolidation"
    ]

    disciplined = result[
        "mnexa_disciplined_consolidation"
    ]

    # Same evidence entered both consolidators.
    assert result[
        "same_source_evidence"
    ] is True

    # Current consolidation learned the correction...
    assert current[
        "lesson_correct_knowledge"
    ] is True

    # ...but also carried unsupported failed-decision content.
    assert current[
        "lesson_contaminated"
    ] is True

    assert current[
        "transfer_contaminated"
    ] is True

    assert current[
        "task_success"
    ] is False

    # Disciplined consolidation learned the correction
    # without carrying the unsupported assumption.
    assert disciplined[
        "lesson_correct_knowledge"
    ] is True

    assert disciplined[
        "lesson_contaminated"
    ] is False

    assert disciplined[
        "transfer_contaminated"
    ] is False

    assert disciplined[
        "task_success"
    ] is True


def test_005_has_twenty_fresh_unique_families():
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

        assert family[
            "candidate_decision"
        ]

        assert family[
            "correction"
        ]

        assert family[
            "correct_grader"
        ]["all_regex"]

        assert family[
            "contamination_regex"
        ]


def test_005_fixture_integrity():
    from experiments.seed_growth import (
        grade_text,
    )

    payload = build_taskset()

    for family in payload[
        "families"
    ]:
        # Ground-truth correction must contain
        # all knowledge expected by the grader.
        assert grade_text(
            family["correction"],
            family["correct_grader"],
        ), family["id"]

        # Failed candidate must actually contain
        # at least one designated contamination.
        assert contains_any_regex(
            family["candidate_decision"],
            family["contamination_regex"],
        ), family["id"]

        # The authoritative correction itself
        # must not contain the contamination.
        assert not contains_any_regex(
            family["correction"],
            family["contamination_regex"],
        ), family["id"]


def test_instruction_declares_epistemic_asymmetry():
    low = (
        EVIDENCE_DISCIPLINE_INSTRUCTION
        .lower()
    )

    assert "decision" in low
    assert "correction" in low
    assert "unsupported" in low
    assert "truth" in low
