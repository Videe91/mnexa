# Decision Rules

MNEXA preserves the decisions that create the code, not just the code itself.

## Decision tiers

### D0 — Implementation detail

Examples: local variable names, private helper decomposition, loop structure, formatting, test fixture mechanics.

Record in code/tests when useful. No ADR is required.

### D1 — Local design

Examples: internal class split inside an already approved component, local module boundaries, test-double design, non-durable refactoring approach.

Record in the active plan/task notes. Claude may decide within the approved specification if the choice does not change a durable interface or invariant.

### D2 — Durable decision

Examples: persistent schema, externally consumed interface, canonical identity format, event ordering semantics, storage guarantees, major dependency, cross-component contract, migration behavior.

An ADR is required before implementation. If no accepted ADR/spec already covers the choice, create a proposal using the `decide` skill and stop for approval.

### D3 — Constitutional or scientific decision

Examples: changing a MNEXA constitutional invariant, evidence semantics, knowledge/truth promotion rules, benchmark success criteria, hidden-evaluation methodology, privacy/authorization guarantees, or what would count as proof of the thesis.

An ADR plus explicit owner approval is required before implementation or benchmark execution proceeds.

## ADR lifecycle

Use one of these statuses:

- `proposed`
- `accepted`
- `rejected`
- `superseded`
- `deprecated`

A later ADR may supersede an earlier ADR. Never rewrite historical reasoning to make an old decision look different in hindsight.

## Required ADR contents

Each durable ADR records:

- decision ID and status
- date and scope
- relevant vision/spec references
- context: what forced the decision
- real alternatives considered
- selected decision
- reasons and evidence available at decision time
- consequences and trade-offs
- reversibility
- validation/falsification condition
- later outcome, when known
- supersession links, when applicable

## Decision discipline

- Code does not silently supersede an ADR.
- Repetition or convenience does not turn a D2/D3 question into D0/D1.
- A new dependency is not 'just implementation' when it constrains architecture or persisted behavior.
- Do not manufacture an ADR for trivial choices; signal matters more than volume.
- When uncertain between D1 and D2, surface the decision rather than hiding it.
- Record the decision artifact, not private chain-of-thought. Preserve options, evidence, rationale, consequences, and outcomes.
