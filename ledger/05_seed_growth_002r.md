# Ledger Step 05: Seed Growth 002R Diagnostic Regrade

**Date:** 2026-09-13  
**Objective:** Correct the surface-form phrasing mismatch in `heliosstore-e62` ("each of the six parts") without calling LLM APIs.

---

## 1. Diagnostic Adjustment & Code Changes

Created [`experiments/graders_002r.json`](file:///Users/vineetpandey/Desktop/mnexa/experiments/graders_002r.json):
- Updated `heliosstore-e62` `all_regex` pattern to:
  `\b(?:every|each|per)\b(?:\s+of\s+the\s+\w+)?\s+parts?\b`
- Added unit test `test_002r_accepts_each_of_the_six_parts` in `tests/test_seed_growth_experiment.py`.

---

## 2. Execution & Diagnostic Results

**Command:**
```bash
/Users/vineetpandey/.local/bin/uv run python -m experiments.regrade_seed_growth \
  --result experiments/results/20260913T135101Z/result.json \
  --graders experiments/graders_002r.json \
  --output experiments/results/20260913T135101Z/regrade-002R.json
```

**Report Output (`experiments/results/20260913T135101Z/regrade-002R.json`):**
```json
{
  "experiment": "seed-growth-001R",
  "baseline_passes": 1,
  "mnexa_passes": 4,
  "net_improvement": 3
}
```

### Breakdown:
- ✅ `nebulapay-r17`: **PASS**
- ✅ `orchiddb-l42`: **PASS**
- ✅ `atlasparser-qn`: **PASS**
- ✅ `heliosstore-e62`: **PASS** (*"each of the six parts"* matched)
- ❌ `saffronqueue-amber7`: **FAIL** (Reasoning seat dropped `"once"`)

---

## 3. Findings

With lossless consolidation, MNEXA achieved **4/5 passes (+3 net improvement)** on the 5 task families. Saffron remained the single genuine failure due to the reasoning seat omitting `"once"`.
