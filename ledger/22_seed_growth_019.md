# Seed Growth 019 — Degraded Identity Activation

**Run ID**: `20260914T044729Z`  
**Taskset SHA256**: `6b80cb0dd1e1c7c283ee29bd99cf3fc5fef7f79bbbb2141a7e3b5d502a7b1032`  
**Model**: `gpt-4o-mini`  
**Embedder**: `sentence-transformers/all-MiniLM-L6-v2`  
**Classification**: Exploratory fresh degraded identity activation ablation  

---

## Executive Summary

Seed Growth 019 tested whether MNEXA memory activation degrades gracefully as exact identity metadata is progressively removed (`full_identity` → `code_only` → `system_only` → `context_only`).

The hypothesis—**"Addressing should degrade gracefully"**—was **confirmed**.

Hierarchical candidate selection (`code` → `system` → `cluster` → `domain` → `global`) improved overall task pass rate from **75.0% (15/20) to 95.0% (19/20)**, increased mean retrieval precision from **45.0% to 65.8%**, increased target recall from **75.0% to 90.0%**, and reduced mean candidate set size from **7.25 to 2.75 memories**, with **zero global fallback queries** (vs 5 in Seed 018 baseline).

---

## Primary Results Comparison

| Metric | Condition A (Seed 018 Identity Overlap) | Condition B (Seed 019 Hierarchical) | Delta |
| :--- | :---: | :---: | :---: |
| **Overall Semantic Task Passes** | 15 / 20 (75.0%) | **19 / 20 (95.0%)** | **+4 (+20.0%)** |
| **Target Clause Visible** | 15 / 20 (75.0%) | **18 / 20 (90.0%)** | **+3 (+15.0%)** |
| **Families with Wrong Memory** | 15 / 20 (75.0%) | **10 / 20 (50.0%)** | **-5 (-25.0%)** |
| **Mean Retrieval Precision** | 45.0% | **65.8%** | **+20.8%** |
| **Mean Retrieval Recall** | 75.0% | **90.0%** | **+15.0%** |
| **Mean Candidate Count** | 7.25 | **2.75** | **-4.50 (-62.1%)** |
| **Global Fallback Queries** | 5 / 20 (25.0%) | **0 / 20 (0.0%)** | **-5 (-25.0%)** |
| **Mean Memory Words** | 187.80 | **150.00** | **-20.1%** |

---

## Degradation Curve by Mode

### 1. `full_identity` (system + code)
- **Condition A (Seed 018)**: 4/5 passes (80.0%), candidate count 4.0 (retained all 4 sharing system), precision 43.3%.
- **Condition B (Hierarchical)**: **5/5 passes (100.0%)**, candidate count **1.0** (narrowed strictly to code), precision **100.0%**, 0 wrong memory.

### 2. `code_only` (code)
- **Condition A (Seed 018)**: 5/5 passes (100.0%), candidate count 1.0, precision 100.0%.
- **Condition B (Hierarchical)**: **5/5 passes (100.0%)**, candidate count **1.0**, precision **100.0%**, 0 wrong memory.

### 3. `system_only` (system)
- **Condition A (Seed 018)**: 4/5 passes (80.0%), candidate count 4.0, precision 23.3%.
- **Condition B (Hierarchical)**: **4/5 passes (80.0%)**, candidate count **4.0**, precision 20.0%.

### 4. `context_only` (cluster)
- **Condition A (Seed 018)**: 2/5 passes (40.0%), candidate count 20.0 (global pool fallback), precision 13.3%.
- **Condition B (Hierarchical)**: **5/5 passes (100.0%)**, candidate count **5.0** (narrowed to cluster neighborhood), precision **43.3%**.

---

## Query Routing Tiers

- **Code Tier Matches**: 10 / 20 (50.0%) [5 `full_identity` + 5 `code_only`]
- **System Tier Matches**: 5 / 20 (25.0%) [5 `system_only`]
- **Cluster Tier Matches**: 5 / 20 (25.0%) [5 `context_only`]
- **Domain Tier Matches**: 0 / 20 (0.0%)
- **Global Fallback Queries**: 0 / 20 (0.0%)
- **Router LLM Calls**: 0

---

## Paired Rescues and Harms

- **Task Rescues**: 5 families (25.0%) [3 `context_only`, 1 `full_identity`, 1 `code_only`]
- **Task Harms**: 1 family (5.0%) [1 `system_only` family where 4-memory system neighborhood still exhibited internal RRF interference]
- **Visibility Rescues**: 4 families (20.0%)

---

## Control Invariants & Verification

- `all_target_lessons_identical_between_conditions`: **true**
- `all_target_source_evidence_equal`: **true**
- `all_transfer_queries_equal`: **true**
- `all_compact_renderers_equal`: **true**
- `all_context_budget_configuration_equal`: **true**
- `all_reasoners_equal`: **true**
- `all_candidate_selection_from_same_full_pool`: **true**
- `hierarchical_router_used_family_id`: **false**
- `hierarchical_router_used_semantic_clause`: **false**
- `hierarchical_router_used_semantic_grader`: **false**
- `hierarchical_router_used_model`: **false**

---

## Key Insights & Next Frontier

1. **Graceful Degradation**: Instead of collapsing from a single exact record (candidate count 1.0) directly to global 20-memory pool fallback, hierarchical routing expands candidate neighborhoods gradually (1.0 → 4.0 → 5.0 memories).
2. **Context-Only Rescue**: In queries lacking exact system or code anchors (`context_only`), cluster-level addressing rescued task pass rate from **40.0% to 100.0%** by constraining candidates to 5 relevant memories instead of 20.
3. **Identified Frontier (System-Level Neighborhood RRF)**: Under `system_only` degraded addressing (candidate count 4.0), 1 family failed due to RRF ranking distractor memories within the 4-memory system neighborhood. This points to candidate ranking within identity neighborhoods as the next frontier.
