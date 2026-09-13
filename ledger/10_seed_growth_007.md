# Seed Growth 007 — Raw Evidence Atomization & Deterministic Span Grounding

**Step**: 10  
**Classification**: Exploratory Fresh Raw Evidence Atomization Ablation  
**Taskset**: `experiments/tasks_007.json`  
**Taskset SHA-256**: `34990e657a9151e10da763c0aaa65dcc06f4abf71d85d38e060cc8d82e71ea63`  
**Run ID**: `20260913T150445Z`  
**Model**: `gpt-4o-mini`  
**Embedder**: `sentence-transformers/all-MiniLM-L6-v2`  

---

## 1. Executive Summary

Seed Growth 007 resolves the core boundary exposed by Seed 006. In Seed Growth 006, closed-world admission proved that claims could be gated against pre-registered evidence atoms, but relied on hand-authored oracle atoms (`E1`, `E2`, ...).

Seed Growth 007 eliminates the requirement for pre-registered oracle atoms by introducing **Raw Evidence Atomization & Deterministic Span Grounding**:

```text
RAW HISTORICAL EVIDENCE
          ↓
  LLM Atom Discovery Proposal
  ("text", "source_quote")
          ↓
 Deterministic Span Grounding
  - source_quote in raw_evidence?
  - source_quote count == 1?
  - text == source_quote (normalized)?
  - start/end offset & sha256 hash
          ↓
   Grounded Evidence Atoms (E1, E2, ...)
          ↓
  Closed-World Claim Ancestry Gate
          ↓
   Durable Persistent Memory
```

Furthermore, 007 explicitly attacked the runtime rejection gate by introducing **40 pre-registered adversarial atom challenges** (2 per family: 1 non-existent source quote, 1 citation smuggling quote).

### Empirical Results Summary

| Metric | Condition A (Baseline) | Condition B (Oracle Grounded Claims) | Condition C (Raw Span Grounded Claims) |
| :--- | :---: | :---: | :---: |
| **Transfer Task Success** | **0 / 20 (0%)** | **15 / 20 (75%)** | **15 / 20 (75%)** |
| **Knowledge Completeness** | N/A | **20 / 20 (100%)** | **20 / 20 (100%)** |
| **Contaminated Lessons** | N/A | 1 / 20 (5%) | 1 / 20 (5%) |
| **Model Atom Proposals** | N/A | N/A | **86** |
| **Grounded Atoms Admitted** | N/A | N/A | **86** |
| **Adversarial Atom Challenges** | N/A | N/A | **40** |
| **Adversarial Atom Rejections** | N/A | N/A | **40 (100%)** |
| **Ungrounded Atoms Admitted** | N/A | N/A | **0 (0%)** |
| **Unsupported Claims Admitted** | N/A | N/A | **0 (0%)** |
| **Mean Source Span Coverage** | N/A | N/A | **1.075 (107.5%)** |
| **Source-Evidence Equal** | N/A | `True` | `True` |

---

## 2. Key Architectural Invariants Proven

1. **Parity Between Oracle and Raw Span Discovery**:
   - Condition C (Raw Span Grounded) achieved identical transfer task success (**15 / 20**) and complete lesson knowledge retention (**20 / 20**) to Condition B (Oracle Grounded).
2. **100% Adversarial Challenge Rejection**:
   - The runtime span grounding gate encountered **40 adversarial challenges** designed to smuggle hallucinated facts or invalid quotes.
   - **40 / 40 (100%) adversarial challenges were rejected** by `admit_grounded_atoms`.
3. **Zero Ungrounded or Unsupported Admissions**:
   - `ungrounded_atoms_admitted == 0`
   - `unsupported_claims_admitted == 0`
   - Memory promotion remains strictly bounded by physical evidence spans.

---

## 3. Files Added & Modified

- `experiments/seed_growth_007.py`: Raw evidence atomization and span grounding pipeline.
- `experiments/make_tasks_007.py`: Generator for 20 fresh task families with pre-registered adversarial challenges.
- `tests/test_seed_growth_007.py`: Unit tests for span grounding, JSON parsing, and 3-way ablation runner (37/37 passing).
- `docs/experiments/seed-growth-007.md`: Pre-registered experiment specification.
- `experiments/tasks_007.json` & `experiments/tasks_007.sha256`: Frozen benchmark taskset.
