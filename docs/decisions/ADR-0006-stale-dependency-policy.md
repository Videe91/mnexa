---
id: ADR-0006
status: proposed
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/08-self-model-meta-memory-self-improvement.md
spec_refs: []
supersedes: []
---

# ADR-0006 — Stale Dependency Policy for Interpretive Objects

**Tier: D3 (epistemic semantics).** Requires explicit owner approval.

Covers register entry **D-22**.

## Decision question

When an interpretive object's pinned upstream dependency has been superseded by a newer version, what should
MNEXA do with the dependent interpretation?

## Context

ADR-0005 rule 4 makes staleness *computable* — a dependent is stale with respect to a basis when its pinned
source version is not that source object's current head — and deliberately stopped there. This ADR decides
the consequence.

### Two validities that must not be conflated

The single most important distinction in this decision:

| | Question it answers | Effect of upstream supersession |
|---|---|---|
| **Historical validity** | Was this object really derived from those versions at that time? | **None, ever.** Guaranteed by ADR-0005 rules 5–6: provenance is inside the version's content identity |
| **Current epistemic validity** | Should this object still be relied upon now? | **Raises a question. Does not answer it.** |

Supersession of a source is not a refutation of the dependent. It is a change of basis whose consequence is
unknown until examined. Collapsing the two validities in either direction produces a specific failure:

- Treating supersession as refutation destroys usable knowledge on every upstream typo fix.
- Treating supersession as irrelevant lets a principle resting on a corrected pattern keep influencing
  decisions with no signal that its basis moved.

The vision keeps these apart deliberately. 3.13 has interpretation maturing while history stays fixed; 8.6
separates *uncertain* (one answer favoured but weakly) from *unresolved* (evidence supports competing
answers) — and a stale dependent is in neither state. It is **unrechecked**, which is a third thing: nothing
new argues against it, and nothing has confirmed it still follows.

### Supersession reasons are not uniform, and v0 cannot tell them apart

A pattern may be superseded for a typo, an added example, a clarified boundary, or a fundamental narrowing
that breaks everything downstream. Only the last genuinely threatens dependents. MNEXA has no supersession
change-classification — that gap is recorded below as D-23 — so v0 must treat all supersessions uniformly.
Uniform treatment over-signals and never under-signals, which is the safe direction, but it means staleness
in v0 is a weak signal and must not carry strong automatic consequences. This constrains the options more
than anything else in this decision.

### Transitive blast radius

```text
Pattern A  →  Belief B  →  Principle C  →  Skill S
```

If A is superseded, B is *directly* stale. C and S are stale only *by inheritance*, and the further from A,
the weaker the implication that anything is actually wrong. Any policy must say whether and how far
staleness travels — the vision discusses this as epistemic blast radius (9.44) and derived forgetting (9.48),
both explicitly deferred from v0, so v0 needs the smallest thing that stays correct without importing them.

## Options considered

### Option 1 — Informational only

Staleness is computable on demand. No consequence, no propagation, no queue.

Benefits: cheapest; historical validity trivially preserved; no new machinery.

Costs: a consumer must remember to ask. Recall can surface a principle whose basis was corrected with no
indication, which is precisely the "memory that quietly misleads" failure 5.11 and 5.16 exist to prevent.
Revalidation capability exists in principle but nothing ever triggers it.

### Option 2 — Mark dependency-stale, retain the object

Staleness is surfaced as an explicit signal on the object wherever it is read, while the object stays fully
usable and unchanged.

Benefits: signals current-validity risk without asserting the dependent is wrong; leaves the judgement to the
consumer; no mutation of the dependent, so historical validity is untouched by construction.

Costs: a signal nobody acts on is only marginally better than Option 1 — it needs a path to revalidation to
be worth anything.

### Option 3 — Confidence degradation

Reduce the dependent's confidence in proportion to upstream change.

Benefits: single scalar; naturally attenuates across hops.

Costs: **conflates two different quantities.** Confidence answers "how likely is this true"; staleness
answers "has this been rechecked since its basis moved". Folding the second into the first makes them
inseparable afterwards, and 8.5 already insists coverage and confidence stay distinct for the same reason.
Worse, v0's confidence semantics are themselves undecided (D-11, tension T-2) — degrading a number that has
no agreed grounding compounds an unresolved question rather than answering this one. Also arbitrary: with no
supersession classification, any degradation coefficient is invented.

### Option 4 — Automatic invalidation

The dependent becomes unusable until revalidated.

Benefits: safest-sounding; no stale knowledge can influence a decision.

Costs: catastrophic over-reaction given no change classification — an upstream typo fix invalidates an entire
subtree. Combined with transitivity, a single edit can disable an arbitrarily large region of memory. Treats
supersession as refutation, the exact conflation this ADR exists to prevent. Would also make consolidation
adversarial to its own outputs: improving a pattern would be punished by invalidating everything built on it.

### Option 5 — Automatic eager re-derivation

Consolidation immediately re-derives every stale dependent against the new source versions.

Benefits: memory is always current; staleness never accumulates.

Costs: unbounded eager recomputation with transitive fan-out — one supersession can trigger a cascade whose
cost is proportional to the dependent subtree, not to the size of the change. Every re-derivation is a model
call under ADR-0003 rule 5, so the cost is real and metered. Produces churn: a new version of every
descendant on every upstream edit, most of which will be identical in substance. Also cannot run during an
evaluation epoch (ADR-0004 rule 9), so it does not remove the need for a deferred path anyway.

### Option 6 — Queue-based revalidation

Detected staleness enqueues a revalidation task processed during consolidation under a bounded budget and a
priority order. The dependent remains available and unchanged until processed.

Benefits: bounded cost; revalidation actually happens rather than remaining theoretical; naturally fits
MNEXA Sleep (3.16) as asynchronous processing outside the action loop; priority allows the small number of
consequential cases to be handled first.

Costs: needs a queue and a priority rule; a backlog can grow if consolidation budget is persistently
insufficient — which must itself be observable.

## Decision

**Recommendation: Option 2 combined with Option 6.** *(Proposed. Not approved.)*

These are naturally one policy: a signal plus a path to resolve it. Options 3, 4 and 5 are rejected.

Seven rules.

### Validity separation

1. **Historical validity is never affected.** Supersession of a source never alters, weakens or annotates the
   dependent version's recorded derivation. This follows from ADR-0005 rules 5–6 and is restated here because
   the temptation to "fix up" provenance is greatest exactly when a basis has moved.
2. **Staleness is a current-validity signal, and a distinct one.** It is not confidence, not groundedness,
   and not contradiction. A stale object is **unrechecked**: nothing new argues against it and nothing has
   confirmed it still follows. It remains grounded under ADR-0002 I-9a, because its ancestry still resolves.

### Computation and propagation

3. **Staleness is computed, never stored as truth.** Consistent with ADR-0005 rule 4, staleness is derived on
   demand by comparing pinned versions against their objects' heads. No authoritative staleness flag is
   persisted, so it cannot drift from the graph. Caches for performance are permitted only if invalidated by
   the same comparison.
4. **Direct and inherited staleness are distinguished, and propagation is lazy.** *Direct* staleness means a
   pinned source's head has moved. *Inherited* staleness means an ancestor is stale. Both are computed by
   traversal on demand; neither is eagerly materialized across the graph. Traversal runs to a declared depth
   limit, and **a truncated traversal reports truncation rather than returning "not stale"** — an unknown
   must never be rendered as a clean bill of health.

### Consequence

5. **No automatic invalidation and no automatic confidence change.** A stale dependent stays retrievable and
   usable, with its confidence untouched. The signal accompanies it; the judgement belongs to the consumer
   and, later, to revalidation.
6. **Recall must surface staleness.** Any interpretive object entering active cognition carries its staleness
   determination, including whether that determination was truncated. This is the point of the whole policy:
   a decision made on an unrechecked basis should record that it was (5.40, ADR-0002 rule 5).
7. **Revalidation is queued, bounded and offline.** Detected staleness enqueues a revalidation task processed
   during consolidation under a declared budget, highest-priority first. Queue depth and age are observable so
   a persistent backlog is visible rather than silent. Processing never occurs during an evaluation epoch
   (ADR-0004 rule 9), and its compute is metered as offline consolidation compute (ADR-0003 rule 7).
   Revalidation that changes an interpretation produces a **new version** (ADR-0005 rule 6); revalidation that
   confirms it re-pins to the current source versions, also as a new version.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| M-1 | Upstream supersession never mutates a dependent version | Hash every dependent version before and after an upstream supersede; assert unchanged, including its derivation edge set |
| M-2 | Staleness is derived, never read from persisted state as authoritative | Recompute staleness independently and compare against any cached value; assert agreement, and assert no code path reads a stored flag without that comparison |
| M-3 | Direct staleness is computed correctly | For each dependent, assert `stale_direct` ⟺ ∃ pinned source version ≠ that source object's head |
| M-4 | Inherited staleness is distinguished from direct | Assert every staleness result labels which kind it is and names the responsible ancestor |
| M-5 | Truncated traversal is reported, never silently clean | Force the depth limit in a fixture with a stale distant ancestor; assert the result carries `truncated = true` and is not reported as not-stale |
| M-6 | Confidence is unchanged by upstream supersession | Assert the dependent's confidence value is byte-identical before and after |
| M-7 | Stale objects remain retrievable and usable | Assert retrieval succeeds and the object is admissible to recall while stale |
| M-8 | Every object entering active cognition carries a staleness determination | Assert each recall result includes a staleness verdict and its truncation status |
| M-9 | Revalidation is enqueued on detection | Assert a queue entry exists for each detected direct staleness, deduplicated per dependent/source pair |
| M-10 | Revalidation never runs inside an evaluation epoch | Assert no revalidation processing timestamp falls between an epoch's open and close (ADR-0004 K-4) |
| M-11 | Revalidation produces new versions rather than editing | Assert the pre-revalidation version still resolves unchanged after processing |
| M-12 | Queue backlog is observable | Assert queue depth and oldest-entry age are exported per consolidation cycle |

## Evidence and rationale

The recommendation is the smallest policy that keeps all three properties the question demands:
**correctness** (rules 1–2, M-1, M-6), **revalidation capability** (rule 7, M-9, M-11), and **no expensive
eager recomputation** (rules 3–4, 7).

Options 4 and 5 are rejected for the same underlying reason from opposite directions: both convert a weak
signal into a strong automatic action. With no supersession classification available in v0, staleness cannot
support that weight. Option 4 treats every upstream edit as refutation; Option 5 treats every upstream edit
as requiring immediate expensive work. Both would make improving a pattern costly, which is a perverse
incentive in a system whose entire purpose is to improve its patterns.

Option 3 is rejected on a cleaner point. Confidence and staleness are different questions, and once summed
into one scalar they cannot be separated again. 8.5 makes exactly this argument for coverage versus
confidence, and the same logic applies here. The additional objection is dependency: v0 confidence semantics
are unresolved (D-11/T-2), so Option 3 would have this ADR silently take a position on a decision that has
not been surfaced.

Rule 4's laziness is what keeps blast radius from becoming an implementation problem before the Epistemic
Immune System exists. Because staleness is computed rather than propagated, a supersession costs nothing at
write time regardless of how large the dependent subtree is; cost is paid only by whoever asks, and only to
the depth they ask. This gives 9.44's blast-radius question a v0-shaped answer without building 9.44.

Rule 4's truncation clause deserves its own note. A depth-limited traversal that returns "not stale" when it
simply stopped looking is worse than no check, because it manufactures false assurance. Reporting truncation
keeps the system's ignorance visible, which is the distinction 8.6 draws between *unknown* and *answered*.

Rule 6 is where the policy earns its place. A staleness signal that never reaches cognition changes no
decision. Surfacing it at recall means that when an outcome is later analysed, the record shows whether the
decision rested on an unrechecked basis — which feeds directly into D-13's attribution question rather than
leaving it unanswerable.

## Consequences

**Easier:** improving upstream patterns without penalty; distinguishing "wrong" from "unrechecked" in
analysis; bounding the cost of a supersession regardless of subtree size; explaining after an outcome whether
a stale basis was involved.

**Harder:** every recall path must carry a staleness determination, which adds a computation to the read
path; consolidation gains a queue with its own budget and priority rule; a stale-but-fine object may be
revalidated repeatedly across cycles if the priority rule is poor.

**Newly required:** on-demand staleness computation with a declared depth limit and truncation reporting; a
revalidation queue with deduplication, priority, depth and age metrics; staleness fields on recall results.

**Constrained:** D-11 (confidence semantics) must not later fold staleness into confidence without
superseding rule 5. D-13 (activation trace) gains staleness as a recorded attribute of each activation.
D-19 (forgetting) interacts — an object stale for a long time is a candidate for decay, but that is a
forgetting decision, not this one.

**Newly discovered decision — recorded, not decided here:** **D-23 — supersession change classification.**
Whether a supersession declares its kind (correction, clarification, extension, narrowing, refutation) so
staleness can be weighted by consequence instead of treated uniformly. This would materially improve the
policy — most supersessions are harmless and currently produce identical signal to the dangerous ones — but
it is a separate durable decision about what a supersession event must carry, and settling it here would
repeat the scope expansion that produced D-21 and D-22.

## Reversibility

High. All six options remain reachable from this one, because it preserves the information every other option
would need: derivations are intact, confidence is unmodified, and staleness is computed rather than baked in.
Moving later to automatic invalidation or eager re-derivation requires only a policy change, not a migration.
Moving *from* Option 3 or 4 back to this one would not have been reversible, since degraded confidence and
invalidated objects do not record what they were before.

## Validation / falsification

Revisit if:

- the revalidation queue backlog grows monotonically across consolidation cycles, indicating the budget or
  priority rule is wrong, or that uniform treatment of supersessions is generating unusable signal volume —
  the latter would pull D-23 forward; or
- staleness proves so common that nearly every recalled object carries the signal, which would make it
  uninformative and argue for classification before signalling; or
- analysis of outcomes shows decisions made on stale bases were no worse than those on fresh bases, which
  would suggest the signal has no decision value at v0 scale and should be recorded but not surfaced.

Evidence that a dependent was *silently* relied upon after its basis was refuted — with no staleness signal
present — would falsify the claim that this policy is sufficient and would argue for Option 4's treatment of
the refutation case specifically, once D-23 makes that case identifiable.

## Outcome

Pending. No implementation exists.
