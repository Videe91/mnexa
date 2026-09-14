# Ledger Step 04: Seed Growth 002 Lossless Consolidation

**Date:** 2026-09-13  
**Objective:** Eliminate consolidation information loss by introducing `build_consolidation_prompt` while holding retrieval and reasoning seats constant.

---

## 1. Rationale & Controlled Change

Seed Growth 001R showed that consolidation omitted decision-critical details like `"every part"` and `"once"`.
We made exactly **one controlled hypothesis change**:
> Upgrade the consolidation prompt to require lossless operational consolidation, explicitly preserving numbers, units, exact counts, negations, header names, and constraints.

Reasoning model, task families, retrieval channel fusion, and meters remained untouched.

---

## 2. Code Implementation

In [`experiments/seed_growth.py`](file:///Users/vineetpandey/Desktop/mnexa/experiments/seed_growth.py), added `build_consolidation_prompt(evidence)`:
- Explicit instructions:
  - Preserve numbers, timings, units, exact counts, headers, and protocol values.
  - Preserve words like *exactly, only, every, each, before, after*.
  - Require structured output: `TRIGGER`, `REUSABLE RULE`, `CRITICAL CONSTRAINTS`.
  - Prohibit vague advice (e.g. *"follow documentation"*).

Updated `make_consolidator()` to consume `build_consolidation_prompt(evidence)`.

---

## 3. Execution & Results (Seed Growth 002)

**Command:**
```bash
export $(grep -v '^#' .env | xargs) && export MNEXA_MODEL="gpt-4o-mini"
/Users/vineetpandey/.local/bin/uv run python -m experiments.seed_growth \
  --experiment seed-growth-002 \
  --grader-profile experiments/graders_001r.json
```

**Result (`experiments/results/20260913T135101Z/result.json`):**
```json
{
  "experiment": "seed-growth-002",
  "baseline_passes": 1,
  "mnexa_passes": 3,
  "net_improvement": 2
}
```

---

## 4. Trace Findings & Failure Decomposition

### A. Consolidation Constraint Preservation
With the upgraded prompt, **100% of critical constraints were preserved in the consolidated lessons**:
- **Helios Lesson**: Explicitly contained `"attach a SHA-256 digest for every part"`.
- **Saffron Lesson**: Explicitly contained `"requeue the job once"` and `"Do not retry the same leased job"`.

### B. Reasoning / Grader Phrasing Mismatch
- **Helios Decision**: `"switch to multipart upload with 16 MiB parts. Ensure that a SHA-256 digest is attached for each of the six parts..."`
  - *Grader Check (`graders_001r.json`)*: Required `\b(?:every|each|per)\s+part\b`. The model inserted `"of the six"` (`"each of the six parts"`), failing the regex pattern.
- **Saffron Decision**: `"requeue the job under the new lease. Do not retry the same leased job."`
  - *Grader Check*: recoded lesson contained `"once"`, but decision seat omitted `"once"`.
