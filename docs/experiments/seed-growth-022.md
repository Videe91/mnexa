# Seed Growth 022 — Non-Discriminative Channel Abstention

## Classification

Exploratory fresh non-discriminative-channel-abstention ablation.

## Question

Should a retrieval channel be allowed to influence Reciprocal Rank
Fusion when it contains no information that distinguishes the
candidate memories?

## Principle

> No discrimination, no vote.

## Motivation

Seed 021 separated retrieval representation from authoritative semantic
representation.

It reduced retrieval-index size substantially, but did not establish
behavioral superiority.

Inspection of Seed 021 exposed a lower-level fusion defect.

Inside context-only five-memory neighborhoods, every memory can receive
the same entity-overlap score:

2, 2, 2, 2, 2

The current deterministic ranker nevertheless maps those scores to:

1, 2, 3, 4, 5

RRF then treats those arbitrary ranks as evidence.

Therefore candidate insertion order can affect the fusion result even
though the entity channel contains zero discriminative information.

Seed 022 tests removal of that artificial vote.

## Condition A — Seed 021 Fusion

Use the existing Seed 021 retrieval-handle ranker.

Channels:

- semantic
- lexical
- entity

Current deterministic rank conversion is unchanged.

RRF K = 60.

Top K = 3.

## Condition B — Abstaining Fusion

Use the EXACT channel scores produced by Condition A.

Do not recompute:

- embeddings;
- semantic scores;
- lexical scores;
- entity scores.

Change fusion only.

### Full-Channel Tie

If every candidate receives exactly the same score from a channel:

the channel abstains.

Its RRF contribution is zero for every candidate.

### Partial Tie

If only some candidates share the same score:

assign statistical mid-ranks.

Example:

scores:

10, 10, 5, 1, 1

ranks:

1.5, 1.5, 3.0, 4.5, 4.5

Equal evidence therefore receives equal fusion influence.

### No Epsilon

Seed 022 uses exact score equality only.

Near-equal score handling is not part of this experiment.

## Fresh Benchmark

20 fresh task families.

Four neighborhoods:

- retry-policy;
- lane-routing;
- channel-session;
- storage-finalization.

Five memories per neighborhood.

All queries are context-only.

Seed 020 conjunctive routing must return exactly five memories.

## Frozen Entity Geometry

For every query and every candidate in its routed neighborhood:

entity overlap score = 2.0

Therefore the entity channel is intentionally and provably
non-discriminative.

## Critical Ablation

Both conditions use identical:

- learned memories;
- source evidence;
- candidate routing;
- five-memory candidate set;
- retrieval-handle representation;
- semantic scores;
- lexical scores;
- entity scores;
- RRF K;
- Top K;
- authoritative model-visible payload;
- context budget;
- transfer reasoner.

Only the fusion treatment of non-discriminative and tied scores differs.

## Same-State Noise Control

If Conditions A and B select the same canonical Top-K memory set:

1. use the same frozen authoritative snapshot;
2. execute transfer reasoning once;
3. reuse the exact result for both conditions.

No stochastic model variation may be counted as a fusion effect.

## Primary Metrics

- target selected into Top K;
- target semantic clause visible;
- semantic task success;
- wrong-memory presentation;
- wrong-rule contamination.

## Fusion Diagnostics

Record:

- artificial sequential tie count by channel;
- abstention count by channel;
- average active channel count;
- selection rescue;
- selection harm.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

Seed 022 does not change:

- knowledge formation;
- source grounding;
- semantic closure;
- lossless fallback;
- compact semantic representation.

## Strong Success Pattern

A strong result would look like:

entity artificial sequential ties:
20 / 20

entity abstentions:
20 / 20

target selection:
Seed 021-style baseline < abstaining fusion

selection harms:
0 or near 0

target visibility:
equal or higher

task success:
equal or higher

unsupported claims:
0

ranker model calls:
0

## Failure Interpretation

If selection does not improve, the arbitrary entity vote was not the
main ranking bottleneck.

If selection improves but target visibility does not, the next
bottleneck is selective context assembly.

If target visibility improves but task success does not, the next
bottleneck is downstream decision fidelity under competing memories.

## Scientific Boundary

Seed 022 does not establish:

- optimal RRF weighting;
- learned fusion;
- probabilistic tie thresholds;
- near-tie abstention;
- dynamic Top K;
- million-memory scale;
- RAG superiority.

It tests one narrow rule:

a channel with no candidate-discriminating information should not
manufacture preference from deterministic ordering.

## Burn Rule

The fresh Seed 022 taskset is burned after the first live execution.

Do not tune:

- channel weights;
- tie tolerance;
- RRF K;
- Top K;
- prompts;
- graders;
- task families;
- candidate order;

against the live result and rerun it as fresh evidence.
