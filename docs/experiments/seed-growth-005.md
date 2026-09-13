# Seed Growth 005 — Epistemic Consolidation

## Classification

Exploratory fresh consolidation ablation.

## Question

Can MNEXA learn an authoritative correction without promoting
unsupported assumptions from a failed prior decision into reusable
knowledge?

## Conditions

### A — Baseline

Frozen reasoning model with the constraint-fidelity decision policy.

No persistent MNEXA memory.

### B — Current MNEXA Consolidation

Controlled failed decision.

Authoritative correction.

Current lossless consolidation policy.

Constraint-fidelity reasoning policy on the transfer task.

### C — Evidence-Disciplined Consolidation

Exactly the same failed decision.

Exactly the same authoritative correction.

Evidence-disciplined consolidation policy.

Same constraint-fidelity reasoning policy on the transfer task.

## Critical Ablation Invariant

Conditions B and C must receive byte-equivalent source evidence.

The experiment records a SHA-256 hash of the source evidence for both
conditions.

If those hashes differ, that family is invalid.

## Metrics

### Correct Knowledge

Whether the consolidated lesson or transfer decision contains all
required operational knowledge supplied by the authoritative
correction.

### Contamination

Whether the consolidated lesson or transfer decision contains
designated unsupported content that appeared only in the failed
decision.

### Task Success

Correct knowledge is present AND no designated contamination is
present.

## Hypothesis

Evidence-disciplined consolidation will reduce contamination without
reducing retention of authoritative corrected knowledge.

## Controlled Fixture

The failed historical decision is deterministic.

This is intentional.

Seed Growth 005 is testing consolidation behavior, not whether a model
happens to hallucinate a particular wrong action.

The failed decision remains preserved historically by MNEXA.

Only its promotion into reusable interpretive knowledge is under test.

## Frozen Components

No changes to:

- MNEXA storage
- historical event behavior
- retrieval
- embeddings
- ranking
- context budget
- reasoning model
- constraint-fidelity decision policy

The only B/C difference is consolidation policy.
