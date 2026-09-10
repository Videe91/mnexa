---
id: ADR-0014
status: accepted
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/09-trust-identity-privacy-epistemic-immune-system.md
spec_refs: []
supersedes: []
---

# ADR-0014 — Activation and Context Trace

**Tier: D3 (constitutional).** Requires explicit owner approval.

Covers register entry **D-13** as narrowed by the approved split. Credit attribution is **D-30** and is not
touched here.

**Approval:** accepted by owner 2026-09-10, following three owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **Presentation is segment-based, not one-to-one with memory items.** The original implicitly modelled each
   presented memory as a context element, which fails the moment a segment synthesises several memories or a
   memory contributes to several segments. — rules 7a–7c, V-21 … V-24.
2. **The exactness boundary is the canonical model-request input.** The original stated the boundary but did
   not enumerate what is included, what is explicitly not claimed, or when a serialization detail becomes
   semantically relevant. — rules 8, 8a–8c, V-25.
3. **The trace must not become an authorization side channel.** The original said nothing about who may read
   the trace, leaving suppressed protected content recoverable through provenance. — rule 18a, V-26 … V-28,
   and registered dependency **D-32**.

## Decision question

What immutable historical evidence must MNEXA preserve about context assembly so that a later investigator can
reconstruct exactly which information was made available to the reasoning seat, where it came from, and which
returned memories were excluded — without making unsupported claims about causal influence?

## Context

The constitutional boundary this ADR sits inside:

```text
DURABLY ELIGIBLE          ADR-0010 / ADR-0013
RETURNED BY RECALL        ADR-0011 / ADR-0012
SELECTED / SUPPRESSED / PRESENTED    ← ADR-0014
ACTUALLY INFLUENCED DECISION         ✗ not here — D-30
CONTRIBUTED TO OUTCOME               ✗ not here — D-30
```

ADR-0011 established what a recall returned and deliberately stopped there. ADR-0013 requires live-supplied and
recall-supplied knowledge to stay distinguishable in the trace, and left that design here. ADR-0007 N-11
requires any projection that influenced cognition to be capturable as historical evidence — context assembly is
the last such projection before the reasoning seat.

## Options considered

### A — Per-memory activation events

One `MemoryActivated` or `MemorySuppressed` record per item.

| Property | Assessment |
|---|---|
| Fine-grained observability | Good — each item has its own record |
| Partial-write risk | **Severe** — N items means N commits; a failure midway leaves an incomplete disposition set in an append-only ledger that cannot be repaired |
| Ordering | Commit sequence orders the *records*, which is not the *presentation order* within the context. A second ordering must be carried anyway |
| Atomicity | **None** — no single record represents "the context" |
| Duplication | Budget, policy, model configuration repeated on every item record |
| Reconstruction of the final request | **Impossible** — activations name items, not the assembled artefact: system instructions, ordering, transformations and live input are all absent |

The last row is disqualifying. Option A cannot answer the central question at all.

### B — Context snapshot only

One immutable `ContextAssembled` record holding the exact final context.

Reconstruction of the final input is complete. Returned-but-suppressed items are *partially* recoverable by
differencing ADR-0011's returned set against the presented set — but that yields no **reason**, so a
budget drop, a policy exclusion and a permission denial are indistinguishable. Regret boundary two exists as a
set but not as an explanation.

### C — Atomic context trace

One primary immutable `ContextAssembled` record representing the assembly operation atomically: the final
context, provenance of its segments, disposition of every returned memory, selection and suppression evidence,
and transformation evidence. `MemoryActivation` becomes a **projection** over that record.

**Recommendation: C.** Context assembly is the atomic fact that must be reconstructable, and every per-item
question is answerable as a view over it.

### Applying ADR-0007's lifecycle test

`ContextAssembled` is an **ExperienceRecord event type**, not a canonical object. `Context`, `Activation`,
`CognitiveCycle` and `Recall` remain non-primitives: none is versioned, superseded or revised, so none has a
lifecycle. ContextFrame remains a projection.

## Decision

Twenty rules. *(Proposed. Not approved.)*

### Stage vocabulary

1. **Four stages, never used interchangeably.**

   | Stage | Definition | Owner |
   |---|---|---|
   | `RETURNED` | The item appeared in a `RecallPerformed` result | ADR-0011 |
   | `SELECTED` | Context assembly chose the returned item for **attempted** inclusion | ADR-0014 |
   | `PRESENTED` | Some representation derived from the item **actually appeared** in the final input supplied to the reasoning seat | ADR-0014 |
   | `SUPPRESSED` | The returned item was not ultimately presented | ADR-0014 |

2. **`SELECTED` does not imply `PRESENTED`.** An item selected and then removed by budget, authorization,
   serialization failure or any other operational cause is **suppressed**, not presented. Selection is an
   attempt; presentation is an outcome.

3. **"Activation" is retired as a normative term.** `PRESENTED` is normative. `MemoryActivated` becomes a
   **projection** over `ContextAssembled` — the set of returned items whose disposition is `PRESENTED` — and is
   a convenience view, not an independent historical record.

   The word carries connotations MNEXA cannot observe: internal attention, comprehension, reliance, causal
   influence. None is establishable from outside the model. Where the vision speaks of *active memory* (5.12,
   5.40), the v0 reading is the presented set.

   **This refines ADR-0007's provisional event-type list**, which named `MemoryActivated`. That list was
   explicitly left open (ADR-0007 amendment 2), so this is permitted evolution rather than supersession — but
   it is surfaced here for approval, not applied silently.

### The atomic record

4. **`ContextAssembled` is an `ExperienceRecord` event type and the primary trace record.** Its commit asserts
   **one completed assembly result**.

5. **No half-written context is ever exposed.** A committed record never shows some dispositions present and
   others missing. If assembly fails before a valid final context exists, the failure is recorded separately or
   with an explicit failed/incomplete assembly status — a partial context is never represented as the final
   model input.

6. **Assembly and invocation are distinct facts.** *This context was assembled* does not imply *the model
   successfully processed it*. A subsequent invocation failure leaves the assembly record historically valid.

### The final input

7. **The record preserves enough to reconstruct the decision-affecting input actually supplied**, including
   where applicable: system, developer and runtime instructions visible to the model; user and task input; live
   working evidence; tool results; recalled memory representations; the **ordering** of segments; segment
   boundaries and types; truncation and transformation; tool and capability definitions exposed to the model;
   and context budget actually consumed.

7a. **The presentation unit is the context segment, not the memory item.** A segment may derive from one
   recalled memory version, an excerpt of one, **several** memories, live working evidence, user or task input,
   system or runtime instructions, tool definitions, deterministic derived material, or model-generated
   transformed material. Symmetrically, **one memory may contribute to more than one segment**.

7b. **`ContextAssembled` carries an ordered final-segment manifest.** For each presented segment it preserves,
   where applicable: a stable segment identity within the trace; its exact ordered position; the exact
   recoverable presented representation; the source category; version-pinned source references wherever durable
   sources exist; **all** source references where the segment derives from multiple inputs; transformation or
   projection provenance; and the relevant transformation policy or model identity.

7c. **Returned-item disposition is kept separately from the segment manifest**, and the mapping between them is
   many-to-many:

   ```text
   recall returned M7, M8, M9

   M7  SELECTED → PRESENTED via segment S3
   M8  SELECTED → PRESENTED via segment S4
   M9  SELECTED → PRESENTED via segment S4      (S4 synthesises M8 + M9)
   ```

   Where a selected item contributes only partially — through clipping, excerpting or transformation — that
   partial relationship is preserved rather than forced into an all-or-nothing item model.

   **This establishes provenance of presented material and nothing more.** It does not imply that M8 or M9
   influenced the eventual decision; that inference belongs to D-30.

   The record remains atomic: one commit, one completed assembly result (rules 4–5).

8. **The exactness boundary is the canonical model-request input.** MNEXA preserves the exact **semantically
   relevant** request it supplied to the reasoning provider or runtime, in a canonical recoverable
   representation whose meaning does not depend on future serializers or prompt templates.

8a. **Included, where applicable:** ordered model-visible messages and segments; system, developer and runtime
   instructions supplied to the model; user and task input supplied; recalled MNEXA material supplied; live
   evidence supplied; tool and capability schemas exposed to the model; model identity and version; generation
   and decoding configuration relevant to output; **context-assembly policy and configuration identity**; and
   transformations already applied before submission.

   The assembly policy identity is what later lets a debugger distinguish *historical input replay* from
   *re-executing today's assembly logic* — the same distinction ADR-0011 rule 15 draws for retrieval.

8b. **Not required and not claimed:** transport-level HTTP or TLS byte layout where semantically irrelevant;
   provider-private prompt rewriting; provider KV-cache state; hidden model activations; hidden
   chain-of-thought; and other provider internals MNEXA cannot observe.

   The historical assertion is **"MNEXA submitted this canonical request"**, never *"MNEXA knows the provider's
   internal cognitive representation"*.

8c. **A serialization detail that changes provider-visible semantics is semantically relevant** and is
   captured. The exclusion in 8b is scoped to details that do not affect meaning; it is not a licence to drop
   anything the provider actually reads.

9. **Content is recoverable, not merely hashed.** ADR-0011 rules 2a–2c apply unchanged. A later change to
   rendering, serialization, prompt templates, tokenizers, assembly logic or memory formatting **must not alter
   what a historical `ContextAssembled` says was presented**.

### Memory representation

10. **Presented memory is version-pinned.** If `B17 v4` is included, the trace references `B17 v4` — never
    `B17 current`, never *whatever the head is now*.

11. **Excerpts and renderings preserve both halves.** Where only an excerpt, rendering, summary or other
    transformation of `B17 v4` is presented, the record preserves **both** the provenance to `B17 v4` **and**
    the exact recoverable representation actually presented. A historical representation is never
    reconstructed by re-running today's rendering logic.

### Transformations

12. **Deterministic transformation** — clipping, formatting, field selection, rendering, compression — records
    the transformation policy and configuration identity, plus the exact resulting presented content.

13. **Model-generated transformation** — summarization or any model-produced rendering — records model
    attribution and provenance under ADR-0002 rules 8–9, counts as model compute under ADR-0003 rules 1–4 and
    J-5, and preserves the exact produced representation. **The transformed text is not grounded merely because
    its source memory was grounded**: a model summary of a grounded belief is attributed content, and grounding
    does not survive rewriting. If such a transformation becomes a durable Interpretation, normal interpretive
    authority and versioning apply — it is never silently promoted.

### Provenance of segments

14. **Every context segment carries a provenance channel**, distinguishing at least: `persistent_recall`,
    `user_task_input`, `live_observation`, `system_instruction`, `derived_transform`.

15. **Live evidence is never mislabelled as recalled memory.** ADR-0013 rules 6a–6c require the distinction to
    survive. A live tool result received after the cycle watermark may legitimately be presented; if that same
    result was also committed to MNEXA after N, the trace must still assert *this arrived live during the
    cycle*, never *MNEXA remembered it*.

### Multiple recalls and disposition

16. **The presented set is not the union of recall results.** A cycle may contain several `RecallPerformed`
    operations, all at the same cycle watermark (ADR-0013). The record preserves which returned items came from
    which recall where needed for reconstruction, and makes each item's **final disposition** observable —
    items may be selected, suppressed, transformed, deduplicated, dropped for budget, or excluded by current
    authorization.

17. **Suppression reasons are operational, not semantic verdicts.** The vocabulary records what the system did:
    `excluded_by_budget` · `excluded_by_policy_rule <id>` · `duplicate_of <item>` · `permission_denied` ·
    `stale_policy_excluded` · `serialization_failure` · `lower_ranked_under_policy <id>`. Reasons should be
    reproducible from declared policy where possible.

    A label such as *irrelevant*, *wrong* or *unimportant* may be recorded **only** as *policy P classified
    this item as irrelevant* — an attributed classification. MNEXA never establishes irrelevance as truth. This
    is the same prohibition ADR-0008 rule 11 applied to relation semantics and ADR-0011 rule 10 to retrieval
    scores.

### Authorization and freshness

18. **Presentation-time authorization is a hard boundary.** No durable memory item denied by the applicable
    presentation-time authorization boundary may appear in the final context. A memory may legitimately be
    `RETURNED` and then `SUPPRESSED` with `permission_denied` because authorization changed after the cycle's
    watermark — ADR-0013 rule 8 permits exactly this, and the trace must make it visible. The derived-revocation
    mechanism is **D-29** and is not designed here.

18a. **The trace is never an authorization side channel.** Historical observability must never grant broader
    access to information than the underlying information permits.

    `ContextAssembled` may contain or reference sensitive persistent memories, suppressed memories, live tool
    results, user data, system instructions and other protected material. **A principal must not gain access to
    protected content merely because it appears in** context provenance, returned-item disposition, suppression
    metadata, transformation ancestry, or the exact historical model request.

    Concretely: `RETURNED M17 → SUPPRESSED permission_denied` must **not** let an unauthorized trace reader
    recover M17's protected content through `ContextAssembled`.

    Exact trace content and provenance therefore remain subject to the same authorization and compartment
    restrictions as their sources. Where an inspector lacks authority, a **restricted or redacted trace view**
    exposes only the metadata they are permitted to know.

    **Minimum propagation rule in force:** a segment derived from several sources is at least as restricted as
    its **most restricted** source. This errs conservatively — it can over-restrict but never leak — and is
    stated as the minimum rather than as the full mechanism. How authorization labels propagate across
    transformation ancestry, and whether the conservative default may ever be relaxed, is **D-32**. Derived
    revocation and unlearning remain **D-29**.

    The governing rule: *the trace is evidence about access and presentation; it is never a privilege-escalation
    path around them.*

19. **Freshness inclusion is recorded, never inferred.** ADR-0011 records the freshness assessment *attached to
    the returned item*. This ADR records whether that freshness information was itself **included in the
    presented representation**. *Freshness returned by recall* never implies *freshness shown to the reasoning
    seat*. This is where ADR-0006 rule 6's requirement is discharged on the cognition side.

### Measurement and linkage

20. **Budget evidence supports ADR-0003 parity verification**, permitting measurement of: total final input
    size under the **declared measurement basis**; memory-contributed input size; per-memory presented size
    where required; truncation or dropping caused by the budget; and the model, tokenizer and configuration
    identity relevant to token accounting.

    **The measurement basis is stated honestly.** An estimated token count is never presented as exact where
    the provider does not expose exact tokenization. *Which basis v0 declares is not settled here — see
    **D-31**.*

    **Linkage is backward, per ADR-0008.** `ContextAssembled` references already-committed `RecallPerformed`
    records and already-committed live-input evidence through a proposed structural relation `assembled_from`;
    a later decision record references the `ContextAssembled` record rather than requiring a forward link.
    `assembled_from` is admissible under ADR-0008 rule 2 — the runtime holds both identities, and no semantic
    inference is involved — and **extends that ADR's provisional vocabulary**, surfaced for approval. The
    decision→context relation is D-12's to name, requiring only that it point backward.

### Regret preconditions — evidence, not blame

The trace must later permit distinguishing:

| Case | Evidence available |
|---|---|
| eligible but **not returned** | ADR-0011 S-18 plus the cycle watermark |
| returned but **not presented** | disposition and suppression reason (rules 16–17) |
| presented but poor decision | requires investigation beyond the trace |

**Case two must not be labelled "attention failure" automatically.** A returned item suppressed by budget or by
authorization is not an attention defect, and even a policy-driven exclusion may have been correct. The
historical trace supplies evidence; it does not assign blame. No regret mechanism is implemented here.

### Hard boundary with D-30

**This ADR establishes none of:** that a presented memory influenced the model; how strongly; that a decision
depended on it; that the decision caused the outcome; or how credit should be split.

**No field named `influence_score`, `causal_weight`, `credit`, `blame` or equivalent may enter the historical
trace**, unless it explicitly records that some external or model process *produced such an attributed
estimate* — in which case it is attributed content under ADR-0002 rules 9–10 and is never historical truth.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| V-1 | Every context assembly reaching the reasoning seat emits one `ContextAssembled` record | Assert one record per assembly; assert record immutability |
| V-2 | A committed record represents a completed assembly; no partial context is ever presented as final | Fail assembly midway in a fixture; assert either no record or an explicit failed/incomplete status, never a partial context marked final |
| V-3 | Every returned item has exactly one final disposition | Assert each item from every `RecallPerformed` in the cycle resolves to `PRESENTED` or `SUPPRESSED` with a reason |
| V-4 | `SELECTED` is never reported as `PRESENTED` | Fixture dropping a selected item at budget; assert disposition is `SUPPRESSED` with `excluded_by_budget` |
| V-5 | Presented memory references are version-pinned | Assert no `current`-style reference; assert every presented memory names a version identity |
| V-6 | Transformed content preserves both source provenance and exact presented representation | Assert both fields non-null for every transformed segment; assert the representation is recoverable, not regenerated |
| V-7 | Historical presented content is unaffected by later rendering changes | Change the renderer in a fixture; re-read a historical record; assert byte-identical output |
| V-8 | Model-generated transformations are attributed and metered | Assert model identity recorded and the call metered under ADR-0003 J-5 |
| V-9 | A transformation does not inherit its source's grounded status | Assert transformed content's epistemic status is attributed, not grounded, absent its own ancestry |
| V-10 | Every segment carries a provenance channel | Assert channel ∈ the declared enum for every segment |
| V-11 | Live-supplied content is never labelled `persistent_recall` | Fixture where a live tool result is also committed post-N; assert the segment's channel remains `live_observation` |
| V-12 | Suppression reasons are operational and, where possible, reproducible from declared policy | Assert reason ∈ the declared vocabulary; re-evaluate the declared policy and assert the same reason |
| V-13 | Semantic verdicts appear only as attributed classifications | Assert no bare `irrelevant`-style value; assert any such value names the classifying policy |
| V-14 | No item denied by presentation-time authorization appears in the final context | Fixture revoking access after the watermark; assert the item is absent and disposition is `permission_denied` |
| V-15 | Freshness inclusion in the presented representation is recorded, not inferred | Assert the record states whether freshness was included; assert no path derives it from the recall's attached assessment |
| V-16 | Budget evidence permits ADR-0003 parity verification | Assert total, memory-contributed and per-memory sizes plus truncation are derivable |
| V-17 | The measurement basis is declared and never overstated | Assert the basis is recorded; assert an estimated count is not labelled exact |
| V-18 | Linkage is backward only | Assert `ContextAssembled` references only already-committed records (ADR-0008 P-3, P-4) |
| V-19 | `MemoryActivated` resolves as a projection, not a stored record | Assert no independent `MemoryActivated` record type exists; assert the projection recomputes from `ContextAssembled` |
| V-20 | No causal or credit field enters the trace | Assert no `influence_score`, `causal_weight`, `credit` or `blame` field exists except as explicitly attributed estimate content |
| V-21 | The segment manifest is ordered and complete | Assert every presented segment has a stable identity and an exact ordered position; assert the manifest reconstructs the request ordering |
| V-22 | Multi-source segments record all source references | Fixture synthesising two memories into one segment; assert both version-pinned references are present |
| V-23 | One memory may map to several segments and one segment to several memories | Assert the disposition-to-segment mapping is many-to-many and neither direction is constrained to one |
| V-24 | Partial contribution is preserved, not rounded to all-or-nothing | Fixture presenting an excerpt; assert the partial relationship and the exact excerpt are both recorded |
| V-25 | Semantically relevant serialization detail is captured | Assert any detail affecting provider-visible semantics appears in the canonical representation; assert excluded details are declared as semantically irrelevant |
| V-26 | Trace reads are subject to the sources' authorization | Assert an unauthorized principal reading `ContextAssembled` cannot resolve protected content through any field |
| V-27 | Suppressed protected content is not recoverable from disposition metadata | Fixture with `permission_denied`; assert the reason is visible but the content is not resolvable by an unauthorized reader |
| V-28 | A derived segment is at least as restricted as its most restricted source | Assert the effective restriction of every multi-source segment is the maximum over its sources |

## Evidence and rationale

**Option A fails on the central question rather than on cost.** Per-item activation records describe *which
items*, and the question asks *what input was supplied*. System instructions, segment ordering, tool
definitions, transformations and live evidence have no home in a per-memory record, so no set of them
reconstructs the request. Its partial-write exposure is the same defect ADR-0008 identified when it rejected
link-records-only: in an append-only ledger, a failure midway through N commits leaves damage that cannot be
edited away.

**Option B is close, and its gap is precise.** It reconstructs the input perfectly and yields the
returned-but-not-presented *set* by difference. What it cannot yield is *why*, and the distinction between an
item dropped for budget, excluded by policy, and denied by authorization is exactly what separates a capacity
problem from a selection problem from a security event. Option C is Option B plus dispositions.

**Rule 3 is the most consequential wording choice here.** "Activated" is the vision's term and it is doing
double duty: sometimes it means *entered the context*, sometimes *was attended to*, sometimes *mattered*. Only
the first is observable from outside a model. Keeping the word as normative would let the other two meanings
ride along into a historical record, which is precisely how a trace becomes an attribution claim without anyone
deciding to make one. Demoting it to a projection over `PRESENTED` keeps the vision's vocabulary available
while making the historical assertion exactly as strong as the evidence supports.

**Rule 13's grounding rule closes a leak that would otherwise be invisible.** ADR-0002 rule 11 makes grounding
a property of an object's ancestry. A model-written summary of a grounded belief has different content and
different ancestry, so it is a new attributed production — but it looks like the belief, sits where the belief
would sit, and would naturally be treated as carrying the belief's status. Stating that grounding does not
survive rewriting (V-9) is what prevents a summarization step from laundering attributed content into grounded
knowledge.

**Rule 17 continues a pattern this project has now applied four times.** ADR-0006 refused to let supersession
imply falsity; ADR-0008 refused to let `correction_of` imply the target was wrong; ADR-0011 refused to let a
retrieval score become confidence. Here, an exclusion reason must not become a verdict about the memory. In
each case the mechanism is identical: the system may record *what it did* or *what a policy classified*, never
*what is true*.

**Rules 7a–7c correct a modelling error rather than adding detail.** An item-shaped trace assumes each
presented memory occupies its own slot, which holds only while nothing is combined or excerpted. The moment a
segment synthesises two memories, an item model must either invent two phantom segments or record one memory as
unpresented — both false. Separating the ordered segment manifest from the returned-item disposition table, with
a many-to-many mapping between them, represents what actually happened without forcing either structure to
approximate the other. It also keeps the D-30 boundary clean: a memory contributing to a synthesised segment has
demonstrable *provenance* in the presented material and no demonstrated *influence*, and only the first is
claimed.

**Rule 8b's exclusions are a statement of honesty, and 8c prevents them becoming an excuse.** MNEXA cannot see
provider KV-cache state or hidden reasoning, so claiming to capture them would be false. But "semantically
irrelevant" is exactly the kind of judgement that expands under convenience pressure, and a detail the provider
actually reads is never irrelevant however incidental it looks. 8c makes the test provider-visible semantics
rather than implementation tidiness.

**Rule 18a exists because a perfect trace is a perfect disclosure.** Everything this ADR requires — exact
presented content, full provenance, transformation ancestry, suppression reasons — is precisely what an
attacker would want, and it is all gathered in one record. The `permission_denied` case is the sharpest: the
system correctly refused to present M17, then wrote a durable record referencing M17. If trace reads are not
themselves authorized, the refusal accomplished nothing. Making the trace inherit its sources' restrictions,
with a redacted view for lesser inspectors, keeps observability and access control from trading against each
other. The conservative propagation default is chosen because the failure directions are asymmetric:
over-restriction costs an inspector a query, under-restriction costs a disclosure that cannot be undone.

**Rule 2's separation of selection from presentation matters for the regret analysis D-30 will inherit.** If
selection and presentation are conflated, an item dropped by a serialization failure is indistinguishable from
one a policy deliberately excluded, and every capacity or infrastructure defect masquerades as a cognitive
choice. That would corrupt the very analysis the trace exists to enable.

## Consequences

**Easier:** reconstructing the exact input supplied to the reasoning seat, forever; explaining why any returned
memory did not appear; distinguishing live-supplied from recalled knowledge; verifying ADR-0003's context
parity; auditing whether a transformation laundered attributed content.

**Harder:** assembly must be atomic and instrumented, and cannot stream partial context; every segment needs
provenance; transformations must retain both source and result; exclusion reasons must be produced rather than
implied.

**Newly required:** the `ContextAssembled` event type; an ordered segment manifest with stable segment
identities; a many-to-many disposition-to-segment mapping; a segment provenance-channel enum; a
suppression-reason vocabulary; a transformation-policy identity registry; a declared context measurement basis;
the `assembled_from` structural relation; authorization-aware trace reads with a redacted view.

**Proposed refinements to accepted ADRs, surfaced for approval rather than applied silently:**

- **ADR-0007** — `MemoryActivated` moves from the provisional event-type list to a projection (rule 3). The list
  was explicitly open, so this is permitted evolution; the canonical object count is unchanged.
- **ADR-0008** — `assembled_from` extends the provisional structural relation vocabulary (rule 20).

**Constrained or unblocked:**

- **D-12 (decision/prediction/outcome linkage)** — unblocked on its context dependency. It names the
  decision→`ContextAssembled` relation, which must point backward.
- **D-30 (credit attribution)** — unblocked. It now has its full input: returned, selected, presented and
  suppressed with reasons, plus exact presented representations.
- **D-14 (port surface)** — the assembly boundary is where provenance channels are stamped.
- **D-29** — rule 18's hard boundary is the minimum in force until D-29 designs derived revocation.
- **ADR-0006 rule 6** — discharged on the cognition side by rule 19.

**Newly uncovered decisions — recorded, not decided here:**

**D-32 — trace authorization label propagation.** Rule 18a states the minimum in force: a derived segment is at
least as restricted as its most restricted source, and trace reads are subject to their sources' authorization.
How labels propagate across transformation ancestry, how a redacted view is composed, and whether the
conservative default may ever be relaxed for genuinely non-disclosing derivations are unsettled. Interacts with
**D-29** (derived revocation) and with vision 9.24–9.25 on memory taint.

**D-31 — context measurement basis.** ADR-0003 rule 3
requires B and C to share an injected-context budget and J-4 requires token-counting the injected block, but
neither says how size is measured when a provider does not expose exact tokenization. Rule 20 requires the
basis to be declared and honestly labelled; **which** basis v0 declares — provider-reported usage, a pinned
local tokenizer, or characters — is a durable choice that determines whether parity is verifiable at all.
Registered rather than settled.

## Reversibility

High for vocabulary, low for atomicity. Suppression reasons, provenance channels and segment types are registry
extensions. Moving from an atomic record to per-item events later would lose the guarantee that a context was
ever complete, and records written under C could not be re-derived into A's shape with dispositions intact.

## Validation / falsification

Revisit if:

- context assembly for long inputs cannot be made atomic without unacceptable latency, indicating rule 4's
  granularity is wrong rather than its principle; or
- the suppression vocabulary proves unable to express a common real disposition, requiring either extension or
  a free-text escape that V-12 would have to police; or
- preserving exact presented representations for large contexts dominates storage, which would argue for
  content-addressed segment sharing rather than for weakening rule 9.

Evidence that an investigator could not determine why a returned memory was absent from a context — despite
V-3 and V-12 — would falsify the claim that this disposition vocabulary is sufficient.

## Outcome

Pending. No implementation exists.
