# 30. Seed Growth 027 — Evidence-Quorum Attention

## Hypothesis

If fewer than two discriminative retrieval channels remain active after channel abstention, MNEXA must not prune active context using Pareto dominance; preserving a fixed Top-3 context when corroborating channels abstain prevents single-channel over-pruning collapse and protects target memory retention.

## Principle

> One signal may rank. Multiple distinct active signals are required to prune.

## Implementation

```text
Seed 026 proposition-local ranking
        ↓
Seed 022 channel abstention
        ↓
active channels >= 2 ?
        │
        ├── YES → Seed 025 Pareto assembly
        │
        └── NO  → preserve fixed Top-3
```

- **Zero LLM calls for context assembly**: 0 ranker model calls, 0 assembler model calls.
- **Zero oracle knowledge**: No target identity, grader, answer, or confidence threshold.
- **Frozen threshold**: `min_active_channels = 2`.

## Live Execution Results

- **Run ID**: `20260914T113610Z`
- **Taskset SHA256**: `69c94aa9b9ab72c48cd2d2ad4909bf4b186840e9d94d30d5fd8bced2846faefd`
- **Model**: `gpt-4o-mini`
- **Embedder**: `sentence-transformers/all-MiniLM-L6-v2`

| Metric | Baseline (Seed 025 Pareto) | Treatment (Seed 027 Evidence-Quorum) | Impact |
| :--- | :---: | :---: | :---: |
| **Active Channels Distribution** | 1: 9, 2: 11 | 1: 9, 2: 11 | 9 subquorum families |
| **Target Top-3 Availability** | 20 / 20 (100%) | 20 / 20 (100%) | Baseline 100% |
| **Target Memory Retention** | 16 / 20 (80.0%) | **20 / 20 (100.0%)** | **+4 families (+20.0%)** |
| **Over-Pruning Failures** | 4 | **0** | **-4 failures (-100%)** |
| **Subquorum Target Retention** | 5 / 9 (55.6%) | **9 / 9 (100.0%)** | **+4 families (+44.4%)** |
| **Subquorum Task Passes** | 5 / 9 (55.6%) | **9 / 9 (100.0%)** | **+4 families (+44.4%)** |
| **Overall Semantic Task Passes** | 16 / 20 (80.0%) | **20 / 20 (100.0%)** | **+4 passes (+20.0%)** |
| **Target Rescues / Harms** | - | **4 Rescues / 0 Harms** | Net +4 |
| **Mean Context $K$** | $1.4$ | $2.3$ | $+0.9$ memories |
| **Mean Memory Words** | $117.85$ | $176.25$ | $+58.4$ words |
| **Admitted Unsupported Claims** | 0 | 0 | Clean safety |

## Cluster Breakdown

| Cluster | Pareto Retention | Quorum Retention | Pareto Task Pass | Quorum Task Pass | Subquorum Families |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `channel-session` | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 3 |
| `lane-routing` | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 0 |
| `retry-policy` | 3/5 (60%) | **5/5 (100%)** | 3/5 (60%) | **5/5 (100%)** | 4 |
| `storage-finalization` | 3/5 (60%) | **5/5 (100%)** | 3/5 (60%) | **5/5 (100%)** | 2 |

## Key Findings

1. **Mechanism Exercised & Validated**: 9 of 20 families fell below the 2-channel quorum threshold. In all 9 subquorum families, single-channel Pareto dominance would have collapsed context to $K=1$. The quorum guard prevented pruning, raising subquorum retention from 5/9 to 9/9 and task passes from 5/9 to 9/9.
2. **Perfect Task Success (20/20)**: Overall task passes reached 20/20 (100%), with 4 target rescues and 0 task harms.
3. **Over-Pruning Completely Eliminated**: Over-pruning dropped from 4 failures to 0.
4. **Controlled Context Tradeoff**: Context size modestly expanded from mean $K=1.4$ to $K=2.3$ (+58.4 words per prompt), which was well within budget and caused zero decision contamination or task harms.

## Conclusion

Evidence-Quorum Attention successfully resolves single-channel Pareto collapse: when channel abstention removes corroboration signals, MNEXA refrains from aggressive pruning and preserves context breadth, achieving 100% target retention and 100% downstream task success without any model calls or target leakage.
