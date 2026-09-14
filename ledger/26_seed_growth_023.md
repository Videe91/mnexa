# Seed Growth 023 — Confidence-Gated Context Assembly

## 1. Executive Summary

Seed Growth 023 tested whether **retrieval confidence can dictate context breadth** without invoking LLM rankers or target-aware oracles. By measuring adjacent score gaps in the RRF ranking output ($g_1 = s_1 - s_2, g_2 = s_2 - s_3, g_3 = s_3 - s_4$), MNEXA dynamically assigned context cutoffs $K \in \{1, 2, 3\}$.

### Key Results
- **Safe Compaction**: In **10 / 20** families, dynamic context assembly retained the target memory while pruning **1.30 distractor memories per query** on average.
- **Distractor Memory Reduction**: Mean distractors presented per query fell from **2.15 to 0.85** ($-60.5\%$).
- **Wrong-Memory Elimination**: Families presenting wrong memories dropped from **20 / 20 to 13 / 20** ($-35\%$). Total wrong clause occurrences fell from **25 to 14** ($-44\%$).
- **Memory Efficiency**: Mean model-visible memory words fell from **191.55 to 130.25** ($-32\%$) and segments from **2.1 to 1.4** ($-33.3\%$).
- **Over-Pruning Tradeoff**: On **3 / 20** families where the target was ranked at position 2 or 3, an uncalibrated score gap after position 1 led to over-pruning, causing task pass rate to adjust from **15 / 20 (75%) to 13 / 20 (65%)**.
- **Zero-Model Assembly**: $0$ model calls were used for context boundary determination. $0$ unsupported claims were admitted.

---

## 2. Quantitative Benchmark Metrics

| Metric | Condition A (Fixed Top-K=3) | Condition B (Dynamic Gap K) | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Fixed Target Selected** | 17 / 20 (85.0%) | 17 / 20 (85.0%) | Frozen baseline |
| **Dynamic Target Retained** | N/A | 14 / 20 (70.0%) | -3 over-pruned |
| **Safe Compaction Families** | N/A | **10 / 20 (50.0%)** | Distractors removed, target kept |
| **Over-Pruning Families** | N/A | **3 / 20 (15.0%)** | Target pruned at rank 2 or 3 |
| **Upstream Rank Misses** | 3 / 20 | 3 / 20 | Unchanged |
| **No Change Families (K=3)** | N/A | 4 / 20 (20.0%) | Full K=3 retained |
| **Mean Dynamic K** | 3.00 | **1.55** | Distribution: K=1: 13, K=2: 3, K=3: 4 |
| **Mean Distractors Presented** | 2.15 | **0.85** | **-60.5% distractors** |
| **Families with Wrong Memory** | 20 / 20 (100%) | **13 / 20 (65.0%)** | **7 families freed from wrong memory** |
| **Wrong Clause Occurrences** | 25 | **14** | **-44.0% wrong clauses** |
| **Mean Memory Words** | 191.55 | **130.25** | **-32.0% words** |
| **Mean Memory Segments** | 2.10 | **1.40** | **-33.3% segments** |
| **Semantic Task Passes** | 15 / 20 (75.0%) | 13 / 20 (65.0%) | 1 rescue, 3 harms |
| **Target Clause Visibility** | 17 / 20 (85.0%) | 14 / 20 (70.0%) | 0 rescues, 3 harms |
| **Model Calls (Assembly)** | 0 | 0 | Deterministic gap logic |
| **Unsupported Claims Admitted** | 0 | 0 | Closed-world safety intact |

---

## 3. Cluster Analysis

### Fixed Top-K=3 vs Dynamic Gap K

| Interference Cluster | Fixed Task Passes | Dynamic Task Passes | Fixed Wrong Memory Fams | Dynamic Wrong Memory Fams | Mean Fixed Words | Mean Dynamic Words |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `channel-session` | 5 / 5 (100%) | 5 / 5 (100%) | 5 / 5 | **1 / 5** | 182.0 | **110.0** |
| `lane-routing` | 5 / 5 (100%) | 3 / 5 (60%) | 5 / 5 | **4 / 5** | 197.4 | **145.2** |
| `retry-policy` | 1 / 5 (20%) | 1 / 5 (20%) | 5 / 5 | **4 / 5** | 190.4 | **88.0** |
| `storage-finalization` | 4 / 5 (80%) | 4 / 5 (80%) | 5 / 5 | **4 / 5** | 196.4 | **177.8** |

In `channel-session`, wrong memory presentation was eliminated in **4 out of 5** families while preserving 100% task pass rate and reducing context word count by 39.6%.

---

## 4. Architectural Findings

1. **Context Compaction Works**: Raw uncalibrated score gaps successfully identified single-winner candidate queries in 50% of cases, eliminating 60.5% of distractor memories and 44% of wrong clause presentations.
2. **Over-Pruning Hazard**: Without absolute confidence calibration (or thresholding), relative gap maximization can aggressively select $K=1$ when the target memory is ranked at position 2 or 3 with a small score delta from position 1.
3. **Synthesis**: Confidence-gated context assembly is an essential layer of the Attention Firewall, but requires calibrated score confidence thresholds or soft density gating to avoid over-pruning valid non-rank-1 targets.
