# Seed Growth 029 — Frozen Context Reasoning

## Classification

Exploratory fresh frozen-context reasoning ablation.

## Question

Given literally identical MNEXA-supplied accumulated intelligence, does
explicit competing-hypothesis reasoning improve the external model's
decision?

## Principle

> MNEXA fixes the evidence. The model is free to change how it reasons
> over that evidence.

## Architectural Purpose

Seed 028 attempted to vary model reasoning instructions while holding
memory constant.

Its causal control failed because the reasoning instruction was also
part of the recall query.

ADR-0017 now separates:

MNEXA context preparation

from:

external model reasoning.

Seed 029 is the first experiment designed around that boundary.

## Cognitive Flow

For each family:

    recall intent
         |
         v
    MNEXA ContextPreparer
         |
         v
    ContextFrame X
         |
         +-----------------------+
         |                       |
         v                       v
    Condition A             Condition B
    model reasoning         model reasoning
    normal instruction      competing-hypothesis
                            instruction

There is one context preparation and two model reasoning calls.

## Condition A

The external model receives:

- the task;
- frozen ContextFrame X;
- no additional reasoning instruction.

## Condition B

The exact same external model receives:

- the same task;
- the literal same ContextFrame X;
- a fixed competing-hypothesis reasoning instruction.

## Hard Architectural Control

For every A/B family pair:

    ContextFrame A is ContextFrame B

and:

    evidence_sha256 A == evidence_sha256 B

The following must also remain identical:

- recall watermark;
- selected memory IDs;
- model-visible MNEXA context;
- context metadata;
- task;
- model.

Only the external model reasoning instruction may differ.

## Call-Count Invariant

For 20 benchmark families:

    context preparations = 20
    recall calls         = 20
    reasoning calls      = 40

A run with 40 recalls is invalid.

## Context Integrity

Every ContextFrame must satisfy:

    ContextFrame.verify_integrity() == true

before either model call is executed.

## Frozen Retrieval Stack

Both conditions share:

- Seed 020 addressing;
- Seed 021 grounded retrieval handles;
- Seed 026 proposition-local semantic/lexical matching;
- Seed 022 non-discriminative channel abstention;
- exact-tie treatment;
- RRF K=60;
- Seed 027 evidence-quorum guarded Pareto attention;
- identical selected memories.

## Strict Decision Grading

Seed 028's stricter post-hoc grader remains primary.

A decision passes only when:

1. the target decision signature is present; and
2. no competing candidate decision signature is present.

Target present plus competing target = failure.

Benchmark grading metadata is removed before:

- memory formation;
- recall;
- context preparation;
- model reasoning.

## Fresh Benchmark

20 fresh families.

Four clusters:

- retry-policy;
- lane-routing;
- channel-session;
- storage-finalization.

Five memories per cluster.

All queries are context-only.

## Primary Metrics

- Condition A exclusive-correct passes;
- Condition B exclusive-correct passes;
- target-rule presence;
- competing-rule mention families;
- total competing-rule hits;
- exclusive rescues;
- exclusive harms.

## Mechanism-Specific Metrics

Report separately for contexts containing more than one active memory:

- A exclusive passes;
- B exclusive passes;
- A competing-rule mentions;
- B competing-rule mentions.

## ADR-0017 Validity Metrics

The following are gates, not secondary metrics:

- context_prepare_calls;
- recall_calls;
- reasoner_calls;
- context_hash_equal_pairs;
- context_hash_mismatch_pairs;
- ContextFrame integrity;
- ADR-0017 boundary validity.

## Causal Validity Rule

The reasoning A/B result may be causally interpreted only when:

    adr_0017_boundary_valid == true

and:

    context_hash_mismatch_pairs == 0

If either fails, do not interpret A/B behavioral differences as a
reasoning-instruction effect.

## Success Pattern

A strong result requires:

1. 20/20 identical ContextFrame hashes;
2. exactly 20 recalls and 40 reasoning calls;
3. all ContextFrames pass integrity verification;
4. multiple multi-memory contexts;
5. Condition B exclusive correctness > A;
6. competing-rule mentions lower in B;
7. exclusive rescues > harms;
8. target-rule presence does not materially decline;
9. unsupported memory admissions remain zero.

## Interpretation Boundary

If B wins, the claim is about external model reasoning:

Given identical MNEXA-supplied intelligence, explicit
competing-hypothesis framing improved this model's decision behavior.

It is not a claim that MNEXA performed the reasoning.

## Failure Interpretation

### ADR-0017 boundary fails

Stop.

The architectural separation is not operationally correct.

### Boundary holds, no behavioral improvement

The architectural boundary is still correct.

Prompt-level competing-hypothesis reasoning is insufficient.

A stronger agent/model-side arbitration mechanism may be required.

### Competing-rule mentions fall but target presence falls

The instruction suppresses alternatives rather than resolving them.

### Multi-memory cases improve disproportionately

The framing is specifically useful when MNEXA preserves uncertainty.

## Scientific Boundary

Seed 029 does not establish:

- optimal model reasoning;
- learned hypothesis arbitration;
- causal reasoning;
- probabilistic belief;
- cross-model superiority;
- production-scale context retrieval;
- conventional-RAG superiority;
- ADR-0003 Grand Proof superiority.

## Burn Rule

The fresh taskset burns after the first live run.

Do not tune:

- reasoning instruction;
- task wording;
- strict signatures;
- retrieval;
- channel abstention;
- quorum;
- Top-K;
- RRF;
- task families;

against the live result and rerun the same benchmark as fresh evidence.
