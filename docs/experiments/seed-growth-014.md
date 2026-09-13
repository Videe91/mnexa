# Seed Growth 014 — Lossless Rejection / Grounded Fallback

## Classification

Exploratory fresh lossless-rejection / grounded-fallback ablation.

## Question

When a structured memory proposal fails normalization or structural
validation, can MNEXA preserve its valid authoritative evidence instead
of deleting that evidence entirely?

## Motivation

Seed Growth 013 established that semantic-closed projection works when
the required semantic evidence survives the repair stage.

On the frozen Seed 013 run:

- 16 families retained the required semantic evidence after repair;
- semantic closure passed 16/16 of those families.

The remaining failures occurred before projection.

The common failure mode was:

valid authoritative source support
→ imperfect structured representation
→ structured validation failure
→ entire proposition deleted

This conflates two different questions:

1. Is the historical evidence valid?
2. Is our current normalization of that evidence valid?

Seed 014 separates them.

## Principle

> Structural failure must never erase valid authoritative evidence.

## Conditions

Both conditions use:

- the same raw evidence;
- the same initial structured extraction;
- the same repair-model output;
- the same shared repair candidate proposal;
- the same structured admission result;
- the same semantic-closed projection for successfully structured
  propositions;
- the same transfer model.

### A — Current All-or-Nothing Admission

A repaired proposition must pass the complete structured validator.

If any structural component is invalid, the proposition contributes
nothing to durable memory.

### B — Support-First Lossless Admission

Admission occurs in stages.

#### Stage 1 — Support validation

`source_quote` must:

- exist exactly once;
- be an exact contiguous source substring;
- belong to `authoritative_correction`.

If this fails:

`HARD REJECT`

Nothing survives.

#### Stage 2 — Structured validation

The existing structured validator evaluates:

- nucleus;
- qualifiers;
- qualifier types;
- overlaps;
- nucleus uniqueness;
- final structured consistency.

If structure passes:

`STRUCTURED KNOWLEDGE`

If structure fails but support was valid:

`UNRESOLVED GROUNDED SUPPORT`

The exact authoritative support remains available to semantic-closed
projection.

No replacement wording is generated.

## Grounded Fallback

A fallback record contains only:

- exact support quote;
- exact support offsets;
- authoritative source role;
- source hash;
- support-span hash;
- `structure_status = unresolved`.

It contains no generated normalized claim.

## Challenge Classes

Each of 20 fresh families contains three deterministic fallback attacks.

### Recoverable Structural Challenge

The source support is valid and authoritative.

The deliberately malformed structure attaches a semantic operator as an
overlapping qualifier to the full nucleus.

Example:

source:

`never reuse the prior nonce`

candidate:

nucleus:

`never reuse the prior nonce`

qualifier:

`never`

The structured representation should fail.

The support must survive.

Total:

`20`

### Fabricated Support Challenge

A support quote that does not exist in the source.

Target:

`0 admitted`

Total:

`20`

### Non-authoritative Support Challenge

A real exact source quote taken from `failed_decision`.

Target:

`0 admitted`

Total:

`20`

Total unsafe challenges:

`40`

## Critical Controls

Both conditions must satisfy:

`all_source_evidence_equal == true`

`all_initial_structured_proposals_equal == true`

`all_repair_proposals_equal == true`

`all_structured_admissions_equal == true`

Condition B receives no additional model call.

The only difference is what happens to valid support after structured
validation fails.

## Primary Metrics

### Semantic Clause Survival

How many benchmark semantic clauses remain represented after admission?

### Semantic Task Success

Does the final transfer answer preserve the pre-registered semantic
contract?

### Recoverable Challenge Retention

How many of the 20 valid-support / invalid-structure attacks retain
their evidence?

Target:

`20 / 20`

### Unsafe Support Admission

Fabricated and non-authoritative fallback attacks admitted.

Target:

`0 / 40`

## Secondary Metrics

- exact semantic-clause visibility;
- complete lessons;
- number of grounded fallback records;
- families using fallback;
- model-visible memory words.

## Constitutional Targets

`lossless_fabricated_support_challenges_admitted == 0`

`lossless_nonauthoritative_support_challenges_admitted == 0`

`lossless_unsafe_support_challenges_admitted == 0`

`lossless_unsupported_claims_admitted == 0`

Every fallback record must retain exact physical ancestry.

## Important Distinction

Seed 014 does not make structurally invalid memory become structured
knowledge.

It creates a lower-confidence state:

`structure_status = unresolved`

The system knows:

- the evidence is valid;
- the normalization is unresolved.

That distinction is intentional.

## Interpretation

A strong result would show:

- semantic clauses survive admission more often;
- downstream semantic task success increases;
- all 20 recoverable challenge supports survive;
- all 40 unsafe support challenges remain rejected;
- unsupported claims remain zero.

The narrow claim would be:

> MNEXA can lose a proposed structure without losing the valid evidence
> beneath it.

## What Seed 014 Does Not Prove

It does not prove:

- universal semantic parsing;
- automatic repair correctness;
- confidence calibration;
- contradiction resolution;
- multi-source synthesis;
- optimal fallback retrieval;
- efficient context compression;
- conventional-RAG superiority.

## Deferred Problem

Semantic-closed representations remain context-heavy.

Compacting exact semantic payload without meaning loss is intentionally
deferred.

## Frozen Components

No changes to:

- `mnexa_seed.py`
- canonical storage
- retrieval
- embedding
- ranking
- structured extraction
- repair-model prompt
- semantic-closed projection for valid structured propositions
- transfer reasoner

Only the rejection/reconciliation policy is ablated.

## Burn Rule

The fresh Seed 014 task set is burned after its first live execution.

Do not tune against the result and rerun it as fresh evidence.
