from mnexa_seed import MnexaSeed


class FakeEmbedder:
    vocab = (
        "429",
        "retry",
        "backoff",
        "payments",
        "retry-after",
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
    success=False,
):
    decision = m.event(
        "DecisionMade",
        decision_text,
        (
            "api:payments",
        ),
    )

    outcome = m.observe_outcome(
        decision.object_id,
        outcome_text,
        success=success,
    )

    return (
        decision,
        outcome,
    )


def _lesson_proposal(
    m,
    decision_id,
    lesson,
):
    return m.propose_lesson(
        decision_id,
        lambda evidence: lesson,
    )


def _active_belief(
    m,
):
    lesson = (
        "When Payments API returns 429, "
        "retry with exponential backoff."
    )

    decision_a, _ = (
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

    decision_b, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retry immediately again."
            ),
            outcome_text=(
                "Rate-limit amplification occurred."
            ),
        )
    )

    _lesson_proposal(
        m,
        decision_a.object_id,
        lesson,
    )

    proposal_b = (
        _lesson_proposal(
            m,
            decision_b.object_id,
            lesson,
        )
    )

    belief = (
        m.promote_lesson_if_supported(
            proposal_b.object_id
        )
    )

    assert belief is not None

    return (
        belief,
        lesson,
    )


def _belief_versions(
    m,
    belief_id,
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

            WHERE
                plane='interpretive'
                AND object_id=?

            ORDER BY version
            """,
            (
                belief_id,
            ),
        )
    ]


def _contradiction_text():
    return (
        "For this Payments API, Retry-After "
        "must be obeyed instead of using "
        "independent exponential backoff."
    )


# ---------------------------------------------------------------------
# 1. CONTRADICTION IS A PROPOSAL, NOT AUTOMATIC TRUTH
# ---------------------------------------------------------------------

def test_contradiction_proposal_is_historical_and_pins_belief_version(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    decision, outcome = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Used exponential backoff."
            ),
            outcome_text=(
                "Server returned Retry-After 30; "
                "the early retry was rejected."
            ),
        )
    )

    observed = {}

    def contradiction_builder(
        evidence,
    ):
        observed[
            "evidence"
        ] = evidence

        return (
            _contradiction_text()
        )

    proposal = (
        m.propose_contradiction(
            belief.object_id,
            decision.object_id,
            contradiction_builder,
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
        "ContradictionProposed"
    )

    assert (
        proposal.refs
        ==
        (
            belief.object_id,
            decision.object_id,
            outcome.object_id,
        )
    )

    assert (
        proposal.metadata[
            "target_belief_id"
        ]
        ==
        belief.object_id
    )

    assert (
        proposal.metadata[
            "target_belief_version"
        ]
        ==
        belief.version
    )

    assert (
        proposal.metadata[
            "target_belief_seq"
        ]
        ==
        belief.seq
    )

    assert (
        proposal.metadata[
            "authority"
        ]
        ==
        "proposal_only"
    )

    assert belief.text in (
        observed["evidence"]
    )

    assert (
        "Used exponential backoff."
        in
        observed["evidence"]
    )

    assert (
        "Retry-After 30"
        in
        observed["evidence"]
    )


# ---------------------------------------------------------------------
# 2. ONE CONTRADICTION IS NOT ENOUGH
# ---------------------------------------------------------------------

def test_one_independent_contradiction_does_not_contest_belief(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Used exponential backoff."
            ),
            outcome_text=(
                "Retry-After instruction was violated."
            ),
        )
    )

    m.propose_contradiction(
        belief.object_id,
        decision.object_id,
        lambda evidence: (
            _contradiction_text()
        ),
    )

    result = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    assert result is None

    versions = (
        _belief_versions(
            m,
            belief.object_id,
        )
    )

    assert len(
        versions
    ) == 1

    assert (
        versions[-1].version
        ==
        belief.version
    )


# ---------------------------------------------------------------------
# 3. TWO INDEPENDENT MATCHING CONTRADICTIONS CONTEST THE BELIEF
# ---------------------------------------------------------------------

def test_two_independent_matching_contradictions_create_contested_version(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    decision_a, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Used exponential backoff "
                "before Retry-After elapsed."
            ),
            outcome_text=(
                "Request was rejected."
            ),
        )
    )

    decision_b, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Retried using local backoff timing."
            ),
            outcome_text=(
                "Server again required Retry-After."
            ),
        )
    )

    contradiction_a = (
        m.propose_contradiction(
            belief.object_id,
            decision_a.object_id,
            lambda evidence: (
                _contradiction_text()
            ),
        )
    )

    contradiction_b = (
        m.propose_contradiction(
            belief.object_id,
            decision_b.object_id,
            lambda evidence: (
                _contradiction_text()
            ),
        )
    )

    contested = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    assert contested is not None

    assert (
        contested.object_id
        ==
        belief.object_id
    )

    assert (
        contested.version
        ==
        belief.version + 1
    )

    assert (
        contested.seq
        >
        belief.seq
    )

    assert (
        contested.text
        ==
        belief.text
    )

    assert (
        contested.metadata[
            "status"
        ]
        ==
        "contested"
    )

    assert tuple(
        contested.metadata[
            "support_refs"
        ]
    ) == belief.refs

    assert set(
        contested.metadata[
            "contradiction_refs"
        ]
    ) == {
        contradiction_a.object_id,
        contradiction_b.object_id,
    }

    assert set(
        contested.refs
    ) == (
        set(
            belief.refs
        )
        |
        {
            contradiction_a.object_id,
            contradiction_b.object_id,
        }
    )


# ---------------------------------------------------------------------
# 4. ONE DECISION CANNOT FAKE TWO CONTRADICTIONS
# ---------------------------------------------------------------------

def test_multiple_contradiction_proposals_from_same_decision_count_once(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Used exponential backoff."
            ),
            outcome_text=(
                "Retry-After was required."
            ),
        )
    )

    for _ in range(
        2
    ):
        m.propose_contradiction(
            belief.object_id,
            decision.object_id,
            lambda evidence: (
                _contradiction_text()
            ),
        )

    result = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    assert result is None

    assert len(
        _belief_versions(
            m,
            belief.object_id,
        )
    ) == 1


# ---------------------------------------------------------------------
# 5. FAKE ANCESTRY DOES NOT COUNT
# ---------------------------------------------------------------------

def test_fake_contradiction_without_real_decision_outcome_chain_is_ignored(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    real_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Used exponential backoff."
            ),
            outcome_text=(
                "Retry-After was required."
            ),
        )
    )

    m.propose_contradiction(
        belief.object_id,
        real_decision.object_id,
        lambda evidence: (
            _contradiction_text()
        ),
    )

    # Same contradiction text, but fake ancestry.
    m.event(
        "ContradictionProposed",
        _contradiction_text(),
        (
            "api:payments",
        ),
        refs=(
            belief.object_id,
            "missing-decision",
            "missing-outcome",
        ),
        metadata={
            "target_belief_id": (
                belief.object_id
            ),
            "target_belief_version": (
                belief.version
            ),
            "target_belief_seq": (
                belief.seq
            ),
            "authority": (
                "proposal_only"
            ),
        },
    )

    result = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    assert result is None


# ---------------------------------------------------------------------
# 6. CONTRADICTION TEXT MUST MATCH
# ---------------------------------------------------------------------

def test_different_contradiction_claims_do_not_form_quorum(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    decision_a, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt A.",
            outcome_text="Outcome A.",
        )
    )

    decision_b, _ = (
        _decision_with_outcome(
            m,
            decision_text="Attempt B.",
            outcome_text="Outcome B.",
        )
    )

    m.propose_contradiction(
        belief.object_id,
        decision_a.object_id,
        lambda evidence: (
            "Retry-After must replace "
            "local exponential backoff."
        ),
    )

    m.propose_contradiction(
        belief.object_id,
        decision_b.object_id,
        lambda evidence: (
            "The API requires a fixed "
            "thirty second wait."
        ),
    )

    result = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    assert result is None


# ---------------------------------------------------------------------
# 7. STALE CONTRADICTIONS DO NOT ATTACK A NEWER BELIEF VERSION
# ---------------------------------------------------------------------

def test_contradictions_are_scoped_to_exact_belief_version(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief_v1, lesson = (
        _active_belief(
            m
        )
    )

    old_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Contradict old belief."
            ),
            outcome_text=(
                "Old belief encountered counterevidence."
            ),
        )
    )

    m.propose_contradiction(
        belief_v1.object_id,
        old_decision.object_id,
        lambda evidence: (
            _contradiction_text()
        ),
    )

    # New supporting evidence strengthens the belief to v2.
    support_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Another immediate retry."
            ),
            outcome_text=(
                "Another flooding incident."
            ),
        )
    )

    support_proposal = (
        _lesson_proposal(
            m,
            support_decision.object_id,
            lesson,
        )
    )

    belief_v2 = (
        m.promote_lesson_if_supported(
            support_proposal.object_id
        )
    )

    assert (
        belief_v2.version
        ==
        belief_v1.version + 1
    )

    new_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Contradict newer belief."
            ),
            outcome_text=(
                "New version encountered counterevidence."
            ),
        )
    )

    m.propose_contradiction(
        belief_v2.object_id,
        new_decision.object_id,
        lambda evidence: (
            _contradiction_text()
        ),
    )

    # One contradiction targeted v1.
    # One targeted v2.
    #
    # They must NOT be merged into a quorum.
    result = (
        m.contest_belief_if_supported(
            belief_v2.object_id
        )
    )

    assert result is None


# ---------------------------------------------------------------------
# 8. CONTESTED BELIEF DISAPPEARS FROM NORMAL RECALL
#    BUT HISTORICAL AS-OF RECALL STILL WORKS
# ---------------------------------------------------------------------

def test_contested_belief_is_withheld_from_normal_recall_but_history_survives(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    query = (
        "Payments API 429 "
        "exponential backoff"
    )

    before = (
        m.recall(
            query,
            (
                "api:payments",
            ),
            top_k=10,
            as_of=belief.seq,
        )
    )

    assert any(
        hit.item.object_id
        ==
        belief.object_id

        for hit in before
    )

    for label in (
        "A",
        "B",
    ):
        decision, _ = (
            _decision_with_outcome(
                m,
                decision_text=(
                    f"Contradicting attempt {label}."
                ),
                outcome_text=(
                    "Retry-After evidence contradicted "
                    "the active belief."
                ),
            )
        )

        m.propose_contradiction(
            belief.object_id,
            decision.object_id,
            lambda evidence: (
                _contradiction_text()
            ),
        )

    contested = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    assert (
        contested.metadata[
            "status"
        ]
        ==
        "contested"
    )

    after = (
        m.recall(
            query,
            (
                "api:payments",
            ),
            top_k=10,
            as_of=contested.seq,
        )
    )

    assert all(
        hit.item.object_id
        !=
        belief.object_id

        for hit in after
    )

    historical = (
        m.recall(
            query,
            (
                "api:payments",
            ),
            top_k=10,
            as_of=belief.seq,
        )
    )

    assert any(
        hit.item.object_id
        ==
        belief.object_id
        and
        hit.item.version
        ==
        belief.version

        for hit in historical
    )


# ---------------------------------------------------------------------
# 9. RE-EVALUATING SAME CONTRADICTION QUORUM IS IDEMPOTENT
# ---------------------------------------------------------------------

def test_contestation_retry_returns_same_version(
    tmp_path,
):
    m = _seed(
        tmp_path
    )

    belief, _ = (
        _active_belief(
            m
        )
    )

    for label in (
        "A",
        "B",
    ):
        decision, _ = (
            _decision_with_outcome(
                m,
                decision_text=(
                    f"Contradiction {label}."
                ),
                outcome_text=(
                    "Retry-After contradicted "
                    "the active belief."
                ),
            )
        )

        m.propose_contradiction(
            belief.object_id,
            decision.object_id,
            lambda evidence: (
                _contradiction_text()
            ),
        )

    first = (
        m.contest_belief_if_supported(
            belief.object_id
        )
    )

    second = (
        m.contest_belief_if_supported(
            belief.object_id
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

    versions = (
        _belief_versions(
            m,
            belief.object_id,
        )
    )

    assert len(
        versions
    ) == 2
