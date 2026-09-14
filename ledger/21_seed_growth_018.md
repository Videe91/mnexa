# Seed Growth 018 — Identity-Anchored Activation

**Run ID**: `20260914T031740Z`  
**Taskset SHA256**: `ef0286d64996549cad380070db1f4cfdb46c79e2a32e2b6fa112f9e3914a56ea`  
**Model**: `gpt-4o-mini`  
**Embedder**: `sentence-transformers/all-MiniLM-L6-v2`  
**Classification**: Exploratory fresh identity-anchored activation ablation  

---

## Executive Summary

Seed Growth 018 tested whether resolving exact experience identity (`system:` and `code:`) **before** similarity ranking recovers precise memory activation under 20-memory pooled interference.

The hypothesis—**"Identity narrows. Similarity ranks."**—was **100% confirmed**.

Restricting the candidate set via exact identity addressing before running the unchanged retrieval stack restored **task pass rate from 45.0% to 100.0%**, **target recall from 45.0% to 100.0%**, and **retrieval precision from 16.7% to 100.0%**, while completely eliminating wrong-memory presentation (from 20/20 families down to 0/20) and wrong-rule final-answer contamination (from 9 families down to 0).

---

## Primary Results

| Metric | Condition A (Current Full Pool RRF) | Condition B (Identity-Anchored RRF) | Delta |
| :--- | :---: | :---: | :---: |
| **Semantic Task Passes** | 9 / 20 (45.0%) | **20 / 20 (100.0%)** | **+11 (+55.0%)** |
| **Semantic Violations** | 11 / 20 (55.0%) | **0 / 20 (0.0%)** | **-11 (-55.0%)** |
| **Target Clause Visible** | 9 / 20 (45.0%) | **20 / 20 (100.0%)** | **+11 (+55.0%)** |
| **Families with Wrong Memory** | 20 / 20 (100.0%) | **0 / 20 (0.0%)** | **-20 (-100.0%)** |
| **Wrong Clause Occurrences** | 48 | **0** | **-48** |
| **Mean Retrieval Precision** | 16.7% | **100.0%** | **+83.3%** |
| **Mean Retrieval Recall** | 45.0% | **100.0%** | **+55.0%** |
| **Wrong Rule Contamination** | 9 / 20 (45.0%) | **0 / 20 (0.0%)** | **-9 (-45.0%)** |

---

## Candidate Selection Performance

- **Identity Match Queries**: 20 / 20 (100.0%)
- **Identity Fallback Queries**: 0 / 20 (0.0%)
- **Target Selected Families**: 20 / 20 (100.0%)
- **Mean Candidate Count**: 1.0
- **Mean Candidate Precision**: 1.0 (100.0%)
- **Mean Candidate Recall**: 1.0 (100.0%)
- **Identity Router Model Calls**: 0

---

## Paired Effects & Rescues

- **Activation Rescues**: 11 families (55.0%)
- **Activation Harms**: 0 families (0.0%)
- **Visibility Rescues**: 11 families (55.0%)

---

## Resource & Context Efficiency

- **Mean Memory Words**: 243.35 (Current) → **88.25 (Anchored)** (-63.7% context overhead)
- **Mean Memory Segments**: 2.85 (Current) → **1.00 (Anchored)**

---

## Cluster-Level Breakdown

### Current Full Pool (Condition A)
- `channel-session`: 3 / 5 passes (60.0%), 12 wrong clauses, precision 20.0%
- `lane-routing`: 2 / 5 passes (40.0%), 12 wrong clauses, precision 16.7%
- `retry-policy`: 1 / 5 passes (20.0%), 14 wrong clauses, precision 0.0%
- `storage-finalization`: 3 / 5 passes (60.0%), 10 wrong clauses, precision 30.0%

### Identity-Anchored (Condition B)
- `channel-session`: **5 / 5 passes (100.0%)**, 0 wrong clauses, precision 100.0%
- `lane-routing`: **5 / 5 passes (100.0%)**, 0 wrong clauses, precision 100.0%
- `retry-policy`: **5 / 5 passes (100.0%)**, 0 wrong clauses, precision 100.0%
- `storage-finalization`: **5 / 5 passes (100.0%)**, 0 wrong clauses, precision 100.0%

---

## Control Invariants & Verification

- `all_target_lessons_identical_between_conditions`: **true**
- `all_target_source_evidence_equal`: **true**
- `all_transfer_queries_equal`: **true**
- `all_compact_renderers_equal`: **true**
- `all_context_budget_configuration_equal`: **true**
- `all_reasoners_equal`: **true**
- `all_identity_selection_from_same_full_pool`: **true**
- `identity_router_used_family_id`: **false**
- `identity_router_used_semantic_clause`: **false**
- `identity_router_used_semantic_grader`: **false**
- `identity_router_used_model`: **false**

---

## Architectural Signposts

1. **Identity as Addressing Primitive**: Seed 018 proves that experience addressing must precede similarity ranking in multi-experience memory systems.
2. **Attention Firewall Primitive**: Restricting retrieval candidates via deterministic identity anchors eliminates distractor memory presentation and reasoning contamination without requiring LLM-based routing.
