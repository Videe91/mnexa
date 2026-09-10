---
id: ADR-0002
status: proposed
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0002 — Experience/Interpretation Boundary and Historical Immutability in MNEXA v0

**Tier: D3 (constitutional). Requires explicit owner approval.**

## Decision question

Where exactly does the boundary between immutable history and evolving interpretation fall for concrete
MNEXA v0 objects, and what does "immutable" mechanically obligate?

## Context

The vision states the separation as constitutional but never operationalizes it:

- 3.48 law 1 — "History is immutable; interpretation is evolutionary."
- 10.7 — sorts all objects into append-only *historical* or evolvable *interpretive*, with no rule for
  assigning a given object to one side.
- 3.4 — "The original record cannot later be silently rewritten."
- 3.13 — reconsolidation: "The historical event remains immutable. But the interpretation may mature."
- 10.70 law 2 — repeats the law at constitutional level.

Every remaining v0 object definition depends on this. Whether an Episode, a confidence value, a causal
attribution, or a consolidation output is historical or interpretive determines whether it may be revised,
whether it needs an evidence spine, and whether a model is permitted to author it.

The decision is forced now because the v0 domain model cannot be written without it, and because getting it
wrong is expensive: a system that permits silent revision of history cannot later be made immutable
retroactively — the pre-existing records have already lost their guarantee.

The v0 thesis makes this load-bearing in a second way. Grand Proof 1 (10.41) requires showing that a frozen
model improved *because MNEXA preserved and transformed prior experience*. If history can be edited, an
apparent improvement can always be explained by history having been quietly reshaped to fit later outcomes.
Immutability is what makes the experimental claim auditable.

## Options considered

### Option A — Single mutable memory object

One object per remembered thing. New information updates it in place. Conventional memory-store and RAG
design.

Benefits: simplest to build; smallest storage; no reconciliation between planes; familiar.

Costs: directly violates 3.48 law 1 and 10.70 law 2. Destroys the ability to answer "what did we know at
the time" (2.6). Makes hindsight contamination structurally undetectable — the exact failure 2.6 and 6.20
exist to prevent. Forfeits the audit property that makes Grand Proof 1 defensible.

Failure mode: an improvement result that cannot be distinguished from history having been fitted to it.

Reversibility: very low. Records written under mutable semantics never regain the guarantee.

### Option B — Two planes with one-way dependency

A **Historical plane** (append-only, immutable after commit) and an **Interpretive plane** (versioned;
changed by supersession, never by mutation). Interpretive objects cite the historical records they derive
from. Historical objects may never reference interpretive objects.

Benefits: implements the constitutional law directly. Preserves "what did we know at the time" by
construction. Gives every interpretation an evidence spine (3.20). The one-way dependency rule is
mechanically checkable, so the invariant is testable rather than aspirational. Supports 3.13
reconsolidation without rewriting history. Leaves the promotion ladder (2.19) and belief branching (3.22)
expressible later without migration.

Costs: two object families instead of one; every interpretation carries citation overhead; corrections to
history become append-plus-supersede rather than an edit, which is less intuitive to operators.

Failure mode: boundary disputes for objects that feel like both (Episode is exactly this case — see
register T-1/D-03). This ADR fixes the *rule*; D-03 applies it to Episode.

Reversibility: high in the loosening direction (constraints can be relaxed later), low in the tightening
direction — which is the correct asymmetry for a constitutional choice.

### Option C — Full event-sourced bitemporal graph with derived projections

Everything is an event. All queryable state is a projection recomputed from the event log, with full
bitemporal indexing from the start.

Benefits: strongest possible integrity and replay; subsumes Option B; makes 6.4 and 10.6 native.

Costs: substantially more machinery than the v0 loop requires; projection rebuild and versioning become
core engineering work before the thesis has any evidence behind it. Conflicts with the standing rule
against speculative infrastructure and with the v0 non-goal "premature scalability architecture".

Reversibility: high — Option B is a strict subset, so C remains reachable without discarding data written
under B.

## Decision

**Recommendation: Option B.** *(Proposed. Not approved. Requires owner approval before it constrains the
specification.)*

Concretely, the proposal commits v0 to:

1. **Two planes.** Every v0 object is declared historical or interpretive. No object is both.
2. **Historical immutability.** A committed historical record is never updated or deleted in normal
   operation. Its content is fixed at commit.
3. **Correction by append.** A mistaken historical record is corrected by appending a new record that
   supersedes it. The original stays readable, and the supersession is itself historical.
4. **Interpretation by supersession.** An interpretive object changes by producing a new version that
   supersedes the prior version. Prior versions remain retrievable.
5. **One-way dependency.** Interpretive objects cite historical records. Historical records never cite
   interpretive objects. This is what structurally prevents interpretation from contaminating history.
6. **Atomic unit.** The immutable unit is the Experience Record as accepted at capture. Sub-fields are not
   independently mutable.
7. **Model outputs are interpretive by default.** Anything a model authored is interpretive unless it is a
   record *of the fact that the model produced it*, which is historical.

Point 7 is the practically important one: it means no model can write to the historical plane, only into
it as a recorded event. This is the v0-shaped version of "no model has unilateral authority over truth"
(3.48 law 9) and is what D-07 will build on.

## Evidence and rationale

The vision does not leave this genuinely open — Option A is foreclosed by two separately stated
constitutional laws. The real choice is between B and C, and that choice is about *scope*, not principle.

Option C is chosen against on the standing implementation rules rather than on merit: it is strictly more
capable, and it remains reachable later precisely because B's guarantees are a subset of C's. Building C
now would mean building replay and projection infrastructure before there is any evidence that the thesis
holds — which is the failure the v0 non-goals name explicitly.

Point 5 (one-way dependency) is the part of this proposal that is not merely restating the vision. The
vision asserts the two planes but never forbids the back-reference. Without that prohibition the planes
leak: a historical record citing an interpretation makes the historical record's meaning change whenever
the interpretation is superseded, which silently reintroduces mutable history through the back door.

### Invariants this yields, and how each is checked

| Invariant | How checked |
|---|---|
| No historical record is modified after commit | Content hash recorded at commit; recompute and compare on read |
| No historical record references an interpretive object | Static check on the reference graph; assert zero edges historical→interpretive |
| Every interpretive object cites ≥1 historical record | Schema constraint plus graph check for orphaned interpretations |
| Superseded versions remain retrievable | Fetch-by-version test across a supersession chain |
| Corrections append rather than edit | Deletion/update path absent from the historical write port; asserted by interface test |

These are stated here rather than in the spec because the standing rules treat an invariant without a
stated check as not an invariant.

## Consequences

**Easier:** reconstructing what was known at any past time; auditing why a belief exists; defending an
experimental result against the "history was fitted to the outcome" objection; adding the promotion ladder
and belief branching later.

**Harder:** operator correction of bad data (append-and-supersede, not edit); storage grows monotonically
in v0 since nothing is deleted; any consolidation output needs an explicit citation set.

**Newly required:** every v0 object must be classified into a plane as part of the domain model; the
historical write port must not expose update or delete; D-03 must resolve Episode's plane before the
domain model can be completed.

**Constrained:** D-02, D-03, D-04, D-05, D-06, D-07 and D-13 all inherit from this. If this ADR is
rejected or amended, those decisions change with it.

## Reversibility

Asymmetric by design. Loosening later is cheap. Tightening later is not: any record written under weaker
semantics permanently lacks the guarantee, because the evidence that it was never altered does not exist
retroactively. This asymmetry is the reason the decision is surfaced before the specification rather than
during implementation.

Migration to Option C remains available without data loss, since B's historical plane is a valid event log.

## Validation / falsification

Revisit if v0 implementation shows that:

- append-and-supersede correction is so operationally painful that operators route around it, which would
  indicate the granularity in point 6 is wrong; or
- the one-way dependency rule (point 5) blocks a legitimate v0 need that has no alternative expression; or
- storage growth without decay becomes a real constraint at v0 scale, which would pull D-19 forward.

Evidence that the two-plane split imposed cost without ever being *used* — no interpretation superseded, no
historical reconstruction performed across the whole v0 cycle — would argue the separation is premature at
this scale and should be revisited.

## Outcome

Pending. No implementation exists.
