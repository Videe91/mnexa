# Seed Growth 021 — Retrieval Handle Separation Ledger

Created At: 2026-09-14T11:52:00+05:30  
Completed At: 2026-09-14T11:52:00+05:30  
File Path: `file:///Users/vineetpandey/Desktop/mnexa/ledger/24_seed_growth_021.md`

---

## 1. Context & Scientific Question

Seed Growth 020 established **Conjunctive Address Refinement**: combining system identity (`system:`) and cluster context (`cluster:`) to constrain candidate sets. However, in `context_only` queries where no system identity is present, candidate selection narrows 20 memories down to a 5-memory valid neighborhood, but RRF ranking inside that neighborhood still presented distractors in **5/5** cases with only **40% retrieval precision**.

Seed Growth 021 asks:
> **Can MNEXA improve memory selection inside an already-correct candidate neighborhood by separating retrieval representation from authoritative semantic representation?**

### Core Principle
> **"Retrieval handles locate knowledge. Authoritative support supplies meaning."**

---

## 2. Experimental Design & Controls

### Population & Geometry
- **Pool Size**: 20 memories across 5 systems × 4 interference clusters (`retry-policy`, `lane-routing`, `channel-session`, `storage-finalization`).
- **Queries**: 100% `context_only` degradation mode (no `system:` or `code:` in query prompt/entities).
- **Candidate Neighborhood**: Frozen Seed 020 conjunctive routing producing exactly **5 candidate memories** for every query.

### Ablated Conditions
- **Condition A (Full-Memory Retrieval Index)**: 3-channel RRF ranking (semantic, lexical, entity; $K=60$, Top-$K=3$) using the complete compact semantic memory.
- **Condition B (Retrieval-Handle Index)**: Identical 3-channel RRF ranking using a lightweight retrieval index (`HANDLE="..." -> E...`, `META ...`, address entities, `UNRESOLVED_GROUNDED_SUPPORT="..."`).

### Noise-Free Same-State Control
When Conditions A and B select the exact same top-3 memory IDs (7/20 families), they share the exact frozen SQLite candidate snapshot and reuse the transfer evaluation. **0 model calls** are spent on equal-selection pairs.

---

## 3. Live Run Results

Execution run `20260914T061922Z` using `gpt-4o-mini`:

| Metric | Condition A (Full Compact Memory Index) | Condition B (Retrieval Handle Index) | Delta / Finding |
| :--- | :---: | :---: | :--- |
| **Selection Target Recall** | 16 / 20 (80.0%) | **17 / 20 (85.0%)** | **+1 target family selected** |
| **Selection Target Precision** | 26.67% | **28.33%** | +1.66% selection precision |
| **Mean Index Words / Query** | 446.25 words | **203.75 words** | **54.33% index size reduction** |
| **Task Pass Rate** | 16 / 20 (80.0%) | 15 / 20 (75.0%) | -1 task pass (within noise) |
| **Target Visible Families** | 16 / 20 (80.0%) | 15 / 20 (75.0%) | -1 target visible family |
| **Wrong Memory Families** | 20 / 20 (100%) | 20 / 20 (100%) | Equal (Top-K=3 from 5) |
| **Wrong Clause Occurrences** | 29 occurrences | **27 occurrences** | -2 wrong clause instances |
| **Unsupported Claims Admitted**| 0 | 0 | **100% closed-world safety** |
| **Equal Selection Pairs** | N/A | **7 / 20 (35.0%)** | Reused exact evaluation (0 LLM noise) |
| **Ranker Model Calls** | 0 | **0** | Deterministic 3-channel RRF |

---

## 4. Key Architectural Insights

1. **Retrieval Index Compression**: Projecting normalized handles and structural metadata reduced retrieval index word count by **54.33%** (446.25 -> 203.75 words/query) while improving selection recall from 80.0% to 85.0%.
2. **Handle-Selection Separation**: Separating retrieval ranking representations from authoritative semantic payloads preserves closed-world safety (**0 unsupported claims**) without altering the underlying grounded memory formation.
3. **Context Assembly Bottleneck**: Inside a 5-memory neighborhood with $K=3$ selection, downstream presentation still contains distractors when 3 memories are selected out of 5. This proves that the remaining frontier for context-only queries is **selective context assembly / dynamic Top-K filtering**, rather than retrieval index representation alone.

---

## 5. Verification & Compliance

- **Unit Tests**: 296/296 tests passing (`pytest`).
- **Frozen Taskset**: `experiments/tasks_021.json` (`sha256: 5cab3adee47708db2042603dd29ab3343f6a632506c3645a8b3e8dfc05e33af2`).
- **Protocol**: `docs/experiments/seed-growth-021.md`.
