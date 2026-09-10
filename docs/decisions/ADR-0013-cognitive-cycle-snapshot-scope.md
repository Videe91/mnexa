---
id: ADR-0013
status: proposed
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0013 — Cognitive-Cycle Knowledge Snapshot Scope

**Tier: D3 (constitutional).** Requires explicit owner approval.

Covers register entry **D-28**.

## Decision question

Must one cognitive decision cycle operate against a single stable knowledge watermark, or may separate recall
operations within the same cycle observe different watermarks?

## Context

ADR-0011 rules 3a–3b fixed the snapshot for a **single recall**: the watermark binds before retrieval and does
not move. It left the cycle-level question open.

### Does this genuinely block D-13?

**Yes — and the reason is specific rather than general.** Tested rather than assumed:

D-13's data model does *not* depend on this. An activation record can cite the recall that produced it, and
therefore that recall's watermark, whatever policy governs cycles. Per-recall, everything ADR-0011 established
remains well-defined, including S-18's eligible-but-not-returned computation.

What breaks is D-13's **central deliverable**. Retrieval regret asks *was a useful memory eligible but not
returned* — and at the decision level, "eligible" needs one eligible set. With two recalls at `N₁ = 500` and
`N₂ = 503`, a memory committed at `#502` was ineligible to the first and eligible to the second. Computing
decision-level regret against a single decision watermark then produces **false positives**: items flagged as
"available but not retrieved" that no constituent recall could legitimately have found. Distinguishing
retrieval failure from attention failure — the boundary ADR-0011 rule 18 handed to D-13 — becomes unreliable
in exactly the cases that matter.

There is also an unresolved inconsistency upstream. **ADR-0010 rule 12 already requires a decision to carry
*a* watermark**, singular. If constituent recalls use different ones, that watermark is either the earliest
(and later recalls saw beyond the decision's declared eligible set), the latest (and earlier recalls could not
see everything the decision claims was available), or undefined (contradicting rule 12). Rule 12 is currently
under-determined, and D-28 is where that is resolved.

D-13 could be written around the hole — per-recall regret, decision-level regret marked conditional — but that
is specifying around an unmade decision, which is the failure this process exists to prevent.

### What v0 actually needs

Two observations narrow the choice before the options are compared.

**Inside an evaluation epoch the question cannot arise.** ADR-0004 rule 9 freezes memory for the epoch's
duration, so no commits occur and every policy yields identical behaviour. Whatever is chosen therefore costs
nothing in the measured condition.

**A v0 decision cycle does not need to observe its own in-flight commits.** The v0 loop places action and
outcome *after* the decision; they enter as experience for the next cycle. A multi-step agent's within-task
observations live in working context (vision's L0), not in consolidated MNEXA memory — MNEXA recall serves
*prior* experience. Nothing in the v0 loop requires a recall to see something committed after its own cycle
began.

## Options considered

### A — Single cycle snapshot

One watermark binds at cycle start; every recall in the cycle uses it.

Benefits: the decision's eligible set is unambiguous by construction, resolving ADR-0010 rule 12 rather than
working around it. Decision-level regret has no watermark-mismatch false positives. Replay of a whole cycle is
one `AS_OF(N)` reconstruction. Simplest thing to state and to check.

Costs: a cycle that genuinely needs newer state cannot get it without ending. Long-running cycles observe
increasingly stale memory.

### B — Per-recall watermarks, unconstrained

Each recall binds the then-current watermark.

Benefits: always freshest; no cycle concept needed; simplest to implement.

Costs: leaves ADR-0010 rule 12 undefined. Decision-level eligibility is not a set but a family of sets, and
every decision-level regret computation inherits the false-positive problem above. Cycle replay requires
reconstructing several views and reasoning about their differences.

### C — Per-recall watermarks plus a declared decision-watermark rule

As B, but the decision's watermark is defined by an explicit rule — `max` or `min` over constituent recalls —
with per-recall watermarks also recorded.

Benefits: rule 12 gets a definition; freshness preserved.

Costs: the definition is arbitrary in a way that shows. Under `max`, items eligible at the decision watermark
were not eligible to earlier recalls, so regret must consult per-recall watermarks anyway and the decision
watermark buys nothing. Under `min`, later recalls demonstrably saw beyond it, so the decision record asserts
an eligible set that is knowably incomplete. Either way the decision-level number needs a caveat attached
permanently.

### D — Single snapshot with explicit recorded re-anchoring

As A, but a cycle may re-anchor to a newer watermark, recorded as a historical event, splitting the cycle into
segments.

Benefits: A's clarity plus an escape hatch for long-running cognition.

Costs: a re-anchored cycle is two cycles with extra vocabulary. Every consumer must then reason about segments,
and the decision-level eligible set becomes per-segment — reintroducing C's ambiguity behind a new name.

## Decision

**Recommendation: A — one knowledge watermark per cognitive cycle.** *(Proposed. Not approved.)*

Seven rules.

1. **One watermark per cycle.** A cognitive cycle binds a single knowledge watermark N before its first recall,
   and every recall within that cycle binds the same N (ADR-0011 rule 3a applies unchanged to each).

2. **The cycle is delimited by its watermark and its decision.** A cognitive cycle spans from binding N to
   committing the decision record for that cycle. *This defines the cycle in terms of its watermark only; what
   a decision record contains and how it links remains D-12's.*

3. **The decision's watermark is the cycle watermark.** This resolves ADR-0010 rule 12's under-determination:
   the decision carries exactly one watermark, and it is N.

4. **The decision-level eligible set is `AS_OF(N)`, without qualification.** Every constituent recall drew from
   the same view, so *available to this decision* is a single well-defined set and decision-level retrieval
   regret needs no per-recall caveat.

5. **Needing newer state means a new cycle.** A cycle that must observe state committed after N terminates;
   a new cycle begins with a new watermark. There is no re-anchoring within a cycle. A decision made after
   observing new state *is* a different decision, and requiring a new cycle makes that explicit rather than
   implicit.

6. **Within-cycle observations are not required to be recallable within that cycle.** Records captured during a
   cycle commit normally and become eligible to *later* cycles. Working context (L0) carries what the cycle
   itself has just observed; MNEXA recall serves prior experience.

7. **Every `RecallPerformed` in a cycle records the cycle's watermark.** ADR-0011 rule 3b's distinction stands
   unchanged: each record's own `commit_sequence` differs from N and from the other records' sequences, and is
   never mistaken for the watermark.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| U-1 | Every recall in a cycle carries the cycle's watermark | Assert all `RecallPerformed` records for one cycle report the same N |
| U-2 | The decision's watermark equals the cycle watermark | Assert the decision record's watermark matches N (satisfies ADR-0010 rule 12) |
| U-3 | No recall in a cycle observes state committed after N | Commit records mid-cycle in a fixture; assert no later recall in that cycle returns or reads them (extends ADR-0011 S-23 to cycle scope) |
| U-4 | The decision-level eligible set is a single `AS_OF(N)` set | Assert eligibility for a decision resolves to exactly one watermark with no per-recall qualification |
| U-5 | No re-anchoring occurs within a cycle | Assert no operation changes a cycle's watermark after binding; assert observing newer state requires a new cycle identity |
| U-6 | Within-cycle captures commit normally and become eligible to later cycles | Assert a record captured during a cycle is absent from that cycle's recalls and present in a subsequent cycle's `AS_OF` view |
| U-7 | Behaviour inside an evaluation epoch is identical under any snapshot policy | Assert no divergence across an epoch, where ADR-0004 rule 9 freezes memory |
| U-8 | Decision-level retrieval regret produces no watermark-mismatch false positives | Fixture with several recalls in one cycle; assert every item flagged eligible-but-not-returned was eligible to every recall |

## Evidence and rationale

**Option A is chosen for unambiguity, and the cost that would normally argue against it does not apply in v0.**
The obvious objection — a long cycle sees increasingly stale memory — presupposes that cycles run long enough
for meaningful commits to accumulate, and that the cycle needs those commits from *memory* rather than from
working context. Neither holds in the v0 loop: action and outcome follow the decision, and within-task
observations are in context, not yet consolidated. Rule 6 states that explicitly so the assumption is visible
and falsifiable rather than buried.

**Option C is the one worth arguing against carefully**, because it looks like a compromise and is not. Its
decision watermark is definitionally arbitrary, and both definitions fail in the same place: under `max`, regret
must still consult per-recall watermarks to avoid false positives, so the decision watermark carries no
information; under `min`, the decision record asserts an eligible set that later recalls provably exceeded.
A number that must be accompanied by a caveat every time it is used is not a resolution of rule 12's ambiguity
— it is the ambiguity written down.

**Option D fails for a reason worth naming.** An escape hatch that splits a cycle into segments has not avoided
multiple watermarks; it has renamed them. Every downstream consumer would then reason about segment-level
eligibility, which is C's problem with additional vocabulary. If a cycle needs newer state, rule 5's answer —
that this is a new cycle — is both simpler and more honest about what changed.

**Rule 5 is the substantive commitment**, and it is a claim about what a decision *is*: cognition that has
observed new state is making a different decision than cognition that has not. Forcing that to appear as a new
cycle keeps the record's structure aligned with the epistemic situation, and it is what makes rule 4's
unqualified eligible set true rather than approximately true.

**On the interaction with ADR-0004.** That every policy behaves identically inside an evaluation epoch (U-7) is
worth stating because it means this decision cannot influence measured results — it cannot be a source of
advantage for condition C, and it cannot be tuned to produce one. Its entire effect is on the interpretability
of the record outside epochs, which is where it is needed.

## Consequences

**Easier:** answering *what was available to this decision* with one set; computing decision-level retrieval
regret without caveats; replaying a whole cycle as one `AS_OF(N)` reconstruction; satisfying ADR-0010 rule 12
exactly rather than approximately.

**Harder:** the runtime must carry a cycle identity and its watermark across multiple recalls rather than
resolving current state per call; long-running cognition must be structured as multiple cycles; a cycle cannot
consult memory for something it has just captured.

**Newly required:** a cycle identity bound to a watermark; cycle-scoped watermark propagation to every recall;
cycle boundaries observable enough to check U-1 and U-5.

**Constrained or unblocked:**

- **D-13 (activation trace) — unblocked.** Decision-level eligibility is now a single set, so the
  retrieval-failure versus attention-failure boundary is computable without per-recall qualification. D-13 may
  now be drafted.
- **D-12 (decision/prediction/outcome linkage)** — gains rule 3: the decision's watermark is the cycle's. D-12
  still owns the decision record's contents and its links; rule 2 defines the cycle only in terms of its
  watermark and does not settle that.
- **ADR-0010 rule 12** — its under-determination is resolved, not overridden. The rule required one watermark
  per decision; this supplies which one it is.
- **ADR-0011** — rules 3a–3b stand unchanged; U-3 extends S-23's guarantee from one recall to a cycle.

**No new durable decision uncovered.**

## Reversibility

Moderate. Moving from A to B or C later is a policy change, but every cycle recorded under A carries one
watermark and would remain interpretable, so no migration is needed. Moving *to* A from B would be harder:
existing decisions would have no single eligible set, and none could be reconstructed after the fact. The
asymmetry favours A now.

## Validation / falsification

Revisit if:

- v0 cognition turns out to require consulting memory for within-cycle captures — which would falsify rule 6's
  assumption and argue for D's re-anchoring despite its cost; or
- cycles run long enough that staleness measurably degrades decisions, which would be visible as later recalls
  in a cycle underperforming earlier ones; or
- the cycle boundary proves hard to delimit for agents whose control flow does not decompose into
  decision-shaped units, indicating rule 2's definition is too tied to a single-decision loop.

Evidence that decision-level regret was computed correctly under per-recall watermarks, at v0 scale and without
caveats, would falsify the claim that a single snapshot is necessary rather than merely convenient.

## Outcome

Pending. No implementation exists.
