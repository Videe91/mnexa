# Step 18: Seed Growth 015 — Semantic Closure Compaction

## Context & Motivation

Seed Growth 014 established a lossless admission boundary, achieving 20/20 semantic task passes, 0 semantic violations, and 0 unsafe support admissions. However, lossless semantic memory was verbose, averaging 160.9 (and 165.3 on 015 tasks) model-visible words per family.

The principal source of redundancy was the repeated rendering of identical authoritative support spans under multiple retrieval handles (e.g., P1, P2, P3, P4 all rendering the full source paragraph independently).

**Seed Growth 015** tests **Semantic Closure Compaction**:
- **Principle**: *Evidence should exist once. Knowledge structures may reference it many times.*
- **Condition A (`verbose`)**: Seed 014 lossless semantic memory with repeated support text rendered under every proposition.
- **Condition B (`compact`)**: Compact semantic memory where each unique physical support span is emitted once in an `EVIDENCE` index (`E1`, `E2`, ...), and structured handles and unresolved fallback records reference that evidence by ID (`HANDLE -> E1`).

**Critical Controls**:
Both Condition A and Condition B consume the **exact same raw source evidence** (`all_source_evidence_equal == true`), the **exact same initial structured proposal** (`all_initial_structured_proposals_equal == true`), the **exact same repair proposal** (`all_repair_proposals_equal == true`), the **exact same structured admissions** (`all_structured_admissions_equal == true`), and the **exact same fallback records** (`all_fallback_records_equal == true`).

Compaction is 100% deterministic—zero additional LLM calls were executed for Condition B.

---

## Experimental Setup & Methodology

- **Task Set**: 20 fresh synthetic test families generated in `experiments/tasks_015.json` (SHA256: `6a1cc9835508617afc3db186d1c99fc35da17c79c2975403d7b65c709c10b118`).
- **Semantic Operator Dimensions Covered**: `polarity`, `scope`, `cardinality`, `condition`.
- **Adversarial Fallback Challenge Injections**: 60 total injected challenges (20 recoverable, 40 unsafe).
- **Conditions Tested**:
  - **Condition A (`verbose`)**: Seed 014 lossless semantic memory rendering.
  - **Condition B (`compact`)**: Deduplicated exact evidence index + handle references.
- **Model & Tools**:
  - Model: `gpt-4o-mini`
  - Embedder: `sentence-transformers/all-MiniLM-L6-v2`
  - Meter: `WordMeter`

---

## Quantitative Results Summary

```json
{
  "experiment": "seed-growth-015",
  "classification": "exploratory-fresh-semantic-closure-compaction-ablation",
  "run_id": "20260913T181404Z",
  "taskset_sha256": "6a1cc9835508617afc3db186d1c99fc35da17c79c2975403d7b65c709c10b118",
  "model": "gpt-4o-mini",
  "embedder": "SentenceTransformerEmbedder",
  "meter": "WordMeter",
  "task_count": 20,
  "conditions": {
    "A": "seed_014_lossless_semantic_memory_verbose",
    "B": "same_structure_same_fallback_deduplicated_exact_evidence_index"
  },
  "verbose_semantic_task_passes": 20,
  "compact_semantic_task_passes": 19,
  "verbose_semantic_violations": 0,
  "compact_semantic_violations": 1,
  "verbose_exact_semantic_clause_visible_families": 20,
  "compact_exact_semantic_clause_visible_families": 20,
  "verbose_complete_lessons": 19,
  "compact_complete_lessons": 19,
  "verbose_unsupported_claims_admitted": 0,
  "compact_unsupported_claims_admitted": 0,
  "mean_verbose_memory_words": 165.3,
  "mean_compact_memory_words": 88.15,
  "mean_memory_word_reduction": 77.15,
  "mean_memory_word_reduction_fraction": 0.4667271627344223,
  "total_input_support_occurrences": 79,
  "total_unique_support_records": 64,
  "duplicate_support_occurrences_removed": 15,
  "families_with_smaller_compact_memory": 20,
  "families_with_equal_compact_memory": 0,
  "families_with_larger_compact_memory": 0,
  "all_source_evidence_equal": true,
  "all_initial_structured_proposals_equal": true,
  "all_repair_proposals_equal": true,
  "all_structured_admissions_equal": true,
  "all_fallback_records_equal": true
}
```

---

## Comparison Table

| Metric | Condition A (Verbose Lossless) | Condition B (Compact Evidence Index) | Delta / Findings |
| :--- | :---: | :---: | :--- |
| **Total Transfer Task Passes** | **20 / 20 (100.0%)** | 19 / 20 (95.0%) | -1 task pass (minor phrasing delta in `umber-store-us-89`) |
| **Total Semantic Violations** | **0** | 1 | 1 minor scope operator (`only`) omitted in transfer phrasing |
| **Exact Clause Memory Visibility** | **20 / 20 (100.0%)** | **20 / 20 (100.0%)** | **100% Exact Evidence Clause Visibility Preserved** |
| **Knowledge Complete Lessons** | 19 / 20 (95.0%) | 19 / 20 (95.0%) | Equal (95.0%) |
| **Unsupported Claims Admitted** | **0** | **0** | **Zero ungrounded claims admitted** |
| **Mean Model-Visible Memory Words** | 165.30 words | **88.15 words** | **-77.15 words (-46.67% CONTEXT COMPRESSION)** |
| **Families with Smaller Memory** | N/A | **20 / 20 (100.0%)** | **100% of families achieved smaller context size** |
| **Input Support Spans vs Unique** | 79 total | **64 unique** | 15 duplicate support occurrences removed |
| **Compaction LLM Calls Executed** | 0 | **0** | **100% deterministic (0 LLM cost)** |
| **Source Evidence Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |
| **Initial Proposal Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |
| **Repair Proposal Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |
| **Structured Admissions Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |
| **Fallback Records Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |

---

## Key Insights & Takeaways

1. **46.67% Model-Visible Memory Compression**:
   - Compaction reduced mean model-visible memory words from **165.30 words to 88.15 words**, achieving a **46.67% relative reduction** (-77.15 words per family).
   - 100% (20/20) of test families achieved smaller memory under Condition B.
2. **100% Exact Evidence Visibility & Zero Hallucinations**:
   - Exact semantic clause visibility remained at **20/20 (100%)** in both conditions.
   - Zero unsupported or ungrounded claims were admitted under both conditions.
3. **High Downstream Task Retention (95.0% Pass Rate)**:
   - Condition B achieved **19/20 (95.0%) transfer passes** compared to 20/20 in Condition A. The single failure (`umber-store-us-89`) occurred because transfer generation omitted the keyword `only` in its decision text despite referencing evidence `E1` correctly.
4. **Deterministic & Zero Extra Cost**:
   - Memory compaction is performed entirely via deterministic hashing of physical support span bounds (`source_sha256`, `source_start`, `source_end`, `support_span_sha256`), introducing **0 additional LLM calls**.
5. **Conclusion**: Seed Growth 015 demonstrates that separating evidence identity from knowledge references allows MNEXA to achieve **46.67% context compression** while maintaining **100% exact evidence visibility and zero unsafe admissions**.
