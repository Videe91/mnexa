import inspect
import json

import pytest

from agent_cycle import (
    reason_over_context,
)

from mnexa_context import (
    ContextFrame,
)

from mnexa_seed import (
    MnexaSeed,
)


class FakeEmbedder:
    vocab = (
        "429",
        "retry",
        "backoff",
        "payments",
    )

    def embed(
        self,
        text,
    ):
        words = (
            text
            .lower()
            .split()
        )

        return [
            float(
                sum(
                    token in word
                    for word
                    in words
                )
            )
            for token
            in self.vocab
        ]


class WordMeter:
    name = "word-meter-v1"

    def count(
        self,
        text,
    ):
        return len(
            text.split()
        )


def _seed(
    tmp_path,
):
    return MnexaSeed(
        tmp_path / "mnexa.db",
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )


def test_external_model_decision_enters_mnexa_after_frozen_context(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    entities = (
        "api:payments",
    )

    # Existing durable intelligence.
    m.learn(
        (
            "When an API returns 429, "
            "retry with exponential backoff."
        ),
        entities,
        (),
    )

    watermark_before_recall = (
        m.watermark()
    )

    # MNEXA'S JOB:
    # retrieve + assemble + freeze evidence.
    context = (
        m.prepare_context(
            "Payments API returns 429",
            entities,
        )
    )

    assert isinstance(
        context,
        ContextFrame,
    )

    assert (
        context.watermark
        ==
        watermark_before_recall
    )

    assert (
        context.verify_integrity()
        is True
    )

    assert (
        context
        .context_assembled_event_id
    )

    assert (
        "exponential backoff"
        in
        context.context_text.lower()
    )

    # AI'S JOB:
    # reasoning happens outside MNEXA.
    model_calls = []

    def external_reasoner(
        prompt,
    ):
        model_calls.append(
            prompt
        )

        return (
            "Retry with exponential backoff."
        )

    agent_decision = (
        reason_over_context(
            context=context,
            task=(
                "Payments API returns 429"
            ),
            reasoner=(
                external_reasoner
            ),
        )
    )

    assert len(
        model_calls
    ) == 1

    assert (
        agent_decision
        .context_evidence_sha256
        ==
        context.evidence_sha256
    )

    # MNEXA'S JOB AGAIN:
    # record what the external thinker decided.
    recorded = (
        m.record_external_decision(
            context=context,

            decision_text=(
                agent_decision.decision
            ),

            context_evidence_sha256=(
                agent_decision
                .context_evidence_sha256
            ),

            entities=entities,

            decision_kind=(
                "task_response"
            ),
        )
    )

    row = (
        m.db.execute(
            """
            SELECT *
            FROM commits
            WHERE object_id=?
            """,
            (
                recorded.record_id,
            ),
        )
        .fetchone()
    )

    assert (
        row["kind"]
        ==
        "DecisionMade"
    )

    refs = tuple(
        json.loads(
            row["refs"]
        )
    )

    assert refs == (
        context
        .context_assembled_event_id,
    )

    metadata = json.loads(
        row["metadata"]
    )

    assert (
        metadata[
            "decided_from"
        ]
        ==
        context
        .context_assembled_event_id
    )

    assert (
        metadata[
            "context_evidence_sha256"
        ]
        ==
        context.evidence_sha256
    )

    assert (
        metadata[
            "watermark"
        ]
        ==
        context.watermark
    )

    assert (
        metadata[
            "decision_kind"
        ]
        ==
        "task_response"
    )


def test_record_external_decision_rejects_wrong_context_hash(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    context = (
        m.prepare_context(
            "Payments API returns 429",
            (
                "api:payments",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="context evidence hash",
    ):
        m.record_external_decision(
            context=context,

            decision_text=(
                "Retry with backoff."
            ),

            context_evidence_sha256=(
                "wrong-hash"
            ),

            entities=(
                "api:payments",
            ),
        )


def test_record_external_decision_requires_recorded_context(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    context = (
        ContextFrame.create(
            watermark=0,

            recall_intent=(
                "Payments API returns 429"
            ),

            selected_memory_ids=(),

            context_text="",
        )
    )

    assert (
        context
        .context_assembled_event_id
        is None
    )

    with pytest.raises(
        ValueError,
        match="recorded ContextAssembled",
    ):
        m.record_external_decision(
            context=context,

            decision_text="answer",

            context_evidence_sha256=(
                context
                .evidence_sha256
            ),

            entities=(),
        )


def test_record_external_decision_rejects_corrupted_context(
    tmp_path,
):
    import dataclasses

    m = _seed(
        tmp_path
    )

    context = (
        m.prepare_context(
            "Payments API returns 429",
            (
                "api:payments",
            ),
        )
    )

    corrupted = (
        dataclasses.replace(
            context,
            context_text=(
                "tampered context"
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="integrity",
    ):
        m.record_external_decision(
            context=corrupted,

            decision_text="answer",

            context_evidence_sha256=(
                corrupted
                .evidence_sha256
            ),

            entities=(),
        )


def test_prepare_context_has_no_reasoner_or_model_parameter():
    signature = inspect.signature(
        MnexaSeed.prepare_context
    )

    prohibited = {
        "reasoner",
        "model",
        "reasoning_instruction",
        "system_prompt",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_record_external_decision_has_no_reasoner_parameter():
    signature = inspect.signature(
        MnexaSeed.record_external_decision
    )

    prohibited = {
        "reasoner",
        "model",
        "retriever",
        "recall",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_end_to_end_external_decision_learning_loop(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    entities = (
        "api:payments",
    )

    # 1. Prepare context (no prior memory exists)
    context1 = (
        m.prepare_context(
            "Payments API returns 429",
            entities,
        )
    )

    assert (
        context1.selected_memory_ids
        == ()
    )

    # 2. External AI reasons over empty context
    agent_decision1 = (
        reason_over_context(
            context=context1,
            task="Payments API returns 429",
            reasoner=lambda prompt: (
                "Retry immediately with zero delay."
            ),
        )
    )

    # 3. Record external decision
    decision1 = (
        m.record_external_decision(
            context=context1,
            decision_text=agent_decision1.decision,
            context_evidence_sha256=agent_decision1.context_evidence_sha256,
            entities=entities,
        )
    )

    # 4. Existing observe_outcome()
    m.observe_outcome(
        decision1.record_id,
        "Zero delay retry caused request flooding",
        success=False,
    )

    # 5. Existing consolidate()
    m.consolidate(
        decision1.record_id,
        lambda prompt: (
            "When Payments API returns 429, retry with exponential backoff."
        ),
    )

    # 6. Next encounter: prepare_context surfaces the consolidated lesson
    context2 = (
        m.prepare_context(
            "Payments API returns 429",
            entities,
        )
    )

    assert len(
        context2.selected_memory_ids
    ) == 1

    assert (
        "exponential backoff"
        in context2.context_text.lower()
    )
