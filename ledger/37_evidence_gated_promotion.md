# Ledger 37 — Evidence-Gated Automatic Promotion Architecture

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Evidence-Gated Automatic Epistemic Promotion  
**Principle:** *Same normalized lesson + 2 distinct DecisionMade records + each backed by OutcomeObserved evidence = eligible for automatic promotion.*

---

## 1. Executive Summary

This slice implements evidence-gated automatic promotion on `MnexaSeed`.

A candidate lesson proposed via `propose_lesson()` is automatically promoted into active searchable interpretive memory (`plane='interpretive'`, `kind='belief'`) if and only if it achieves a quorum of at least 2 distinct `DecisionMade` records, each backed by real `OutcomeObserved` evidence.

Normalization for v0 is simple and deterministic (`" ".join(text.casefold().split())`), collapsing case and whitespace variations while preserving exact semantic phrasing.

Repeated evaluation of `promote_lesson_if_supported()` is repeat-safe and idempotent via a deterministic internal key `auto-promote:<sha256(normalized_text)>`.

---

## 2. Quorum Promotion Pipeline

```text
Decision A → Outcome A → Proposal A ┐
                                    ├→ promote_lesson_if_supported()
Decision B → Outcome B → Proposal B ┘
                                    ↓
            belief (interpretive plane, active & searchable)
            refs = (Proposal A, Proposal B)
```

---

## 3. Invariants & Controls Verified

| Test Function | Verification Target | Result |
| :--- | :--- | :---: |
| `test_one_supported_proposal_is_not_enough_for_auto_promotion` | Single decision support returns `None`; zero interpretive memories created. | PASSED |
| `test_two_distinct_decisions_with_same_lesson_auto_promote` | Two distinct decisions with matching normalized lesson create active `belief` referencing both proposals. | PASSED |
| `test_case_and_whitespace_are_normalized_for_quorum` | Mixed case and extra whitespace collapse under normalization to satisfy quorum. | PASSED |
| `test_different_wording_does_not_form_quorum` | Paraphrased or non-identical wording fails normalization match and returns `None`. | PASSED |
| `test_two_proposals_from_same_decision_count_as_one_support` | Multiple proposals originating from the same `decision_id` count as only 1 distinct decision. | PASSED |
| `test_fake_matching_proposal_without_real_evidence_does_not_count` | Proposals without valid `DecisionMade` $\rightarrow$ `OutcomeObserved` evidence chain are ignored. | PASSED |
| `test_auto_promotion_is_repeat_safe_without_caller_key` | Repeated calls return the identical commit without creating duplicate interpretive memories. | PASSED |

---

## 4. Full Test Suite Telemetry

- **New Test File:** `tests/test_evidence_gated_promotion.py` (7 tests)
- **Total Test Suite:** 515 / 515 passed in 0.56s
