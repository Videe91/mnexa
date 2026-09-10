---
id: ADR-0004
status: accepted
date: 2026-09-10
scope: scientific
vision_refs:
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0004 — Hidden Evaluation Isolation

**Tier: D3 (constitutional / scientific). Requires explicit owner approval.**

Covers register entry **D-17**.

**Approval:** accepted by owner 2026-09-10, following two owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **Read-only extended from the memory store to all decision-influencing state.** The original proposal
   froze the canonical MNEXA snapshot but said nothing about session history, working memory, adaptive
   retrieval statistics, caches, tool-side state or process-global state — every one of which can carry a
   result from one evaluation task into the next. Introduces the *evaluation epoch* and the *Evaluation
   Evidence Sink*. — rules 8–10, invariants K-9 … K-13.
2. **Exposure / burn rule added.** The original had no notion that an evaluation instance stops being
   pristine once its results have been seen. Introduces the SEALED → EXPOSED → RETIRED lifecycle and the
   epoch freeze. — rules 11–13, invariants K-14 … K-17.

Both amendments close V3, V4, V5 and V6 more tightly without changing the core decision (Option A).

## Decision question

What structurally guarantees that hidden evaluation instances cannot enter the experience, memory or
consolidation path used to build the intelligence being evaluated?

## Context

`.claude/rules/scientific-method.md` is unambiguous: "Do not inspect, retrieve, memorize, prompt with, tune
against, or special-case hidden evaluation instances." ADR-0003 controls *resources*. This ADR controls
*data*. They are separate threat models with separate enforcement points, which is why they are separate
ADRs.

MNEXA makes this harder than it is for a conventional system, for a reason intrinsic to its design. The
vision instructs it to capture broadly — 3.4: "Every meaningful interaction creates an immutable Experience
Record" — and then to metabolize what it captured into reusable intelligence. A system built to remember
everything it encounters is structurally predisposed to remember the test. The breadth that makes MNEXA
work is exactly what makes accidental contamination easy.

The contamination surface is also wider than "did an eval task get ingested", because MNEXA records
outcomes, not just inputs (10.18), and consolidates across records (3.15). Six distinct vectors exist:

| # | Vector | Mechanism |
|---|---|---|
| V1 | **Direct ingestion** | An evaluation instance is captured as an experience |
| V2 | **Outcome leakage** | The *outcome* of an evaluation task enters memory even though the task text did not |
| V3 | **Within-eval cross-contamination** | Task 1's result enters memory before task 50 runs, so memory has learned from the evaluation set mid-pass |
| V4 | **Operator leakage** | A human inspects evaluation failures and then tunes memory, prompts or policy |
| V5 | **Repeated-evaluation leakage** | Evaluation is run, memory consolidates, evaluation is run again — training on the test set across runs |
| V6 | **Selection leakage** | Which experiences to keep, or which memory version to promote, is chosen by evaluation performance |

V3 is the one most likely to be built in by accident, because the vision's own loop
(`outcome → consolidation → better future recall`, 3.47) *wants* outcomes to flow into memory. Running that
loop live during evaluation converts a held-out set into training data partway through the pass, and the
resulting number is uninterpretable rather than merely optimistic.

V5 and V6 are the ones most likely to happen through ordinary diligence — rerunning an experiment after a
fix, or keeping the memory snapshot that scored best.

Out of scope but stated: the frozen model's pretraining may already contain evaluation material. That is not
controllable here. It is non-differential across A, B and C because ADR-0003 rule 1 fixes the same model in
every condition, so it cannot produce a spurious *difference* between conditions — which is what the v0
claim rests on. Model identity is recorded so the limitation is auditable.

## Options considered

### Option A — Frozen-snapshot, read-only evaluation

Memory state is pinned and content-hashed before an evaluation pass. During evaluation the memory write
path is *disabled as a capability*, not merely unused. Evaluation reads memory; nothing writes back.

Benefits: closes V1, V2, V3, V5 and V6 structurally rather than by policy. Makes contamination detectable
after the fact by snapshot hash comparison. Gives a clean claim: memory was built only from the experience
corpus and evaluated on instances it never saw.

Costs: the evaluated pass does not exercise the live outcome→consolidation loop, so v0's primary proof
measures *accumulated* intelligence rather than *continual* learning. The loop is still exercised — during
the experience phase — but not under evaluation.

Reversibility: high. A continual-learning variant can be added later as a separately labelled experiment,
mirroring ADR-0003 rule 5's treatment of heterogeneous consolidation.

### Option B — Online evaluation with live memory writes

Evaluation tasks write to memory as they run, testing continual learning directly.

Benefits: exercises the full vision loop; closer to real deployment; would be a stronger result *if* it were
interpretable.

Costs: V3 is not a bug in this design but its defining property — every task after the first is evaluated
against memory that has seen part of the evaluation set. The held-out property is destroyed within a single
pass, and no post-hoc adjustment recovers it at v0 sample sizes. Also forecloses rerunning an evaluation,
since the second run faces contaminated memory.

Reversibility: low within a result — a contaminated pass cannot be decontaminated, only discarded.

### Option C — Declared corpus partition only

Experience and evaluation corpora are declared disjoint by policy; writes remain enabled.

Benefits: minimal machinery; permits the live loop.

Costs: closes V1 only, and only by convention. Leaves V2 through V6 entirely open. Policy-level separation
fails exactly when it matters most — under schedule pressure, after a disappointing result, at the hands of
whoever is most convinced they know which instances are safe.

Reversibility: high, but results produced under it carry an unfalsifiable contamination caveat.

## Decision

**Recommendation: Option A.** *(Proposed. Not approved.)*

Seven rules.

### Structural isolation

1. **Disjoint corpora by instance identity.** The experience corpus and the hidden evaluation corpus are
   disjoint sets of registered instance identifiers. Disjointness is asserted, not assumed.
2. **No route from capture to evaluation data.** The experience-capture path holds no credential, mount,
   route or handle by which it can read the evaluation corpus. Isolation is a property of the deployment,
   not a rule the capture code is trusted to follow.
3. **Evaluation is read-only.** During an evaluation pass, memory write capability is *absent* — the write
   ports are not exposed to the evaluation harness, rather than exposed and left unused.

### Verifiable state

4. **Snapshot pinning.** Memory state is content-hashed immediately before an evaluation pass and again
   immediately after. The two hashes must match. The pre-pass hash is recorded in the experiment record and
   is what the result is attributed to.
5. **Provenance non-intersection.** No historical record's provenance may resolve to a registered
   evaluation instance identifier. This is checkable because ADR-0002 rules 8–11 already require every
   object to carry resolvable ancestry.

### Human and procedural vectors

6. **Inspection is a recorded event.** Operator inspection of evaluation results is recorded. Any memory,
   prompt, policy or configuration change that follows inspection of evaluation results — and precedes a
   further evaluation run — marks subsequent runs as contaminated for the primary proof. Such runs may still
   be reported, labelled, as development iterations.
7. **Re-evaluation uses the pinned snapshot or is labelled a variant.** Repeating an evaluation against an
   evolved memory state is permitted only as a separately labelled variant, excluded from primary-proof
   aggregation. Selection of a memory snapshot by evaluation performance is prohibited for the primary
   proof.

### Ephemeral state and the evidence sink

8. **Fresh ephemeral state per evaluation task.** Each evaluation task begins with fresh ephemeral
   task/runtime cognitive state. No result from an earlier evaluation task may influence a later one
   through any of: conversation or session history; working memory; mutable retrieval or reranking state;
   adaptive retrieval statistics; caches whose contents can affect decisions; temporary files; tool-side
   persistent state; process-global adaptive state; or any other writable state on the subject's decision
   path. The list is illustrative of a general rule — *nothing writable on the decision path survives a
   task boundary* — not an exhaustive allowlist to be read narrowly.

9. **The permitted exception is frozen treatment state.** Condition C may access the same pre-evaluation
   frozen MNEXA snapshot across all tasks. That snapshot must not change at any point during the
   **evaluation epoch**. This is the only state permitted to span tasks, and it is read-only.

10. **The Evaluation Evidence Sink is one-way.** The harness may record outputs, traces, timings, outcomes
    and scores into a separate Evaluation Evidence Sink. The sink lies outside the evaluated agent/MNEXA
    cognitive path and has no read path back into the evaluated subject until the evaluation epoch has
    closed. The distinction is explicit:

    - **MNEXA / agent state** — frozen and read-only during primary evaluation.
    - **Evaluation evidence** — writable by the harness for measurement, inaccessible to the evaluated
      system during the epoch.

### Exposure and epoch freeze

11. **Exposure lifecycle.** Every evaluation instance, or evaluation-set version, carries a recorded
    exposure state:

    ```text
    SEALED  →  EXPOSED  →  RETIRED FROM NEW CONFIRMATORY CLAIMS
    ```

    An instance ceases to be pristine — becomes **EXPOSED** — once its content, behavioural result, failure
    information or answer-relevant evidence has been shown to a model, an operator, or a development process
    capable of influencing subsequent system changes.

12. **What an exposed set may still be used for.** An exposed set remains usable for regression testing,
    debugging and exploratory experiments. After system changes influenced by its results, it must not be
    represented as a fresh hidden holdout supporting a new primary confirmatory claim.

13. **Epoch freeze.** For a predeclared primary evaluation epoch, the following are frozen before the epoch
    begins and unchanged until it closes: architecture and configuration; benchmark contract version; the
    A/B/C treatment definitions; and the resource controls of ADR-0003. In addition, detailed results from
    an earlier condition must not be used to alter a later condition inside the same epoch.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| K-1 | Experience and evaluation corpora share no instance identifier | Set intersection over registered identifiers; assert empty |
| K-2 | The capture path cannot read the evaluation corpus | Negative access test from the capture context; assert access denied, plus config assertion that no credential/route is granted |
| K-3 | Memory write capability is absent during an evaluation pass | Interface assertion that write ports are unexposed to the harness; attempted write in a test run must fail as unavailable, not merely be skipped |
| K-4 | Memory state is unchanged across the whole evaluation epoch | Content-hash the memory snapshot at epoch open and close, and sample between tasks; assert all equal |
| K-5 | No historical record's provenance resolves to an evaluation instance | Traverse provenance for all records; assert no terminal identifier ∈ evaluation registry |
| K-6 | Each result is attributed to a recorded pre-pass snapshot hash | Assert the experiment record carries a non-null pre-pass hash matching the pinned snapshot |
| K-7 | Runs following post-inspection changes are marked contaminated for the primary proof | Compare inspection-event timestamps against memory/config change timestamps; assert any run after such a sequence carries the contaminated label |
| K-8 | Variant and contaminated runs are excluded from primary aggregation | Assert primary aggregation contains only runs labelled clean |
| K-9 | Each evaluation task starts from fresh ephemeral state | Assert a new execution context per task (distinct container/process/session identifiers); assert no subject-side session or thread identifier is reused across tasks |
| K-10 | No writable surface on the decision path persists across tasks | Enumerate writable mounts, cache directories and temp paths on the decision path; assert each is read-only or empty at task start; hash them at task start and end and assert the start state is restored |
| K-11 | Decision-affecting caches are absent; cost/latency-only caches are disclosed | Assert no cache whose contents can alter model output is on the decision path; record any provider-side prompt cache in the experiment record, since it affects timing measurements even when it does not affect decisions |
| K-12 | The evaluated subject cannot read the Evaluation Evidence Sink during the epoch | Negative access test from the subject context; assert sink credentials and routes are absent from the subject environment; assert sink read access is granted only after epoch close |
| K-13 | Frozen treatment state is the only state spanning tasks | Diff the subject-visible state surface between consecutive tasks; assert the only non-empty difference is the pinned read-only snapshot |
| K-14 | Every evaluation instance or set version carries a recorded exposure state | Assert non-null exposure state for every registered instance/set version |
| K-15 | Primary confirmatory claims cite only instances SEALED at epoch open | Assert every instance contributing to a primary claim had exposure state SEALED at the epoch-open timestamp |
| K-16 | Epoch-frozen artefacts are unchanged across the epoch | Hash architecture/config, benchmark contract version, treatment definitions and resource controls at epoch open and close; assert all equal |
| K-17 | No later condition is altered after detailed results from an earlier condition in the same epoch | Compare per-condition configuration change timestamps against earlier conditions' result-availability timestamps; assert no change follows |

K-10 and K-13 are the practical answer to "detect state drift where practical". Exhaustive proof that no
writable byte influenced a decision is not achievable; hashing the declared writable surface at task
boundaries and diffing the subject-visible state between tasks detects the realistic failures — a cache that
was supposed to be cleared, a temp file left behind, a session identifier quietly reused.

K-5 is available only as a consequence of ADR-0002. Because provenance is resolvable and terminates in
historical records, "did anything in memory descend from an evaluation instance" is a graph query rather
than an act of faith. The provenance decision made the isolation decision mechanically checkable.

## Evidence and rationale

Option C is the status quo of most ML practice and is rejected because it defends against only the vector
nobody accidentally trips. The vectors that actually contaminate results — V3 through V6 — are all
*procedural*, and policy cannot defend against procedure. Rules 2 and 3 convert the two most important
defences from "the code is supposed to" into "the capability is not present", which is the difference
between an invariant and an intention.

Option B is rejected reluctantly, because it is the more faithful realization of the vision's loop. The
decisive point is that V3 is not a defect of a particular implementation of B but its structure: consolidation
during evaluation means later evaluation tasks are judged against memory containing earlier evaluation
tasks. The vision itself is explicit that MNEXA's value is producing intelligence about *unseen related*
situations (10.41, 10.47). A design that lets the evaluation set enter memory mid-pass cannot report on
unseen situations at all, so it cannot test the thesis it exists to test.

That said, Option A's cost should be stated plainly rather than minimized: the primary v0 proof will
measure accumulated intelligence under frozen memory, not continual learning. The compounding loop the
vision describes (3.47) runs during the experience phase and is exercised there; it is switched off during
measurement. That is the standard train/test discipline, and it means a positive v0 result supports "MNEXA
accumulated transferable intelligence" and does *not* by itself support "MNEXA learns continuously during
deployment". Rule 7's variant path is where the latter claim would later be earned.

### Why freezing the memory store was not enough

The original proposal froze the canonical MNEXA snapshot and treated that as the read-only guarantee. It was
not. The snapshot is only one of many places a result from task 1 can reach task 50: a session that is never
reset, a reranker that updates statistics as it serves, a cache keyed on something task-derived, a temp file,
a tool that keeps state server-side. Each of these reproduces V3 exactly, while the memory hash stays
reassuringly constant.

Rules 8–10 therefore invert the default. Instead of enumerating what must be frozen, they establish that
*nothing writable on the decision path survives a task boundary*, with one named exception — the pinned
read-only snapshot — and one named outlet: the Evidence Sink, which flows one way. That inversion matters
because the enumeration in rule 8 will always be incomplete; new state carriers appear with every tool
added. A rule that lists carriers ages badly. A rule that permits exactly one exception does not.

The sink is what makes the inversion workable. Measurement genuinely requires writing — outputs, traces,
timings, scores — and without a designated one-way outlet, the freeze rule and the need to measure would be
in direct conflict, which is how such rules get quietly relaxed in practice.

### Why exposure state is needed on top of isolation

Isolation protects an evaluation set during a single epoch. It does nothing about what happens to that set
afterwards. Once results are read, a diagnosis formed and the system changed, the same instances no longer
measure what they measured before — they now sit downstream of a development process that saw them. Nothing
in the isolation rules detects this, because no rule was broken during any individual epoch.

The SEALED → EXPOSED → RETIRED lifecycle makes that erosion explicit and tracked rather than gradual and
invisible. It also preserves the legitimate use: an exposed set is still perfectly good for regression and
debugging, and saying so removes the incentive to pretend it is still pristine. What it can no longer do is
support a *new primary confirmatory claim*, and rule 12 says only that.

Rule 13's epoch freeze closes the corresponding gap within an epoch. Freezing architecture, contract version,
treatment definitions and resource controls before the epoch opens is what makes the epoch a measurement
rather than a search; and forbidding a later condition from being altered after an earlier condition's
detailed results is what prevents A/B/C from becoming a sequence in which C is tuned with knowledge of how A
and B fared.

Rule 6 exists because the most likely contamination in this project is not adversarial and not automated.
It is a capable operator looking at which evaluation cases failed, forming a correct diagnosis, and
improving memory in a way that happens to be shaped by the held-out set. Nothing about that sequence feels
like cheating from the inside, which is exactly why it needs a recorded timestamp rather than a norm.

## Consequences

**Easier:** stating that memory never saw the evaluation set, and supporting the statement with a graph
query and two hashes; rerunning evaluations safely against a pinned snapshot; distinguishing development
iterations from primary-proof runs.

**Harder:** the harness must support disabling write capability rather than merely not calling it;
evaluation and experience data must live in separately credentialed stores; every operator inspection needs
recording, which adds friction to exactly the debugging loop people most want to move fast in.

**Newly required:** an evaluation instance registry carrying exposure state; content-hashable memory
snapshots; per-task execution isolation with a hashable writable-surface inventory; a separately credentialed
Evaluation Evidence Sink with one-way flow; negative access tests in CI for both the evaluation corpus and
the sink; inspection-event recording; epoch open/close artefact hashing; clean/variant/contaminated
labelling on every run.

**Constrained:** D-14 (port surface) must make write capability separable from read capability, since rule 3
depends on withholding one without the other. D-18 (failure semantics) interacts with rule 3 — a capture
failure during an evaluation pass must be impossible rather than retried, because there is nothing legitimate
to capture. The Benchmark Contract inherits these rules and may tighten but not loosen them.

**Explicitly not decided here:** task populations, success metrics, stopping rules, exact split
construction, sample sizes, and evaluation-set release policy. This ADR establishes isolation and exposure
*semantics*; the Benchmark Contract will define how splits are built, how large they are, and when sets are
released or rotated. Rule 11's lifecycle implies evaluation sets are a consumable resource that must
eventually be replenished — the replenishment policy is a Benchmark Contract decision, not one made here.

## Reversibility

High as configuration, low as evidence. The mechanisms are straightforward to relax later, and the
instrumentation is useful regardless. But a contaminated result cannot be repaired after the fact — it can
only be discarded and rerun from a clean snapshot. That asymmetry is why isolation is decided before capture
is built rather than before evaluation is run.

## Validation / falsification

Revisit if:

- the frozen-snapshot constraint proves to hide a genuine v0 effect that only appears under continual
  learning, which would argue for promoting Option B's variant to a co-primary result under a design that
  handles V3; or
- rule 6's inspection recording proves so burdensome that operators stop recording, which would mean the
  invariant has become fiction and needs a different enforcement point; or
- K-5 turns out to be computationally impractical at v0 memory sizes, which would require an indexed
  provenance summary rather than full traversal.

Evidence that contamination occurred and was **not** caught by K-1 through K-8 would falsify the claim that
these invariants are sufficient and would require strengthening them, not relaxing them.

## Subsequent refinement

**2026-09-10 — ADR-0010 rule 21 (approved).** Evaluation-epoch boundaries are identified by **commit-sequence
watermarks** rather than wall-clock timestamps. Each epoch records its opening and closing `commit_sequence`,
and epoch-membership checks compare sequences rather than clocks.

This applies to the evaluation epoch throughout this ADR — rules 9 and 13, and invariants K-4 and K-9 … K-17.
It makes those checks exact and independent of clock skew, regression and collision. **The invariants
themselves are unchanged**; only the comparison becomes reliable. Nothing in this ADR's accepted decision or
rationale is rewritten.

## Outcome

Pending. No implementation, no evaluation corpus and no experiment exist.
