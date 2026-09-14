# Ledger Step 03: Seed Growth 001R Diagnostic Regrade

**Date:** 2026-09-13  
**Objective:** Perform a post-hoc diagnostic regrade of Seed Growth 001 using deterministic regex matching without calling LLM APIs.

---

## 1. Rationale & Design

To distinguish surface-form phrasing variations from genuine reasoning/learning failures, we created a deterministic regex grader profile.
- **Rule**: Zero LLM calls; zero modification to the original `result.json` output.
- **Grader Profile ([`experiments/graders_001r.json`](file:///Users/vineetpandey/Desktop/mnexa/experiments/graders_001r.json))**:
  - `all_regex`: Flexible token spacing, optional words (e.g. `\bretry\b.*\b(?:exactly\s+)?once\b`).
  - `none_regex`: Prohibitions (e.g. `retry\s+indefinitely`).
- **Regrader Engine ([`experiments/regrade_seed_growth.py`](file:///Users/vineetpandey/Desktop/mnexa/experiments/regrade_seed_growth.py))**:
  - Re-evaluates saved decision texts offline.

---

## 2. Code Changes

1. **`experiments/seed_growth.py`**:
   - Upgraded `grade_text` to support `all_regex` and `none_regex` via `re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)`.
2. **`tests/test_seed_growth_experiment.py`**:
   - Added `test_grade_text_supports_regex_groups` and `test_regrade_uses_saved_outputs_without_model_calls`.

---

## 3. Execution & Diagnostic Results

**Command:**
```bash
/Users/vineetpandey/.local/bin/uv run python -m experiments.regrade_seed_growth \
  --result experiments/results/20260913T134132Z/result.json
```

**Report Output ([`experiments/results/20260913T134132Z/regrade-001R.json`](file:///Users/vineetpandey/Desktop/mnexa/experiments/results/20260913T134132Z/regrade-001R.json)):**

```json
{
  "experiment": "seed-growth-001R",
  "baseline_passes": 0,
  "mnexa_passes": 3,
  "net_improvement": 3
}
```

### Breakdown:
- ✅ **`nebulapay-r17`**: **PASS** (Model decision: *"wait for 3 seconds, then retry the refund request exactly once..."*)
- ✅ **`orchiddb-l42`**: **PASS** (Model decision: *"refresh any stale lease tokens, and then retry... once without reconnecting..."*)
- ✅ **`atlasparser-qn`**: **PASS** (Model decision: *"Normalize the legacy boolean value for 'archived' from 'N' to false..."*)
- ❌ **`heliosstore-e62`**: **FAIL** (Consolidated lesson lost constraint `every part`)
- ❌ **`saffronqueue-amber7`**: **FAIL** (Consolidated lesson lost constraint `once` & `do not retry same`)

---

## 4. Key Discovery

MNEXA successfully learned local runbook rules for 3 out of 5 task families. The two failures (`heliosstore-e62` and `saffronqueue-amber7`) were caused by **information loss during consolidation** (the original consolidation prompt compressed away operational constraints).
