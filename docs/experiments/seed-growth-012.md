# Seed Growth 012 — Grounded Structure Repair

## Classification

Exploratory fresh grounded-structure-repair ablation.

## Question

Can MNEXA inspect and repair its own first-pass structured memory
before durable promotion, improving proposition atomicity and
qualifier attachment without weakening evidence ancestry?

## Motivation

Seed Growth 011 established that separating:

- evidence support span;
- reusable proposition nucleus;
- grounded semantic qualifiers

improved autonomous nucleus recovery while preserving exact physical
ancestry and closed-world admission.

However, two structural failure modes remained.

### Compound nuclei

A physically grounded nucleus could still contain several independent
propositions.

Example:

`refresh the lease and wait 8 seconds`

may contain:

- `refresh the lease`
- `wait 8 seconds`

### Qualifier over-attachment

Conditions and ordering markers could be copied onto propositions they
did not actually govern.

This increased context size and reduced qualifier precision.

## Thesis

The first interpretation of evidence does not need to become durable
memory immediately.

MNEXA should be able to challenge the structure of a proposed memory
before promotion.

The Seed 012 loop is:

raw evidence
→ first-pass structured extraction
→ deterministic grounding
→ structure audit
→ repair
→ deterministic re-grounding
→ durable lesson
→ future action

## Conditions

### A — Initial Structured Memory

Condition A uses the first-pass grounded structured propositions
directly.

This is equivalent to the Seed 011 mechanism.

### B — Grounded Structure Repair

Condition B begins from the exact same first-pass structured proposal.

It receives one additional repair-model call.

The repair model receives:

- the original historical source;
- runtime-admitted first-pass propositions;
- runtime-rejected first-pass candidates;
- rejection reasons.

It may propose a repaired structured representation.

The repaired result must pass the same deterministic source-grounding
gate before becoming durable memory.

## Critical Control

The structured extractor executes exactly once per family.

Both conditions originate from that same proposal.

Target:

`all_initial_structured_proposals_equal == true`

The historical source evidence must also remain byte-equivalent.

Target:

`all_source_evidence_equal == true`

## Repair Operations

The repair model may label its audit decisions as:

- `KEEP`
- `SPLIT`
- `REMOVE_QUALIFIER`
- `REATTACH_QUALIFIER`

The operation labels are diagnostic metadata.

Only the final repaired proposition set affects durable memory.

## Repair Objective 1 — Compound Nucleus Detection

The repair pass asks whether a nucleus contains multiple independently
reusable operational propositions.

It must not blindly split punctuation or conjunctions.

The distinction is semantic.

## Repair Objective 2 — Qualifier Attachment

A qualifier should remain attached only when the source makes it
govern the corresponding nucleus.

Qualifiers must not be propagated to unrelated propositions merely
because they appear in the same paragraph or sequence.

## Negation and Scope

Words such as:

- `only`
- `never`
- `exactly`

remain inside the nucleus when they are part of the proposition's
operational meaning.

The repair pass must not redundantly represent the same physical word
as an overlapping qualifier.

## Runtime Safety

The repair model cannot directly write durable memory.

Every repaired proposition must pass the existing structured grounding
gate.

The runtime verifies:

1. exact support span;
2. authoritative source role;
3. exact nucleus ancestry;
4. exact qualifier ancestry;
5. allowed qualifier type;
6. no duplicate nucleus span;
7. no overlapping final nuclei.

## Fresh Benchmark

Seed 012 contains 20 fresh families.

Five structural styles are represented:

1. numbered syntax;
2. conditional + ordering syntax;
3. conjunction syntax;
4. negation/scope syntax;
5. mixed ordering syntax.

Each family contains four hidden canonical nuclei.

Each family also contains two pre-registered compound challenges.

Total compound challenges:

`40`

## Primary Metrics

### Nucleus Recall

Exact hidden canonical nuclei recovered / expected nuclei.

### Nucleus Precision

Exact hidden canonical nuclei recovered / admitted nuclei.

### Compound Nuclei Admitted

Target:

`repaired < initial`

Ideal:

`0`

### Exact-Nucleus Families

Number of families whose final nucleus set exactly matches the hidden
canonical set.

### Qualifier Micro Recall

Aggregate:

`matched qualifier relations / expected qualifier relations`

Unlike the Seed 011 macro average, this metric does not allow
zero-qualifier families to inflate the headline recall score.

### Qualifier Micro Precision

Aggregate:

`matched qualifier relations / admitted qualifier relations`

### Compound Challenge Survival

The benchmark records how many of the 40 pre-registered compound
challenge nuclei remain after repair.

Target:

`0`

## Secondary Metrics

- durable lesson completeness;
- transfer task success;
- persistent-memory word count;
- repair operation counts.

## Constitutional Targets

The repaired condition targets:

`source ancestry valid families == 20`

`invented nuclei admitted == 0`

`invented qualifiers admitted == 0`

`non-authoritative propositions admitted == 0`

`unsupported claims admitted == 0`

## Resource Asymmetry

Condition B intentionally receives one additional model call per
family for structure repair.

This compute is not hidden or equalized.

Seed 012 is an exploratory mechanism experiment, not a confirmatory
resource-parity benchmark.

The report explicitly records:

- initial extraction model calls;
- repair model calls.

## Interpretation

A successful result would demonstrate that MNEXA can improve the
quality of its own proposed memory representation before persistence.

The desired pattern is:

- nucleus recall increases;
- nucleus precision increases;
- compound nuclei decrease;
- qualifier micro precision increases;
- qualifier micro recall remains high;
- complete lessons increase;
- downstream transfer improves or remains stable;
- constitutional safety remains unchanged.

The key claim would be narrow:

> Grounded memory proposals can be challenged and structurally repaired
> before promotion without sacrificing exact evidence ancestry.

## What Seed 012 Does Not Prove

It does not prove:

- universal semantic decomposition;
- autonomous truth discovery;
- causal reasoning;
- confidence calibration;
- collective knowledge promotion;
- multi-source contradiction resolution;
- conventional-RAG superiority.

## Frozen Components

No changes to:

- `mnexa_seed.py`
- canonical objects
- persistence
- embeddings
- retrieval channels
- ranking
- context budget
- evidence-role semantics
- source-span semantics
- claim ancestry
- transfer reasoning policy

## Burn Rule

The fresh Seed 012 task set is burned after the first live execution.

Do not tune against this task set and rerun it as fresh evidence.
