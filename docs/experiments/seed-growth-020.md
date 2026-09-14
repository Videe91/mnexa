# Seed Growth 020 — Conjunctive Address Refinement

## Classification

Exploratory fresh conjunctive-address-refinement ablation.

## Question

Can MNEXA combine compatible identity and contextual signals to narrow
an ambiguous candidate neighborhood without weakening stronger
addresses?

## Principle

> Strong identity constrains. Context refines.

## Motivation

Seed 018 established exact identity addressing.

Seed 019 established graceful degradation:

code
→ system
→ cluster
→ domain
→ global

However, Seed 019 stops at the first successful tier.

Therefore a system-only address may retain four memories even when the
query also contains a cluster that would distinguish the intended
memory.

Seed 020 tests whether weaker compatible metadata should refine, rather
than replace, a stronger address.

## Condition A — Seed 019

First successful level wins:

code
else system
else cluster
else domain
else global

## Condition B — Conjunctive Refinement

Start from the strongest matching tier.

Then process weaker available metadata.

If a weaker tier has a non-empty intersection with the current
candidate set, it may narrow the set.

If the intersection is empty, the weaker refinement is rejected.

The stronger address survives.

## Constitutional Routing Rule

Valid stronger address
+
compatible weaker context
→ refine

Valid stronger address
+
conflicting weaker context
→ preserve stronger address

No weaker context may erase a valid stronger identity.

## Fresh Pool

20 memories.

5 systems × 4 semantic neighborhoods.

Every system owns four memories.

Every cluster spans five systems.

## Query Modes

Five families each:

- full_identity
- code_only
- system_context
- context_only

## Expected Candidate Geometry

full_identity:

A = 1
B = 1

code_only:

A = 1
B = 1

system_context:

A = 4
B = 1

context_only:

A = 5
B = 5

Therefore only five of twenty paired evaluations contain a genuine
candidate-state difference.

## Same-State Noise Control

When A and B produce the same canonical candidate set:

1. they use the exact same frozen SQLite candidate snapshot;
2. memory objects and ordering are identical;
3. the transfer evaluation is executed once;
4. the exact result is reused for both conditions.

This prevents stochastic transfer-model variance from being
misclassified as an activation effect.

Only pairs with different candidate states receive a second transfer
model call.

## Primary Metrics

- semantic task success;
- target semantic-clause visibility;
- wrong-memory presentation;
- retrieval precision;
- retrieval recall;
- candidate precision;
- candidate recall;
- candidate-set size;
- task rescue;
- task harm.

## Refinement Metrics

Record:

- accepted refinement steps;
- rejected refinement steps;
- empty-intersection protections;
- seed tier;
- refinement path.

## Context Metrics

Record:

- active memory words;
- active memory segments.

Candidate-count reduction is reported separately from actual
model-visible context reduction.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

No changes are made to:

- grounding;
- evidence roles;
- semantic closure;
- lossless fallback;
- compact memory representation.

## Router Restrictions

The conjunctive router receives no:

- family ID;
- expected answer;
- semantic clause;
- semantic grader;
- canonical atoms;
- model call.

It uses only runtime metadata.

## Interpretation

A successful result would support an address-resolution lattice:

available memory
→ strongest valid address
→ compatible contextual refinement
→ candidate neighborhood
→ similarity ranking
→ active memory

## What Seed 020 Does Not Prove

It does not prove:

- fuzzy entity resolution;
- learned entity linking;
- alias resolution;
- probabilistic identity;
- conflicting-source truth resolution;
- million-memory scale;
- authorization-aware memory routing.

It tests deterministic composition of already-available addressing
metadata.

## Burn Rule

The fresh Seed 020 task set is burned after its first live execution.
Do not tune routing order, metadata, graders, candidate geometry,
context budget, prompts, or retrieval weights against the live result
and rerun it as fresh evidence.
