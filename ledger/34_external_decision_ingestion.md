# Ledger 34 — External Decision Ingestion Bridge

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** ADR-0017 MnexaSeed API Bridge  
**Principle:** *MNEXA retrieves and freezes context. The external AI model reasons. MNEXA ingests and records the decision.*

---

## 1. Executive Summary

This slice implements the canonical ADR-0017 bridge on `MnexaSeed`, establishing:
1. `MnexaSeed.prepare_context()` — Retrieves memories, freezes watermarks, records `ContextAssembled`, and returns an immutable `ContextFrame`. No model reasoning occurs inside MNEXA.
2. `MnexaSeed.record_external_decision()` — Validates that an external decision consumed a valid, recorded `ContextFrame` (matching content, evidence hash, watermark, and event ID), then records the `DecisionMade` commit linked via `refs`.

Existing downstream operations (`observe_outcome()` and `consolidate()`) continue to operate unchanged on the resulting decision record.

---

## 2. Canonical Cognitive Flow

```text
MNEXA.prepare_context(intent, entities)
        ↓
  ContextFrame (immutable, hashed)
        ↓
  reason_over_context(frame, task, external_reasoner)
        ↓
  AgentDecision (contains decision text & context_evidence_sha256)
        ↓
MNEXA.record_external_decision(frame, agent_decision.decision, ...)
        ↓
  DecisionMade Commit
        ↓
MNEXA.observe_outcome(decision_id, outcome_text, success=False)
        ↓
MNEXA.consolidate(decision_id, lesson_builder)
        ↓
Next encounter: prepare_context() surfaces consolidated lesson
```

---

## 3. Unit & Integration Verification

- **New Test File:** `tests/test_external_decision_ingestion.py` (7 tests)
  - `test_external_model_decision_enters_mnexa_after_frozen_context`
  - `test_record_external_decision_rejects_wrong_context_hash`
  - `test_record_external_decision_requires_recorded_context`
  - `test_record_external_decision_rejects_corrupted_context`
  - `test_prepare_context_has_no_reasoner_or_model_parameter`
  - `test_record_external_decision_has_no_reasoner_parameter`
  - `test_end_to_end_external_decision_learning_loop`
- **Total Test Suite:** 492 / 492 passed in 0.45s.
