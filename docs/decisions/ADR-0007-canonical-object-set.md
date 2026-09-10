---
id: ADR-0007
status: accepted
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0007 — Canonical MNEXA v0 Object Set and Plane Assignment

**Tier: D3 (constitutional).** Requires explicit owner approval.

Covers register entry **D-02**. Deliberately does **not** decide D-03 (episode construction authority);
see *Episode boundary* below for the separability analysis.

**Approval:** accepted by owner 2026-09-10, following two owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **The prohibition on historical references to Entity was too absolute.** The original N-3 forbade any
   historical→Entity reference. That destroyed the ability to record which identity resolution the runtime
   actually used at decision time, which is itself historical fact. Replaced with the epistemic distinction:
   such references are permitted, version-pinned, with usage semantics only. — Entity section, N-3, N-9, N-10.
2. **Ephemeral projection does not mean disposable evidence.** The original left projections without a stated
   capture obligation, and described the v0 event-type list as closed. Projections that influenced cognition
   or are needed to reproduce a decision must be *capturable* as historical evidence without gaining
   canonical identity; and the event-type list is provisional pending D-10, D-12 and D-13. — rule on
   capturable projections, N-7, N-11.

## Decision question

Which concepts become canonical MNEXA v0 objects, which are demoted to historical event types or
projections, and on which plane does each canonical object sit?

## Context

ADR-0002 established two planes and the rules governing them. It did not enumerate what lives in them. The
v0 specification's domain model (items 6–9) is exactly this enumeration, and items 10–16 are contracts over
whatever it produces, so nothing further can be written until it is settled.

The governing constraint is YAGNI against the vision's own vocabulary. Sections 2, 3 and 10 name upward of
sixteen intelligence-graph node types spanning every future phase. Promoting each to a canonical object
would build the collective-intelligence ontology during a single-agent experiment. The test applied
throughout is not *does the vision name this* but *does a v0 contract become impossible without it*.

### Three categories

| Category | Definition | Identity |
|---|---|---|
| **Canonical object** | A durable MNEXA primitive with stable identity and semantics, referenced by other objects, carrying a lifecycle | Independent, spans records/versions |
| **Historical event type** | A committed fact that some production, action or observation occurred | Record identity only; no lifecycle beyond existing |
| **Projection / derived view** | Computed for cognition or operation | None durable; may be *captured* into a record for reproducibility |

The distinction between the first two is whether the identity spans anything. An Entity is referred to by
many records over time; an `OutcomeObserved` record is referred to as itself. Adding an event type is a
schema extension. Adding a canonical object is an architectural change — a distinction that matters for how
v0 evolves.

## The plane-assignment criterion

Plane assignment needs a stated criterion, and three are genuinely available.

### Criterion α — by producing mechanism

Model-produced ⇒ interpretive. Deterministic or externally supplied ⇒ historical.

This fails in both directions. A deterministic algorithm grouping records `E1…E5` into "Episode P" produces
an **interpretation** — the grouping asserts those records form one meaningful unit, which is a claim about
organization, not an occurrence, and determinism does not make it less of a claim. Conversely, a record
stating *that a model produced output X* is historical fact despite a model being involved. ADR-0002 rules
8–9 already rejected α implicitly when they separated write authority from content authorship.

### Criterion β — by epistemic meaning

Does the object assert **what occurred**, or **how MNEXA organizes and interprets what occurred**? The first
is historical; the second is interpretive, whatever produced it.

Under β, an externally supplied `session_id` or `transaction_id` is historical evidence — it was genuinely
observed — while MNEXA's Episode abstraction over the records carrying that identifier remains interpretive.
The two are not the same object, and the presence of the first does not make the second historical.

### Criterion γ — by anticipated mutability

If it will never need revision, historical; if it might, interpretive.

Circular. Whether something needs revision *follows from* whether it is an interpretation. γ also invites
plane assignment by convenience, which is how a mutable-history back door gets built.

### Decision on criterion

**Adopt β.** It is not a new rule but the generalization of one already accepted: ADR-0002 rule 7 —
model-authored *claims* are interpretive while the *production event* is historical — is exactly β applied
to the model case. Adopting β explains rule 7 rather than competing with it.

**β is also what makes D-02 and D-03 separable.** Under α, Episode's plane could not be assigned without
first deciding who constructs episodes, and the two decisions would be logically inseparable. Under β the
plane follows from what an Episode *asserts*, independent of its producer — so this ADR can fix the plane
and leave construction authority wholly to D-03. That separability is a consequence of the criterion, not
an assumption.

## Ontology approaches considered

### Option A — Minimal canonical core

Two or three durable primitives; most cognitive concepts become typed events or typed variants.

| Criterion | Assessment |
|---|---|
| Semantic clarity | Moderate — kind becomes a discriminator field rather than a type |
| Provenance | Strong — one implementation, uniformly applied |
| Replay / reconstruction | Strong — one ledger, one interpretation model |
| Reproducibility | Strong |
| Future evolution | **Strongest** — patterns, principles, skills arrive as new *kinds*, not new primitives |
| Implementation complexity | Lowest |
| Risk of premature ontology | **Lowest** |
| Satisfies accepted invariants | Yes, and only once per invariant |

### Option B — Rich explicit ontology

Episode, Belief, Pattern, Principle, Decision, Prediction, Outcome, Skill each a canonical object.

| Criterion | Assessment |
|---|---|
| Semantic clarity | **Highest** — each concept is its own type |
| Provenance | Weaker in practice — versioning, provenance and freshness machinery duplicated per type, with drift between copies |
| Replay / reconstruction | Moderate — reconstruction must understand many types |
| Reproducibility | Moderate |
| Future evolution | Poor — every new cognitive kind is a schema migration |
| Implementation complexity | Highest |
| Risk of premature ontology | **Highest** — v0 has no patterns, principles or skills to model |
| Satisfies accepted invariants | Yes, but 72 invariants must be re-satisfied per type |

Option B also collides with ADR-0002 directly. A `Decision` object that later has its outcome *attached* is
a mutable historical record, which rules 2–3 forbid. Under B, Decision would have to be interpretive, which
misclassifies the plain fact that a decision was made.

### Option C — Principled hybrid

Minimal core, but carve out as a distinct primitive any concept whose **lifecycle** genuinely differs rather
than merely its meaning. Concretely: keep the historical ledger and the generic interpretation primitive, and
separate Entity because identity continuity has merge/split semantics no other interpretation has.

| Criterion | Assessment |
|---|---|
| Semantic clarity | Good — three primitives, each with a distinct reason to exist |
| Provenance | Strong |
| Replay / reconstruction | Strong |
| Reproducibility | Strong |
| Future evolution | Strong — new kinds do not create primitives unless their lifecycle differs |
| Implementation complexity | Low, marginally above A |
| Risk of premature ontology | Low |
| Satisfies accepted invariants | Yes |

**Recommendation: Option C.** It keeps A's evolution and complexity properties while admitting the one case
where a shared primitive would genuinely misrepresent behaviour. The carve-out rule — *a distinct lifecycle,
not a distinct meaning, earns a primitive* — is stated so future phases have a test rather than a precedent.

## Decision

**Three canonical objects.** *(Proposed. Not approved.)*

---

### 1. ExperienceRecord

**Purpose.** The atomic committed fact that something occurred. The ledger's unit and the terminus of every
provenance path.

**Plane.** Historical.

**Why durable identity.** ADR-0002 I-9a requires grounded interpretations to terminate in historical records,
and ADR-0005 requires provenance references to resolve. Both need addressable record identity.

**Immutable or versioned.** Immutable; fixed at commit with a content hash (ADR-0002 rules 2, 7).

**May reference.** Interpretive versions, pinned and with usage semantics only (ADR-0002 rules 5–6). Other
ExperienceRecords — see *newly uncovered decision D-24*, which this ADR does not settle.

**Its existence asserts.** That an event of the recorded type occurred, as observed, at the recorded time.
Where its payload is model-authored it asserts *that the production occurred*, never that the payload's
claims are true (ADR-0002 rules 9–10).

**Could it be an event type or projection instead?** It *is* the event carrier. Specific occurrence
kinds — decision, prediction, action, outcome — are **types of this record**, not separate objects.

**Impossible without it.** Everything. Experience capture, provenance grounding, and the entire historical
plane.

**v0 event types.** A **provisional** list, extensible without architectural change. It is explicitly **not
declared closed**: D-10 (recall reproducibility), D-12 (decision/prediction/outcome linkage) and D-13
(activation trace) may each require additional types, and adding one changes only the enum validated by N-2,
never the canonical object count (N-8).

`ObservationRecorded` · `DecisionMade` · `PredictionMade` · `ActionExecuted` · `OutcomeObserved` ·
`CorrectionReceived` · `ContextAssembled` · `MemoryActivated` · `ConsolidationProduced` ·
`RevalidationAttempted`

The last two are required by accepted decisions: ADR-0002 rules 8–9 for attributed model production, and
ADR-0006 M-20 for revalidation attempts. No separate `InterpretationCommitted` type is proposed — a version's
own commit metadata under ADR-0005 already records that fact, and duplicating it would create two sources of
truth for one event.

---

### 2. Entity

**Purpose.** A persistent identity for something in the world, holding continuity while names and
descriptions change.

**Plane.** **Interpretive.** An Entity asserts *these references denote one persistent thing*, which is a
resolution judgement that can be wrong and must be revisable. Raw identifiers observed in the world —
`session_id`, a service name string, a call ID — are historical evidence inside ExperienceRecord payloads.
They are not Entities, and their presence does not make MNEXA's identity abstraction historical.

**Consequence: identity binding is interpretive, but usage of a binding is historical.** The claim
"identifier X in record R denotes Entity E" is an Interpretation of kind `identity_binding` — a judgement that
may be wrong and must be revisable.

A historical record may nonetheless **reference a version-pinned Entity or identity-related Interpretation
version**, solely to record which identity resolution the runtime actually used at that time. This must be
expressible:

> "Decision D was made while Entity E17 version 4 was the identity resolution used by the runtime."

That is historical fact. It does **not** assert that E17 v4 was objectively the correct identity. Under
ADR-0002 rules 5–6 this is an ordinary version-pinned usage edge, identical in kind to `MemoryActivated`.

The constraints are therefore:

- never reference a mutable Entity or Interpretation **head** from history — version-pinned only;
- edge semantics express **usage and context**, never truth;
- raw observed identifiers remain structurally distinguishable from MNEXA identity references within a
  record, so the two are never conflated on read;
- the presence of an Entity reference in history **never** promotes the identity interpretation to grounded
  fact — its epistemic status is unchanged by being used.

**Why durable identity.** Its stable identity *is* its purpose (2.4: names change, identity persists).

**Immutable or versioned.** Versioned object with a mutable head (ADR-0002 rule 4).

**May reference.** Other Entities (relationships) and Interpretations, all version-pinned (ADR-0005).

**Its existence asserts.** That MNEXA currently models a persistent thing with this identity. Not that its
current description is correct.

**Could it be an Interpretation kind instead?** Considered and rejected, but this is the most contestable
inclusion in the set. Entity carries **merge and split** semantics — two entities discovered to be one, or
one found to be two — which no other interpretation has, and which supersession alone does not express
cleanly. That is a lifecycle difference, which is Option C's stated test for a primitive.

**Impossible without it.** Identity continuity across renaming. Without it the same subject under two surface
names produces two disjoint memory regions, and recall cannot connect them — the failure 2.4 names as losing
continuity because language changed. It also removes entity-conditioned recall (5.6), one of the routes by
which condition C is meant to differ from retrieval.

---

### 3. Interpretation

**Purpose.** Any versioned claim MNEXA holds *about* what occurred: how records group, what they mean, what
follows from them.

**Plane.** Interpretive.

**Why durable identity.** Provenance targets, supersession chains, freshness assessment and activation
records all reference interpretations by identity and version.

**Immutable or versioned.** Versioned chain of immutable versions with a mutable head. Each version's
derivation edge set is inside its content identity (ADR-0005 rules 5–6).

**May reference.** ExperienceRecords, Entities, and other Interpretation versions — all version-pinned, all
subject to strict commit-order preexistence (ADR-0005 L-7) and the DAG check (L-8).

**Its existence asserts.** That MNEXA holds this claim at this version, with this ancestry and this epistemic
status. Whether it is grounded is carried explicitly (ADR-0002 rule 11).

**Kinds in v0.** `episode` · `identity_binding` · `belief`. Kind is a typed discriminator, not a separate
primitive. Future phases add `pattern`, `principle`, `causal_model`, `procedure` and `skill` as kinds; none
requires a new canonical object unless its lifecycle differs.

**Could it be event types or projections instead?** No. Interpretations must be superseded, carry provenance
and be assessed for freshness. Events cannot be superseded; projections have no identity to supersede.

**Impossible without it.** Consolidation, personal memory beyond raw logs, and every accepted invariant in
the I-, L- and M- series, all of which are written about interpretive versions.

---

### Episode boundary — plane only

**Episode is an Interpretation of kind `episode`, on the interpretive plane.** It asserts that a set of
ExperienceRecords forms one meaningful unit, which under criterion β is organization, not occurrence.

This resolves register tension **T-1**: vision 3.2 places episodes in the Memory Plane, while 2.3 and 3.8
describe them in the language of history. 3.2 is correct, and β explains why — 3.8's "MNEXA preserves both
representations" is satisfied by raw records staying historical while the grouping over them is interpretive.

**This ADR does not decide, and D-03 must:** who draws episode boundaries; whether boundaries are
model-generated, deterministic, hybrid or externally supplied; when episodes are formed; and boundary
revision policy. None of these is logically inseparable from the plane assignment, precisely because
criterion β makes the plane independent of the producer.

---

### Concepts intentionally demoted

| Concept | Category | Reasoning |
|---|---|---|
| **Decision** | Event type `DecisionMade` | The *fact* a decision was made is an occurrence. A canonical Decision object with an outcome later attached would be mutable history, which ADR-0002 rules 2–3 forbid. Assessment of the decision is an Interpretation |
| **Prediction** | Event type `PredictionMade` | Same. 6.20 requires predictions never to disappear — immutability gives that. The *score* is an Interpretation |
| **Action** | Event type `ActionExecuted` | Pure occurrence |
| **Outcome** | Event type `OutcomeObserved` | Pure occurrence. Its linkage to a decision is D-12's contract, not a new object |
| **Belief** | Interpretation kind `belief` | Versioned claim; the generic primitive covers it exactly |
| **ContextFrame** | **Projection**, capturable | Assembled per decision from goal, entities and state. No durable identity, but the exact frame used must be capturable as historical evidence for reproducibility (ADR-0003 J-1). `ContextAssembled` is the presumed carrier; the trace contract is D-10's to decide |
| **MemoryActivation** | Event type `MemoryActivated` | The paradigm case of ADR-0002 rules 5–6: a historical fact citing an interpretive version, pinned, with usage semantics. Distinct from the content of the version activated. Satisfies 5.40 cognitive provenance |
| **Recall result** | **Projection**, capturable | No independent identity, but enough immutable historical evidence must be recordable to determine what was retrieved, activated or suppressed where the recall/attribution contract requires it. Whether that is `RecallPerformed`, richer `MemoryActivated` records, `ContextAssembled` payload or another form is **D-10/D-13's decision, not settled here** |
| **Consolidation proposal** | Interpretation version **+** `ConsolidationProduced` record | ADR-0002 rules 8–10 already determine this: the production is historical and attributed; the proposal is an Interpretation whose epistemic status is explicit. A model producing a candidate does not make it grounded |
| **Freshness / staleness assessment** | **Projection**, capturable | Derived state, never stored on a version (ADR-0006 rule 3). The assessment *actually presented to cognition* may be recorded as part of historical activation or context evidence; which carrier is D-13's decision |
| **Revalidation attempt** | Event type `RevalidationAttempted` | Settled by ADR-0006 M-20 |

Six of these eleven were already forced by accepted decisions rather than chosen here.

### Rule: ephemeral projection does not mean disposable evidence

A projection that **materially influenced cognition**, or that is **required to reproduce or attribute a
decision**, must be capable of being captured as immutable historical evidence.

Capture does not confer canonical object identity. The projection remains a projection; only its
*instantiated value or trace* becomes historical. A ContextFrame is still assembled and discarded; what
persists is the record of the frame that was used.

This ADR fixes the obligation and deliberately leaves the mechanism open. Whether the trace is carried by a
`RecallPerformed` event, by richer `MemoryActivated` records, by `ContextAssembled` payload, or by some other
representation belongs to **D-10** (recall reproducibility) and **D-13** (activation trace and attribution),
and is not settled here.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| N-1 | Exactly three canonical object types exist in v0 | Assert the schema registry contains ExperienceRecord, Entity, Interpretation and no other canonical type |
| N-2 | Every ExperienceRecord carries a type from the closed v0 event-type list | Assert `type` ∈ declared enum; reject commit otherwise |
| N-3 | Historical references to Entity or Interpretation are version-pinned, never to a head | Assert every such reference carries a version identity; assert zero references resolving through a mutable head (ADR-0002 I-5) |
| N-4 | Every Interpretation carries a kind from the declared kind list | Assert `kind` ∈ declared enum |
| N-5 | Episode-kind interpretations reference ≥1 ExperienceRecord | Assert each `episode` version's provenance includes at least one historical record |
| N-6 | No canonical object is mutable in place | Assert ExperienceRecord immutability (ADR-0002 I-1) and that Entity/Interpretation change only by new versions (ADR-0005 L-4, L-9) |
| N-7 | ContextFrame, recall results and freshness assessments have no canonical object identity | Assert no canonical object type is registered for any of them |
| N-8 | Adding an event type does not alter canonical object count | Assert N-1 holds across event-type extension; extension changes only the enum in N-2 |
| N-9 | Raw observed identifiers and MNEXA identity references are structurally distinguishable in a record | Assert they occupy distinct, separately typed fields; assert no read path conflates them |
| N-10 | Using an interpretation from history does not change its epistemic status | Assert the referenced version's grounded/ungrounded status is unchanged before and after being referenced |
| N-11 | Any projection that influenced cognition or is required to reproduce a decision is capable of historical capture | Assert the historical plane admits a record carrying it — i.e. no such projection is structurally uncapturable. The specific record type is D-10/D-12/D-13's decision, not asserted here |

## Evidence and rationale

The demotions carry more weight than the promotions. Option B's ontology is what most systems would build,
and it is wrong here for a reason specific to ADR-0002: the vision repeatedly describes objects that *accrue*
information — a Decision that later has its outcome attached (2.7), a memory that strengthens with use
(3.12). Under accepted immutability none of those can be a mutable object. They are a fixed historical
record plus a superseding interpretation, and once that is seen, Decision, Prediction, Action and Outcome
stop looking like objects and start looking like what they are: occurrences.

The Entity treatment is where criterion β does the most work. It would be natural to make identity binding
part of the ExperienceRecord — the identifiers are right there in the payload. But binding an observed
identifier to a persistent identity is a resolution judgement, and putting a judgement inside an immutable
record makes it uncorrectable except by appending a correcting record, which is the wrong mechanism for
something that will be revised routinely as evidence accumulates. Keeping bindings interpretive also avoids
a collision with ADR-0002 rule 6, since a record asserting "this is Entity E" would be a truth assertion from
history about an interpretation, which rule 6 prohibits.

Three primitives is not minimal for its own sake. Two — dropping Entity into Interpretation — was seriously
considered and is the single most reversible choice here. It was rejected on merge/split, which supersession
represents poorly: merging two entities is not one of them superseding the other, since both had valid
independent histories, and expressing that as ordinary supersession would lose which observations belonged
to which prior identity.

## Consequences

**Easier:** future cognitive kinds arrive without schema migration; the 72 accepted invariants are
implemented once each rather than per type; the domain model fits on a page.

**Harder:** kind-specific semantics need discipline to avoid accreting ad hoc onto a shared primitive; a
reader looking for a `Decision` type will not find one and must learn the event-type model.

**Newly required:** an event-type registry with closed-enum validation; an Interpretation kind registry;
capture of the exact assembled context inside `ContextAssembled`.

**Constrained:** D-12 must express decision/prediction/outcome linkage as references between records rather
than as object fields. D-13's activation trace is `MemoryActivated` record content. D-14's ports operate over
three object types plus event append. D-04's identity semantics apply to Entity and to `identity_binding`
interpretations, now known to be interpretive.

**Newly uncovered decision — recorded, not decided here: D-24 — historical-to-historical reference
semantics.** ADR-0002 I-5 governs historical→interpretive references and ADR-0005 governs
interpretive→interpretive, but nothing covers a historical record citing another historical record. Demoting
Decision and Outcome to event types makes this immediately load-bearing: an `OutcomeObserved` record must
point at the `DecisionMade` record it is an outcome of. Both are immutable so no pinning question arises, but
whether such references are permitted, whether a commit-order constraint analogous to L-7 applies, and
whether they may form cycles are unanswered. D-12 depends on the answer.

## Reversibility

Moderate and asymmetric. Adding a canonical object later is straightforward. **Removing one is not** — data
written under a primitive that turns out to be unnecessary must be migrated into whatever replaces it. This
asymmetry argues for the smaller set: promoting a kind to a primitive later is cheap, demoting a primitive to
a kind is not. Event-type and kind lists are extensible at will and are the intended growth path.

## Validation / falsification

Revisit if:

- kind-specific behaviour accumulates on Interpretation to the point that the shared primitive is a union
  type in all but name, which would argue Option B was right for the kinds that diverged; or
- Entity's merge/split turns out to be unnecessary at v0 scale, which would collapse the set to two; or
- `ContextAssembled` capture proves insufficient to reproduce a decision, which would mean ContextFrame needs
  durable identity after all and N-7 is wrong.

Evidence that a v0 contract could not be written against these three objects — that some required behaviour
has nowhere to live — would falsify the claim that this set is sufficient.

## Outcome

Pending. No implementation exists.
