---
id: ADR-0005
status: accepted
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/02-cognitive-architecture.md
spec_refs: []
supersedes: []
---

# ADR-0005 — Version Pinning of Interpretive Derivation Edges

**Tier: D3.** The register classified D-21 as D2. It is raised here to D3 because it does not sit beside
ADR-0002 but *inside* it: ADR-0002 I-9a defines grounding as a traversal over these edges, so their
mutability determines what an accepted constitutional invariant actually asserts. Requires explicit owner
approval.

Covers register entry **D-21**.

**Approval:** accepted by owner 2026-09-10, following two owner-directed mechanical clarifications made
while the ADR was still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **Strict preexistence replaces timestamp ordering.** The original L-7 said only that a derivation may not
   reference a future version. That is insufficient where versions are created in the same transaction or
   logical operation, or where timestamps can collide. Ordering is now defined by *commit*, and an explicit
   DAG check is retained as defence in depth rather than relying on ordering alone. — rule 5, invariants
   L-7/L-8/L-10.
2. **The derivation edge set is part of the version's content identity.** The original left open whether a
   version's provenance could be amended after commit. It cannot: source identities, edge types and the
   provenance relationship set are covered by the version's content hash, and re-derivation produces a new
   version rather than rewriting an existing one's provenance. — rule 6, invariants L-9/L-4.

## Decision question

Should interpretive→interpretive provenance/derivation edges be pinned to immutable source versions rather
than mutable object heads?

## Context

ADR-0002 settled two adjacent questions and left this one open:

- I-5 pins **historical→interpretive** references to immutable version identity.
- Rule 11 permits **transitive** provenance, so a principle may reach historical records through patterns
  rather than citing episodes directly.

It never said whether the interpretive→interpretive edges that transitivity traverses are themselves pinned.
The gap was recorded as D-21 rather than resolved, because the amendment that produced it concerned
grounding, not edge mutability.

The question is load-bearing in a way that is easy to miss. ADR-0002 I-9a checks grounding by traversing
derivation edges and asserting the traversal reaches the historical plane. If those edges float, the
traversal is evaluated against whatever the graph looks like *now* — so "this principle is grounded" is a
statement about the present, not about the derivation that actually occurred. The invariant would still pass.
It would simply be checking something other than what it appears to check.

Two vision requirements bear directly:

- 3.20 requires every higher-order object to retain an evidence spine answering *why do we believe this*.
- 3.21 requires that when a contradiction arrives, MNEXA can determine what the contradiction affects — which
  presupposes knowing which abstractions actually rest on the contradicted material.

### The concrete failure

```text
Pattern X v1        →  Principle P derived from it
Pattern X superseded by v2 (boundary conditions corrected)
```

Under floating edges, P now appears to derive from X v2 — material P's derivation never saw. If X v2
narrows the pattern such that P no longer follows, nothing detects it: P's provenance looks healthy, and the
grounding check passes. The evidence spine has silently become a claim about the current state of the graph
rather than a record of derivation.

## Options considered

### Option A — Pin derivation edges to immutable versions

A derivation edge references a specific immutable interpretive **version**. Objects continue to carry a
mutable **head** pointer; a pinned edge reaches the current interpretation indirectly, by resolving the
referenced version to its parent object and reading that object's head.

Benefits: provenance means what it says — the traversal reproduces the derivation that occurred. Staleness
becomes computable rather than invisible: for any edge pinned to version *v*, comparing *v* against its
object's head answers "has my basis moved?" in one step, which is exactly the query 3.21 needs. Makes
ADR-0002 I-9a check the thing it appears to check. Uniform with I-5, so there is one rule for provenance
references rather than two.

Costs: an abstraction does not automatically inherit improvements to its supporting patterns; something must
decide when to re-derive. Retention pressure grows, since pinned versions cannot be discarded while
referenced — the same obligation ADR-0002 I-6 already created for historical references.

Reversibility: high toward B (drop the pin, keep the object reference) and low back again — floating edges
never recorded which version was actually used, so pinning cannot be reconstructed retroactively.

### Option B — Float derivation edges to object heads

A derivation edge references the interpretive object; resolution always yields its current version.

Benefits: simplest representation; abstractions automatically track improvements to their basis; no
retention obligation on old versions; no re-derivation machinery.

Costs: destroys the evidence spine's meaning, as shown above. Makes 3.21's contradiction-propagation query
unanswerable — there is no record of which version an abstraction rested on, so there is no way to determine
which abstractions a contradicted version affects. Silently weakens ADR-0002 I-9a. Also reintroduces, one
plane up, exactly the defect ADR-0002 I-5 was written to prevent: a reference whose meaning changes when
something else is revised.

Reversibility: low in the direction that matters. Every derivation recorded under B is permanently missing
the version it used.

### Option C — Dual edges: pinned provenance plus a separate floating discovery edge

Maintain two edge types — a pinned `derived_from_version` for provenance, and a separate floating
`current_basis` for discovering the present interpretation.

Benefits: provenance is preserved exactly as in A, while "what does this rest on now" is a single hop rather
than two.

Costs: the floating edge adds no capability. Under Option A the current interpretation is already reachable —
pinned version → parent object → head — and staleness is already computable by comparing the pin to that
head. So C buys one hop of convenience in exchange for a second edge that must be kept synchronized with the
first, and a new class of defect when the two disagree (a `current_basis` pointing at an object the
`derived_from_version` never came from). It is redundant state on the exact path where ADR-0002 chose
integrity over convenience.

Reversibility: high, but the synchronization burden is permanent while it exists.

## Decision

**Recommendation: Option A.** *(Proposed. Not approved.)*

Five rules.

1. **Derivation edges are version-pinned.** Every interpretive→interpretive provenance or derivation edge
   references an immutable version identity — a version ID or content hash — never an object identifier that
   resolves to a head.
2. **Heads remain, on objects, for discovery.** Interpretive objects keep their mutable head pointer from
   ADR-0002 rule 4. The current interpretation of a pinned basis is reached by resolving the pinned version
   to its parent object and reading that object's head. No separate floating edge is introduced.
3. **Supersession never rewrites existing edges.** Creating a new version of an object leaves every existing
   derivation edge pointing where it pointed. Supersession moves a head; it does not retarget provenance.
4. **Staleness is computed, not stored.** An abstraction is *stale with respect to a basis* when the pinned
   version is not that object's current head. This is derived on demand from rules 1–3; no separate staleness
   flag is maintained, so it cannot drift from the graph.
5. **Strict preexistence.** A derivation/provenance edge may reference only an immutable source version that
   was **already committed** before the derived version itself is committed. A derived version may not cite:

   - itself;
   - an uncommitted version;
   - a concurrently-created version whose prior commit is not established;
   - a version committed after it.

   The required order is therefore strict:

   ```text
   source version committed
       → derived version may reference source
   ```

   Ordering is established by commit, not by wall-clock timestamp, because timestamps may collide or be
   assigned before commit. This makes derivation ancestry a DAG *by construction*. An explicit cycle/DAG
   integrity check is retained as defence in depth (L-8) rather than relying on ordering alone.

6. **The derivation edge set is part of the version's content identity.** A derived version's provenance is
   immutable and covered by that version's content hash. Once committed, none of the following may change
   for that version:

   - the source version identities it cites;
   - the derivation edge types and their semantics;
   - the provenance relationship set as a whole.

   If an interpretation is re-derived against newer source versions, that produces a **new version** of the
   derived object. It never rewrites the provenance of the historical derived version.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| L-1 | Every interpretive→interpretive derivation edge carries an immutable version identity | Assert each such edge's reference type ∈ {version_id, content_hash}; assert zero edges referencing a bare object identifier |
| L-2 | No derivation edge references an object head or a "current" alias | Assert no edge target resolves through a mutable pointer; attempt resolution twice across an intervening supersession and assert identical results |
| L-3 | Every derivation edge resolves to an existing immutable version | Resolve all edges; assert none dangling |
| L-4 | Supersession does not retarget existing derivation edges | Hash the outgoing derivation-edge set of each existing version before and after a supersede operation elsewhere in the graph; assert unchanged |
| L-5 | Staleness is computable for every derivation edge | For each edge, assert the referenced version's parent object and that object's head both resolve |
| L-6 | Provenance traversal is stable over time | Hash the traversal output for an unchanged object; re-run after an unrelated supersession elsewhere; assert identical |
| L-7 | Every referenced source version was committed before the referencing version was committed | At commit, assert each source's state is `committed` and its commit sequence number is strictly less than the derived version's; reject the commit otherwise. Use the commit sequence, never wall-clock time |
| L-8 | Derivation ancestry contains no cycle | Topological sort over all derivation edges independently of commit ordering; assert no cycle. Retained as defence in depth so a defect in sequence assignment cannot silently admit a cycle |
| L-9 | A version's derivation edge set is covered by its content identity | Recompute the version content hash including source identities, edge types and the full relationship set; assert it matches the stored hash |
| L-10 | No version cites itself | Assert no derivation edge has identical source and target version identity |

L-6 is the end-to-end property the whole decision exists for: the answer to *why do we believe this* does not
change unless the derivation itself changes.

L-7 and L-8 are deliberately redundant. L-7 makes cycles impossible by construction through strict commit
ordering; L-8 detects one anyway. The redundancy is the point — L-7's guarantee depends on commit sequence
numbers being assigned correctly, and a defect there would otherwise admit a cycle with no check standing
between it and ADR-0002 I-12's traversal, which assumes termination.

L-9 is what makes rule 6 enforceable rather than declarative. Without provenance inside the content hash, a
version's edge set could be amended after commit while its identity stayed the same, which would defeat L-6
and reintroduce mutable provenance one level below where ADR-0002 I-5 blocked it.

## Evidence and rationale

The owner's stated expectation entering this decision was that derivation edges should be pinned while
mutable heads exist for discovering the current interpretation. That expectation is adopted, but it was
tested rather than assumed, and the analysis refines its second half.

The first half survives scrutiny easily. Option B is not a viable competitor once the failure case is
written out: it makes 3.21's contradiction-propagation query unanswerable and quietly changes what ADR-0002
I-9a asserts. Its apparent benefit — abstractions automatically tracking improvements to their basis — is
the same mechanism as its defect. Automatic tracking *is* silent retargeting.

The second half needed adjustment. "Mutable heads for discovery" is satisfied by heads living on objects,
which ADR-0002 rule 4 already provides; it does not require a separate floating *edge*. Option C was
constructed to represent the strongest reading of that expectation and then rejected on its merits: the
floating edge adds no reachability that Option A lacks, adds no staleness capability that Option A lacks,
and introduces a synchronization invariant that can fail. Rule 2 therefore keeps the head and declines the
extra edge.

Rule 4 follows the same reasoning one level down. A stored staleness flag would be a second representation
of a fact already implied by the graph, and second representations drift. Computing staleness from the pin
and the head means it cannot be wrong.

The honest cost of Option A is rule-shaped rather than technical: pinning creates a re-derivation question
that floating edges never raise, because under B abstractions silently update and nobody has to decide
anything. That is the cost of making derivation auditable, and it is the same trade ADR-0002 accepted when
it chose append-and-supersede over editing. It is recorded below as a follow-on decision rather than
resolved here.

## Consequences

**Easier:** answering *why do we believe this* with a reproducible traversal; determining what a contradicted
pattern version affects (3.21); auditing whether an abstraction was derived before or after a correction;
detecting stale abstractions with a single comparison.

**Harder:** abstractions do not improve automatically when their basis improves; retention obligations extend
to interpretive versions referenced by other interpretive versions, not only those referenced by history.

**Newly required:** stable version identity on every interpretive version, including those never referenced
from the historical plane; a total commit ordering (commit sequence numbers, not timestamps) sufficient to
evaluate L-7; a commit-time admission check that rejects a derived version citing an uncommitted or
concurrently-created source; version content hashing that covers the derivation edge set.

**Constrained:** ADR-0002 I-9a now traverses a stable graph, so grounding is a statement about the derivation
that occurred rather than about the present. ADR-0002 I-12's acyclicity is now guaranteed twice over — by
construction through L-7 and by explicit check through L-8. Commit becomes a two-phase operation for derived
versions, since admission depends on the commit state of every cited source. D-19
(forgetting) inherits an additional retention obligation and will have to reckon with it, as flagged in
ADR-0002.

**Newly discovered decision — recorded, not decided here:** rule 4 makes staleness *detectable* but says
nothing about what to do when detected. Whether v0 re-derives stale abstractions during consolidation,
flags them, weakens their confidence, or ignores staleness entirely is a separate durable decision. It is
recorded as **D-22 — re-derivation policy for stale abstractions** and is deliberately not settled here,
since deciding it silently would repeat the failure that produced D-21.

## Reversibility

Asymmetric, in the same direction as ADR-0002. Moving from pinned to floating later is trivial and loses
only the ability to ask historical questions going forward. Moving from floating to pinned is impossible for
existing data, because a floating edge never recorded which version was used. This asymmetry is the main
argument for deciding it before any derivation edges exist rather than after.

## Validation / falsification

Revisit if:

- the retention obligation on pinned interpretive versions grows unmanageable at v0 scale, which would pull
  D-19 forward rather than reverse this decision; or
- re-derivation proves so routine that nearly every abstraction is stale nearly always, which would suggest
  the pinning granularity is wrong — perhaps pinning should attach to a stable *claim* within a version
  rather than to the whole version; or
- traversal cost at depth makes L-6 impractical, requiring a materialized provenance summary that would then
  need its own consistency invariant.

Evidence that a contradiction propagated incorrectly *despite* pinned edges would falsify the claim that
pinning is sufficient for 3.21, and would indicate the contradiction machinery, not the representation,
needs strengthening.

## Outcome

Pending. No implementation exists.
