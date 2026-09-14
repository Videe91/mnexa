from __future__ import annotations

import dataclasses
import hashlib
import json

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
)


CONTEXT_FRAME_VERSION = (
    "mnexa-context-frame/0.1"
)


def _canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    )


def _normalize_metadata(
    metadata: (
        Mapping[str, Any]
        |
        None
    ),
) -> str:
    if metadata is None:
        metadata = {}

    return _canonical_json(
        dict(
            metadata
        )
    )


def _normalize_memory_ids(
    values: Sequence[str],
) -> tuple[str, ...]:
    result = tuple(
        str(value)
        for value
        in values
    )

    if len(
        result
    ) != len(
        set(
            result
        )
    ):
        raise ValueError(
            "selected_memory_ids "
            "must be unique"
        )

    return result


@dataclass(
    frozen=True,
    slots=True,
)
class AssembledRecall:
    """
    Output of MNEXA's retrieval + context-assembly phase.

    This object still belongs entirely to MNEXA.

    It contains no model reasoning instruction.
    """

    selected_memory_ids: (
        tuple[str, ...]
        |
        Sequence[str]
    )

    context_text: str

    metadata: (
        Mapping[str, Any]
        |
        None
    ) = None

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "selected_memory_ids",
            _normalize_memory_ids(
                self.selected_memory_ids
            ),
        )

        if not isinstance(
            self.context_text,
            str,
        ):
            raise TypeError(
                "context_text must be str"
            )


@dataclass(
    frozen=True,
    slots=True,
)
class ContextFrame:
    """
    Immutable boundary object exported by MNEXA to a reasoning system.

    MNEXA decides what evidence is active.

    The model decides what to think/do with that evidence.
    """

    version: str

    watermark: int

    recall_intent: str

    selected_memory_ids: (
        tuple[str, ...]
    )

    context_text: str

    metadata_json: str

    evidence_sha256: str

    context_assembled_event_id: (
        str
        |
        None
    ) = None

    @classmethod
    def create(
        cls,
        *,
        watermark: int,
        recall_intent: str,
        selected_memory_ids: (
            Sequence[str]
        ),
        context_text: str,
        metadata: (
            Mapping[str, Any]
            |
            None
        ) = None,
        context_assembled_event_id: (
            str
            |
            None
        ) = None,
    ) -> "ContextFrame":
        if not isinstance(
            watermark,
            int,
        ):
            raise TypeError(
                "watermark must be int"
            )

        if watermark < 0:
            raise ValueError(
                "watermark must be >= 0"
            )

        recall_intent = str(
            recall_intent
        ).strip()

        if not recall_intent:
            raise ValueError(
                "recall_intent may not "
                "be empty"
            )

        if not isinstance(
            context_text,
            str,
        ):
            raise TypeError(
                "context_text must be str"
            )

        memory_ids = (
            _normalize_memory_ids(
                selected_memory_ids
            )
        )

        metadata_json = (
            _normalize_metadata(
                metadata
            )
        )

        evidence_sha256 = (
            cls.compute_evidence_sha256(
                version=(
                    CONTEXT_FRAME_VERSION
                ),
                watermark=watermark,
                recall_intent=(
                    recall_intent
                ),
                selected_memory_ids=(
                    memory_ids
                ),
                context_text=(
                    context_text
                ),
                metadata_json=(
                    metadata_json
                ),
            )
        )

        return cls(
            version=(
                CONTEXT_FRAME_VERSION
            ),
            watermark=watermark,
            recall_intent=(
                recall_intent
            ),
            selected_memory_ids=(
                memory_ids
            ),
            context_text=(
                context_text
            ),
            metadata_json=(
                metadata_json
            ),
            evidence_sha256=(
                evidence_sha256
            ),
            context_assembled_event_id=(
                context_assembled_event_id
            ),
        )

    @staticmethod
    def compute_evidence_sha256(
        *,
        version: str,
        watermark: int,
        recall_intent: str,
        selected_memory_ids: (
            Sequence[str]
        ),
        context_text: str,
        metadata_json: str,
    ) -> str:
        payload = {
            "version": (
                version
            ),

            "watermark": (
                watermark
            ),

            "recall_intent": (
                recall_intent
            ),

            "selected_memory_ids": list(
                selected_memory_ids
            ),

            "context_text": (
                context_text
            ),

            "metadata_json": (
                metadata_json
            ),
        }

        return (
            hashlib
            .sha256(
                _canonical_json(
                    payload
                )
                .encode(
                    "utf-8"
                )
            )
            .hexdigest()
        )

    def verify_integrity(
        self,
    ) -> bool:
        expected = (
            self.compute_evidence_sha256(
                version=(
                    self.version
                ),
                watermark=(
                    self.watermark
                ),
                recall_intent=(
                    self.recall_intent
                ),
                selected_memory_ids=(
                    self.selected_memory_ids
                ),
                context_text=(
                    self.context_text
                ),
                metadata_json=(
                    self.metadata_json
                ),
            )
        )

        return (
            expected
            ==
            self.evidence_sha256
        )

    def metadata(
        self,
    ) -> dict[str, Any]:
        return json.loads(
            self.metadata_json
        )


FreezeWatermark = Callable[
    [],
    int,
]

RecallFunction = Callable[
    [
        str,
        int,
    ],
    Any,
]

AssembleFunction = Callable[
    [
        Any,
        int,
    ],
    AssembledRecall,
]

RecordContextFunction = Callable[
    [
        ContextFrame,
    ],
    str,
]


class ContextPreparer:
    """
    MNEXA-side cognitive boundary.

    This object knows how to:

        freeze history
        -> recall
        -> assemble
        -> freeze ContextFrame

    It deliberately knows nothing about:

        models
        reasoning prompts
        inference
        decisions
    """

    def __init__(
        self,
        *,
        freeze_watermark: (
            FreezeWatermark
        ),
        recall: (
            RecallFunction
        ),
        assemble: (
            AssembleFunction
        ),
        record_context: (
            RecordContextFunction
            |
            None
        ) = None,
    ) -> None:
        self._freeze_watermark = (
            freeze_watermark
        )

        self._recall = (
            recall
        )

        self._assemble = (
            assemble
        )

        self._record_context = (
            record_context
        )

    def prepare(
        self,
        *,
        recall_intent: str,
    ) -> ContextFrame:
        """
        Perform one explicit MNEXA recall cycle.

        No reasoning instruction enters this API.
        """

        recall_intent = str(
            recall_intent
        ).strip()

        if not recall_intent:
            raise ValueError(
                "recall_intent may not "
                "be empty"
            )

        watermark = (
            self._freeze_watermark()
        )

        recalled = (
            self._recall(
                recall_intent,
                watermark,
            )
        )

        assembled = (
            self._assemble(
                recalled,
                watermark,
            )
        )

        if not isinstance(
            assembled,
            AssembledRecall,
        ):
            raise TypeError(
                "assemble() must return "
                "AssembledRecall"
            )

        frame = (
            ContextFrame.create(
                watermark=watermark,
                recall_intent=(
                    recall_intent
                ),
                selected_memory_ids=(
                    assembled
                    .selected_memory_ids
                ),
                context_text=(
                    assembled
                    .context_text
                ),
                metadata=(
                    assembled.metadata
                ),
            )
        )

        if (
            self._record_context
            is None
        ):
            return frame

        event_id = (
            self._record_context(
                frame
            )
        )

        if not isinstance(
            event_id,
            str,
        ) or not event_id:

            raise ValueError(
                "record_context() must "
                "return a non-empty event id"
            )

        return dataclasses.replace(
            frame,
            context_assembled_event_id=(
                event_id
            ),
        )
