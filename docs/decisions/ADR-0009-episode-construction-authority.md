---
id: ADR-0009
status: accepted
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

**Approval:** accepted by owner 2026-09-10, following three owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **Option A's rejection was re-argued on architectural grounds.** The original rationale rejected
   deterministic session-boundary episodes partly because a retrieval baseline could obtain similar structure,
   making C > B harder to demonstrate. **That is not an admissible criterion** — it selects architecture to
   win a benchmark, which `.claude/rules/scientific-method.md` forbids. The rejection now rests on the
   semantic argument that external session boundaries are not cognitive episode boundaries. — *Options*,
   *Evidence and rationale*.
2. **External anchors no longer define Episode identity.** The original made the anchor fix Episode object
   identity, which forced one episode per external session and forbade an episode spanning sessions — the very
   conflation amendment 1 identifies. Episodes now receive their own stable opaque MNEXA identity. — rules
   1–3, Q-4, Q-12, Q-15.
3. **Deterministic validation establishes admissibility, not boundary truth.** The original left what
   validation proves underspecified. — rules 12–14, Q-13, Q-14.

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

Costs: **an externally defined session, call or transaction boundary is not a cognitive episode boundary.**
The two differ structurally, not merely in quality:

- One external session may contain **multiple** cognitive episodes — a single long session can cover an
  investigation, an unrelated question, and a deployment.
- One cognitive episode may span **multiple** external sessions — an incident diagnosed across a reconnect,
  a handoff, or two days.

Vision 3.8's worked example — deployment, error increase, saturation, alert, rollback, recovery becoming
*"production incident caused by deployment X"* — is one episode because of what occurred, and no session
boundary determines it. Option A therefore does not construct episodes; it renames sessions.

### B — Model-proposed construction only

A model reads records and segments them by meaning.

Benefits: captures 3.8's cognitive episode directly; strongest compression.

Costs: nondeterministic, so the same corpus yields different episodes across runs, adding variance to exactly
the comparison the experiment depends on. Consumes consolidation compute per segmentation. And it cannot
stand alone constitutionally: under ADR-0002 a model's segmentation is attributed content — a proposal — so
something else must establish the Episode regardless. Option B is not actually a complete answer.

### C — Hybrid: deterministic constraints, model-proposed interpretation, runtime-validated

Deterministic structural evidence constrains and helps generate candidates. Boundaries within those
constraints may be deterministic or model-proposed. The trusted runtime establishes the Episode version by
validating structural admissibility and recording provenance for how the boundary was decided. Episode
identity is MNEXA's own, independent of any external grouping key.

Benefits: allows cognitive meaning to enter while keeping every structural property checkable; makes the
proposal/establishment split explicit; degrades gracefully — with no model available, boundaries are
deterministic and the machinery is unchanged.

Costs: two mechanisms to describe; requires being precise about what validation does and does not prove.

## Decision

**Recommendation: Option C.** *(Proposed. Not approved.)*

Eleven rules.

### Episode identity

1. **An Episode has its own stable opaque MNEXA identity**, assigned when it is first established and stable
   across all its versions:

   ```text
   Episode E17
     v1  v2  v3        ← object identity E17 unchanged
   ```

2. **Identity is never derived from external grouping keys or from membership.** A source session ID, call
   ID, transaction ID or time-window key is *historical evidence* and may constrain or support a proposal,
   but **external grouping identity ≠ cognitive Episode identity**. Identity is also not derived from the
   membership set, which evolves across versions.

3. **Revision requires explicit lineage targeting.** A later consolidation proposal produces a **new version
   of an existing Episode** only when the proposal explicitly targets that Episode lineage as a revision and
   the normal authority and head-movement rules permit it. Otherwise it establishes a **separate Episode
   object**.

   This is what makes revision distinguishable from duplication without conflating identity with any external
   key.

### Structural evidence (constraints, not identity)

4. **What "anchor" means here.** An anchor is deterministic structural evidence drawn from identifier
   material in ExperienceRecord payloads — run, session, trace root, task or transaction identifier — used for
   **candidate generation** and for **validation**. It is never an identity. Because identity is opaque and
   assigned at establishment (rule 1), anchors cannot reintroduce the conflation rule 2 forbids.

5. **v0 anchors are identifier-based, never time-based.** Time-gap heuristics are excluded from v0 because
   they would make this decision depend on D-05. A scope constraint, not a claim that time-based anchoring is
   wrong.

6. **The permitted shapes follow.** Because anchors do not define identity, all of these are expressible:
   multiple Episodes inside one external session; one ExperienceRecord in multiple Episodes; overlapping
   Episodes; and — where evidence supports it — an Episode spanning multiple external sessions.

### Membership

7. **Membership references exact ExperienceRecord identities.** Required by ADR-0002 I-9a and ADR-0005 L-3.
   Records are immutable, so no version-pinning question arises.

8. **Membership and order are immutable within a version.** Not a new rule: membership *is* the version's
   derivation edge set, already covered by its content identity under ADR-0005 rule 6 and L-9.

9. **Extension creates a new version.** Prior versions are unchanged and remain retrievable.

10. **No exclusivity constraint.** Overlap and multi-membership are permitted.

### Authority

11. **A model may propose a boundary; it may never establish one.** A model's segmentation is recorded as a
    `ConsolidationProduced` record — attributed content asserting the production occurred (ADR-0002 rules
    8–10). The Episode version is written by the trusted runtime, which is always `committed_by`.

12. **Deterministic validation establishes structural admissibility only.** The validator may check that:

    - every ExperienceRecord reference exists;
    - every referenced record is committed;
    - provenance is legal under ADR-0002 and ADR-0005;
    - membership uses immutable record identities;
    - required access and ownership constraints hold;
    - the proposal's structure is valid;
    - any **declared** external anchors actually match the underlying historical payload.

    Passing these establishes that the proposal is **admissible**. It does **not** prove that these records
    objectively constitute the correct cognitive episode.

13. **What an established Episode means.** Episode membership remains an interpretive claim. An established
    Episode asserts:

    > *this is MNEXA's currently established, evidence-backed interpretation of an episode boundary*

    and never *this boundary is historical fact*. **A model gains no epistemic authority merely because its
    proposal passed structural validation.**

14. **Provenance is mandatory.** Every Episode version retains provenance to the exact ExperienceRecords it
    groups, the attributed proposal or consolidation production where applicable, and any structural anchor
    evidence the validator used.

### Timing and revision

15. **Episodes form during consolidation only.** Not incrementally as events arrive. This avoids a version
    per event under rule 8, and satisfies ADR-0004 rule 9 since consolidation never runs inside an evaluation
    epoch.

16. **Reinterpretation produces a new immutable version, never a rewrite.** ADR-0006 governs the consequences
    for dependents: they become `DIRECT_STALE` and are queued for revalidation rather than invalidated.

### Explicitly deferred

**Split and merge are not in v0.** With opaque identity and explicit lineage targeting (rules 1–3), a
consolidation that regroups records either targets an existing lineage — producing a new version — or
establishes a separate Episode. Neither is a split or a merge in the strict sense: no v0 contract requires
one Episode object to become two, or two to become one, with their prior lineages resolved. Were it needed,
the shape is implied: a split or merge would produce **new Episode objects deriving from the originals'
versions**, not new versions of them, because the originals had valid independent extents and ordinary
supersession would misrepresent that. That is a distinct identity decision, recorded as **D-25**.

Also out of scope, per the v0 non-goals: hierarchical narrative memory, collective episodes, and any
causal or world-model structure over episodes.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| Q-1 | Every Episode version's membership resolves to existing ExperienceRecord identities | Resolve all member references; assert none dangling |
| Q-2 | Membership and order are immutable within a version | Recompute the version content hash including the ordered member set; assert it matches (ADR-0005 L-9) |
| Q-3 | Extension creates a new version and leaves the prior unchanged | Assert a new version identity exists and the prior version's hash is unchanged and still resolves |
| Q-4 | Episode object identity is opaque, stable across versions, and derived from neither external keys nor membership | Assert identity is a MNEXA-issued opaque value; assert it is unchanged across a version chain; assert no external identifier or membership hash is used to compute it |
| Q-5 | Declared anchor evidence resolves and matches the underlying payload | Assert every declared anchor's identifier reference resolves into the historical plane and matches the referenced records' actual payload |
| Q-6 | Anchors are identifier-based, never time-derived | Assert every anchor's basis type ∈ the identifier-basis enum; assert no time-gap basis is admissible in v0 |
| Q-7 | A model never writes an Episode version | Assert `committed_by` is a trusted runtime (ADR-0002 I-2); assert every model-proposed boundary cites a `ConsolidationProduced` record |
| Q-8 | Boundary method and, where applicable, model identity are recorded in provenance | Assert every Episode version carries a non-null boundary-method field and, when model-proposed, a resolvable model identity |
| Q-9 | Episodes form only during consolidation, never inside an evaluation epoch | Assert no Episode version's commit falls between an epoch's open and close (ADR-0004 K-4) |
| Q-10 | Declared anchors are truthful, but membership is not confined to one anchor | Assert any declared anchor matches the payload (Q-5); assert **no** check rejects a version whose members span multiple anchors |
| Q-11 | No exclusivity constraint is enforced | Assert a record may be admitted to a second Episode without rejection |
| Q-12 | A new version exists only where the proposal explicitly targeted that lineage | Assert every version after v1 carries an explicit lineage target matching its object identity; assert an untargeted proposal establishes a new object instead |
| Q-13 | Validation checks admissibility only | Assert the validator's check set equals the enumerated admissibility list and contains no check purporting to establish boundary correctness |
| Q-14 | Passing validation confers no epistemic authority | Assert an established Episode's status remains an interpretive claim; assert no code path treats validator success as evidence the boundary is correct |
| Q-15 | Multiple Episodes may share one external session, and one Episode may span several | Assert no uniqueness constraint on external-key→Episode; assert a version whose members carry differing session identifiers is admissible |

## Evidence and rationale

Option C is recommended, but the more useful observation is that **Option B was never a complete answer**.
Under ADR-0002 a model cannot establish anything, so "model-proposed construction" always requires a second
party to establish the result. Recognising that collapses the apparent three-way choice into a narrower one:
whether the establishing party has deterministic constraints to validate against. C says yes; B without
constraints says the runtime rubber-stamps whatever the model returned, which is establishment in name only.

Option A is rejected on a semantic argument that stands independently of any measurement. An external
session, call or transaction boundary is a fact about a *transport or execution container*; a cognitive
episode is a claim about what constitutes one meaningful unit of experience. Those coincide only by accident.
One session routinely contains several unrelated episodes, and one episode can outlive a reconnect or a
handoff. Option A does not construct episodes; it renames sessions, and calling the result an Episode would
misrepresent what the object asserts.

An earlier draft of this ADR additionally argued that Option A would make C > B harder to demonstrate,
because a retrieval baseline could reproduce session-shaped chunks. **That argument was withdrawn as
inadmissible.** Choosing an architecture because a simpler one might not beat the baseline is selecting the
mechanism to win the measurement, which `.claude/rules/scientific-method.md` forbids. Architecture is chosen
for semantic correctness before outcomes are known, and the benchmark is then permitted to falsify the claim.
If a simpler architecture performs no better than conventional retrieval, that is a valid and useful result,
not a reason to have built something more elaborate in advance.

Identity is opaque rather than anchor-derived because tying it to an external key would silently re-impose
the very equivalence Option A was rejected for. If the session ID were the Episode's identity, then one
session could hold at most one Episode and no Episode could span two — the architecture would assert
session ≡ episode in its identity model while denying it in its prose. Rule 3's explicit lineage targeting
answers the revision-versus-duplication question that anchor-identity was reaching for, without buying it at
that price: a proposal either names the lineage it revises or it does not, and that is a property of the
proposal rather than of any external key.

Rule 7's permissiveness is deliberate asymmetry. Adding an exclusivity constraint later is cheap; removing
one is not, because data written under exclusivity never recorded the memberships it rejected. The same
asymmetry argued for the smaller object set in ADR-0007.

Rules 12–14 exist because structural validation is easy to over-read. Every check the validator performs is
about *form* — references resolve, records are committed, provenance is legal, declared anchors are truthful.
None of them touches whether these records belong together, and none could: that is an interpretive judgement
and no deterministic check can settle it. Saying so explicitly matters because the alternative failure is
quiet — a boundary that passed validation being treated downstream as though it had been verified, which
would let a model acquire epistemic authority through the back door of a green check. Q-13 and Q-14 are what
prevent the validator's check set from silently growing a correctness claim.

Rule 15 removes a problem rather than solving one. Live incremental assembly would produce a version per
event under rule 6's immutability, which is both expensive and meaningless — most intermediate versions would
never be read. Deferring formation to consolidation makes the version chain match the granularity at which
episodes are actually interpreted, and it inherits ADR-0004's epoch guarantee for free.

## Consequences

**Easier:** representing episodes that do not align with session boundaries; distinguishing revision from
duplication by an explicit property of the proposal; auditing why particular records were grouped; degrading
to deterministic boundaries when no model is available.

**Harder:** consolidation must decide, per proposal, whether it is revising a lineage or establishing a new
Episode — a policy this ADR requires but does not supply (see D-26); consolidation carries the cost of
segmentation; without an explicit targeting policy, repeated consolidation could accumulate near-duplicate
Episodes over the same records.

**Newly required:** MNEXA-issued opaque Episode identity; an explicit lineage-target field on proposals; an
anchor-basis registry with an identifier-only enum for v0; boundary-method and model-identity fields on
Episode versions.

**Constrained:** D-07 inherits a worked instance of propose-versus-establish that its general rule should
remain consistent with. D-10 is helped — episode *identity* is deterministic even where boundaries are not,
so reproducibility failures localize to segmentation. D-13's activation records may reference Episode
versions as pinned interpretive versions under ADR-0002 rules 5–6.

**Newly uncovered decisions — recorded, not decided here:**

- **D-25 — episode split and merge identity.** Deferred from v0 as above.
- **D-26 — episode lineage revision targeting policy.** Rule 3 requires a proposal to declare whether it
  revises an existing lineage, but does not say how consolidation decides. Without a policy, repeated
  consolidation may establish near-duplicate Episodes over the same records rather than revising. This is
  consolidation behaviour rather than episode semantics, and settling it here would have expanded scope.

## Reversibility

High throughout, and higher than the earlier draft. Adding time-based or composite anchors later is a
registry change. Because identity is opaque and MNEXA-issued rather than derived from anything, changing
anchor policy, boundary method or even the notion of anchors entirely does not disturb existing Episode
identities — which is a direct benefit of amendment 2 over the anchor-derived scheme it replaced.

## Validation / falsification

Revisit if:

- available experience sources carry no usable identifiers, leaving candidate generation underdetermined and
  forcing time-based evidence — which would make D-05 a prerequisite after all; or
- model-proposed boundaries prove so unstable across consolidations that near-duplicate Episodes accumulate,
  which would make D-26 urgent rather than deferred; or
- episodes are never recalled independently of the beliefs derived from them, suggesting the kind carries no
  weight at v0 scale.

Evidence that MNEXA performs equally well with episodes disabled would be a genuine and reportable result
about this architecture, not a defect in the experiment. It would argue for removing the kind rather than
refining it, and that argument should be allowed to run.

## Outcome

Pending. No implementation exists.
