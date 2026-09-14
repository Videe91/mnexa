import sqlite3

import pytest

import mnexa_seed


class FakeEmbedder:
    vocab = (
        "retry",
        "payments",
        "429",
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
    path,
):
    return mnexa_seed.MnexaSeed(
        path,
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )


def _commit_count(
    m,
):
    return int(
        m.db.execute(
            """
            SELECT COUNT(*) n
            FROM commits
            """
        )
        .fetchone()["n"]
    )


def _idempotency_count(
    m,
):
    return int(
        m.db.execute(
            """
            SELECT COUNT(*) n
            FROM write_idempotency
            """
        )
        .fetchone()["n"]
    )


def test_same_key_same_event_returns_original_commit(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.event(
            "ObservationRecorded",
            "Payments API returned 429",
            ("api:payments",),
            metadata={
                "source": "runtime",
            },
            idempotency_key=(
                "capture:payments:001"
            ),
        )
    )

    watermark_after_first = (
        m.watermark()
    )

    second = (
        m.event(
            "ObservationRecorded",
            "Payments API returned 429",
            ("api:payments",),
            metadata={
                "source": "runtime",
            },
            idempotency_key=(
                "capture:payments:001"
            ),
        )
    )

    assert (
        second.object_id
        ==
        first.object_id
    )

    assert (
        second.seq
        ==
        first.seq
    )

    assert (
        m.watermark()
        ==
        watermark_after_first
    )

    assert (
        _commit_count(m)
        == 1
    )

    assert (
        _idempotency_count(m)
        == 1
    )


def test_metadata_key_order_does_not_change_request_identity(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.event(
            "RuntimeEvidence",
            "same evidence",
            metadata={
                "a": 1,
                "b": 2,
            },
            idempotency_key=(
                "event:canonical:1"
            ),
        )
    )

    second = (
        m.event(
            "RuntimeEvidence",
            "same evidence",
            metadata={
                "b": 2,
                "a": 1,
            },
            idempotency_key=(
                "event:canonical:1"
            ),
        )
    )

    assert (
        first.seq
        ==
        second.seq
    )

    assert (
        _commit_count(m)
        == 1
    )


def test_same_key_different_request_is_rejected_without_mutation(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.event(
            "ObservationRecorded",
            "Payments API returned 429",
            ("api:payments",),
            idempotency_key=(
                "capture:payments:002"
            ),
        )
    )

    watermark_before_conflict = (
        m.watermark()
    )

    with pytest.raises(
        Exception
    ) as exc:

        m.event(
            "ObservationRecorded",
            "Payments API returned 500",
            ("api:payments",),
            idempotency_key=(
                "capture:payments:002"
            ),
        )

    assert (
        type(
            exc.value
        ).__name__
        ==
        "IdempotencyConflict"
    )

    assert (
        m.watermark()
        ==
        watermark_before_conflict
        ==
        first.seq
    )

    assert (
        _commit_count(m)
        == 1
    )

    assert (
        _idempotency_count(m)
        == 1
    )


def test_different_keys_preserve_identical_real_events(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.event(
            "ObservationRecorded",
            "identical observation",
            ("sensor:7",),
            idempotency_key=(
                "sensor:7:reading:1"
            ),
        )
    )

    second = (
        m.event(
            "ObservationRecorded",
            "identical observation",
            ("sensor:7",),
            idempotency_key=(
                "sensor:7:reading:2"
            ),
        )
    )

    assert (
        first.object_id
        !=
        second.object_id
    )

    assert (
        first.seq
        !=
        second.seq
    )

    assert (
        _commit_count(m)
        == 2
    )

    assert (
        _idempotency_count(m)
        == 2
    )


def test_legacy_no_key_calls_remain_independent_writes(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.event(
            "ObservationRecorded",
            "same payload",
        )
    )

    second = (
        m.event(
            "ObservationRecorded",
            "same payload",
        )
    )

    assert (
        first.object_id
        !=
        second.object_id
    )

    assert (
        first.seq
        !=
        second.seq
    )

    assert (
        _commit_count(m)
        == 2
    )

    assert (
        _idempotency_count(m)
        == 0
    )


def test_retry_survives_database_restart(
    tmp_path,
):
    db = (
        tmp_path
        /
        "mnexa.db"
    )

    m = _seed(
        db
    )

    first = (
        m.event(
            "ObservationRecorded",
            "Payments API returned 429",
            ("api:payments",),
            idempotency_key=(
                "restart-safe:001"
            ),
        )
    )

    first_seq = (
        first.seq
    )

    first_object_id = (
        first.object_id
    )

    m.close()

    m = _seed(
        db
    )

    second = (
        m.event(
            "ObservationRecorded",
            "Payments API returned 429",
            ("api:payments",),
            idempotency_key=(
                "restart-safe:001"
            ),
        )
    )

    assert (
        second.seq
        ==
        first_seq
    )

    assert (
        second.object_id
        ==
        first_object_id
    )

    assert (
        _commit_count(m)
        == 1
    )

    assert (
        _idempotency_count(m)
        == 1
    )


def test_failed_atomic_write_exposes_neither_half(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    m.db.executescript(
        """
        CREATE TRIGGER force_idempotency_failure
        BEFORE INSERT ON write_idempotency
        BEGIN
            SELECT RAISE(
                ABORT,
                'forced idempotency failure'
            );
        END;
        """
    )

    with pytest.raises(
        sqlite3.DatabaseError
    ):

        m.event(
            "ObservationRecorded",
            "this must roll back",
            idempotency_key=(
                "atomicity:001"
            ),
        )

    assert (
        _commit_count(m)
        == 0
    )

    assert (
        _idempotency_count(m)
        == 0
    )

    assert (
        m.watermark()
        == 0
    )


def test_generated_interpretation_identity_is_stable_on_retry(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.learn(
            (
                "When Payments API returns "
                "429 use backoff."
            ),
            ("api:payments",),
            (),
            idempotency_key=(
                "lesson:payments:001"
            ),
        )
    )

    second = (
        m.learn(
            (
                "When Payments API returns "
                "429 use backoff."
            ),
            ("api:payments",),
            (),
            idempotency_key=(
                "lesson:payments:001"
            ),
        )
    )

    assert (
        second.object_id
        ==
        first.object_id
    )

    assert (
        second.version
        ==
        first.version
        ==
        1
    )

    assert (
        second.seq
        ==
        first.seq
    )

    assert (
        _commit_count(m)
        == 1
    )


def test_observation_capture_can_be_retried_safely(
    tmp_path,
):
    m = _seed(
        tmp_path / "mnexa.db"
    )

    first = (
        m.observe(
            "Payments API returned 429",
            ("api:payments",),
            idempotency_key=(
                "observation:001"
            ),
        )
    )

    second = (
        m.observe(
            "Payments API returned 429",
            ("api:payments",),
            idempotency_key=(
                "observation:001"
            ),
        )
    )

    assert (
        first.seq
        ==
        second.seq
    )

    assert (
        first.object_id
        ==
        second.object_id
    )

    assert (
        _commit_count(m)
        == 1
    )
