# Implementation Rules

## Work boundaries

Implement only the active approved plan task. Do not opportunistically build later MNEXA phases.

Before editing:

1. Read the relevant spec and ADRs.
2. Inspect the files being changed.
3. Confirm the task's interfaces and acceptance criteria.
4. Identify any uncovered D2/D3 decision before writing implementation code.

## TDD

For behavior changes:

1. Write the smallest meaningful failing test.
2. Run it and confirm the expected failure.
3. Implement the minimum code required.
4. Run the focused test.
5. Run the relevant wider suite.
6. Refactor only while tests stay green.

Documentation/governance-only changes do not require artificial code tests; verify structure, links, syntax, and repository state instead.

## Scope control

- Prefer focused modules with one clear responsibility.
- YAGNI: future vision is not current scope.
- Avoid abstractions that have only hypothetical consumers.
- Do not introduce distributed infrastructure until measured constraints require it.
- Do not optimize benchmark-specific cases.
- Do not change persistent semantics as a side effect of refactoring.

## Traceability

Durable implementation should be traceable to the governing spec/ADR. Use identifiers in plan tasks, commit messages, or nearby documentation rather than noisy comments on every line.

## Evidence from implementation

If coding reveals that an approved design cannot satisfy its invariant, stop. Capture the concrete evidence and return to the decision/spec layer. Do not quietly weaken the requirement to make tests pass.

## Completion

Never report success from intention. Report the verification command or inspection performed and its result. Update `docs/state/CURRENT.md` when the active milestone, plan, task, blocker, or next action changes.
