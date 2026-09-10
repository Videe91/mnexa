---
id: ADR-0001
status: accepted
date: 2026-09-10
scope: project
vision_refs:
  - docs/vision/01-thesis.md
  - docs/vision/08-self-model-meta-memory-self-improvement.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0001 — Use Decision-First Development for MNEXA

## Decision question

How should MNEXA preserve the intellectual decisions and experimental evidence that produce its implementation without drowning development in low-value logging?

## Context

MNEXA's thesis treats persistent decisions, evidence, outcomes, revisions, and accumulated capability as more durable than any individual model or implementation. Building the project code-first would allow important architecture and benchmark choices to disappear into transient coding sessions. Logging every tool call and micro-decision would create the opposite failure: a large event stream with poor decision signal.

The development process should therefore preserve the project's meaningful cognitive history while leaving implementation details lightweight.

## Options considered

### Option A — Code-first development

Let coding agents make most choices during implementation and rely on Git/code comments afterward.

Benefits: fastest local implementation and least process overhead.

Costs: architectural intent, rejected alternatives, and evidence are easily lost; later code appears authoritative merely because it exists.

Reversibility: high initially, but historical rationale cannot be reconstructed reliably after the fact.

### Option B — Decision-first development

Record durable decisions as ADRs, derive explicit specs and implementation plans, implement inside the approved decision space, and attach experiments/outcomes afterward.

Benefits: preserves intent and evidence; separates vision, decisions, specification, implementation, and proof; gives future coding agents durable context.

Costs: modest process overhead and a need to classify decisions correctly.

Reversibility: high; the process can be simplified later if it proves too heavy.

### Option C — Full development event sourcing

Persist every coding-agent action, tool call, reasoning transition, and micro-decision as project history.

Benefits: maximal raw traceability.

Costs: enormous noise, privacy/reasoning concerns, high storage/processing overhead, and weak signal-to-noise for durable engineering decisions.

Reversibility: technically high but operationally costly.

## Decision

Adopt **Option B — Decision-first development**.

MNEXA will preserve durable decisions and experimental evidence rather than every cognitive micro-step. Code may be written autonomously inside an approved decision space; coding agents may not silently expand or redefine that space.

## Evidence and rationale

The approach matches MNEXA's own architectural philosophy: immutable history should remain distinguishable from evolving interpretation; important knowledge should retain provenance; outcomes should be able to revise earlier beliefs; and model/session replacement should not destroy accumulated intelligence.

The repository therefore separates:

`Vision → ADRs → Specs → Plans → Code/Tests → Experiments/Outcomes → Revised/Superseding ADRs`

Decision tiers prevent the process from turning implementation trivia into governance paperwork.

## Consequences

- D2 durable decisions require ADR coverage before implementation.
- D3 constitutional/scientific decisions require explicit owner approval.
- Specifications define required behavior after decisions are accepted.
- Implementation plans translate specs into task-sized work.
- Experiments are first-class artifacts and remain separate from unit/integration tests.
- Claude Code sessions use repository state rather than chat memory as the durable handoff mechanism.
- Negative experimental outcomes are preserved and may supersede accepted architecture.

## Reversibility

High. If the process becomes too heavy, decision thresholds can be changed through a later ADR without changing MNEXA's product semantics.

## Validation / falsification

Revisit after the MNEXA v0 proof cycle. Evidence that this process materially slows iteration without improving traceability, reproducibility, architectural consistency, or recovery across coding sessions would support simplifying it.

## Outcome

Pending MNEXA v0 proof-cycle review.
