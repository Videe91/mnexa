# MNEXA Seed Ledger: Executive Overview & Trajectory

This directory contains the immutable step-by-step ledger documenting the birth, empirical testing, diagnostic analysis, and evolution of the **MNEXA Seed** substrate.

---

## 1. Vision & Core Philosophy

MNEXA is a model-independent persistent intelligence substrate. It establishes a living cognitive loop:

```text
FIRST ENCOUNTER                 SECOND ENCOUNTER (TRANSFER)

Task                             Unseen Related Task
  ↓                                 ↓
Recall (empty)                   3-Channel RRF Recall (Semantic + Lexical + Entity)
  ↓                                 ↓
Decision (generic/failed)        Durable Reusable Lesson Surfaced
  ↓                                 ↓
Outcome Observation              Context Assembled with Memory Budget
  ↓                                 ↓
Consolidation                    Decision Changed (Protocol-Aware)
  ↓                                 ↓
Durable Lesson Appended          Successful Transfer
```

---

## 2. Phase-by-Phase Summary Matrix

| Step | Identifier | Classification | Scope / Description | Baseline Pass | MNEXA Pass | Delta | Key Architectural Finding |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **01** | **Seed Planting** | Unit TDD | Core two-file engine & unit tests | N/A | N/A | N/A | SQLite append-only commit ledger, 3-channel Reciprocal Rank Fusion, `AS_OF(N)` watermarking. |
| **02** | **Seed Growth 001** | Exploratory | 5 synthetic task families (literal string grader) | 0 / 5 | 0 / 5 | 0 | Model decisions changed dramatically, but rigid literal substring checks produced false negatives. |
| **03** | **Seed Growth 001R** | Post-Hoc Diagnostic | Offline regrade of 001 with regex graders (0 LLM calls) | 0 / 5 | 3 / 5 | +3 | Proven transfer on NebulaPay, OrchidDB, AtlasParser. Uncovered operational constraint loss in Helios/Saffron. |
| **04** | **Seed Growth 002** | Exploratory | Upgraded lossless consolidation prompt (`build_consolidation_prompt`) | 1 / 5 | 3 / 5 | +2 | Consolidation constraint preservation reached **100%**. Revealed surface-form phrasing mismatch in Helios. |
| **05** | **Seed Growth 002R** | Post-Hoc Diagnostic | Offline regrade of 002 with regex matching "each of the six parts" | 1 / 5 | 4 / 5 | +3 | Helios passed; Saffron remained a genuine failure (reasoning seat dropped `once`). |
| **06** | **Seed Growth 003** | Frozen Benchmark | Fresh 10 synthetic task families (`tasks_003.json`, sha256 frozen) | 0 / 10 | **7 / 10** | **+7** | **+7 net improvement** on unseen 10-family taskset. Pinpointed failure boundary to decision-seat prohibition omissions. |
| **07** | **Seed Growth 004** | Fresh 3-Way Ablation | Fresh 20 synthetic task families (`tasks_004.json`, sha256 frozen), testing Condition A (Baseline), B (Current MNEXA), C (MNEXA + Constraint Fidelity Prompt) | 0 / 20 | **B: 17 / 20**<br>**C: 19 / 20** | **+17 (B)**<br>**+19 (C)** | **Constraint fidelity jumped from 10% (B) to 95% (C)** with identical memory (`all_b_c_memory_equal == True`). Closed the reasoning seat information loss gap. |
| **08** | **Seed Growth 005** | Consolidation Ablation | Fresh 20 synthetic task families (`tasks_005.json`, sha256 frozen), testing Condition A (Baseline), B (Current Lossless Consolidation), C (Evidence-Disciplined Consolidation) | 0 / 20 | **B: 17 / 20**<br>**C: 20 / 20** | **+17 (B)**<br>**+20 (C)** | **Contamination dropped from 60% (B) to 0% (C)** while retaining 100% correct knowledge, achieving **20/20 (100%) transfer success** (`all_source_evidence_equal == True`). |
| **09** | **Seed Growth 006** | Claim Ancestry Ablation | Fresh 20 synthetic task families (`tasks_006.json`, sha256 frozen), testing Condition A (Baseline), B (Evidence-Disciplined Consolidation), C (Claim-Ancestry Closed-World Admission) | 0 / 20 | **B: 17 / 20**<br>**C: 17 / 20** | **+17 (B)**<br>**+17 (C)** | **Closed-World Admission Gate admitted 80/80 (100%) supported claims with 0 unsupported claims.** Enforced *"No knowledge without ancestry"* by shifting memory authority to runtime admission (`all_source_evidence_equal == True`). |
| **10** | **Seed Growth 007** | Raw Evidence Atomization Ablation | Fresh 20 synthetic task families (`tasks_007.json`, sha256 frozen), testing Condition A (Baseline), B (Oracle Grounded Claims), C (Raw Span Grounded Claims) | 0 / 20 | **B: 15 / 20**<br>**C: 15 / 20** | **+15 (B)**<br>**+15 (C)** | **Deterministic Span Grounding achieved parity with Oracle Grounding while rejecting 40/40 (100%) adversarial ungrounded challenges** with 0 ungrounded or unsupported admissions (`all_source_evidence_equal == True`). |

---

## 3. Directory Index

1. [`01_seed_planting.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/01_seed_planting.md): Core two-file seed implementation (`mnexa_seed.py`, `tests/test_seed.py`).
2. [`02_seed_growth_001.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/02_seed_growth_001.md): Initial experiment infrastructure (`model_adapter.py`, `experiments/seed_growth.py`, `tasks.json`) & initial 001 run.
3. [`03_seed_growth_001r.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/03_seed_growth_001r.md): Offline diagnostic regrade of 001 (`experiments/graders_001r.json`, `experiments/regrade_seed_growth.py`).
4. [`04_seed_growth_002.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/04_seed_growth_002.md): Lossless consolidation prompt upgrade & Seed Growth 002 execution.
5. [`05_seed_growth_002r.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/05_seed_growth_002r.md): Offline diagnostic regrade of 002 (`experiments/graders_002r.json`).
6. [`06_seed_growth_003.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/06_seed_growth_003.md): Fresh 10-family frozen benchmark execution & full root cause failure analysis.
7. [`07_seed_growth_004.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/07_seed_growth_004.md): Fresh 20-family 3-way controlled ablation benchmark & constraint fidelity instruction evaluation.
8. [`08_seed_growth_005.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/08_seed_growth_005.md): Fresh 20-family controlled consolidation ablation & evidence-disciplined consolidation evaluation.
9. [`09_seed_growth_006.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/09_seed_growth_006.md): Fresh 20-family controlled claim ancestry ablation & closed-world admission gate evaluation.
10. [`10_seed_growth_007.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/10_seed_growth_007.md): Fresh 20-family controlled raw evidence atomization ablation & deterministic span grounding gate evaluation.




