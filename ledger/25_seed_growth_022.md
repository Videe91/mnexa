# Seed Growth 022 — Non-Discriminative Channel Abstention Ledger

Created At: 2026-09-14T12:17:30+05:30  
Completed At: 2026-09-14T12:17:30+05:30  
File Path: `file:///Users/vineetpandey/Desktop/mnexa/ledger/25_seed_growth_022.md`

---

## 1. Context & Scientific Question

Seed Growth 021 separated retrieval ranking representation from authoritative semantic representation, achieving a 54.33% index size reduction, but exposed a lower-level fusion defect: inside context-only 5-memory candidate neighborhoods, every memory received an identical entity overlap score ($2.0, 2.0, 2.0, 2.0, 2.0$), yet the ranker assigned artificial sequential ranks ($1, 2, 3, 4, 5$). Reciprocal Rank Fusion (RRF) then treated those arbitrary ranks as evidence, creating candidate insertion-order bias.

Seed Growth 022 asks:
> **Should a retrieval channel be allowed to influence Reciprocal Rank Fusion when it contains no information that distinguishes candidate memories?**

### Core Principle
> **"No discrimination, no vote. Attention signals should earn their vote through information gain."**

---

## 2. Experimental Design & Controls

### Population & Geometry
- **Pool Size**: 20 memories across 5 systems × 4 interference clusters (`retry-policy`, `lane-routing`, `channel-session`, `storage-finalization`).
- **Queries**: 100% `context_only` degradation mode.
- **Candidate Neighborhood**: Frozen Seed 020 conjunctive routing returning 5 candidates per query.
- **Entity Geometry**: Intentionally tied at $2.0$ entity overlap score across all 5 candidates in every query (20/20 families).

### Ablated Conditions
- **Condition A (Seed 021 Baseline)**: Sequential rank conversion on tied scores before RRF.
- **Condition B (Abstaining Fusion)**: **Zero score recomputation**. Reuses exact A channel scores. Completely non-discriminative channels abstain ($0.0$ RRF vote); partial ties receive statistical mid-ranks.

---

## 3. Live Run Results

Execution run `20260914T064424Z` using `gpt-4o-mini`:

| Metric | Condition A (Seed 021 Baseline) | Condition B (Abstaining Fusion) | Delta / Significance |
| :--- | :---: | :---: | :--- |
| **Artificial Tie Channels** | 20 / 20 (entity channel) | **0 / 20** | **100% artificial tie elimination** |
| **Abstained Channels** | 0 / 20 | **20 / 20 (entity channel)** | **20/20 full entity abstentions** |
| **Mean Active Channels** | 3.0 channels | **2.0 channels** | Pure Semantic + Lexical fusion |
| **Selection Target Recall** | 16 / 20 (80.0%) | **18 / 20 (90.0%)** | **+2 target families selected into Top-K** |
| **Selection Target Precision** | 26.67% | **30.00%** | **+3.33% selection precision** |
| **Target Clause Visibility** | 15 / 20 (75.0%) | **17 / 20 (85.0%)** | **+2 target visible families (+10%)** |
| **Semantic Task Passes** | 15 / 20 (75.0%) | **17 / 20 (85.0%)** | **+2 task passes (+10% pass rate)** |
| **Selection Rescues** | N/A | **3 families** | Families rescued by abstention |
| **Unsupported Claims Admitted**| 0 | 0 | **100% closed-world safety** |
| **Ranker Model Calls** | 0 | **0** | Deterministic fusion policy |

---

## 4. Key Architectural Insights

1. **Information Gain Gate**: Abstaining non-discriminative channels restored target selection recall from 80.0% to **90.0%** and downstream task pass rate from 75.0% to **85.0%** without calling an LLM.
2. **Attention Firewall Primitive**: Signals that contain zero candidate-discriminating information must not manufacture preference through deterministic order bias. Every retrieval channel must earn its RRF vote through candidate discrimination.
3. **Next Frontier**: With target selection recall at 90.0%, the remaining bottleneck in context-only queries is **selective context assembly / dynamic Top-K filtering** to prevent distractor memory presentation when 3 memories are selected out of 5.

---

## 5. Verification & Compliance

- **Unit Tests**: 317/317 tests passing (`pytest`).
- **Frozen Taskset**: `experiments/tasks_022.json` (`sha256: e62e6f0a01fac12c1864e9aed236f1f9b5af471d17935cee03fee43ff70440cd`).
- **Protocol**: `docs/experiments/seed-growth-022.md`.
