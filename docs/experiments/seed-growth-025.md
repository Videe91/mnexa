# Seed Growth 025 — Pareto-Safe Context Assembly

## Classification

Exploratory fresh Pareto-safe context-assembly ablation.

## Question

Can MNEXA safely compact active memory by retaining every candidate
that is not clearly inferior across all active retrieval signals?

## Principle

> Do not discard a memory if no other memory clearly beats it across
> every active retrieval signal.

## Motivation

Seed 024 showed that channel consensus is safer than raw RRF-gap
confidence.

However, preserving only each channel's top winner can still remove a
memory that represents a legitimate cross-channel tradeoff.

A candidate may be:

- weaker than A semantically;
- stronger than A lexically;
- weaker than B lexically;
- stronger than B semantically.

Such a memory is not clearly inferior to either competitor.

Seed 025 treats those candidates as non-dominated.

## Pareto Dominance

Candidate A dominates candidate B iff:

1. A is ranked at least as highly as B on every active retrieval
   channel; and
2. A is ranked strictly higher than B on at least one active channel.

If no candidate dominates B, B belongs to the Pareto frontier.

## Condition A

Seed 022 fixed Top-K=3.

## Condition B

Use the identical complete Seed 022 fused ranking.

Compute the Pareto frontier using active retrieval-channel ranks.

Choose the smallest fused prefix containing every frontier member if
all frontier members lie within Top-3.

If any frontier member lies below rank 3:

retain Top-3.

If there are no active channels:

retain Top-3.

## Frozen Retrieval Stack

Seed 020 addressing
→ Seed 021 retrieval handles
→ Seed 022 non-discriminative-channel abstention
→ exact-tie midranks
→ RRF
→ complete fused ranking

No ranking behavior changes.

## No Calibration

Seed 025 introduces no:

- confidence threshold;
- score-gap threshold;
- learned weight;
- model router;
- LLM judge.

## Fresh Benchmark

20 fresh families.

Four clusters:

- retry-policy;
- lane-routing;
- channel-session;
- storage-finalization.

Five memories per cluster.

All queries are context-only.

## Primary Safety Metric

Over-pruning.

A target present in fixed Top-3 but excluded from Pareto context is an
assembly failure.

## Assembly Classes

SAFE_COMPACTION:
target retained while one or more distractors are removed.

OVER_PRUNING:
target in fixed Top-3 but removed.

UPSTREAM_RANK_MISS:
target absent from fixed Top-3.

NO_CHANGE:
Pareto policy retains fixed Top-3.

## Primary Metrics

- fixed target availability;
- Pareto target retention;
- over-pruning;
- safe compaction;
- mean Pareto K;
- frontier size;
- distractors before/after.

## Secondary Metrics

- target visibility;
- semantic task success;
- wrong-memory exposure;
- wrong-clause occurrences;
- wrong-rule contamination;
- memory words;
- memory segments.

## Same-State Control

If both conditions assemble the same memory set, execute the transfer
reasoner once and reuse the result.

## Controls

Both conditions must share:

- learned memory;
- evidence;
- candidate routing;
- candidate population;
- retrieval handles;
- semantic scores;
- lexical scores;
- entity scores;
- channel abstention;
- tie handling;
- RRF constant;
- complete fused ordering;
- authoritative presentation representation;
- transfer query;
- reasoner;
- context budget.

Only context assembly differs.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

Assembler model calls:

0

The assembler receives no target family ID, semantic clause, grader or
expected answer.

## Strong Success Pattern

fixed target availability:
high

Pareto target retention:
approximately equal to fixed availability

over-pruning:
0 or near 0

mean K:
below 3

wrong-memory exposure:
lower

memory words:
lower

task performance:
equal or better

unsupported claims:
0

## Scientific Boundary

Seed 025 does not establish optimal attention or optimal multi-objective
retrieval.

It tests whether Pareto non-domination is a safer deterministic
attention-preservation rule than retaining only per-channel winners.

## Burn Rule

The fresh Seed 025 taskset is burned after the first live execution.

Do not tune the Pareto rule, Top-K limit, channel weights, prompts,
graders or task families against the live result and rerun it as fresh
evidence.
