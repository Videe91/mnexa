# Ledger Step 01: Planting the Core MNEXA Seed

**Date:** 2026-09-13  
**Objective:** Plant a minimal, zero-dependency, test-first seed containing the living MNEXA cognitive loop.

---

## 1. Context & Motivation

To prove that persistence, recall, observation, and consolidation improve decision performance over time without speculative infrastructure, we established a strict **two-file test-first seed**:
- No FastAPI, Postgres, Kafka, workers, graph DBs, or complex ORMs.
- Standard library dependencies (`sqlite3`, `dataclasses`, `uuid`, `json`, `math`, `re`).

---

## 2. Red-Green TDD Process

### A. RED State Setup ([`tests/test_seed.py`](file:///Users/vineetpandey/Desktop/mnexa/tests/test_seed.py))
We wrote `tests/test_seed.py` first, establishing test contracts:
1. `test_seed_grows_from_experience`:
   - First encounter: decide without prior memory -> produces default/failing action.
   - Outcome observation: observe reality (`success=False`).
   - Consolidation: synthesize experience + outcome into durable knowledge.
   - Second encounter: decide under updated memory -> verified that recalled lesson changes decision to exponential backoff.
2. `test_seed_persists_and_uses_three_retrieval_routes`:
   - Verify SQLite persistence across process re-initialization.
   - Verify that 3 retrieval routes (`semantic`, `lexical`, `entity`) are activated.

**Command:**
```bash
/Users/vineetpandey/.local/bin/uv run --with pytest pytest -q
```
**Result:** `ModuleNotFoundError: No module named 'mnexa_seed'` (Confirmed RED state).

---

### B. GREEN State Implementation ([`mnexa_seed.py`](file:///Users/vineetpandey/Desktop/mnexa/mnexa_seed.py))
Created `mnexa_seed.py` implementing:
- **Ports**: `Embedder`, `Meter`.
- **Read Models**: `Item`, `Hit`, `Decision`.
- **Append-Only Commit Store**: Single `commits` SQLite table with plane separation (`historical` vs `interpretive`), version tracking, metadata, and JSON serialized attributes.
- **Epistemic Snapshotting (`AS_OF(N)`)**: `watermark()` and `_searchable_as_of(n)` ensuring immutable recall views.
- **3-Channel Reciprocal Rank Fusion Recall**:
  - *Channel 1*: Vector cosine similarity (`_cos`).
  - *Channel 2*: Token Jaccard index (`_tokens`).
  - *Channel 3*: Entity set intersection.
  - *Fusion*: Score = $\sum \frac{1}{60 + \text{rank}}$.
- **Cognitive Cycle**: `decide()` budgeting memory segments, logging `ContextAssembled` and `DecisionMade` events.
- **Consolidation**: `observe_outcome()` and `consolidate()` appending durable `belief` items to the `interpretive` plane.

**Command:**
```bash
/Users/vineetpandey/.local/bin/uv run --with pytest pytest -q
```
**Result:** `2 passed in 0.03s` (Confirmed GREEN state).

---

## 3. Key Invariants & Architectural Artifacts

- **Persistence Layer**: `commits` table in SQLite (`plane`, `object_id`, `version`, `kind`, `text`, `entities`, `refs`, `embedding`, `metadata`).
- **Plane Separation**: `historical` (raw immutable logs) vs `interpretive` (consolidated beliefs with version incrementing).
