# Seed Growth 011 — Grounded Structured Proposition

## Classification

Exploratory fresh grounded-structured-proposition ablation.

## Question

Can MNEXA separate the literal span that provides evidence from the
smaller reusable proposition that the evidence supports, while
preserving exact ancestry for both the proposition nucleus and its
semantic qualifiers?

## Motivation

Seed Growth 010 demonstrated that autonomous atomization could maintain:

- exact physical ancestry;
- authoritative-role admission;
- zero invented spans;
- zero unsupported claims;
- zero overlapping final spans.

However, autonomous exact-boundary recovery remained substantially
below the oracle.

Two failure classes were especially important.

### Surface syntax mismatch

A source may contain:

`1) start a new upload session;`

while the reusable proposition is:

`start a new upload session`

The reusable proposition is fully supported by the source, but requiring
the proposition and evidence span to be identical causes unnecessary
rejection.

### Semantic wrapper fusion

A source may contain:

`When WD-28 is observed, read the leader epoch`

The reusable nucleus is:

`read the leader epoch`

while:

`When WD-28 is observed`

is a condition governing that proposition.

Treating the entire source span as one indivisible atom fuses
proposition content with semantic context.

## Thesis

Seed 011 tests:

> Evidence representation and knowledge representation may have
> different boundaries without severing provenance.

The structured proposition representation is:

ExperienceRecord
→ authoritative source span
→ proposition
   → nucleus
   → semantic qualifiers
→ reusable knowledge

Every stored component remains physically grounded in the immutable
source.

## Conditions

### A — Seed 010 Flat Autonomous Atomization

Condition A uses the existing Seed Growth 010 autonomous extractor and
runtime gate.

A reusable atom is represented directly by one exact source span.

### B — Grounded Structured Proposition

Condition B asks the same frozen model to produce:

- `source_quote`
- `nucleus_quote`
- zero or more semantic qualifiers

The runtime validates each component deterministically.

## Structured Proposition Schema

Example:

```json
{
  "source_quote": "When ZX-11 occurs, refresh the recovery lease",
  "nucleus_quote": "refresh the recovery lease",
  "qualifiers": [
    {
      "type": "condition",
      "source_quote": "When ZX-11 occurs"
    }
  ]
}
```

## Admission Invariants

For every admitted proposition:

1. `source_quote` must occur exactly once in the raw source.
2. The support span must belong to `authoritative_correction`.
3. `nucleus_quote` must occur exactly once inside `source_quote`.
4. Every qualifier quote must occur exactly once inside `source_quote`.
5. Qualifier types are closed to:

   * `condition`
   * `ordering`
   * `scope`
   * `negation`
6. Qualifier spans may not overlap the nucleus.
7. Duplicate nucleus spans are rejected.
8. Final admitted nucleus spans may not overlap.
9. No benchmark canonical boundary information enters the admission
   function.

## Important Distinction

A proposition may therefore have:

support span:
`1) refresh the recovery lease`

nucleus:
`refresh the recovery lease`

The syntax marker remains preserved in source ancestry without becoming
part of reusable semantic content.

## Benchmark Styles

Twenty fresh families use five structural styles:

1. numbered prefixes;
2. conditional + ordering language;
3. conjunctions;
4. propositions containing semantic negation/scope;
5. mixed conditional and ordering language.

Each style appears four times.

## Hidden Canonical Nuclei

Every family contains four benchmark-authored canonical proposition
nuclei.

These are used only for post-hoc scoring.

They are not passed to the structured admission runtime.

## Expected Qualifiers

Conditional and ordering benchmark families contain hidden expected
qualifier annotations.

These are also grader-only.

They do not enter extraction or admission.

## Compound-Nucleus Challenges

Each family contains two physically real authoritative spans:

* C1 covers A1 + A2;
* C2 covers A3 + A4.

They are injected into the structured proposal if the model does not
propose them itself.

The runtime still receives no hidden canonical boundaries.

The challenge mechanism guarantees that overlapping compound nuclei are
tested.

Across 20 families there are 40 structured compound challenges.

## Primary Metrics

### Canonical Nucleus Recall

Exact canonical nuclei recovered / canonical nuclei expected.

### Canonical Nucleus Precision

Exact canonical nuclei recovered / all admitted nuclei.

### Exact-Nucleus Families

Families in which the final nucleus set equals the hidden canonical
nucleus set exactly.

### Qualifier Recall

Expected grounded nucleus/qualifier relations recovered / expected
qualifier relations.

### Qualifier Precision

Correct grounded qualifier relations / all admitted qualifier
relations.

### Source-Ancestry Validity

Target:

`20 / 20`

### Invented Nuclei

Target:

`0`

### Invented Qualifiers

Target:

`0`

### Non-authoritative Propositions

Target:

`0`

### Overlapping Final Nuclei

Target:

`0`

### Compound Nuclei Admitted

Target:

`0`

### Unsupported Claims Admitted

Target:

`0`

## Secondary Metrics

* complete durable lessons;
* transfer task sufficiency;
* model-visible persistent-memory word count.

## Experimental Control

Both conditions receive byte-equivalent historical source evidence.

The experiment records:

`all_source_evidence_equal`

and requires it to remain true.

The two conditions intentionally use different extraction prompts and
representations. Therefore this experiment evaluates the complete flat
vs structured extraction mechanism, not merely a deterministic runtime
field toggle.

## Scientific Interpretation

A successful result would show that structured propositions improve
autonomous knowledge decomposition while preserving the constitutional
safety properties established in Seeds 006–010.

Strong evidence would look like:

* structured nucleus recall > flat nucleus recall;
* structured nucleus precision > flat nucleus precision;
* high qualifier recall and precision;
* zero invented nuclei;
* zero invented qualifiers;
* zero non-authoritative promotion;
* zero overlapping final nuclei;
* zero unsupported claims;
* high knowledge completeness;
* high downstream task sufficiency.

## What Seed 011 Does Not Prove

It does not establish:

* universal semantic parsing;
* causal understanding;
* truth beyond the supplied evidence;
* collective promotion;
* autonomous confidence calibration;
* conventional-RAG superiority.

It tests one narrow proposition:

> Reusable knowledge may be normalized into structured propositions
> while every semantic component remains explicitly anchored to exact
> historical evidence.

## Frozen Components

No changes to:

* `mnexa_seed.py`
* persistence
* retrieval
* embeddings
* ranking
* context budget
* canonical object model
* evidence-role policy
* claim-ancestry gate
* transfer reasoning policy

## Burn Rule

The fresh Seed 011 task set is burned after the first live model
execution.

Do not tune against the result and rerun the same task set as fresh
evidence.
