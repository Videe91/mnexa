---
name: decide
description: Use when MNEXA work encounters a durable architectural, scientific, persistence, interface, security, privacy, or epistemic decision not already settled by an accepted ADR or specification.
---

# Decide

Create a durable decision artifact before implementation crosses an architectural boundary.

## Workflow

1. Read `docs/state/CURRENT.md`, the relevant vision sections, accepted ADRs, active spec, active plan, and affected code.
2. State the exact decision in one sentence.
3. Classify it D2 or D3 using `.claude/rules/decisions.md`.
4. Identify constraints and evidence already available.
5. Present 2–3 genuinely viable alternatives, including the simplest option where appropriate.
6. For each alternative, state benefits, costs, failure modes, reversibility, and effects on future MNEXA phases.
7. Recommend one option, but separate recommendation from evidence.
8. Create `docs/decisions/ADR-NNNN-<slug>.md` with status `proposed` using the format in `docs/decisions/README.md`.
9. Stop before implementation. D2 requires approval of the proposal; D3 requires explicit owner approval.
10. After approval, change status to `accepted`, record the approval context without rewriting the original rationale, update affected specs/state, then resume work.

## Rules

- Do not record private chain-of-thought. Record decision-relevant options, evidence, rationale, trade-offs, and outcomes.
- Do not create ADRs for D0 implementation trivia.
- Do not let existing code silently decide a question that belongs at D2/D3.
- If evidence later overturns the decision, create a new ADR that supersedes the old one rather than rewriting history.
