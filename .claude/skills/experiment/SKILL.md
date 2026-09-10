---
name: experiment
description: Use before running an MNEXA benchmark, ablation, baseline comparison, or experiment intended to support or falsify a scientific or performance claim.
---

# Experiment

Run experiments as reproducible evidence, not demonstrations designed to make MNEXA look good.

## Preconditions

Before execution, a benchmark contract or explicit experimental protocol must define the evaluation boundary and primary metric. If changing those rules would be D3, stop and use the `decide` skill.

## Workflow

1. Create an experiment ID `EXP-NNNN`.
2. Write `docs/experiments/EXP-NNNN-<slug>.md` before running anything.
3. Record the hypothesis, null/alternative where useful, primary metric, baselines, controlled variables, task/dataset versions, hidden-evaluation boundary, model/configuration, tools, seeds, and stopping rule.
4. Record the exact repository commit being evaluated.
5. Run the baseline/control condition first when practical.
6. Run the MNEXA condition without changing the frozen contract.
7. Preserve raw results in the experiment's declared result location.
8. Record all runs covered by the stopping rule, including failures and null results.
9. Compute/report the predeclared metrics and uncertainty/sample size.
10. Write interpretation separately from observations.
11. State whether the result supports, weakens, or is inconclusive for the hypothesis.
12. Link any resulting architectural decision to an ADR rather than editing architecture silently.

## Non-negotiables

- Never expose hidden evaluation cases to memory construction or implementation tuning.
- Never modify a benchmark after seeing a poor result without versioning the benchmark and preserving the original result.
- Never use passing unit tests as evidence for the scientific thesis.
- Never omit an inconvenient run simply because it lowers the score.
