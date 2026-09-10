# MNEXA v0 — Decision Register

**Status:** audit complete; ADRs being surfaced sequentially.
**Branch:** `spec/mnexa-v0`
**Purpose:** inventory of every unresolved D2/D3 decision required to make `docs/specs/0001-mnexa-v0.md` precise.

This register is an *inventory*, not a decision. Nothing here is settled by being listed.
Each entry becomes a proposed ADR, surfaced one at a time per `.claude/skills/decide/SKILL.md`.

Entries were derived by reading the v0-relevant vision sections and asking, for each required
specification element, whether the vision already constrains the answer uniquely. Where the vision
constrains it uniquely, no decision is needed and the spec simply inherits the constraint. Where the
vision is silent, ambiguous, or self-tensioned, a durable decision exists and is recorded below.

---

## Sequencing decision (owner, 2026-09-10)

After ADR-0002 is accepted, experimental validity is de-risked **before** the domain model continues.
Order: ADR-0002 -> D-08/D-09/D-17 -> remaining domain-model decisions.

Recommended decomposition for D-08/D-09/D-17: **two ADRs** (resource parity; hidden-evaluation isolation).
Rationale recorded under those entries. Both have since been drafted: ADR-0003 (accepted), ADR-0004
(proposed).

Owner sequencing addendum (2026-09-10): after D-17 resolves, **D-21 surfaces next**, before the remaining
domain-model decisions. D-21 is foundational provenance semantics and must not be silently decided.

---

## Severity note

Three entries (**D-08**, **D-09**, **D-17**) do not affect whether MNEXA works. They affect whether
any result MNEXA produces means anything. They are grouped into one ADR (experimental parity) and are
the highest-risk items in this register.

---

## Critical path as of 2026-09-10

Six decisions settled: D-01, D-08, D-09, D-17, D-21, D-22 (ADR-0002 … ADR-0006).

**Nine decisions settled:** D-01, D-02, D-03, D-08, D-09, D-17, D-21, D-22, D-24 (ADR-0002 … ADR-0009).

**Ten decisions settled:** D-01, D-02, D-03, D-05, D-08, D-09, D-17, D-21, D-22, D-24 (ADR-0002 … ADR-0010).

**Thirteen decisions settled:** D-01, D-02, D-03, D-05, D-08, D-09, D-10, D-17, D-21, D-22, D-24, D-27, D-28
(ADR-0002 … ADR-0013).

**Next blocker: D-13 (narrowed) — activation and context evidence.** ADR-0014 proposed 2026-09-10, awaiting
review. Split approved; credit attribution is **D-30** and remains unresolved.

Earlier blocking analysis, retained for reference:

| Decision | Spec elements blocked | Upstream of | Notes |
|---|---|---|---|
| **D-10 recall reproducibility** | **12, 13** | **D-12, D-13** | Holds the watermark carrier (ADR-0010 rule 12) and the level-2 activation boundary (rule 10) |
| D-13 activation trace | 20, 24 | — | Close second; depends on D-10's output shape. T-3 open |
| D-18 failure/idempotency | 10 (partly), 21, 22 | — | Gained sequencer durability and linearization from ADR-0010 |
| D-12 linkage | 14, 15 | — | Fully unblocked; needs D-10's watermark carrier |
| D-06 provenance minimum | 7 (partly), 17 | — | Largely settled already |
| D-04 identity semantics | 6, 7 | — | Narrowed by ADR-0007/0009 |
| D-07 consolidation authority | 16 | — | Pre-shaped by ADR-0002 and ADR-0009 |
| D-14 port surface | 23 | — | Better derived after the contracts it exposes |
| D-11 confidence | 19 | — | T-2 open |
| D-16 personal scope | 11 | — | |
| D-15 memory-not-authority | 25 | — | |
| D-20 domain generality | 2, 3 | — | |
| D-19 decay | 29 | — | Likely deferral |

D-13 blocks the same number of elements and is arguably weightier — element 24 is the experiment's whole
measurement surface. It is placed second because it depends on what recall produces: the activation trace
records what recall surfaced, so its shape follows the recall contract rather than preceding it.

**D-23 is deferred.** It is not required to write a correct v0 specification: ADR-0006 treats all
supersessions uniformly, which is complete and safe, and classification would only refine signal quality.
The spec can state the uniform policy without it.

## Dependency order

```text
D-01 experience/interpretation boundary        [root]
  ├── D-02 canonical object set
  ├── D-03 episode definition + authority
  ├── D-04 identity semantics
  ├── D-05 time/ordering semantics
  └── D-06 provenance minimum
        │
        ├── D-07 consolidation authority
        ├── D-11 confidence semantics
        ├── D-12 decision/prediction/outcome linkage
        └── D-13 activation trace + utility attribution
              │
              ├── D-10 recall reproducibility
              ├── D-14 port surface
              └── D-15 memory-is-not-authority

D-08 / D-09 / D-17 experimental parity         [independent; blocks benchmark validity]
D-16 / D-18 / D-19 / D-20 scope + durability   [mostly deferrals; low branching factor]
```

---

## Register

### D-01 — Experience/interpretation boundary and historical immutability

**Tier:** D3 (constitutional)
**Vision:** 2.2, 3.4, 3.13, 5.40, 9.11, 10.7, 10.70 law 2
**Status:** **SETTLED** — ADR-0002 accepted 2026-09-10 after three owner-directed amendments.

The vision states the separation is constitutional but does not fix *where the line falls* for concrete
v0 objects, at what granularity a historical record is immutable, or what "immutable" obligates
mechanically. Every other object definition depends on which side of this line each object sits.

### D-02 — Canonical object set for v0

**Tier:** D2
**Vision:** 2.2–2.9, 3.2, 10.6
**Status:** **SETTLED** — ADR-0007 accepted 2026-09-10 after two owner-directed amendments (historical
references to Entity permitted when version-pinned with usage semantics; projections must be capturable as
historical evidence, and the event-type list is provisional not closed).

The vision names ~16 intelligence-graph node types across all phases. v0 needs the minimum subset that
closes the loop. Which objects exist in v0 is durable because later phases extend rather than replace them.

### D-03 — Episode definition and construction authority

**Tier:** D3 (epistemic semantics)
**Vision:** 2.3, 3.8, 3.2, 10.7
**Status:** **SETTLED** — ADR-0009 accepted 2026-09-10 after three owner-directed amendments (Option A
re-argued on semantic grounds; opaque MNEXA Episode identity replacing anchor-derived identity; validation
establishes admissibility not boundary truth).

What exactly constitutes an Episode, what its boundaries are, and *who* draws them: the agent, a
deterministic rule, or a model. If a model segments episodes, the episode is an interpretation and cannot
sit in the immutable plane.

### D-04 — Canonical identity semantics

**Tier:** D2
**Vision:** 2.4, 3.7, 6.8
**Status:** pending; **shaped** by ADR-0007. Identity applies to two things now known to be interpretive:
the Entity object and `identity_binding` interpretations. Raw observed identifiers are historical payload
content and are not Entities. D-04 decides identifier format, issuance, and resolution/merge/split semantics.

Identifier format and issuance for records and entities; what makes two references the same entity;
whether entity resolution is reversible; whether identity may be assigned by a model.

### D-05 — Time and ordering semantics

**Tier:** D2
**Vision:** 2.6, 6.4, 6.6
**Status:** **SETTLED** — ADR-0010 accepted 2026-09-10 after three owner-directed amendments (`committed_at`
added as a fourth concept; `commit_sequence` strengthened to visibility linearization; availability
distinguished from cognitive use). Was constrained by ADR-0005 and ADR-0008, which fixed **commit sequence** as the
admission-ordering primitive for both planes. That sharpens rather than answers D-05: three time axes now
exist and their relationship is unspecified — *occurred-at* (when the event happened in the world),
*recorded-at* (when MNEXA received it), and *commit sequence* (already settled). D-05 must settle the first
two and how they relate to the third.

Blocks the largest share of the specification — items 9, 10, 13, 14, 15, 20 and 21 — because every record and
every version carries time, and no capture contract can be written without saying which timestamps exist and
what ordering guarantee capture provides. Also upstream of D-12 (an outcome observed long after it occurred
is inexpressible without the distinction) and pairs with D-18 in specification item 21.

Whether v0 is bitemporal (occurred-at vs recorded-at), what ordering guarantee the ledger provides, and
how "what was knowable at time T" is reconstructed. This is also a benchmark-integrity control: without a
recorded-at axis, later knowledge can silently leak into a reconstruction of an earlier decision.

### D-06 — Provenance minimum for v0

**Tier:** D2 (D3 where it touches evidence semantics)
**Vision:** 3.20, 3.43, 9.6, 10.36
**Status:** **UNBLOCKED** — D-01 settled. **Partially settled by ADR-0002** rules 8-10 (model provenance for
attributed content) and further by ADR-0006 M-20 (revalidation attempts recorded with attribution).
Remaining scope: provenance minimum for non-model-authored records.

The minimum provenance every v0 object carries, explicitly including *model provenance* (3.43). The v0
non-goals defer the epistemic immune system but not provenance itself — 10.36 makes evidence-path
recoverability constitutional.

### D-07 — Consolidation authority: propose versus establish

**Tier:** D3 (constitutional)
**Vision:** 3.41, 3.48 law 9, 10.21, 10.70 law 5
**Status:** pending. Pre-shaped by ADR-0002 rules 8-10 (a consolidation model's output is an attributed
production recorded historically; the proposal it carries is interpretive) and further by ADR-0006 rule 8
(revalidation may propose a new version but head movement obeys normal promotion rules — revalidation is not
a shortcut around epistemic authority).

The vision forbids a model having unilateral authority over truth and separates author from judge. In v0
there is no Verification Engine and no second agent. What, concretely, may a model establish in a
single-agent v0 without violating the law — and what must remain a proposal?

### D-08 — Consolidation model identity and parity

**Tier:** D3 (scientific / benchmark methodology)
**Vision:** 3.42, 10.41; `.claude/rules/scientific-method.md`
**Status:** **SETTLED** — ADR-0003 accepted 2026-09-10 after four owner-directed precision amendments.

If consolidation is performed by a model stronger than the frozen model under test, condition C's gain may
come from the consolidation model's intelligence rather than from accumulated experience. The thesis claim
would not survive scrutiny. The vision permits heterogeneous models inside consolidation (3.42) but never
addresses the confound this creates for Grand Proof 1 (10.41).

### D-09 — Inference-time compute parity across conditions

**Tier:** D3 (scientific / benchmark methodology)
**Vision:** 10.41; `.claude/rules/scientific-method.md`
**Status:** **SETTLED** — ADR-0003 accepted 2026-09-10 after four owner-directed precision amendments.

If MNEXA's recall path may itself call a model at decision time, condition C consumes more inference
compute than A and B, and any improvement is confounded with extra compute. Requires an explicit parity
rule at specification level.

### D-10 — Recall reproducibility

**Tier:** D2 (D3 where it affects experimental validity)
**Vision:** 5.3, 5.10; `.claude/rules/scientific-method.md`
**Status:** **SETTLED** — ADR-0011 accepted 2026-09-10 after three owner-directed amendments (content must be
recoverable not merely identified; recall binds a fixed knowledge snapshot; returned is not presented).

Whether recall must be deterministic given identical memory state and Context Frame. Nondeterministic
recall makes controlled comparison noisier and makes a failed run non-reproducible.

### D-11 — Confidence and uncertainty semantics, including bootstrap

**Tier:** D3 (epistemic semantics)
**Vision:** 3.10, 3.14, 6.21, 8.5, 8.6
**Status:** pending. **Constrained by ADR-0006** rule 5/M-6 (staleness must not be folded into confidence)
and by **ADR-0011** rule 10/S-11 (retrieval scores may not become confidence, so the bootstrap cannot draw on
ranking signals). The bootstrap question (T-2) remains fully open.
**Vision tension — see Contradictions below.**

Where a confidence value comes from at t=0, given that the vision distrusts model-asserted confidence
(3.10) but v0 has no predictive track record to ground it (6.21) and cannot yet learn the weighting (3.14).

### D-12 — Decision, prediction and outcome linkage

**Tier:** D3 (scientific)
**Vision:** 2.7, 3.6, 6.19–6.23, 10.18
**Status:** pending; **constrained** by ADR-0007. Decision, Prediction, Action and Outcome are historical
event types, not canonical objects, so linkage must be expressed as references between records rather than
as fields on a mutable object. **Unblocked by ADR-0008**: `outcome_for`, `execution_of` and
`evaluates_prediction` make the linkage expressible. **Temporal dependency cleared by ADR-0010** (proposed):
D-12 must carry the knowledge watermark, may express observation lag as `recorded_at` − `occurred_at`, and
must keep prediction horizon in payload rather than in a record time field.

What must be recorded at decision time so that prediction error is computable later without hindsight
contamination; how an outcome binds to the decision that produced it; what happens when an outcome never
arrives.

### D-13 — Memory activation trace and utility attribution

**Tier:** D3 (scientific)
**Vision:** 3.12, 3.39, 5.36–5.41
**Status:** ADR-0014 proposed 2026-09-10; awaiting owner review. **Split approved by owner 2026-09-10** — as
narrowed, D-13 covers activation and context evidence only; credit attribution is **D-30**.

**Split analysis (2026-09-10).** D-13 as registered contains two decisions of different kinds:

| | Question | Kind |
|---|---|---|
| **A — activation/context evidence** | What was selected, suppressed, assembled and presented? | Historical observability |
| **B — credit attribution** | What evidence licenses claiming an activated memory contributed to an outcome? | Epistemic inference |

They are separable, and the dependency runs one way: **B needs A** (attribution requires knowing what was
presented), while **A does not need B** (a trace contract is fully specifiable from ADR-0011's returned set plus
selection decisions). One-way dependency with different decision kinds is the standard case for splitting.

Two further reasons: **T-3** — the vision tension about distributing credit across several simultaneously
active memories — belongs entirely to B, so A can be settled without touching an unresolved tension. And
specification element 20 requires a trace *"required for later utility measurement"*, which maps exactly onto
A recording what B will later need, rather than onto performing attribution in v0.

Bundling them would let A's tractable observability decisions be held hostage to B's genuinely hard epistemic
question, and would risk B being decided by default inside A.

**The chain that must be preserved, with no inference across the marked boundaries:**

```text
DURABLY ELIGIBLE  →  RETURNED  →  SELECTED  →  PRESENTED/ACTIVATED  →  DECISION  →  OUTCOME
   ADR-0010/13       ADR-0011        D-13          D-13                 D-12        D-12
                                                        ╳ no inference PRESENTED → CAUSED DECISION
                                                        ╳ no inference DECISION → CAUSED OUTCOME
```

Both crossings require an explicit attribution standard, which is **D-30**.

**Original scope, retained for reference:** what the activation/usage trace must record and how utility is
attributed. **Partially settled by ADR-0006** rule 6/M-8, by **ADR-0010 rule 10**, and by **ADR-0011**,
which supplies its input: the returned, version-pinned set
with presented freshness, plus the retrieval-regret boundary-one computation. D-13 owns
presented/activated/suppressed and attribution. **Partially settled by ADR-0006** rule 6/M-8 and by
**ADR-0010 rule 10**,
which fixes the three-level structure D-13 must implement: durably available (settled — `commit_sequence`),
presented/activated (D-10 + D-13), actually used/attributed (D-13's attribution contract). Levels 2 and 3 must
not collapse. ADR-0010 also makes vision 5.40's *not activated* line computable, since the watermark defines
what was eligible but unused. The attribution question (T-3) remains fully open.
**Vision tension — see Contradictions below.**

The vision requires memory strength to depend on demonstrated usefulness, and requires recording what was
*actually active* at decision time (5.40). It does not say how utility is attributed when several memories
were active simultaneously. Without a stated attribution rule this is unmeasurable, and an unmeasurable
criterion is a defect under the standing rules.

### D-14 — Agent-to-MNEXA port surface

**Tier:** D2
**Vision:** 10.5, 10.11
**Status:** pending; **shaped** by ADR-0007 (three canonical object types plus typed event append) and by
ADR-0011 (the recall port accepts a watermark and returns version-pinned items with completion status).

The conceptual operations v0 exposes. Durable because it is the externally consumed interface and because
10.5 makes it constitutional that agents do not see storage.

### D-15 — Memory content is not authority

**Tier:** D3 (security / epistemic)
**Vision:** 9.11, 9.12, 9.39, 5.49, 5.50
**Status:** pending

v0 recalls stored text into a model prompt, so memory-borne prompt injection exists in v0 even though the
full Cognitive Firewall is deferred. Per the standing rules a security requirement enters as an invariant
with a stated `howChecked`, at design time.

### D-16 — Personal-scope isolation boundary

**Tier:** D2
**Vision:** 2.17, 2.20, 3.27, 10.8
**Status:** pending; **shaped** by ADR-0011: the recall request's namespace field is where scope isolation is
enforced at the recall boundary.

How v0 structurally guarantees single-agent scope so that later L2+ scopes extend rather than retrofit.

### D-17 — Experience corpus versus hidden-evaluation boundary

**Tier:** D3 (scientific)
**Vision:** 10.59; `.claude/rules/scientific-method.md`
**Status:** **SETTLED** — ADR-0004 accepted 2026-09-10 after two owner-directed amendments (ephemeral-state
freeze + evidence sink; exposure/burn lifecycle + epoch freeze).

What MNEXA is permitted to ingest, and the structural guarantee that hidden evaluation instances cannot
enter memory. Must be locked before any experience is captured, not at benchmark time.

### D-18 — Failure semantics and ledger durability

**Tier:** D2
**Vision:** 3.4, 9.7
**Status:** pending. **Shaped** by ADR-0008 (commit is a two-phase admission for records carrying structural
edges) and by ADR-0010, which adds commit-sequencer durability across restarts and the visibility
linearization invariant (rule 9). Leaves open whether a failed commit consumes a sequence number — gaps are
permitted, so either answer is admissible, but retroactive insertion beneath an exposed watermark is not.

What happens on partial write, duplicate submission, and capture failure; whether a lost experience is
allowed to fail silently. Idempotency is part of the durable contract if the capture port is retryable.

### D-19 — Decay and forgetting in v0

**Tier:** D2 (scope)
**Vision:** 2.16, 3.33–3.36
**Status:** pending. Retention pressure now arrives from three accepted decisions — ADR-0002 I-6, ADR-0005
(pinned interpretive versions), ADR-0006 (long-stale objects as decay candidates).

The stated v0 non-goals do not mention forgetting, but the vision treats it as core. Likely a deferral —
but deferral must be explicit, because if v0 records no decay-relevant signal, decay cannot be added later
without a migration.

### D-20 — Domain-generality guarantee

**Tier:** D2
**Vision:** 10.12, 10.64
**Status:** pending

The structural rule that keeps the substrate domain-general while the first experimental domain is
coding/debugging. Without a stated rule, coding-specific structure leaks in as "obvious".

### D-21 — Version pinning of interpretive-to-interpretive derivation edges

**Tier:** D2, reclassified to **D3** — see status below.
**Vision:** 3.20, 3.46, 3.21
**Discovered:** while amending ADR-0002; deliberately not decided there.

ADR-0002 I-5 pins historical→interpretive references to immutable versions, and rule 11 permits transitive
provenance through interpretive→interpretive derivation edges. It does not say whether those derivation
edges are themselves version-pinned.

If they float, supersession silently rewrites what an abstraction was derived from: Principle P derived from
Pattern X v1 would appear to derive from X v2 after revision, even though P's reasoning never saw v2. That
breaks the evidence spine's meaning and makes revalidation-on-contradiction (3.21) unable to identify which
abstractions actually rest on the contradicted version.

If they are pinned, abstractions do not automatically benefit from improvements to their supporting
patterns, and something must decide when to re-derive.

Not decided in ADR-0002 because the owner amendment addressed grounding, not edge mutability, and deciding
it silently would have expanded the approved decision space.

**Question preserved verbatim (owner, 2026-09-10):**

> Should interpretive→interpretive derivation/provenance edges reference immutable source versions rather
> than mutable object heads?

**Owner's stated architectural expectation, recorded as a *proposed* position and explicitly NOT accepted:**
provenance/derivation edges should be version-pinned, while mutable heads may exist for discovering the
current interpretation. This is to be treated as one candidate option when the ADR is drafted, argued
against genuine alternatives, and not presented as settled.

**Sequencing:** surfaced immediately after D-17, per owner instruction.

**Status:** **SETTLED** — ADR-0005 accepted 2026-09-10 after two owner-directed mechanical clarifications
(strict commit-order preexistence with a retained DAG check; derivation edge set covered by version content
identity). Reclassified **D2 → D3** because
the edges' mutability determines what ADR-0002's accepted invariant I-9a actually asserts, placing the
question inside an accepted constitutional ADR rather than beside it. The owner's expectation was adopted in
its first half (pin derivation edges) and refined in its second: mutable heads live on *objects*, as
ADR-0002 rule 4 already provides, so no separate floating discovery edge is introduced (see ADR-0005
Option C, rejected).

### D-22 — Re-derivation policy for stale abstractions

**Tier:** D2
**Vision:** 3.21, 3.13, 3.34
**Status:** **SETTLED** — ADR-0006 accepted 2026-09-10 after two owner-directed precision amendments
(staleness is derived assessment with four states, never version mutation; revalidation creates new
epistemic history and never restores a version). **Discovered while drafting ADR-0005.**

ADR-0005 rule 4 makes staleness computable — an abstraction is stale with respect to a basis when its pinned
version is not that object's current head. It says nothing about what should happen when staleness is
detected.

Options span: re-derive during consolidation; flag without acting; reduce confidence proportionally to how
far the basis moved; ignore staleness in v0 entirely. Each has different consolidation cost and different
consequences for 3.21's contradiction propagation.

Not decided in ADR-0005 because that ADR's question was edge mutability, and settling re-derivation policy
alongside it would repeat exactly the silent scope expansion that produced D-21.

### D-23 — Supersession change classification

**Tier:** D2
**Vision:** 3.21, 3.13, 2.19
**Status:** pending. **Discovered while drafting ADR-0006; not decided there.**

Whether a supersession event must declare its kind — correction, clarification, extension, narrowing,
refutation — so that staleness can be weighted by consequence rather than treated uniformly.

ADR-0006 must currently treat every supersession identically, because no classification exists. That
over-signals: a typo fix upstream produces the same staleness signal as a fundamental narrowing. Uniform
treatment is the safe direction, but it caps how strong a consequence staleness can justify, and it is the
most likely source of signal-volume problems flagged in ADR-0006's falsification conditions.

Not decided in ADR-0006 because it concerns what a supersession *event* must carry, which is a different
question from what a dependent should do, and settling it there would repeat the scope expansion that
produced D-21 and D-22.

### D-24 — Historical-to-historical reference semantics

**Tier:** D2
**Vision:** 2.7, 10.18, 3.6
**Status:** **SETTLED** — ADR-0008 accepted 2026-09-10 after one owner-directed amendment (structural
admission is evidence-based not actor-based; relation basis immutable and hashed; relations carry no truth
import; inline and RelationshipRecorded forms share one meaning). **Discovered while drafting ADR-0007.**

**Note:** the gap predates ADR-0007. ADR-0002 rule 3 — correction by appending a superseding record — already
required a historical→historical reference, and was accepted without the mechanism existing. ADR-0007 made it
urgent rather than creating it.

ADR-0002 I-5 governs historical→interpretive references. ADR-0005 governs interpretive→interpretive. Nothing
governs a historical record citing another historical record.

ADR-0007 makes this immediately load-bearing by demoting Decision, Prediction, Action and Outcome to event
types: an `OutcomeObserved` record must point at the `DecisionMade` record it is an outcome of, and there is
currently no rule permitting or constraining that edge.

Both endpoints are immutable, so no version-pinning question arises. Open: whether such references are
permitted at all; whether a commit-order preexistence constraint analogous to ADR-0005 L-7 applies; whether
they may form cycles; and whether a record may reference a record committed after it (a decision citing its
own later outcome — presumably forbidden, but unstated).

**D-12 is blocked on this.** Not decided in ADR-0007 because that ADR's question was object classification,
and settling reference semantics there would have expanded the decision space beyond what was surfaced.

### D-25 — Episode split and merge identity

**Tier:** D2
**Vision:** 3.8, 3.19, 2.3
**Status:** pending. **Discovered while drafting ADR-0009; deferred from v0 there.**

ADR-0009 binds Episode object identity to a deterministic anchor, so an Episode's extent follows its anchor
and regrouping the same anchor's records is simply a new version. Subdividing one episode into several, or
combining several into one, only arises when boundaries must cross or partition anchor scopes — which no v0
contract requires.

The shape is already implied if it becomes needed: a split or merge would produce **new Episode objects
deriving from the originals' versions**, not new versions of them, because the originals had valid
independent extents and ordinary supersession would misrepresent that. This mirrors the merge/split reasoning
that earned Entity its own primitive in ADR-0007.

Deferred rather than decided because it is an identity decision distinct from boundary construction, and
settling it inside ADR-0009 would have expanded that ADR's surfaced scope.

### D-26 — Episode lineage revision targeting policy

**Tier:** D2
**Vision:** 3.13, 3.19
**Status:** pending. **Discovered while amending ADR-0009; not decided there.**

ADR-0009 rule 3 requires a consolidation proposal to declare explicitly whether it revises an existing
Episode lineage or establishes a new Episode. It does not say how consolidation decides which.

Without a targeting policy, repeated consolidation over the same records may accumulate near-duplicate
Episodes rather than revising, since establishing a new object is always the path of least resistance.

This is consolidation *behaviour* rather than episode *semantics*, and it interacts with D-07. Not decided in
ADR-0009 because that ADR's question was construction and authority; settling targeting policy there would
have expanded its surfaced scope.

### D-27 — v0 retrieval channel set

**Tier:** D2
**Vision:** 5.6, 5.7, 5.10
**Status:** **SETTLED** — ADR-0012 accepted 2026-09-10 after three owner-directed amendments (lexical/exact
channel added; head-as-of-N default candidate pool; entity channel consumes but never establishes identity).
**Discovered while drafting ADR-0011.**

Vision 5.6 describes many independent activation routes — semantic, entity, temporal, causal, structural,
procedural, outcome, risk and historical-utility. ADR-0011 records a per-item retrieval channel and permits
future ones, but does not decide which exist in v0.

This is a scope decision affecting what recall can actually do, and therefore what condition C *is* in the
experiment. It includes the associated ranking-signal vocabulary that ADR-0011 rule 10 requires to carry
declared algorithmic meanings.

Not decided in ADR-0011 because that ADR's question was the *evidence* contract; settling which mechanisms
produce the evidence would have expanded it from evidence to mechanism.

### D-28 — Cognitive-cycle knowledge snapshot scope

**Tier:** D2
**Vision:** 5.4, 5.13, 5.19
**Status:** pending. **Discovered while amending ADR-0011; not decided there.**

ADR-0011 rules 3a–3b fix the knowledge snapshot for a **single** recall: the watermark binds before retrieval
and does not move. Unresolved: must an entire cognitive decision cycle use one stable watermark, or may
separate recall operations within the same cycle advance to newer ones?

ADR-0010 rule 12 requires a decision to carry *a* watermark, but does not forbid its constituent recalls using
different ones — which would leave the decision's watermark ambiguous, and would make "what was available to
this decision" answerable only per-recall rather than per-decision.

Inside an evaluation epoch the question cannot arise, since ADR-0004 rule 9 freezes memory. Outside one — during
the experience and consolidation phases — it can.

**Status:** **SETTLED** — ADR-0013 accepted 2026-09-10 after three owner-directed amendments (watermark
freezes persistent intelligence not live input; arriving commits do not force a new cycle; the snapshot is
epistemic, not an authorization freeze).

**Blocking analysis (performed 2026-09-10):** D-28 **does** block D-13, though not through D-13's data model.
An activation record can cite its recall and that recall's watermark under any policy. What breaks is D-13's
central deliverable: decision-level retrieval regret needs one eligible set, and with recalls at differing
watermarks an item committed between them was ineligible to one and eligible to another — producing false
positives in exactly the retrieval-versus-attention distinction ADR-0011 rule 18 handed to D-13. ADR-0010 rule
12's requirement that a decision carry *a* watermark is also under-determined until this is settled.

Did **not** block D-27: channel choice is unaffected by how many recalls a cycle performs, since each binds its
own N regardless.

Not decided in ADR-0011 because that ADR's scope was a single recall operation's evidence contract.

### D-29 — Authorization and revocation temporal semantics

**Tier:** D3 (security / privacy)
**Vision:** 9.43, 9.44, 9.45, 9.48
**Status:** pending. **Discovered while amending ADR-0013; minimum invariant stated there, mechanism not
designed.**

ADR-0013 rule 8 establishes the minimum: `AS_OF(N)` is an epistemic watermark, not an authorization freeze.
Current authorization may restrict a pinned cycle — removing access, returning permission-limited or
incomplete results, or aborting the cycle — and may **never** inject post-N knowledge into the view, rewrite
what was available at N, or imply revoked content never existed.

Unresolved: how revocation propagates to knowledge **derived** from revoked evidence (vision 9.48's derived
forgetting), what the blast radius is (9.44), and how dependent interpretations are re-evaluated (9.45).
Interacts with **D-19** (decay and forgetting) and with ADR-0005's retention obligations.

Likely mostly beyond v0's stated non-goals, but the minimum invariant is required now and is in force.

### D-30 — Outcome and causal credit attribution standard

**Tier:** D3 (scientific / epistemic)
**Vision:** 3.12, 3.39, 5.36–5.39, 6.45
**Status:** pending. **Split out of D-13 on 2026-09-10 — see the D-13 entry for the analysis.**

What evidence licenses MNEXA to claim that a particular activated memory contributed to a success or failure.

Owns **tension T-3**: law 6 (3.48) requires useful recall to strengthen memory and harmful recall to weaken it,
and 5.40 requires recording what was active, but no vision section gives a rule for distributing credit when
several memories were active and the outcome was good. Sections 5.37–5.39 assume utility "can eventually be
inferred from outcomes" at a scale v0 will not reach.

Owns both prohibited inferences in the D-13 chain: `PRESENTED → CAUSED DECISION` and
`DECISION → CAUSED OUTCOME`. Neither may be asserted without a standard this decision supplies.

Depends on D-13 (needs the activation trace as input). **Unblocked by ADR-0014** (proposed), which supplies
that input: returned, selected, presented and suppressed-with-reason, plus exact presented representations.
Likely minimal or deferred in v0. ADR-0014 forbids any `influence_score`, `causal_weight`, `credit` or `blame`
field entering the historical trace except as explicitly attributed estimate content.

### D-31 — Context measurement basis

**Tier:** D2 (scientific / benchmark-adjacent)
**Vision:** 5.14; `.claude/rules/scientific-method.md`
**Status:** pending. **Discovered while drafting ADR-0014; not decided there.**

ADR-0003 rule 3 requires conditions B and C to share one maximum injected-context budget, and J-4 requires
token-counting the injected block. Neither says **how** size is measured when a provider does not expose exact
tokenization.

ADR-0014 rule 20 requires the basis to be declared and honestly labelled — an estimate is never presented as
exact — but does not choose it. The candidates differ materially: provider-reported usage (exact but only
available post-hoc, and covering the whole request rather than the injected portion), a pinned local tokenizer
(pre-computable and attributable per segment, but approximate against the provider), or character/byte counts
(exact and provider-independent, but a poor proxy for model cost).

The choice determines whether ADR-0003's B/C parity is verifiable at all, and therefore whether the claim
boundary in ADR-0003 rule 9 can be checked. Not decided in ADR-0014 because that ADR's question was what the
trace records, not which accounting standard the benchmark adopts.

---

## Contradictions and tensions found in the vision

These are recorded as findings, not resolved here.

### T-1 — Which plane does an Episode belong to? — **RESOLVED by ADR-0007**

Section 3.2 places episodes in the **Memory Plane**, distinct from the Experience Plane, implying episodes
are derived and revisable. Section 10.7 sorts everything into append-only *historical* objects or evolvable
*interpretive* objects. Section 3.8 says an episode is *constructed* from raw events and that MNEXA
"preserves both representations". An episode therefore reads as interpretive, yet Sections 2.3 and 3.8
describe it with the language of history ("what happened"). The boundary case is real and must be decided
explicitly. → **D-03**

**Resolution (ADR-0007, proposed):** 3.2 is correct. Under criterion β an Episode asserts that records form
one meaningful unit — organization, not occurrence — so it is interpretive regardless of what constructs it.
3.8's "preserves both representations" is satisfied by raw records staying historical while the grouping over
them is interpretive.

### T-2 — Confidence has no ground at t=0

Section 3.10 says MNEXA must never depend on a model asserting confidence. Section 6.21 grounds confidence
empirically in predictive track record. Section 3.14 says the weighting should be *learned* rather than
hard-coded. At v0 t=0 all three are unavailable simultaneously: no track record exists, nothing has been
learned, and the only available estimator is the model the vision distrusts. v0 must adopt some explicit
interim policy, and that policy is durable. → **D-11**

### T-3 — Utility attribution is required but underdetermined

Law 6 (3.48) requires useful recall to strengthen memory and harmful recall to weaken it. Section 5.40
requires recording which memories were active at a decision. But when eight memories are active and the
outcome is good, the vision gives no rule for distributing credit. Sections 5.37–5.39 assume utility "can
eventually be inferred from outcomes" at a scale v0 will not reach. v0 needs either a stated attribution
rule or an explicit deferral that still records enough to attribute later. → **D-30** (split out of D-13)

### T-4 — Consolidation model choice is unconstrained but experimentally load-bearing

Section 3.42 explicitly permits different models for different consolidation jobs, treating this as a
feature of model independence. Section 10.41 requires the base model to remain frozen for the persistent-
learning proof. Neither section addresses that a stronger consolidation model imports intelligence from
outside the frozen-weights boundary, which is precisely what Grand Proof 1 claims did not happen. → **D-08**

### T-5 — "Not merely retrieved verbatim" is asserted, never operationalized

Section 10.41 requires improvement to come from reusable intelligence rather than verbatim retrieval of the
current task, and 1.10/1.3 distinguish MNEXA from RAG on exactly this axis. No section defines how the two
are told apart in a result. This is primarily a Benchmark Contract concern, but it constrains v0: the
substrate must record enough to make the distinction computable later. → interacts with **D-13**, **D-17**

---

## Non-decisions

Recorded so they are not mistaken for gaps. These are constrained uniquely enough by the vision that the
specification inherits them without an ADR:

- History is immutable; interpretation evolves. (Law; *how* it applies to specific objects is D-01.)
- Every durable claim retains provenance. (Law; the v0 *minimum* is D-06.)
- Experience is local by default. (Law; the v0 *mechanism* is D-16.)
- Retrieved memory is evidence, not authority. (Law; the v0 *enforcement* is D-15.)
- Storage technology. Explicitly not a specification-level choice; deferred to implementation per
  `.claude/rules/implementation.md` scope control.
