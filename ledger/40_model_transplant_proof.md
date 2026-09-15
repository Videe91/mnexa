# Ledger 40 — Deterministic Model Transplant Proof Architecture

**Date:** 2026-09-15  
**Status:** Completed & Validated  
**Classification:** Substrate Independence & Model Transplant Proof  
**Principle:** *Durable intelligence resides in the MNEXA substrate, allowing fresh reasoning models to inherit accumulated experience without local model state transfer.*

---

## 1. Executive Summary

This milestone establishes a **deterministic model transplant proof** (`tests/test_model_transplant.py`), verifying the core MNEXA thesis without modifying core engine logic.

The experiment compares two states of a fresh reasoner instance (**Model B**):
1. **Control (Cold)**: Fresh Model B + Empty MNEXA substrate $\rightarrow$ yields naive decision (`"Retry immediately with zero delay."`).
2. **Transplant**: Fresh Model B + MNEXA substrate trained via earlier experiences with **Model A** $\rightarrow$ retrieves promoted belief `i_auto_<hash>:v1` and yields improved decision (`"Retry with exponential backoff."`).

Model A is completely closed and discarded before Phase 3 begins. Model B possesses zero local memory. The causal contrast in Model B's behavior is driven entirely by the frozen `ContextFrame` provided by MNEXA's persistent substrate.

---

## 2. Experimental Design & Causal Contrast

```text
=====================================================================
PHASE 1: TRAINING WITH MODEL A
=====================================================================
Model A (naive reasoner) + Empty MNEXA DB
  ├─ Episode 1: Naive retry → Failure 429 flooding → Proposal A
  └─ Episode 2: Naive retry → Failure 429 amplification → Proposal B
       ↓
  MNEXA promotes Lesson: "When Payments API returns 429, retry with exponential backoff."
  MNEXA Database closed. Model A instance discarded.

=====================================================================
PHASE 2: COLD CONTROL WITH FRESH MODEL B
=====================================================================
Fresh Model B + Empty MNEXA DB
  ↓ prepare_context() → Empty ContextFrame
  ↓ reason_over_context()
  Output: "Retry immediately with zero delay." (NAIVE)

=====================================================================
PHASE 3: TRANSPLANT WITH FRESH MODEL B
=====================================================================
Fresh Model B + Reopened MNEXA DB (trained in Phase 1)
  ↓ prepare_context() → ContextFrame containing Promoted Belief v1
  ↓ reason_over_context()
  Output: "Retry with exponential backoff." (IMPROVED)
```

---

## 3. Invariants & Controls Verified

| Test Function | Verification Target | Result |
| :--- | :--- | :---: |
| `test_fresh_model_b_inherits_intelligence_accumulated_with_model_a` | Fresh Model B instance makes naive decision on empty DB, but inherits improved decision when attached to MNEXA DB trained under Model A. | PASSED |

---

## 4. Full Test Suite Telemetry

- **New Test File:** `tests/test_model_transplant.py` (1 proof test)
- **Total Test Suite:** 534 / 534 passed in 0.72s
