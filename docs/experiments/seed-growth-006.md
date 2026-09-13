# Seed Growth 006 — Claim Ancestry

## Classification

Exploratory fresh claim-ancestry ablation.

## Question

Can MNEXA require every promoted reusable claim to prove its
evidence ancestry while retaining enough grounded knowledge for
successful transfer?

## Constitutional Principle Under Test

No knowledge without ancestry.

## Conditions

### A — Baseline

Same frozen reasoning model.

Constraint-fidelity decision policy.

No persistent MNEXA memory.

### B — Evidence-Disciplined MNEXA

Same failed historical decision.

Same authoritative correction.

Seed Growth 005 evidence-disciplined consolidation.

Same constraint-fidelity transfer reasoning policy.

### C — Claim-Ancestry MNEXA

Exactly the same failed historical decision.

Exactly the same authoritative correction.

The authoritative correction is deterministically decomposed into
atomic evidence items:

E1
E2
E3
...

The model may propose candidate claims.

Every candidate claim must:

1. cite exactly one valid evidence atom;
2. copy that atom's canonical proposition;
3. pass deterministic runtime admission.

Claims without valid ancestry are rejected before durable storage.

## Closed-World Admission Rule

Seed Growth 006 does not attempt general semantic entailment.

A claim is admitted only if its normalized text equals the canonical
text of the single evidence atom it cites.

This is intentionally restrictive.

The experiment asks whether executable ancestry can prevent
unsupported promotion before later experiments generalize the
entailment mechanism.

## Source-Evidence Invariant

Conditions B and C must receive byte-identical raw historical source
evidence.

Condition C additionally receives a deterministic indexed
decomposition of the authoritative correction.

The decomposition adds no new factual content.

## Metrics

### Transfer Task Success

Whether required grounded operational knowledge is present and
designated failed-decision contamination is absent.

### Correct Knowledge Retained

Whether the durable lesson preserves the authoritative protocol.

### Designated Contamination

Whether propositions intentionally present only in the failed
decision leak into reusable memory or transfer behavior.

### Ancestry Coverage

Fraction of authoritative evidence atoms represented by admitted
durable claims.

### Unsupported Claims Admitted

Number of claims admitted without satisfying the deterministic
closed-world ancestry gate.

Target: zero.

### Rejected Claims

Candidate model claims rejected by the deterministic admission layer.

A rejection is not necessarily a system failure. It can demonstrate
the admission boundary preventing unsupported promotion.

## Frozen Components

No changes to:

- mnexa_seed.py
- historical storage
- interpretive storage
- retrieval
- embeddings
- ranking
- context budget
- reasoning model
- constraint-fidelity transfer policy
- Seed 005 evidence-disciplined policy used in Condition B

## Interpretation

A vs B measures persistent grounded-memory benefit.

B vs C measures the effect of explicit claim ancestry plus
deterministic admission.

The critical Seed 006 result is not simply a higher task score.

The central question is whether MNEXA can make:

"No knowledge without ancestry"

an executable invariant.
