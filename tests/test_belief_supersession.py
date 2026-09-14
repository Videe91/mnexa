from mnexa_seed import MnexaSeed


class FakeEmbedder:
    vocab = (
        "429",
        "retry",
        "backoff",
        "payments",
        "retry-after",
        "obey",
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


OLD_LESSON = (
    "When Payments API returns 429, "
    "retry with exponential backoff."
)

NEW_LESSON = (
    "When Payments API returns 429 with Retry-After, "
    "obey Retry-After before retrying."
)

CONTRADICTION = (
    "When Retry-After is present, independent exponential "
    "backoff can contradict the server-required retry timing."
)


def _seed(tmp_path):
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
        ("api:payments",),
    )

    outcome = m.observe_outcome(
        decision.object_id,
        outcome_text,
        success=success,
    )

    return decision, outcome


def _lesson_proposal(
    m,
    decision_id,
    lesson,
):
    return m.propose_lesson(
        decision_id,
        lambda evidence: lesson,
    )


def _active_old_belief(m):
    decision_a, _ = _decision_with_outcome(
        m,
        decision_text="Retried immediately.",
        outcome_text="Immediate retry caused flooding.",
    )

    decision_b, _ = _decision_with_outcome(
        m,
        decision_text="Retried immediately again.",
        outcome_text="Rate-limit amplification occurred.",
    )

    _lesson_proposal(
        m,
        decision_a.object_id,
        OLD_LESSON,
    )

    proposal_b = _lesson_proposal(
        m,
        decision_b.object_id,
        OLD_LESSON,
    )

    belief = m.promote_lesson_if_supported(
        proposal_b.object_id
    )

    assert belief is not None

    return belief


def _counterepisode(
    m,
    old_belief_id,
    *,
    label,
    propose_replacement=True,
):
    decision, _ = _decision_with_outcome(
        m,
        decision_text=(
            f"Counterepisode {label}: used local "
            "exponential backoff."
        ),
        outcome_text=(
            f"Counterepisode {label}: server supplied "
            "Retry-After and rejected the earlier retry."
        ),
    )

    contradiction = m.propose_contradiction(
        old_belief_id,
        decision.object_id,
        lambda evidence: CONTRADICTION,
    )

    replacement_proposal = None

    if propose_replacement:
        replacement_proposal = _lesson_proposal(
            m,
            decision.object_id,
            NEW_LESSON,
        )

    return (
        decision,
        contradiction,
        replacement_proposal,
    )


def _promote_replacement_from_decisions(
    m,
    decisions,
):
    proposals = []

    for decision in decisions:
        proposals.append(
            _lesson_proposal(
                m,
                decision.object_id,
                NEW_LESSON,
            )
        )

    replacement = m.promote_lesson_if_supported(
        proposals[-1].object_id
    )

    assert replacement is not None

    return replacement


def _belief_versions(
    m,
    belief_id,
):
    return [
        m._item(row)
        for row in m.db.execute(
            """
            SELECT *
            FROM commits
            WHERE
                plane='interpretive'
                AND object_id=?
            ORDER BY version
            """,
            (belief_id,),
        )
    ]


# ---------------------------------------------------------------------
# 1. ONLY A CONTESTED BELIEF MAY BE SUPERSEDED
# ---------------------------------------------------------------------

def test_active_uncontested_belief_cannot_be_superseded(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    replacement_decision_a, _ = (
        _decision_with_outcome(
            m,
            decision_text="Obeyed Retry-After A.",
            outcome_text="Request succeeded A.",
            success=True,
        )
    )

    replacement_decision_b, _ = (
        _decision_with_outcome(
            m,
            decision_text="Obeyed Retry-After B.",
            outcome_text="Request succeeded B.",
            success=True,
        )
    )

    replacement = (
        _promote_replacement_from_decisions(
            m,
            (
                replacement_decision_a,
                replacement_decision_b,
            ),
        )
    )

    try:
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
        )
    except ValueError as exc:
        assert "contested" in str(exc)
    else:
        raise AssertionError(
            "uncontested belief was superseded"
        )


# ---------------------------------------------------------------------
# 2. REPLACEMENT MUST BE A DIFFERENT PROPOSITION
# ---------------------------------------------------------------------

def test_same_proposition_cannot_supersede_itself_under_new_identity(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    counter_a = _counterepisode(
        m,
        old.object_id,
        label="A",
        propose_replacement=False,
    )

    counter_b = _counterepisode(
        m,
        old.object_id,
        label="B",
        propose_replacement=False,
    )

    contested = m.contest_belief_if_supported(
        old.object_id
    )

    assert (
        contested.metadata["status"]
        ==
        "contested"
    )

    fake_same = m.learn(
        OLD_LESSON,
        ("api:payments",),
        (
            counter_a[1].object_id,
            counter_b[1].object_id,
        ),
    )

    try:
        m.supersede_belief_if_supported(
            old.object_id,
            fake_same.object_id,
        )
    except ValueError as exc:
        assert "different proposition" in str(exc)
    else:
        raise AssertionError(
            "same proposition superseded itself"
        )


# ---------------------------------------------------------------------
# 3. AN UNRELATED PROMOTED BELIEF CANNOT REPLACE X
# ---------------------------------------------------------------------

def test_promoted_replacement_without_shared_counterepisodes_does_not_supersede(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    _counterepisode(
        m,
        old.object_id,
        label="A",
        propose_replacement=False,
    )

    _counterepisode(
        m,
        old.object_id,
        label="B",
        propose_replacement=False,
    )

    contested = m.contest_belief_if_supported(
        old.object_id
    )

    assert (
        contested.metadata["status"]
        ==
        "contested"
    )

    unrelated_a, _ = _decision_with_outcome(
        m,
        decision_text="Independent replacement episode C.",
        outcome_text="Retry-After worked in C.",
        success=True,
    )

    unrelated_b, _ = _decision_with_outcome(
        m,
        decision_text="Independent replacement episode D.",
        outcome_text="Retry-After worked in D.",
        success=True,
    )

    replacement = (
        _promote_replacement_from_decisions(
            m,
            (
                unrelated_a,
                unrelated_b,
            ),
        )
    )

    result = (
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
        )
    )

    assert result is None

    versions = _belief_versions(
        m,
        old.object_id,
    )

    assert (
        versions[-1].metadata["status"]
        ==
        "contested"
    )


# ---------------------------------------------------------------------
# 4. ONE SHARED COUNTEREPISODE IS NOT ENOUGH
# ---------------------------------------------------------------------

def test_one_shared_counterepisode_does_not_supersede(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    shared_decision, _, shared_proposal = (
        _counterepisode(
            m,
            old.object_id,
            label="A",
            propose_replacement=True,
        )
    )

    _counterepisode(
        m,
        old.object_id,
        label="B",
        propose_replacement=False,
    )

    contested = m.contest_belief_if_supported(
        old.object_id
    )

    assert (
        contested.metadata["status"]
        ==
        "contested"
    )

    unrelated_decision, _ = (
        _decision_with_outcome(
            m,
            decision_text=(
                "Replacement support from unrelated episode C."
            ),
            outcome_text=(
                "Retry-After worked in unrelated episode C."
            ),
            success=True,
        )
    )

    unrelated_proposal = _lesson_proposal(
        m,
        unrelated_decision.object_id,
        NEW_LESSON,
    )

    replacement = m.promote_lesson_if_supported(
        unrelated_proposal.object_id
    )

    assert replacement is not None

    # The replacement has two supports:
    #
    #     shared_decision
    #     unrelated_decision
    #
    # but only shared_decision also participated in contesting X.
    result = (
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
        )
    )

    assert result is None

    assert (
        _belief_versions(
            m,
            old.object_id,
        )[-1].metadata["status"]
        ==
        "contested"
    )


# ---------------------------------------------------------------------
# 5. TWO SHARED INDEPENDENT EPISODES SUPERSEDE X WITH Y
# ---------------------------------------------------------------------

def test_two_shared_counterepisodes_supersede_contested_belief(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    decision_a, contradiction_a, proposal_a = (
        _counterepisode(
            m,
            old.object_id,
            label="A",
            propose_replacement=True,
        )
    )

    decision_b, contradiction_b, proposal_b = (
        _counterepisode(
            m,
            old.object_id,
            label="B",
            propose_replacement=True,
        )
    )

    contested = m.contest_belief_if_supported(
        old.object_id
    )

    assert (
        contested.metadata["status"]
        ==
        "contested"
    )

    replacement = m.promote_lesson_if_supported(
        proposal_b.object_id
    )

    assert replacement is not None

    superseded = (
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
        )
    )

    assert superseded is not None

    assert (
        superseded.object_id
        ==
        old.object_id
    )

    assert (
        superseded.version
        ==
        contested.version + 1
    )

    assert (
        superseded.text
        ==
        old.text
    )

    assert (
        superseded.metadata["status"]
        ==
        "superseded"
    )

    assert (
        superseded.metadata[
            "superseded_by"
        ]
        ==
        replacement.object_id
    )

    assert (
        superseded.metadata[
            "superseded_by_version"
        ]
        ==
        replacement.version
    )

    assert (
        superseded.metadata[
            "superseded_by_seq"
        ]
        ==
        replacement.seq
    )

    assert (
        superseded.metadata[
            "superseded_from_version"
        ]
        ==
        contested.version
    )

    assert set(
        superseded.metadata[
            "shared_decision_ids"
        ]
    ) == {
        decision_a.object_id,
        decision_b.object_id,
    }

    assert set(
        superseded.metadata[
            "contradiction_refs"
        ]
    ) == {
        contradiction_a.object_id,
        contradiction_b.object_id,
    }

    assert set(
        superseded.metadata[
            "replacement_support_refs"
        ]
    ) == {
        proposal_a.object_id,
        proposal_b.object_id,
    }

    assert set(
        superseded.refs
    ) == (
        set(contested.refs)
        |
        {
            proposal_a.object_id,
            proposal_b.object_id,
        }
    )


# ---------------------------------------------------------------------
# 6. FAKE ACTIVE BELIEF WITHOUT VALID LESSON ANCESTRY CANNOT REPLACE X
# ---------------------------------------------------------------------

def test_replacement_without_valid_lesson_ancestry_is_rejected(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    _counterepisode(
        m,
        old.object_id,
        label="A",
        propose_replacement=False,
    )

    _counterepisode(
        m,
        old.object_id,
        label="B",
        propose_replacement=False,
    )

    contested = m.contest_belief_if_supported(
        old.object_id
    )

    assert (
        contested.metadata["status"]
        ==
        "contested"
    )

    fake_replacement = m.learn(
        NEW_LESSON,
        ("api:payments",),
        (
            "missing-proposal-a",
            "missing-proposal-b",
        ),
    )

    result = (
        m.supersede_belief_if_supported(
            old.object_id,
            fake_replacement.object_id,
        )
    )

    assert result is None

    assert (
        _belief_versions(
            m,
            old.object_id,
        )[-1].metadata["status"]
        ==
        "contested"
    )


# ---------------------------------------------------------------------
# 7. SUPERSEDED X STAYS OUT OF RECALL; Y BECOMES THE ACTIVE MEMORY
# ---------------------------------------------------------------------

def test_recall_uses_replacement_and_keeps_old_belief_historical(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    _, _, proposal_a = _counterepisode(
        m,
        old.object_id,
        label="A",
        propose_replacement=True,
    )

    _, _, proposal_b = _counterepisode(
        m,
        old.object_id,
        label="B",
        propose_replacement=True,
    )

    contested = m.contest_belief_if_supported(
        old.object_id
    )

    replacement = m.promote_lesson_if_supported(
        proposal_b.object_id
    )

    superseded = (
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
        )
    )

    query = (
        "Payments API 429 Retry-After "
        "exponential backoff"
    )

    current = m.recall(
        query,
        ("api:payments",),
        top_k=20,
        as_of=superseded.seq,
    )

    assert all(
        hit.item.object_id
        !=
        old.object_id
        for hit in current
    )

    assert any(
        hit.item.object_id
        ==
        replacement.object_id
        for hit in current
    )

    historical = m.recall(
        query,
        ("api:payments",),
        top_k=20,
        as_of=old.seq,
    )

    assert any(
        hit.item.object_id
        ==
        old.object_id
        and
        hit.item.version
        ==
        old.version
        for hit in historical
    )


# ---------------------------------------------------------------------
# 8. SUPERSESSION RETRY IS IDEMPOTENT
# ---------------------------------------------------------------------

def test_supersession_retry_returns_same_version(
    tmp_path,
):
    m = _seed(tmp_path)

    old = _active_old_belief(m)

    _, _, proposal_a = _counterepisode(
        m,
        old.object_id,
        label="A",
        propose_replacement=True,
    )

    _, _, proposal_b = _counterepisode(
        m,
        old.object_id,
        label="B",
        propose_replacement=True,
    )

    m.contest_belief_if_supported(
        old.object_id
    )

    replacement = m.promote_lesson_if_supported(
        proposal_b.object_id
    )

    first = (
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
        )
    )

    second = (
        m.supersede_belief_if_supported(
            old.object_id,
            replacement.object_id,
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

    versions = _belief_versions(
        m,
        old.object_id,
    )

    # v1 active
    # v2 contested
    # v3 superseded
    assert [
        version.version
        for version in versions
    ] == [
        1,
        2,
        3,
    ]
