# Seed Growth 027 — Evidence-Quorum Attention

## Classification

Exploratory fresh evidence-quorum attention ablation.

## Question

When proposition-local retrieval leaves only one discriminative
retrieval channel active, should MNEXA still be allowed to aggressively
prune active memory?

## Principle

> One signal may rank. Multiple distinct active signals are required
> to prune.

Alternative shorthand:

> No corroboration, no collapse.

"Distinct" here refers to separate retrieval channels. The experiment
does not claim statistical independence between those channels.

## Motivation

Seed 026 improved proposition-level selectivity but exposed a new
interaction.

When a channel became non-discriminative it correctly abstained.

In some families this left only one active channel.

Seed 025 Pareto assembly then operated over a one-dimensional ranking.

In one dimension, Pareto dominance effectively collapses toward the
best-ranked candidate and may aggressively remove alternatives despite
the loss of corroborating evidence.

Seed 027 tests whether channel abstention should therefore directly
control how much context pruning is permitted.

## Frozen Retrieval Stack

Both conditions use the exact same:

Seed 020 addressing
→ Seed 021 grounded retrieval handles
→ Seed 026 proposition-local semantic/lexical scoring
→ Seed 022 non-discriminative-channel abstention
→ exact-tie midranks
→ RRF
→ complete five-memory fused ordering

Ranking is identical between conditions.

## Condition A — Current Pareto

Use Seed 025 Pareto-safe context assembly regardless of how many
retrieval channels remain active.

## Condition B — Evidence Quorum

If:

active_channel_count >= 2

then:

apply the unchanged Seed 025 Pareto context rule.

If:

active_channel_count < 2

then:

do not prune based on Pareto dominance.

Preserve the fixed fused Top-3.

## No Confidence Threshold

Seed 027 introduces no:

- score threshold;
- score-gap threshold;
- learned calibration;
- channel weight;
- LLM judge;
- model router.

The only new rule is a deterministic minimum count of active
discriminative channels.

## Frozen Threshold

Minimum active channels required to prune:

2

This threshold is frozen before live execution.

## Fresh Benchmark

20 fresh families.

Four clusters:

- retry-policy
- lane-routing
- channel-session
- storage-finalization

Five memories per cluster.

All queries are context-only.

Within a cluster, memories intentionally share three background
propositions and differ primarily in one decision-relevant proposition.

## Mechanism Exercise Metric

Record:

subquorum_families

A subquorum family has fewer than two active channels after Seed 022
abstention.

If the fresh benchmark produces zero subquorum families, the main Seed
027 mechanism was not exercised and the result is inconclusive for the
quorum hypothesis.

Do not reinterpret zero mechanism cases as success.

## Primary Metrics

- target Top-3 availability;
- Pareto target retention;
- quorum target retention;
- Pareto over-pruning;
- quorum over-pruning;
- quorum target rescues;
- quorum target harms.

## Subquorum Metrics

For families with fewer than two active channels record:

- target available in Top-3;
- target retained by current Pareto;
- target retained by quorum guard;
- current Pareto task passes;
- quorum task passes.

These are the most mechanism-specific metrics.

## Cost Metrics

The quorum guard is expected to increase active-context breadth.

Record:

- mean Pareto K;
- mean quorum K;
- K distribution;
- number of context expansions;
- memory words;
- memory segments;
- wrong-memory exposure;
- wrong-clause occurrences.

Safety must be evaluated together with this context-cost tradeoff.

## Downstream Metrics

- semantic task passes;
- target visibility;
- wrong-memory presentation;
- wrong-clause occurrences;
- wrong-rule contamination;
- task rescues;
- task harms.

## Same-State Noise Control

If both assembly policies select the exact same canonical memory set:

- use the same frozen snapshot;
- perform transfer reasoning once;
- reuse the exact evaluation.

## Controls

Both conditions must share:

- learned memories;
- source evidence;
- routing;
- candidate population;
- proposition units;
- semantic scores;
- lexical scores;
- entity scores;
- abstention decisions;
- complete fused ranking;
- RRF constant;
- authoritative memory representation;
- query;
- reasoner;
- context-budget configuration.

Only the context-pruning safety rule differs.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

Ranker model calls:

0

Assembler model calls:

0

The quorum assembler receives no:

- target family ID;
- semantic clause;
- semantic grader;
- expected answer.

## Strong Success Pattern

A strong result would show:

- the mechanism is exercised by multiple subquorum families;
- target retention improves;
- over-pruning decreases;
- quorum target rescues > harms;
- task performance is equal or better;
- unsupported admissions remain zero.

Some increase in context size is expected.

## Failure Interpretation

### No subquorum cases

Mechanism not exercised.

Result is inconclusive.

### Target retention improves but context cost grows sharply

The quorum rule is safer but expensive.

The next frontier becomes finer uncertainty calibration rather than a
binary quorum.

### No retention improvement

Single-channel collapse was not a material cause of errors on the fresh
benchmark.

### More task harms despite better target retention

Preserving the target is insufficient because additional distractor
memory creates downstream decision interference.

### Most failures remain upstream Top-3 misses

Retrieval discrimination remains the dominant bottleneck.

## Scientific Boundary

Seed 027 does not establish:

- statistical independence of retrieval channels;
- probabilistic confidence;
- optimal quorum size;
- learned uncertainty;
- optimal context width;
- production-scale retrieval;
- conventional-RAG superiority.

It tests one narrow rule:

Whether aggressive context pruning should require corroboration from at
least two active retrieval channels.

## Burn Rule

The fresh Seed 027 taskset is burned after the first live execution.

Do not tune:

- minimum channel count;
- Pareto policy;
- proposition scoring;
- abstention;
- RRF K;
- Top-K;
- prompts;
- graders;
- benchmark families;

against the first live result and rerun it as fresh evidence.
