---
name: handoff
description: Use before ending a substantial MNEXA development session or when context is about to reset, so the next agent/session can resume from repository state rather than chat memory.
---

# Handoff

Leave the repository self-explanatory for the next session.

## Workflow

1. Inspect repository status, current branch, recent commits, and the active plan/spec.
2. Run the verification required for the last completed task or record why it could not run.
3. Update `docs/state/CURRENT.md` with:
   - current phase and milestone
   - current branch
   - active spec and plan
   - last completed task/commit
   - exact verification and result
   - open D2/D3 decisions
   - known blockers or anomalies
   - experiments in progress/results not yet interpreted
   - the single next approved action
4. Ensure new durable decisions are recorded as ADRs rather than only in chat.
5. Ensure experiment evidence is recorded under `docs/experiments/`.
6. Commit the handoff/state change when it materially changes repository state.
7. Report only what is verified as complete. Do not infer completion from partially written files.

## Goal

A fresh Claude Code session should be able to read `CLAUDE.md` and `docs/state/CURRENT.md`, inspect referenced artifacts, and continue without needing the previous chat transcript.
