---
id: ADR-0003
status: proposed
date: 2026-09-10
scope: scientific
vision_refs:
  - docs/vision/03-memory-lifecycle-consolidation.md
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0003 — Resource and Cognitive Compute Parity Across Experimental Conditions

**Tier: D3 (scientific / benchmark methodology). Requires explicit owner approval.**

Covers register entries **D-08** (consolidation model identity and parity) and **D-09** (inference-time
compute parity).

## Decision question

Which resources — model capability and inference compute — must be held equal across experimental
conditions A, B and C, at which stage of the pipeline, and measured how?

## Context

The v0 thesis is that a frozen model becomes measurably better on unseen related tasks because MNEXA
preserved and transformed its prior experience. The comparison is:

```text
A   frozen model, no persistent memory
B   same frozen model, conventional retrieval baseline
C   same frozen model, MNEXA
```

Every one of these is a way for C to win without the thesis being true:

- C's memory was built by a **stronger model** than the one under test, so C inherits intelligence from
  outside the frozen-weights boundary (3.42 permits heterogeneous consolidation models; 10.41 requires
  frozen weights for the proof; neither section notices the collision).
- C's decision path **calls a model** during recall, so C spends more inference per task than A or B.
- C is allowed to **inject far more context** than B, so C wins on prompt volume rather than memory quality.
- C's model calls are **not all metered**, so an unmeasured call escapes any budget.

The decision is forced before the specification because parity determines what MNEXA must be *able to
declare and meter*. A system that cannot report which model touched the memory-construction path cannot be
retrofitted with that evidence later, and `.claude/rules/scientific-method.md` requires the benchmark
contract be frozen *before* implementing the mechanism being evaluated.

### The trap: equalizing the wrong thing

Naive "fair comparison" reasoning says equalize total compute. That would destroy the experiment.

MNEXA's entire mechanism is that it spends compute **offline, between tasks**, converting experience into
reusable intelligence, so that **less or equal** compute is needed **per task** later. Offline consolidation
compute is not a confound — it is the treatment. Equalizing it to A's level (zero) is equivalent to running
condition C with MNEXA disabled and then reporting that memory does not help.

Symmetrically, per-task decision-time compute is not a treatment. If C thinks longer per task than A, the
result is confounded with extra reasoning and says nothing about memory.

So the axes must be separated rather than pooled. The distinctions below are the substance of this ADR.

### The five axes, and what each demands

| # | Axis | When it runs | Is it the treatment? | Required handling |
|---|---|---|---|---|
| 1 | **Decision-time model compute** | during an evaluated task | No | **Hard parity** across A/B/C |
| 2 | **Retrieval/storage compute** (non-model: indexing, ranking, graph traversal, I/O) | during an evaluated task | No | Metered and reported; **not** equalized |
| 3 | **Offline consolidation compute** | between tasks | **Yes — this is the mechanism** | **Never equalized**; declared, metered, reported |
| 4 | **Model capability / version** | every stage | No | Identical in the reasoning seat; **capability ceiling** elsewhere |
| 5 | **Lifetime vs per-task compute** | — | Lifetime: yes. Per-task: no | Per-task equalized; lifetime reported, never equalized |

Axis 2 is where the loophole lives. A "retrieval" step that calls a model to rerank candidates is not
retrieval compute — it is decision-time model compute wearing retrieval's clothes. The boundary must be
drawn by *whether a model is invoked*, not by which subsystem the code lives in.

Axis 5 is the distinction most likely to be got wrong in reporting. C legitimately consumes far more
**lifetime** compute than A. That is the honest shape of the claim — amortized investment — and the claim
must be *scoped* to it ("MNEXA achieves X at Y offline cost per Z experiences"), not hidden by it.

### The context-budget problem

Strict token parity at decision time is impossible in principle: MNEXA cannot supply memory without adding
input tokens. Enforcing equal input tokens across A/B/C would nullify the treatment exactly as equalizing
offline compute would.

The meaningful control is therefore parity of **injected-context budget between B and C**. Both baselines
that inject memory get the same token allowance; A injects nothing by definition. C must beat B *at equal
injected-context budget*. This is what makes the comparison test "MNEXA's selection is better than
conventional retrieval's" rather than "more context beats less context" — which is the precise claim
1.10 and 5.2 make MNEXA responsible for.

## Options considered

### Option A — Strict total-compute parity

Equalize all compute across conditions, offline included.

Benefits: trivially defensible against "C got more resources"; single number to report.

Costs: eliminates the treatment. Consolidation is MNEXA's mechanism; budgeting it to parity with a
no-memory condition means measuring MNEXA with MNEXA switched off. Guarantees a null result regardless of
whether the thesis is true.

Failure mode: a false negative that looks rigorous.

Reversibility: n/a — the results produced under it are uninformative.

### Option B — Staged parity by axis

Hard parity on decision-time model compute and reasoning-seat model capability. Capability ceiling on any
model touching the memory-construction path. Offline and lifetime compute declared, metered and reported
but never equalized. Injected-context budget equalized between B and C.

Benefits: controls each axis according to whether it is treatment or confound. Directly forecloses all four
failure modes listed in Context. Produces a claim whose scope is explicit. Every rule is mechanically
checkable.

Costs: more instrumentation than a single compute counter — every model invocation must route through one
metered client, and every stage must declare which seat it occupies. Requires the parity configuration to
be frozen and committed before the first evaluation run.

Failure mode: a model invocation that bypasses the metered client would silently break parity. J-5 exists
specifically to detect this by cross-checking against provider-reported usage.

Reversibility: high. Budgets and ceilings are configuration; changing them after results exist is itself a
D3 change and preserves earlier results under the earlier contract version.

### Option C — Declare and report only

No hard parity. Record every resource difference and adjust statistically as covariates.

Benefits: least constraint on implementation; nothing is forbidden; maximum flexibility to tune C.

Costs: relies on statistical adjustment at a sample size v0 will not reach. Leaves "MNEXA won because it
had a stronger consolidation model" as a live alternative explanation that no reader is obliged to accept.
Conflicts with the standing rule that a mechanism which cannot beat a simpler baseline should not be
promoted on architectural elegance.

Reversibility: high, but the results produced under it are weak evidence.

## Decision

**Recommendation: Option B.** *(Proposed. Not approved.)*

Eight rules.

### Hard parity (decision time)

1. **Identical reasoning seat.** The model identity, version, and all sampling/reasoning parameters in the
   reasoning seat are byte-identical across A, B and C. No condition may use a different model, a different
   version, or different thinking settings.
2. **Equal per-task decision-time budget.** Each evaluated task receives the same budget of model calls and
   the same budget of generated tokens — including tokens the provider does not return in the visible
   response, such as hidden reasoning tokens — in every condition.
3. **Equal injected-context budget for memory conditions.** B and C receive the same token allowance for
   injected memory content. A injects none. C's advantage must come from *what* it selects within that
   allowance, not from being allowed more of it.
4. **Every model call counts, wherever it lives.** Any model invocation on the decision path — including
   one inside recall, ranking, reranking, query construction, or context assembly — counts against rules 1
   and 2. Subsystem boundaries do not create exemptions.

### Capability ceiling (memory construction)

5. **No model on the memory-construction path may exceed the frozen model under test.** Consolidation,
   extraction, episode construction, and any other stage that shapes what ends up in memory are restricted
   to a declared allowlist that does not contain a model more capable than the model being evaluated. The
   recommended v0 setting is the strictest one: *the same frozen model everywhere*.
6. **Baselines get the same construction budget in kind.** Whatever preparation condition B is permitted
   (embedding, chunking, indexing) is declared alongside C's, so C is not compared against a deliberately
   underbuilt retrieval baseline.

### Report, never equalize

7. **Offline and lifetime compute are metered and reported, not equalized.** Consolidation compute, total
   experiences ingested, and cumulative model calls across the condition's lifetime are recorded per
   condition and published with the result. The thesis claim is scoped to them.
8. **Parity configuration is frozen before execution.** The full parity configuration is committed before
   the first evaluation run and referenced by content hash from the experiment record. Changing it after
   observing results is a D3 change that preserves the earlier result under the earlier contract version.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| J-1 | Reasoning-seat model identity, version and parameters are identical across conditions | Hash the reasoning-seat config per condition; assert all hashes equal |
| J-2 | Per-task model-call and generated-token budgets are equal across conditions and not exceeded | Meter per task; assert declared budgets equal and every actual ≤ budget |
| J-3 | Hidden/reasoning tokens are counted, not just visible output | Record provider usage fields per call; assert reasoning-token field present and non-null where the provider reports it |
| J-4 | Injected-context tokens for B and C stay within one shared budget | Token-count the injected block; assert `budget_B == budget_C` and each actual ≤ budget |
| J-5 | No model call on the decision path escapes metering | Route all invocations through one instrumented client; assert metered call count equals provider-reported call count per task |
| J-6 | No model above the declared ceiling touches the memory-construction path | Assert every model identity recorded in construction-path provenance ∈ declared allowlist |
| J-7 | Offline and lifetime compute are recorded per condition | Assert the experiment record carries non-null totals for each condition |
| J-8 | Parity configuration was frozen before the first evaluation run | Assert config content hash committed at a timestamp earlier than the first run's start |

J-6 is enforceable only because ADR-0002 rules 8–9 require model provenance on attributed content: the
identity of every model that touched the construction path is already recorded as historical fact. Parity
is checkable here as a direct consequence of the accepted provenance decision.

## Evidence and rationale

The vision states both halves of the conflict and never resolves it — 3.42 treats interchangeable
consolidation models as a feature of model independence, while 10.41 requires frozen weights for the
persistent-learning proof. The resolution proposed here is that model independence is a claim about *the
substrate surviving model replacement*, not a licence to import capability from a stronger model during the
very experiment that claims no such import occurred. Rule 5 preserves 3.42's intent for production while
constraining it for the experiment.

The rules are not symmetric across axes because the axes are not symmetric. Rule 7 exists because
equalizing offline compute would be the single most damaging thing this ADR could do, and it is the
intuitive move — "make everything equal" is what fairness sounds like. 10.45 (Grand Proof 5) makes the
correct framing explicit: the distilled agent should perform as well or better *at dramatically lower
cognitive cost per task*, having paid a large one-time consolidation cost. Cost asymmetry across time is
the expected shape of a positive result, not a flaw in the design.

Rule 3 follows from 5.2 and 5.56: MNEXA's claim over conventional retrieval is specifically that it
activates *the right few* items under a finite attention budget. If C is permitted a larger injected budget
than B, the experiment cannot distinguish better selection from more context, and 5.56's attention
challenge — quality maintained as irrelevant memory grows — becomes untestable.

Rule 4 closes the loophole most likely to be crossed accidentally rather than deliberately. A reranking
step feels like retrieval infrastructure; if it invokes a model it is reasoning compute. Drawing the line
at *model invoked / not invoked* rather than at subsystem ownership makes the rule mechanical.

Option C is rejected on sample size. Statistical covariate adjustment for compute differences requires many
more trials than a v0 cycle will produce, and `.claude/rules/scientific-method.md` requires reporting
uncertainty and sample size — which would make the weakness of such an adjustment visible in the result
anyway. Better to constrain the design than to explain the confound afterwards.

## Consequences

**Easier:** stating the thesis claim with explicit scope; defending against "C had more resources";
detecting an accidental parity break before results are published rather than after.

**Harder:** implementation must route every model invocation through one metered client, which constrains
how recall is built; the parity configuration must be frozen before the first run, which removes the option
of tuning C after seeing early results.

**Newly required:** a declared model allowlist for the construction path; per-task metering of calls,
generated tokens, hidden reasoning tokens and injected-context tokens; per-condition lifetime compute
totals in the experiment record; a committed, content-hashed parity configuration.

**Constrained:** D-10 (recall reproducibility) narrows — if recall may invoke a model, that invocation is
budgeted here and its determinism is decided there. D-14 (port surface) must expose metering hooks. The
Benchmark Contract inherits rules 1–8 and may tighten but not loosen them.

**Explicitly not decided here:** task population, train/eval split mechanics, primary metric, stopping
rules, and the definition of "unseen related task". Those belong to the Benchmark Contract, which is not
being written. D-17 (hidden-evaluation isolation) is deliberately excluded and surfaces separately: it
concerns which *data* may enter the memory path, a different threat model with a different enforcement
point from resource allocation.

**Accepted risk:** rule 5's strict setting may mean the frozen model performs consolidation poorly, and a
null result would then be ambiguous between "MNEXA does not work" and "this model cannot consolidate". The
mitigation is to record consolidation-output quality separately so the two readings can be distinguished;
whether that mitigation is sufficient is a question for the Benchmark Contract.

## Reversibility

High. All quantities are configuration rather than architecture. The instrumentation required (single
metered client, provenance-recorded model identities) is useful regardless of the parity values chosen and
is not wasted if budgets change. Changing parity after results exist is permitted but is a D3 change that
must preserve earlier results under the earlier contract version.

## Validation / falsification

Revisit if:

- metering shows the single-client constraint is impractical for a legitimate recall design, indicating
  rule 4's enforcement point is wrong even though its principle holds; or
- the frozen model proves unable to perform useful consolidation at all, making rule 5's strict setting a
  measurement of the model rather than of MNEXA; or
- injected-context budget parity (rule 3) turns out to advantage B rather than equalize, because MNEXA's
  representation is denser per token than retrieved chunks — in which case the right control may be
  information content rather than token count, and this ADR would be superseded.

Evidence that a parity break occurred and was *not* caught by J-1 through J-8 would falsify the claim that
these invariants are sufficient, and would require strengthening rather than relaxing them.

## Outcome

Pending. No implementation and no experiment exist.
