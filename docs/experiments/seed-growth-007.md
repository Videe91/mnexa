# Seed Growth 007 — Raw Evidence Atomization & Deterministic Span Grounding

## Classification

Exploratory fresh raw evidence atomization and span grounding ablation.

## Question

Can MNEXA discover and ground evidence atoms directly from raw historical evidence via deterministic span matching without relying on pre-registered oracle atoms, while rejecting adversarial ungrounded claims?

## Constitutional Principle Under Test

No knowledge without ancestry. (Extended from pre-registered atoms to raw historical evidence spans).

## Conditions

### A — Baseline

Same frozen reasoning model.

Constraint-fidelity decision policy.

No persistent MNEXA memory.

### B — Oracle Grounded MNEXA

Same failed historical decision.

Same authoritative correction.

Uses pre-registered oracle evidence atoms (Seed Growth 006 upper bound).

Same claim ancestry consolidation policy and closed-world claim admission gate.

### C — Raw Span Grounded MNEXA

Exactly the same failed historical decision.

Exactly the same authoritative correction.

Raw historical evidence is atomized via LLM proposal.

Candidate evidence atoms undergo deterministic span grounding:
1. `source_quote` must exist in raw evidence.
2. `source_quote` must occur exactly once (unique span).
3. `text` must equal `source_quote` after minimal normalization.

Admitted grounded evidence atoms are assigned unique IDs, byte offsets, and SHA-256 hashes.

Admitted atoms are passed to the claim ancestry consolidator and closed-world claim admission gate.

## Adversarial Atom Challenges

To attack and verify the runtime rejection gate, each family introduces 2 pre-registered adversarial atom challenges:
1. Nonexistent source span (claiming a quote not present in raw evidence).
2. Citation smuggling (claiming an existing quote with altered claim text).

Target: `ungrounded_atoms_admitted == 0` and `adversarial_atom_rejections == 40`.

## Source-Evidence Invariant

Conditions B and C must receive byte-identical raw historical source evidence.

## Metrics

### Transfer Task Success
Whether required transfer operational knowledge is present and designated failed-decision contamination is absent (`raw_span_task_passes`).

### Knowledge Completeness
Whether the durable lesson preserves the complete set of authoritative protocol rules (`raw_span_complete_lessons`).

### Model Atom Proposals & Grounded Atoms
Total raw atom proposals by model, total admitted grounded atoms, total rejected atoms.

### Adversarial Rejections
Total pre-registered adversarial challenges rejected by the deterministic span grounding runtime gate (`adversarial_atom_rejections`).

### Ungrounded & Unsupported Admissions
`ungrounded_atoms_admitted` (target: 0) and `unsupported_claims_admitted` (target: 0).

### Source Span Coverage
Fraction of oracle evidence atoms successfully discovered and grounded from raw text (`mean_source_span_coverage`).

## Frozen Components

No changes to:
- `mnexa_seed.py`
- historical storage
- interpretive storage
- retrieval
- embeddings
- ranking
- context budget
- reasoning model
- constraint-fidelity transfer policy
