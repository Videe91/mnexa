# Seed Growth 020 — Conjunctive Address Refinement

**Run ID**: `20260914T055150Z`  
**Taskset SHA256**: `35f198c2cffebeeea3eb6c6df72b724ffa2ceb325d7e1088ed7b30de29119859`  
**Model**: `gpt-4o-mini`  
**Embedder**: `sentence-transformers/all-MiniLM-L6-v2`  
**Classification**: Exploratory fresh conjunctive address refinement ablation  

---

## Executive Summary

Seed Growth 020 tested whether weaker compatible metadata should refine (narrow), rather than replace or be stopped by, a stronger address signal (`system` match refined by `cluster` match).

The hypothesis—**"Strong identity constrains. Context refines."**—was **100% confirmed**.

In the target `system_context` mode (queries containing system name and cluster context, but no exact code), conjunctive refinement narrowed candidate set size from **4.0 to 1.0 memory**, increased target visibility from **60.0% (3/5) to 100.0% (5/5)**, increased task pass rate from **80.0% (4/5) to 100.0% (5/5)**, and completely eliminated wrong-memory presentation (**5/5 families down to 0/5**).

Across the full 20-family benchmark:
- **Target Clause Visibility**: 18/20 (90.0%) → **20/20 (100.0%)**
- **Mean Retrieval Precision**: 65.8% → **85.0%**
- **Mean Retrieval Recall**: 90.0% → **100.0%**
- **Mean Candidate Count**: 2.75 → **2.00 memories**
- **Task Harms**: **0**
- **Visibility Harms**: **0**

---

## Noise-Free Controlled Evaluation

Seed 020 implemented strict candidate-state identity controls:
- **Equal Candidate Set Pairs**: 15 / 20 families (100% in `full_identity`, `code_only`, `context_only`)
- **Differing Candidate Set Pairs**: 5 / 20 families (100% in `system_context`)
- **Reused Transfer Evaluations**: 15 / 20 (exact same transfer result reused for equal candidate pairs)
- **Total Transfer Model Calls**: 25 (20 baseline + 5 additional calls for differing candidate sets)
- **Controls**: `all_equal_candidate_pairs_share_snapshot == true` & `all_equal_candidate_pairs_reused_evaluation == true`

This guaranteed that stochastic LLM variance was **100% eliminated** from the 15 control pairs, isolating the exact behavioral effect to the 5 `system_context` candidate refinement pairs.

---

## Primary Results Comparison

| Metric | Condition A (Seed 019 Hierarchical) | Condition B (Seed 020 Conjunctive) | Delta |
| :--- | :---: | :---: | :---: |
| **Overall Task Passes** | 18 / 20 (90.0%) | **19 / 20 (95.0%)** | **+1 (+5.0%)** |
| **Target Clause Visible** | 18 / 20 (90.0%) | **20 / 20 (100.0%)** | **+2 (+10.0%)** |
| **Families with Wrong Memory** | 10 / 20 (50.0%) | **5 / 20 (25.0%)** | **-5 (-25.0%)** |
| **Wrong Clause Occurrences** | 17 | **8** | **-9 (-52.9%)** |
| **Mean Retrieval Precision** | 65.8% | **85.0%** | **+19.2%** |
| **Mean Retrieval Recall** | 90.0% | **100.0%** | **+10.0%** |
| **Mean Candidate Count** | 2.75 | **2.00** | **-0.75 (-27.3%)** |
| **Mean Candidate Precision** | 61.25% | **80.0%** | **+18.75%** |
| **Mean Memory Words** | 150.75 | **120.90** | **-19.8%** |

---

## Degradation & Refinement Geometry

### 1. `full_identity` (system + code) — Reused Control
- Candidate geometry: A = 1, B = 1 (15/15 equal control)
- **Pass rate**: 5/5 (100.0%) | **Target visible**: 5/5 (100.0%) | **Wrong memory**: 0 | **Precision**: 100.0%

### 2. `code_only` (code) — Reused Control
- Candidate geometry: A = 1, B = 1 (15/15 equal control)
- **Pass rate**: 5/5 (100.0%) | **Target visible**: 5/5 (100.0%) | **Wrong memory**: 0 | **Precision**: 100.0%

### 3. `system_context` (system + cluster) — Active Refinement Frontier
- Candidate geometry: A = 4, B = 1 (**refinement from 4 memories down to 1**)
- **Condition A (Seed 019)**: 4/5 passes (80.0%), 3/5 target visible (60.0%), 5/5 families with wrong memory (9 occurrences), precision 23.3%, recall 60.0%.
- **Condition B (Seed 020)**: **5/5 passes (100.0%)**, **5/5 target visible (100.0%)**, **0 families with wrong memory (0 occurrences)**, **precision 100.0%**, **recall 100.0%**.

### 4. `context_only` (cluster) — Reused Control
- Candidate geometry: A = 5, B = 5 (15/15 equal control)
- **Pass rate**: 4/5 (80.0%) | **Target visible**: 5/5 (100.0%) | **Wrong memory**: 5/5 (8 occurrences) | **Precision**: 40.0%

---

## Refinement Telemetry

- **Accepted Refinement Steps**: 5 / 5 (`system` matched → `cluster` refinement accepted)
- **Rejected Refinement Steps**: 0
- **Empty Intersection Protections**: 0
- **Task Rescues**: 1 family (in `system_context`)
- **Task Harms**: **0**
- **Visibility Rescues**: 2 families (in `system_context`)
- **Visibility Harms**: **0**
- **Router LLM Calls**: **0**

---

## Control Invariants & Verification

- `all_equal_candidate_pairs_share_snapshot`: **true**
- `all_equal_candidate_pairs_reused_evaluation`: **true**
- `all_target_lessons_identical_between_conditions`: **true**
- `all_target_source_evidence_equal`: **true**
- `all_transfer_queries_equal`: **true**
- `all_compact_renderers_equal`: **true**
- `all_context_budget_configuration_equal`: **true**
- `all_reasoners_equal`: **true**
- `all_candidate_selection_from_same_full_pool`: **true**
- `conjunctive_router_used_family_id`: **false**
- `conjunctive_router_used_semantic_clause`: **false**
- `conjunctive_router_used_semantic_grader`: **false**
- `conjunctive_router_used_model`: **false**

---

## Architectural Signposts

1. **Conjunctive Address Resolution**: Weaker metadata (such as cluster context) refines strong identity neighborhoods (system) when compatible, resolving ambiguity without breaking exact-code addressing or risking empty candidate sets.
2. **Attention Firewall Addressing Lattice**:
   ```text
   Available Memory Population
                ↓
   Strongest Matching Identity Address (code / system)
                ↓
   Compatible Contextual Refinement (cluster / domain)
                ↓
   Restricted Candidate Neighborhood
                ↓
   3-Channel RRF Similarity Ranking
                ↓
   Active Compact Memory Context
                ↓
   Downstream Transfer Reasoning
   ```
