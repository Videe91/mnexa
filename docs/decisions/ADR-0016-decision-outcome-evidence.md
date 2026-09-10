---
id: ADR-0016
status: proposed
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/02-cognitive-architecture.md
  - docs/vision/06-world-model-causality-prediction.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0016 — Decision, Prediction, Action and Outcome Evidence

**Tier: D3 (constitutional).** Requires explicit owner approval.

Covers register entry **D-12**. Credit attribution remains **D-30**, deferred, and is not touched here.

## Decision question

What minimum immutable historical contract allows MNEXA to reconstruct what an agent decided, what it
predicted, what was actually executed, what outcome evidence was later observed, and which of those events are
structurally linked — without smuggling causal, correctness, utility, credit or blame claims into the
historical plane?

## Context

This is the last unsettled link in the v0 cognitive loop. Everything around it is fixed: ADR-0008 supplies
structural edges and their admission rules, ADR-0010 the four temporal concepts and the watermark, ADR-0013 the
cycle snapshot, ADR-0014 the `ContextAssembled` record a decision must reference backward.

The governing constraint is that this ADR sits one step before the boundary D-30 owns. Every structure it
creates will be read by consolidation and later by attribution, and the temptation at each step is to let a
link mean slightly more than it does.

## Options considered

### A — Collapsed decision/outcome record

One historical record containing decision, action and result.

| Case | Outcome under A |
|---|---|
| Delayed outcomes | **Impossible** — the record must commit before the outcome exists, or block indefinitely |
| Failed execution | Cannot distinguish decided-but-not-executed from executed |
| Multiple actions | Not representable |
| Multiple observations | Not representable |
| Predictions | Conflated with decisions |
| Partial outcomes | Not representable |
| Corrections | Would require mutating the record — forbidden by ADR-0002 rule 2 |
| Provenance | One record, many sources, no per-part attribution |
| Causal overstatement | **Co-location is itself a causal claim** |

The last row is the deepest objection. Putting a decision and its outcome in one record asserts they belong
together as one fact, which is precisely the inference ADR-0008 rule 3 keeps off the historical plane.
Rejected.

### B — Strict linear 1:1 chain

`DecisionMade → ActionExecuted → OutcomeObserved`, with `PredictionMade` where applicable, each link mandatory
and one-to-one.

Every assumption it encodes is false: a decision may produce two actions or none; an action may yield an
immediate response, a delayed effect and a later correction; a benchmark answer is evaluated with no action at
all; outcomes are not observed once and finally. Mandatory 1:1 linkage would force manufacturing records that
did not happen in order to satisfy the shape — the specific failure this ADR must avoid.

### C — Separate event types with explicit structural links

Four distinct `ExperienceRecord` event kinds, linked by ADR-0008 structural relations, with no cardinality
requirement beyond what admissible correlation supports.

**Recommendation: C.**

**No new canonical objects.** `DecisionMade`, `PredictionMade`, `ActionExecuted` and `OutcomeObserved` are
event kinds. Applying ADR-0007's test — none is versioned, superseded or revised, so none has a lifecycle —
`Decision`, `Prediction`, `Action` and `Outcome` are not promoted to primitives.

## Decision

Twenty-two rules. *(Proposed. Not approved.)*

### `DecisionMade`

1. **Minimum evidence.** Cognitive-cycle correlation identity; the cycle knowledge watermark (ADR-0013);
   a backward reference to the `ContextAssembled` record for that decision step; the exact recoverable decision
   output representation; the decision kind; the chosen option or action where applicable; model and provider
   attribution where model-generated; the runtime or agent identity that committed it; and the relevant policy
   and configuration identity.

2. **What it asserts.** *Model M produced content X and runtime R committed it as the decision.* **Never**
   *X is correct*. `committed_by` remains the trusted runtime under ADR-0002 rule 8; the model is never a write
   principal.

3. **The decision boundary is declared, not inferred.** A `DecisionMade` corresponds to an **externally
   identifiable commitment or choice boundary established by the agent/runtime contract**. It is emphatically
   *not* every generated token, every thought-like intermediate, every retrieval choice, or every internal
   model operation. Boundaries are pre-declared by the integration and pinned as configuration recorded in the
   trace — never reconstructed after the fact to suit an analysis.

4. **Decision kinds are typed.** v0 requires `task_response` and `tool_invocation`. The vocabulary is
   extensible on the same terms as ADR-0007's event-type list; `plan_commitment` and other kinds are admitted
   when a contract needs them, not pre-emptively.

5. **Private chain-of-thought is not recorded.** What is recorded is observable decision content and its
   provenance.

### Context linkage

6. **A decision references the context actually associated with that decision operation** — not the cycle as a
   whole. A cognitive cycle may contain several model and context steps, and one `ContextAssembled` record does
   not necessarily describe all of them.

7. **The relation is `decided_from`** (`DecisionMade` → `ContextAssembled`), backward-only under ADR-0008 rules
   4–5. It is admissible under ADR-0008 rule 2 — the runtime holds both identities and no inference is
   involved — and **extends that ADR's provisional vocabulary**, surfaced here for approval. ADR-0014 rule 20
   left this relation for D-12 to name.

8. **The watermark and the record's own sequence are distinct.** The persistent-knowledge watermark is the
   cycle's (ADR-0013 rule 3). The `DecisionMade` record's own later `commit_sequence` is never confused with it
   (ADR-0011 rule 3b).

### `PredictionMade`

9. **Kept distinct, and only where a falsifiable forecast was actually issued.** Minimum evidence: exact
   recoverable prediction content; the subject or target it concerns; the target variable or event where
   structured; the horizon, deadline or target time; units or value domain where applicable; model or agent
   attribution; cycle and context provenance; and any explicitly declared evaluation criterion.

10. **Time distinctions hold.** Per ADR-0010 rule 15, `PredictionMade.occurred_at` is *when the prediction was
    made*; the horizon or target time it concerns lives in the payload.

11. **Not required, not necessarily probabilistic.** No decision is required to contain a prediction, and no
    prediction is required to be probabilistic. **Probability or confidence values are never invented where the
    source produced none** — this ADR settles nothing about confidence semantics, which remain D-11.

12. **Structural pairing establishes no correctness.** Outcome evidence paired with a prediction does not by
    itself make the prediction correct, incorrect, well calibrated or badly calibrated. Where a deterministic
    benchmark or protocol evaluator explicitly computes a result, history records **that the evaluator produced
    that result**, attributed to the evaluator and protocol — never promoted to a correctness fact by the event
    type.

### `ActionExecuted`

13. **Intent is not execution.** A decision may select an action never successfully executed. `ActionExecuted`
    records what the runtime, tool or environment actually attempted or executed.

14. **Minimum evidence.** A backward `execution_of` reference to the corresponding `DecisionMade` **where such
    a decision exists**; the action, tool or capability identity; exact recoverable submitted arguments; the
    execution correlation or request identity; the target or environment where relevant; the operational
    execution status; the immediate transport or tool response where relevant; and runtime attribution.

15. **Status describes execution, never achievement.** `HTTP 200`, *tool invocation completed*, `exit 0`
    establish **operational completion**. They do **not** establish that the agent achieved its intended
    real-world objective — that is what outcome evidence is for, and the status field is named for the
    execution rather than for success to keep the two apart.

16. **Actions without a governing decision are permitted, and never fabricated.** Where a tool invocation is an
    agent choice, it is itself a commitment boundary and carries its own `DecisionMade` of kind
    `tool_invocation`, which the `ActionExecuted` references — no fiction required. Where an action was
    performed by deterministic runtime logic with no agent choice, **no `execution_of` edge is created and none
    is invented**. The contract must serve both one-shot decisions and agentic cycles containing intermediate
    tool interactions.

### `OutcomeObserved`

17. **Outcome is evidence, not a verdict.** `OutcomeObserved` records that some outcome, state or evaluation
    **was observed or reported**. It is never modelled as the final objective truth about what happened.

18. **Many observations per action or decision, all immutable.**

    ```text
    Action A
      ├── O1  immediate response
      ├── O2  delayed external effect
      └── O3  later correction or follow-up
    ```

    A later observation never rewrites an earlier one. Where an earlier observation was wrong, the accepted
    append-and-correct semantics apply (ADR-0002 rule 3, ADR-0008 `correction_of`).

19. **Absence of outcome means absence of evidence.** No `OutcomeObserved` record means *MNEXA has no recorded
    outcome evidence* — **never** *the action failed* or *nothing happened*.

    > `not observed` ≠ `observed absence`

    Where the system actively checks and observes *no change*, that is genuine observation evidence and may be
    recorded as such. **A negative outcome is never inferred from missing history.**

20. **Outcomes may be immediate, delayed, partial, intermediate, source-reported, benchmark-evaluated or later
    corrected.** No canonical final outcome per decision is required. Where a protocol or source labels an
    observation final, the **basis of that designation** is preserved rather than converted into universal
    truth.

### Structure, cardinality and attribution

21. **Structural edges, their meaning, and their explicit non-implications.** All are backward-only, admitted
    only on machine-verifiable correlation under ADR-0008 rule 2 — similarity and model inference are never
    sufficient.

    | Edge | Establishes | Does **not** establish |
    |---|---|---|
    | `execution_of`<br>Action → Decision | The runtime executed this as the action corresponding to that decision | That the decision *caused* the action; that the action faithfully implements the decision's intent; that the decision was good |
    | `outcome_for`<br>Outcome → Action or Decision | This observation was recorded for that event by verifiable correlation | That the action *caused* the outcome; that the outcome is complete or final; that the decision was right |
    | `evaluates_prediction`<br>Outcome → Prediction | This evidence was designated as evaluation evidence for that prediction | That the prediction was correct, incorrect or calibrated; that the evaluation is authoritative beyond its attributed source |
    | `decided_from`<br>Decision → Context | That context supplied the model-visible input for that decision | That any presented item influenced the decision — **D-30** |

22. **No 1:1 requirement, and no cardinality fiction.** One decision may have several actions; one action
    several outcomes; one prediction several evaluation evidences. Where direct admissible correlation exists,
    an outcome may relate to more than one prior event. Duplicates are **not** collapsed merely because
    payloads look similar — collapsing would assert an identity the correlation evidence does not support.

    Supported shapes include `Context → DecisionMade → OutcomeObserved` with **no** `ActionExecuted` — a
    benchmark answer, recommendation or classification evaluated directly — and
    `DecisionMade → ActionExecuted → (no outcome yet)`, which is an **incomplete evidence situation, not an
    implicit failure**.

    **Attribution:** any payload produced by a model, human, benchmark grader, external API or sensor preserves
    its provenance. History records *source S asserted or reported X* unless the trusted runtime can establish
    the narrower structural fact itself. **An attributed judgement is never upgraded into truth by being
    embedded in an `OutcomeObserved` record.**

    **Time:** ADR-0010's four concepts apply. A late outcome whose `occurred_at` precedes another event does
    not thereby become available to an earlier decision.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| X-1 | Every `DecisionMade` carries cycle identity, watermark and a backward `decided_from` reference | Assert all three non-null and resolvable |
| X-2 | `committed_by` on a decision is the trusted runtime, never a model | Assert `committed_by` ∉ model registry (ADR-0002 I-2) |
| X-3 | Decision content is exactly recoverable | Assert inline or content-addressed retained storage (ADR-0011 S-21) |
| X-4 | Decision kind ∈ the declared vocabulary | Assert enum membership; reject commit otherwise |
| X-5 | Decision boundaries are pre-declared and pinned | Assert the boundary declaration identity is recorded per decision; assert no boundary is derived post-hoc |
| X-6 | No chain-of-thought is recorded | Assert no field carries private reasoning traces |
| X-7 | A decision references the context of its own step, not the cycle | Fixture with two context steps in one cycle; assert each decision references its own `ContextAssembled` |
| X-8 | The decision's watermark is the cycle's, not the record's sequence | Assert watermark equals cycle watermark and differs from the record's `commit_sequence` |
| X-9 | Prediction horizon lives in payload, not in a record time field | Assert no time field carries the target time (ADR-0010 R-15) |
| X-10 | No probability or confidence is invented | Assert absent where the source produced none; assert never defaulted |
| X-11 | `evaluates_prediction` asserts no correctness | Assert no correctness field derives from the edge; assert evaluator results are attributed to the evaluator |
| X-12 | Execution status describes execution, not objective achievement | Assert the status vocabulary contains no field asserting goal attainment |
| X-13 | `execution_of` is optional and never fabricated | Assert runtime-initiated actions with no agent choice carry no `execution_of` edge |
| X-14 | Tool-invocation choices carry their own `DecisionMade` | Assert an agent-chosen tool invocation has a decision of kind `tool_invocation` |
| X-15 | Multiple outcomes per action are permitted and all immutable | Assert several `outcome_for` edges are admissible; assert no earlier outcome is mutated by a later one |
| X-16 | Absence of outcome is never read as failure | Assert no path infers a negative outcome from a missing record; assert observed-no-change is a distinct positive record |
| X-17 | Finality designations preserve their basis | Assert any final label names the protocol or source that designated it |
| X-18 | All four edge types are backward-only and correlation-admitted | Assert ADR-0008 P-3, P-4 and P-10 hold for each |
| X-19 | No 1:1 cardinality is enforced anywhere | Assert one-to-many is admissible on every edge; assert similar payloads are not auto-collapsed |
| X-20 | Decisions without actions and actions without outcomes are both valid | Assert neither shape is rejected nor flagged as incomplete history |
| X-21 | External payloads retain source attribution | Assert grader, API, human and sensor payloads name their source |
| X-22 | No causal, credit or blame field exists | Assert no `causal_weight`, `influence_score`, `memory_credit`, `blame`, utility-attribution or "caused" field, except as explicitly attributed estimate content |

## Evidence and rationale

**Option A's disqualifying flaw is representational, not practical.** Its practical failures — delayed
outcomes, multiple observations, corrections — are individually fatal, but the structural one matters more: a
record containing both a decision and its outcome asserts that they are one fact. That is a causal claim made
by schema rather than by anyone deciding to make it, which is exactly how this project has repeatedly found
truth claims entering the historical plane sideways.

**Option B fails on a subtler version of the same thing.** Requiring a 1:1 chain does not merely fail to
represent real shapes; it *forces the shapes to be falsified*. An agent that invokes three tools and answers
once must, under B, produce two fictitious decisions or drop two real actions. Manufactured history is worse
than absent history, because it is indistinguishable from the real thing at read time.

**Rule 16 resolves the intermediate-tool problem without inventing anything.** The tempting fix is to attach
intermediate actions to the eventual final decision, which would assert a correspondence that did not exist —
the tool call happened *before* that decision and was not its execution. Treating an agent-chosen tool
invocation as its own commitment boundary makes the real structure representable, and making `execution_of`
optional handles the remaining case where the runtime acted with no agent choice at all. Neither branch
requires a fabricated record.

**Rule 19 is the most important thing in this ADR and the easiest to violate downstream.** Consolidation will
want to know whether decisions succeeded, and the shape of the data invites treating a missing outcome as a
failure — silence reads as bad news. It is not evidence at all. Vision 6.37 makes the same distinction for the
world model, requiring MNEXA to understand *absence* rather than infer from it. A system that reads missing
outcomes as failures would systematically penalise actions whose effects are slow, external or simply
unobserved, and would do so invisibly, since no record would exist to audit. The `observed no change` case is
the counterpart: it is a genuine positive observation and belongs in history.

**Rule 21's table exists because the non-implications are where this contract does its work.** Each edge is
individually innocuous and collectively they describe a chain from decision to outcome — which is exactly the
shape a causal reading wants. Documenting what each edge does *not* establish, next to what it does, is what
prevents the chain being read as a causal narrative by a later consumer who never saw this ADR. It continues
the pattern applied to supersession (ADR-0006), `correction_of` (ADR-0008), retrieval scores (ADR-0011) and
suppression reasons (ADR-0014): the system records what happened or what a source asserted, never what is true.

**Rule 15's carefulness about "success" is not pedantry.** A tool returning `exit 0` is the most available
success-shaped signal in an agentic system, and it measures whether the call completed, not whether the task
advanced. Naming the field for execution rather than success removes the invitation to treat the two as one.

**Rule 12 keeps prediction scoring honest without deciding it.** A deterministic grader's output is a fact
about the grader. Recording it as *the evaluator computed this result* preserves its usefulness while leaving
open who is right if the grader is later found faulty — and it avoids this ADR quietly settling D-11's
confidence semantics or D-30's attribution through the back door of a correctness field.

## Consequences

**Easier:** representing agentic cycles with intermediate tools honestly; accumulating delayed and corrected
outcome evidence without rewriting anything; distinguishing decided-but-not-executed from executed;
reconstructing a decision's exact model-visible input; keeping benchmark grading attributable.

**Harder:** four event types plus four edge types to implement and validate; boundaries must be declared in
advance by each integration; consumers must handle one-to-many everywhere rather than assuming a chain.

**Newly required:** a decision-kind vocabulary; a pre-declared, pinned decision-boundary declaration per
integration; an execution-status vocabulary named for execution; the `decided_from` structural relation.

**Proposed refinement to an accepted ADR, surfaced for approval:** **ADR-0008** — `decided_from` extends the
provisional structural relation vocabulary, as ADR-0014 rule 20 anticipated.

**Constrained or unblocked:**

- **D-07 (consolidation authority) — unblocked.** It now has the raw historical structure to ask what was
  decided, under which context and watermark, what was executed, what outcome evidence appeared, and which
  predictions were evaluated. **It is told none of** which memory deserves credit, whether the decision was
  wise, how strongly an action caused an outcome, what should be strengthened, or what should become a skill.
- **D-30 (credit attribution) — deferral condition (ii) satisfied.** The linkage evidence a later standard
  needs now exists. Rule 21 and X-22 keep every causal field out of the historical plane meanwhile.
- **D-11 (confidence)** — constrained by rule 11: no probability is invented where none was produced.
- **D-14 (port surface)** — must expose decision, prediction, action and outcome capture.
- **Benchmark Contract** — the shape `ContextAssembled → DecisionMade → grader result → OutcomeObserved` with
  no `ActionExecuted` is representable, with grader identity, version and protocol attributable. Two questions
  are left to it: **which** observation is scored where several exist, and how long absence of outcome is
  awaited before a run is judged incomplete. Neither is a durable semantic decision.

**No new durable decision uncovered.** Decision-boundary comparability *across different agent integrations*
was considered and is not a v0 concern: ADR-0003 rule 1 fixes one agent and one seat configuration across A, B
and C, so boundary declarations are identical between conditions and cannot bias the comparison. It becomes a
Benchmark Contract question only when comparing across integrations or domains.

## Reversibility

High for vocabularies, moderate for the event split. Decision kinds, execution statuses and edge types are
registry extensions. Merging the four event types later would be a genuine architectural change, but the
asymmetry favours the split: separate events can always be read together, while a collapsed record cannot be
decomposed into events that were never separately committed.

## Validation / falsification

Revisit if:

- declared decision boundaries prove impossible to state in advance for some agent architecture, indicating
  rule 3's pre-declaration requirement is too strong rather than its principle wrong; or
- the volume of `tool_invocation` decisions in agentic cycles dominates the ledger, suggesting the boundary is
  drawn too finely; or
- outcome evidence in practice almost never arrives after the immediate response, which would make rules 18 and
  20's generality unnecessary weight at v0 scale.

Evidence that a consumer read a structural edge as a causal claim **despite** rule 21's documented
non-implications would falsify the claim that documentation is sufficient, and would argue for edge names that
resist the misreading rather than for relying on the table.

## Outcome

Pending. No implementation exists.
