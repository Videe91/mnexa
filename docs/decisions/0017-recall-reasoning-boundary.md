# ADR-0017 — Recall / Reasoning Boundary

**Status:** Accepted  
**Date:** 2026-09-14

## Context

MNEXA is a persistent intelligence substrate.

The model is cognitive compute.

MNEXA must therefore determine what accumulated intelligence is
available to a cognitive cycle, but it must not own the reasoning
operation itself.

Seed Growth 028 exposed an architectural coupling in the current seed
harness: the same prompt string could influence both memory activation
and model reasoning.

Changing a reasoning instruction could therefore change which memories
were recalled.

That violates the intended model-independent boundary.

## Decision

Recall intent and reasoning intent are separate inputs owned by separate
components.

The canonical flow is:

    task / situation
          |
          v
    MNEXA recall
          |
          v
    immutable ContextFrame
          |
          +------------------------+
                                   |
                                   v
                              AI model
                               reasons
                                   |
                                   v
                               decision
                                   |
                                   v
                                MNEXA
                         records decision/outcome
                                   |
                                   v
                                 learns

MNEXA owns:

- experience history;
- memory formation;
- recall;
- retrieval ranking;
- memory activation;
- context assembly;
- provenance;
- ContextFrame identity;
- recording decisions and outcomes;
- subsequent learning.

The AI/model owns:

- reasoning;
- interpretation of the supplied ContextFrame;
- planning;
- inference;
- generation of the decision.

## Invariants

1. A recall operation receives recall intent only.

2. Reasoning instructions are not inputs to MNEXA recall.

3. Context assembly completes before model reasoning begins.

4. A completed ContextFrame is immutable.

5. Every ContextFrame carries a deterministic evidence hash.

6. The evidence hash excludes model reasoning instructions.

7. Different models or reasoning instructions may consume the same
   ContextFrame without causing re-retrieval.

8. A new retrieval requires an explicit new recall operation.

9. Model substitution must not change the already-frozen ContextFrame.

10. Decisions and outcomes may reference the ContextFrame that informed
    them.

## Compatibility

The existing seed `decide()` helper may temporarily remain as a
compatibility/testing wrapper.

It is not the normative architecture.

New work must use:

    MNEXA.prepare_context(...)
        -> ContextFrame

followed by model reasoning outside MNEXA.

## Consequence

The durable cognitive cycle becomes:

    MNEXA remembers
        ->
    AI reasons
        ->
    world responds
        ->
    MNEXA learns

## Falsification

This boundary is violated if changing only a model reasoning instruction
changes:

- the recall watermark;
- selected memory IDs;
- model-visible memory text;
- provenance;
- ContextFrame evidence hash.

Such a change requires an explicit new recall operation.
