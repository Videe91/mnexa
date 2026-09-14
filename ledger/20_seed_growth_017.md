# Step 20: Seed Growth 017 — Pooled Memory Interference

## Context & Motivation

Seed Growth 016 established that compact semantic memory is stable across repeated transfer trials. However, all prior experiments evaluated memory in single-family isolation (1 learned memory in the database at a time).

**Seed Growth 017** tests **Pooled Memory Interference**:
- **Question**: Can MNEXA continue to retrieve, activate, and use the correct learned experience when 20 compact memories coexist in the same database?
- **Experimental Design**: 20 fresh synthetic test families divided into 4 semantic interference clusters (`retry-policy`, `lane-routing`, `channel-session`, `storage-finalization`). Each target query is evaluated under two conditions:
  - **Condition A (`isolated`)**: Target compact memory alone in the database (1 memory).
  - **Condition B (`pooled`)**: Same target compact memory coexisting with all 19 other learned memories in the database (20 memories total, including 4 near-neighbors within the same cluster).
- **Snapshot Isolation**: The 20-memory pooled SQLite state is built once, closed, and copied byte-for-byte into private evaluation databases for every target query (`all_pooled_evaluations_from_same_snapshot == true`, `all_snapshot_copies_byte_identical_before_evaluation == true`). Evaluation writes cannot contaminate subsequent queries.

---

## Experimental Setup & Methodology

- **Task Set**: 20 fresh synthetic test families in `experiments/tasks_017.json` (SHA256: `6927a52bc41a02828971b8f736583d2d39a06c295e5583628f28b4d7737441c8`).
- **Interference Clusters**: 4 clusters × 5 families each = 20 families.
- **Distractor Load**: 19 distractors per target (4 near-neighbors + 15 broader distractors).
- **Conditions Tested**:
  - **Condition A (`isolated`)**: Single target compact memory.
  - **Condition B (`pooled`)**: Target compact memory + 19 distractors in 3-channel RRF index.
- **Model & Tools**:
  - Model: `gpt-4o-mini`
  - Embedder: `sentence-transformers/all-MiniLM-L6-v2`
  - Meter: `WordMeter`

---

## Quantitative Results Summary

```json
{
  "experiment": "seed-growth-017",
  "classification": "exploratory-fresh-pooled-memory-interference-ablation",
  "run_id": "20260914T030444Z",
  "taskset_sha256": "6927a52bc41a02828971b8f736583d2d39a06c295e5583628f28b4d7737441c8",
  "model": "gpt-4o-mini",
  "embedder": "SentenceTransformerEmbedder",
  "meter": "WordMeter",
  "task_count": 20,
  "pool_size": 20,
  "distractors_per_target": 19,
  "near_neighbors_per_target": 4,
  "conditions": {
    "A": "isolated_compact_memory_target_only",
    "B": "pooled_compact_memory_target_plus_nineteen_distractors"
  },
  "isolated_task_passes": 19,
  "pooled_task_passes": 10,
  "isolated_task_pass_rate": 0.95,
  "pooled_task_pass_rate": 0.5,
  "isolated_semantic_violations": 1,
  "pooled_semantic_violations": 10,
  "isolated_target_clause_visible_families": 20,
  "pooled_target_clause_visible_families": 10,
  "isolated_families_with_wrong_memory_presented": 0,
  "pooled_families_with_wrong_memory_presented": 20,
  "isolated_wrong_family_clause_occurrences": 0,
  "pooled_wrong_family_clause_occurrences": 50,
  "mean_isolated_retrieval_precision": 1.0,
  "mean_pooled_retrieval_precision": 0.16666666666666666,
  "mean_isolated_retrieval_recall": 1.0,
  "mean_pooled_retrieval_recall": 0.5,
  "isolated_wrong_rule_contamination_families": 0,
  "pooled_wrong_rule_contamination_families": 8,
  "paired_retrieval_regret_families": 9,
  "paired_target_omission_regret_families": 9,
  "paired_contamination_regret_families": 9,
  "mean_isolated_memory_words": 85.85,
  "mean_pooled_memory_words": 243.4,
  "mean_isolated_memory_segments": 1.0,
  "mean_pooled_memory_segments": 3.0,
  "bundles_with_exact_semantic_clause_visible": 20,
  "bundle_unsupported_claims_admitted": 0,
  "all_target_lessons_identical_between_conditions": true,
  "all_target_source_evidence_equal": true,
  "all_transfer_queries_equal": true,
  "all_compact_renderers_equal": true,
  "all_context_budget_configuration_equal": true,
  "all_pooled_evaluations_from_same_snapshot": true,
  "all_isolated_evaluations_from_frozen_snapshots": true,
  "all_snapshot_copies_byte_identical_before_evaluation": true
}
```

---

## Comparison Table

| Metric | Condition A (Isolated Memory) | Condition B (Pooled 20-Memory State) | Delta / Findings |
| :--- | :---: | :---: | :--- |
| **Transfer Task Pass Rate** | **19 / 20 (95.0%)** | **10 / 20 (50.0%)** | **-45.0% DROP IN DOWNSTREAM TASK SUCCESS** |
| **Total Semantic Violations** | 1 | **10** | **+9 violations (50% violation rate in pooled setting)** |
| **Target Clause Visibility** | **20 / 20 (100.0%)** | **10 / 20 (50.0%)** | Target clause displaced in 50% of pooled queries |
| **Families with Distractors in Context** | **0 / 20 (0.0%)** | **20 / 20 (100.0%)** | **100% of queries presented wrong distractor clauses** |
| **Total Distractor Clause Occurrences** | 0 | **50 occurrences** | Mean 2.5 distractor clauses per model prompt |
| **Model-Visible Retrieval Precision** | **1.000** | **0.1667** | Severe context dilution (1/6 precision) |
| **Model-Visible Retrieval Recall** | **1.000** | **0.5000** | 50% target retrieval recall |
| **Decision Contamination Rate** | **0 / 20 (0.0%)** | **8 / 20 (40.0%)** | **40% of final decisions contained wrong-rule text** |
| **Paired Retrieval Regret** | N/A | **9 / 20 (45.0%)** | **9 families failed strictly due to memory pooling** |
| **Target Omission Regret** | N/A | **9 / 20 (45.0%)** | Target omitted in all 9 regret families |
| **Contamination Regret** | N/A | **9 / 20 (45.0%)** | Distractor clauses present in all 9 regret families |
| **Mean Model-Visible Context Words** | 85.85 words | **243.40 words** | RRF maxes out 3-segment context budget (243.4w) |
| **Mean Model-Visible Segments** | 1.0 segment | **3.0 segments** | Max 3 segments filled with distractors |
| **Memory Bundle Clause Survival** | **20 / 20 (100%)** | **20 / 20 (100%)** | 100% target evidence survival during learning |
| **Unsupported Claims Admitted** | **0** | **0** | Zero ungrounded claims admitted |
| **Target Lessons Control Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B memory control preserved |
| **Snapshot Isolation Control Invariant** | Equal (`true`) | Equal (`true`) | Byte-identical snapshot copies evaluated |

---

## Cluster-Level Interference Breakdown

| Cluster Name | Families | Isolated Passes | Pooled Passes | Pooled Target Visible | Pooled Distractor Clauses | Families with Distractors |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `channel-session` | 5 | 5 / 5 (100%) | 3 / 5 (60%) | 3 / 5 (60%) | 12 | 5 / 5 (100%) |
| `lane-routing` | 5 | 5 / 5 (100%) | 2 / 5 (40%) | 2 / 5 (40%) | 13 | 5 / 5 (100%) |
| `retry-policy` | 5 | 5 / 5 (100%) | 2 / 5 (40%) | 2 / 5 (40%) | 13 | 5 / 5 (100%) |
| `storage-finalization` | 5 | 4 / 5 (80%) | 3 / 5 (60%) | 3 / 5 (60%) | 12 | 5 / 5 (100%) |

---

## Key Insights & Takeaways

1. **PROVED POOLED MEMORY INTERFERENCE (45% Task Pass Drop)**:
   - When 20 learned memories coexisted in the same database pool, downstream transfer task success collapsed from **95.0% (19/20) to 50.0% (10/20)**.
   - **45.0% Paired Retrieval Regret (9/20 families)**: 9 families that passed cleanly in single-memory isolation failed when evaluated against the 20-memory pool.
2. **100% Distractor Presentation & 50% Target Displace Rate**:
   - In **20 / 20 (100.0%)** of pooled queries, the 3-channel Reciprocal Rank Fusion (RRF) index retrieved and presented wrong distractor clauses (50 total occurrences across 20 prompts).
   - In **10 / 20 (50.0%)** of pooled queries, distractor memories completely displaced the target memory from the 3-segment context budget (`retrieval_recall = 0.5000`, `retrieval_precision = 0.1667`).
3. **40% Wrong-Rule Decision Contamination**:
   - In 8 out of 10 failed pooled queries, the reasoner emitted the exact distractor rule text in its final decision.
4. **Memory Formation vs. Memory Activation**:
   - Memory formation remains 100% intact (`bundles_with_exact_semantic_clause_visible = 20/20`, `bundle_unsupported_claims_admitted = 0`). The target evidence is correctly stored and validated.
   - However, **memory activation/retrieval fails under pooling** because entity matching (`domain:recovery`, `cluster:retry-policy`) and lexical/semantic RRF ranking allow near-neighbor distractors to crowd out the target lesson.
5. **Architectural Conclusion**: Seed Growth 017 demonstrates that while MNEXA forms compact, grounded, and closed-world safe memories cleanly, **coexisting memories in a shared pool interfere severely with 3-channel RRF retrieval**. The primary architectural frontier has shifted from memory formation to **selective memory routing, entity-specific indexing, and ranking**.
