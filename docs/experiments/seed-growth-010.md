# Seed Growth 010 — Autonomous Atomic Boundary Discovery

## Classification

Exploratory fresh autonomous atomic-boundary-discovery ablation.

## Question

Can MNEXA discover reusable proposition boundaries directly from raw
authoritative evidence without receiving benchmark-authored canonical
atomic boundaries?

## Motivation

Seed Growth 009 established that when canonical boundaries are known,
MNEXA can reject compound evidence spans while preserving:

- 100% atomic recall,
- 100% knowledge completeness,
- zero unsupported claims,
- lower memory-context cost.

However, Seed 009 supplied the runtime with the correct atomic
boundaries.

Real evidence does not provide those boundaries.

Seed Growth 010 removes that oracle from the experimental condition.

## Conditions

### A — Oracle Atomicity

The runtime receives the four benchmark-authored canonical atomic
source spans.

This is an upper bound.

### B — Autonomous Atomic Boundary Discovery

The model receives:

- the same raw historical evidence,
- role markers,
- no canonical proposition boundaries.

It proposes minimal exact source spans representing independently
reusable operational propositions.

The runtime receives only:

- raw source,
- proposed text,
- proposed source quote.

The autonomous admission function does NOT receive:

- the family fixture,
- canonical atom IDs,
- canonical atom text,
- benchmark boundary offsets.

## Autonomous Runtime Gate

The gate checks only properties knowable from raw evidence:

1. candidate is structurally valid;
2. text equals source_quote;
3. source_quote occurs exactly once;
4. source span belongs to `authoritative_correction`;
5. duplicate spans are rejected;
6. final admitted spans may not overlap.

When grounded candidate spans overlap, the shorter span is considered
first.

This is a generic minimum-span heuristic.

It is not canonical boundary knowledge.

## Important Limitation

The runtime cannot prove semantic atomicity.

For example, if the model proposes only:

`wait 8`

instead of:

`wait 8 seconds`

both could be valid physical source spans.

The runtime cannot know which one is the correct semantic proposition
without external semantic information.

Canonical benchmark boundaries are therefore used only after memory
construction to measure discovery quality.

## Benchmark Evidence Styles

The 20 fresh families include at least five structural styles:

1. semicolon-separated clauses;
2. conjunction + contrastive conjunction;
3. inline numbered clauses;
4. conditional introductory clauses;
5. mixed commas, semicolons and ordering language.

The purpose is to make simple sentence splitting insufficient.

## Canonical Units

Each family contains four hidden benchmark atomic propositions.

These are used only for:

- oracle Condition A;
- post-hoc scoring.

They are not passed into the autonomous Condition B gate.

## Compound Challenges

Each family contains two physically valid, authoritative,
multi-proposition source spans:

- challenge C1 crosses A1 + A2;
- challenge C2 crosses A3 + A4.

If the model does not propose them independently, the harness inserts
them into the autonomous proposal before runtime admission.

Across 20 families this produces 40 compound challenges.

The autonomous gate still receives no canonical boundary map.

The challenge mechanism merely guarantees that overlap/minimality
logic is exercised.

## Primary Metrics

### Canonical Boundary Recall

Exact canonical atomic propositions admitted divided by canonical
atomic propositions expected.

### Canonical Boundary Precision

Exact canonical atomic propositions admitted divided by all
autonomously admitted atoms.

### Exact-Boundary Families

Number of families where autonomous admitted atom set exactly equals
the canonical atom set.

### Invented Spans Admitted

Target:

`0`

### Non-authoritative Spans Admitted

Target:

`0`

### Overlapping Final Span Pairs

Target:

`0`

### Source-Ancestry Valid Families

Target:

`20 / 20`

## Secondary Metrics

- lesson knowledge completeness;
- transfer task sufficiency;
- persistent-memory word count;
- unsupported claims admitted.

## Source-Evidence Invariant

Conditions A and B must receive byte-equivalent historical source
evidence.

Target:

`all_source_evidence_equal == true`

## Scientific Interpretation

A strong result would look like:

- autonomous canonical-boundary recall close to oracle;
- autonomous canonical-boundary precision close to oracle;
- zero invented spans;
- zero non-authoritative admissions;
- zero overlapping final spans;
- 100% exact source ancestry;
- high knowledge completeness;
- high downstream task sufficiency.

A lower autonomous score is not a failed experiment.

It identifies the actual remaining boundary-discovery problem.

## What This Experiment Does Not Prove

Seed Growth 010 does not prove:

- generalized natural-language semantic decomposition;
- universal proposition ontology;
- causal understanding;
- autonomous truth discovery;
- collective knowledge promotion;
- conventional-RAG superiority.

It tests one narrow claim:

> Can atomic evidence structure be discovered from raw evidence rather
> than supplied by an oracle?

## Frozen Components

No changes to:

- `mnexa_seed.py`;
- persistence;
- retrieval channels;
- embeddings;
- ranking;
- context budget;
- evidence-role semantics;
- claim-ancestry semantics;
- transfer reasoning policy;
- canonical object model.

## Burn Rule

The 20 task families are exploratory and are burned after the first
live execution.

Do not tune against Seed Growth 010 and rerun it as fresh evidence.
