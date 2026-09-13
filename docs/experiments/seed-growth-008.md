# Seed Growth 008 — Evidence Role Boundary

## Classification

Exploratory fresh evidence-role ablation.

## Question

Can MNEXA distinguish between a statement that is physically grounded in an
immutable source and a statement that is epistemically eligible for promotion
into reusable knowledge?

## Principle Under Test

> Source-grounded does not automatically mean knowledge-worthy.

Seed Growth 007 established exact source-span ancestry. Seed Growth 008 tests
the next boundary: evidence role.

## Mixed Historical Source

Every family contains one structured source with five explicit roles:

1. `status`
2. `failed_decision`
3. `authoritative_correction`
4. `operator_note`
5. `diagnostic_metadata`

All five roles contain physically real source spans.

For this experiment, only `authoritative_correction` is eligible for promotion
to reusable operational knowledge.

The other roles must remain available as historical evidence but must not be
promoted merely because their text exists in the record.

## Conditions

### A — Baseline

Same reasoning model and transfer task.

No persistent MNEXA memory.

### B — Exact Span Grounding Only

One shared atom proposal is generated from the mixed historical source.

An atom is admitted when:

- its source quote exists exactly once;
- its claim text matches the quote after minimal normalization;
- the quote lies inside any recognized role section.

No role-based eligibility check is applied.

This represents the evidence boundary reached by Seed Growth 007.

### C — Exact Span + Evidence Role Gate

Condition C receives:

- the same raw historical source;
- the same atom proposal;
- the same model;
- the same transfer reasoning policy.

It adds one deterministic rule:

> A grounded atom is knowledge-eligible only when its source role is
> `authoritative_correction`.

Grounded spans from status, failed decisions, operator speculation, and
metadata are rejected from promotion while remaining historical evidence.

## Shared Atom Proposal Invariant

The model atomizer is run once per family.

Conditions B and C consume the same serialized atom proposal. This removes
atomizer stochasticity from the B/C comparison.

The experiment records a SHA-256 digest of the shared atom proposal.

## Role Challenges

Each family pre-registers four grounded but knowledge-ineligible statements:

- one `status` statement;
- one `failed_decision` statement;
- one `operator_note` statement;
- one `diagnostic_metadata` statement.

If the model omits one of these challenge statements, the harness inserts that
exact source-grounded statement into the shared B/C atom proposal.

This guarantees that the role gate is actually exercised rather than merely
observed under cooperative model behavior.

Across 20 families there are 80 pre-registered role challenges.

## Claim Admission

To isolate the role boundary, every admitted evidence atom is converted into a
1:1 candidate claim and passed through the existing Seed Growth 006 closed-world
claim ancestry gate.

There is no second stochastic claim-generation model call in the B/C
comparison.

## Primary Metrics

### Authoritative Recall

expected authoritative atoms recovered / expected authoritative atoms

Bounded to `[0, 1]`.

### Authoritative Precision

expected authoritative atoms admitted / all atoms admitted to reusable memory

Bounded to `[0, 1]`.

### Ineligible Atoms Admitted

Count of reusable-memory atoms originating from:

- `status`
- `failed_decision`
- `operator_note`
- `diagnostic_metadata`

Target for Condition C: `0`.

### Role Challenge Rejections

Number of pre-registered grounded-but-ineligible challenges rejected by the
role gate.

Target: all 80.

## Secondary Metrics

### Knowledge Completeness

Whether all four authoritative operational atoms survive into the durable
lesson.

### Transfer Task Sufficiency

Each transfer prompt asks only for a pre-registered subset of the known rule.

The transfer grader scores only the atoms actually required by that task.

This avoids treating "did not repeat every stored fact" as a task failure.

### Transfer Non-Knowledge Leak

Whether the final answer explicitly repeats pre-registered material from an
ineligible source role.

## Frozen Components

No changes to:

- `mnexa_seed.py`
- persistence
- retrieval
- embeddings
- ranking
- context budget
- reasoning model
- constraint-fidelity decision policy
- Seed Growth 006 claim ancestry gate
- Seed Growth 007 exact-span grounding semantics

The B/C difference is evidence-role admission only.

## Interpretation

Seed Growth 008 does not claim that `authoritative_correction` is the only
knowledge-worthy role for MNEXA generally.

It tests the narrower architectural proposition that:

> evidence role is an independent admission dimension from physical source
> grounding.

Future systems may define richer role-specific policies for telemetry,
independent observations, human testimony, documents, tools, and other source
classes.
