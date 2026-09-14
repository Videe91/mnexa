# Seed Growth 018 — Identity-Anchored Activation

## Classification

Exploratory fresh identity-anchored activation ablation.

## Question

Can MNEXA recover precise memory activation under pooled interference by
resolving exact experience identity before applying similarity ranking?

## Motivation

Seed Growth 017 established that memory formation was intact while
activation failed under interference.

With one target memory:

- target recall was 100%;
- retrieval precision was 100%.

With twenty memories:

- target recall fell to 50%;
- retrieval precision fell to 16.7%;
- every pooled query received distractor memory;
- downstream task success fell to 50%.

The target knowledge had not disappeared.

The wrong memories were becoming active.

## Principle

> Identity narrows. Similarity ranks.

Equivalent formulation:

> Address before similarity.

## Problem

Current retrieval combines:

- semantic similarity;
- lexical similarity;
- entity similarity;

through Reciprocal Rank Fusion.

This makes semantically common features compete directly with exact
identity signals.

For example:

`domain:recovery`

is broad contextual evidence.

But:

`code:CD-102`

is an addressing signal.

Seed 018 tests whether these should occupy different stages of memory
activation.

## Identity Anchors

Only two entity namespaces act as identity anchors:

`system:`

`code:`

Examples:

`system:CedarAPI`

`code:CD-102`

Contextual entities remain ordinary retrieval information:

`domain:recovery`

`cluster:retry-policy`

They cannot independently constrain the candidate set.

## Conditions

### A — Current Full-Pool Retrieval

All twenty memories enter the current retrieval system.

The existing:

- semantic channel;
- lexical channel;
- entity channel;
- RRF;
- context budget;

remain unchanged.

### B — Identity-Anchored Activation

The same twenty-memory population is available.

Before current retrieval:

1. extract exact `system:` and `code:` anchors from the query;
2. compare them with memory identity anchors;
3. if exact matches exist, restrict the candidate population to those
   memories;
4. run the existing retrieval/ranking implementation unchanged inside
   that candidate population.

If no exact anchor match exists:

`fall back to current full-pool retrieval`

No model call performs routing.

## Important Boundary

Identity routing does NOT receive:

- benchmark family ID;
- expected answer;
- semantic clause;
- semantic grader;
- canonical atomic units.

It operates only on entity metadata that would exist at runtime.

Benchmark target IDs are used only after retrieval for evaluation.

## Why Candidate Generation Comes First

The experiment distinguishes:

### Addressing

What experience is this query about?

from:

### Ranking

Which memories about that experience are most useful?

These are not the same problem.

Similarity is useful for ranking within a plausible neighborhood.

It is dangerous when asked to simultaneously infer identity from a
large population of semantically similar experiences.

## Fresh Interference Pool

Twenty fresh learned families are divided into four neighborhoods:

- retry policy;
- lane routing;
- channel/session;
- storage/finalization.

Each family has:

- one unique `system:` anchor;
- one unique `code:` anchor;
- shared `domain:recovery`;
- shared cluster context.

Thus the benchmark deliberately preserves the semantic interference
observed in Seed 017.

## Primary Metrics

### Semantic Task Success

Does the final answer preserve the target rule?

### Target Clause Visibility

Does the correct target semantic clause reach active model context?

### Wrong-Family Presentation

How many distractor semantic clauses become active?

### Retrieval Recall

Target clause visible:

`1`

otherwise:

`0`

### Retrieval Precision

Same exact-clause metric used in Seed 017.

### Activation Rescue

Current pooled condition fails while identity-anchored condition passes.

## Candidate Metrics

Record:

- exact identity matches;
- candidate count;
- target candidate inclusion;
- candidate recall;
- candidate precision;
- fallback usage.

The candidate selector itself cannot see target identity during
selection.

Target membership is scored post-hoc only.

## Secondary Metrics

- wrong-rule final-answer contamination;
- active memory words;
- active memory segments;
- cluster-level behavior.

## Resource Accounting

Across twenty families:

- 20 initial extraction model calls;
- 20 repair model calls;
- 20 current transfer calls;
- 20 anchored transfer calls.

Identity routing:

`0 model calls`

Candidate snapshot construction:

`0 model calls`

## Controls

The experiment must preserve:

`all_target_lessons_identical_between_conditions == true`

`all_target_source_evidence_equal == true`

`all_transfer_queries_equal == true`

`all_compact_renderers_equal == true`

`all_context_budget_configuration_equal == true`

`all_reasoners_equal == true`

`all_identity_selection_from_same_full_pool == true`

And:

`identity_router_used_family_id == false`

`identity_router_used_semantic_clause == false`

`identity_router_used_semantic_grader == false`

`identity_router_used_model == false`

## Strong Success Pattern

A strong result would look approximately like:

current pooled target recall:
~50%

identity-anchored target recall:
~100%

current pooled task success:
~50%

identity-anchored task success:
~90–100%

identity fallback:
near 0 for explicitly addressed queries

wrong-family presentation:
sharply reduced

unsupported claims:
remain 0

## Interpretation

If successful, Seed 018 would provide evidence for a first primitive of
the MNEXA Attention Firewall:

available memory
→ identity routing
→ relevant candidate neighborhood
→ similarity ranking
→ active memory
→ reasoning

It would support the architectural distinction:

> Identity is an addressing primitive, not merely another similarity
> feature.

## Failure Interpretation

If exact identity anchoring still produces substantial interference,
the problem is deeper than candidate generation.

Likely next suspects would include:

- memory object granularity;
- retrieval ranking within identity neighborhoods;
- entity propagation;
- context assembly;
- multi-memory conflict resolution.

## What Seed 018 Does Not Prove

It does not prove:

- fuzzy identity resolution;
- aliases;
- entity linking;
- implicit identity inference;
- ambiguous identities;
- cross-agent authorization;
- contradiction resolution;
- large-scale retrieval;
- conventional-RAG superiority.

It tests exact runtime identity anchors only.

## Frozen Components

No changes to:

- memory formation;
- evidence grounding;
- structured repair;
- lossless fallback;
- compact memory representation;
- embeddings;
- semantic retrieval scoring;
- lexical retrieval scoring;
- entity retrieval scoring;
- Reciprocal Rank Fusion;
- context budget;
- transfer reasoner.

The only ablated mechanism is candidate population selection before
current retrieval.

## Burn Rule

The fresh Seed 018 benchmark is burned after its first live execution.

Do not tune:

- identity prefixes;
- benchmark entities;
- retrieval weights;
- context budget;
- graders;
- prompts;
- fallback behavior;

against the first live result and rerun it as fresh evidence.
