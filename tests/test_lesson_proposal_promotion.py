import pytest

from mnexa_seed import (
    MnexaSeed,
)


class FakeEmbedder:
    vocab = (
        "429",
        "retry",
        "backoff",
        "payments",
        "flooding",
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
                    for word in words
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


def _failed_decision(
    m,
):
    decision = (
        m.event(
            "DecisionMade",
            "Retry immediately with zero delay.",
            (
                "api:payments",
            ),
        )
    )

    outcome = (
        m.observe_outcome(
            decision.object_id,
            (
                "Zero delay retry caused "
                "request flooding."
            ),
            success=False,
        )
    )

    return (
        decision,
        outcome,
    )


def _interpretation_count(
    m,
):
    return int(
        m.db.execute(
            """
            SELECT COUNT(*) n
            FROM commits
            WHERE plane='interpretive'
            """
        )
        .fetchone()["n"]
    )


def test_lesson_proposal_is_history_not_active_memory(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, outcome = (
        _failed_decision(
            m
        )
    )

    proposal = (
        m.propose_lesson(
            decision.object_id,

            lambda evidence: (
                "When Payments API returns 429, "
                "retry with exponential backoff."
            ),
        )
    )

    assert (
        proposal.plane
        ==
        "historical"
    )

    assert (
        proposal.kind
        ==
        "LessonProposed"
    )

    assert (
        proposal.refs
        ==
        (
            decision.object_id,
            outcome.object_id,
        )
    )

    # Merely proposing a lesson must not create
    # active searchable knowledge.
    assert (
        _interpretation_count(m)
        ==
        0
    )

    hits = (
        m.recall(
            (
                "Payments 429 "
                "exponential backoff"
            ),
            (
                "api:payments",
            ),
            top_k=10,
        )
    )

    assert all(
        hit.item.object_id
        !=
        proposal.object_id

        for hit in hits
    )


def test_promoting_lesson_creates_searchable_interpretation(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, _ = (
        _failed_decision(
            m
        )
    )

    proposal = (
        m.propose_lesson(
            decision.object_id,

            lambda evidence: (
                "When Payments API returns 429, "
                "retry with exponential backoff."
            ),
        )
    )

    memory = (
        m.promote_lesson(
            proposal.object_id
        )
    )

    assert (
        memory.plane
        ==
        "interpretive"
    )

    assert (
        memory.kind
        ==
        "belief"
    )

    # Active memory points directly back to
    # the proposal that produced it.
    assert (
        memory.refs
        ==
        (
            proposal.object_id,
        )
    )

    assert (
        _interpretation_count(m)
        ==
        1
    )

    hits = (
        m.recall(
            (
                "Payments API 429 "
                "retry backoff"
            ),
            (
                "api:payments",
            ),
            top_k=10,
        )
    )

    assert any(
        hit.item.object_id
        ==
        memory.object_id

        for hit in hits
    )

    assert any(
        "exponential backoff"
        in hit.item.text.lower()

        for hit in hits
    )


def test_proposal_preserves_complete_decision_outcome_evidence(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, first_outcome = (
        _failed_decision(
            m
        )
    )

    second_outcome = (
        m.observe_outcome(
            decision.object_id,
            (
                "Later telemetry confirmed "
                "rate-limit amplification."
            ),
            success=False,
        )
    )

    observed = {}

    def lesson_builder(
        evidence,
    ):
        observed[
            "evidence"
        ] = evidence

        return (
            "Use exponential backoff "
            "for rate limiting."
        )

    proposal = (
        m.propose_lesson(
            decision.object_id,
            lesson_builder,
        )
    )

    assert (
        "Retry immediately with zero delay."
        in observed["evidence"]
    )

    assert (
        "request flooding"
        in observed["evidence"]
    )

    assert (
        "rate-limit amplification"
        in observed["evidence"]
    )

    assert (
        proposal.refs
        ==
        (
            decision.object_id,
            first_outcome.object_id,
            second_outcome.object_id,
        )
    )


def test_empty_lesson_proposal_is_rejected(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, _ = (
        _failed_decision(
            m
        )
    )

    with pytest.raises(
        ValueError,
        match="empty lesson",
    ):
        m.propose_lesson(
            decision.object_id,
            lambda evidence: "   ",
        )

    assert (
        _interpretation_count(m)
        ==
        0
    )


def test_promotion_rejects_non_lesson_event(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    unrelated = (
        m.event(
            "ObservationRecorded",
            "ordinary observation",
        )
    )

    with pytest.raises(
        ValueError,
        match="LessonProposed",
    ):
        m.promote_lesson(
            unrelated.object_id
        )


def test_proposal_requires_observed_outcome(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision = (
        m.event(
            "DecisionMade",
            "some decision",
        )
    )

    with pytest.raises(
        ValueError,
        match="no observed outcome",
    ):
        m.propose_lesson(
            decision.object_id,

            lambda evidence: (
                "candidate lesson"
            ),
        )


def test_promotion_retry_is_idempotent(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, _ = (
        _failed_decision(
            m
        )
    )

    proposal = (
        m.propose_lesson(
            decision.object_id,

            lambda evidence: (
                "When Payments API returns 429, "
                "retry with exponential backoff."
            ),
        )
    )

    first = (
        m.promote_lesson(
            proposal.object_id,

            idempotency_key=(
                "promotion:lesson:001"
            ),
        )
    )

    second = (
        m.promote_lesson(
            proposal.object_id,

            idempotency_key=(
                "promotion:lesson:001"
            ),
        )
    )

    assert (
        first.object_id
        ==
        second.object_id
    )

    assert (
        first.version
        ==
        second.version
    )

    assert (
        first.seq
        ==
        second.seq
    )

    assert (
        _interpretation_count(m)
        ==
        1
    )
