from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from dotenv import (
    load_dotenv,
)

from agent_cycle import (
    reason_over_context,
)

from mnexa_seed import (
    MnexaSeed,
)

from model_adapter import (
    AnthropicMessagesModel,
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


# =====================================================================
# EXPERIMENT IDENTITY
# =====================================================================

EXPERIMENT = (
    "030_real_cross_model_transplant"
)

ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

RESULTS_DIR = (
    ROOT
    /
    "experiments"
    /
    "results"
)


# =====================================================================
# SYNTHETIC UNKNOWN-TO-THE-MODELS WORLD
#
# These values are intentionally arbitrary.
#
# The point is to prevent either model's pretraining from being the
# source of the answer.
# =====================================================================

SYSTEM_NAME = (
    "ORCHID-729"
)

FAILURE_CODE = (
    "VX-41"
)

EXPECTED_MODE = (
    "EMBER-7"
)

EXPECTED_WAIT_MS = (
    137
)

EXPECTED_HEADER = (
    "X-Relay:cobalt"
)

EXPECTED_RULE = (
    EXPECTED_MODE,
    EXPECTED_WAIT_MS,
    EXPECTED_HEADER,
)

EXPECTED_ANSWER = (
    "MODE=EMBER-7\n"
    "WAIT_MS=137\n"
    "HEADER=X-Relay:cobalt"
)

CANONICAL_LESSON = (
    "ORCHID-729 VX-41 recovery requires "
    "MODE=EMBER-7; "
    "WAIT_MS=137; "
    "HEADER=X-Relay:cobalt."
)


# =====================================================================
# TASK
#
# IMPORTANT:
#
# The secret recovery values DO NOT appear here.
# =====================================================================

TASK = (
    "You are operating synthetic system ORCHID-729. "
    "It has returned failure code VX-41. "
    "Determine the authoritative recovery procedure. "
    "\n\n"
    "Return exactly these three fields if the procedure is established:"
    "\n"
    "MODE=<value>\n"
    "WAIT_MS=<integer>\n"
    "HEADER=<value>"
    "\n\n"
    "If the supplied MNEXA context does not establish all three values, "
    "answer exactly:"
    "\n"
    "UNKNOWN"
)

ENTITIES = (
    "system:orchid-729",
)

REASONING_INSTRUCTION = (
    "Treat only MNEXA CONTEXT as authoritative evidence for the "
    "ORCHID-729 recovery procedure. "
    "Do not use prior knowledge, inference, analogy, or guessing. "
    "If MODE, WAIT_MS, and HEADER are not all established by the "
    "MNEXA CONTEXT, answer exactly UNKNOWN."
)


# =====================================================================
# REALITY FEEDBACK
#
# This is the only place the hidden rule enters the learning episodes.
# =====================================================================

OUTCOME_A = (
    "Episode A reality feedback: the attempted recovery did not resolve "
    "ORCHID-729 failure VX-41. "
    "The authoritative recovery procedure observed from the environment "
    "is MODE=EMBER-7; WAIT_MS=137; HEADER=X-Relay:cobalt."
)

OUTCOME_B = (
    "Episode B independent reality feedback: recovery again failed until "
    "the environment supplied its authoritative VX-41 procedure. "
    "For ORCHID-729 the observed procedure is "
    "MODE=EMBER-7; WAIT_MS=137; HEADER=X-Relay:cobalt."
)


# =====================================================================
# ENVIRONMENT
# =====================================================================

def _load_environment():
    env_path = (
        ROOT
        /
        ".env"
    )

    load_dotenv(
        env_path
    )

    required = (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    )

    missing = [
        name
        for name
        in required

        if not os.getenv(
            name
        )
    ]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            +
            ", ".join(
                missing
            )
        )

    return {
        "openai_model": (
            os.getenv(
                "OPENAI_TRANSPLANT_MODEL",
                "gpt-5.6-luna",
            )
        ),

        "anthropic_model": (
            os.getenv(
                "ANTHROPIC_TRANSPLANT_MODEL",
                "claude-sonnet-4-6",
            )
        ),
    }


# =====================================================================
# MNEXA FACTORY
# =====================================================================

def _seed(
    db_path,
):
    return MnexaSeed(
        db_path,

        embedder=(
            SentenceTransformerEmbedder()
        ),

        meter=(
            WordMeter()
        ),
    )


# =====================================================================
# TELEMETRY
# =====================================================================

def _call_model(
    model,
    prompt,
    calls,
    *,
    purpose,
):
    generation = (
        model.generate(
            prompt
        )
    )

    calls.append(
        {
            "purpose": purpose,

            "model": (
                model.name
            ),

            "input_tokens": (
                generation
                .input_tokens
            ),

            "output_tokens": (
                generation
                .output_tokens
            ),

            "response_id": (
                generation
                .response_id
            ),
        }
    )

    return (
        generation.text.strip()
    )


def _reasoner(
    model,
    calls,
    *,
    purpose,
):
    def reason(
        prompt,
    ):
        return _call_model(
            model,
            prompt,
            calls,
            purpose=purpose,
        )

    return reason


# =====================================================================
# MACHINE-READABLE RULE EXTRACTION
#
# This does NOT infer a rule.
#
# It only verifies/extracts fields explicitly emitted by the model.
# =====================================================================

def _extract_rule(
    text,
):
    text = (
        str(text)
        .replace(
            "`",
            "",
        )
    )

    mode_match = re.search(
        r"\bMODE\s*=\s*([A-Za-z0-9._:\-]+)",
        text,
        flags=re.IGNORECASE,
    )

    wait_match = re.search(
        r"\bWAIT(?:_MS)?\s*=\s*(\d+)",
        text,
        flags=re.IGNORECASE,
    )

    header_match = re.search(
        r"\bHEADER\s*=\s*([A-Za-z0-9._:\-]+)",
        text,
        flags=re.IGNORECASE,
    )

    if not (
        mode_match
        and
        wait_match
        and
        header_match
    ):
        return None

    return (
        mode_match
        .group(1)
        .upper(),

        int(
            wait_match
            .group(1)
        ),

        header_match
        .group(1),
    )


# =====================================================================
# OPENAI LESSON BUILDER
#
# Model A receives the real DecisionMade + OutcomeObserved evidence.
#
# It must itself extract the hidden rule.
#
# We canonicalize only AFTER verifying the model emitted all fields.
# This gives both independent proposals exactly the same proposition
# identity without inserting semantic content not emitted by Model A.
# =====================================================================

def _openai_lesson_builder(
    model,
    calls,
    *,
    episode,
):
    def build(
        evidence,
    ):
        prompt = (
            "You are extracting one durable operational lesson from "
            "real decision/outcome evidence."
            "\n\n"
            "Use ONLY the evidence below."
            "\n"
            "Do not guess."
            "\n"
            "Do not add explanation."
            "\n\n"
            "Return exactly three lines:"
            "\n"
            "MODE=<observed value>"
            "\n"
            "WAIT_MS=<observed integer>"
            "\n"
            "HEADER=<observed value>"
            "\n\n"
            "EVIDENCE:"
            "\n"
            +
            evidence
        )

        raw = (
            _call_model(
                model,
                prompt,
                calls,

                purpose=(
                    "lesson_extraction_"
                    +
                    episode
                ),
            )
        )

        extracted = (
            _extract_rule(
                raw
            )
        )

        if (
            extracted
            !=
            EXPECTED_RULE
        ):
            raise AssertionError(
                "OpenAI Model A did not extract the authoritative "
                "recovery rule from outcome evidence."
                "\n\n"
                "Raw model output:"
                "\n"
                +
                raw
            )

        return (
            CANONICAL_LESSON
        )

    return build


# =====================================================================
# ONE OPENAI EXPERIENCE
# =====================================================================

def _run_training_episode(
    m,
    model,
    calls,
    *,
    episode,
    outcome,
):
    # -------------------------------------------------------------
    # Before promotion, the hidden rule must NOT already be in
    # active MNEXA context.
    # -------------------------------------------------------------

    context = (
        m.prepare_context(
            TASK,
            ENTITIES,
        )
    )

    for secret in (
        EXPECTED_MODE,
        str(
            EXPECTED_WAIT_MS
        ),
        EXPECTED_HEADER,
    ):
        if (
            secret.lower()
            in
            context.context_text.lower()
        ):
            raise AssertionError(
                "Hidden recovery rule leaked into active context "
                "before evidence-gated promotion."
            )

    # -------------------------------------------------------------
    # REAL MODEL A reasons.
    # -------------------------------------------------------------

    agent_decision = (
        reason_over_context(
            context=context,

            task=TASK,

            reasoner=(
                _reasoner(
                    model,
                    calls,

                    purpose=(
                        "training_decision_"
                        +
                        episode
                    ),
                )
            ),

            reasoning_instruction=(
                REASONING_INSTRUCTION
            ),
        )
    )

    # -------------------------------------------------------------
    # MNEXA records the external model decision.
    # -------------------------------------------------------------

    recorded = (
        m.record_external_decision(
            context=context,

            decision_text=(
                agent_decision
                .decision
            ),

            context_evidence_sha256=(
                agent_decision
                .context_evidence_sha256
            ),

            entities=ENTITIES,

            decision_kind=(
                "synthetic_recovery_attempt"
            ),
        )
    )

    # -------------------------------------------------------------
    # Reality provides the authoritative outcome.
    # -------------------------------------------------------------

    observed = (
        m.observe_outcome(
            recorded.record_id,

            outcome,

            success=False,
        )
    )

    # -------------------------------------------------------------
    # Model A proposes the lesson from that evidence.
    # -------------------------------------------------------------

    proposal = (
        m.propose_lesson(
            recorded.record_id,

            _openai_lesson_builder(
                model,
                calls,
                episode=episode,
            ),
        )
    )

    return {
        "context": context,

        "decision": (
            agent_decision.decision
        ),

        "decision_id": (
            recorded.record_id
        ),

        "outcome_id": (
            observed.object_id
        ),

        "proposal_id": (
            proposal.object_id
        ),

        "proposal_text": (
            proposal.text
        ),
    }


# =====================================================================
# PHASE 1
#
# OPENAI MODEL A LIVES THROUGH EXPERIENCE.
# =====================================================================

def _train_with_openai(
    db_path,
    model_name,
):
    m = (
        _seed(
            db_path
        )
    )

    model_a = (
        OpenAIResponsesModel(
            model_name
        )
    )

    calls = []

    episode_a = (
        _run_training_episode(
            m,
            model_a,
            calls,
            episode="A",
            outcome=OUTCOME_A,
        )
    )

    # -------------------------------------------------------------
    # One episode must NOT be enough.
    # -------------------------------------------------------------

    first_promotion = (
        m.promote_lesson_if_supported(
            episode_a[
                "proposal_id"
            ]
        )
    )

    if (
        first_promotion
        is not None
    ):
        raise AssertionError(
            "One episode unexpectedly promoted the lesson."
        )

    episode_b = (
        _run_training_episode(
            m,
            model_a,
            calls,
            episode="B",
            outcome=OUTCOME_B,
        )
    )

    # -------------------------------------------------------------
    # Two independent evidence-backed episodes should establish
    # the durable belief.
    # -------------------------------------------------------------

    belief = (
        m.promote_lesson_if_supported(
            episode_b[
                "proposal_id"
            ]
        )
    )

    if belief is None:
        raise AssertionError(
            "Two independent OpenAI episodes did not promote "
            "the canonical lesson."
        )

    if (
        belief.text
        !=
        CANONICAL_LESSON
    ):
        raise AssertionError(
            "Promoted belief text differs from canonical lesson."
        )

    result = {
        "belief_id": (
            belief.object_id
        ),

        "belief_version": (
            belief.version
        ),

        "belief_seq": (
            belief.seq
        ),

        "belief_text": (
            belief.text
        ),

        "watermark": (
            m.watermark()
        ),

        "episode_a": {
            "decision": (
                episode_a[
                    "decision"
                ]
            ),

            "decision_id": (
                episode_a[
                    "decision_id"
                ]
            ),

            "proposal_id": (
                episode_a[
                    "proposal_id"
                ]
            ),
        },

        "episode_b": {
            "decision": (
                episode_b[
                    "decision"
                ]
            ),

            "decision_id": (
                episode_b[
                    "decision_id"
                ]
            ),

            "proposal_id": (
                episode_b[
                    "proposal_id"
                ]
            ),
        },

        "calls": calls,
    }

    # -------------------------------------------------------------
    # MODEL A and this MNEXA process end here.
    # -------------------------------------------------------------

    m.close()

    return result


# =====================================================================
# CLAUDE CONDITION
#
# Used identically for:
#
#     cold Claude + empty MNEXA
#
# and
#
#     fresh Claude + OpenAI-trained MNEXA
# =====================================================================

def _run_claude_condition(
    db_path,
    model_name,
    *,
    condition,
):
    m = (
        _seed(
            db_path
        )
    )

    model_b = (
        AnthropicMessagesModel(
            model_name,
            max_tokens=256,
        )
    )

    calls = []

    context = (
        m.prepare_context(
            TASK,
            ENTITIES,
        )
    )

    decision = (
        reason_over_context(
            context=context,
            task=TASK,

            reasoner=(
                _reasoner(
                    model_b,
                    calls,
                    purpose=condition,
                )
            ),

            reasoning_instruction=(
                REASONING_INSTRUCTION
            ),
        )
    )

    result = {
        "condition": condition,

        "decision": (
            decision.decision.strip()
        ),

        "parsed_rule": (
            _extract_rule(
                decision.decision
            )
        ),

        "context_watermark": (
            context.watermark
        ),

        "selected_memory_ids": list(
            context.selected_memory_ids
        ),

        "context_text": (
            context.context_text
        ),

        "context_evidence_sha256": (
            context.evidence_sha256
        ),

        "calls": calls,
    }

    m.close()

    return result


# =====================================================================
# TOKEN TELEMETRY
# =====================================================================

def _token_totals(
    calls,
):
    input_tokens = sum(
        call["input_tokens"] or 0
        for call
        in calls
    )

    output_tokens = sum(
        call["output_tokens"] or 0
        for call
        in calls
    )

    return {
        "input_tokens": (
            input_tokens
        ),

        "output_tokens": (
            output_tokens
        ),

        "calls": (
            len(
                calls
            )
        ),
    }


# =====================================================================
# MAIN
# =====================================================================

def main():
    config = (
        _load_environment()
    )

    openai_model_name = (
        config[
            "openai_model"
        ]
    )

    anthropic_model_name = (
        config[
            "anthropic_model"
        ]
    )

    # -------------------------------------------------------------
    # Sanity check:
    #
    # Secret must not accidentally be in the task.
    # -------------------------------------------------------------

    for secret in (
        EXPECTED_MODE,
        str(
            EXPECTED_WAIT_MS
        ),
        EXPECTED_HEADER,
    ):
        assert (
            secret.lower()
            not in
            TASK.lower()
        )

    with tempfile.TemporaryDirectory(
        prefix=(
            "mnexa-exp030-"
        )
    ) as temp_dir:

        temp_dir = Path(
            temp_dir
        )

        shared_db = (
            temp_dir
            /
            "openai_trained_mnexa.db"
        )

        cold_db = (
            temp_dir
            /
            "cold_mnexa.db"
        )

        # =========================================================
        # PHASE 1
        #
        # OPENAI accumulates experience into MNEXA.
        # =========================================================

        training = (
            _train_with_openai(
                shared_db,
                openai_model_name,
            )
        )

        # =========================================================
        # PHASE 2
        #
        # Fresh Claude + empty MNEXA.
        # =========================================================

        cold = (
            _run_claude_condition(
                cold_db,
                anthropic_model_name,
                condition=(
                    "claude_cold_control"
                ),
            )
        )

        # =========================================================
        # PHASE 3
        #
        # A second fresh Claude client + the SAME MNEXA database
        # trained while OpenAI was present.
        # =========================================================

        transplanted = (
            _run_claude_condition(
                shared_db,
                anthropic_model_name,
                condition=(
                    "claude_transplanted"
                ),
            )
        )

        # =================================================================
        # SCORING
        # =================================================================

        cold_rule_correct = (
            tuple(
                cold[
                    "parsed_rule"
                ]
            )
            ==
            EXPECTED_RULE

            if cold[
                "parsed_rule"
            ]
            is not None
            else False
        )

        transplanted_rule_correct = (
            tuple(
                transplanted[
                    "parsed_rule"
                ]
            )
            ==
            EXPECTED_RULE

            if transplanted[
                "parsed_rule"
            ]
            is not None
            else False
        )

        cold_answered_unknown = (
            cold[
                "decision"
            ]
            .strip()
            .upper()
            ==
            "UNKNOWN"
        )

        cold_context_clean = (
            training[
                "belief_id"
            ]
            not in
            cold[
                "selected_memory_ids"
            ]
        )

        transplanted_received_belief = any(
            training[
                "belief_id"
            ]
            in
            mem_id
            for mem_id
            in
            transplanted[
                "selected_memory_ids"
            ]
        )

        causal_contrast = (
            not cold_rule_correct
            and
            transplanted_rule_correct
        )

        proof_pass = (
            causal_contrast
            and
            cold_context_clean
            and
            transplanted_received_belief
        )

        # =================================================================
        # RESULT ARTIFACT
        # =================================================================

        timestamp = (
            datetime
            .now(
                timezone.utc
            )
            .strftime(
                "%Y%m%dT%H%M%SZ"
            )
        )

        RESULTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        result_path = (
            RESULTS_DIR
            /
            (
                f"{EXPERIMENT}_"
                f"{timestamp}.json"
            )
        )

        result = {
            "experiment": (
                EXPERIMENT
            ),

            "timestamp_utc": (
                timestamp
            ),

            "direction": (
                "OpenAI -> MNEXA -> Anthropic"
            ),

            "models": {
                "trainer": (
                    openai_model_name
                ),

                "recipient": (
                    anthropic_model_name
                ),
            },

            "synthetic_world": {
                "system": (
                    SYSTEM_NAME
                ),

                "failure_code": (
                    FAILURE_CODE
                ),

                "expected_answer": (
                    EXPECTED_ANSWER
                ),
            },

            "training": (
                training
            ),

            "cold_claude": (
                cold
            ),

            "transplanted_claude": (
                transplanted
            ),

            "scores": {
                "cold_answered_unknown": (
                    cold_answered_unknown
                ),

                "cold_rule_correct": (
                    cold_rule_correct
                ),

                "transplanted_rule_correct": (
                    transplanted_rule_correct
                ),

                "cold_context_clean": (
                    cold_context_clean
                ),

                "transplanted_received_belief": (
                    transplanted_received_belief
                ),

                "causal_contrast": (
                    causal_contrast
                ),

                "proof_pass": (
                    proof_pass
                ),
            },

            "token_usage": {
                "openai_training": (
                    _token_totals(
                        training[
                            "calls"
                        ]
                    )
                ),

                "anthropic_cold": (
                    _token_totals(
                        cold[
                            "calls"
                        ]
                    )
                ),

                "anthropic_transplanted": (
                    _token_totals(
                        transplanted[
                            "calls"
                        ]
                    )
                ),
            },
        }

        result_path.write_text(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
            +
            "\n",

            encoding="utf-8",
        )

        # =================================================================
        # HUMAN-READABLE REPORT
        # =================================================================

        print()
        print(
            "=" * 72
        )

        print(
            "MNEXA EXPERIMENT 030 — REAL CROSS-MODEL TRANSPLANT"
        )

        print(
            "=" * 72
        )

        print()
        print(
            "Direction:"
        )

        print(
            "  OpenAI -> MNEXA -> Anthropic"
        )

        print()

        print(
            f"OpenAI trainer:   {openai_model_name}"
        )

        print(
            f"Anthropic target: {anthropic_model_name}"
        )

        print()

        print(
            "Promoted MNEXA belief:"
        )

        print(
            "  "
            +
            training[
                "belief_text"
            ]
        )

        print()

        print(
            "Cold Claude:"
        )

        print(
            cold[
                "decision"
            ]
        )

        print()

        print(
            "Transplanted Claude:"
        )

        print(
            transplanted[
                "decision"
            ]
        )

        print()

        print(
            "Scores:"
        )

        print(
            "  cold_rule_correct="
            +
            str(
                cold_rule_correct
            )
        )

        print(
            "  transplanted_rule_correct="
            +
            str(
                transplanted_rule_correct
            )
        )

        print(
            "  transplanted_received_belief="
            +
            str(
                transplanted_received_belief
            )
        )

        print(
            "  causal_contrast="
            +
            str(
                causal_contrast
            )
        )

        print(
            "  PROOF_PASS="
            +
            str(
                proof_pass
            )
        )

        print()

        print(
            "Result:"
        )

        print(
            f"  {result_path}"
        )

        print()

        print(
            "=" * 72
        )

        if not proof_pass:
            raise SystemExit(
                1
            )


if __name__ == "__main__":
    main()
