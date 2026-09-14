# Seed Growth 028 — Competing-Hypothesis Reasoning

## Classification

Exploratory fresh competing-hypothesis reasoning ablation.

## Question

When uncertainty causes MNEXA to preserve several candidate memories,
can the reasoner keep them as alternatives instead of combining
mutually incompatible rules?

## Principle

> Preserve alternatives without conflating them.

Equivalent formulation:

> Uncertainty should widen the hypothesis set, not merge its members.

## Motivation

Seed 027 established that one active retrieval signal is insufficient
evidence for aggressive context pruning.

Evidence-quorum attention preserved all Top-3 targets in its fresh
benchmark.

That safety increased active-context breadth.

The resulting failure mode is different:

the correct target may remain visible while the reasoner incorporates
additional incompatible candidate rules into the final answer.

Seed 028 tests the reasoning boundary after uncertainty has correctly
been preserved.

## Frozen Cognitive Stack

Both conditions share:

Seed 020 addressing
→ Seed 021 grounded retrieval handles
→ Seed 026 proposition-local retrieval
→ Seed 022 non-discriminative channel abstention
→ RRF
→ Seed 027 evidence-quorum guarded Pareto assembly
→ identical selected snapshot

No retrieval or attention mechanism changes.

## Condition A

Use the existing Seed 027 transfer reasoning behavior.

## Condition B

Use the same base transfer question.

Add one fixed epistemic instruction:

- memories are alternative candidate hypotheses;
- candidates may conflict;
- select the single candidate rule whose decision-relevant evidence
  best answers the question;
- do not merge incompatible candidate rules;
- state only the chosen rule, with non-conflicting background facts
  only when necessary.

## Strict Success Definition

A final decision passes only if:

1. the target decision signature is present; and
2. zero competing decision signatures are present.

Therefore:

target present + competing rule present = FAIL

This metric is intentionally stricter than target-presence grading.

## Grader Isolation

Decision signatures and competing signatures are benchmark-only
post-hoc metadata.

They are removed before:

- memory formation;
- retrieval;
- context assembly;
- model reasoning.

The strict grader uses zero model calls.

## Critical Presentation Control

The existing evaluation seam uses the transfer prompt during the
cognitive cycle.

Therefore the experiment records whether A and B actually receive the
same:

- memory segments;
- visible family IDs;
- memory segment count.

For every family:

presentation_control.valid =
    memory_segments_equal
    AND visible_family_ids_equal
    AND memory_segment_count_equal

## Causal Validity Rule

If:

presentation_causal_interpretation_valid == false

then the experiment must not be interpreted as clean evidence that the
epistemic reasoning frame caused the decision difference.

The run remains useful diagnostically, but the A/B causal claim is
invalid because the added instruction altered memory activation.

Do not tune and rerun the burned benchmark.

## Fresh Benchmark

20 fresh families.

Four clusters:

- retry-policy
- lane-routing
- channel-session
- storage-finalization

Five memories per cluster.

All queries are context-only.

Each cluster shares three background propositions and differs primarily
in one decision-relevant proposition.

## Primary Metrics

- base exclusive-correct passes;
- alternative-aware exclusive-correct passes;
- competing-rule mention families;
- total competing-rule signature hits;
- exclusive rescues;
- exclusive harms.

## Mechanism-Specific Metrics

Report the same metrics specifically on multi-memory contexts.

If the fresh benchmark produces too few multi-memory contexts, the
competing-hypothesis mechanism is weakly exercised.

## Secondary Metrics

Retain the existing semantic task grader for comparison:

- semantic task passes;
- semantic violations.

The strict exclusive metric is primary.

## Controls

Both conditions share:

- memories;
- evidence;
- candidate routing;
- proposition units;
- channel scores;
- abstention;
- fused ranking;
- quorum boundary;
- selected family IDs;
- snapshot;
- reasoner model;
- context budget;
- base user question.

Only the epistemic reasoning frame differs intentionally.

## Strong Success Pattern

A strong result requires:

1. presentation causal control valid for all or nearly all families;
2. multiple multi-memory contexts;
3. alternative-aware exclusive passes > baseline;
4. competing-rule mentions materially lower;
5. exclusive rescues > harms;
6. target-rule presence not materially degraded;
7. unsupported memory admissions remain zero.

## Failure Interpretation

### Presentation control fails

The framing instruction altered memory activation.

Do not attribute decision differences purely to hypothesis framing.

The next experiment must separate recall query from reasoner
instruction at the runtime interface.

### Target presence stays high but competing mentions remain

Instruction framing is insufficient.

MNEXA needs a structural hypothesis-selection operation rather than a
reasoning prompt.

### Competing mentions fall but target presence also falls

The frame is suppressing rather than resolving uncertainty.

### Exclusive correctness rises materially

Treating retained memories explicitly as competing alternatives is
useful downstream of uncertainty-preserving attention.

## Scientific Boundary

Seed 028 does not establish:

- optimal hypothesis selection;
- causal reasoning;
- probabilistic belief;
- contradiction resolution;
- learned arbitration;
- production-scale reasoning;
- conventional-RAG superiority.

It tests whether explicit epistemic framing helps a fixed reasoner avoid
conflating mutually incompatible candidate memories.

## Burn Rule

The fresh Seed 028 taskset burns after its first live execution.

Do not tune:

- the epistemic instruction;
- signatures;
- retrieval;
- quorum;
- Pareto;
- Top-K;
- prompts;
- task families;
- graders;

against the live result and rerun the same taskset as fresh evidence.
