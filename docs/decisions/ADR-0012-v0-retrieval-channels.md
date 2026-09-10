---
id: ADR-0012
status: proposed
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

**A narrowed form of B: two channels — semantic and entity.** Structural provenance traversal is retained as a
**port operation** rather than a channel, and temporal recency as a **ranking signal** rather than a channel.
Exact/lexical matching is **not in v0** but remains addable under ADR-0011's channel field.

## Decision

*(Proposed. Not approved.)* Twelve rules.

### The two v0 channels

1. **Semantic channel.** Retrieves candidates by embedding similarity over a declared text projection of the
   object. Operates over **`Interpretation` versions** (kinds `episode` and `belief`) and **`ExperienceRecord`
   payloads**. Its channel-local evidence is a similarity score whose algorithmic meaning is declared under
   ADR-0011 rule 10.

2. **Entity channel.** Given entities present in the ContextFrame, retrieves candidates bound to those
   entities. Resolution runs through `identity_binding` interpretations at their **head-as-of-N**
   (ADR-0011 rule 4). Operates over **`ExperienceRecord`s** reached via bindings and over **`Interpretation`
   versions** that reference the Entity. Its channel-local evidence is a binding reference and match kind, not
   a similarity score.

3. **Both channels may return `ExperienceRecord`s as well as `Interpretation` versions.** Vision 5.28–5.29
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

6. **Exact/lexical matching is not in v0**, and no accepted v0 element requires it. It remains addable later
   through ADR-0011's channel field without contract change.

### Merging and ranking

7. **Candidates are unioned with channel attribution preserved.** An item found by both channels appears once,
   carrying attribution to **every** channel that produced it. The union happens before ranking.

8. **Candidate generation is channel-specific; final ranking is shared and declared.** Channel-local evidence
   is not comparable across channels — a cosine similarity and a binding match are different kinds of thing —
   so ordering the union requires one declared ranking policy that states how it combines them. Both the
   channel-local meanings and the combination rule are recorded (ADR-0011 rules 9–10, S-10).

9. **Deduplication is by version identity, never object identity.** Two different versions of one object are
   distinct candidates, not duplicates. Whether the policy collapses them to head-as-of-N is a policy choice,
   declared and recorded in the evidence.

### `AS_OF(N)` in retrieval

10. **Filtering must occur within the search, not after it.** An index may physically contain items committed
    after N. Retrieving a top-k and *then* discarding ineligible items is **not** equivalent to `AS_OF(N)`
    retrieval: the discarded items displaced eligible ones from the result. Either the search filters within
    itself, or it over-fetches and re-ranks the eligible subset, and **which strategy was used is recorded**.

11. **Entity heads resolve as-of N.** Entity-channel resolution uses `identity_binding` heads-as-of-N, so a
    later re-resolution never changes what an earlier recall would have found (ADR-0011 rules 3, 4).

### Filters, scope and evidence

12. **Filters and permissions apply inside the `AS_OF(N)` view and before ranking, and are recorded.**
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
| T-1 | Exactly two retrieval channels are active in v0 | Assert the channel registry contains `semantic` and `entity` and no other enabled channel |
| T-2 | Both channels can return `ExperienceRecord`s and `Interpretation` versions | Assert each channel's admissible result kinds include both |
| T-3 | Entity resolution uses `identity_binding` head-as-of-N | Fixture where a binding was re-resolved after N; assert the recall resolves via the binding current at N |
| T-4 | Eligibility filtering occurs within the search, not after top-k | Fixture where post-N items would otherwise occupy top-k slots; assert eligible items are not displaced; assert the strategy used is recorded |
| T-5 | Every candidate carries attribution to all channels that produced it | Assert an item found by both channels appears once with both attributions |
| T-6 | Deduplication is by version identity | Assert two versions of one object remain distinct candidates; assert any collapse is a declared policy recorded in evidence |
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

**Exact/lexical matching was the closest call.** Embedding retrieval is known to miss precise identifiers, and
the first experimental domain is likely coding — where identifiers matter. That is precisely why it is excluded:
admitting a channel because it suits the anticipated benchmark domain is domain-specific tuning of a substrate
required to stay domain-general (vision 10.12, 10.64), and it is the same inadmissible reasoning ADR-0009
withdrew. If v0 evidence later shows semantic retrieval failing on identifier-shaped queries across domains,
that is an architectural finding that justifies adding the channel then.

## Consequences

**Easier:** entity continuity actually functions; the channel set is small enough to reason about; adding
channels later needs no contract change; recall evidence stays interpretable because only two evidence types
exist.

**Harder:** two indexes must be maintained and both must respect `AS_OF(N)` internally; the ranking policy must
combine incomparable evidence types explicitly rather than implicitly; per-channel completion adds bookkeeping.

**Newly required:** a channel registry; a declared text projection per object kind for the semantic index; a
declared ranking policy combining channel-local evidence; per-channel completion status; in-search eligibility
filtering.

**Constrained:** D-14 (port surface) gains provenance traversal as a distinct operation. D-16's namespace scope
becomes a hard retrieval filter (T-11). D-13 is unaffected — it consumes the returned-item contract regardless
of which channels produced the items, which is why it did not need to precede this decision.

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
- semantic retrieval proves unable to find identifier-shaped content across multiple domains, which would
  justify adding the lexical channel on domain-general evidence; or
- combining two incomparable evidence types in one ranking policy proves arbitrary in practice, suggesting
  channel-specific result quotas rather than a merged ranking.

Evidence that v0 performs identically with the entity channel disabled would be a real finding about this
architecture and should be reported as one, not treated as a reason to add channels until a difference appears.

## Outcome

Pending. No implementation exists.
