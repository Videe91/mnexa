# Ledger Step 02: Seed Growth 001 Experiment Infrastructure & Initial Run

**Date:** 2026-09-13  
**Objective:** Construct an exploratory transfer experiment harness and evaluate Seed Growth 001 against 5 synthetic task families.

---

## 1. Architecture & Component Additions

1. **Model & Embedding Adapters ([`model_adapter.py`](file:///Users/vineetpandey/Desktop/mnexa/model_adapter.py))**:
   - `Generation`: Immutable dataclass for text, input/output token counts, and response IDs.
   - `OpenAIResponsesModel`: Thin wrapper calling OpenAI's `responses.create` API.
   - `SentenceTransformerEmbedder`: Local semantic embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
   - `WordMeter`: Word-count token measurement basis (`word-meter-v1`).
2. **Experiment Package ([`experiments/seed_growth.py`](file:///Users/vineetpandey/Desktop/mnexa/experiments/seed_growth.py))**:
   - `grade_text`: Literal string matching (`all_of`, `none_of`).
   - `make_reasoner` & `make_consolidator`: Prompt seats.
   - `run_family`: Executes Condition B0 (Baseline, no memory) vs Condition MNEXA (Experience -> Outcome -> Consolidation -> Transfer).
   - `run_experiment`: Saves structured `result.json` reports.
3. **Synthetic Task Families ([`experiments/tasks.json`](file:///Users/vineetpandey/Desktop/mnexa/experiments/tasks.json))**:
   - 5 Opaque Synthetic Rule Families: `nebulapay-r17`, `orchiddb-l42`, `atlasparser-qn`, `heliosstore-e62`, `saffronqueue-amber7`.
4. **Test Suite ([`tests/test_seed_growth_experiment.py`](file:///Users/vineetpandey/Desktop/mnexa/tests/test_seed_growth_experiment.py))**:
   - Added unit test cases with `DeterministicModel` verifying `grade_text` and single-family execution (`4 passed in 0.04s`).

---

## 2. Experimental Execution (Seed Growth 001)

**Configuration:**
- Model: `gpt-4o-mini`
- Embedder: `sentence-transformers/all-MiniLM-L6-v2`
- API: Real OpenAI Responses API (`OPENAI_API_KEY` from `.env`)

**Command:**
```bash
export $(grep -v '^#' .env | xargs) && export MNEXA_MODEL="gpt-4o-mini"
/Users/vineetpandey/.local/bin/uv run python -m experiments.seed_growth
```

**Raw Output Summary (`experiments/results/20260913T134132Z/result.json`):**
```json
{
  "experiment": "seed-growth-001",
  "baseline_passes": 0,
  "mnexa_passes": 0,
  "net_improvement": 0
}
```

---

## 3. Failure Trace Decomposition

Deep inspection of `result.json` revealed an important insight:
- **Consolidation**: `YES`. Lessons were extracted for all 5 families.
- **Retrieval & Context**: `YES`. Lessons were recalled (`watermark: 4`) and presented in context.
- **Reasoning**: `YES`. The model changed its decision from generic boilerplate to specific runbook execution.
- **Grader Discrepancy**: The literal string grader required exact sub-string matches like `"retry exactly once"`. The model generated `"retry the refund request exactly once"`, causing the rigid string grader to report `passed: false` for all cases.
