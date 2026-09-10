---
id: ADR-0011
status: accepted
date: 2026-09-10
scope: constitutional
vision_refs:
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/08-self-model-meta-memory-self-improvement.md
spec_refs: []
supersedes: []
---

# ADR-0011 — Recall Reproducibility and Evidence Contract

**Tier: D3 (constitutional / scientific).** Requires explicit owner approval.

Covers register entry **D-10**.

**Approval:** accepted by owner 2026-09-10, following three owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **Identity does not equal recoverability.** The original described the v0 form as recording "identities,
   not artefacts". That is correct for the retrieval *environment* and wrong for request and result *content*:
   a hash proves identity but does not let the content be read back. Semantically relevant request and result
   content must remain recoverable. — rules 2a–2c, S-21, S-22.
2. **Recall binds a fixed knowledge snapshot.** The original required every read to be `AS_OF(N)` but did not
   forbid the view advancing mid-operation, nor distinguish the recall's watermark from the evidence record's
   own commit identity. — rules 3a–3b, S-23, S-24. Surfaced **D-28** rather than settling the cycle-scope
   question.
3. **Returned is not presented.** The original said freshness was "presented to cognition", which asserts a
   D-13 fact from D-10 evidence. Wording corrected throughout to *returned/attached by the recall operation*.
   — rules 7, 9, 17, S-8.

## Decision question

What must MNEXA preserve about a recall operation so that what was eligible, what was returned, and what
became available for activation can be reconstructed from immutable evidence, without relying on the current
retrieval system to recreate the past?

## Context

ADR-0010 supplied the primitive — `AS_OF(N)` — and left three things to this decision: which record carries a
decision's knowledge watermark, what the level-2 activation boundary rests on, and whether recall must be
reproducible at all.

Two accepted decisions already bear directly. ADR-0006 rule 6 requires every object entering active cognition
to carry a freshness determination. ADR-0007 N-11 requires any projection that influenced cognition to be
capturable as historical evidence while remaining a projection. Recall is the largest such projection in v0.

### Two different properties, routinely confused

| | Question | Depends on |
|---|---|---|
| **Historical / forensic replay** | What actually happened at that recall? | Immutable evidence captured then |
| **Computational re-execution** | Can the mechanism be rerun to produce the same result? | Today's algorithms, indexes, embeddings, models |

The second is useful. The first is constitutional. Conflating them makes historical truth contingent on
software that will certainly change — indexes get rebuilt, embeddings get replaced, policies evolve, provider
model aliases float. If replay requires rerunning today's retriever and hoping, then a discrepancy years later
is uninterpretable: it cannot be told apart from the past having genuinely been different.

## Options considered

### A — Recompute-only

Persist request, watermark and policy identity; reconstruct the recall later by rerunning retrieval.

Costs: fails under index rebuilds, embedding changes, approximate-nearest-neighbour nondeterminism, tie
ordering, concurrent index updates, policy evolution and floating model aliases — each of which changes
results without any record having changed. Worse than fragile, it is **unfalsifiable**: when a rerun differs
from expectation there is no evidence establishing which of the two is wrong. It also makes forensic capability
decay silently as the system improves, so the longer the project runs the less it can say about its own past.

Rejected.

### B — Capture-only

Persist the exact historical result; record nothing about the retrieval environment.

Benefits: forensically complete and cheap. Historical replay is exact by construction.

Costs: recall drift becomes undetectable — with no environment identity there is no way to tell whether
today's retriever behaves as it did, which ADR-0003's parity reporting and ADR-0004's epoch reasoning both
want to know. Debugging a regression means comparing results with no way to attribute the difference to policy,
index, embedding or model. Honest claims about rerun equivalence become impossible, because there is nothing
to compare environments against.

### C — Dual contract

Persist exact immutable recall evidence **and** record enough retrieval environment identity to support
controlled re-execution where required.

The minimum useful v0 form records **identities**, not artefacts: policy identity and hash, index and embedding
identity, model identity and version, budget and filters. It does not snapshot indexes or embedding tables.
That keeps the cost close to B's while making rerun claims checkable.

**Recommendation: C**, with the reproducibility model below.

## Decision

**Reproducibility model: hybrid, with a strict asymmetry.** *(Proposed. Not approved.)*

- **Exact historical replay is mandatory and constitutional.**
- **Computational re-execution is supported under a sufficiently pinned environment**, for benchmarking and
  debugging.
- **Historical truth never depends on successful recomputation.** A failed or divergent rerun is evidence
  about the *environment*, never about what happened.

Twenty rules.

### The recall evidence record

1. **`RecallPerformed` is a historical ExperienceRecord event type.** Every recall operation whose result can
   affect cognition emits one. It is **not** a canonical object — ADR-0007 classified recall results as
   projections, and this ADR keeps that, adding only the event type its provisional list was left open for.
   `RecallRequest` and `RecallResult` remain projections; what becomes durable is the evidence about them.

2. **The record is the source of historical truth.** Replay reads the `RecallPerformed` record. It never
   invokes the live retrieval mechanism, and never depends on any index, embedding or model still existing.

2a. **Content must be recoverable, not merely identified.** The semantically relevant `RecallRequest` and
   `RecallResult` content must remain readable back. This may be achieved by storing canonical immutable
   content directly, **or** by storing an immutable content-addressed reference whose target is retained and
   resolvable for the required lifetime. **A hash alone proves identity and provides no recoverability.**
   Historical replay must never depend on an external mutable object that can later change or disappear.

2b. **Environment identity is recorded; environment *recoverability* is conditional.** Policy, configuration,
   model, index and embedding identities and hashes are preserved on every record. If computational
   re-execution is **claimed as supported**, the exact required environment must actually be resolvable or
   reconstructable. If it is not, the rerun status is `unsupported` (rule 15).

2c. **Full index snapshots are not required.** An index may satisfy 2b by being reproducibly reconstructable
   from the `AS_OF(N)` durable state, a pinned build and configuration identity, a pinned embedding identity
   and any other required deterministic inputs. Where an approximate or nondeterministic index cannot be
   recreated exactly, **historical replay remains valid** — it reads the record — while exact computational
   rerun must not be claimed.

### What `AS_OF(N)` governs

3. **`AS_OF(N)` governs the entire recall view, not just the results.** It is not sufficient that every
   returned item has `commit_sequence ≤ N`. **Every decision-affecting state consulted by retrieval must be
   valid as of N.** A recall claiming to represent state at N may not consult a newer interpretation head,
   usage statistics updated after N, a later freshness assessment, a later entity resolution, a later
   retrieval weight, or adaptive ranking state created after N.

   **The rule:** *a recall `AS_OF(N)` may depend only on durable cognitive state eligible at N, plus explicitly
   pinned non-learning runtime configuration.* Anything else leaks future information into a historical recall.

3a. **The snapshot is bound before retrieval begins and does not move.** A recall invocation binds its
   watermark N up front, and every durable-state read influencing that recall observes the same `AS_OF(N)`
   view. Commits landing during execution do not become visible partway through:

   ```text
   recall starts AS_OF(500)
     … #501, #502, #503 commit while it runs …
   the recall remains a recall AS_OF(500)
   ```

3b. **The recall watermark and the evidence record's own commit identity are distinct concepts.** The
   `RecallPerformed` record for the recall above may itself commit at `#504`. **Its `commit_sequence` is not
   the recall's knowledge watermark**, and both are preserved separately. Recording the evidence never
   retroactively changes what was eligible to the recall it describes.

4. **Head selection means head-as-of-N.** Where a policy selects an object's current version, that resolves to
   the latest version with `commit_sequence ≤ N` — well-defined given ADR-0010's visibility linearization.
   It never means *whatever the head is now*.

5. **Non-durable inputs are identified by pinned configuration identity.** Retrieval inputs that are static
   configuration rather than durable MNEXA state are recorded by policy or configuration identity and hash, so
   the boundary between *state at N* and *configuration* is explicit rather than assumed.

### Version pinning

6. **Every returned item is version-pinned.** Recall output contains no floating head references:

   ```text
   NOT:  Belief B17 / current
   BUT:  Belief B17 version 4
   ```

   This is ADR-0005's pinning rule applied at the cognition boundary, and it is what makes rule 2's replay
   resolve to the same content forever.

### Freshness

7. **Returned freshness is evaluated as-of N and preserved.** ADR-0006 defines freshness as derived state
   over pinned provenance and *current* heads; within a recall, "current" means **as-of N**. If `P v1` was
   `CLEAN` at `#500` and became `DIRECT_STALE` by `#900`, a recall that occurred at `#500` must never be
   reconstructed as though `P v1` was stale then.

   The exact freshness assessment **returned and attached by the recall operation** is preserved in the
   evidence. This does not contradict ADR-0006 M-13/M-16 — nothing is written onto the interpretive version;
   the assessment is captured as historical evidence about the recall, which is what ADR-0007 N-11 requires of
   an influential projection.

   **This ADR asserts only that the assessment was attached to the returned item.** Whether that item entered
   cognition, and whether this assessment was what cognition saw, are separate historical facts owned by D-13.
   ADR-0006 rule 6's requirement — that objects entering active cognition carry a freshness determination — is
   satisfied jointly: this ADR supplies the returned-side half, D-13 the cognition-side half.

### Evidence contents

8. **The request evidence** resolves or contains: the agent and memory namespace; the knowledge watermark N;
   task, goal or query intent; the ContextFrame input; entity references where applicable; retrieval scope;
   retrieval budget or maximum result allowance; filters and constraints; recall policy identity, version and
   hash; and the requested memory or object kinds.

9. **The result evidence** contains: the ordered, version-pinned items returned, with rank; the retrieval
   channel per item where the channel materially affects interpretation; the relevance or ranking signals
   surfaced; the freshness assessment attached per returned item; the budget or limit that constrained the result; and the
   completion status of rule 11.

10. **Ranking signals carry their declared algorithmic meaning.** A retrieval or relevance score is recorded
    with what it actually measures. **It is never, by itself, epistemic confidence, probability of truth,
    importance, or causal influence.** Score semantics must not drift into epistemic ones, which is the same
    prohibition ADR-0006 rule 5 applied to staleness and confidence, one layer out.

### Completeness

11. **Completion status is mandatory, and incompleteness is never silent.** If recall terminates because of a
    timeout, resource cap, unavailable index, permission limitation, partial backend failure or any other
    explicit limit, the evidence carries that status and its reason.

11a. **Completion describes execution of the declared procedure, nothing more.** For approximate retrieval,
    `COMPLETE` or `NORMAL_COMPLETION` must **not** be read as implying exhaustive examination of every
    eligible memory, a globally optimal top-k, or proof that no more relevant memory existed. It means the
    declared algorithm and policy completed normally under their declared scope and budget.

    "Returned 5 memories" must never be readable as "these were the best or complete eligible memories" when
    the search itself was incomplete. This is ADR-0006's `CHECK_INCOMPLETE` principle in a second domain, and
    the vocabulary is deliberately parallel: an incomplete inspection never masquerades as a complete one.

### Side effects

12. **Recall is observationally read-only with respect to the memory view at its starting watermark.** The
    recall computation performs no durable write: no access-count increment used by future ranking, no
    strengthening of a memory because it was returned, no synchronous retrieval-weight adaptation, no head
    movement.

13. **The fact that recall occurred is recorded afterward as immutable evidence.** The `RecallPerformed`
    record commits at a sequence later than N. It is legitimate history, and it does **not** feed ranking —
    learning from use happens later through explicit outcome, activation, utility and consolidation mechanisms,
    never as a side effect of retrieval.

### Model participation

14. **Model calls inside recall are model compute.** Any invocation for query expansion, semantic
    reformulation, reranking, retrieval interpretation, reflection or candidate judging counts under ADR-0003
    rules 1–4, is metered under J-5, and is recorded in the recall evidence with model identity and version.
    Model reasoning is never hidden behind the word "retrieval".

### Rerun honesty

15. **A rerun claim carries exactly one of three statuses:** `exact`, `equivalent-within-tolerance`, or
    `unsupported`. **`exact` may be claimed only where the pinned environment identity actually matched.**
    Where only the historical result was captured, the honest status is `unsupported` — never an exact-
    reproducibility claim.

16. **Divergence is evidence about the environment, not about history.** A rerun that differs from the
    captured result establishes that something in the retrieval environment changed. It never revises what the
    recall returned.

### Boundary with D-13

17. **This ADR owns *retrieved / returned* and nothing beyond it.**

    | Claim | Owner |
    |---|---|
    | M7 was returned by recall | **D-10** — historical fact, this ADR |
    | M7 entered final model context (presented / activated / selected / suppressed) | **D-13** |
    | M7 caused the model to choose Action A | **D-13's attribution semantics**, never inferred from activation |

    ADR-0010 rule 10's three levels are preserved: returning establishes eligibility-plus-retrieval, not
    presentation, and certainly not influence. **No statement in the recall evidence may assert that an item,
    or its attached freshness assessment, was actually presented to cognition** — that is D-13's fact to
    establish, and if D-13 later shows this exact assessment entered cognition, that is a separate historical
    fact recorded separately.

18. **Retrieval-regret preconditions are preserved, not implemented.** The evidence must later distinguish:

    - a memory that was durably eligible at N but **not returned** → possible *retrieval* failure;
    - a memory returned but **not activated** → possible *attention/context-selection* failure;
    - a memory activated but the outcome was still poor → possible *reasoning, knowledge or attribution*
      problem.

    This ADR makes the first boundary computable, by making the returned set immutable and eligibility
    recomputable from N. **D-13 completes the second and third.** No regret mechanism is built here.

### Benchmark support

19. **Recall evidence must be sufficient for the later Benchmark Contract** to reconstruct which memories were
    surfaced, verify model calls made inside recall, detect recall drift via environment identity, and
    distinguish historical replay from rerun equivalence. Note the division: ADR-0003 J-4 counts **injected**
    context, and injection is presentation — so D-13 supplies the injected set while this ADR supplies the
    returned set and the budget that constrained it. No benchmark metric is defined here.

### Scope

20. **The contract permits future retrieval channels without requiring them.** Recording a per-item channel
    (rule 9) leaves room for the routes vision 5.6 describes without making any of them a v0 requirement.
    **Which channels v0 actually implements is not decided here** — see D-27.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| S-1 | Every cognition-affecting recall emits an immutable `RecallPerformed` record | Assert one record per recall reaching cognition; assert record immutability (ADR-0002 I-1) |
| S-2 | Every recall evidence record carries its watermark N | Assert non-null, resolvable `commit_sequence` watermark |
| S-3 | No returned item is a floating head reference | Assert every returned item carries a version or record identity; assert zero `current`-style references |
| S-4 | Head selection resolves to head-as-of-N | Fixture where an object's head moved after N; assert recall returns the version current at N |
| S-5 | No retrieval input with `commit_sequence > N` is consulted | Instrument state reads during recall; assert every durable read resolves ≤ N |
| S-6 | No adaptive state created after N influences a recall AS_OF(N) | Assert no ranking input derives from state committed after N; fixture with post-N usage statistics asserting no effect |
| S-7 | Non-durable retrieval inputs are pinned by configuration identity | Assert every non-durable input is named by a recorded configuration or policy identity and hash |
| S-8 | Returned freshness is evaluated as-of N and preserved in evidence | Fixture where freshness changed after N; assert the record preserves the as-of-N assessment, not today's; assert the evidence claims attachment, not presentation |
| S-9 | Completion status is present, and incomplete is never reported as complete | Fixture per termination cause; assert status and reason recorded; assert no consumer treats an incomplete result as exhaustive |
| S-10 | Every ranking signal records its declared algorithmic meaning | Assert each signal in the vocabulary carries a definition; assert none is undefined |
| S-11 | No retrieval score is converted into an epistemic quantity | Assert no path maps a retrieval score to confidence, probability of truth, importance or causal influence |
| S-12 | Model calls inside recall are recorded and metered | Assert model identity and version recorded per call; cross-check count against ADR-0003 J-5 metering |
| S-13 | Recall performs no durable write to the memory view at its starting watermark | Hash the memory view before and after a recall; assert unchanged |
| S-14 | Recall behaves identically inside and outside an evaluation epoch | Assert the recall path contains no write that ADR-0004 rule 3 would disable; compare behaviour across an epoch boundary |
| S-15 | Historical replay never invokes the live retrieval mechanism | Assert replay resolves solely from the `RecallPerformed` record; disable the retriever in a fixture and assert replay still succeeds |
| S-16 | Every rerun claim carries exactly one of the three statuses | Assert status ∈ {exact, equivalent-within-tolerance, unsupported} |
| S-17 | `exact` is claimed only where pinned environment identity matched | Assert every `exact` claim cites matching policy, index, embedding and model identities |
| S-18 | The eligible-but-not-returned set is computable | Assert `AS_OF(N)` eligibility minus the returned set is derivable from the record and the store |
| S-19 | Environment identity is recorded | Assert policy, index/embedding and model identities are non-null on every record |
| S-20 | `RecallPerformed` does not feed ranking | Assert no ranking input reads `RecallPerformed` records |
| S-21 | Request and result content is recoverable, not merely hashed | Assert content is stored inline or via a content-addressed reference; resolve every reference and assert the target is retained and readable |
| S-22 | Replay depends on no external mutable object | Assert every replay dependency is immutable or content-addressed; mutate an external source in a fixture and assert replay output is unchanged |
| S-23 | The recall view does not advance during execution | Commit records mid-recall in a fixture; assert none appears in the result and no read observed them |
| S-24 | Recall watermark and evidence-record commit identity are distinct and both preserved | Assert both fields exist and differ where the record committed later; assert no path treats the record's own `commit_sequence` as the recall watermark |
| S-25 | `COMPLETE` never implies exhaustiveness | Assert no consumer derives optimality or exhaustiveness from a normal-completion status |

## Evidence and rationale

**Rule 3 is the substance of this ADR and the easiest thing to get wrong.** Filtering returned versions by
`commit_sequence ≤ N` looks like it implements `AS_OF(N)` and does not. A retriever that filters its *output*
correctly while consulting a current head for entity resolution, or today's usage statistics for ranking, has
already leaked the future into the past — and the leak is invisible, because every returned item passes the
obvious check. The failure mode matters specifically for this project: a reconstruction of why a decision was
made would show memories ranked by evidence that did not exist yet, making past cognition look better-informed
than it was. That is the hindsight corruption vision 2.6 exists to prevent, arriving through the ranking path
rather than the content path.

**Rule 12's read-only requirement has an argument specific to v0 that is stronger than the general one.** The
general case is that stateful recall makes replay depend on recall history rather than on commits. The
v0-specific case is decisive: ADR-0004 rule 3 makes memory write capability **absent** during an evaluation
epoch. If recall normally incremented access counts or adapted weights, it could not do so during evaluation,
so **condition C would behave differently inside and outside the epoch** — the treatment being measured would
not be the treatment that was built. S-14 checks exactly this. Making recall read-only is therefore not a
purity preference; it is what keeps the evaluated system and the deployed system the same system.

Learning from use is not lost, only relocated. Vision 3.12's principle — memory strength should depend on
demonstrated usefulness — survives intact through outcome, activation and consolidation mechanisms, which run
where learning belongs and where ADR-0003 rule 7 already meters them.

**Rule 15's three statuses exist because the honest answer is often the third.** The temptation, having
captured a result and some configuration, is to describe recall as reproducible. But approximate-nearest-
neighbour search, tie ordering, concurrent index updates and floating provider aliases each break exactness
without breaking anything else, and a system that claims exact reproducibility it cannot deliver will be
believed until the first time it matters. Requiring a status forces the claim to be stated rather than
implied, and S-17 makes `exact` cost something to assert.

**Rule 10 prevents a specific semantic drift.** A cosine similarity of 0.87 is a statement about vector
geometry. Once it appears next to a memory in a context window, it reads as a confidence, and downstream
reasoning will treat it as one. Recording its algorithmic meaning and forbidding the conversion (S-11) keeps
the retrieval layer from silently manufacturing epistemic claims — the same failure ADR-0006 rule 5 prevented
when it refused to fold staleness into confidence, and ADR-0008 rule 11 prevented when it refused to let
`correction_of` imply falsity.

**Option B was close.** It is forensically complete, and forensic completeness is the constitutional
requirement. It was rejected only because environment identity is nearly free — identities and hashes, not
snapshots — and without it the project cannot tell drift from defect, which ADR-0003's reporting obligations
will eventually require. The recommendation is B plus a small amount of C, not a genuine dual system.

**Rules 2a–2c draw the line the original blurred.** "Identities, not artefacts" is the right economy for the
*environment* — an embedding table need not be snapshotted when its identity plus a deterministic build
procedure can reconstruct it, and where it cannot, rule 15's `unsupported` status is the honest answer. It is
the wrong economy for *content*: a hash of a result set proves which result set it was and lets nobody read
it. Since rule 2 makes the record the sole source of historical truth, a record that cannot yield its own
content is not evidence. S-22's fixture — mutate an external source, assert replay unchanged — is what stops
recoverability being satisfied by a pointer into something that will drift.

**Rule 3a exists because `AS_OF(N)` on individual reads is not the same as a snapshot.** A retriever that
resolves each read against watermark N still produces an incoherent view if the underlying store advances
between reads and some reads are served from a later state that happens to satisfy the filter. Binding the
view once, before retrieval begins, makes the whole operation observe one consistent world. Rule 3b then
prevents the opposite confusion: the evidence record necessarily commits *after* the recall it describes, and
treating its own sequence as the watermark would silently include everything that landed during execution.

## Consequences

**Easier:** answering what a past recall returned, forever, without any retrieval infrastructure; detecting
recall drift; making honest reproducibility claims; computing the eligible-but-not-returned set that retrieval
regret will later need; keeping evaluated and deployed behaviour identical.

**Harder:** every recall pays the cost of emitting an evidence record; retrieval must thread a watermark
through every state read rather than consulting current state, which constrains implementation more than a
naive retriever would like; policy, index, embedding and model identities must be stable and recorded.

**Newly required:** the `RecallPerformed` event type; watermark-scoped state reads throughout retrieval; a
ranking-signal vocabulary with declared meanings; environment identity capture; completion status; rerun status
vocabulary.

**Constrained or unblocked:**

- **D-12 (decision/prediction/outcome linkage)** — the watermark carrier question is answered for recall:
  `RecallPerformed` carries N. D-12 decides how a decision record binds to the recall(s) that informed it,
  and may reference them through ADR-0008's structural vocabulary.
- **D-13 (activation trace)** — **unblocked.** It now has a defined input: the returned, version-pinned set
  with its presented freshness. D-13 owns presented/activated/suppressed and attribution, and rule 18 leaves
  boundaries two and three explicitly to it.
- **D-11 (confidence)** — constrained by rule 10 and S-11: retrieval scores may not become confidence, so
  D-11's bootstrap cannot draw on ranking signals.
- **D-06 (provenance minimum)** — recall evidence adds environment identity to what provenance must cover.
- **D-14 (port surface)** — the recall port must accept a watermark and return version-pinned items with
  completion status.
- **D-16 (personal scope)** — the request's namespace field is where scope isolation is enforced at the recall
  boundary.

**Newly uncovered decisions — recorded, not decided here:**

**D-28 — cognitive-cycle knowledge snapshot scope.** Rules 3a–3b fix the snapshot for a *single* recall.
Whether an entire cognitive decision cycle must use one stable watermark, or whether separate recalls within a
cycle may advance to newer ones, is unresolved. ADR-0010 rule 12 requires a decision to carry *a* watermark
but does not forbid its constituent recalls using different ones, which would leave the decision's watermark
ambiguous. Inside an evaluation epoch the question cannot arise, since ADR-0004 rule 9 freezes memory; outside
one it can. Materially relevant to D-12 and D-13, and registered rather than settled here.

**D-27 — v0 retrieval channel set.** Vision 5.6
describes many activation routes: semantic, entity, temporal, causal, structural, procedural, outcome, risk and
historical-utility. This ADR records a per-item channel and permits future ones, but does not decide which
exist in v0. That is a scope decision affecting what recall can do and therefore what condition C is, and it
includes the associated ranking-signal vocabulary. Deciding it here would have expanded this ADR's surfaced
scope from evidence to mechanism.

**YAGNI check.** No accepted v0 invariant required multi-stage neural attention, learned retrieval-policy
evolution, reinforcement learning for recall, a graph database, distributed or cross-agent retrieval,
prospective memory or a counter-memory system. Rule 20 keeps the contract open to them without requiring any.

## Reversibility

High for the evidence contract, low for the read-only rule. Adding fields to `RecallPerformed` is additive, and
richer environment capture can be layered later. Making recall stateful afterwards would be a genuine
architectural change: every recall recorded under read-only semantics would have to be reinterpreted, and
S-14's guarantee that evaluated and deployed behaviour match would be lost. That asymmetry argues for
read-only now.

## Validation / falsification

Revisit if:

- threading a watermark through every retrieval state read proves impractical for some legitimate channel,
  indicating rule 3's scope is too broad for a particular input class rather than wrong in principle; or
- read-only recall leaves usage-based strengthening (vision 3.12) with insufficient signal, because outcome and
  consolidation paths turn out not to observe enough — which would argue for an explicit, metered usage-recording
  step rather than for stateful retrieval; or
- evidence-record volume dominates the ledger at v0 scale, suggesting the granularity of "a recall" is wrong.

Evidence that a historical replay produced a different answer than the recall actually returned would falsify
the claim that this evidence set is sufficient, and would indicate a field the record failed to capture.

## Outcome

Pending. No implementation exists.
