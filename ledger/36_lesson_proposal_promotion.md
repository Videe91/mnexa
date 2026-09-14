# Ledger 36 — Lesson Proposal → Promotion Architecture

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Two-Stage Epistemic Memory Pipeline  
**Principle:** *Models can propose knowledge. They cannot silently declare knowledge.*

---

## 1. Executive Summary

This slice establishes the two-stage epistemic memory pipeline separating **Lesson Proposal** from **Lesson Promotion** on `MnexaSeed`.

Previously, `consolidate()` took lesson text from an AI builder and immediately called `learn()`, automatically converting model hypotheses into active searchable memory.

Under the new two-stage architecture:
1. `propose_lesson(decision_id, lesson_builder)`: Gathers complete decision and outcome evidence, invokes `lesson_builder`, and records a historical `LessonProposed` commit. **No active searchable memory is created** (`plane='historical'`, `kind='LessonProposed'`).
2. `promote_lesson(proposal_id, idempotency_key=None)`: Verifies that `proposal_id` references a valid `LessonProposed` event, then explicitly promotes it into active searchable memory (`plane='interpretive'`, `kind='belief'`, `refs=(proposal_id,)`).

---

## 2. Epistemic Pipeline Flow

```text
EXPERIENCE (DecisionMade + OutcomeObserved)
       ↓
propose_lesson(decision_id, lesson_builder)
       ↓
LessonProposed (historical event ONLY, non-searchable)
       ↓
explicit promote_lesson(proposal_id)
       ↓
belief (interpretive memory, active & searchable)
       ↓
Surfaced in future prepare_context()
```

---

## 3. Invariants & Controls Verified

| Test Function | Verification Target | Result |
| :--- | :--- | :---: |
| `test_lesson_proposal_is_history_not_active_memory` | Proposal creates `LessonProposed` in historical plane; 0 interpretive commits created; recall returns 0 proposal hits. | PASSED |
| `test_promoting_lesson_creates_searchable_interpretation` | Promotion creates `belief` in interpretive plane; references proposal ID; recall surfaces promoted lesson. | PASSED |
| `test_proposal_preserves_complete_decision_outcome_evidence` | Builder receives decision text and ALL outcome texts; proposal `refs` contain decision and all outcome IDs. | PASSED |
| `test_empty_lesson_proposal_is_rejected` | Empty or whitespace-only lesson proposal raises `ValueError("empty lesson")`. | PASSED |
| `test_promotion_rejects_non_lesson_event` | Promoting non-`LessonProposed` event raises `ValueError("LessonProposed")`. | PASSED |
| `test_proposal_requires_observed_outcome` | Proposing a lesson for a decision without an observed outcome raises `ValueError("no observed outcome")`. | PASSED |
| `test_promotion_retry_is_idempotent` | Retrying `promote_lesson()` with an `idempotency_key` returns the original promoted commit. | PASSED |

---

## 4. Full Test Suite Telemetry

- **New Test File:** `tests/test_lesson_proposal_promotion.py` (7 tests)
- **Newest 3 Slices Suite:** 23 / 23 passed
- **Total Test Suite:** 508 / 508 passed in 0.51s
