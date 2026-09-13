# Seed Growth 004

## Classification

Exploratory fresh-task ablation.

## Question

Does accumulated MNEXA experience improve performance on fresh
opaque transfer tasks, and does an explicit constraint-fidelity
instruction reduce information loss between recalled memory and
the final decision?

## Frozen Conditions

### A — Baseline

Same frozen reasoning model.

No persistent MNEXA memory.

### B — Current MNEXA

Same frozen reasoning model.

Current MNEXA seed.

Current reasoning prompt.

### C — MNEXA + Constraint Fidelity

Same persistent MNEXA memory as Condition B.

Same frozen reasoning model.

One additional instruction requiring every decision-critical
constraint to survive into the final answer.

## Metrics

### Task Success

Whether the produced decision prescribes operationally compliant
behavior.

### Constraint Fidelity

Whether all critical constraints are explicitly retained,
including prohibitions, counts, limits, identifiers, ordering,
numbers and units.

## Ablation Invariant

Conditions B and C must receive identical persistent-memory
segments.

If their memory segments differ, the family result is invalid.

## Scope

No changes in this experiment to:

- MNEXA storage;
- ExperienceRecord behavior;
- consolidation;
- embeddings;
- retrieval;
- memory ranking;
- context budget;
- model;
- task family after freezing.

## Task Set

20 new synthetic opaque families.

The task set is SHA-256 hashed before the first model run.

## Interpretation

A vs B measures persistent-memory benefit.

B vs C measures the effect of constraint-preserving decision
generation.

This experiment is exploratory rather than confirmatory.
