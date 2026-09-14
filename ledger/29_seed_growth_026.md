# Seed Growth 026 — Proposition-Local Retrieval

## 1. Executive Summary

Seed Growth 026 evaluated **proposition-local retrieval** against whole-retrieval-document scoring on a fresh 20-family operational benchmark (`tasks_026.json`). The principle under test was: **retrieve the proposition, not the memory blob**.

Within each interference cluster, candidate memories shared three background propositions and differed primarily in one decision-relevant rule. Condition A scored the query against the complete multi-handle retrieval document as a single unit. Condition B split each memory's handles into independent proposition units ($3.95$ units/memory average), scored each unit independently, and assigned the memory the maximum similarity score among its constituent propositions.

Proposition-local retrieval increased target **#1 rankings from 10 to 13 families** (+30%) and improved mean target rank from **1.9 to 1.8**. In combination with Seed 025 Pareto assembly, proposition locality sharpened score discrimination, driving mean context size down from $K=2.1$ to $K=1.3$ and reducing wrong-memory exposure from **15/20 (75%) to 9/20 (45%)** (a 40% drop) and wrong-clause occurrences from **21 to 11** (-47.6%). However, aggressive context narrowing led to 4 over-pruning cases, yielding **14/20 (70%)** downstream task passes vs **15/20 (75%)** in whole-document scoring.

## 2. Quantitative Results

| Metric | Condition A (Whole Document) | Condition B (Proposition Local) | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Target Rank #1 Families** | 10 / 20 (50.0%) | 13 / 20 (65.0%) | **+3 Target #1 Rankings (+30%)** |
| **Target Top-3 Families** | 19 / 20 (95.0%) | 18 / 20 (90.0%) | 1 ranking harm, 1 rescue |
| **Mean Target Rank** | 1.90 | 1.80 | **-0.10 mean rank improvement** |
| **Ranking Rescues / Harms** | N/A | 1 rescue / 2 harms | 1 net ranking harm |
| **Pareto Target Retained Families**| 16 / 20 (80.0%) | 14 / 20 (70.0%) | 2 net targets lost to over-pruning |
| **Safe Compaction Families** | 9 / 20 (45.0%) | 13 / 20 (65.0%) | **+4 Safe Compaction Families** |
| **Over-Pruning Families** | 3 / 20 (15.0%) | 4 / 20 (20.0%) | +1 over-pruning |
| **Upstream Rank Miss Families** | 1 / 20 (5.0%) | 2 / 20 (10.0%) | +1 upstream miss |
| **Mean Context Size ($K$)** | 2.10 | 1.30 | **-38.1% context size compaction** |
| **Families with Wrong Memory** | 15 / 20 (75.0%) | 9 / 20 (45.0%) | **-40.0% wrong memory exposure** (6 families freed) |
| **Wrong Clause Occurrences** | 21 | 11 | **-47.6% wrong clauses** |
| **Wrong Rule Contamination** | 7 / 20 (35.0%) | 6 / 20 (30.0%) | -1 contamination family |
| **Mean Memory Words** | 161.05 | 112.20 | **-30.3% word reduction** |
| **Semantic Task Passes** | 15 / 20 (75.0%) | 14 / 20 (70.0%) | 1 task rescue / 2 harms |
| **Units per Memory (Average)** | N/A | 3.95 units | 4 background/rule propositions |
| **Semantic Comparisons / Query** | 5 | 19.75 | 3.95x similarity work per query |
| **Ranker Model Calls** | 0 | 0 | 100% analytical scoring |
| **Unsupported Claims Admitted** | 0 | 0 | Closed-world safety intact |

## 3. Structural Breakdown & Tradeoffs

1. **Target Discrimination**: When multiple memories share background operational steps, whole-document scoring dilutes the unique rule. Proposition-local scoring isolates the exact matching rule, increasing #1 rank placement from **10 to 13 families**.
2. **Interaction with Pareto Frontier**: Because proposition-local scores create sharper score differentials between top matches and competitors, Pareto non-domination narrows context aggressively ($K=1.3$ vs $K=2.1$). This dramatically reduces wrong memory exposure (15 -> 9 families), but slightly increases over-pruning risk when a target is ranked #3.
3. **Deterministic Compute Cost**: Proposition-local matching increased semantic similarity comparisons per query from 5 to 19.75. This additional compute is strictly analytical (vector dot products) and consumes 0 LLM calls.

## 4. Key Takeaways

1. **Proposition Granularity Improves Retrieval Precision**: Matching queries against individual proposition handles prevents shared background text from obscuring decision-relevant distinctions.
2. **Sharper Attention Boundaries**: Proposition locality provides cleaner input signals to the Attention Firewall, reducing wrong-clause exposure by 47.6% and context word load by 30.3%.
3. **Next Frontier**: Balancing high-precision proposition retrieval with Pareto frontier retention when dealing with near-neighbor rank-3 candidates.
