# Seed Growth 008 — Evidence Role Boundary

**Step**: 11  
**Classification**: Exploratory Fresh Evidence Role Ablation  
**Taskset**: `experiments/tasks_008.json`  
**Taskset SHA-256**: `599c76722136307ac56b2bc7afc33ad55d9507bd136ffe97abd2dacb1d708981`  
**Run ID**: `20260913T153128Z`  
**Model**: `gpt-4o-mini`  
**Embedder**: `sentence-transformers/all-MiniLM-L6-v2`  

---

## 1. Executive Summary

Seed Growth 008 addresses the core architectural boundary exposed by Seed Growth 007:

> **Physical source-span grounding does not automatically mean epistemic knowledge eligibility.**

In Seed Growth 007, exact span grounding successfully rejected hallucinated quotes and citation smuggling, but admitted physical metadata like `EVALUATION: FAIL.` and failed candidate decisions into persistent memory, causing measured span coverage to exceed 100%.

Seed Growth 008 introduces **Evidence Role Eligibility**:

```text
STRUCTURED HISTORICAL SOURCE (5 ROLES)
- status
- failed_decision
- authoritative_correction
- operator_note
- diagnostic_metadata
          ↓
  LLM Atom Discovery Proposal
          ↓
  Exact Source-Span Grounding
          ↓
  Evidence-Role Eligibility Gate
   (role == "authoritative_correction")
          ↓
  Admitted Grounded Evidence Atoms
          ↓
  Closed-World Claim Ancestry Gate
          ↓
  Durable Persistent Memory
```

### Key Empirical Findings

| Metric | Condition A (Baseline) | Condition B (Span-Only Grounding) | Condition C (Span + Role-Gated) |
| :--- | :---: | :---: | :---: |
| **Transfer Task Success** | **0 / 20 (0%)** | **9 / 20 (45%)** | **18 / 20 (90%)** |
| **Complete Knowledge Retention** | N/A | **20 / 20 (100%)** | **20 / 20 (100%)** |
| **Ineligible Atoms Admitted** | N/A | **80 / 80** | **0 / 80 (0%)** |
| **Authoritative Precision** | N/A | **0.425 (42.5%)** | **0.850 (85.0%)** |
| **Authoritative Recall** | N/A | **0.850 (85.0%)** | **0.850 (85.0%)** |
| **Role Challenge Rejections** | N/A | N/A | **80 / 80 (100%)** |
| **Transfer Non-Knowledge Leaks** | N/A | **9 / 20 (45%)** | **0 / 20 (0%)** |
| **Unsupported Claims Admitted** | N/A | **0 (0%)** | **0 (0%)** |
| **Source Evidence Invariant** | N/A | `True` | `True` |
| **Atom Proposal Invariant** | N/A | `True` | `True` |

---

## 2. Architectural Breakthroughs

1. **Massive Performance Lift (+9 Task Passes)**:
   - In Condition B (Span Only), non-knowledge statements (status, failed decisions, speculation, metadata) entered memory, causing LLM decisions during transfer to repeat failed attempts or speculative notes (**9 non-knowledge leaks**), dropping task passes to **9/20**.
   - In Condition C (Role Gated), rejecting ineligible roles eliminated all **9 non-knowledge leaks**, raising transfer task success to **18/20 (90%)** (+9 net improvement).
2. **Doubled Authoritative Precision**:
   - Authoritative Precision jumped from **0.425** (Condition B) to **0.850** (Condition C) because all **80 ineligible atoms** were filtered out by the role gate.
3. **100% Role Challenge Rejection**:
   - The role gate encountered **80 pre-registered challenges** (4 per family: status, failed_decision, operator_note, diagnostic_metadata).
   - **80 / 80 (100%) ineligible challenges were rejected** from promotion while remaining in immutable historical trace records.
4. **Controlled Ablation Invariants**:
   - Both B and C consumed byte-identical raw historical evidence (`all_source_evidence_equal == True`) and identical model atom proposals (`all_atom_proposals_equal == True`).

---

## 3. Files Added & Modified

- `experiments/seed_growth_008.py`: Mixed-evidence atomization and evidence-role admission gate.
- `experiments/make_tasks_008.py`: Taskset generator for 20 fresh 5-role structured task families with pre-registered role challenges.
- `tests/test_seed_growth_008.py`: TDD test suite for role region parsing, span grounding, role gating, recall/precision metrics, and 3-way ablation runner (**47/47 passing**).
- `docs/experiments/seed-growth-008.md`: Pre-registered experiment specification.
- `experiments/tasks_008.json` & `experiments/tasks_008.sha256`: Frozen benchmark taskset.
