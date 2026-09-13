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
| **11** | **Seed Growth 008** | Evidence Role Boundary Ablation | Fresh 20 synthetic task families (`tasks_008.json`, sha256 frozen), testing Condition A (Baseline), B (Exact Span Grounding Only), C (Exact Span + Authoritative Role Gate) | 0 / 20 | **B: 9 / 20**<br>**C: 18 / 20** | **+9 (B)**<br>**+18 (C)** | **Evidence Role Gate doubled precision from 0.425 (B) to 0.850 (C), eliminated all 9 non-knowledge leaks, and rejected 80/80 (100%) ineligible role challenges** (`all_source_evidence_equal == True`, `all_atom_proposals_equal == True`). |
| **12** | **Seed Growth 009** | Evidence Atomicity Boundary Ablation | Fresh 20 synthetic task families (`tasks_009.json`, sha256 frozen), testing Condition A (Role Gate Only), B (Role Gate + Atomicity Gate) | 0 / 20 | **A: 19 / 20**<br>**B: 19 / 20** | **+19 (A)**<br>**+19 (B)** | **Atomicity Gate eliminated 100% (40/40) of compound atom proposals, raised atomic precision from 0.6667 (A) to 1.0000 (B), and compressed memory context by 40.7% (70.3 to 41.65 words)** (`all_source_evidence_equal == True`, `all_atom_proposals_equal == True`). |
| **13** | **Seed Growth 010** | Autonomous Atomic Boundary Discovery Ablation | Fresh 20 synthetic task families (`tasks_010.json`, sha256 frozen across 5 syntax styles), testing Condition A (Oracle Canonical Boundaries), B (Autonomous Boundary Discovery) | 0 / 20 | **A: 18 / 20**<br>**B: 14 / 20** | **+18 (A)**<br>**+14 (B)** | **Autonomous Discovery achieved 100% exact match in 8/20 families with 100% physical ancestry validity, 0 invented spans, 0 non-authoritative spans, and 0 overlapping spans** (`all_source_evidence_equal == True`). Isolated boundary normalization as the remaining frontier. |
| **14** | **Seed Growth 011** | Grounded Structured Proposition Ablation | Fresh 20 synthetic task families (`tasks_011.json`, sha256 frozen across 5 syntax styles), testing Condition A (Flat Autonomous Atomization), B (Grounded Structured Proposition) | 0 / 20 | **A: 13 / 20**<br>**B: 14 / 20** | **+13 (A)**<br>**+14 (B)** | **Structured Propositions increased mean nucleus recall from 0.3500 (A) to 0.5750 (B) (+64.3%) and precision from 0.3583 to 0.6833 (+90.7%) with 0.9375 qualifier recall and 100% physical ancestry validity** (`all_source_evidence_equal == True`). Decoupled support spans from operational nuclei without severing provenance. |
| **15** | **Seed Growth 012** | Grounded Structure Repair Ablation | Fresh 20 synthetic task families (`tasks_012.json`, sha256 frozen across 5 syntax styles), testing Condition A (One-Pass Structured Memory), B (Same Proposal + Grounded Structure Repair) | 0 / 20 | **A: 12 / 20**<br>**B: 10 / 20** | **+12 (A)**<br>**+10 (B)** | **Structure Repair eliminated 100% of compound nuclei (12 to 0) and 100% of compound challenges (12 to 0), pushed mean nucleus recall to 0.8000 (+45.5%) and precision to 0.9708 (+41.2%, 97.08%), and raised exact-nucleus families from 4 to 7** (`all_source_evidence_equal == True`, `all_initial_structured_proposals_equal == True`). Proved grounded memory proposals can be challenged and repaired before promotion. |
| **16** | **Seed Growth 013** | Semantic Closure Projection Ablation | Fresh 20 synthetic task families (`tasks_013.json`, sha256 frozen across 4 semantic dimensions), testing Condition A (Nucleus as Claim Payload), B (Nucleus as Retrieval Handle + Full Support Span as Semantic Payload) | 0 / 20 | **A: 15 / 20**<br>**B: 16 / 20** | **+15 (A)**<br>**+16 (B)** | **Semantic Closure Projection achieved 16/16 (100.0%) transfer task passes and 16/16 (100.0%) exact clause visibility on supported families (vs 15/16 and 10/20 in Condition A), eliminating scope loss** (`all_source_evidence_equal == True`, `all_repaired_structured_propositions_equal == True`). Proved that projecting full support spans as claim payloads while keeping nuclei as retrieval handles closes the semantic preservation gap. |
| **17** | **Seed Growth 014** | Lossless Rejection / Grounded Fallback Ablation | Fresh 20 synthetic task families (`tasks_014.json`, sha256 frozen across 4 semantic dimensions with 60 injected adversarial fallback challenges), testing Condition A (All-or-Nothing Admission), B (Support-First Lossless Fallback) | 0 / 20 | **A: 15 / 20**<br>**B: 20 / 20** | **+15 (A)**<br>**+20 (B)** | **Support-First Lossless Fallback achieved PERFECT 20/20 (100.0%) transfer task success, 0 semantic violations, and 0/40 admitted unsafe attacks** (`all_source_evidence_equal == True`, `all_repair_proposals_equal == True`). Rescued 5 structurally failed evidence spans into `structure_status = unresolved` fallback records without generating hallucinated structure. |
| **18** | **Seed Growth 015** | Semantic Closure Compaction Ablation | Fresh 20 synthetic task families (`tasks_015.json`, sha256 frozen across 4 semantic dimensions with 60 injected adversarial fallback challenges), testing Condition A (Verbose Lossless Memory), B (Compact Evidence Index) | 0 / 20 | **A: 20 / 20**<br>**B: 19 / 20** | **+20 (A)**<br>**+19 (B)** | **Compact Evidence Index achieved 46.67% context reduction (165.30 to 88.15 words) and 100% exact evidence visibility with 0 unsafe admissions** (`all_source_evidence_equal == True`, `all_repair_proposals_equal == True`, `all_fallback_records_equal == True`). Proved evidence deduplication via handle references preserves closed-world safety while cutting context size in half. |

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
11. [`11_seed_growth_008.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/11_seed_growth_008.md): Fresh 20-family controlled evidence-role ablation & authoritative role gate evaluation.
12. [`12_seed_growth_009.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/12_seed_growth_009.md): Fresh 20-family controlled evidence-atomicity ablation & atomic boundary gate evaluation.
13. [`13_seed_growth_010.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/13_seed_growth_010.md): Fresh 20-family controlled autonomous boundary discovery ablation & runtime source validation gate evaluation.
14. [`14_seed_growth_011.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/14_seed_growth_011.md): Fresh 20-family controlled grounded structured proposition ablation & nucleus/qualifier extraction gate evaluation.
15. [`15_seed_growth_012.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/15_seed_growth_012.md): Fresh 20-family controlled grounded structure repair ablation & structure audit gate evaluation.
16. [`16_seed_growth_013.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/16_seed_growth_013.md): Fresh 20-family controlled semantic closure projection ablation & support span claim payload gate evaluation.
17. [`17_seed_growth_014.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/17_seed_growth_014.md): Fresh 20-family controlled lossless rejection / grounded fallback ablation & support-first admission gate evaluation.
18. [`18_seed_growth_015.md`](file:///Users/vineetpandey/Desktop/mnexa/ledger/18_seed_growth_015.md): Fresh 20-family controlled semantic closure compaction ablation & evidence deduplication index evaluation.











