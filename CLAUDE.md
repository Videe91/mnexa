# MNEXA Engineering Constitution

MNEXA is a model-independent persistent intelligence substrate. The canonical vision lives under `docs/vision/`.

This repository is developed decision-first: code is the executable consequence of recorded decisions and evidence. Code is not the source of architectural truth.

## Source-of-truth hierarchy

When sources conflict, stop and resolve the conflict rather than silently choosing one.

1. `docs/vision/` — north-star purpose and constitutional principles.
2. Accepted ADRs in `docs/decisions/` — why durable choices were made.
3. Approved specifications in `docs/specs/` — what must be true.
4. Active implementation plan in `docs/plans/` — how an approved spec is being implemented.
5. Code and tests — executable implementation of the above.
6. Experiments in `docs/experiments/` — evidence about whether MNEXA actually improves intelligence.

## Session startup

Before architectural or implementation work:

1. Read `docs/state/CURRENT.md`.
2. Inspect the current branch and recent repository history.
3. Read the active specification and plan, if any.
4. Read the relevant ADRs and vision sections.
5. Inspect the actual code before making claims about it. Never speculate about files you have not opened.

The detailed project rules are in `.claude/rules/`.

## Decision law

Use the decision tiers in `.claude/rules/decisions.md`.

- D0 implementation choices may be made locally and captured by code/tests.
- D1 local design choices belong in the active implementation plan or task notes.
- D2 durable choices require an ADR before implementation proceeds.
- D3 constitutional or scientific choices require an ADR and explicit owner approval.

A durable decision includes changes to architecture, persistence semantics, public interfaces, invariants, benchmark methodology, epistemic semantics, privacy/security boundaries, major dependencies, or cross-component behavior.

If an accepted ADR/spec does not cover a required D2/D3 decision, use the `/decide` workflow, record the proposal, and stop at the approval boundary. Do not silently expand the decision space while coding.

## Scientific law

MNEXA is a scientific claim as well as a software system.

- Tests establish implementation correctness; experiments test hypotheses. Do not confuse them.
- Never claim a mechanism improves intelligence without a controlled comparison.
- Freeze evaluation rules before using them to judge the mechanism they evaluate.
- Preserve negative and null results.
- Never leak hidden evaluation cases into memory construction, prompts, implementation, or tuning.
- Do not modify benchmark conditions merely to improve MNEXA's score.
- Record exact model/configuration/dataset/commit provenance for experiments.

Use `.claude/skills/experiment/SKILL.md` for benchmark or experimental work.

## Implementation law

- Work from one approved plan task at a time.
- Use tests before implementation for behavior changes.
- Implement the smallest change that satisfies the current task.
- Do not build future roadmap phases early.
- Do not add speculative infrastructure without evidence or an accepted decision.
- Preserve backward traceability from code to spec/ADR where the change is durable.
- If implementation evidence contradicts a spec or ADR, stop, record the evidence, and revise the decision/spec before continuing.

## Completion law

Before declaring a task complete:

1. Run the task's required verification.
2. Record the exact result, including failures.
3. Update `docs/state/CURRENT.md` when project state changed.
4. Capture any newly discovered D2/D3 decisions.
5. Update relevant experiment records when evidence was produced.
6. Reference relevant ADR/spec/plan identifiers in the commit message when applicable.

Before ending a substantial session, use the `/handoff` workflow.

## Core principle

> Claude may write code autonomously inside an approved decision space. Claude may not silently expand or redefine that decision space.
