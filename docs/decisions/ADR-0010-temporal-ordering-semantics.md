---
id: ADR-0010
status: proposed
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

Sixteen rules.

### The three fields

1. **`occurred_at` — world/source time. Optional.** When the event's world time is unknown, the field is
   **absent**. No value is fabricated.

2. **`occurred_at` carries a basis, and only two bases are admissible on the historical plane:**

   | Basis | Meaning | What history establishes |
   |---|---|---|
   | `observed` | The trusted runtime directly observed the event time | That the runtime observed the event at T |
   | `asserted` | An external source supplied the time | That **source S reported event-time T** — not that the event objectively occurred at T |

   An external timestamp appearing in a payload does **not** become an objectively true world-time assertion
   by being recorded. The source identity is recorded alongside an `asserted` time.

3. **Inferred event time is interpretive and never historical.** A time derived by reasoning — from context,
   from ordering, from a model — may exist only as an Interpretation citing the records it was inferred from.
   It is never written to `occurred_at`.

4. **`occurred_at` states its precision.** A single granularity qualifier (for example second, minute, hour,
   day) accompanies the value, and no time is recorded at finer precision than its basis supports. This is one
   enum, not an interval model — coarse precision simply yields no ordering under rule 15, rather than
   requiring interval algebra.

5. **`recorded_at` — receipt time. Required.** A trusted MNEXA runtime wall-clock observation of when the
   evidence entered the capture boundary. It supports ingestion-delay measurement, provenance, operational
   debugging and latency analysis.

6. **`recorded_at` is never an ordering primitive.** Wall clocks collide, skew and regress, and concurrent
   events share timestamps. No preexistence check, no ordering decision and no epistemic determination may
   read it. **No separate commit wall-clock field is introduced** — see rule 16 for why the operational need
   it would serve is better met by commit sequence.

7. **`commit_sequence` — logical admission order. Required.** One monotonically strictly increasing sequence
   for the v0 MNEXA memory namespace, spanning immutable commits in **both** the historical and interpretive
   planes, so that:

   ```text
   source record committed at        #100
   derived interpretation committed  #101
   ```

   mechanically proves strict preexistence for ADR-0005 L-7 and ADR-0008 P-3. Values are never reused and
   never reordered; gaps are permitted. **This is a single-namespace sequence, not a global or
   civilization-wide one** — distributed and collective ordering is outside v0 and will require its own
   decision when collective phases arrive.

### What governs influence

8. **Availability, not occurrence, determines influence.** Whether information could have influenced
   cognition is determined solely by whether it was committed before the decision's cognitive boundary.
   Given:

   ```text
   10:00  event actually occurs
   10:05  decision made
   10:07  MNEXA receives evidence
   10:08  evidence committed
   ```

   a replay must **not** allow the 10:00 event to influence the 10:05 decision, however much earlier its
   `occurred_at` is. This is a hard anti-hindsight invariant, not a default.

9. **Every decision carries a knowledge watermark.** A decision is associated with the commit sequence
   defining what was durably available to it, so replay has a specific N. *Which record carries the watermark
   — `ContextAssembled`, the decision record, or another — is D-10's and D-12's to decide; this ADR requires
   only that one exist.*

10. **`AS_OF(N)`.** MNEXA must support reconstructing what durable intelligence was available as of commit
    sequence N. That reconstruction excludes everything with `commit_sequence > N`, regardless of any earlier
    `occurred_at`. This is an invariant on the answer, not a prescription for storage.

### Ordering discipline

11. **Late and out-of-order arrival is permitted and normal.**

    ```text
    commit #200   occurred_at = 14:00
    commit #201   occurred_at = 12:00
    ```

    is valid; the second record simply arrived late. Commit order states when MNEXA acquired durable access to
    information. It asserts nothing about world-event order.

12. **`occurred_at` ordering implies nothing.** Earlier `occurred_at` does not imply causality, knowledge
    availability, decision influence, or provenance ancestry. Vision 2.8's prohibition — `A happened before B`
    must never silently become `A caused B` — applies to every one of these, not only to causation.

13. **Historical reference rules are unchanged by lateness.** ADR-0008 rules 4–5 stand: inline references
    point only to already-committed records, and forward references are never permitted. If an event arrives
    whose structural relationship concerns a record not yet committed, no inline edge is created; once both
    exist, `RelationshipRecorded` establishes the relationship where admissible evidence supports it. Late
    arrival is precisely the case that mechanism was built for.

14. **Timestamps are never mutated.** If a source or runtime later establishes that a recorded event time was
    wrong, the original record is preserved and the correction appended under ADR-0002 rule 3 and ADR-0008's
    `correction_of`. A "currently best temporal view" is a **projection or interpretation** over immutable
    history, never a rewrite. No temporal correction engine is built in v0.

15. **Ties and uncertainty manufacture no order.** Identical `occurred_at` values produce no ordering between
    records. Absent or coarse-precision world time produces no ordering. `commit_sequence` may order when
    MNEXA learned of them without claiming that was their world order.

### Consequential refinement

16. **Epoch bounds are recorded as commit sequences.** ADR-0004's evaluation epoch and ADR-0006's revalidation
    scheduling currently compare wall-clock timestamps to epoch boundaries. Recording each epoch's opening and
    closing **commit sequence** makes those checks exact and removes their dependence on clock behaviour. The
    invariants themselves are unchanged; only the comparison becomes reliable. *This refines accepted ADRs and
    is surfaced here for approval rather than applied silently.*

### Interpretive-version timing

Interpretive versions are epistemic artefacts, not world events, and are **not** given `occurred_at`.

| Question | Answer |
|---|---|
| When was it proposed? | Already carried by the historical production record — `ConsolidationProduced` — which the version cites. Not duplicated on the version |
| When did it become established? | Its `commit_sequence` |
| What is its ordering? | `commit_sequence`, as for everything else |

For **Episode** specifically, the *time covered by the episode* is derived on demand from the `occurred_at`
values of the ExperienceRecords it groups. It is a **projection**, never a stored field, and it must never be
confused with *the time the Episode interpretation was created*, which is its commit sequence.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| R-1 | Every historical record carries `recorded_at` and `commit_sequence` | Schema constraint; assert both non-null on every record |
| R-2 | `occurred_at`, when present, carries a basis and — for `asserted` — a source identity | Assert basis ∈ {observed, asserted}; assert source identity non-null when `asserted` |
| R-3 | No inferred world time on the historical plane | Assert no admissible basis denotes inference; assert inferred times exist only as Interpretations citing their evidence |
| R-4 | No world time is recorded at finer precision than its basis supports | Assert a precision qualifier accompanies every `occurred_at`; assert the value carries no significant digits beyond it |
| R-5 | `commit_sequence` is strictly increasing, total in the namespace, never reused or reordered | Assert strict monotonicity across all commits; assert no duplicate value; assert existing values are immutable |
| R-6 | `recorded_at` never establishes ordering or preexistence | Assert no preexistence, ordering or epistemic code path reads `recorded_at` (extends ADR-0005 L-7, ADR-0008 P-3) |
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

## Evidence and rationale

The recommendation is close to the stated expectation, and the parts worth defending are where it goes
further.

**Rule 2's two-basis rule is the substance of the world-time answer.** The tempting design is a single
`occurred_at` field populated from whatever the source supplies. That would let a source's claim enter the
immutable plane as established fact, which is the same error ADR-0002 rules 9–10 prevented for model output
and ADR-0008 rule 11 prevented for relation semantics. The pattern is now consistent across three ADRs:
history records *that something was asserted*, never *that the assertion is true*. Rule 3 completes it by
keeping inferred times off the plane entirely, since an inferred time is a conclusion, not an observation.

**Rule 6 answers the question of whether receipt and commit wall-clock need separate concepts: they do not.**
The operational uses of a commit wall-clock are latency measurement and boundary determination. The first is
adequately served by `recorded_at` plus commit sequence. The second — deciding whether a commit falls inside
an evaluation epoch — is better served by sequences than by clocks, which is what rule 16 proposes. Adding a
third time field to serve a need that a sequence serves more reliably would be overloading the model rather
than clarifying it.

**Rule 8 is the load-bearing invariant of this ADR.** It is also the one most likely to be violated by
accident, because the natural implementation of "what did we know then" is a query filtered by world time,
and that query is wrong in a way that produces plausible results. A replay filtered on `occurred_at ≤ 10:05`
would include the 10:00 event and produce a reconstruction in which the decision looks worse-informed or
better-informed than it was. Rule 10's `AS_OF(N)` gives the correct query a name so it can be the default
rather than the careful choice. R-7's fixture — a late record whose world time precedes the watermark —
is the specific test that catches the wrong implementation.

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

**Newly required:** a monotonic commit sequencer for the namespace; `occurred_at` basis and precision fields;
source identity for asserted times; a knowledge watermark per decision; epoch records carrying commit-sequence
bounds.

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
landed on an already-registered decision. That is worth stating plainly: it is the first ADR in this sequence
to add nothing to the register, which suggests the decision space is converging rather than expanding.

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
