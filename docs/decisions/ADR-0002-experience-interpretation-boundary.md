---
id: ADR-0002
status: proposed
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/09-trust-identity-privacy-epistemic-immune-system.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0002 — Experience/Interpretation Boundary and Historical Immutability in MNEXA v0

**Tier: D3 (constitutional). Requires explicit owner approval.**

**Amendment history:** revised 2026-09-10 on owner direction, before acceptance, in two respects: the
treatment of model-authored content in the historical plane (§Decision 8–10), and the replacement of a
blanket prohibition on historical→interpretive references with a version-pinning rule (§Decision 5–6).
Rationale for both changes is recorded under *Evidence and rationale*. No accepted decision was rewritten;
this ADR has not yet been accepted.

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

Two further vision constraints bound the answer and were underweighted in the first draft:

- 5.40 (cognitive provenance) requires recording *which knowledge was actually active* when a decision was
  made — "Active knowledge: P7-v2, E91, Skill S18. Not activated: P19." Note that the vision's own example
  is already version-qualified (`P7-v2`). Recording this is historical fact about cognition, and it
  necessarily points at interpretive artifacts.
- 9.11 and 9.39 require that content never becomes authority merely by being in memory, and that historical
  behaviour is evidence rather than policy.

The decision is forced now because the v0 domain model cannot be written without it, and because getting it
wrong is expensive: a system that permits silent revision of history cannot be made immutable
retroactively — the pre-existing records have already lost the guarantee.

The v0 thesis makes this load-bearing a second way. Grand Proof 1 (10.41) requires showing a frozen model
improved *because MNEXA preserved and transformed prior experience*. If history can be edited, an apparent
improvement can always be explained by history having been quietly reshaped to fit later outcomes.
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

### Option B — Two planes with referential stability

A **Historical plane** (append-only, immutable after commit) and an **Interpretive plane** (versioned;
changed by supersession, never by mutation). Interpretive artifacts cite the historical records they derive
from. Historical records may cite interpretive artifacts *only by immutable version identity*, and only to
record use or activation — never to assert that the interpretation is true.

Benefits: implements the constitutional law directly. Preserves "what did we know at the time" by
construction. Gives every interpretation an evidence spine (3.20). Preserves cognitive provenance (5.40)
rather than sacrificing it. The pinning rule is mechanically checkable, so the invariant is testable rather
than aspirational. Supports 3.13 reconsolidation without rewriting history. Leaves the promotion ladder
(2.19) and belief branching (3.22) expressible later without migration.

Costs: two object families instead of one; every interpretation carries citation overhead; corrections to
history become append-plus-supersede rather than an edit; version retention obligations grow because any
interpretive version ever referenced by history must be kept.

Failure mode: boundary disputes for objects that feel like both (Episode is exactly this case — see
register T-1/D-03). This ADR fixes the *rule*; D-03 applies it to Episode.

Reversibility: high in the loosening direction, low in the tightening direction — the correct asymmetry for
a constitutional choice.

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

Concretely, the proposal commits v0 to ten rules.

### Plane structure

1. **Two planes.** Every v0 object is declared historical or interpretive. No object is both.
2. **Historical immutability.** A committed historical record is never updated or deleted in normal
   operation. Its content is fixed at commit and bound by a content hash.
3. **Correction by append.** A mistaken historical record is corrected by appending a new record that
   supersedes it. The original stays readable, and the supersession is itself historical.
4. **Interpretive versioning.** An interpretive object is a chain of immutable **versions** plus a mutable
   **head** pointer. Supersession appends a new version and moves the head. A version, once created, is
   never mutated. Prior versions remain retrievable.

### Referential stability (amended)

5. **Version-pinned provenance references.** A historical record MAY reference an interpretive artifact,
   but only by immutable version identity (version ID or content identity). A historical record may never
   reference mutable interpretive state — not an object head, not a "current version" pointer, not any
   reference that resolves differently at different times.
6. **Reference semantics are usage, not endorsement.** An edge from the historical plane to an interpretive
   version may only carry a usage or activation meaning — *was active at*, *was used by*, *was surfaced
   for*. It may never carry a truth-assertion meaning. The historical fact recorded is "this exact version
   was active or used at that time", never "the interpretation this version represents was correct".
7. **Atomic unit.** The immutable unit is the Experience Record as accepted at capture. Sub-fields are not
   independently mutable.

### Authorship versus authority (amended)

8. **Write authority is separate from content authorship.** Every historical record carries a
   `committed_by` naming the trusted MNEXA runtime or adapter that appended it, and this is never a model
   identity. A model is never a write principal. A trusted runtime MAY append an immutable historical
   record stating that a particular model or agent produced an output, decision, prediction or action.
9. **Model-authored content is attributed content.** Model-generated payloads enter the historical plane
   only inside an attribution envelope carrying the authoring model's identity, version, and the parameters
   needed to reproduce the production event. The record's assertion scope is *that the production
   occurred*. It is not an assertion that the payload's claims are true.
10. **Grounding is a separate, interpretive act.** Any claim that content inside an attributed payload is
    *true* is an interpretive object that cites the historical record. It is never inferred from the
    payload's presence in the ledger.

Rules 8–10 give the precise reading of "models cannot write history": models may not **establish** historical
truth, but their productions are **recordable** as historical fact. `Model X produced decision D at time T`
is historical. `Claim C inside D is true` is interpretive unless independently grounded.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| I-1 | No historical record is modified after commit | Content hash recorded at commit; recompute on read and assert equal |
| I-2 | `committed_by` on every historical record is a registered trusted runtime/adapter, never a model | Schema constraint; assert `committed_by` ∉ model registry |
| I-3 | Model-authored payloads appear only inside an attribution envelope carrying model identity and version | Type check: payload with `authored_by` set ⇒ envelope type is `AttributedContent` and provenance fields non-empty |
| I-4 | No attributed payload is consumed as grounded fact | Assert no truth-assertion edge originates at an `AttributedContent` node; every grounded claim resolves to an interpretive object citing the record |
| I-5 | Every historical→interpretive reference is version-pinned | Assert each such reference carries a version ID or content hash; assert zero bare object-ID references from the historical plane |
| I-6 | Interpretive versions referenced by history are immutable and retained | Recompute version content hash; assert every referenced version resolves for as long as the referencing record exists |
| I-7 | Supersession never mutates a prior version | Capture prior-version hash before and after a supersede operation; assert unchanged |
| I-8 | History→interpretation edges carry only usage/activation types | Edge-type allowlist check |
| I-9 | Every interpretive object cites ≥1 historical record | Schema constraint plus graph check for orphaned interpretations |
| I-10 | Superseded versions remain retrievable | Fetch-by-version across a supersession chain |
| I-11 | The historical write port exposes no update or delete | Interface test asserting absence of those operations |

These are stated here rather than deferred to the spec because the standing rules treat an invariant
without a stated check as not an invariant.

## Evidence and rationale

The vision does not leave the plane split genuinely open — Option A is foreclosed by two separately stated
constitutional laws. The real choice is between B and C, and that choice is about *scope*, not principle.
Option C is chosen against on the standing implementation rules rather than on merit: it is strictly more
capable and remains reachable later precisely because B's guarantees are a subset of C's. Building C now
would mean building replay and projection infrastructure before any evidence exists that the thesis holds.

### Why the blanket prohibition was wrong

The first draft of this ADR forbade all historical→interpretive references. That rule was aimed at a real
property but misidentified it. The property required is **referential stability**: a historical record's
meaning must not change over time. A blanket ban achieves this, but only by also destroying cognitive
provenance (5.40) — under it, MNEXA could not record that Decision D was made while Belief B4 v7 was active,
which is precisely the record 5.40 requires and precisely the record needed to later distinguish "the
decision was wrong because the knowledge was wrong" from "because the right knowledge was not recalled".

Version-pinning achieves referential stability directly and at lower cost. A pinned version is immutable, so
a record citing it means the same thing forever; supersession moves a head the historical record never
looked at. The precise rule is therefore about **the mutability of the referent**, not about crossing planes.
The failure mode the ban was guarding against — a historical record whose meaning silently shifts when an
interpretation is revised — is caused specifically by *floating* references, and I-5 prohibits exactly those.

Rule 6 closes the remaining gap. Version-pinning alone would still permit a historical record that asserts
an interpretation is *correct*, which would freeze a belief into the immutable plane and put it beyond
revision — reintroducing the contamination through semantics rather than through mutability. Restricting the
edge meaning to usage keeps the interpretive plane fully revisable while the record of what was used stays
fixed.

### Why attributed content belongs in the historical plane

The first draft treated model outputs as interpretive by default. That is right about *claims* and wrong
about *events*. That a model produced a given output at a given time is an observable fact about the world,
in the same category as any other observation the ledger records — and it is a fact MNEXA must retain, since
3.43 requires model provenance precisely so MNEXA can later discover that "Model version X systematically
produced poor causal hypotheses in domain Y". That discovery is impossible if productions were never
recorded as events.

The distinction that carries the constitutional weight is between **write authority** and **content
authorship** (rule 8). The vision's law is that no model has unilateral authority over truth (3.48 law 9) and
that content must not become authority by accident (9.11). Neither is violated by recording what a model
produced, so long as the record asserts production rather than truth, and so long as no code path treats an
attributed payload as grounded. I-3 and I-4 are what make that enforceable rather than a matter of
convention; without I-4 in particular, "attributed content" is only a label, and consolidation could quietly
read attributed claims as facts.

This also pre-shapes D-07 (consolidation authority) usefully: a consolidation model's output is an
attributed production recorded historically, and the *proposal* it represents is interpretive. Author and
judge stay separate (10.21) without needing a second agent in v0.

## Consequences

**Easier:** reconstructing what was known at any past time; auditing why a belief exists; recording cognitive
provenance for later attribution work (D-13); measuring model reliability over time (3.43); defending an
experimental result against the "history was fitted to the outcome" objection; adding the promotion ladder
and belief branching later.

**Harder:** operator correction of bad data (append-and-supersede, not edit); storage grows monotonically in
v0 since nothing is deleted; any consolidation output needs an explicit citation set; interpretive versions
can no longer be garbage-collected freely once history references them.

**Newly required:** every v0 object must be classified into a plane as part of the domain model; the
historical write port must not expose update or delete; the interpretive store must support stable
version identity and retention; D-03 must resolve Episode's plane before the domain model can be completed.

**Constrained:** D-02, D-03, D-04, D-05, D-06, D-07 and D-13 all inherit from this. Rules 8–10 partially
settle the model-provenance portion of D-06 and pre-shape D-07. If this ADR is amended further or rejected,
those decisions change with it.

**Interaction with deferred forgetting (D-19):** I-6's retention obligation means a referenced interpretive
version cannot simply be dropped. When forgetting arrives, it must reckon with this. That is a known,
accepted cost of preserving provenance, and it is the same tension the vision records at 9.48 (derived
forgetting).

## Reversibility

Asymmetric by design. Loosening later is cheap. Tightening later is not: any record written under weaker
semantics permanently lacks the guarantee, because the evidence that it was never altered does not exist
retroactively. This asymmetry is why the decision is surfaced before the specification rather than during
implementation.

Migration to Option C remains available without data loss, since B's historical plane is a valid event log.

## Validation / falsification

Revisit if v0 implementation shows that:

- append-and-supersede correction is so operationally painful that operators route around it, indicating the
  granularity in rule 7 is wrong; or
- the version-pinning rule (I-5) blocks a legitimate v0 need that has no alternative expression; or
- the retention obligation (I-6) causes unbounded growth at v0 scale, which would pull D-19 forward; or
- the attribution envelope (rule 9) proves impossible to enforce at a boundary where model and non-model
  content are interleaved in a single payload.

Evidence that the two-plane split imposed cost without ever being *used* — no interpretation superseded, no
historical reconstruction performed, no cognitive-provenance query run across the whole v0 cycle — would
argue the separation is premature at this scale and should be revisited.

## Outcome

Pending. No implementation exists.
