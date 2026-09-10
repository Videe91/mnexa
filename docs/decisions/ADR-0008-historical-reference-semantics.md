---
id: ADR-0008
status: accepted
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0008 — Historical-to-Historical Reference Semantics

**Tier: D3 (constitutional).** Requires explicit owner approval.

Covers register entry **D-24**.

**Approval:** accepted by owner 2026-09-10, following one owner-directed amendment made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (pre-acceptance, owner-directed):**

1. **Structural admission is evidence-based, not actor-based.** The original rule 2 and P-10 tested whether a
   model participated. That is the wrong boundary in both directions: a model may legitimately *propose* a
   relationship the runtime then independently verifies, while a human or heuristic performing semantic
   judgement is producing interpretation despite no model being involved. The test is now the admissibility
   of the *evidence*, with an enumerated basis list. The amendment additionally requires immutable relation
   basis/provenance, narrows relation semantics against truth import, and requires representational
   equivalence between inline and `RelationshipRecorded` forms. — rules 2, 9–12, invariants P-10, P-12 … P-16.

## Decision question

May a historical record reference another historical record, and under what ordering, mutability and
relationship semantics?

## Context

Three reference directions exist. Two are settled:

| Direction | Governed by |
|---|---|
| historical → interpretive | ADR-0002 I-5, I-8 — version-pinned, usage semantics only |
| interpretive → interpretive | ADR-0005 — version-pinned, strict commit-order preexistence |
| **historical → historical** | **nothing** |

The gap is older than it appears. **ADR-0002 rule 3 already presupposed it:** "A mistaken historical record
is corrected by appending a new record that supersedes it." A superseding record must identify what it
supersedes, which is a historical→historical reference. The rule was accepted without the mechanism it
requires existing. ADR-0007 did not create this gap; it made it urgent by demoting Decision, Prediction,
Action and Outcome to event types, so that decision→action→outcome linkage now has nowhere else to live.

### The distinction that governs everything here

Both endpoints being historical does **not** make the relationship between them historical.

- **Structural linkage** — the relationship's existence is determined by runtime or source correlation,
  from identifiers the emitter already holds. No inference, no similarity, no judgement. *This outcome is the
  outcome of that decision* is a fact the runtime knows because it emitted both.
- **Interpretive claim** — the relationship is asserted on the basis of reasoning about content.
  *This outcome was caused by that decision* is a claim that may be wrong, however obvious it looks.

Admitting the second onto the historical plane would smuggle unrevisable causal claims into immutable
storage, which is the precise failure ADR-0002 exists to prevent. Vision 2.8 is explicit that `A happened
before B` must never silently become `A caused B`, and 3.23 gives causal promotion its own multi-stage
evidence ladder. A historical edge would bypass that ladder entirely.

## Options considered

### Option 1 — Forbid historical→historical references entirely

All linkage between records is interpretive.

Benefits: one simple rule; no new vocabulary; maximum purity of the historical plane.

Costs: misclassifies runtime fact as judgement. The runtime *knows* which decision an action executed; making
that an interpretation means it starts life ungrounded, carries confidence it does not need, and can be
superseded — none of which fits a correlation the emitter observed directly. Also breaks replay: a trajectory
could not be reconstructed from the ledger alone, only from the ledger plus a correct set of interpretations.
And it leaves ADR-0002 rule 3's correction mechanism unimplementable.

Rejected.

### Option 2 — Inline structural references only

A record may cite already-committed records through a closed structural vocabulary, carried inside the
referencing record and covered by its content hash. No other mechanism.

Benefits: simple; atomic — a record and its linkage commit together; strict ordering trivially enforced.

Costs: fails the later-discovery case entirely. An outcome observed long after its decision, or a correlation
an external system establishes retrospectively, has nowhere to go, because neither existing record may be
modified. Those relationships would be forced onto the interpretive plane despite being structural.

### Option 3 — Inline structural references plus append-only Link records

Both mechanisms, distinguished by *when the relationship becomes known*. Known at commit → inline, inside the
referencing record's content identity. Discovered later → append a new historical record that cites both
endpoints and mutates neither.

Benefits: covers both timings without weakening immutability. The common case stays atomic. The
later-discovery case has a home, and the appended record carries its own timestamp and provenance, so *when
the relationship became known* is itself preserved — information Option 2 discards and Option 4 preserves
only at the cost of the atomicity below.

Costs: two representations of one concept; queries must union inline edges with link records.

### Option 4 — Link records only

Every historical→historical edge is a separate record. Endpoints never carry edges.

Benefits: one uniform mechanism; every edge has its own identity, timestamp and provenance; endpoint hashes
concern only the event itself.

Costs: **loses atomicity**. An `ActionExecuted` record and its `execution_of` link commit separately, so a
crash between them leaves a permanently orphaned action in an append-only ledger that cannot be repaired by
editing. Option 3 avoids this for every relationship known at emit time, which is most of them. Also doubles
record count for the common case and forces a join to reconstruct a trajectory.

## Decision

**Recommendation: Option 3.** *(Proposed. Not approved.)*

Eight rules, answering the six questions in order.

### Permission and vocabulary

1. **Historical records may reference historical records, structurally only.** Permitted through a declared
   structural relationship vocabulary and no other way.

2. **Structural admission is evidence-based.** A historical→historical structural relationship may be
   admitted only when the trusted runtime can establish it from **non-semantic, machine-verifiable
   structural or correlation evidence**. The test is the evidence, not the actor.

   Admissible bases include, where applicable:

   - explicit prior-record identity carried in the emitted event;
   - execution or run identifier;
   - trace parent identifier;
   - request/response correlation identifier;
   - transaction identifier;
   - protocol-defined parent/child identity;
   - an authoritative source explicitly targeting a particular prior record, where what history records is
     that targeting relationship.

   Semantic similarity, model judgement, human interpretation, inferred causation, and "these appear
   related" are **not** admissible bases. Neither the presence nor the absence of a model is decisive:
   a model may propose, and a human may still be interpreting.

   Provisional v0 vocabulary: `outcome_for` · `execution_of` · `response_to` · `correction_of` ·
   `evaluates_prediction` · `continuation_of`. `correction_of` is the mechanism ADR-0002 rule 3 assumed.

3. **Interpretive meanings are forbidden on the historical plane.** `caused_by`, `explains`,
   `supports_truth_of`, `proves` and their equivalents may never be historical edges, regardless of how
   evident the relationship appears or that both endpoints are historical. They are Interpretations citing
   the records.

   **External-protocol assertions are recorded as content, not as edges.** If an external system asserts a
   causal relationship, what history records is *that the system asserted it* — payload inside a record, with
   the asserting source identified. The edge remains non-causal. An external protocol may only contribute a
   *structural* edge where the protocol itself establishes the correlation, such as a trace parent-child
   relation or a request/response pairing.

### Ordering and direction

4. **Strict preexistence.** A referenced record must already be **committed** before the referencing record
   is committed, ordered by commit sequence rather than wall-clock time — the same rule and the same reason
   as ADR-0005 L-7, where timestamps were rejected because they collide.

5. **No forward references, ever, and no self-reference.** A record may never cite a record committed after
   it. **The later record points backward:** an outcome cites its decision; a decision never cites its own
   later outcome. This makes the historical reference graph a DAG by construction; an explicit cycle check is
   retained as defence in depth, following ADR-0005 L-8.

### Immutability

6. **Inline edges are part of content identity.** A referencing record's structural edges are covered by its
   content hash and fixed at commit, consistent with ADR-0005 rule 6 for interpretive versions. There is no
   operation to add, retarget or remove an inline edge after commit.

7. **Later-discovered relationships append, never modify.** A relationship established after the referencing
   record was committed is expressed by appending a new historical record of type `RelationshipRecorded`,
   citing both endpoints and carrying the same structural vocabulary and constraints. **Neither endpoint is
   touched.** Its own commit time records when the relationship became known, which is distinct from when
   either event occurred.

8. **`RelationshipRecorded` is an event type, not a fourth canonical object.** It is an ExperienceRecord
   under ADR-0007, added to that ADR's provisional event-type list — exactly the extension path ADR-0007
   amendment 2 kept open. The canonical object count is unchanged (ADR-0007 N-1, N-8).

### Proposals, basis and semantics

9. **Proposals do not create edges.** A model or a human may propose "R20 may be related to R10". That
   proposal may itself be recorded historically where appropriate. It does **not** create a structural edge
   unless the trusted runtime can independently satisfy rule 2. Where no admissible structural evidence
   exists, the claimed relationship belongs on the interpretive plane.

10. **Relation basis is immutable and hashed.** Every structural relationship preserves enough immutable
    admission evidence to answer *why was this relation allowed onto the historical plane*. The relation
    type, target record identity and relation-basis material are part of the immutable content identity of
    whichever record establishes the relationship — the referencing ExperienceRecord for an inline edge, the
    `RelationshipRecorded` for a later one. A stable immutable **reference** to admissible evidence is
    sufficient; redundant raw data need not be duplicated.

11. **A structural relation states only its defined structural meaning.** It carries no truth import.

    - `CorrectionReceived R100 —correction_of→ R50` means R100 was issued or received as a correction
      targeting R50. It does **not** mean every claim in R50 is false.
    - `OutcomeObserved R30 —evaluates_prediction→ R10` means the runtime, source or protocol structurally
      paired that outcome with that prediction. The edge does **not** assert whether the prediction was
      correct.

    No historical relation vocabulary may smuggle in `caused_by`, `proves`, `explains`, `supports_truth_of`
    or `contradicts_truth_of` — unless what history records is explicitly that some **attributed source made
    such an assertion**, which is a record of an assertion, not MNEXA establishing it as historical truth.

12. **Representational equivalence.** A relation type has identical core semantics whether captured inline or
    via `RelationshipRecorded`. The only difference is temporal and provenance: inline means the relationship
    was established when the referencing event was committed; `RelationshipRecorded` means it became
    established or recorded later. Two representations must never acquire two epistemic meanings.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| P-1 | Every historical→historical edge uses the declared structural vocabulary | Assert edge type ∈ declared enum; reject commit otherwise |
| P-2 | No historical→historical edge carries an interpretive meaning | Assert the forbidden set (`caused_by`, `explains`, `supports_truth_of`, `proves`, equivalents) is absent from the vocabulary and from all stored edges |
| P-3 | Every referenced record was committed before the referencing record | At commit, assert each target's state is `committed` and its commit sequence is strictly less than the referencing record's; reject otherwise. Never use wall-clock time |
| P-4 | No forward references and no self-references | Assert no edge targets a record with a greater-or-equal commit sequence; assert no edge has identical source and target |
| P-5 | The historical reference graph is acyclic | Topological sort over all historical→historical edges, independent of commit ordering; assert no cycle |
| P-6 | Inline edges are covered by the referencing record's content hash | Recompute the record hash including its edge set; assert it matches the stored hash |
| P-7 | No mechanism exists to add or alter an inline edge after commit | Interface test asserting no such operation is exposed; this is what makes rule 7 self-enforcing rather than a convention |
| P-8 | Appending a `RelationshipRecorded` mutates neither endpoint | Hash both endpoints before and after; assert unchanged |
| P-9 | `RelationshipRecorded` endpoints are covered by its own content hash | Recompute including both endpoint identities; assert match |
| P-10 | Every structural edge is admitted on evidence from the declared admissible-basis list | Assert each edge records an admission basis whose type ∈ the admissible enum; reject commit otherwise. Assert semantic-similarity, model-judgement and human-judgement bases are absent from that enum |
| P-12 | A proposal alone never creates a structural edge | Assert every stored structural edge carries a runtime-verified basis; assert any proposed relation lacking one exists only as an Interpretation or as recorded proposal content, never as a historical edge |
| P-13 | Relation basis is covered by the establishing record's content hash | Recompute the record hash including relation type, target identity and basis material; assert it matches |
| P-14 | Relation basis references resolve | Assert every basis reference resolves to existing immutable evidence |
| P-15 | Structural relations carry no truth import | Assert the vocabulary definition of each relation type records its explicit non-implications; assert no consumer path derives a truth value from an edge type alone |
| P-16 | A relation type means the same inline and via `RelationshipRecorded` | Assert both representations resolve to one vocabulary definition; assert no representation-specific semantic override exists |
| P-11 | Adding `RelationshipRecorded` does not change the canonical object count | Assert ADR-0007 N-1 still holds |

## Evidence and rationale

The recommendation is Option 3 rather than the more uniform Option 4 on a single decisive point: atomicity in
an append-only store. Under Option 4 a record and its linkage are separate commits, and a failure between
them leaves an orphaned record that immutability then makes permanent — the ledger cannot be edited to repair
it, so the only remedies are a compensating record or living with the orphan. Option 3 removes that failure
mode for every relationship known at emit time, which is the overwhelming majority. The cost, two
representations to query, is an implementation inconvenience rather than a correctness problem.

Option 1 deserves more than a dismissal because its instinct is right — keep the historical plane austere.
It fails because austerity applied here misclassifies. The runtime emitting an action *knows* which decision
it executes; that is not a belief it holds, and modelling it as one would give it confidence, groundedness
and revisability it has no use for, while making trajectory replay depend on interpretations being correct.
The austerity that matters is rule 3's, which keeps *meanings* off the plane, not rule 1's, which would keep
*facts* off it.

Rule 2 makes the structural/interpretive boundary enforceable by testing the evidence rather than the actor.
An actor-based test fails both ways: it would reject a model-proposed relationship that the runtime then
verifies against a trace parent identifier — which is structurally admissible however it was suggested — and
it would accept a human's semantic judgement, which is interpretation whatever produced it. Enumerating
admissible bases makes the check mechanical (P-10) without making it a proxy for who was in the room.

Rule 10 is what stops the vocabulary allowlist from being the only defence. An allowlist constrains what an
edge is *called*; the basis record constrains what it was *established from*, and it is the second that can
be audited after the fact. Requiring the basis inside the content hash means an edge cannot later acquire a
justification it did not have at commit.

Rule 11 addresses a failure that would otherwise be invisible: a permitted structural edge quietly read as a
truth claim. `correction_of` naming a prior record is the obvious case — the temptation to treat the target
as refuted is strong, and wrong, in exactly the way ADR-0006 rule 2 found for supersession. Stating each
relation's non-implications in the vocabulary itself gives P-15 something to check.

Rule 5's direction convention — later points backward — is what turns preexistence into a usable design
rather than a constraint to work around. The natural temptation is to model a decision as owning its outcome,
which would require a forward reference and therefore either a mutable record or a deferred commit. Inverting
it costs nothing semantically and removes the pressure entirely.

Rule 7 preserves something the alternatives lose: *when a relationship became known* is different from when
either event occurred, and it matters. A correction discovered a week later is a different epistemic
situation from one caught at emit time, and the appended record's own commit time captures that distinction
without any additional machinery.

## Consequences

**Easier:** reconstructing a decision→action→outcome trajectory from the ledger alone; implementing ADR-0002
rule 3's correction mechanism, which previously had no defined representation; expressing retrospective
correlations without weakening immutability; distinguishing when something happened from when it was noticed.

**Harder:** queries over relationships must union inline edges with `RelationshipRecorded` records; commit
becomes a two-phase admission for records carrying edges, since preexistence must be verified against every
target; the structural vocabulary needs governance as new adapters arrive.

**Newly required:** a structural relationship vocabulary registry with closed-enum validation and an explicit
forbidden set; commit-time preexistence admission for historical records, mirroring the check ADR-0005
introduced for interpretive versions; a `RelationshipRecorded` event type.

**Constrained:** **D-12 is unblocked** — decision/prediction/outcome linkage can now be expressed, using
`outcome_for`, `execution_of` and `evaluates_prediction`, with D-12 deciding the content and completeness
contract rather than whether the edges may exist. D-05 (time and ordering) inherits commit-sequence ordering
as the historical plane's ordering primitive and must still settle occurred-at versus recorded-at. D-18
(failure semantics) inherits the two-phase commit admission. D-03 is untouched.

**Not decided here:** what a decision record must contain for prediction error to be computable, how
completeness of linkage is verified, and what happens when an outcome never arrives — all D-12. The
relationship *vocabulary* is provisional in the same sense as ADR-0007's event types: extensible as adapters
require, subject to rules 2 and 3.

## Reversibility

High for the vocabulary, low for the constraints. Adding a structural relationship type is a registry change.
Relaxing preexistence, forward-reference prohibition or inline immutability later would not be — records
committed under the strict rules cannot retroactively acquire the guarantees, and records committed under
relaxed rules could not later be proven to satisfy them. The asymmetry again favours deciding before any
records exist.

## Validation / falsification

Revisit if:

- a genuinely structural relationship proves inexpressible under the backward-only direction rule, indicating
  rule 5's convention is too rigid for some adapter's emission order; or
- the model-participation test (rule 2) rejects an edge that is clearly structural but happens to route
  through a component that also calls a model, indicating the test needs to be scoped to the specific
  determination rather than the path; or
- `RelationshipRecorded` volume comes to dominate the ledger, suggesting too much is being discovered late
  and the capture points are wrong.

Evidence that an interpretive claim entered the historical plane *despite* P-1 through P-3 — most likely by a
structural-looking edge type whose real meaning was causal — would falsify the claim that a vocabulary
allowlist is sufficient, and would argue for per-edge provenance of how the correlation was established.

## Subsequent refinements

The provisional structural vocabulary of rule 2 has been extended by later accepted ADRs, under rule 2's
admission test and rule 3's prohibitions. The original decision and rationale are unchanged.

| Relation | Added by | Precise meaning |
|---|---|---|
| `assembled_from` | ADR-0014 rule 20 | This `ContextAssembled` was assembled from these already-committed `RecallPerformed` and live-input records |
| `decided_from` | ADR-0016 rule 7 | This exact `ContextAssembled` record supplied the model-visible input associated with this committed decision operation |
| `produced_from_context` | ADR-0016 rule 9b | This historical output was produced from this specific supplied context, by machine-verifiable request/response correlation |

All three are backward-only (rules 4–5), admitted only on machine-verifiable correlation evidence (rule 2), and
carry no truth import (rule 11). **ADR-0016 rule 23 additionally establishes that structural edges have no
automatic transitive closure**: a path through admitted edges is evidence that those edges exist, never a
newly admitted relationship and never a causal claim.

## Outcome

Pending. No implementation exists.
