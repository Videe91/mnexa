# Seed Growth 009 — Evidence Atomicity Boundary

## Classification

Exploratory fresh evidence-atomicity ablation.

## Question

Can MNEXA distinguish between:

1. an authoritative source-grounded span; and
2. an authoritative source-grounded span that represents exactly one
   reusable proposition?

## Principle Under Test

> Grounded + authoritative does not automatically mean atomic.

Seed Growth 007 established source-span grounding.

Seed Growth 008 established evidence-role eligibility.

Seed Growth 009 tests proposition granularity.

## Conditions

### A — Current Role-Gated MNEXA

A candidate evidence atom is admitted when:

- its source quote exists exactly once;
- its atom text equals that quote;
- the quote belongs to the `authoritative_correction` role.

No proposition-boundary check is performed.

A span containing two or more valid authoritative rules can therefore
be admitted as one evidence atom.

### B — Role Gate + Atomicity Gate

Condition B receives:

- exactly the same historical source;
- exactly the same model atom proposal;
- the same source-span gate;
- the same evidence-role gate;
- the same claim-ancestry gate;
- the same transfer reasoning policy.

It adds one deterministic rule:

> An admitted evidence atom must match exactly one pre-registered
> proposition boundary.

A candidate is rejected if it:

- crosses multiple proposition boundaries;
- contains only part of one proposition;
- falls outside all registered proposition boundaries.

## Controlled Atomic Boundaries

Each synthetic authoritative correction contains exactly four
pre-registered atomic propositions.

The atomic boundaries are part of the frozen benchmark specification.

Seed Growth 009 therefore tests atomicity admission, not autonomous
boundary discovery.

Autonomous discovery of proposition boundaries is a later problem.

## Shared Proposal Invariant

The atomizer runs once per family.

Conditions A and B consume the same serialized proposal.

A SHA-256 digest of that proposal is recorded.

## Atomicity Challenges

Each family contains two pre-registered compound challenges.

Challenge C1 spans authoritative propositions A1 + A2.

Challenge C2 spans authoritative propositions A3 + A4.

Each challenge is:

- physically present in the source;
- entirely inside the authoritative role;
- factually supported;
- but non-atomic.

If the model does not independently propose a challenge, the harness
inserts it into the shared proposal for both conditions.

Across 20 families there are 40 compound challenges.

This guarantees that the atomicity boundary is exercised.

## Primary Metrics

### Atomic Recall

Number of expected canonical atomic propositions admitted divided by
number of expected atomic propositions.

Bounded to `[0, 1]`.

### Atomic Precision

Number of expected atomic propositions admitted divided by all
admitted authoritative atoms.

A compound span therefore lowers precision even when every word in the
span is authoritative and true.

### Compound Atoms Admitted

Number of admitted atoms whose source span crosses two or more
canonical proposition boundaries.

Target for Condition B: `0`.

### Atomicity Challenge Rejections

Number of pre-registered compound challenge spans rejected by the
atomicity gate.

Target: `40 / 40`.

## Secondary Metrics

### Knowledge Completeness

Whether the durable lesson still contains all four required
authoritative facts.

This is intentionally distinct from atomic recall.

A single compound span can be knowledge-complete while still being
non-atomic.

### Transfer Task Sufficiency

Each transfer task asks for a pre-registered subset of the rule.

The decision is scored only on the facts needed by that task.

### Memory Word Count

The experiment records model-visible persistent-memory word count.

This allows observation of whether eliminating redundant compound
atoms reduces context size.

## Important Tradeoff

The atomicity gate is rejection-only.

It does not repair a compound atom by splitting it.

Therefore, if the model proposes only a compound span and omits its
atomic components, Condition B may lose recall.

That is scientifically useful.

It distinguishes:

- detecting bad granularity; from
- repairing bad granularity.

Repair is not part of Seed Growth 009.

## Frozen Components

No changes to:

- `mnexa_seed.py`
- persistence
- retrieval
- embeddings
- ranking
- memory budget
- reasoning model
- source-span grounding
- evidence-role semantics
- claim-ancestry semantics
- decision-fidelity policy

The A/B difference is atomic-boundary admission only.

## Interpretation

A successful Seed Growth 009 result would show that MNEXA can enforce:

ExperienceRecord
→ source span
→ evidence role
→ atomic proposition
→ grounded claim
→ reusable knowledge

The strongest result is not necessarily a higher transfer-task score.

The primary proof is:

- compound spans are rejected;
- atomic propositions remain recoverable;
- unsupported claims remain zero;
- source/proposal invariants remain equal.

If rejection substantially harms recall, the next problem is not the
gate itself.

The next problem would be controlled atomization repair.
