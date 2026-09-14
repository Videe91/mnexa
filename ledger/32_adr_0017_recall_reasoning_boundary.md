# 32. ADR-0017 — Recall / Reasoning Boundary Refactor

## Architecture Decision Record

See [`docs/decisions/0017-recall-reasoning-boundary.md`](file:///Users/vineetpandey/Desktop/mnexa/docs/decisions/0017-recall-reasoning-boundary.md).

## Core Principle

> **MNEXA retrieves and freezes context. The model reasons outside MNEXA.**

```text
    MNEXA ContextPreparer.prepare(recall_intent)
                    ↓
       immutable ContextFrame (with evidence_sha256)
                    ↓
          Model / Reasoner (outside MNEXA)
```

## Key Changes

1. **`mnexa_context.py`**:
   - `AssembledRecall`: Immutable container for MNEXA context assembly.
   - `ContextFrame`: Immutable boundary object with deterministic `evidence_sha256` digest and payload `verify_integrity()` check.
   - `ContextPreparer`: Pure MNEXA context preparer. Freezes watermark, invokes recall & assembly, and records context events without model dependencies.

2. **`agent_cycle.py`**:
   - `render_model_input`: Formats task, context text, and reasoning instructions separately. Validates context frame integrity.
   - `reason_over_context`: Invokes reasoner over frozen `ContextFrame` without retrieval access, returning an `AgentDecision` linked to `context_evidence_sha256`.

3. **Legacy Decoupling & Docstrings**:
   - `MnexaSeed.decide()` marked as a legacy convenience wrapper.

## Key Invariants Verified

- **100% Immutable Context Identity**: Different reasoning instructions consume the exact same `ContextFrame` and `evidence_sha256` without re-triggering memory retrieval.
- **Zero Reasoner Parameters in Recall**: `ContextPreparer.prepare()` accepts `recall_intent` only and has no parameter for model or prompt instructions.
- **Payload Integrity Verification**: `ContextFrame.verify_integrity()` detects any payload tampering prior to model inference.

## Unit Test Coverage

- [`tests/test_recall_reasoning_boundary.py`](file:///Users/vineetpandey/Desktop/mnexa/tests/test_recall_reasoning_boundary.py): 14 unit tests.
- [`tests/test_agent_cycle.py`](file:///Users/vineetpandey/Desktop/mnexa/tests/test_agent_cycle.py): 5 unit tests.
- Total Suite: **466 / 466 passed (100%)**.
