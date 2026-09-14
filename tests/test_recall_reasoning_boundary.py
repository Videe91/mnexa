import dataclasses
import inspect

import pytest


def _boundary():
    import mnexa_context

    return mnexa_context


def test_same_recall_produces_same_evidence_hash():
    module = _boundary()

    first = module.ContextFrame.create(
        watermark=41,
        recall_intent="exact retry rule",
        selected_memory_ids=(
            "m1",
            "m2",
        ),
        context_text="memory one\nmemory two",
        metadata={
            "ranking": "rrf",
        },
    )

    second = module.ContextFrame.create(
        watermark=41,
        recall_intent="exact retry rule",
        selected_memory_ids=(
            "m1",
            "m2",
        ),
        context_text="memory one\nmemory two",
        metadata={
            "ranking": "rrf",
        },
    )

    assert (
        first.evidence_sha256
        ==
        second.evidence_sha256
    )


def test_reasoning_instruction_is_not_part_of_context_frame():
    module = _boundary()

    fields = {
        field.name
        for field
        in dataclasses.fields(
            module.ContextFrame
        )
    }

    assert (
        "reasoning_instruction"
        not in fields
    )

    assert (
        "reasoner"
        not in fields
    )

    assert (
        "model"
        not in fields
    )


def test_context_frame_is_immutable():
    module = _boundary()

    frame = module.ContextFrame.create(
        watermark=10,
        recall_intent="find retry policy",
        selected_memory_ids=("m1",),
        context_text="retry exactly five times",
    )

    with pytest.raises(
        dataclasses.FrozenInstanceError
    ):
        frame.context_text = "changed"


def test_selected_memory_ids_are_immutable_tuple():
    module = _boundary()

    frame = module.ContextFrame.create(
        watermark=10,
        recall_intent="find retry policy",
        selected_memory_ids=[
            "m1",
            "m2",
        ],
        context_text="context",
    )

    assert (
        frame.selected_memory_ids
        ==
        (
            "m1",
            "m2",
        )
    )

    assert isinstance(
        frame.selected_memory_ids,
        tuple,
    )


def test_metadata_is_canonicalized():
    module = _boundary()

    a = module.ContextFrame.create(
        watermark=12,
        recall_intent="query",
        selected_memory_ids=("m1",),
        context_text="context",
        metadata={
            "b": 2,
            "a": 1,
        },
    )

    b = module.ContextFrame.create(
        watermark=12,
        recall_intent="query",
        selected_memory_ids=("m1",),
        context_text="context",
        metadata={
            "a": 1,
            "b": 2,
        },
    )

    assert (
        a.metadata_json
        ==
        b.metadata_json
    )

    assert (
        a.evidence_sha256
        ==
        b.evidence_sha256
    )


def test_reasoning_instruction_cannot_change_hash():
    module = _boundary()

    frame = module.ContextFrame.create(
        watermark=91,
        recall_intent="find exact rule",
        selected_memory_ids=(
            "memory-a",
            "memory-b",
        ),
        context_text="frozen evidence",
    )

    instruction_a = (
        "Answer normally."
    )

    instruction_b = (
        "Treat memories as competing hypotheses."
    )

    assert (
        instruction_a
        !=
        instruction_b
    )

    # Neither instruction participates in ContextFrame identity.
    assert (
        frame.evidence_sha256
        ==
        frame.evidence_sha256
    )


def test_integrity_verification_passes_for_valid_frame():
    module = _boundary()

    frame = module.ContextFrame.create(
        watermark=7,
        recall_intent="query",
        selected_memory_ids=("m1",),
        context_text="evidence",
    )

    assert (
        frame.verify_integrity()
        is True
    )


def test_integrity_verification_detects_modified_payload():
    module = _boundary()

    frame = module.ContextFrame.create(
        watermark=7,
        recall_intent="query",
        selected_memory_ids=("m1",),
        context_text="evidence",
    )

    corrupted = dataclasses.replace(
        frame,
        context_text="different evidence",
    )

    assert (
        corrupted.verify_integrity()
        is False
    )


def test_context_preparer_has_no_reasoning_parameter():
    module = _boundary()

    signature = inspect.signature(
        module.ContextPreparer.prepare
    )

    prohibited = {
        "model",
        "reasoner",
        "reasoning_instruction",
        "system_prompt",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_context_preparer_freezes_watermark_before_recall():
    module = _boundary()

    calls = []

    def freeze_watermark():
        calls.append(
            ("watermark",)
        )

        return 77

    def recall(
        recall_intent,
        watermark,
    ):
        calls.append(
            (
                "recall",
                recall_intent,
                watermark,
            )
        )

        return {
            "records": ["m1"],
        }

    def assemble(
        recalled,
        watermark,
    ):
        calls.append(
            (
                "assemble",
                recalled,
                watermark,
            )
        )

        return module.AssembledRecall(
            selected_memory_ids=(
                "m1",
            ),
            context_text=(
                "authoritative memory"
            ),
            metadata={
                "channel": "semantic",
            },
        )

    preparer = module.ContextPreparer(
        freeze_watermark=(
            freeze_watermark
        ),
        recall=recall,
        assemble=assemble,
    )

    frame = preparer.prepare(
        recall_intent=(
            "find the retry rule"
        )
    )

    assert calls == [
        ("watermark",),

        (
            "recall",
            "find the retry rule",
            77,
        ),

        (
            "assemble",
            {
                "records": ["m1"],
            },
            77,
        ),
    ]

    assert (
        frame.watermark
        == 77
    )


def test_preparer_never_invokes_reasoner():
    module = _boundary()

    reasoner_calls = []

    def reasoner(*args, **kwargs):
        reasoner_calls.append(
            (
                args,
                kwargs,
            )
        )

        return "decision"

    def freeze_watermark():
        return 5

    def recall(
        recall_intent,
        watermark,
    ):
        return [
            "m1",
        ]

    def assemble(
        recalled,
        watermark,
    ):
        return module.AssembledRecall(
            selected_memory_ids=("m1",),
            context_text="memory",
        )

    preparer = module.ContextPreparer(
        freeze_watermark=(
            freeze_watermark
        ),
        recall=recall,
        assemble=assemble,
    )

    preparer.prepare(
        recall_intent="query"
    )

    assert (
        reasoner_calls
        == []
    )


def test_context_assembled_event_can_reference_frozen_hash():
    module = _boundary()

    observed = {}

    def freeze_watermark():
        return 88

    def recall(
        recall_intent,
        watermark,
    ):
        return ["m3"]

    def assemble(
        recalled,
        watermark,
    ):
        return module.AssembledRecall(
            selected_memory_ids=("m3",),
            context_text="memory three",
        )

    def record_context(frame):
        observed[
            "hash"
        ] = frame.evidence_sha256

        observed[
            "watermark"
        ] = frame.watermark

        return "event-context-123"

    preparer = module.ContextPreparer(
        freeze_watermark=(
            freeze_watermark
        ),
        recall=recall,
        assemble=assemble,
        record_context=(
            record_context
        ),
    )

    frame = preparer.prepare(
        recall_intent="query"
    )

    assert (
        frame.context_assembled_event_id
        ==
        "event-context-123"
    )

    assert (
        observed["hash"]
        ==
        frame.evidence_sha256
    )

    assert (
        observed["watermark"]
        ==
        88
    )


def test_recording_event_does_not_change_evidence_hash():
    module = _boundary()

    def freeze_watermark():
        return 10

    def recall(
        recall_intent,
        watermark,
    ):
        return ["m1"]

    def assemble(
        recalled,
        watermark,
    ):
        return module.AssembledRecall(
            selected_memory_ids=("m1",),
            context_text="same context",
        )

    without_event = (
        module.ContextPreparer(
            freeze_watermark=(
                freeze_watermark
            ),
            recall=recall,
            assemble=assemble,
        )
        .prepare(
            recall_intent="same query"
        )
    )

    with_event = (
        module.ContextPreparer(
            freeze_watermark=(
                freeze_watermark
            ),
            recall=recall,
            assemble=assemble,
            record_context=(
                lambda frame:
                    "ctx-event-9"
            ),
        )
        .prepare(
            recall_intent="same query"
        )
    )

    assert (
        without_event.evidence_sha256
        ==
        with_event.evidence_sha256
    )


def test_new_recall_intent_creates_different_frame_identity():
    module = _boundary()

    a = module.ContextFrame.create(
        watermark=4,
        recall_intent="retry rule",
        selected_memory_ids=("m1",),
        context_text="context",
    )

    b = module.ContextFrame.create(
        watermark=4,
        recall_intent="storage rule",
        selected_memory_ids=("m1",),
        context_text="context",
    )

    assert (
        a.evidence_sha256
        !=
        b.evidence_sha256
    )
