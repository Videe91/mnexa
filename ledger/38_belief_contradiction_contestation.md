# Ledger 38 — Belief Contradiction & Contestation Architecture

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Epistemic Contradiction & Recall Suppression Pipeline  
**Principle:** *Contradiction evidence suppresses active recall without destroying historical durability.*

---

## 1. Executive Summary

This slice implements evidence-gated belief contradiction, contestation, and recall suppression on `MnexaSeed`.

Key capabilities established:
1. `propose_contradiction(belief_id, decision_id, builder)`: Captures historical evidence (`plane='historical'`, `kind='ContradictionProposed'`) pinning the exact target belief version (`id`, `version`, `seq`). No belief is automatically altered or suppressed at proposal time.
2. `contest_belief_if_supported(belief_id, required_distinct_decisions=2)`: Evaluates matching contradiction proposals. Upon reaching a quorum of $\ge 2$ distinct decision evidence chains, it appends a new version of the belief with `metadata={'status': 'contested'}` while preserving both positive and negative evidence ancestry in `refs`.
3. `_searchable_as_of(n)`: Automatically suppresses contested belief heads from ordinary active recall (`recall()`), while historical `as_of(seq)` queries at or before the uncontested version retain access to the historical belief state.

---

## 2. Epistemic Contestation Pipeline

```text
Decision A → Outcome A → Contradiction A ┐
                                          ├→ contest_belief_if_supported(belief_id)
Decision B → Outcome B → Contradiction B ┘
                                          ↓
             belief X (v2, status='contested', text unchanged)
                                          ↓
             Ordinary recall(): withheld
             Historical recall as_of(v1.seq): visible
```

---

## 3. Invariants & Controls Verified

| Test Function | Verification Target | Result |
| :--- | :--- | :---: |
| `test_contradiction_proposal_is_historical_and_pins_belief_version` | Proposal creates `ContradictionProposed` event with exact target `belief_id`, `version`, and `seq` metadata. | PASSED |
| `test_one_independent_contradiction_does_not_contest_belief` | Single contradiction returns `None`; belief remains uncontested at current version. | PASSED |
| `test_two_independent_matching_contradictions_create_contested_version` | Two distinct decision contradictions create `v2` with `status='contested'`, preserving combined refs. | PASSED |
| `test_multiple_contradiction_proposals_from_same_decision_count_once` | Multiple proposals originating from the same decision count as 1 support unit. | PASSED |
| `test_fake_contradiction_without_real_decision_outcome_chain_is_ignored` | Proposals lacking valid `DecisionMade` $\rightarrow$ `OutcomeObserved` chain are rejected. | PASSED |
| `test_different_contradiction_claims_do_not_form_quorum` | Non-identical contradiction claims fail normalization matching and return `None`. | PASSED |
| `test_contradictions_are_scoped_to_exact_belief_version` | Contradictions targeting `v1` do not attack or merge with `v2` proposals. | PASSED |
| `test_contested_belief_is_withheld_from_normal_recall_but_history_survives` | Normal recall withholds contested belief; historical `as_of` query surfaces `v1`. | PASSED |
| `test_contestation_retry_returns_same_version` | Re-evaluating contestation is repeat-safe and idempotent, returning the existing contested version. | PASSED |

---

## 4. Full Test Suite Telemetry

- **New Test File:** `tests/test_belief_contradiction.py` (9 tests)
- **Epistemic Pipeline Suite:** 24 / 24 passed
- **Total Test Suite:** 525 / 525 passed in 0.60s
