from mnexa_seed import MnexaSeed


class FakeEmbedder:
    vocab = ("429", "retry", "backoff", "payments")

    def embed(self, text):
        words = text.lower().split()
        return [
            float(sum(token in word for word in words))
            for token in self.vocab
        ]


class WordMeter:
    name = "word-meter-v1"

    def count(self, text):
        return len(text.split())


def reasoner(task, context):
    if "exponential backoff" in context.lower():
        return "Retry with exponential backoff."

    return "Call once and fail on 429."


def consolidator(evidence):
    assert "429" in evidence

    return (
        "When an API returns 429, "
        "retry with exponential backoff."
    )


def test_seed_grows_from_experience(tmp_path):
    db = tmp_path / "mnexa.db"

    m = MnexaSeed(
        db,
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    # First encounter: MNEXA has not learned anything yet.
    first = m.decide(
        "Payments API returns 429",
        ("api:payments",),
        reasoner,
    )

    assert "fail" in first.text.lower()

    # Reality tells MNEXA what happened.
    m.observe_outcome(
        first.record_id,
        "Request failed with HTTP 429",
        success=False,
    )

    # MNEXA converts experience + outcome into durable knowledge.
    m.consolidate(
        first.record_id,
        consolidator,
    )

    # Same class of problem appears again.
    second = m.decide(
        "Payments API returns 429",
        ("api:payments",),
        reasoner,
    )

    # This time previous experience changes the decision.
    assert "exponential backoff" in second.text.lower()

    assert any(
        "exponential backoff" in segment.lower()
        for segment in second.memory_segments
    )


def test_seed_persists_and_uses_three_retrieval_routes(tmp_path):
    db = tmp_path / "mnexa.db"

    m = MnexaSeed(
        db,
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    m.learn(
        "When an API returns 429, retry with exponential backoff.",
        ("api:payments",),
        (),
    )

    m.close()

    # New process / new session.
    m = MnexaSeed(
        db,
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    hit = m.recall(
        "payments API 429 retry",
        ("api:payments",),
        top_k=1,
    )[0]

    assert {
        "semantic",
        "lexical",
        "entity",
    }.issubset(hit.channels)
