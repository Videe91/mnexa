# Ledger 39 — Evidence-Gated Belief Supersession Architecture

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Epistemic Supersession & Change-of-Mind Pipeline  
**Principle:** *A belief is superseded only when shared real-world episodes both contradict the old belief and support the replacement.*

---

## 1. Executive Summary

This slice implements evidence-gated belief supersession on `MnexaSeed`.

Key capabilities established:
1. `supersede_belief_if_supported(old_belief_id, replacement_belief_id, required_shared_decisions=2)`: Replaces a contested belief $X$ with an active belief $Y$ if and only if $\ge 2$ independent `DecisionMade` episodes both:
   - Contributed valid contradiction evidence against $X$
   - Contributed valid lesson evidence supporting $Y$
2. **Lineage & Metadata Tracking**: Creates a new version of $X$ with `metadata={'status': 'superseded', 'superseded_by': replacement_id, 'superseded_by_version': v, 'shared_decision_ids': [...]}`, preserving complete evidence ancestry without modifying $X$'s original text or creating synthetic cross-links.
3. **Recall Isolation**: `_searchable_as_of(n)` suppresses both `"contested"` and `"superseded"` belief heads from ordinary active `recall()`, while historical `as_of(watermark)` queries retain full visibility of $X$'s prior active state.

---

## 2. Complete Epistemic Lifecycle

```text
Experience A + B ───────────────→ Belief X (v1, active)
                                     │
Counterepisodes C + D ───────────→ Belief X (v2, contested, withheld from recall)
 (contradict X, support Y)           │
                                     ├─→ Belief Y (v1, active, independently promoted)
                                     │
supersede_belief_if_supported ──→ Belief X (v3, superseded_by Y)
                                     ↓
                     Active Recall: returns Y (X withheld)
                     Historical Recall as_of(v1.seq): returns X v1
```

---

## 3. Invariants & Controls Verified

| Test Function | Verification Target | Result |
| :--- | :--- | :---: |
| `test_active_uncontested_belief_cannot_be_superseded` | Uncontested belief raises `ValueError("old belief must be contested")`. | PASSED |
| `test_same_proposition_cannot_supersede_itself_under_new_identity` | Same normalized proposition raises `ValueError("different proposition")`. | PASSED |
| `test_promoted_replacement_without_shared_counterepisodes_does_not_supersede` | Promoted belief without shared counterepisodes returns `None`. | PASSED |
| `test_one_shared_counterepisode_does_not_supersede` | Single shared counterepisode returns `None` (quorum requires $\ge 2$). | PASSED |
| `test_two_shared_counterepisodes_supersede_contested_belief` | Two shared counterepisodes append `v3` (`status='superseded'`) on $X$, referencing $Y$. | PASSED |
| `test_replacement_without_valid_lesson_ancestry_is_rejected` | Synthetic or fake replacement beliefs lacking valid ancestry are rejected. | PASSED |
| `test_recall_uses_replacement_and_keeps_old_belief_historical` | Active recall surfaces $Y$ and withholds $X$; historical query `as_of(v1.seq)` surfaces $X$. | PASSED |
| `test_supersession_retry_returns_same_version` | Supersession retry is repeat-safe and idempotent, returning the existing superseded commit. | PASSED |

---

## 4. Full Test Suite Telemetry

- **New Test File:** `tests/test_belief_supersession.py` (8 tests)
- **Epistemic Pipeline Suite:** 32 / 32 passed
- **Total Test Suite:** 533 / 533 passed in 0.74s
