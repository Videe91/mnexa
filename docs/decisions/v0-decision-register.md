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

**Next blocker: D-24 — historical-to-historical reference semantics.** ADR-0008 proposed 2026-09-10,
awaiting review. Surfaced ahead of D-03 because it blocks D-12 and interacts with D-05.

D-03 (episode construction authority) is unblocked and narrowed, awaiting its turn.

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
**Status:** pending; **narrowed** by ADR-0007. Episode's plane is fixed as interpretive (Interpretation of
kind `episode`), resolving tension T-1. D-03 is now purely about construction: who draws boundaries, whether
generation is model-based/deterministic/hybrid/externally supplied, when episodes form, and boundary
revision policy. The coupling that made D-02 and D-03 look inseparable dissolved once criterion β
(plane follows epistemic meaning, not producer) was adopted — see ADR-0007.

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
**Status:** pending. Constrained by ADR-0005's commit ordering for interpretive versions and by ADR-0008
(proposed), which makes commit sequence the historical plane's ordering primitive. The occurred-at versus
recorded-at question remains fully open and is D-05's core.

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
**Status:** pending. **Touched by ADR-0006** rule 6: recall output must include a freshness determination,
which is itself a computed value whose reproducibility falls under this decision.

Whether recall must be deterministic given identical memory state and Context Frame. Nondeterministic
recall makes controlled comparison noisier and makes a failed run non-reproducible.

### D-11 — Confidence and uncertainty semantics, including bootstrap

**Tier:** D3 (epistemic semantics)
**Vision:** 3.10, 3.14, 6.21, 8.5, 8.6
**Status:** pending. **Constrained by ADR-0006** rule 5 and M-6: staleness must not be folded into
confidence without superseding that rule. The bootstrap question (T-2) remains fully open.
**Vision tension — see Contradictions below.**

Where a confidence value comes from at t=0, given that the vision distrusts model-asserted confidence
(3.10) but v0 has no predictive track record to ground it (6.21) and cannot yet learn the weighting (3.14).

### D-12 — Decision, prediction and outcome linkage

**Tier:** D3 (scientific)
**Vision:** 2.7, 3.6, 6.19–6.23, 10.18
**Status:** pending; **constrained** by ADR-0007. Decision, Prediction, Action and Outcome are historical
event types, not canonical objects, so linkage must be expressed as references between records rather than
as fields on a mutable object. **Unblocked by ADR-0008** (proposed): `outcome_for`, `execution_of` and
`evaluates_prediction` make the linkage expressible, leaving D-12 to decide the content and completeness
contract rather than whether the edges may exist.

What must be recorded at decision time so that prediction error is computable later without hindsight
contamination; how an outcome binds to the decision that produced it; what happens when an outcome never
arrives.

### D-13 — Memory activation trace and utility attribution

**Tier:** D3 (scientific)
**Vision:** 3.12, 3.39, 5.36–5.41
**Status:** pending. **Partially settled by ADR-0006** rule 6 and M-8: every object entering active cognition
carries a freshness determination, so an activation record must include it. The attribution question (T-3)
remains fully open. **Vision tension — see Contradictions below.**

The vision requires memory strength to depend on demonstrated usefulness, and requires recording what was
*actually active* at decision time (5.40). It does not say how utility is attributed when several memories
were active simultaneously. Without a stated attribution rule this is unmeasurable, and an unmeasurable
criterion is a defect under the standing rules.

### D-14 — Agent-to-MNEXA port surface

**Tier:** D2
**Vision:** 10.5, 10.11
**Status:** pending; **shaped** by ADR-0007. The port surface operates over three canonical object types plus
typed event append.

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
**Status:** pending

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
**Status:** pending. **Shaped** by ADR-0008 (proposed): commit becomes a two-phase admission for records
carrying structural edges, since preexistence must be verified against every target before commit.

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
**Status:** ADR-0008 proposed 2026-09-10; awaiting owner review. **Discovered while drafting ADR-0007.**

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
rule or an explicit deferral that still records enough to attribute later. → **D-13**

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
