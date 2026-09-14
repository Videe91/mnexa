# Seed Growth 023 — Confidence-Gated Context Assembly

## Classification

Exploratory fresh confidence-gated-context-assembly ablation.

## Question

Can MNEXA expose fewer memories when retrieval confidence is strong,
reducing distractor interference without unnecessarily discarding the
correct memory?

## Principle

> Confidence determines context breadth.

## Motivation

Seed 022 improved retrieval by preventing non-discriminative channels
from manufacturing votes.

However, fixed Top-K=3 still presents distractor memories.

Seed 023 freezes routing and ranking and changes only the boundary
between ranked memory and active context.

## Condition A

Seed 022 unchanged:

Seed 020 routing
→ Seed 021 retrieval handles
→ Seed 022 abstaining RRF
→ fixed Top-K=3
→ authoritative context

## Condition B

Use the identical complete ranking and identical RRF scores.

For ordered memories:

M1 >= M2 >= M3 >= M4 >= M5

compute:

g1 = score(M1) - score(M2)
g2 = score(M2) - score(M3)
g3 = score(M3) - score(M4)

The largest gap defines the active-context boundary.

largest g1 → K=1
largest g2 → K=2
largest g3 → K=3

On an exact tie for largest gap, choose the larger K.

No threshold is introduced.

## Scientific Boundary

Dynamic context assembly cannot rescue a target absent from Seed 022's
Top-3 because Condition B is always a prefix of Condition A.

Therefore:

- upstream ranking miss is not an assembly failure;
- removing a target that was in fixed Top-3 is over-pruning;
- retaining the target while removing distractors is safe compaction.

## Fresh Benchmark

20 fresh memories.

Four context-only neighborhoods:

- retry-policy
- lane-routing
- channel-session
- storage-finalization

Five memories per neighborhood.

## Frozen Invariants

Both conditions use identical:

- learned memory;
- evidence;
- candidate routing;
- five-memory neighborhood;
- retrieval handles;
- semantic scores;
- lexical scores;
- entity scores;
- Seed 022 abstention;
- exact-tie midranks;
- RRF constant;
- complete ranking;
- authoritative memory representation;
- transfer query;
- reasoner;
- context-budget configuration.

Only the active-context boundary differs.

## Assembly Classes

### SAFE_COMPACTION

Target is in fixed Top-3 and retained by dynamic assembly while at
least one distractor is removed.

### OVER_PRUNING

Target is in fixed Top-3 but dynamic assembly removes it.

### UPSTREAM_RANK_MISS

Target was absent from fixed Top-3.

This is not attributed to context assembly.

### NO_CHANGE

Dynamic K remains 3.

## Primary Metrics

- fixed target selected;
- dynamic target retained;
- safe compaction;
- over-pruning;
- upstream ranking misses;
- dynamic K distribution;
- distractors before/after.

## Downstream Metrics

- target clause visibility;
- semantic task success;
- wrong-memory presentation;
- wrong-clause occurrences;
- wrong-rule contamination;
- memory words;
- memory segments.

## Same-State Noise Control

If dynamic K=3 and the context set is unchanged:

- use the same frozen snapshot;
- execute transfer reasoning once;
- reuse the exact result.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

The assembler:

- uses no model;
- receives no target ID;
- receives no semantic clause;
- receives no semantic grader.

## Success Pattern

A strong result would preserve most or all targets already available
in fixed Top-3 while materially reducing:

- selected memories;
- model-visible distractors;
- memory segments;
- memory words.

Task success should remain equal or improve.

## Burn Rule

The fresh Seed 023 taskset is burned after its first live execution.

Do not tune:

- gap thresholds;
- gap transformation;
- K range;
- RRF K;
- prompts;
- graders;
- task families;
- ranking;

against the live result and rerun it as fresh evidence.
