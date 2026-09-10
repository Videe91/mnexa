---
id: ADR-0009
status: proposed
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/05-recall-attention-machine-intuition.md
spec_refs: []
supersedes: []
---

# ADR-0009 — Episode Construction and Boundary Authority

**Tier: D3 (epistemic semantics).** Requires explicit owner approval.

Covers register entry **D-03**.

## Decision question

How does MNEXA decide which historical experiences constitute an episode, and who has authority to establish
or revise that boundary?

## Context

ADR-0007 fixed the plane: an Episode is an Interpretation of kind `episode`, interpretive regardless of what
constructs it. What remains is construction and authority.

Three accepted decisions already constrain the answer more than they might appear to:

- **ADR-0002 rules 8–10** — a model never writes; a trusted runtime appends a record that the model produced
  something, and the payload is attributed content asserting production, not truth.
- **ADR-0005 rule 6** — a version's derivation edge set is inside its content identity. For an Episode,
  *membership is the derivation edge set*, so membership immutability per version is already settled.
- **ADR-0004 rule 9** — memory is frozen during an evaluation epoch, so no episode may form during one.

The remaining freedom is narrower than the question suggests, and most of this ADR is working out what
follows rather than choosing freely.

### Independence check

D-03 can be decided without D-05 **only if v0 anchors are identifier-based**. A time-gap heuristic —
"a pause longer than N minutes starts a new episode" — would depend on the occurred-at versus recorded-at
question that D-05 owns, and D-03 would become undecidable independently. Restricting v0 anchors to
identifiers observed in the record payload keeps the two separable. This is a reason to prefer identifier
anchors beyond their simplicity, and it is recorded as a constraint rather than a preference.

D-03 also touches D-07 (consolidation authority) without settling it. This ADR decides authority for
*episode boundaries specifically*, by applying ADR-0002's already-accepted authorship/authority split. D-07's
general question — what consolidation may establish across all output kinds — remains open.

## Options considered

### A — Deterministic construction only

Boundaries derive entirely from structural signals in the records: run identifier, session identifier, trace
root, task identifier.

Benefits: fully reproducible, which serves D-10 and reduces experimental noise; costs no consolidation
compute; trivially auditable; no attributed-content machinery.

Costs: the Episode becomes the session. Vision 3.8's worked example — deployment, error increase, saturation,
alert, rollback, recovery becoming *"production incident caused by deployment X"* — is meaningful because of
what occurred, not because a session ended. Purely deterministic episodes are log grouping, and if MNEXA's
Episode is exactly the transcript boundary then a retrieval baseline can reproduce it, weakening the C > B
claim that ADR-0003 rule 9 requires for any architectural advantage.

### B — Model-proposed construction only

A model reads records and segments them by meaning.

Benefits: captures 3.8's cognitive episode directly; strongest compression.

Costs: nondeterministic, so the same corpus yields different episodes across runs, adding variance to exactly
the comparison the experiment depends on. Consumes consolidation compute per segmentation. And it cannot
stand alone constitutionally: under ADR-0002 a model's segmentation is attributed content — a proposal — so
something else must establish the Episode regardless. Option B is not actually a complete answer.

### C — Hybrid: deterministic anchors and constraints, model-proposed interpretation, runtime-validated

A deterministic **anchor** derived from identifier evidence defines the envelope and fixes Episode object
identity. Within that envelope, boundaries may be deterministic or model-proposed. The trusted runtime
establishes the Episode version, validating constraints and recording provenance for how the boundary was
decided.

Benefits: keeps identity and constraints reproducible while allowing meaning to enter; makes the
proposal/establishment split explicit rather than implicit; degrades gracefully — with no model available,
C reduces to A and still works.

Costs: two mechanisms to describe; the anchor concept is new vocabulary.

## Decision

**Recommendation: Option C.** *(Proposed. Not approved.)*

Eleven rules.

### Identity and anchors

1. **Every Episode is bound to exactly one anchor.** An anchor is a deterministic envelope derived from
   identifier evidence present in ExperienceRecord payloads — run, session, trace root, task or transaction
   identifier. The anchor fixes **Episode object identity**: the same anchor always denotes the same Episode
   object, so a later reinterpretation produces a *new version* of that object rather than a competing one.

2. **v0 anchors are identifier-based, never time-based.** Time-gap heuristics are excluded from v0 because
   they would make this decision depend on D-05. This is a scope constraint, not a claim that time-based
   anchoring is wrong.

3. **The anchor is evidence, not the Episode.** An externally supplied `session_id` is historical payload
   (ADR-0007). The Episode is MNEXA's interpretive grouping over records carrying it. They are different
   objects, and the presence of the identifier does not make the grouping historical.

### Membership

4. **Membership references exact ExperienceRecord identities.** Required by ADR-0002 I-9a — grounding
   traverses to historical records — and ADR-0005 L-3. Records are immutable, so no version-pinning question
   arises.

5. **Membership and order are immutable within a version.** This is not a new rule: membership *is* the
   version's derivation edge set, already covered by its content identity under ADR-0005 rule 6 and L-9.

6. **Extension creates a new version.** An Episode extended by later records produces a new version whose
   membership is the prior membership plus the additions. The prior version is unchanged and remains
   retrievable (ADR-0002 rule 4, ADR-0005 L-4). Nothing rewrites an earlier version.

7. **No exclusivity constraint.** A single ExperienceRecord may belong to more than one Episode, and
   overlapping episodes are permitted. v0 uses a single anchor kind, so overlap is expected to be rare in
   practice — but forbidding it would add an invariant with no v0 purpose and would foreclose hierarchical
   episodes later.

### Authority

8. **A model may propose a boundary; it may never establish one.** A model's segmentation is recorded as a
   `ConsolidationProduced` record — attributed content asserting the production occurred (ADR-0002 rules
   8–10). The Episode version is then written by the trusted runtime, citing that record in its provenance.
   The runtime is always `committed_by`; the model is never a write principal.

9. **The boundary method is part of provenance.** Every Episode version records how its boundary was decided
   — deterministic, or model-proposed with the model identity and version — alongside the anchor evidence and
   the member records. This makes *why these records and not others* answerable, which is 3.20's evidence
   spine applied to grouping.

### Timing and revision

10. **Episodes form during consolidation only.** Not incrementally as events arrive. This avoids a new
    version per event, and it satisfies ADR-0004 rule 9, since consolidation never runs inside an evaluation
    epoch. There is no live episode-assembly path in v0.

11. **Reinterpretation produces a new version, never an edit.** A later consolidation that groups the same
    anchor's records differently creates a new Episode version. Prior versions remain retrievable, and
    ADR-0006 governs the consequences for anything derived from them: dependents become `DIRECT_STALE` and
    are queued for revalidation rather than invalidated.

### Explicitly deferred

**Split and merge are not in v0.** Anchor-bound identity (rule 1) means an Episode's extent is determined by
its anchor, so subdividing or combining episodes only arises when boundaries must cross or partition anchor
scopes — which no v0 contract requires. Were it needed, the shape is already implied: a split or merge would
produce new Episode objects deriving from the originals' versions, not new versions of them, since the
originals had valid independent extents. That is a distinct identity decision and is recorded as **D-25**
rather than settled here.

Also out of scope, per the v0 non-goals: hierarchical narrative memory, collective episodes, and any
causal or world-model structure over episodes.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| Q-1 | Every Episode version's membership resolves to existing ExperienceRecord identities | Resolve all member references; assert none dangling |
| Q-2 | Membership and order are immutable within a version | Recompute the version content hash including the ordered member set; assert it matches (ADR-0005 L-9) |
| Q-3 | Extension creates a new version and leaves the prior unchanged | Assert a new version identity exists and the prior version's hash is unchanged and still resolves |
| Q-4 | Every Episode object is bound to exactly one anchor, and one anchor maps to one Episode object | Assert a single anchor identity per object; assert the anchor→object mapping is injective |
| Q-5 | Anchor evidence resolves to historical records | Assert every anchor's supporting identifier reference resolves into the historical plane |
| Q-6 | Anchors are identifier-based, never time-derived | Assert every anchor's basis type ∈ the identifier-basis enum; assert no time-gap basis is admissible in v0 |
| Q-7 | A model never writes an Episode version | Assert `committed_by` is a trusted runtime (ADR-0002 I-2); assert every model-proposed boundary cites a `ConsolidationProduced` record |
| Q-8 | Boundary method and, where applicable, model identity are recorded in provenance | Assert every Episode version carries a non-null boundary-method field and, when model-proposed, a resolvable model identity |
| Q-9 | Episodes form only during consolidation, never inside an evaluation epoch | Assert no Episode version's commit falls between an epoch's open and close (ADR-0004 K-4) |
| Q-10 | All members of a version satisfy its anchor constraint | Assert every member record carries the anchor's identifier evidence |
| Q-11 | No exclusivity constraint is enforced | Assert a record may be admitted to a second Episode without rejection |

## Evidence and rationale

Option C is recommended, but the more useful observation is that **Option B was never a complete answer**.
Under ADR-0002 a model cannot establish anything, so "model-proposed construction" always requires a second
party to establish the result. Recognising that collapses the apparent three-way choice into a narrower one:
whether the establishing party has deterministic constraints to validate against. C says yes; B without
constraints says the runtime rubber-stamps whatever the model returned, which is establishment in name only.

Option A deserves its due: it is genuinely reproducible, costs nothing, and would be defensible if episodes
were only a storage convenience. It fails on the experiment rather than on principle. ADR-0003 rule 9
requires C > B before any claim of advantage over conventional retrieval, and if MNEXA's episodes are exactly
session boundaries, a retrieval baseline chunking by session has the same structure. Option A would leave the
architectural claim resting entirely on beliefs and recall, with episodes contributing nothing distinguishing.

The anchor is doing more work than it appears. Making it fix *object identity* rather than merely suggest a
boundary answers the revision question that would otherwise be genuinely hard: when a later consolidation
regroups the same records, is that a new Episode or a new version of the old one? Without a deterministic
identity rule that question has no principled answer, and consolidation would accumulate competing episodes
over the same records with no way to tell revision from duplication. With anchor-bound identity it is simply
a new version, and ADR-0006's staleness machinery handles the consequences for dependents without any
episode-specific mechanism.

Rule 7's permissiveness is deliberate asymmetry. Adding an exclusivity constraint later is cheap; removing
one is not, because data written under exclusivity never recorded the memberships it rejected. The same
asymmetry argued for the smaller object set in ADR-0007.

Rule 10 removes a problem rather than solving one. Live incremental assembly would produce a version per
event under rule 6's immutability, which is both expensive and meaningless — most intermediate versions would
never be read. Deferring formation to consolidation makes the version chain match the granularity at which
episodes are actually interpreted, and it inherits ADR-0004's epoch guarantee for free.

## Consequences

**Easier:** deciding whether a regrouping is a revision or a new episode; reproducing episode identity across
runs even when boundaries are model-proposed; auditing why particular records were grouped; degrading to
deterministic construction when no model is available.

**Harder:** anchors must be extractable from every experience source, so each adapter must supply identifier
evidence or its records cannot be episoded; consolidation carries the cost of segmentation; a corpus with no
usable identifiers has no anchors and therefore no episodes in v0.

**Newly required:** an anchor-basis registry with an identifier-only enum for v0; boundary-method and
model-identity fields on Episode versions; anchor→object identity mapping.

**Constrained:** D-07 inherits a worked instance of propose-versus-establish that its general rule should
remain consistent with. D-10 is helped — episode *identity* is deterministic even where boundaries are not,
so reproducibility failures localize to segmentation. D-13's activation records may reference Episode
versions as pinned interpretive versions under ADR-0002 rules 5–6.

**Newly uncovered decision — recorded, not decided here: D-25 — episode split and merge identity.** Deferred
from v0 as above; becomes live if any contract needs boundaries crossing or subdividing anchor scopes.

## Reversibility

High for anchor kinds and boundary method, low for the identity rule. Adding time-based or composite anchors
later is a registry change. Changing what fixes Episode object identity after episodes exist would require
re-deriving identity across the whole store, since existing objects would have been created under a different
mapping. The identity rule is therefore the part of this ADR most worth scrutinising before acceptance.

## Validation / falsification

Revisit if:

- available experience sources turn out not to carry usable identifiers, leaving anchors underdetermined and
  forcing time-based anchoring — which would make D-05 a prerequisite after all; or
- model-proposed boundaries prove so unstable across consolidations that Episode version churn dominates the
  store, suggesting v0 should reduce to Option A; or
- episodes are found never to be recalled independently of the beliefs derived from them, which would suggest
  the kind is carrying no weight at v0 scale.

Evidence that C > B holds with episodes disabled entirely would falsify the claim that episode construction
contributes to the architectural advantage, and would argue for removing the kind from v0 rather than
refining it.

## Outcome

Pending. No implementation exists.
