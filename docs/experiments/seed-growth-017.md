# Seed Growth 017 — Pooled Memory Interference

## Classification

Exploratory fresh pooled-memory interference ablation.

## Question

Can MNEXA continue to activate and use the correct accumulated
experience when many semantically similar memories coexist?

## Motivation

Seed Growth 016 established that compact semantic memory is stable
under repeated transfer sampling.

The next unresolved question is not whether one learned memory works.

It is whether accumulated memories interfere with one another.

A persistent intelligence that becomes less capable as experience
accumulates has not solved memory.

## Principle

> Available memory is not the same as active memory.

MNEXA should make the right experience active while leaving irrelevant
experience available but silent.

## Conditions

### Condition A — Isolated

Each transfer query is evaluated with only its own learned compact
memory present.

### Condition B — Pooled

The exact same target memory is evaluated alongside nineteen additional
learned memories.

The target memory itself is unchanged.

## Pool

Twenty learned families are divided into four semantic interference
clusters:

- retry policy;
- lane routing;
- channel/session;
- storage/finalization.

Each target therefore receives:

- 4 very close semantic near-neighbors;
- 15 additional broader distractors;
- 19 distractors total.

## Near-Neighbor Design

Distractors deliberately reuse similar vocabulary while changing
decision-relevant semantics.

Examples include:

`retry exactly twice`

`retry at most twice`

`retry at least twice`

`never retry the failed request`

and:

`only to the cobalt lane`

`only to the violet lane`

`only to the silver lane`

The benchmark therefore tests interference rather than merely unrelated
memory volume.

## Identity Signals

Families retain:

- unique system entity;
- unique code entity;
- shared `domain:recovery` entity;
- shared cluster entity.

This tests the current MNEXA retrieval stack as implemented rather than
artificially disabling its entity channel.

## Memory Construction

Every family's compact semantic lesson is built once.

That exact lesson is then learned into:

1. its isolated snapshot;
2. the shared pooled snapshot.

No separate extraction or repair pass exists between A and B.

## Frozen Evaluation

The pooled snapshot is built once and closed before evaluation.

For every target:

1. copy the closed pooled SQLite snapshot;
2. verify byte equality;
3. open the copy;
4. execute one transfer query;
5. discard the evaluation copy.

Therefore one evaluation decision cannot affect another evaluation.

Isolated evaluations use the same procedure with their own frozen
single-memory snapshots.

## Primary Metrics

### Semantic Task Success

Does the final transfer answer satisfy the target semantic contract?

### Target Semantic Clause Visibility

Is the exact target semantic clause present in model-visible memory?

### Wrong-Family Clause Visibility

How many known distractor semantic clauses become model-visible?

### Model-Visible Retrieval Recall

There is one relevant target memory.

Therefore:

`1.0` = target semantic clause visible

`0.0` = target semantic clause absent

### Model-Visible Retrieval Precision

If the target and N identifiable family clauses are visible:

`precision = 1 / N`

If the target is absent:

`precision = 0`

This is an exact-clause benchmark metric, not a universal semantic
retrieval metric.

## Retrieval Regret

The central paired metric is:

isolated passes
+
pooled fails
=
retrieval/interference regret

Because the target learned lesson exists in both conditions, this
measures behavioral harm introduced by accumulated surrounding memory.

### Omission Regret

Paired regret where the target clause is absent from pooled model-visible
memory.

### Contamination Regret

Paired regret where at least one wrong-family clause is model-visible.

These categories may overlap.

## Final-Decision Contamination

The experiment also records whether a final answer contains an exact
semantic clause belonging to another family.

This is deliberately conservative.

It does not claim to detect every possible paraphrased contamination.

## Context Cost

Record:

- model-visible memory words;
- model-visible memory segment count.

The purpose is to distinguish:

memory pool size

from:

actual active context size.

A pool of twenty memories should not require twenty memories to be shown
to the reasoner.

## Cluster Analysis

Performance is reported separately for:

- retry-policy;
- lane-routing;
- channel-session;
- storage-finalization.

This identifies whether interference concentrates around particular
semantic neighborhoods.

## Safety

All memory bundles continue to use:

- source-role admission;
- exact evidence ancestry;
- lossless fallback;
- compact evidence indexing.

Target:

`bundle_unsupported_claims_admitted == 0`

## Critical Controls

The run must preserve:

`all_target_lessons_identical_between_conditions == true`

`all_target_source_evidence_equal == true`

`all_transfer_queries_equal == true`

`all_compact_renderers_equal == true`

`all_context_budget_configuration_equal == true`

`all_pooled_evaluations_from_same_snapshot == true`

`all_isolated_evaluations_from_frozen_snapshots == true`

`all_snapshot_copies_byte_identical_before_evaluation == true`

## Resource Accounting

For twenty families:

- 20 initial extraction calls;
- 20 repair calls;
- 20 isolated transfer calls;
- 20 pooled transfer calls.

Snapshot construction uses no model calls.

## Success Interpretation

A strong result would show:

- pooled task success close to isolated task success;
- high target-memory visibility;
- low retrieval regret;
- low wrong-family presentation;
- no wrong-rule decision contamination;
- bounded model-visible context despite a 20-memory pool.

This would provide preliminary evidence that MNEXA's accumulated
memories can coexist without destroying their usefulness.

## Failure Interpretation

If pooled performance materially degrades while isolated performance
remains high, the bottleneck has moved to:

- retrieval;
- routing;
- ranking;
- presentation;
- or context selection.

That would be a useful failure.

It would mean memory formation is working, while memory activation still
needs to grow.

## What Seed 017 Does Not Prove

It does not prove:

- large-scale retrieval;
- million-memory performance;
- long-term temporal memory;
- contradictory-belief resolution;
- authorization-aware routing;
- cross-agent collective memory;
- model-independent retrieval stability;
- conventional-RAG superiority.

It tests twenty accumulated memories under deliberately overlapping
semantics.

## Frozen Components

No changes to:

- `mnexa_seed.py`;
- canonical persistence;
- retrieval channels;
- retrieval ranking;
- context budget;
- evidence-role admission;
- structure repair;
- lossless fallback;
- compact semantic representation;
- transfer reasoner.

Only memory population differs between the two conditions.

## Burn Rule

The fresh Seed 017 task set is burned after its first live execution.

Do not tune retrieval weights, ranking, tasks, entity definitions,
semantic graders, context budget, or transfer prompts against the live
result and rerun it as fresh evidence.
