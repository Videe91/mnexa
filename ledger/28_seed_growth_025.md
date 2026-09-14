# Seed Growth 025 — Pareto-Safe Context Assembly

## 1. Executive Summary

Seed Growth 025 evaluated **Pareto-safe context assembly** against Seed 022's fixed Top-3 baseline on a fresh 20-family operational benchmark (`tasks_025.json`). The principle under test was: **do not discard a memory if no other memory clearly beats it across every active retrieval signal**.

Condition B computed the Pareto frontier across active retrieval channels (semantic, lexical, entity). Non-dominated memories were preserved up to `max_k=3`. Context assembly used 0 model calls and 0 target/oracle information.

Results show that Pareto-safe context assembly reduced wrong-memory exposure from **20/20 to 12/20 families** (a 40% reduction), lowered wrong-clause occurrences from **23 to 15**, cut mean memory words from **177.3 to 144.15**, and reduced mean context size from $K=3$ to $K=1.9$. Over-pruning affected only **1 family**, while **12 families** achieved safe compaction. Crucially, task pass rate increased from **16/20 (80%) to 17/20 (85%)**, with 2 task rescues versus 1 harm.

## 2. Quantitative Results

| Metric | Condition A (Fixed Top-3) | Condition B (Pareto Frontier) | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Fixed Target Selected Families** | 18 / 20 (90%) | 18 / 20 (90%) | Baseline target availability |
| **Pareto Target Retained Families** | N/A | 17 / 20 (85%) | 1 over-pruning loss |
| **Target on Pareto Frontier** | N/A | 17 / 20 (85%) | Frontier coverage |
| **Safe Compaction Families** | N/A | 12 / 20 (60%) | Compacted without target loss |
| **Over-Pruning Families** | N/A | 1 / 20 (5%) | Pruned target from Top-3 |
| **Upstream Rank Miss Families** | 2 / 20 (10%) | 2 / 20 (10%) | Target not in Top-3 |
| **No Change Families** | N/A | 6 / 20 (30%) | Pareto selected $K=3$ |
| **Mean Context Size ($K$)** | 3.00 | 1.90 | **-36.7% context size** |
| **Context $K$ Distribution** | 3: 20 | 1: 8, 2: 6, 3: 6 | 70% of cases pruned context |
| **Mean Distractors Presented** | 2.10 | 1.05 | **-50.0% distractor burden** |
| **Semantic Task Passes** | 16 / 20 (80%) | 17 / 20 (85%) | **+1 Task Pass Net** |
| **Target Clause Visible** | 17 / 20 (85%) | 17 / 20 (85%) | Equal net visibility |
| **Families with Wrong Memory** | 20 / 20 (100%) | 12 / 20 (60%) | **-40% wrong memory exposure** |
| **Wrong Clause Occurrences** | 23 | 15 | **-34.8% wrong clauses** |
| **Wrong Rule Contamination** | 7 / 20 (35%) | 4 / 20 (20%) | **-42.9% contamination** |
| **Mean Memory Words** | 177.30 | 144.15 | **-18.7% word reduction** |
| **Task Rescues / Harms** | N/A | 2 rescues / 1 harm | Net positive (+1) |
| **Assembler Model Calls** | 0 | 0 | 100% deterministic |
| **Unsupported Claims Admitted** | 0 | 0 | Closed-world safety intact |

## 3. Structural Breakdown

- **Frontier Size Distribution**:
  - Size 1: 8 families (40%)
  - Size 2: 7 families (35%)
  - Size 3: 4 families (20%)
  - Size 4: 1 family (5%)
- **Frontier Class Distribution**:
  - `single_nondominated_candidate`: 8 families (40%) → $K=1$
  - `multi_candidate_frontier`: 11 families (55%) → $K=2$ (6) or $K=3$ (5)
  - `frontier_outside_max_k`: 1 family (5%) → fell back to $K=3$

## 4. Key Takeaways

1. **Tradeoff-Aware Compaction**: By defining Pareto dominance across active retrieval channels (semantic, lexical, entity), MNEXA only discards a memory when another memory is strictly non-inferior across all active signals and superior on at least one.
2. **Superior Compaction vs Safety Balance**: Compared to Seed 024's channel-consensus rule, Pareto-safe assembly preserved cross-channel tradeoff candidates, reducing wrong memory exposure by 40% while improving overall task performance to 85% (17/20).
3. **Zero Model Cost**: Pareto boundary computation remains 100% analytical, consuming 0 model calls and maintaining exact closed-world safety (`unsupported_claims == 0`).
