# Seed Growth 024 — Channel-Consensus Context Assembly

## Classification

Exploratory fresh channel-consensus-context-assembly ablation.

## Question

Can MNEXA compact model-visible memory while avoiding the
over-pruning caused by treating fused RRF score gaps as calibrated
confidence?

## Principle

> Agreement permits compression. Disagreement preserves breadth.

## Motivation

Seed 023 demonstrated that selective context assembly can materially
reduce distractor exposure and context cost.

However, raw RRF score-gap pruning over-pruned valid targets.

The failure suggested that the fused score magnitude itself is not a
calibrated confidence estimate.

Seed 024 therefore ignores score-gap magnitude and uses agreement
between independently active retrieval channels to determine context
breadth.

## Frozen Retrieval Stack

Both conditions use:

Seed 020 conjunctive routing
→ Seed 021 retrieval-handle representation
→ Seed 022 non-discriminative-channel abstention
→ exact-tie midranks
→ RRF
→ complete five-memory fused ordering

No part of ranking changes.

## Condition A

Fixed Top-K=3.

## Condition B

For each active retrieval channel:

1. identify its highest-ranked memory;
2. preserve all exact top ties;
3. locate those channel winners in the fused ranking.

Choose the smallest fused prefix that contains every active-channel
winner when all winners lie within Top-3.

Examples:

semantic winner = M1
lexical winner = M1
→ K=1

semantic winner = M1
lexical winner = M2
→ K=2

semantic winner = M3
lexical winner = M1
→ K=3

If any active-channel winner lies outside Top-3:

→ retain K=3

If no channel is active:

→ retain K=3

## Interpretation

Full channel agreement permits aggressive context compression.

Channel disagreement is evidence of retrieval uncertainty and therefore
preserves a wider context.

## No Numeric Confidence Threshold

Seed 024 introduces no:

- gap threshold;
- score threshold;
- learned calibration;
- channel weight;
- model call.

## Fresh Benchmark

20 fresh memory families.

Four interference clusters:

- retry-policy;
- lane-routing;
- channel-session;
- storage-finalization.

Five memories per cluster.

All transfer queries are context-only.

## Primary Safety Metric

Over-pruning.

A target present in fixed Top-3 but removed by channel-consensus
assembly is an over-pruning failure.

## Assembly Classes

### SAFE_COMPACTION

Target exists in fixed Top-3 and remains in consensus context while at
least one distractor is removed.

### OVER_PRUNING

Target exists in fixed Top-3 but consensus context removes it.

### UPSTREAM_RANK_MISS

Target is absent from fixed Top-3.

This is not attributed to context assembly.

### NO_CHANGE

Consensus retains all three fixed memories.

## Primary Metrics

- fixed target selected;
- consensus target retained;
- over-pruning;
- safe compaction;
- consensus K distribution;
- mean distractors before/after.

## Secondary Metrics

- semantic task success;
- target clause visibility;
- wrong-memory presentation;
- wrong-clause occurrences;
- wrong-rule contamination;
- model-visible memory words;
- model-visible memory segments.

## Same-State Noise Control

If fixed and consensus context contain the same memory set:

- use the same frozen snapshot;
- execute transfer reasoning once;
- reuse the exact evaluation.

## Controls

Both conditions must have identical:

- learned memory;
- source evidence;
- candidate routing;
- candidate population;
- retrieval-handle representation;
- semantic scores;
- lexical scores;
- entity scores;
- channel abstention;
- tie handling;
- RRF constant;
- fused ordering;
- authoritative semantic representation;
- transfer query;
- reasoner;
- context-budget configuration.

Only context assembly policy differs.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

The consensus assembler receives no:

- target family ID;
- semantic clause;
- semantic grader;
- expected answer.

Assembler model calls:

0

## Strong Success Pattern

A strong result would show:

fixed targets available:
high

consensus target retention:
approximately equal to fixed availability

over-pruning:
0 or near 0

mean context K:
below 3

wrong-memory exposure:
materially lower

memory words:
materially lower

task success:
equal or higher

unsupported claims:
0

## Failure Interpretation

If over-pruning remains high, top-channel agreement is not sufficient
evidence for safe context compression.

If target retention is high but distractor reduction is small, the
policy is safe but too conservative.

If target retention and compaction are both strong but task success
does not improve, the next bottleneck is decision behavior under
remaining memory competition.

If targets are frequently absent from fixed Top-3, ranking remains an
upstream bottleneck and should not be attributed to context assembly.

## Scientific Boundary

Seed 024 does not establish:

- optimal confidence calibration;
- learned attention;
- probabilistic uncertainty;
- optimal Top-K;
- production-scale retrieval;
- cross-domain retrieval;
- conventional-RAG superiority.

It tests whether channel agreement is a safer context-breadth signal
than raw fused-score gaps.

## Burn Rule

The fresh Seed 024 taskset is burned after the first live execution.

Do not tune:

- agreement policy;
- Top-K limit;
- channel weights;
- RRF K;
- prompts;
- graders;
- task families;

against the first live result and rerun it as fresh evidence.
