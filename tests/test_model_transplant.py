from agent_cycle import (
    reason_over_context,
)

from mnexa_seed import (
    MnexaSeed,
)


TASK = (
    "Payments API returns 429. "
    "What should the agent do?"
)

ENTITIES = (
    "api:payments",
)

LESSON = (
    "When Payments API returns 429, "
    "retry with exponential backoff."
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
    db_path,
):
    return MnexaSeed(
        db_path,
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )


# ---------------------------------------------------------------------
# MODEL A
#
# Model A has no durable local intelligence.
#
# It repeatedly makes the bad decision.
# After reality shows the decision was bad, its lesson-builder proposes
# the durable lesson that MNEXA may eventually promote.
# ---------------------------------------------------------------------

class ModelA:
    def __init__(
        self,
    ):
        self.decision_calls = []
        self.lesson_calls = []

    def decide(
        self,
        prompt,
    ):
        self.decision_calls.append(
            prompt
        )

        return (
            "Retry immediately "
            "with zero delay."
        )

    def propose_lesson(
        self,
        evidence,
    ):
        self.lesson_calls.append(
            evidence
        )

        return LESSON


# ---------------------------------------------------------------------
# MODEL B
#
# Model B begins with ZERO local memory.
#
# Its behavior depends only on the frozen context supplied to it.
#
# With no inherited MNEXA intelligence:
#     it makes the naive decision.
#
# With the lesson supplied by MNEXA:
#     it makes the improved decision.
# ---------------------------------------------------------------------

class ModelB:
    def __init__(
        self,
    ):
        self.calls = []

    def decide(
        self,
        prompt,
    ):
        self.calls.append(
            prompt
        )

        if (
            "exponential backoff"
            in
            prompt.lower()
        ):
            return (
                "Retry with "
                "exponential backoff."
            )

        return (
            "Retry immediately "
            "with zero delay."
        )


def _run_model_a_episode(
    m,
    model_a,
    *,
    outcome_text,
):
    # -------------------------------------------------------------
    # MNEXA freezes whatever intelligence currently exists.
    # -------------------------------------------------------------

    context = (
        m.prepare_context(
            TASK,
            ENTITIES,
        )
    )

    # -------------------------------------------------------------
    # Model A reasons OUTSIDE MNEXA.
    # -------------------------------------------------------------

    agent_decision = (
        reason_over_context(
            context=context,

            task=TASK,

            reasoner=(
                model_a.decide
            ),
        )
    )

    # -------------------------------------------------------------
    # MNEXA records what Model A actually decided.
    # -------------------------------------------------------------

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

            entities=ENTITIES,
        )
    )

    # -------------------------------------------------------------
    # Reality provides the outcome.
    # -------------------------------------------------------------

    m.observe_outcome(
        recorded.record_id,

        outcome_text,

        success=False,
    )

    # -------------------------------------------------------------
    # Model A proposes meaning.
    #
    # Proposal is NOT automatically knowledge.
    # -------------------------------------------------------------

    proposal = (
        m.propose_lesson(
            recorded.record_id,

            model_a.propose_lesson,
        )
    )

    return (
        recorded,
        proposal,
    )


def _train_mnexa_while_model_a_is_present(
    db_path,
):
    m = _seed(
        db_path
    )

    model_a = (
        ModelA()
    )

    # -------------------------------------------------------------
    # Experience 1
    # -------------------------------------------------------------

    _, proposal_a = (
        _run_model_a_episode(
            m,
            model_a,

            outcome_text=(
                "Zero-delay retry caused "
                "request flooding."
            ),
        )
    )

    # One experience must not yet create the belief.
    assert (
        m.promote_lesson_if_supported(
            proposal_a.object_id
        )
        is None
    )

    # -------------------------------------------------------------
    # Experience 2
    # -------------------------------------------------------------

    _, proposal_b = (
        _run_model_a_episode(
            m,
            model_a,

            outcome_text=(
                "Immediate retry again "
                "amplified the rate limit."
            ),
        )
    )

    # -------------------------------------------------------------
    # Two independent experiences establish the durable belief.
    # -------------------------------------------------------------

    belief = (
        m.promote_lesson_if_supported(
            proposal_b.object_id
        )
    )

    assert belief is not None

    assert (
        belief.text
        ==
        LESSON
    )

    assert (
        belief.version
        ==
        1
    )

    belief_id = (
        belief.object_id
    )

    final_watermark = (
        m.watermark()
    )

    # -------------------------------------------------------------
    # Simulate Model A disappearing.
    #
    # The database survives.
    # The model object does not participate in the next phase.
    # -------------------------------------------------------------

    m.close()

    return {
        "belief_id": (
            belief_id
        ),

        "watermark": (
            final_watermark
        ),

        "model_a_decision_calls": (
            len(
                model_a.decision_calls
            )
        ),

        "model_a_lesson_calls": (
            len(
                model_a.lesson_calls
            )
        ),
    }


# ---------------------------------------------------------------------
# GRAND TRANSPLANT TEST
# ---------------------------------------------------------------------

def test_fresh_model_b_inherits_intelligence_accumulated_with_model_a(
    tmp_path,
):
    shared_db = (
        tmp_path
        /
        "shared_mnexa.db"
    )

    cold_db = (
        tmp_path
        /
        "cold_mnexa.db"
    )

    # =============================================================
    # PHASE 1
    #
    # Model A lives through experiences.
    # MNEXA learns while A is present.
    # =============================================================

    training = (
        _train_mnexa_while_model_a_is_present(
            shared_db
        )
    )

    assert (
        training[
            "model_a_decision_calls"
        ]
        ==
        2
    )

    assert (
        training[
            "model_a_lesson_calls"
        ]
        ==
        2
    )

    # =============================================================
    # PHASE 2 — CONTROL
    #
    # Fresh Model B + EMPTY MNEXA.
    #
    # This establishes what B does WITHOUT inherited intelligence.
    # =============================================================

    cold_mnexa = (
        _seed(
            cold_db
        )
    )

    cold_model_b = (
        ModelB()
    )

    assert (
        cold_model_b.calls
        ==
        []
    )

    cold_context = (
        cold_mnexa.prepare_context(
            TASK,
            ENTITIES,
        )
    )

    assert (
        cold_context
        .selected_memory_ids
        ==
        ()
    )

    assert (
        "exponential backoff"
        not in
        cold_context
        .context_text
        .lower()
    )

    cold_decision = (
        reason_over_context(
            context=cold_context,

            task=TASK,

            reasoner=(
                cold_model_b.decide
            ),
        )
    )

    assert (
        cold_decision.decision
        ==
        (
            "Retry immediately "
            "with zero delay."
        )
    )

    cold_mnexa.close()

    # =============================================================
    # PHASE 3 — TRANSPLANT
    #
    # Fresh Model B instance.
    #
    # Model A is gone.
    #
    # We reopen the SAME MNEXA database that accumulated intelligence
    # while Model A existed.
    # =============================================================

    transplanted_mnexa = (
        _seed(
            shared_db
        )
    )

    transplanted_model_b = (
        ModelB()
    )

    # This is a genuinely fresh reasoner instance.
    assert (
        transplanted_model_b
        is not
        cold_model_b
    )

    assert (
        type(
            transplanted_model_b
        )
        is
        type(
            cold_model_b
        )
    )

    assert (
        transplanted_model_b.calls
        ==
        []
    )

    # =============================================================
    # MNEXA now retrieves intelligence created before Model B existed.
    # =============================================================

    transplanted_context = (
        transplanted_mnexa
        .prepare_context(
            TASK,
            ENTITIES,
        )
    )

    assert any(
        training[
            "belief_id"
        ]
        in mem_id

        for mem_id
        in transplanted_context
        .selected_memory_ids
    )

    assert (
        "exponential backoff"
        in
        transplanted_context
        .context_text
        .lower()
    )

    # The frozen context was built from persistent state that existed
    # before this new Model B instance reasoned.
    assert (
        transplanted_context.watermark
        >=
        training[
            "watermark"
        ]
    )

    # =============================================================
    # Same Model-B logic.
    #
    # Only meaningful difference from the cold control:
    # MNEXA contains accumulated intelligence.
    # =============================================================

    transplanted_decision = (
        reason_over_context(
            context=(
                transplanted_context
            ),

            task=TASK,

            reasoner=(
                transplanted_model_b
                .decide
            ),
        )
    )

    assert (
        transplanted_decision.decision
        ==
        (
            "Retry with "
            "exponential backoff."
        )
    )

    # =============================================================
    # CAUSAL CONTRAST
    # =============================================================

    assert (
        cold_decision.decision
        !=
        transplanted_decision.decision
    )

    assert (
        "exponential backoff"
        not in
        cold_model_b.calls[0]
        .lower()
    )

    assert (
        "exponential backoff"
        in
        transplanted_model_b.calls[0]
        .lower()
    )

    transplanted_mnexa.close()
