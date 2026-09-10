---
id: ADR-0010
status: accepted
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/06-world-model-causality-prediction.md
spec_refs: []
supersedes: []
---

# ADR-0010 — Temporal and Ordering Semantics

**Tier: D3 (constitutional).** Requires explicit owner approval.

Covers register entry **D-05**.

**Approval:** accepted by owner 2026-09-10, following three owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **`committed_at` added as a fourth concept.** The original concluded that `recorded_at` plus
   `commit_sequence` made a commit wall-clock unnecessary. That was wrong: a logical sequence carries
   *ordering* information, not *elapsed time*, so capture-to-commit latency and the wall-clock age of an
   interpretation were both unanswerable. — rules 6–7, R-1, R-6, R-17, R-22.
2. **`commit_sequence` strengthened to visibility/linearization order.** The original specified monotonic
   allocation, which permits a lower-numbered commit becoming visible after a higher one — retroactively
   changing the meaning of an already-published `AS_OF(N)`. — rule 9, R-18, R-19.
3. **Availability distinguished from cognitive use.** The original said commit order determines "what MNEXA
   knew". It determines only what was **eligible**. Three levels — durably available, presented/activated,
   actually used — must not collapse into one another. — rules 10–11, R-20, R-21.

The epoch-watermark refinement (rule 21) was approved in the same review.

## Decision question

What is the minimum temporal model that distinguishes when something happened in the world, when MNEXA
received evidence of it, and when it became durable available state — without collapsing the three?

## Context

Time is the one property every object carries, which is why D-05 blocks seven specification elements. Two
accepted decisions already fixed part of the answer: ADR-0005 L-7 and ADR-0008 P-3 both establish ordering by
**commit sequence** and both explicitly reject wall-clock time because timestamps collide and may be assigned
before commit. What remains is world time, receipt time, and how all three relate.

Vision 2.6 makes the stakes explicit — MNEXA must answer *what did we know at the time* and *which decision
was rational given the information available then*, and it names the failure directly: preventing hindsight
from corrupting historical reasoning. 6.20 requires predictions to survive so hindsight cannot rewrite them.
Neither is achievable with one timestamp.

### Three orders, only two usable

| Order | Source | Properties |
|---|---|---|
| **World order** | `occurred_at` | Partial at best. Frequently unknown, tied, or merely asserted by a source. Never total, never authoritative for influence |
| **Receipt** | `recorded_at` | Wall-clock. Descriptive. Collides, skews, can regress. **Not an ordering primitive** |
| **Commit order** | `commit_sequence` | Total, monotonic, deterministic. Authoritative for availability, influence and replay |

A clarification worth stating, because the register described three orders and one of them is ambiguous:
**"knowledge order" in the epistemic sense is commit order, not receipt order.** `recorded_at` describes when
evidence *arrived*; `commit_sequence` determines when it became *available to cognition*. Only the second
governs whether information could have influenced anything, because evidence sitting in a capture buffer has
influenced nothing. Receipt time remains useful for ingestion-delay and operational analysis and is never
consulted for epistemic questions.

## Options considered

### A — Single timestamp plus commit ordering

One time field per record, plus commit sequence.

What is lost depends on which timestamp is kept, and both choices lose something v0 needs:

- Keep only `occurred_at`: ingestion delay is uncomputable, so late arrival is undetectable. Outcome linkage
  (specification element 15) cannot distinguish an outcome observed promptly from one observed a week later,
  which is exactly the distinction ADR-0008 rule 7 preserved for relationships.
- Keep only `recorded_at`: world time is gone entirely. Vision 2.6's `STATE(t)` becomes unrepresentable and
  temporal-relevance recall (5.43) has nothing to reason over.

Anti-hindsight would still hold, since it rests on commit sequence — so A is *safe* but *impoverished*. It
fails on information loss, not on correctness.

### B — Minimal dual-time plus logical commit ordering

`occurred_at` (optional, qualified) + `recorded_at` + `commit_sequence`.

### C — Full bitemporal model

Valid-time and transaction-time intervals, temporal joins, and a temporal correction engine.

Strictly more capable and subsumes B. Requires interval algebra and correction machinery that the v0 YAGNI
list excludes, to serve corrections that B already handles by append-plus-projection (ADR-0002 rule 3).

### Evaluation

| Criterion | A | B | C |
|---|---|---|---|
| Replay | Adequate — rests on commit sequence | Adequate — same basis | Adequate |
| Provenance | Weak — cannot show acquisition lag | Strong | Strong |
| Late-arriving evidence | **Undetectable** | Detected via `recorded_at` − `occurred_at` | Detected, with intervals |
| Out-of-order events | Representable but indistinguishable from prompt ones | Representable and distinguishable | Representable |
| Decision/outcome linkage | **Loses observation lag** | Preserved | Preserved |
| Reproducibility | Strong | Strong | Strong |
| Hindsight leakage | Prevented | Prevented | Prevented |
| Temporal uncertainty | **Cannot express** | Expressible via optional/qualified `occurred_at` | Fully expressible |
| Implementation complexity | Lowest | Low | **High** |
| Future evolution | B and C both reachable | C reachable without migration | — |
| v0 necessity | Insufficient | **Sufficient** | Beyond need |

**Recommendation: B.** *(Proposed. Not approved.)* A is rejected for information loss that two specification
elements depend on; C is rejected on YAGNI, and remains reachable because B's fields are a subset of C's.

## Decision

Twenty-one rules.

### The four temporal concepts

1. **`occurred_at` — world/source time. Optional.** Applies only where there is an external event-time
   meaning. When world time is unknown the field is **absent**; no value is fabricated.

2. **`occurred_at` carries a basis, and only two are admissible on the historical plane:**

   | Basis | Meaning | What history establishes |
   |---|---|---|
   | `observed` | The trusted runtime directly observed the event time | That the runtime observed the event at T |
   | `asserted` | An external source supplied the time | That **source S reported event-time T** — not that the event objectively occurred at T |

   **The basis must be resolvable, not merely labelled.** An `asserted` time identifies the source whose
   timestamp claim is recorded; an `observed` time identifies the trusted observation basis. Existing
   ExperienceRecord provenance may satisfy this without a further standalone field — the requirement is that
   the source or observer can be resolved, not that a new field exists.

3. **Inferred event time is interpretive, never historical.** A time derived by reasoning may exist only as an
   Interpretation citing the records it was inferred from.

4. **`occurred_at` states its precision.** One granularity qualifier accompanies the value, and no time is
   recorded at finer precision than its basis supports. This is an enum, not an interval model.

5. **`recorded_at` — capture-boundary receipt time. Required on historical records.** A trusted runtime
   wall-clock observation of when evidence entered the MNEXA capture boundary.

6. **`committed_at` — durable-commit wall-clock time. Required on historical records and interpretive
   versions.** A trusted runtime wall-clock observation of when the record or version became committed and
   visible durable MNEXA state. This is operational and observability metadata, supporting:

   - capture-to-commit latency (`committed_at` − `recorded_at`);
   - approximate wall-clock age of an interpretation;
   - operational debugging;
   - consolidation timing and measurement.

7. **Neither `recorded_at` nor `committed_at` is ever an ordering primitive.** Clock skew, regression, ties
   and collisions must never override `commit_sequence` for epistemic replay or preexistence. **World-event
   time is never inferred from `committed_at`.**

8. **`commit_sequence` — authoritative logical ordering of durable state.** One sequence for the v0 MNEXA
   memory namespace, spanning immutable commits in **both** planes, so that:

   ```text
   source record committed        #100
   derived interpretation         #101
   ```

   mechanically proves strict preexistence for ADR-0005 L-7 and ADR-0008 P-3. Namespace-local, **not** global
   or civilization-wide; distributed ordering is outside v0.

### Linearization

9. **`commit_sequence` is visibility order, not allocation order.** A committed sequence number participates
   in a stable durable-state linearization. This must be impossible:

   ```text
   A allocated #100, still uncommitted
   B allocated #101, becomes visible          ← AS_OF(101) published
   A later commits and becomes visible as #100 ← AS_OF(101) has changed
   ```

   **The invariant:** *once durable state through watermark N has been exposed as committed, no durable object
   or version may later become newly visible with `commit_sequence ≤ N`.* Equivalently: **`AS_OF(N)` is
   immutable once N is a published, visible watermark.**

   Gaps are permitted. **Retroactive insertion beneath an exposed watermark is not.** The invariant spans both
   planes, because ADR-0005's derivation preexistence relies on the same order.

   *The implementation mechanism is not decided here.* Assigning sequence at commit linearization, holding the
   visible watermark behind unresolved lower sequences, or any other mechanism satisfying the invariant is
   admissible. D-18 may still decide whether failed commits consume sequence values.

### Eligibility, activation and use

10. **Three levels, never collapsed.**

    | Level | Claim | Established by |
    |---|---|---|
    | **1 — Durably available** | The object was committed at or before the cognitive watermark | `commit_sequence` |
    | **2 — Presented / activated** | It entered the relevant cognitive process | The historical cognition/activation trace, which **D-10 and D-13 will define** |
    | **3 — Actually used / attributed** | It influenced the outcome | Whatever evidence the later attribution contract permits |

    `commit_sequence` establishes **level 1 only**. It determines which durable intelligence was *eligible* to
    influence cognition as of a watermark. It does **not** prove the object was retrieved, assembled into
    context, activated, attended to, or used. **Level 2 does not imply level 3 either:** activation is not
    proof of causal influence.

    This separation is what later distinguishes *a useful memory existed and was eligible but recall failed to
    surface it* — vision 5.38's retrieval regret — from *reasoning ignored information it actually saw*. Those
    are different failures with different remedies, and collapsing the levels makes them indistinguishable.

11. **Anti-hindsight.** Nothing committed after a decision's cognitive watermark is eligible to have influenced
    it, however early its `occurred_at`. Given:

    ```text
    10:00  event actually occurs
    10:05  decision made
    10:07  MNEXA receives evidence
    10:08  evidence committed
    ```

    replay must **not** treat the 10:00 event as available to the 10:05 decision. This is a hard invariant.

12. **Every decision carries a knowledge watermark** — the commit sequence defining what was durably available
    to it. *Which record carries it is D-10's and D-12's to decide; this ADR requires only that one exist.*

13. **`AS_OF(N)`.** MNEXA must support reconstructing what durable intelligence was available as of commit
    sequence N, excluding everything with `commit_sequence > N` regardless of earlier `occurred_at`. An
    invariant on the answer, not a prescription for storage.

### Ordering discipline

14. **Late and out-of-order arrival is legal and normal.** `#200 occurred_at 14:00` followed by
    `#201 occurred_at 12:00` is valid. Commit order states when MNEXA acquired durable access; it asserts
    nothing about world-event order.

15. **`occurred_at` ordering implies nothing** — not causality, not knowledge availability, not decision
    influence, not provenance ancestry. Vision 2.8's prohibition applies to all four, not only causation.

16. **Historical reference rules are unchanged by lateness.** ADR-0008 rules 4–5 stand: inline references only
    to already-committed records, never forward. Where a relationship concerns a record not yet committed,
    `RelationshipRecorded` establishes it later. Late arrival is the case that mechanism exists for.

17. **Timestamps are never mutated.** Corrections append under ADR-0002 rule 3 and ADR-0008's `correction_of`.
    A "currently best temporal view" is a projection or interpretation over immutable history. No temporal
    correction engine in v0.

18. **Ties and uncertainty manufacture no order.** Identical, absent or coarse `occurred_at` produce no
    ordering. `commit_sequence` may order when MNEXA learned of them without claiming world order.

### Interpretive-version timing

19. **Interpretive versions carry `committed_at` and `commit_sequence`, and no `occurred_at`.**

    | Question | Answer |
    |---|---|
    | When did it become established durable state? | `committed_at` (wall-clock) and `commit_sequence` (order) |
    | When was it proposed? | Already on the historical production record — `ConsolidationProduced` — which the version cites. Not duplicated |

    An interpretation is not an event in the external world, and gains no `occurred_at` merely because
    `committed_at` now exists. Where the interpretation's **content** contains an explicitly modelled temporal
    claim, that claim lives inside its content and provenance — never as a version-level `occurred_at`, which
    would pretend the interpretation itself occurred in the world.

20. **Episode temporal extent is derived, never stored.** The *time covered by an episode* is a projection over
    its member records' `occurred_at` values, and must never be confused with *the time the Episode
    interpretation was created*, which is its `committed_at` and `commit_sequence`.

### Approved refinement to accepted ADRs

21. **Evaluation-epoch boundaries are identified by commit-sequence watermarks, not wall-clock timestamps.**
    Each epoch records its opening and closing `commit_sequence`, making epoch-membership checks exact and
    independent of clock behaviour.

    Applied to **ADR-0004** (the evaluation epoch throughout: rules 9, 13 and invariants K-4, K-9 … K-17) and
    to **ADR-0006** only where it genuinely uses the same epoch concept — rule 7 and M-10. It is **not**
    broadened to ADR-0006's freshness or staleness semantics, which carry no epoch meaning.

    Those ADRs' accepted history is not rewritten; the refinement is recorded here and noted in each.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| R-1 | Every historical record carries `recorded_at`, `committed_at` and `commit_sequence` | Schema constraint; assert all three non-null on every record |
| R-1b | Every interpretive version carries `committed_at` and `commit_sequence` | Schema constraint; assert both non-null on every version |
| R-2 | `occurred_at`, when present, carries a basis whose source or observer resolves | Assert basis ∈ {observed, asserted}; resolve the asserting source (for `asserted`) or the trusted observation basis (for `observed`) via the record's provenance; assert resolution succeeds |
| R-3 | No inferred world time on the historical plane | Assert no admissible basis denotes inference; assert inferred times exist only as Interpretations citing their evidence |
| R-4 | No world time is recorded at finer precision than its basis supports | Assert a precision qualifier accompanies every `occurred_at`; assert the value carries no significant digits beyond it |
| R-5 | `commit_sequence` is strictly increasing, total in the namespace, never reused or reordered | Assert strict monotonicity across all commits; assert no duplicate value; assert existing values are immutable |
| R-6 | Neither `recorded_at` nor `committed_at` establishes ordering or preexistence | Assert no preexistence, ordering or epistemic code path reads either field (extends ADR-0005 L-7, ADR-0008 P-3) |
| R-7 | `AS_OF(N)` excludes everything committed after N | Fixture with a late-arriving record whose `occurred_at` precedes N's world time; assert it is absent from `AS_OF(N)` |
| R-8 | Decision replay sees only what its watermark admits | Assert replay of a decision resolves to its watermark N and that nothing with `commit_sequence > N` is visible |
| R-9 | Every decision has a knowledge watermark | Assert a resolvable commit-sequence watermark exists for each decision record |
| R-10 | Interpretive versions carry `commit_sequence` and no `occurred_at` | Assert no `occurred_at` field on interpretive versions |
| R-11 | Episode temporal extent is derived, never stored | Assert no stored extent field; assert the projection recomputes from member `occurred_at` values |
| R-12 | Committed timestamps are never mutated | Recompute record content hashes after a temporal correction; assert originals unchanged and the correction is a separate appended record |
| R-13 | Late arrival is admissible | Assert a record whose `occurred_at` precedes an already-committed record's is accepted, not rejected |
| R-14 | No causal, influence, ancestry or availability conclusion is derived from `occurred_at` | Assert no code path compares `occurred_at` to determine any of the four |
| R-15 | `PredictionMade.occurred_at` is when the prediction was made | Assert the prediction horizon or target time is a payload field, not a record time field |
| R-16 | Epoch boundaries are recorded as commit sequences | Assert each epoch record carries opening and closing `commit_sequence`; assert epoch-membership checks compare sequences, not wall clocks |
| R-17 | `committed_at` is present and usable for elapsed-time measurement | Assert `committed_at` − `recorded_at` is computable per record and exported for observability |
| R-18 | `AS_OF(N)` is immutable once N is exposed as a visible watermark | Snapshot `AS_OF(N)` at exposure; re-evaluate after subsequent commits; assert the result is byte-identical |
| R-19 | No object becomes newly visible with `commit_sequence ≤` an already-exposed watermark | Fixture with a delayed lower-numbered commit; assert it either never becomes visible beneath the exposed watermark or the watermark was never exposed while it was unresolved |
| R-20 | Availability is never treated as activation | Assert no code path infers that an object entered cognition from its being committed before the watermark |
| R-21 | Activation is never treated as attributed use | Assert no code path infers causal influence from an activation record alone |
| R-22 | World-event time is never inferred from `committed_at` | Assert no path populates or derives `occurred_at` from `committed_at` |
| R-23 | Interpretive versions carry no `occurred_at`; temporal claims live in content | Assert no `occurred_at` field on interpretive versions; assert any modelled temporal claim resides in content/provenance |

## Evidence and rationale

The recommendation is close to the stated expectation, and the parts worth defending are where it goes
further.

**Rule 2's two-basis rule is the substance of the world-time answer.** The tempting design is a single
`occurred_at` field populated from whatever the source supplies. That would let a source's claim enter the
immutable plane as established fact, which is the same error ADR-0002 rules 9–10 prevented for model output
and ADR-0008 rule 11 prevented for relation semantics. The pattern is now consistent across three ADRs:
history records *that something was asserted*, never *that the assertion is true*. Rule 3 completes it by
keeping inferred times off the plane entirely, since an inferred time is a conclusion, not an observation.

**On whether receipt and commit wall-clock need separate concepts: they do.** An earlier draft concluded they
did not, reasoning that a commit wall-clock's uses were latency measurement and epoch-boundary determination,
and that sequences served both. That conflated two different questions. Sequences do serve boundary
determination better than clocks — rule 21 stands on that. But a logical sequence carries *ordering*
information and no *elapsed time*: the interval between `#100` and `#101` may be a millisecond or a week, and
nothing in the sequence distinguishes them. Capture-to-commit latency and the wall-clock age of an
interpretation are therefore unanswerable without `committed_at`. Rule 6 adds it as observability metadata,
and rule 7 keeps it firmly out of the ordering role where its clock behaviour would be dangerous.

**Rule 9 closes a gap that monotonic allocation leaves open.** Allocating sequence numbers in increasing order
is not the same as committing in that order. If `#101` becomes visible while `#100` is still in flight, and a
consumer observes `AS_OF(101)`, then `#100` landing afterwards changes what `AS_OF(101)` means — retroactively,
and silently. Every reproducibility guarantee in ADR-0003 and ADR-0004 rests on replay answering the same
question the same way, so a watermark whose contents can grow later is not a watermark. Stating the invariant
at the level of *visibility* rather than allocation leaves the mechanism free while making the guarantee
checkable (R-18, R-19).

**Rule 11 is the load-bearing invariant of this ADR.** It is also the one most likely to be violated by
accident, because the natural implementation of "what did we know then" is a query filtered by world time,
and that query is wrong in a way that produces plausible results. A replay filtered on `occurred_at ≤ 10:05`
would include the 10:00 event and produce a reconstruction in which the decision looks better- or
worse-informed than it was. Rule 13's `AS_OF(N)` gives the correct query a name so it becomes the default
rather than the careful choice. R-7's fixture — a late record whose world time precedes the watermark — is the
specific test that catches the wrong implementation.

**Rule 10's three levels prevent a subtler version of the same error.** Establishing that an object was
committed before a decision's watermark is easy and feels conclusive, and the tempting shorthand is to call
that "MNEXA knew it". It is not: eligibility is a property of the store, while knowing is a property of what
cognition actually received. Collapsing them would make every failure look like a reasoning failure, because
anything eligible and unused would appear to have been ignored. Keeping level 1 separate from level 2 is what
makes vision 5.38's retrieval regret expressible at all — the case where recall simply never surfaced an
eligible memory is a *retrieval* defect, and conflating it with reasoning would send every investigation to
the wrong subsystem. Keeping level 2 separate from level 3 matters for the same reason one hop further out:
an activated memory that made no difference is not evidence of influence, and treating it as such would make
attribution unfalsifiable.

**Rule 12 generalises vision 2.8 further than the vision states it.** The vision warns against `before`
becoming `caused`. The same illegitimate inference produces three other conclusions that matter here:
that MNEXA *knew* of an earlier event, that it *influenced* a later one, or that it is an *ancestor* of it.
All four are separately prohibited, and R-14 checks for all four, because forbidding only causation would
leave the other three available.

**Rule 15's treatment of coarse precision is what keeps rule 4 from needing interval algebra.** If a source
knows only the day, the honest representation is a day-precision value that participates in no ordering —
not an interval requiring interval arithmetic, and not a fabricated midnight timestamp that would silently
order it against everything else. Absent, coarse and tied all produce the same outcome: no order. That single
rule absorbs the entire temporal-uncertainty requirement at the cost of one enum field.

## Consequences

**Easier:** answering *what was available then* correctly by default; detecting and quantifying late arrival;
distinguishing an outcome observed promptly from one observed late; auditing whether a source's asserted time
was ever treated as fact; making epoch-membership checks exact.

**Harder:** every adapter must supply `occurred_at` provenance rather than a bare timestamp, or omit the field;
the commit sequencer needs a single serialization point in the v0 namespace, and its durability across
restarts becomes a real requirement; consumers must use `AS_OF(N)` rather than time-filtered queries, which is
a discipline the API should enforce rather than document.

**Newly required:** a commit sequencer providing stable visibility linearization for the namespace;
`occurred_at` basis and precision fields with resolvable source or observer; `committed_at` on records and
interpretive versions; a knowledge watermark per decision; epoch records carrying commit-sequence bounds.

**Constrained or unblocked:**

- **D-12 (decision/prediction/outcome linkage)** — unblocked on its remaining temporal dependency. It must now
  carry the knowledge watermark (rule 9) and may use `recorded_at` − `occurred_at` to represent observation
  lag. Rule 15 fixes that prediction horizon lives in payload, not in a time field.
- **D-10 (recall reproducibility)** — gains `AS_OF(N)` as the reproducibility primitive: a recall is
  reproducible if it is reproducible as of its watermark. Must decide which record carries the watermark.
- **D-13 (activation trace)** — activations are ordered by commit sequence; the watermark makes "what was
  available but not activated" (vision 5.40's *not activated* line) computable rather than aspirational.
- **D-18 (failure semantics)** — inherits sequencer durability, and must decide whether a failed commit
  consumes a sequence number. Rule 7 permits gaps, so either answer is admissible.
- **D-04 (identity semantics)** — unaffected.
- **ADR-0004 and ADR-0006** — rule 16 refines how their epoch checks are performed, without changing what
  they assert. Surfaced for approval, not applied silently.

**No new durable decision was uncovered.** Every question this ADR raised resolved inside its own scope or
landed on an already-registered decision — including after the three amendments, which added a field, a
linearization invariant and an epistemic distinction without opening a new question. It is the first ADR in
this sequence to add nothing to the register, which suggests the decision space is converging.

**YAGNI check.** No accepted v0 invariant required distributed clocks, vector or Lamport clocks, cross-agent
ordering, global sequencing, temporal logic, causal ordering or interval algebra. Strict preexistence
(ADR-0005 L-7, ADR-0008 P-3) needs only a single-namespace total order, which rule 7 supplies. Had any
accepted invariant required more, this ADR would have stopped and reported rather than expanding v0.

## Reversibility

High. Moving to Option C later is additive — `occurred_at` with basis and precision is a degenerate valid-time
interval, and `commit_sequence` is already a transaction-time order, so bitemporal intervals can be layered
without migrating existing records. Removing fields would be lossy, which is the correct asymmetry.

The single-namespace commit sequence is the constraint most likely to need revisiting, and it will: collective
phases spanning agents cannot share one sequencer. That is expected and out of v0 scope, and the sequence's
namespace-local definition means a later distributed scheme can subsume it rather than contradict it.

## Validation / falsification

Revisit if:

- adapters routinely cannot supply an `occurred_at` basis, leaving world time absent so often that temporal
  recall has nothing to work with — which would question whether the field earns its place at all; or
- the precision qualifier proves insufficient for a source whose uncertainty is genuinely an interval rather
  than a granularity, which would pull Option C's interval representation forward; or
- the single serialization point for commit sequence becomes a throughput constraint at v0 scale, which would
  be surprising for a single-agent experiment and would indicate the namespace boundary is drawn wrongly.

Evidence that a hindsight leak occurred **despite** R-7 and R-8 would falsify the claim that commit-sequence
watermarking is sufficient, and would most likely indicate a path that queried world time directly rather than
a defect in the model.

## Outcome

Pending. No implementation exists.
