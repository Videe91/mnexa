# Seed Growth 026 — Proposition-Local Retrieval

## Classification

Exploratory fresh proposition-local retrieval ablation.

## Question

Can MNEXA distinguish highly similar memories more reliably by matching
the query against individual reusable propositions rather than scoring
the entire retrieval representation as one document?

## Principle

> Retrieve the proposition, not the memory blob.

## Motivation

Seeds 023–025 improved context assembly.

Seed 025 showed that the larger remaining failure is increasingly
upstream retrieval ranking rather than active-context pruning.

Several memories can share most of their retrieval representation while
differing in only one decision-relevant proposition.

Whole-document similarity can therefore allow shared background content
to dilute the discriminative proposition.

## Condition A — Whole Retrieval Document

Use the existing Seed 021 retrieval representation.

For each candidate memory:

query
→ complete retrieval-handle document
→ one semantic score
→ one lexical score

Then:

Seed 022 abstaining fusion
→ RRF
→ Seed 025 Pareto-safe assembly
→ unchanged authoritative reasoning memory.

## Condition B — Proposition-Local Retrieval

Use the same existing retrieval handles.

Split them into independent proposition-local retrieval units.

For each candidate memory:

query
→ score each proposition independently
→ memory semantic score = maximum proposition semantic score
→ memory lexical score = maximum proposition lexical score

The entity channel remains unchanged.

Then use the identical:

Seed 022 abstention
→ RRF
→ Seed 025 Pareto-safe assembly
→ authoritative reasoning memory.

## Grounded Fallback

UNRESOLVED_GROUNDED_SUPPORT remains an exact retrieval unit.

It is not rewritten into a generated proposition.

## Important Separation

Retrieval representation remains separate from reasoning representation.

Proposition-local units determine which memory is activated.

The reasoner still receives the original compact authoritative semantic
memory.

No retrieval handle is promoted into authoritative truth.

## Fresh Benchmark

20 fresh families.

Four clusters:

- retry-policy
- lane-routing
- channel-session
- storage-finalization

Five memories per cluster.

Within each cluster, all five memories share three background
propositions and differ primarily in one decision-relevant proposition.

This intentionally stresses proposition discrimination.

## Frozen Invariants

Both conditions share:

- memory formation;
- source evidence;
- candidate routing;
- candidate population;
- query;
- retrieval handles;
- embedder;
- lexical similarity function;
- entity channel;
- Seed 022 abstention;
- tie handling;
- RRF constant;
- Seed 025 Pareto assembly;
- authoritative presentation memory;
- reasoner;
- context budget.

Only semantic/lexical retrieval scoring granularity differs.

## Primary Ranking Metrics

- target rank #1;
- target Top-3 availability;
- mean target rank;
- ranking rescues;
- ranking harms.

## Assembly Metrics

- target retained after Pareto assembly;
- upstream ranking misses;
- over-pruning;
- safe compaction;
- mean active context size.

## Downstream Metrics

- semantic task success;
- target visibility;
- wrong-memory exposure;
- wrong-clause occurrences;
- wrong-rule contamination.

## Cost Metrics

Proposition-local retrieval performs more similarity comparisons.

Record:

- mean proposition units per memory;
- whole semantic comparisons per query;
- local semantic comparisons per query;
- whole lexical comparisons per query;
- local lexical comparisons per query.

The experiment must not hide the added retrieval-compute cost.

## Same-State Noise Control

If both conditions produce the same assembled canonical memory set:

- use the same frozen snapshot;
- perform the transfer evaluation once;
- reuse the exact evaluation result.

## Safety

Expected:

bundle_unsupported_claims_admitted == 0

Ranker model calls:

0

Neither ranker receives:

- target family ID;
- semantic grader;
- expected answer;
- hidden canonical answer.

## Strong Success Pattern

A strong result would show:

- higher target Top-3 availability;
- lower mean target rank;
- ranking rescues greater than ranking harms;
- fewer upstream ranking misses;
- equal or better target retention after Pareto assembly;
- equal or better downstream task performance;
- no unsupported admissions.

The benefit must be interpreted alongside increased deterministic
similarity-comparison cost.

## Failure Interpretation

If local scoring does not improve ranking, shared-document dilution is
not the dominant retrieval problem.

If ranking improves but Pareto context does not, assembly interaction
remains a bottleneck.

If target ranking improves but downstream task performance does not,
decision behavior under competing valid memories becomes the next
frontier.

If retry-policy improves disproportionately, proposition locality may be
particularly useful for highly homologous memory families rather than
all retrieval.

## Scientific Boundary

Seed 026 does not establish:

- learned retrieval;
- optimal proposition segmentation;
- production-scale indexing;
- million-memory retrieval;
- fuzzy identity routing;
- conventional-RAG superiority;
- Grand Proof superiority.

It tests a narrow representation hypothesis:

Does scoring individual existing grounded retrieval propositions improve
selection among highly similar memories?

## Burn Rule

The taskset is burned after its first live execution.

Do not tune proposition splitting, aggregation, prompts, graders,
embedding model, RRF constant, Top-K, or task families against the live
result and rerun it as fresh evidence.
