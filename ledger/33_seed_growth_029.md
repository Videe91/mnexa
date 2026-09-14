# Ledger 33 — Seed Growth 029: Frozen Context Reasoning

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Exploratory fresh frozen-context reasoning ablation  
**Principle:** *MNEXA fixes the evidence. The model is free to change how it reasons over that evidence.*

---

## 1. Executive Summary

Seed Growth 029 is the first experiment executed across the ADR-0017 structural boundary separating MNEXA context preparation from external model reasoning.

For each of 20 benchmark families, MNEXA prepared **exactly one frozen `ContextFrame`** (1 recall, 1 context assembly, 1 evidence hash). The external model consumed that literal same `ContextFrame` **twice**:
- **Condition A:** Standard reasoning prompt without competing-hypothesis instruction.
- **Condition B:** Epistemic competing-hypothesis reasoning instruction framing retrieved memories as alternative hypotheses rather than cumulative facts.

The architectural boundary held with 100% precision (`adr_0017_boundary_valid = true`, `context_hash_mismatch_pairs = 0`). Under 100% identical evidence, competing-hypothesis framing increased strict exclusive decision passes from **13/20 (65%)** to **16/20 (80%)**, yielding 4 exclusive rescues against 1 harm.

---

## 2. Hard Architectural Controls (ADR-0017 Verification)

| Metric | Target / Expected | Actual Live Result | Status |
| :--- | :---: | :---: | :---: |
| **Context Preparation Calls** | 20 | 20 | PASSED |
| **Recall Calls** | 20 | 20 | PASSED |
| **Context Assembly Calls** | 20 | 20 | PASSED |
| **Model Reasoner Calls** | 40 | 40 | PASSED |
| **Identical ContextFrame Hashes (A/B)** | 20 | 20 | PASSED |
| **Context Hash Mismatch Pairs** | 0 | 0 | PASSED |
| **Identical Context Objects (A/B)** | 20 | 20 | PASSED |
| **ContextFrame Integrity Valid** | 20/20 | 20/20 | PASSED |
| **ADR-0017 Boundary Valid Gate** | `true` | `true` | **VALID** |

Causal validity requirement (`adr_0017_boundary_valid == true` and `context_hash_mismatch_pairs == 0`) is fully satisfied. The observed A/B differences are strictly caused by model reasoning instruction changes over identical MNEXA-supplied context.

---

## 3. Key Experimental Results

### Primary Decision Performance (Exclusive Grader)

| Metric | Condition A (Standard) | Condition B (Competing-Hypothesis) | Delta / Benefit |
| :--- | :---: | :---: | :---: |
| **Strict Exclusive Passes** | **13 / 20 (65.0%)** | **16 / 20 (80.0%)** | **+3 (+15.0%)** |
| **Target Rule Present** | 13 / 20 | 16 / 20 | +3 |
| **Competing Rule Mentions** | 3 families | 2 families | -1 family |
| **Total Competing Rule Hits** | 3 | 2 | -1 hit |
| **Exclusive Rescues (A fail → B pass)** | — | **4 families** | — |
| **Exclusive Harms (A pass → B fail)** | — | **1 family** | — |

### Multi-Memory Context Slice (13 Families with $K > 1$)

| Metric | Condition A | Condition B | Delta |
| :--- | :---: | :---: | :---: |
| **Multi-Memory Families ($K > 1$)** | 13 | 13 | — |
| **Multi-Memory Exclusive Passes** | **8 / 13 (61.5%)** | **10 / 13 (76.9%)** | **+2 (+15.4%)** |
| **Multi-Memory Competing Mentions** | 2 | 1 | -1 |

### Per-Cluster Exclusive Pass Rates

| Interference Cluster | Condition A | Condition B | Rescues | Harms | Net Delta |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `channel-session` (5 fams) | 4 / 5 (80%) | 4 / 5 (80%) | 0 | 0 | 0 |
| `lane-routing` (5 fams) | 3 / 5 (60%) | 4 / 5 (80%) | 1 | 0 | +1 |
| `retry-policy` (5 fams) | 3 / 5 (60%) | 4 / 5 (80%) | 2 | 1 | +1 |
| `storage-finalization` (5 fams) | 3 / 5 (60%) | 4 / 5 (80%) | 1 | 0 | +1 |

---

## 4. Context & Retrieval Stack Telemetry

- **Taskset SHA256:** `d3efd44dd182af8399678ba8f9325f90dd93006667a0d2d7209a6187d23b5a22`
- **Model:** `gpt-4o-mini`
- **Embedder:** `sentence-transformers/all-MiniLM-L6-v2`
- **Candidate Neighborhood:** 5 families per query
- **Context Breadth Distribution ($K$):**
  - $K=1$: 7 families (35%)
  - $K=2$: 4 families (20%)
  - $K=3$: 9 families (45%)
  - **Mean $K$:** 2.1 memories / context
  - **Mean Context Words:** 191.45 words
- **Active Channel Count Distribution:**
  - 1 active channel: 4 families (20%) — preserved Top-3 via Seed 027 evidence quorum
  - 2 active channels: 16 families (80%) — pruned via Seed 024/027 Pareto boundary
- **Unsupported Claims Admitted:** 0 / 20 bundles

---

## 5. Architectural & Cognitive Insights

1. **MNEXA vs Model Responsibility:**
   MNEXA's job is to retrieve, filter, and freeze high-quality context into an immutable `ContextFrame`. The model's job is cognitive reasoning over that context. Seed 029 proves that when MNEXA holds uncertainty (multi-memory context), explicit competing-hypothesis instructions help the external cognitive model select the single target hypothesis rather than merging conflicting candidate rules.

2. **Clean Causal Separation:**
   Unlike Seed 028 (where prompt coupling caused 5 recall presentation errors because the reasoning instruction leaked into the recall query), Seed 029 guarantees 100% frozen evidence. Zero hash mismatches occurred across 20 family pairs.

3. **Net Benefit:**
   Condition B improved pass rate in 3 out of 4 interference clusters, yielding 4 rescues vs 1 harm (+15.0% net overall improvement).

---

## 6. Verification & Artifacts

- Implementation: `experiments/seed_growth_029.py`
- Task Generator: `experiments/make_tasks_029.py`
- Benchmark Fixtures: `experiments/tasks_029.json` (SHA256: `d3efd44dd182af8399678ba8f9325f90dd93006667a0d2d7209a6187d23b5a22`)
- Unit Tests: `tests/test_seed_growth_029.py` (19 tests passing)
- Run Artifact: `experiments/results/20260914T122844Z/result.json`
