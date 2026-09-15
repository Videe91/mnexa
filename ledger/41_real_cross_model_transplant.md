# Ledger 41 — Real Cross-Model Transplant Architecture (OpenAI → MNEXA → Anthropic)

**Date:** 2026-09-15  
**Status:** Completed & Validated  
**Classification:** Live Cross-Provider Model Transplant Proof  
**Principle:** *MNEXA acts as a model-agnostic epistemic substrate, enabling Anthropic models to inherit operational rules extracted and promoted via OpenAI models.*

---

## 1. Executive Summary

This milestone establishes the first **live cross-provider model transplant proof** (`experiments/030_real_cross_model_transplant.py`) using real OpenAI (`gpt-5.6-luna`) and Anthropic (`claude-sonnet-4-6`) APIs.

A synthetic recovery procedure for system `ORCHID-729` failure `VX-41` (`MODE=EMBER-7; WAIT_MS=137; HEADER=X-Relay:cobalt`) was introduced exclusively through environmental feedback during OpenAI training episodes.

1. **Phase 1 (OpenAI Training)**: OpenAI experienced two failure episodes, extracted the hidden rule from environmental feedback, proposed candidate lessons, and MNEXA promoted belief `i_auto_<hash>:v1`. OpenAI client and process were closed.
2. **Phase 2 (Cold Claude Control)**: Fresh Claude client attached to an empty MNEXA database received no context and correctly answered `UNKNOWN`.
3. **Phase 3 (Transplanted Claude)**: A second fresh Claude client attached to the OpenAI-trained MNEXA database retrieved promoted belief `v1` and emitted the exact 3-line recovery procedure.

---

## 2. Live Telemetry & Causal Contrast

```text
========================================================================
MNEXA EXPERIMENT 030 — REAL CROSS-MODEL TRANSPLANT
========================================================================

Direction:
  OpenAI (gpt-5.6-luna) -> MNEXA -> Anthropic (claude-sonnet-4-6)

Promoted MNEXA belief:
  ORCHID-729 VX-41 recovery requires MODE=EMBER-7; WAIT_MS=137; HEADER=X-Relay:cobalt.

Cold Claude:
  UNKNOWN

Transplanted Claude:
  MODE=EMBER-7
  WAIT_MS=137
  HEADER=X-Relay:cobalt

Scores:
  cold_rule_correct            = False
  transplanted_rule_correct    = True
  transplanted_received_belief = True
  causal_contrast              = True
  PROOF_PASS                   = True
```

---

## 3. Invariants & Controls Verified

| Verification Target | Result |
| :--- | :---: |
| **No Secret Leakage**: Hidden rule values absent from task prompt and initial context. | PASSED |
| **Evidence-Gated Promotion**: Lesson promoted only after 2 independent OpenAI episodes with valid evidence chains. | PASSED |
| **Substrate Independence**: OpenAI model and process completely terminated before Claude execution. | PASSED |
| **Causal Contrast**: Cold Claude answered `UNKNOWN`; Transplanted Claude emitted exact recovery rule. | PASSED |
| **Token Usage**: OpenAI training (532 in / 114 out), Cold Claude (180 in / 5 out), Transplanted Claude (267 in / 27 out). | PASSED |

---

## 4. Test Suite Telemetry

- **New Test File:** `tests/test_anthropic_model_adapter.py` (2 adapter unit tests)
- **Live Experiment Artifact:** `experiments/results/030_real_cross_model_transplant_20260915T073336Z.json`
- **Total Test Suite:** 536 / 536 passed in 0.73s
