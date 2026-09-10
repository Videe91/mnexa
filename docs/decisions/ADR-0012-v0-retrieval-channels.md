---
id: ADR-0012
status: accepted
date: 2026-09-10
scope: component
vision_refs:
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
spec_refs: []
supersedes: []
---

# ADR-0012 — v0 Retrieval Channel Set

**Tier: D2.** Requires approval before the Recall contract may be written.

Covers register entry **D-27**.

**Approval:** accepted by owner 2026-09-10, following three owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **A lexical/exact channel was added.** The original excluded it on the grounds that identifiers matter
   especially in the anticipated coding benchmark, so admitting it would be domain-specific tuning. **That
   reasoning was wrong** — it mistook the capability's most visible instance for its justification. Exact
   surface form is a domain-general addressing mode, distinct from meaning and from entity continuity. — rules
   1–3, T-1.
2. **Default candidate generation operates on head-as-of-N, not every version.** The original said all versions
   of an object are distinct candidates, which is true for provenance and wrong for the ordinary recall
   candidate pool. — rules 10–11, T-6, T-12.
3. **The entity channel must not settle D-04.** The original did not state the boundary between consuming an
   established identity interpretation and establishing one. — rule 6, T-13, T-14.

## Decision question

Which retrieval channels does MNEXA v0 implement, over which canonical objects, and how are their candidates
combined?

## Context

ADR-0011 fixed what a recall must *record*. It deliberately did not decide what recall *searches*, leaving the
channel field open so future routes could be added without contract change. The specification's Recall
contract (element 13) cannot be written until v0's channels are chosen.

**D-28 does not block this decision.** The cognitive-cycle snapshot question — whether one decision cycle uses
a single watermark or several — concerns how many recalls a cycle performs and at which watermarks. Each recall
binds its own N either way (ADR-0011 rule 3a), and channel choice is unaffected by how many such operations a
cycle contains. D-27 therefore proceeds.

### The selection criterion

Channels are chosen for what the **v0 memory architecture and thesis require**, not for expected benchmark
performance. Following the correction recorded in ADR-0009, a channel is not admitted because it might help
condition C beat a retrieval baseline; it is admitted because some accepted v0 element does not work without
it. If the resulting set performs no better than conventional retrieval, that is a result to report.

The v0 object model (ADR-0007) is the reference point: `ExperienceRecord`, `Entity`, and `Interpretation` with
kinds `episode`, `identity_binding` and `belief`.

## Options considered

### A — Semantic/vector retrieval only

One channel: embedding similarity over a declared text projection of each object.

Benefits: smallest possible; one index; one score type; no merge problem.

Costs: **`Entity` becomes inert.** ADR-0007 admitted Entity as a canonical object specifically because
identity persists while surface forms change (vision 2.4), and ADR-0009 kept identity bindings interpretive so
resolution could be revised. With semantic retrieval alone, an entity referenced in the ContextFrame is matched
only by surface text — which is exactly the "losing continuity because language changed" failure Entity exists
to prevent. The architecture would contain a primitive that does no work in the loop that justifies it.

### B — Semantic + exact/entity/structural

Three channels: embedding similarity, exact/lexical and identifier matching, and structural traversal over
provenance and relationships.

Benefits: entity continuity works; provenance is reachable; lexical identifiers are findable.

Costs: two of the three are not required by any accepted v0 element. Structural traversal from an already-known
item is a *lookup*, not candidate generation from a context — it answers "what supports this belief", which is
a read operation rather than a search. Exact/lexical matching is a retrieval-quality improvement with no v0
architectural element depending on it.

### C — Minimal multi-route hybrid

Semantic, entity, plus temporal/recency and/or structural/provenance as additional routes.

Benefits: closer to vision 5.6's multi-route picture.

Costs: temporal recency as a *channel* generates candidates by age irrespective of relatedness, which returns
noise unless combined with another route — its useful form is a **ranking signal**, not a candidate generator.
Adding it as a channel buys nothing the signal does not.

### Recommendation

**Three channels — semantic, lexical/exact, and entity.** They represent three genuinely different addressing
modes:

```text
meaning          →  semantic
surface form     →  lexical / exact
entity continuity →  entity
```

Structural provenance traversal is retained as a **port operation** rather than a channel, and temporal
recency as a **ranking signal** rather than a channel. No temporal, causal, provenance, prospective, graph or
learned-attention channel is added.

## Decision

*(Proposed. Not approved.)* Twelve rules.

### The three v0 channels

1. **Semantic channel — retrieval by meaning.** Candidates by embedding similarity over a declared text
   projection of the object. Operates over **`Interpretation` versions** (kinds `episode`, `belief`) and
   **`ExperienceRecord` payloads**. Channel-local evidence is a similarity score whose algorithmic meaning is
   declared under ADR-0011 rule 10.

2. **Lexical/exact channel — retrieval by surface form.** Candidates by exact or lexical surface evidence over
   the same objects. This addresses content that meaning-based retrieval does not reliably reach: names,
   identifiers, error codes, SKUs, legal clause references, quoted phrases, dates, technical terminology and
   external reference numbers. Channel-local evidence is a match kind and matched span — **not** a similarity
   score, and not comparable to one.

3. **Entity channel — retrieval by entity continuity.** Given entities present in the ContextFrame, candidates
   bound to those entities, resolved through `identity_binding` interpretations at their **head-as-of-N**
   (ADR-0011 rule 4). Operates over **`ExperienceRecord`s** reached via bindings and over **`Interpretation`
   versions** referencing the Entity. Channel-local evidence is a binding reference and match kind.

3a. **All three channels may return `ExperienceRecord`s as well as `Interpretation` versions.** Vision 5.28–5.29
   require cognition to move between compressed knowledge and raw experience; a channel set that returned only
   interpretations would make the lower rungs unreachable. Which kinds a given recall wants is filtered by the
   request's requested-kinds field (ADR-0011 rule 8).

### Not channels in v0

4. **Provenance traversal is a port operation, not a channel.** *"What evidence supports this belief"* expands
   from an already-selected item rather than generating candidates from a context, and vision 10.36's
   requirement that a claim reveal its path is a lookup. It belongs to the port surface (D-14), and its absence
   from the channel set does not make the evidence spine unreachable.

5. **Temporal recency is a ranking signal, not a channel.** It may inform the ranking stage under rule 8. It
   does not generate candidates.

6. **The entity channel consumes identity interpretations; it never establishes them.** D-04 remains
   unresolved, and this ADR does not settle it. The channel may use entity identities and `identity_binding`
   interpretations that are valid and available `AS_OF(N)`. It must **not** establish that *query identifier X
   objectively refers to Entity E* merely because it needs an entity key — identity resolution is interpretive
   under ADR-0007 and stays there.

   Concretely:

   - entity references used for recall are version-pinned or resolved `AS_OF(N)`;
   - "current head" means head-as-of-N, never current-now;
   - `identity_binding` interpretations consulted during retrieval also respect N;
   - **ambiguous or unresolved identity is never converted into certain entity membership for retrieval
     convenience.** Where resolution is ambiguous at N, the channel may generate candidates from each matching
     entity **with the ambiguity recorded**, or return none — it may not silently pick one. If ambiguity caused
     truncation, it contributes to completion status under ADR-0011 rule 11;
   - the channel owns candidate generation *from* an established entity interpretation, not the epistemic
     authority to establish that interpretation.

   **D-04 is not blocking for this channel's specification.** Candidate generation is fully specifiable
   against whatever bindings exist. What D-04 governs is how bindings come to exist and what makes two
   references the same — which determines the channel's *yield*, not its contract.

### Merging and ranking

7. **Candidates are unioned with channel attribution preserved.** An item found by both channels appears once,
   carrying attribution to **every** channel that produced it. The union happens before ranking.

8. **Candidate generation is channel-specific; final ranking is shared and declared.** Channel-local evidence
   is not comparable across channels — a cosine similarity and a binding match are different kinds of thing —
   so ordering the union requires one declared ranking policy that states how it combines them. Both the
   channel-local meanings and the combination rule are recorded (ADR-0011 rules 9–10, S-10).

9. **Deduplication collapses the same immutable version found through multiple routes**, retaining all
   channel attributions for that one candidate.

10. **Default candidate generation operates on the eligible head-as-of-N, not every historical version.**
    For a versioned interpretive object:

    ```text
    B17 v1
    B17 v2
    B17 v3   ← head AS_OF(N)
    ```

    ordinary current-state recall considers `B17 v3` **once**, rather than letting v1, v2 and v3 independently
    occupy ranking capacity. Superseded versions are distinct immutable objects for provenance and historical
    purposes, but that does not entitle them to compete in the default candidate pool.

11. **Older versions remain fully accessible and are never deleted, collapsed or rewritten.** They stay
    reachable for forensic replay, provenance traversal, historical queries, contradiction and revalidation
    work, and explicitly requested version-history retrieval. **What ADR-0012 assumes:** that non-head versions
    are reachable through explicit version-scoped requests and through provenance traversal (rule 4), both of
    which ADR-0011's request contract accommodates via its requested-kinds and scope fields. Rule 10 governs
    the *default* pool only; it grants nothing about what an explicit request may ask for.

### `AS_OF(N)` in retrieval

12. **Filtering must occur within the search, not after it.** An index may physically contain items committed
    after N. Retrieving a top-k and *then* discarding ineligible items is **not** equivalent to `AS_OF(N)`
    retrieval: the discarded items displaced eligible ones from the result. Either the search filters within
    itself, or it over-fetches and re-ranks the eligible subset, and **which strategy was used is recorded**.

13. **Entity heads resolve as-of N.** Entity-channel resolution uses `identity_binding` heads-as-of-N, so a
    later re-resolution never changes what an earlier recall would have found (ADR-0011 rules 3, 4).

### Filters, scope and evidence

14. **Filters and permissions apply inside the `AS_OF(N)` view and before ranking, and are recorded.**
    Namespace scope (D-16) is a hard filter. Where a permission or filter caused truncation, it contributes to
    the recall's completion status under ADR-0011 rule 11 — and per ADR-0011 rule 11a, normal completion never
    implies exhaustiveness.

    **`RecallPerformed` records, per recall:** the active channel set with each channel's configuration
    identity; **per-channel completion status**; and, per returned item, the attributing channel(s) and their
    channel-local evidence with declared meaning. Per-channel status matters because channels fail
    independently — a working semantic index and a failed entity index yields an incomplete result that must
    say so, not a complete-looking one.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| T-1 | Exactly three retrieval channels are active in v0 | Assert the channel registry contains `semantic`, `lexical` and `entity`, and no other enabled channel |
| T-2 | All three channels can return `ExperienceRecord`s and `Interpretation` versions | Assert each channel's admissible result kinds include both |
| T-3 | Entity resolution uses `identity_binding` head-as-of-N | Fixture where a binding was re-resolved after N; assert the recall resolves via the binding current at N |
| T-4 | Eligibility filtering occurs within the search, not after top-k | Fixture where post-N items would otherwise occupy top-k slots; assert eligible items are not displaced; assert the strategy used is recorded |
| T-5 | Every candidate carries attribution to all channels that produced it | Assert an item found by both channels appears once with both attributions |
| T-6 | The same immutable version found via multiple channels is one candidate with all attributions | Assert single occurrence; assert every producing channel's attribution is retained |
| T-12 | Default candidate generation uses head-as-of-N, and older versions stay retrievable | Assert the default pool contains at most one version per interpretive object; assert an explicit version-scoped request still resolves superseded versions; assert no superseded version is deleted or rewritten |
| T-13 | The entity channel establishes no identity | Assert no `identity_binding` is created, modified or promoted during retrieval; assert `committed_by` records no binding written on the recall path |
| T-14 | Ambiguous identity is never silently resolved | Fixture with two matching bindings at N; assert the channel does not pick one, records the ambiguity, and reflects any resulting truncation in completion status |
| T-7 | Ranking is a single declared policy over the union | Assert one ranking policy identity per recall; assert the combination rule for channel-local evidence is declared |
| T-8 | Channel-local evidence carries declared algorithmic meaning | Assert each channel's evidence type has a definition (ADR-0011 S-10) |
| T-9 | Per-channel completion status is recorded | Fixture failing one channel; assert overall status is incomplete and the failing channel is identified |
| T-10 | Filters and permissions apply before ranking, inside the `AS_OF(N)` view | Assert filter application precedes ranking; assert no filtered item influences rank positions |
| T-11 | Namespace scope is enforced as a hard filter | Assert no item outside the request's namespace can be returned |

## Evidence and rationale

**The entity channel is the only one this ADR argues is architecturally required, and the argument does not
depend on performance.** ADR-0007 admitted `Entity` as one of three canonical objects on the strength of
identity continuity across surface-form change, and ADR-0009 kept bindings interpretive so resolution stays
revisable. If no retrieval route consults bindings, none of that machinery participates in the loop: entities
would be written and never read, and the object would be justified by a capability v0 never exercises. Either
the entity channel exists or `Entity` should not have been a primitive. That is a coherence argument about the
accepted object model, and it would hold even if the channel turned out to help nothing.

**The semantic channel needs no argument beyond necessity.** Without it there is no content-addressed retrieval
at all, and the request's intent field would have nothing to act on.

**Rule 10's head-as-of-N default is about ranking capacity, not about truth.** Every version of an interpretive
object is a real immutable object, and ADR-0005 exists to keep them addressable forever. But letting `B17` v1,
v2 and v3 each compete for slots in a budgeted result would spend the budget on the object's own history rather
than on distinct intelligence, and would surface superseded interpretations alongside current ones with nothing
but rank to distinguish them. The default pool takes the head; everything else stays reachable by explicit
request and by provenance traversal, which is where historical versions are actually wanted.

**Rule 6 keeps the entity channel a consumer.** The channel needs an entity key, and the shortest path to one
is to resolve an ambiguous identifier and proceed. That would make retrieval an identity-establishing
operation, which ADR-0007 placed firmly on the interpretive plane and D-04 has not yet specified. Recording the
ambiguity and declining to resolve it costs recall quality and preserves the boundary; T-14's two-binding
fixture is the test.

**Two demotions keep the set honest.** Provenance traversal *feels* like a channel because vision 5.8 describes
spreading activation, but the v0 form of that requirement is answering "why do we believe this", which starts
from a known item. Calling it a channel would inflate the set without adding a candidate-generation route.
Recency is the reverse case: genuinely useful, but as a signal. A recency *channel* returns the most recent
items regardless of relatedness, which is noise, and combining it with relatedness is exactly what a ranking
signal does.

**Rule 10 is the subtle one.** Retrieving a top-k and filtering afterwards passes every naive eligibility check
— every returned item satisfies `commit_sequence ≤ N` — while producing a different result than `AS_OF(N)`
retrieval would, because ineligible items consumed slots that eligible ones should have occupied. This is the
same class of error ADR-0011 rule 3 identified for ranking inputs, arriving through result cardinality instead.
T-4's fixture is the specific test.

**Rule 8's shared ranking is a consequence of ADR-0011's honesty requirements rather than a preference.** Since
S-10 and S-11 forbid a retrieval score from becoming an epistemic quantity and require declared meanings,
channel-local scores cannot simply be normalised together and treated as comparable relevance. Making the
combination an explicit declared policy is what keeps the comparison auditable instead of emergent.

**The lexical channel's exclusion was an error, and the error is instructive.** The original argued that since
identifiers matter especially in the anticipated coding domain, admitting a lexical channel would be
domain-specific tuning — the inadmissible reasoning ADR-0009 withdrew. That inverted the test. ADR-0009's rule
forbids selecting architecture by *expected benchmark outcome*; it does not forbid a capability because one
domain displays it prominently. Exact surface form is present in every domain — names, error codes, SKUs, legal
clause references, quoted phrases, dates, external reference numbers — and semantic similarity does not
reliably reach it, nor does entity continuity, which covers only what has been resolved into an Entity.

The correct framing is that the three channels are three **addressing modes**, not three heuristics: content
can be sought by what it means, by how it is literally written, or by which persistent thing it concerns. A
retrieval layer missing one of those modes has a structural gap, and the coding case is an instance of the gap
rather than its justification.

## Consequences

**Easier:** entity continuity actually functions; the channel set is small enough to reason about; adding
channels later needs no contract change; recall evidence stays interpretable because only two evidence types
exist.

**Harder:** two indexes must be maintained and both must respect `AS_OF(N)` internally; the ranking policy must
combine incomparable evidence types explicitly rather than implicitly; per-channel completion adds bookkeeping.

**Newly required:** a channel registry; a declared text projection per object kind for the semantic index; a
declared ranking policy combining channel-local evidence; per-channel completion status; in-search eligibility
filtering.

**Constrained:** D-14 (port surface) gains provenance traversal as a distinct operation, and must expose
version-scoped requests so rule 11's reachability holds. D-16's namespace scope becomes a hard retrieval filter
(T-11). **D-04 is not blocked and does not block**: the entity channel is fully specifiable against whatever
bindings exist, while D-04 governs how bindings arise and therefore the channel's yield. D-13 is unaffected —
it consumes the returned-item contract regardless of which channels produced the items.

**No new durable decision uncovered.** The text projection used for embedding and the ranking policy are both
pinned configuration under ADR-0011 rules 2b and 5, recorded by identity rather than decided here.

**YAGNI check.** No learned attention, graph database, prospective memory, cross-agent recall, causal or
procedural routes are introduced. No accepted v0 invariant requires any of them.

## Reversibility

High. Adding a channel is a registry change plus an evidence type, and ADR-0011's per-item channel attribution
was designed for it. Removing one would be harder, since recorded evidence would reference a channel no longer
defined — which argues for the smaller set now.

## Validation / falsification

Revisit if:

- the entity channel returns almost nothing because identity bindings are sparse in practice, which would
  question whether `Entity` earns its place as a primitive rather than whether the channel does; or
- the lexical channel proves to duplicate the semantic channel's results almost entirely across domains,
  which would suggest the addressing modes are less distinct in practice than in principle; or
- combining two incomparable evidence types in one ranking policy proves arbitrary in practice, suggesting
  channel-specific result quotas rather than a merged ranking.

Evidence that v0 performs identically with the entity channel disabled would be a real finding about this
architecture and should be reported as one, not treated as a reason to add channels until a difference appears.

## Outcome

Pending. No implementation exists.
