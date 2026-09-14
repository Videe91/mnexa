# Seed Growth 024 — Channel-Consensus Context Assembly

## 1. Executive Summary

Seed Growth 024 evaluated **Channel-Consensus Context Assembly** to determine context breadth ($K \in \{1, 2, 3\}$). Rather than using uncalibrated RRF score-gap magnitudes (which caused 3 over-pruning failures in Seed 023), Seed 024 inspected top-ranked winners across active discriminative retrieval channels.

### Key Principle
> **Agreement permits compression. Disagreement preserves breadth.**

### Key Results
- **Over-Pruning Reduced by 66.7%**: Over-pruning fell from **3 / 20 (15.0%) in Seed 023** to **1 / 20 (5.0%)** in Seed 024. Channel consensus preserved **15 out of 16** available target memories.
- **Safe Compaction**: **13 / 20 (65.0%)** families achieved safe compaction—retaining the target memory while pruning **1.20 distractor memories per query** on average.
- **Task Pass Parity**: Task pass rate maintained **100% parity** with fixed Top-K=3 at **14 / 20 (70.0%)** (1 rescue, 1 harm).
- **Distractor Memory Reduction**: Mean distractors presented per query fell from **2.20 to 1.00** ($-54.5\%$).
- **Wrong-Memory Elimination**: Families presenting wrong memory fell from **20 / 20 (100%) to 13 / 20 (65.0%)** ($-35.0\%$). Total wrong clause occurrences fell from **29 to 19** ($-34.5\%$).
- **Context Efficiency**: Mean model-visible memory words fell from **194.40 to 145.55** ($-25.1\%$) and segments from **2.20 to 1.65** ($-25.0\%$).
- **Zero-Model Assembly**: $0$ model calls were used for context boundary selection. $0$ unsupported claims were admitted.

---

## 2. Quantitative Benchmark Metrics

| Metric | Condition A (Fixed Top-K=3) | Condition B (Consensus Gap K) | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Fixed Target Selected** | 16 / 20 (80.0%) | 16 / 20 (80.0%) | Frozen baseline |
| **Consensus Target Retained** | N/A | **15 / 20 (75.0%)** | **93.75% target retention rate** |
| **Safe Compaction Families** | N/A | **13 / 20 (65.0%)** | Distractors removed, target kept |
| **Over-Pruning Families** | N/A | **1 / 20 (5.0%)** | **-66.7% over-pruning vs Seed 023** |
| **Upstream Rank Misses** | 4 / 20 | 4 / 20 | Unchanged |
| **No Change Families (K=3)** | N/A | 2 / 20 (10.0%) | Full K=3 retained |
| **Mean Consensus K** | 3.00 | **1.75** | Distribution: K=1: 7, K=2: 11, K=3: 2 |
| **Consensus Class Distribution** | N/A | `disagreement`: 12, `full_agree`: 7, `winner_out`: 1 | Channel agreement drives K=1/K=2 |
| **Mean Distractors Presented** | 2.20 | **1.00** | **-54.5% distractors** |
| **Families with Wrong Memory** | 20 / 20 (100%) | **13 / 20 (65.0%)** | **7 families freed from wrong memory** |
| **Wrong Clause Occurrences** | 29 | **19** | **-34.5% wrong clauses** |
| **Mean Memory Words** | 194.40 | **145.55** | **-25.1% words** |
| **Mean Memory Segments** | 2.20 | **1.65** | **-25.0% segments** |
| **Semantic Task Passes** | 14 / 20 (70.0%) | **14 / 20 (70.0%)** | **100% pass rate parity** (1 rescue, 1 harm) |
| **Target Clause Visibility** | 15 / 20 (75.0%) | 14 / 20 (70.0%) | 0 rescues, 1 harm |
| **Model Calls (Assembly)** | 0 | 0 | Deterministic consensus logic |
| **Unsupported Claims Admitted** | 0 | 0 | Closed-world safety intact |

---

## 3. Cluster Analysis

### Fixed Top-K=3 vs Consensus Gap K

| Interference Cluster | Fixed Task Passes | Consensus Task Passes | Fixed Wrong Memory Fams | Consensus Wrong Memory Fams | Mean Fixed Words | Mean Consensus Words |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `channel-session` | 4 / 5 (80%) | 4 / 5 (80%) | 5 / 5 | **2 / 5** | 180.4 | **126.2** |
| `lane-routing` | 4 / 5 (80%) | 4 / 5 (80%) | 5 / 5 | **2 / 5** | 184.8 | **130.2** |
| `retry-policy` | 2 / 5 (40%) | 2 / 5 (40%) | 5 / 5 | 5 / 5 | 190.2 | **172.4** |
| `storage-finalization` | 4 / 5 (80%) | 4 / 5 (80%) | 5 / 5 | **4 / 5** | 222.2 | **153.4** |

In `channel-session` and `lane-routing`, wrong memory presentation was eliminated in **3 out of 5** families in each cluster while maintaining 100% task pass rate parity and reducing context word count by **30.0%**.

---

## 4. Architectural Findings

1. **Agreement Drives Safe Compression**: When independent retrieval channels (e.g. semantic and lexical) agree on candidate M1 ($K=1$), context compression is safe and distractor exposure is eliminated.
2. **Disagreement Preserves Breadth**: When channels disagree (e.g. semantic winner M1, lexical winner M2 $\implies K=2$), preserving all channel winners prevents over-pruning, cutting over-pruning from 15% (Seed 023) to 5% (Seed 024).
3. **Synthesis**: Channel consensus provides a robust, zero-cost, model-independent mechanism for context breadth selection in the MNEXA Attention Firewall.
