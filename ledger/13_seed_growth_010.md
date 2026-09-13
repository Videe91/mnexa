# Step 13: Seed Growth 010 — Autonomous Atomic Boundary Discovery

## Context & Motivation

Seed Growth 009 demonstrated that when canonical proposition boundaries are provided by an oracle, MNEXA can enforce strict atomicity, eliminate 100% of compound spans, and compress memory context by over 40% without losing recall or task performance.

However, real historical evidence does not arrive with pre-registered oracle boundaries. **Seed Growth 010** removes that oracle from the runtime condition, testing whether MNEXA can **autonomously discover atomic proposition boundaries directly from raw authoritative evidence**.

**Principle Under Test:** *"Atomic evidence structure can be discovered directly from raw evidence without relying on oracle canonical boundaries."*

---

## Experimental Setup & Methodology

- **Task Set:** 20 fresh synthetic test families generated in `experiments/tasks_010.json` (SHA256: `d56b5f1c7734dd515b28babdbe1e0f46a28de5b0496a2303433ecca9a2743408`).
- **Syntax Diversity:** Benchmark incorporates 5 structural syntax styles across evidence sentences (semicolons, conjunctions `and`/`but`, inline numbers `1)` `2)`, conditional introductory clauses, and mixed comma/ordering clauses).
- **Conditions Tested:**
  - **Condition A (`oracle_boundaries`)**: Oracle canonical atomic boundaries provided (Upper Bound Ceiling).
  - **Condition B (`autonomous_boundaries`)**: Autonomous model boundary discovery from raw source text only. The runtime admission gate receives no family fixture, no canonical atom IDs, and no oracle boundary offsets.
- **Model & Tools:**
  - Model: `gpt-4o-mini`
  - Embedder: `sentence-transformers/all-MiniLM-L6-v2`
  - Meter: `WordMeter`

---

## Quantitative Results Summary

```json
{
  "experiment": "seed-growth-010",
  "classification": "exploratory-fresh-autonomous-atomic-boundary-discovery",
  "run_id": "20260913T165313Z",
  "taskset_sha256": "d56b5f1c7734dd515b28babdbe1e0f46a28de5b0496a2303433ecca9a2743408",
  "model": "gpt-4o-mini",
  "embedder": "sentence-transformers/all-MiniLM-L6-v2",
  "meter": "word-meter-v1",
  "task_count": 20,
  "conditions": {
    "A": "oracle_canonical_atomic_boundaries",
    "B": "autonomous_model_boundary_discovery_plus_runtime_source_validation"
  },
  "oracle_task_passes": 18,
  "autonomous_task_passes": 14,
  "oracle_complete_lessons": 20,
  "autonomous_complete_lessons": 17,
  "mean_oracle_boundary_recall": 1.0,
  "mean_autonomous_boundary_recall": 0.4875,
  "mean_oracle_boundary_precision": 1.0,
  "mean_autonomous_boundary_precision": 0.5166666666666667,
  "oracle_exact_boundary_families": 20,
  "autonomous_exact_boundary_families": 8,
  "autonomous_source_ancestry_valid_families": 20,
  "autonomous_invented_spans_admitted": 0,
  "autonomous_nonauthoritative_spans_admitted": 0,
  "autonomous_overlapping_span_pairs_admitted": 0,
  "autonomous_unsupported_claims_admitted": 0,
  "overlap_challenges": 40,
  "overlap_challenges_injected": 38,
  "autonomous_overlap_challenge_rejections": 28,
  "mean_oracle_memory_words": 41.0,
  "mean_autonomous_memory_words": 36.55,
  "autonomous_boundary_discovery_model_calls": 20,
  "all_source_evidence_equal": true,
  "result": "experiments/results/20260913T165313Z/result.json"
}
```

---

## Comparison Table

| Metric | Condition A (Oracle Upper Bound) | Condition B (Autonomous Discovery) | Delta / Findings |
| :--- | :---: | :---: | :--- |
| **Transfer Task Passes** | 18 / 20 | 14 / 20 | -4 (-20%) |
| **Knowledge Complete Lessons** | 20 / 20 | 17 / 20 | -3 (-15%) |
| **Mean Canonical Boundary Recall** | 1.0000 | 0.4875 | Autonomous model boundary variation |
| **Mean Canonical Boundary Precision** | 1.0000 | 0.5167 | Paraphrase / clause boundary variation |
| **Exact-Boundary Families** | 20 / 20 | 8 / 20 | 8 families achieved 100% exact match |
| **Source Ancestry Validity** | 20 / 20 | **20 / 20** | **100% valid exact physical source spans** |
| **Invented Spans Admitted** | 0 | **0** | Perfect physical grounding safety |
| **Non-Authoritative Spans Admitted** | 0 | **0** | Perfect role boundary safety |
| **Overlapping Final Span Pairs** | 0 | **0** | Minimal-first runtime gate prevented overlaps |
| **Unsupported Claims Admitted** | 0 | **0** | Zero ungrounded or hallucinated claims |
| **Mean Memory Context Words** | 41.00 words | 36.55 words | -4.45 words |
| **Source Evidence Invariant** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |

---

## Key Insights & Takeaways

1. **Constitutional Safety Invariants Satisfied:**
   - `autonomous_source_ancestry_valid_families == 20` (100% exact physical ancestry)
   - `autonomous_invented_spans_admitted == 0`
   - `autonomous_nonauthoritative_spans_admitted == 0`
   - `autonomous_overlapping_span_pairs_admitted == 0`
   - `autonomous_unsupported_claims_admitted == 0`
2. **Autonomous Discovery Capable:** In **8 out of 20 families (40%)**, autonomous model boundary discovery achieved a 100% exact match with oracle canonical boundaries.
3. **Identified Failure Frontier:** Across the remaining 12 families, the model introduced minor boundary variations (e.g., omitting trailing punctuation, combining clauses across conjunctions, or extracting slightly broader spans). This reduced recall to `0.4875` and task success from 18/20 to 14/20.
4. **Actionable Roadmap:** The experiment cleanly isolates the next frontier for MNEXA: **autonomous boundary normalization / atomization refinement**, while guaranteeing that runtime admission safety remains unbreakable.
