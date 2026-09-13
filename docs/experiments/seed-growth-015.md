# Seed Growth 015 — Semantic Closure Compaction

## Classification

Exploratory fresh semantic-closure compaction ablation.

## Question

Can MNEXA preserve the semantic correctness and safety of Seed 014
while materially reducing model-visible persistent-memory size?

## Motivation

Seed Growth 014 established a lossless admission boundary:

valid authoritative evidence + invalid structure
→ preserve exact evidence as unresolved grounded support

invalid / fabricated / non-authoritative evidence
→ reject

The frozen 014 run achieved:

- 20/20 semantic task passes;
- 0 semantic violations;
- 0 unsafe support admissions;
- 0 unsupported claims.

However, lossless semantic memory remained verbose.

The principal source of redundancy is repeated rendering of the same
authoritative support span under multiple retrieval handles.

Example:

P1 → full source paragraph
P2 → same full source paragraph
P3 → same full source paragraph
P4 → same full source paragraph

Seed 015 tests whether that representation can be compressed without
weakening semantics.

## Principle

> Evidence should exist once. Knowledge structures may reference it many
> times.

## Conditions

Both conditions receive:

- the same raw evidence;
- the same initial structured proposal;
- the same repair proposal;
- the same structured admissions;
- the same unresolved fallback records;
- the same transfer task;
- the same transfer model.

### Condition A — Verbose Lossless Memory

Seed 014 representation.

Every structured proposition independently renders its complete
authoritative semantic support.

Fallback evidence is also rendered independently.

### Condition B — Compact Evidence Index

Every unique physical support span is emitted once.

Example:

E1:
`refresh the lease; wait 14 seconds; retry exactly once; never reuse
the old nonce`

References:

P1 handle=`refresh the lease` → E1  
P2 handle=`wait 14 seconds` → E1  
P3 handle=`retry exactly once` → E1  
P4 handle=`never reuse the old nonce` → E1

The evidence is not summarized or rewritten.

## Evidence Identity

Deduplication requires identical:

- source hash;
- source start offset;
- source end offset;
- support span hash.

Text equality alone is insufficient.

The same sentence appearing at two different historical locations
remains two different evidence records.

## Unresolved Fallback

Unresolved grounded support also enters the evidence index.

Example:

E2:
`do not acknowledge the original event`

G1 unresolved → E2

The exact support survives.

No generated replacement claim is introduced.

## Critical Controls

The following must remain true:

`all_source_evidence_equal == true`

`all_initial_structured_proposals_equal == true`

`all_repair_proposals_equal == true`

`all_structured_admissions_equal == true`

`all_fallback_records_equal == true`

Condition B receives no additional extraction, repair, summarization,
or compaction model call.

Compaction is deterministic.

## Primary Metrics

### Semantic Task Success

Compact memory should preserve downstream semantic performance.

### Semantic Violations

Compact representation must not introduce:

- polarity loss;
- scope loss;
- cardinality loss;
- condition loss.

### Exact Semantic Clause Visibility

Decision-relevant evidence should remain exactly visible when it existed
in the lossless representation.

### Model-Visible Memory Words

Primary efficiency measure.

## Secondary Metrics

- complete lessons;
- support occurrences before deduplication;
- unique physical support records;
- duplicate support occurrences removed;
- unsupported claims admitted.

## Safety Target

`compact_unsupported_claims_admitted == 0`

## Compaction Target

A strong result would satisfy:

`compact_semantic_task_passes >= verbose_semantic_task_passes`

while:

`mean_compact_memory_words < mean_verbose_memory_words`

and ideally produce a substantial relative reduction.

## Scientific Interpretation

A successful result would support:

> MNEXA can separate semantic evidence from the structures that index it,
> storing and presenting evidence once while allowing multiple knowledge
> handles to reference it without sacrificing downstream correctness.

This would strengthen the architecture:

experience
→ evidence
→ evidence identity
→ knowledge references
→ compact context
→ reasoning

## What Seed 015 Does Not Prove

It does not prove:

- optimal context compression;
- semantic summarization;
- learned compression;
- lossy compression safety;
- multi-document synthesis;
- contradiction resolution;
- conventional-RAG superiority.

It tests only deterministic redundancy removal.

## Frozen Components

No changes to:

- `mnexa_seed.py`
- persistence
- retrieval
- embeddings
- ranking
- evidence-role admission
- structured extraction
- repair prompt
- support-first fallback
- transfer reasoner

Only model-visible representation of the same admitted evidence is
ablated.

## Burn Rule

The fresh Seed 015 task set is burned after the first live execution.

Do not tune the renderer, task set, graders, repair process, or transfer
prompt against the first live result and rerun it as fresh evidence.
