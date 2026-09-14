from mnexa_seed import MnexaSeed


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


def _decision_with_outcome(
    m,
    *,
    decision_text,
    outcome_text,
    entity="api:payments",
):
    decision = m.event(
        "DecisionMade",
        decision_text,
        (
            entity,
        ),
    )

    outcome = m.observe_outcome(
        decision.object_id,
        outcome_text,
        success=False,
    )

    return (
        decision,
        outcome,
    )


def _proposal(
    m,
    decision_id,
    lesson_text,
):
    return m.propose_lesson(
        decision_id,
        lambda evidence: lesson_text,
    )


def _interpretations(
    m,
):
    return [
        m._item(
            row
        )
        for row
        in m.db.execute(
            """
            SELECT *
            FROM commits
            WHERE plane='interpretive'
            ORDER BY seq
            """
        )
    ]


def test_one_supported_proposal_is_not_enough_for_auto_promotion(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retry immediately."
            ),
            outcome_text=(
                "Immediate retry caused flooding."
            ),
        )
    )

    proposal = _proposal(
        m,
        decision.object_id,
        (
            "When Payments API returns 429, "
            "retry with exponential backoff."
        ),
    )

    result = (
        m.promote_lesson_if_supported(
            proposal.object_id
        )
    )

    assert result is None

    assert (
        _interpretations(m)
        ==
        []
    )


def test_two_distinct_decisions_with_same_lesson_auto_promote(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    first_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retry immediately."
            ),
            outcome_text=(
                "Request flooding occurred."
            ),
        )
    )

    second_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retry again immediately."
            ),
            outcome_text=(
                "Rate-limit amplification occurred."
            ),
        )
    )

    first_proposal = _proposal(
        m,
        first_decision.object_id,
        (
            "When Payments API returns 429, "
            "retry with exponential backoff."
        ),
    )

    second_proposal = _proposal(
        m,
        second_decision.object_id,
        (
            "When Payments API returns 429, "
            "retry with exponential backoff."
        ),
    )

    memory = (
        m.promote_lesson_if_supported(
            second_proposal.object_id
        )
    )

    assert memory is not None

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

    assert (
        memory.text
        ==
        second_proposal.text
    )

    assert set(
        memory.refs
    ) == {
        first_proposal.object_id,
        second_proposal.object_id,
    }


def test_case_and_whitespace_are_normalized_for_quorum(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    first_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt one.",
            outcome_text="Attempt one failed.",
        )
    )

    second_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt two.",
            outcome_text="Attempt two failed.",
        )
    )

    _proposal(
        m,
        first_decision.object_id,
        (
            "When Payments API returns 429, "
            "retry with exponential backoff."
        ),
    )

    second_proposal = _proposal(
        m,
        second_decision.object_id,
        (
            "  when   PAYMENTS api returns 429, "
            "retry with exponential backoff.  "
        ),
    )

    memory = (
        m.promote_lesson_if_supported(
            second_proposal.object_id
        )
    )

    assert memory is not None


def test_different_wording_does_not_form_quorum(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    first_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt one.",
            outcome_text="Attempt one failed.",
        )
    )

    second_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt two.",
            outcome_text="Attempt two failed.",
        )
    )

    _proposal(
        m,
        first_decision.object_id,
        (
            "When Payments API returns 429, "
            "retry with exponential backoff."
        ),
    )

    second_proposal = _proposal(
        m,
        second_decision.object_id,
        (
            "Back off exponentially whenever "
            "the Payments API rate limits."
        ),
    )

    result = (
        m.promote_lesson_if_supported(
            second_proposal.object_id
        )
    )

    assert result is None

    assert (
        _interpretations(m)
        ==
        []
    )


def test_two_proposals_from_same_decision_count_as_one_support(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retry immediately."
            ),
            outcome_text=(
                "Request flooding occurred."
            ),
        )
    )

    lesson = (
        "When Payments API returns 429, "
        "retry with exponential backoff."
    )

    _proposal(
        m,
        decision.object_id,
        lesson,
    )

    second_proposal = _proposal(
        m,
        decision.object_id,
        lesson,
    )

    result = (
        m.promote_lesson_if_supported(
            second_proposal.object_id
        )
    )

    assert result is None

    assert (
        _interpretations(m)
        ==
        []
    )


def test_fake_matching_proposal_without_real_evidence_does_not_count(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    real_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retry immediately."
            ),
            outcome_text=(
                "Request flooding occurred."
            ),
        )
    )

    lesson = (
        "When Payments API returns 429, "
        "retry with exponential backoff."
    )

    real_proposal = _proposal(
        m,
        real_decision.object_id,
        lesson,
    )

    # Same text, but not a valid proposal ancestry:
    # no real DecisionMade + OutcomeObserved evidence chain.
    m.event(
        "LessonProposed",
        lesson,
        (
            "api:payments",
        ),
        refs=(
            "missing-decision",
        ),
        metadata={
            "proposal_for": (
                "missing-decision"
            ),
            "authority": (
                "proposal_only"
            ),
        },
    )

    result = (
        m.promote_lesson_if_supported(
            real_proposal.object_id
        )
    )

    assert result is None

    assert (
        _interpretations(m)
        ==
        []
    )


def test_auto_promotion_is_repeat_safe_without_caller_key(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    first_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt one.",
            outcome_text="Attempt one failed.",
        )
    )

    second_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt two.",
            outcome_text="Attempt two failed.",
        )
    )

    lesson = (
        "When Payments API returns 429, "
        "retry with exponential backoff."
    )

    first_proposal = _proposal(
        m,
        first_decision.object_id,
        lesson,
    )

    second_proposal = _proposal(
        m,
        second_decision.object_id,
        lesson,
    )

    first = (
        m.promote_lesson_if_supported(
            second_proposal.object_id
        )
    )

    second = (
        m.promote_lesson_if_supported(
            first_proposal.object_id
        )
    )

    assert (
        first.object_id
        ==
        second.object_id
    )

    assert (
        first.seq
        ==
        second.seq
    )

    assert (
        len(
            _interpretations(m)
        )
        ==
        1
    )
