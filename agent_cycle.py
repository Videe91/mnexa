from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from mnexa_context import (
    ContextFrame,
)


Reasoner = Callable[
    [
        str,
    ],
    str,
]


@dataclass(
    frozen=True,
    slots=True,
)
class AgentDecision:
    context_evidence_sha256: str

    task: str

    reasoning_instruction: str

    decision: str


def render_model_input(
    *,
    task: str,
    context: ContextFrame,
    reasoning_instruction: str = "",
) -> str:
    if not context.verify_integrity():
        raise ValueError(
            "ContextFrame integrity "
            "verification failed"
        )

    task = str(
        task
    ).strip()

    if not task:
        raise ValueError(
            "task may not be empty"
        )

    reasoning_instruction = str(
        reasoning_instruction
    ).strip()

    sections = [
        (
            "TASK:\n"
            +
            task
        ),

        (
            "MNEXA CONTEXT:\n"
            +
            context.context_text
        ),
    ]

    if reasoning_instruction:

        sections.append(
            (
                "REASONING INSTRUCTION:\n"
                +
                reasoning_instruction
            )
        )

    return "\n\n".join(
        sections
    )


def reason_over_context(
    *,
    context: ContextFrame,
    task: str,
    reasoner: Reasoner,
    reasoning_instruction: str = "",
) -> AgentDecision:
    """
    MODEL/AGENT responsibility.

    This function cannot retrieve from MNEXA.

    It consumes an already-frozen ContextFrame.
    """

    model_input = (
        render_model_input(
            task=task,
            context=context,
            reasoning_instruction=(
                reasoning_instruction
            ),
        )
    )

    decision = (
        reasoner(
            model_input
        )
    )

    if not isinstance(
        decision,
        str,
    ):
        raise TypeError(
            "reasoner must return str"
        )

    return AgentDecision(
        context_evidence_sha256=(
            context.evidence_sha256
        ),
        task=(
            task
        ),
        reasoning_instruction=(
            reasoning_instruction
        ),
        decision=(
            decision
        ),
    )
