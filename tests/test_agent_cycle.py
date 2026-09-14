from agent_cycle import (
    reason_over_context,
    render_model_input,
)

from mnexa_context import (
    ContextFrame,
)


def _frame():
    return ContextFrame.create(
        watermark=101,
        recall_intent=(
            "find retry policy"
        ),
        selected_memory_ids=(
            "m1",
            "m2",
        ),
        context_text=(
            "M1: retry exactly 5 times\n"
            "M2: retry at most 8 times"
        ),
    )


def test_different_reasoning_instructions_share_exact_context():
    frame = _frame()

    observed = []

    def reasoner(
        prompt,
    ):
        observed.append(
            prompt
        )

        return "decision"

    normal = (
        reason_over_context(
            context=frame,
            task=(
                "What is the retry rule?"
            ),
            reasoner=reasoner,
            reasoning_instruction=(
                "Answer normally."
            ),
        )
    )

    competing = (
        reason_over_context(
            context=frame,
            task=(
                "What is the retry rule?"
            ),
            reasoner=reasoner,
            reasoning_instruction=(
                "Treat memories as "
                "competing hypotheses."
            ),
        )
    )

    assert (
        normal
        .context_evidence_sha256
        ==
        competing
        .context_evidence_sha256
        ==
        frame.evidence_sha256
    )

    assert len(
        observed
    ) == 2


def test_reasoning_instruction_does_not_mutate_frame():
    frame = _frame()

    before = (
        frame.evidence_sha256
    )

    reason_over_context(
        context=frame,
        task="question",
        reasoning_instruction=(
            "Use a competing-hypothesis frame."
        ),
        reasoner=lambda prompt: (
            "answer"
        ),
    )

    assert (
        frame.evidence_sha256
        ==
        before
    )

    assert (
        frame.verify_integrity()
        is True
    )


def test_model_input_contains_context_and_instruction_separately():
    frame = _frame()

    rendered = (
        render_model_input(
            task="What rule applies?",
            context=frame,
            reasoning_instruction=(
                "Select one hypothesis."
            ),
        )
    )

    assert (
        "TASK:\n"
        "What rule applies?"
        in rendered
    )

    assert (
        "MNEXA CONTEXT:\n"
        in rendered
    )

    assert (
        frame.context_text
        in rendered
    )

    assert (
        "REASONING INSTRUCTION:\n"
        "Select one hypothesis."
        in rendered
    )


def test_reasoning_does_not_have_retrieval_callback():
    import inspect

    signature = inspect.signature(
        reason_over_context
    )

    prohibited = {
        "recall",
        "retriever",
        "recall_query",
        "watermark",
        "assemble",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_corrupted_context_is_rejected_before_model_call():
    import dataclasses
    import pytest

    frame = _frame()

    corrupted = dataclasses.replace(
        frame,
        context_text=(
            "tampered memory"
        ),
    )

    calls = []

    def reasoner(
        prompt,
    ):
        calls.append(
            prompt
        )

        return "decision"

    with pytest.raises(
        ValueError,
        match="integrity",
    ):
        reason_over_context(
            context=corrupted,
            task="question",
            reasoner=reasoner,
        )

    assert calls == []
