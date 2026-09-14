from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence

import hashlib
import json
import math
import re
import sqlite3
import uuid

from mnexa_context import (
    AssembledRecall,
    ContextFrame,
    ContextPreparer,
)


# ---------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------


class Embedder(Protocol):
    def embed(self, text: str) -> Sequence[float]:
        ...


class Meter(Protocol):
    name: str

    def count(self, text: str) -> int:
        ...


# ---------------------------------------------------------------------
# Read models
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    seq: int
    plane: str

    object_id: str
    version: int | None

    kind: str
    text: str

    entities: tuple[str, ...]
    refs: tuple[str, ...]

    embedding: tuple[float, ...] | None
    metadata: dict


@dataclass(frozen=True)
class Hit:
    item: Item
    channels: frozenset[str]
    score: float


@dataclass(frozen=True)
class Decision:
    record_id: str
    watermark: int

    text: str

    memory_segments: tuple[str, ...]


class IdempotencyConflict(RuntimeError):
    """
    One logical-write idempotency key was reused for a different request.
    """

    pass


# ---------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------


def _tokens(text: str) -> set[str]:
    return {
        x.lower()
        for x in re.findall(
            r"[A-Za-z0-9_:\-.]+",
            text,
        )
    }


def _cos(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(
        x * y
        for x, y in zip(a, b)
    )

    na = math.sqrt(
        sum(x * x for x in a)
    )

    nb = math.sqrt(
        sum(y * y for y in b)
    )

    if na == 0 or nb == 0:
        return 0.0

    return dot / (na * nb)


# ---------------------------------------------------------------------
# MNEXA Seed
# ---------------------------------------------------------------------


class MnexaSeed:
    """
    Smallest living MNEXA loop:

        experience
            ↓
        persistent memory
            ↓
        recall
            ↓
        decision
            ↓
        outcome
            ↓
        consolidation
            ↓
        durable lesson
            ↓
        better future recall
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        embedder: Embedder | None,
        meter: Meter,
    ):
        self.embedder = embedder
        self.meter = meter

        self.db = sqlite3.connect(
            str(db_path)
        )

        self.db.row_factory = sqlite3.Row

        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS commits(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,

                plane TEXT NOT NULL,

                object_id TEXT NOT NULL,
                version INTEGER,

                kind TEXT NOT NULL,
                text TEXT NOT NULL,

                entities TEXT NOT NULL,
                refs TEXT NOT NULL,

                embedding TEXT,

                metadata TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS write_idempotency(
                idempotency_key TEXT PRIMARY KEY,

                request_sha256 TEXT NOT NULL,

                commit_seq INTEGER NOT NULL,
                commit_object_id TEXT NOT NULL
            );


            CREATE UNIQUE INDEX IF NOT EXISTS uq_hist
            ON commits(object_id)
            WHERE plane='historical';


            CREATE UNIQUE INDEX IF NOT EXISTS uq_interp
            ON commits(object_id, version)
            WHERE plane='interpretive';
            """
        )

        self.db.commit()

    # -----------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------

    def close(self):
        self.db.close()

    # -----------------------------------------------------------------
    # Durable knowledge watermark
    # -----------------------------------------------------------------

    def watermark(self) -> int:
        row = self.db.execute(
            """
            SELECT
                COALESCE(MAX(seq), 0) n
            FROM commits
            """
        ).fetchone()

        return int(row["n"])

    # -----------------------------------------------------------------
    # Append-only commit
    # -----------------------------------------------------------------
    # ADR-0018 logical-write identity
    # -----------------------------------------------------------------

    @staticmethod
    def _normalize_idempotency_key(
        idempotency_key,
    ):
        if idempotency_key is None:
            return None

        key = str(
            idempotency_key
        ).strip()

        if not key:
            raise ValueError(
                "idempotency_key may not be empty"
            )

        return key

    @staticmethod
    def _canonical_request_sha256(
        *,
        plane,
        kind,
        text,
        entities,
        refs,
        metadata,
        searchable,
        requested_object_id=None,
    ):
        """
        Fingerprint caller-controlled logical-write meaning.

        Deliberately excludes:

        - generated object IDs;
        - generated interpretation versions;
        - commit sequence;
        - generated embeddings.

        If the caller explicitly selected an interpretation object,
        requested_object_id carries that intent.
        """

        payload = {
            "plane": (
                plane
            ),

            "kind": (
                kind
            ),

            "text": (
                text
            ),

            "entities": list(
                entities
            ),

            "refs": list(
                refs
            ),

            "metadata": (
                metadata
            ),

            "searchable": bool(
                searchable
            ),

            "requested_object_id": (
                requested_object_id
            ),
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )

        return (
            hashlib
            .sha256(
                encoded
            )
            .hexdigest()
        )

    def _append(
        self,
        plane,
        object_id,
        version,
        kind,
        text,
        entities=(),
        refs=(),
        metadata=None,
        searchable=False,
        *,
        idempotency_key=None,
        requested_object_id=None,
    ):
        entities = tuple(
            entities
        )

        refs = tuple(
            refs
        )

        metadata = dict(
            metadata
            or {}
        )

        idempotency_key = (
            self._normalize_idempotency_key(
                idempotency_key
            )
        )

        request_sha256 = (
            self._canonical_request_sha256(
                plane=plane,
                kind=kind,
                text=text,
                entities=entities,
                refs=refs,
                metadata=metadata,
                searchable=searchable,
                requested_object_id=(
                    requested_object_id
                ),
            )
        )

        # Embedding generation happens before taking the SQLite write
        # lock. If embedding fails, nothing durable has started.
        vector = None

        if searchable and self.embedder:
            vector = (
                self.embedder.embed(
                    text
                )
            )

        values = (
            plane,
            object_id,
            version,
            kind,
            text,

            json.dumps(
                entities
            ),

            json.dumps(
                refs
            ),

            (
                json.dumps(
                    list(
                        vector
                    )
                )
                if vector is not None
                else None
            ),

            json.dumps(
                metadata,
                sort_keys=True,
            ),
        )

        def insert_commit():
            return self.db.execute(
                """
                INSERT INTO commits(
                    plane,
                    object_id,
                    version,
                    kind,
                    text,
                    entities,
                    refs,
                    embedding,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )

        # -------------------------------------------------------------
        # Legacy/non-retryable path.
        #
        # No explicit key means this call represents a new independent
        # historical write, preserving existing behavior.
        # -------------------------------------------------------------

        if idempotency_key is None:

            with self.db:
                cur = (
                    insert_commit()
                )

            row = self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE seq=?
                """,
                (
                    cur.lastrowid,
                ),
            ).fetchone()

            return self._item(
                row
            )

        # -------------------------------------------------------------
        # ADR-0018 retryable path.
        #
        # BEGIN IMMEDIATE obtains SQLite's write reservation before
        # examining the idempotency mapping. This keeps:
        #
        #     check key
        #     append commit
        #     register key
        #
        # inside one serialized transaction.
        # -------------------------------------------------------------

        self.db.execute(
            "BEGIN IMMEDIATE"
        )

        try:
            existing = (
                self.db.execute(
                    """
                    SELECT
                        idempotency_key,
                        request_sha256,
                        commit_seq,
                        commit_object_id

                    FROM write_idempotency

                    WHERE idempotency_key=?
                    """,
                    (
                        idempotency_key,
                    ),
                )
                .fetchone()
            )

            # ---------------------------------------------------------
            # Retry of a known logical write.
            # ---------------------------------------------------------

            if existing is not None:

                if (
                    existing[
                        "request_sha256"
                    ]
                    !=
                    request_sha256
                ):
                    raise IdempotencyConflict(
                        "idempotency key "
                        f"{idempotency_key!r} "
                        "was already committed "
                        "for a different request"
                    )

                row = (
                    self.db.execute(
                        """
                        SELECT *
                        FROM commits
                        WHERE seq=?
                        """,
                        (
                            existing[
                                "commit_seq"
                            ],
                        ),
                    )
                    .fetchone()
                )

                if row is None:
                    raise RuntimeError(
                        "idempotency mapping points "
                        "to a missing commit"
                    )

                if (
                    row["object_id"]
                    !=
                    existing[
                        "commit_object_id"
                    ]
                ):
                    raise RuntimeError(
                        "idempotency mapping does not "
                        "match committed object identity"
                    )

                result = (
                    self._item(
                        row
                    )
                )

                self.db.commit()

                return result

            # ---------------------------------------------------------
            # First submission of this logical write.
            # ---------------------------------------------------------

            cur = (
                insert_commit()
            )

            commit_seq = int(
                cur.lastrowid
            )

            self.db.execute(
                """
                INSERT INTO write_idempotency(
                    idempotency_key,
                    request_sha256,
                    commit_seq,
                    commit_object_id
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    idempotency_key,
                    request_sha256,
                    commit_seq,
                    object_id,
                ),
            )

            row = (
                self.db.execute(
                    """
                    SELECT *
                    FROM commits
                    WHERE seq=?
                    """,
                    (
                        commit_seq,
                    ),
                )
                .fetchone()
            )

            result = (
                self._item(
                    row
                )
            )

            self.db.commit()

            return result

        except BaseException:
            self.db.rollback()
            raise

    def _item(
        self,
        row,
    ):
        embedding = (
            json.loads(
                row["embedding"]
            )
            if row["embedding"]
            else None
        )

        return Item(
            seq=row["seq"],
            plane=row["plane"],

            object_id=row["object_id"],
            version=row["version"],

            kind=row["kind"],
            text=row["text"],

            entities=tuple(
                json.loads(
                    row["entities"]
                )
            ),

            refs=tuple(
                json.loads(
                    row["refs"]
                )
            ),

            embedding=(
                tuple(embedding)
                if embedding
                else None
            ),

            metadata=json.loads(
                row["metadata"]
            ),
        )

    # -----------------------------------------------------------------
    # EXPERIENCE
    # -----------------------------------------------------------------

    def observe(
        self,
        text: str,
        entities=(),
        *,
        idempotency_key=None,
    ):
        return self._append(
            "historical",

            f"r_{uuid.uuid4().hex}",
            None,

            "ObservationRecorded",

            text,

            entities,

            searchable=True,

            idempotency_key=(
                idempotency_key
            ),
        )

    # -----------------------------------------------------------------
    # HISTORICAL EVENT
    # -----------------------------------------------------------------

    def event(
        self,
        kind: str,
        text: str,
        entities=(),
        refs=(),
        metadata=None,
        *,
        idempotency_key=None,
    ):
        return self._append(
            "historical",

            f"r_{uuid.uuid4().hex}",
            None,

            kind,

            text,

            entities,
            refs,

            metadata,

            False,

            idempotency_key=(
                idempotency_key
            ),
        )

    # -----------------------------------------------------------------
    # INTERPRETATION / LEARNING
    # -----------------------------------------------------------------

    def learn(
        self,
        text: str,
        entities=(),
        source_record_ids=(),
        object_id=None,
        *,
        idempotency_key=None,
    ):
        # Preserve whether identity was caller-selected.
        #
        # A generated UUID must NOT make an idempotent retry appear to
        # be a different logical request.
        requested_object_id = (
            object_id
        )

        object_id = (
            object_id
            or
            f"i_{uuid.uuid4().hex}"
        )

        row = self.db.execute(
            """
            SELECT
                COALESCE(MAX(version), 0) v

            FROM commits

            WHERE
                plane='interpretive'
                AND object_id=?
            """,
            (
                object_id,
            ),
        ).fetchone()

        version = (
            int(
                row["v"]
            )
            +
            1
        )

        return self._append(
            "interpretive",

            object_id,
            version,

            "belief",

            text,

            entities,
            source_record_ids,

            searchable=True,

            idempotency_key=(
                idempotency_key
            ),

            requested_object_id=(
                requested_object_id
            ),
        )

    # -----------------------------------------------------------------
    # MEMORY VIEW AS_OF(N)
    # -----------------------------------------------------------------

    def _searchable_as_of(
        self,
        n: int,
    ):
        # Raw experience remains available.
        historical = self.db.execute(
            """
            SELECT *
            FROM commits
            WHERE
                plane='historical'
                AND kind='ObservationRecorded'
                AND seq<=?
            """,
            (
                n,
            ),
        ).fetchall()

        # For interpretations, normal recall sees
        # only the newest version AS_OF(N).
        heads = self.db.execute(
            """
            SELECT c.*

            FROM commits c

            JOIN (
                SELECT
                    object_id,
                    MAX(version) v

                FROM commits

                WHERE
                    plane='interpretive'
                    AND seq<=?

                GROUP BY object_id
            ) h

            ON
                c.object_id=h.object_id
                AND c.version=h.v

            WHERE
                c.plane='interpretive'
                AND c.seq<=?
            """,
            (
                n,
                n,
            ),
        ).fetchall()

        return [
            self._item(x)
            for x in (
                *historical,
                *heads,
            )
        ]

    # -----------------------------------------------------------------
    # RECALL
    # -----------------------------------------------------------------

    def recall(
        self,
        query: str,
        entities=(),
        *,
        top_k=5,
        as_of=None,
    ):
        watermark = (
            self.watermark()
            if as_of is None
            else as_of
        )

        items = self._searchable_as_of(
            watermark
        )

        rankings = {}

        # -------------------------------------------------------------
        # Route 1: Semantic
        # -------------------------------------------------------------

        if self.embedder:
            qv = self.embedder.embed(
                query
            )

            semantic = sorted(
                (
                    (
                        item,
                        _cos(
                            qv,
                            item.embedding,
                        ),
                    )
                    for item in items
                ),
                key=lambda pair: pair[1],
                reverse=True,
            )

            rankings["semantic"] = [
                item
                for item, score in semantic
                if score > 0
            ]

        # -------------------------------------------------------------
        # Route 2: Lexical / Exact
        # -------------------------------------------------------------

        q = _tokens(query)

        lexical = sorted(
            (
                (
                    item,
                    (
                        len(
                            q
                            & _tokens(
                                item.text
                            )
                        )
                        /
                        max(
                            1,
                            len(
                                q
                                | _tokens(
                                    item.text
                                )
                            ),
                        )
                    ),
                )
                for item in items
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )

        rankings["lexical"] = [
            item
            for item, score in lexical
            if score > 0
        ]

        # -------------------------------------------------------------
        # Route 3: Entity
        # -------------------------------------------------------------

        requested_entities = set(
            entities
        )

        if requested_entities:
            rankings["entity"] = [
                item
                for item in items
                if (
                    requested_entities
                    & set(item.entities)
                )
            ]

        # -------------------------------------------------------------
        # Merge channels
        #
        # Reciprocal Rank Fusion means unlike raw scores
        # never need to pretend they are directly comparable.
        # -------------------------------------------------------------

        merged = {}

        for (
            channel,
            ranked,
        ) in rankings.items():

            for rank, item in enumerate(
                ranked[:10],
                1,
            ):
                key = (
                    item.object_id,
                    item.version,
                )

                slot = merged.setdefault(
                    key,
                    [
                        item,
                        set(),
                        0.0,
                    ],
                )

                slot[1].add(
                    channel
                )

                slot[2] += (
                    1
                    /
                    (60 + rank)
                )

        out = [
            Hit(
                item=value[0],

                channels=frozenset(
                    value[1]
                ),

                score=value[2],
            )
            for value in merged.values()
        ]

        return sorted(
            out,
            key=lambda hit: (
                hit.score,
                hit.item.seq,
            ),
            reverse=True,
        )[:top_k]

    # -----------------------------------------------------------------
    # ADR-0017 CANONICAL CONTEXT BOUNDARY
    # -----------------------------------------------------------------

    def prepare_context(
        self,
        recall_intent: str,
        entities=(),
        memory_budget=256,
    ) -> ContextFrame:
        """
        Canonical MNEXA-side preparation path.

        MNEXA:
            freezes the memory watermark
            -> recalls
            -> assembles context
            -> records ContextAssembled
            -> returns immutable ContextFrame

        No model reasoning occurs here.
        """

        entities = tuple(
            entities
        )

        if memory_budget < 0:
            raise ValueError(
                "memory_budget must be >= 0"
            )

        def freeze_watermark():
            return self.watermark()

        def recall(
            query,
            watermark,
        ):
            return self.recall(
                query,
                entities,
                top_k=12,
                as_of=watermark,
            )

        def assemble(
            hits,
            watermark,
        ):
            segments = []
            selected_memory_ids = []

            left = (
                memory_budget
            )

            for hit in hits:

                version_suffix = (
                    f":v{hit.item.version}"
                    if hit.item.version
                    is not None
                    else ""
                )

                memory_id = (
                    f"{hit.item.plane}:"
                    f"{hit.item.object_id}"
                    f"{version_suffix}"
                )

                segment = (
                    f"[{memory_id}] "
                    f"{hit.item.text}"
                )

                size = (
                    self.meter.count(
                        segment
                    )
                )

                if size > left:
                    continue

                segments.append(
                    segment
                )

                selected_memory_ids.append(
                    memory_id
                )

                left -= size

            return AssembledRecall(
                selected_memory_ids=(
                    tuple(
                        selected_memory_ids
                    )
                ),

                context_text=(
                    "\n".join(
                        segments
                    )
                ),

                metadata={
                    "watermark": (
                        watermark
                    ),

                    "segments": (
                        tuple(
                            segments
                        )
                    ),

                    "meter": (
                        self.meter.name
                    ),

                    "entities": (
                        entities
                    ),

                    "memory_budget": (
                        memory_budget
                    ),
                },
            )

        def record_context(
            frame,
        ):
            context_event = (
                self.event(
                    "ContextAssembled",

                    frame.context_text,

                    entities,

                    metadata={
                        "watermark": (
                            frame.watermark
                        ),

                        "segments": (
                            tuple(
                                frame
                                .metadata()
                                .get(
                                    "segments",
                                    (),
                                )
                            )
                        ),

                        "meter": (
                            self.meter.name
                        ),

                        "selected_memory_ids": (
                            frame
                            .selected_memory_ids
                        ),

                        "recall_intent": (
                            frame
                            .recall_intent
                        ),

                        "context_evidence_sha256": (
                            frame
                            .evidence_sha256
                        ),
                    },
                )
            )

            return (
                context_event.object_id
            )

        preparer = (
            ContextPreparer(
                freeze_watermark=(
                    freeze_watermark
                ),

                recall=(
                    recall
                ),

                assemble=(
                    assemble
                ),

                record_context=(
                    record_context
                ),
            )
        )

        return preparer.prepare(
            recall_intent=(
                recall_intent
            )
        )

    # -----------------------------------------------------------------
    # EXTERNAL DECISION INGESTION
    # -----------------------------------------------------------------

    def record_external_decision(
        self,
        *,
        context: ContextFrame,
        decision_text: str,
        context_evidence_sha256: str,
        entities=(),
        decision_kind="task_response",
        idempotency_key=None,
    ) -> Decision:
        """
        Record a decision produced outside MNEXA.

        MNEXA does not reason here.

        It verifies which immutable ContextFrame the external decision
        consumed and records the resulting DecisionMade event.
        """

        if not isinstance(
            context,
            ContextFrame,
        ):
            raise TypeError(
                "context must be ContextFrame"
            )

        if not context.verify_integrity():
            raise ValueError(
                "ContextFrame integrity "
                "verification failed"
            )

        if (
            context_evidence_sha256
            !=
            context.evidence_sha256
        ):
            raise ValueError(
                "context evidence hash "
                "does not match ContextFrame"
            )

        context_event_id = (
            context
            .context_assembled_event_id
        )

        if not context_event_id:
            raise ValueError(
                "recorded ContextAssembled "
                "event is required"
            )

        context_row = (
            self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE object_id=?
                """,
                (
                    context_event_id,
                ),
            )
            .fetchone()
        )

        if (
            not context_row
            or
            context_row["kind"]
            !=
            "ContextAssembled"
        ):
            raise ValueError(
                "recorded ContextAssembled "
                "event is required"
            )

        recorded_context = (
            self._item(
                context_row
            )
        )

        recorded_hash = (
            recorded_context
            .metadata
            .get(
                "context_evidence_sha256"
            )
        )

        if (
            recorded_hash
            !=
            context.evidence_sha256
        ):
            raise ValueError(
                "recorded ContextAssembled "
                "event does not match "
                "ContextFrame evidence hash"
            )

        if (
            recorded_context.text
            !=
            context.context_text
        ):
            raise ValueError(
                "recorded ContextAssembled "
                "event does not match "
                "ContextFrame content"
            )

        recorded_watermark = (
            recorded_context
            .metadata
            .get(
                "watermark"
            )
        )

        if (
            recorded_watermark
            !=
            context.watermark
        ):
            raise ValueError(
                "recorded ContextAssembled "
                "event does not match "
                "ContextFrame watermark"
            )

        decision_text = str(
            decision_text
        ).strip()

        if not decision_text:
            raise ValueError(
                "decision_text may not "
                "be empty"
            )

        decision_kind = str(
            decision_kind
        ).strip()

        if not decision_kind:
            raise ValueError(
                "decision_kind may not "
                "be empty"
            )

        entities = tuple(
            entities
        )

        decision = (
            self.event(
                "DecisionMade",

                decision_text,

                entities,

                refs=(
                    context_event_id,
                ),

                metadata={
                    "watermark": (
                        context.watermark
                    ),

                    "decided_from": (
                        context_event_id
                    ),

                    "context_evidence_sha256": (
                        context
                        .evidence_sha256
                    ),

                    "decision_kind": (
                        decision_kind
                    ),

                    "reasoning_owner": (
                        "external"
                    ),
                },

                idempotency_key=(
                    idempotency_key
                ),
            )
        )

        context_metadata = (
            context.metadata()
        )

        return Decision(
            record_id=(
                decision.object_id
            ),

            watermark=(
                context.watermark
            ),

            text=(
                decision_text
            ),

            memory_segments=tuple(
                context_metadata.get(
                    "segments",
                    (),
                )
            ),
        )

    # -----------------------------------------------------------------
    # COGNITIVE CYCLE
    # -----------------------------------------------------------------

    def decide(
        self,
        task: str,
        entities,
        reasoner: Callable[
            [str, str],
            str,
        ],
        memory_budget=256,
    ):
        """
        LEGACY CONVENIENCE WRAPPER.

        This helper combines MNEXA context preparation with an externally
        supplied reasoner for backward compatibility with seed experiments.

        It is not the canonical MNEXA architecture (ADR-0017).

        New code must use:
            ContextPreparer.prepare(...)
        followed by model reasoning outside MNEXA.
        """
        # Freeze persistent memory for this cycle.
        n = self.watermark()

        hits = self.recall(
            task,
            entities,
            top_k=12,
            as_of=n,
        )

        segments = []

        left = memory_budget

        for hit in hits:
            version = (
                f":v{hit.item.version}"
                if hit.item.version
                else ""
            )

            segment = (
                f"["
                f"{hit.item.plane}:"
                f"{hit.item.object_id}"
                f"{version}"
                f"] "
                f"{hit.item.text}"
            )

            size = self.meter.count(
                segment
            )

            if size <= left:
                segments.append(
                    segment
                )

                left -= size

        context = "\n".join(
            segments
        )

        # Historical trace of exactly what MNEXA presented.
        ctx = self.event(
            "ContextAssembled",

            context,

            entities,

            metadata={
                "watermark": n,

                "segments": segments,

                "meter": (
                    self.meter.name
                ),
            },
        )

        # The reasoning model remains external/swappable.
        answer = reasoner(
            task,
            context,
        )

        decision = self.event(
            "DecisionMade",

            answer,

            entities,

            refs=(
                ctx.object_id,
            ),

            metadata={
                "watermark": n,

                "decided_from": (
                    ctx.object_id
                ),
            },
        )

        return Decision(
            record_id=(
                decision.object_id
            ),

            watermark=n,

            text=answer,

            memory_segments=tuple(
                segments
            ),
        )

    # -----------------------------------------------------------------
    # OUTCOME
    # -----------------------------------------------------------------

    def observe_outcome(
        self,
        decision_id: str,
        text: str,
        *,
        success: bool | None,
        idempotency_key=None,
    ):
        decision = self.db.execute(
            """
            SELECT *
            FROM commits
            WHERE object_id=?
            """,
            (
                decision_id,
            ),
        ).fetchone()

        if not decision:
            raise KeyError(
                decision_id
            )

        return self.event(
            "OutcomeObserved",

            text,

            tuple(
                json.loads(
                    decision["entities"]
                )
            ),

            refs=(
                decision_id,
            ),

            metadata={
                "success": success,

                "outcome_for": (
                    decision_id
                ),
            },

            idempotency_key=(
                idempotency_key
            ),
        )

    # -----------------------------------------------------------------
    # LESSON PROPOSAL
    # -----------------------------------------------------------------

    def propose_lesson(
        self,
        decision_id: str,
        lesson_builder: Callable[
            [str],
            str,
        ],
    ):
        """
        Produce a candidate lesson from historical decision/outcome
        evidence.

        The lesson is recorded as historical evidence only.

        It does NOT become searchable interpretive memory here.
        """

        drow = (
            self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE object_id=?
                """,
                (
                    decision_id,
                ),
            )
            .fetchone()
        )

        if not drow:
            raise KeyError(
                decision_id
            )

        decision = (
            self._item(
                drow
            )
        )

        outcomes = [
            self._item(
                row
            )

            for row
            in self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE kind='OutcomeObserved'
                ORDER BY seq
                """
            )

            if decision_id
            in json.loads(
                row["refs"]
            )
        ]

        if not outcomes:
            raise ValueError(
                "no observed outcome"
            )

        evidence = (
            "DECISION: "
            + decision.text
            + "\n"
            + "\n".join(
                (
                    "OUTCOME: "
                    + outcome.text
                )

                for outcome
                in outcomes
            )
        )

        # External/model cognition proposes meaning.
        lesson = (
            lesson_builder(
                evidence
            )
            .strip()
        )

        if not lesson:
            raise ValueError(
                "empty lesson"
            )

        source_ids = (
            decision_id,
            *(
                outcome.object_id
                for outcome
                in outcomes
            ),
        )

        # Historical proposal only.
        #
        # This deliberately does NOT call self.learn().
        return self.event(
            "LessonProposed",

            lesson,

            decision.entities,

            refs=(
                source_ids
            ),

            metadata={
                "proposal_for": (
                    decision_id
                ),

                "outcome_count": (
                    len(
                        outcomes
                    )
                ),

                "authority": (
                    "proposal_only"
                ),
            },
        )

    # -----------------------------------------------------------------
    # LESSON PROMOTION
    # -----------------------------------------------------------------

    def promote_lesson(
        self,
        proposal_id: str,
        *,
        idempotency_key=None,
    ):
        """
        Explicitly promote a historical LessonProposed event into
        searchable interpretive memory.

        Promotion is separate from proposal generation.
        """

        row = (
            self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE object_id=?
                """,
                (
                    proposal_id,
                ),
            )
            .fetchone()
        )

        if not row:
            raise KeyError(
                proposal_id
            )

        proposal = (
            self._item(
                row
            )
        )

        if (
            proposal.plane
            !=
            "historical"
            or
            proposal.kind
            !=
            "LessonProposed"
        ):
            raise ValueError(
                "promotion requires "
                "a LessonProposed event"
            )

        return self.learn(
            proposal.text,

            proposal.entities,

            (
                proposal.object_id,
            ),

            idempotency_key=(
                idempotency_key
            ),
        )

    # -----------------------------------------------------------------
    # EVIDENCE-GATED AUTOMATIC PROMOTION (ADR-0018 / v0 Quorum)
    # -----------------------------------------------------------------

    @staticmethod
    def _normalize_lesson(text: str) -> str:
        return " ".join(str(text).casefold().split())

    def _valid_lesson_support(
        self,
        proposal_item,
    ) -> tuple[str, str] | None:
        """
        Verify that proposal_item has a valid evidence ancestry chain:
        DecisionMade -> OutcomeObserved -> LessonProposed.

        Returns (decision_id, primary_outcome_id) if valid, or None.
        """
        if (
            proposal_item.plane != "historical"
            or proposal_item.kind != "LessonProposed"
            or not proposal_item.refs
        ):
            return None

        decision_id = proposal_item.refs[0]

        drow = self.db.execute(
            """
            SELECT plane, kind
            FROM commits
            WHERE object_id=?
            """,
            (decision_id,),
        ).fetchone()

        if not drow or drow["kind"] != "DecisionMade":
            return None

        outcomes = [
            row
            for row in self.db.execute(
                """
                SELECT object_id, refs
                FROM commits
                WHERE kind='OutcomeObserved'
                """
            )
            if decision_id in json.loads(row["refs"])
        ]

        if not outcomes:
            return None

        outcome_ids = {row["object_id"] for row in outcomes}
        if not any(ref in outcome_ids for ref in proposal_item.refs[1:]):
            return None

        return (decision_id, outcomes[0]["object_id"])

    def promote_lesson_if_supported(
        self,
        proposal_id: str,
        *,
        required_distinct_decisions: int = 2,
    ):
        """
        Automatically promote a lesson proposal into active interpretive memory
        if at least required_distinct_decisions distinct DecisionMade events
        have valid LessonProposed events matching the normalized lesson text.
        """
        row = self.db.execute(
            """
            SELECT *
            FROM commits
            WHERE object_id=?
            """,
            (proposal_id,),
        ).fetchone()

        if not row:
            raise KeyError(proposal_id)

        target_proposal = self._item(row)

        if (
            target_proposal.plane != "historical"
            or target_proposal.kind != "LessonProposed"
        ):
            raise ValueError("promotion requires a LessonProposed event")

        target_norm = self._normalize_lesson(target_proposal.text)

        all_proposals = [
            self._item(r)
            for r in self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE kind='LessonProposed'
                ORDER BY seq
                """
            )
        ]

        matching_proposals_by_decision = {}
        proposal_ids_by_decision = {}

        for p in all_proposals:
            if self._normalize_lesson(p.text) != target_norm:
                continue

            support = self._valid_lesson_support(p)
            if not support:
                continue

            decision_id, _ = support
            if decision_id not in matching_proposals_by_decision:
                matching_proposals_by_decision[decision_id] = p
                proposal_ids_by_decision[decision_id] = [p.object_id]
            else:
                proposal_ids_by_decision[decision_id].append(p.object_id)

        if len(matching_proposals_by_decision) < required_distinct_decisions:
            return None

        all_matching_proposal_ids = []
        all_entities = []

        for p_list in proposal_ids_by_decision.values():
            all_matching_proposal_ids.extend(p_list)

        for p in matching_proposals_by_decision.values():
            all_entities.extend(p.entities)

        seen_ent = set()
        dedup_entities = []
        for e in all_entities:
            if e not in seen_ent:
                seen_ent.add(e)
                dedup_entities.append(e)

        auto_key = (
            f"auto-promote:{hashlib.sha256(target_norm.encode('utf-8')).hexdigest()}"
        )

        return self.learn(
            target_proposal.text,
            tuple(dedup_entities),
            tuple(all_matching_proposal_ids),
            idempotency_key=auto_key,
        )

    # -----------------------------------------------------------------
    # CONSOLIDATION
    # -----------------------------------------------------------------

    def consolidate(
        self,
        decision_id: str,
        lesson_builder: Callable[
            [str],
            str,
        ],
    ):
        drow = self.db.execute(
            """
            SELECT *
            FROM commits
            WHERE object_id=?
            """,
            (
                decision_id,
            ),
        ).fetchone()

        if not drow:
            raise KeyError(
                decision_id
            )

        decision = self._item(
            drow
        )

        outcomes = [
            self._item(row)

            for row in self.db.execute(
                """
                SELECT *
                FROM commits
                WHERE kind='OutcomeObserved'
                ORDER BY seq
                """
            )

            if decision_id
            in json.loads(
                row["refs"]
            )
        ]

        if not outcomes:
            raise ValueError(
                "no observed outcome"
            )

        evidence = (
            "DECISION: "
            + decision.text
            + "\n"
            + "\n".join(
                "OUTCOME: "
                + outcome.text

                for outcome
                in outcomes
            )
        )

        # This can later be an LLM call.
        lesson = lesson_builder(
            evidence
        ).strip()

        if not lesson:
            raise ValueError(
                "empty lesson"
            )

        source_ids = (
            decision_id,

            *(
                outcome.object_id
                for outcome
                in outcomes
            ),
        )

        return self.learn(
            lesson,

            decision.entities,

            source_ids,
        )
