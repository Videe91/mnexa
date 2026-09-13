# Step 12: Seed Growth 009 — Evidence Atomicity Boundary

## Context & Motivation

In Seed Growth 008, evidence-role gating successfully isolated authoritative corrections from diagnostic metadata, status statements, operator notes, and failed candidate decisions. However, in several test families, the atomizer bundled multiple authoritative rules into large compound grounded spans (e.g. `"Refresh the recovery lease. Wait 9 seconds."`).

**Seed Growth 009** isolates **atomic granularity**, testing whether MNEXA can distinguish between:
1. an authoritative source-grounded span; and
2. an authoritative source-grounded span that represents *exactly one* reusable proposition.

**Principle Under Test:** *"Grounded + authoritative does not automatically mean atomic."*

---

## Experimental Setup & Methodology

- **Task Set:** 20 fresh synthetic test families generated in `experiments/tasks_009.json` (SHA256: `fd2603364d8a86248c24d8f3fcbd3d626cefe86c9c11351e1fdab5675c572c22`).
- **Atomicity Challenges:** Each family includes 2 pre-registered compound-but-valid authoritative challenge spans (40 total across the 20 families).
- **Conditions Tested:**
  - **Condition A (`mnexa_role_gated_current`)**: Grounded + evidence-role eligible (Seed 008 state). Unchecked atomicity granularity.
  - **Condition B (`mnexa_atomicity_gated`)**: Grounded + evidence-role eligible + deterministic match to exactly one pre-registered canonical proposition boundary (`exact_atomic_unit`).
- **Model & Tools:**
  - Model: `gpt-4o-mini`
  - Embedder: `sentence-transformers/all-MiniLM-L6-v2`
  - Meter: `WordMeter`

---

## Quantitative Results Summary

```json
{
  "experiment": "seed-growth-009",
  "classification": "exploratory-fresh-evidence-atomicity-ablation",
  "run_id": "20260913T154552Z",
  "taskset_sha256": "fd2603364d8a86248c24d8f3fcbd3d626cefe86c9c11351e1fdab5675c572c22",
  "model": "gpt-4o-mini",
  "embedder": "sentence-transformers/all-MiniLM-L6-v2",
  "meter": "word-meter-v1",
  "task_count": 20,
  "conditions": {
    "A": "mnexa_role_gated_atomicity_unchecked",
    "B": "mnexa_role_gated_plus_atomicity_gate"
  },
  "current_task_passes": 19,
  "atomicity_task_passes": 19,
  "current_complete_lessons": 20,
  "atomicity_complete_lessons": 20,
  "mean_current_atomic_recall": 1.0,
  "mean_atomicity_atomic_recall": 1.0,
  "mean_current_atomic_precision": 0.6666666666666666,
  "mean_atomicity_atomic_precision": 1.0,
  "current_compound_atoms_admitted": 40,
  "atomicity_compound_atoms_admitted": 0,
  "current_partial_atoms_admitted": 0,
  "atomicity_partial_atoms_admitted": 0,
  "atomicity_challenges": 40,
  "current_atomicity_challenge_admissions": 40,
  "atomicity_challenge_rejections": 40,
  "atomicity_boundary_rejections": 40,
  "current_unsupported_claims_admitted": 0,
  "atomicity_unsupported_claims_admitted": 0,
  "mean_current_memory_words": 70.3,
  "mean_atomicity_memory_words": 41.65,
  "all_source_evidence_equal": true,
  "all_atom_proposals_equal": true,
  "result": "experiments/results/20260913T154552Z/result.json"
}
```

---

## Comparison Table

| Metric | Condition A (Role Gate Only) | Condition B (Role Gate + Atomicity Gate) | Lift / Impact |
| :--- | :---: | :---: | :---: |
| **Transfer Task Passes** | 19 / 20 | 19 / 20 | 0 (100% parity) |
| **Knowledge Completeness** | 20 / 20 | 20 / 20 | 0 (100% parity) |
| **Mean Atomic Recall** | 1.000 | 1.000 | 0.000 |
| **Mean Atomic Precision** | 0.6667 | **1.0000** | **+0.3333 (+50%)** |
| **Compound Atoms Admitted** | 40 | **0** | **-40 (100% removal)** |
| **Atomicity Challenge Rejections** | 0 / 40 | **40 / 40** | **100% rejection rate** |
| **Boundary Rejections** | 0 | **40** | 40 non-atomic spans rejected |
| **Unsupported Claims Admitted** | 0 | 0 | 0 across both conditions |
| **Mean Memory Word Count** | 70.30 words | **41.65 words** | **-28.65 words (-40.7%)** |
| **Invariants (Source & Proposal)** | Equal (`true`) | Equal (`true`) | Strict A/B control preserved |

---

## Key Insights & Takeaways

1. **Perfect Granularity Control:** The atomicity boundary gate removed **100% of compound atom proposals** (40/40 challenge spans rejected in Condition B vs 40 admitted in Condition A), raising `atomic_precision` from `0.6667` to `1.0000`.
2. **Context Compression Efficiency:** Eliminating compound multi-proposition spans reduced average persistent-memory context size from **70.30 words to 41.65 words (-40.7%)**, while maintaining identical knowledge completeness (20/20) and transfer task success (19/20).
3. **No Recall Degradation:** In this benchmark, atomic units were independently proposed alongside compound units by the atomizer, resulting in `1.000` recall for both conditions.
4. **Complete Stack Integrity:** MNEXA now enforces end-to-end evidence pipeline discipline:
   $$\text{ExperienceRecord} \rightarrow \text{Source Span} \rightarrow \text{Evidence Role} \rightarrow \text{Atomic Proposition} \rightarrow \text{Grounded Claim} \rightarrow \text{Reusable Knowledge}$$
