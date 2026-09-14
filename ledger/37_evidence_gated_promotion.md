# Ledger 37 — Evidence-Gated Automatic Promotion & Belief Versioning Architecture

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Evidence-Gated Automatic Epistemic Promotion & Reinforcement  
**Principle:** *Proposition identity dictates belief object identity; evidence snapshot growth drives version progression.*

---

## 1. Executive Summary

This slice implements evidence-gated automatic promotion and belief versioning on `MnexaSeed`.

A candidate lesson proposed via `propose_lesson()` is automatically promoted into active searchable interpretive memory (`plane='interpretive'`, `kind='belief'`) if and only if it achieves a quorum of at least 2 distinct `DecisionMade` records, each backed by real `OutcomeObserved` evidence.

Three distinct identities are decoupled:
1. **Proposition Identity** (`lesson_sha256`): Maps normalized lesson text (`" ".join(text.casefold().split())`) to a single stable belief `object_id`.
2. **Evidence Snapshot Identity** (`evidence_sha256`): Maps the tuple of supporting proposal IDs to a version-specific idempotency key (`auto-promote-v2:<lesson-hash>:<evidence-hash>`).
3. **Belief Lineage**: When new independent supporting evidence arrives, `promote_lesson_if_supported()` strengthens the existing belief by appending a new version (`v1` $\rightarrow$ `v2` $\rightarrow$ `v3`) with expanded `refs` rather than creating duplicate belief objects or raising idempotency conflicts.

---

## 2. Evidence Versioning Pipeline

```text
Evidence A + B ──────────────────→ belief X v1 (refs: A, B)
                                      │
Evidence A + B + C ──────────────→ belief X v2 (refs: A, B, C)
                                      │
Retried Evidence A + B + C ──────→ returns belief X v2 (idempotent retry)
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
| `test_new_independent_support_versions_existing_belief` | Additional independent evidence produces `v2` of the existing belief object with updated `refs`. | PASSED |

---

## 4. Full Test Suite Telemetry

- **Test File:** `tests/test_evidence_gated_promotion.py` (8 tests)
- **Total Test Suite:** 516 / 516 passed in 0.54s
