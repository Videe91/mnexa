# MNEXA Architecture Decision Records

Architecture Decision Records (ADRs) preserve durable choices and the evidence available when those choices were made.

Use zero-padded sequential IDs: `ADR-0001-<slug>.md`.

## Template

```markdown
---
id: ADR-0000
status: proposed
date: YYYY-MM-DD
scope: component | project | scientific | constitutional
vision_refs: []
spec_refs: []
supersedes: []
---

# ADR-0000 — Decision Title

## Decision question

One precise sentence describing what must be decided.

## Context

Why the decision exists and which constraints matter.

## Options considered

### Option A — ...

Benefits, costs, risks, and reversibility.

### Option B — ...

Benefits, costs, risks, and reversibility.

## Decision

The selected option. For a proposed ADR, state the recommendation but do not imply approval.

## Evidence and rationale

Decision-relevant evidence and reasoning available at the time. Record conclusions, not private chain-of-thought.

## Consequences

What becomes easier, harder, constrained, or newly required.

## Reversibility

How difficult the choice is to reverse and what migration would be needed.

## Validation / falsification

What future evidence would support revisiting or superseding this ADR.

## Outcome

`Pending` until evidence exists. Append later outcomes without rewriting the historical decision context.
```

## Rules

- Accepted ADRs are durable source-of-truth artifacts.
- Supersede decisions with new ADRs; do not rewrite the original rationale in hindsight.
- Keep implementation trivia out of ADRs.
- Link decisions to relevant specs, experiments, and commits when those artifacts exist.
