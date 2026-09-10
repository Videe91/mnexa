---
id: ADR-0003
status: accepted
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

**Approval:** accepted by owner 2026-09-10, following four owner-directed precision amendments made while
the ADR was still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **"Hard parity" replaced by controlled reasoning-seat parity.** The original proposal said decision-time
   model compute was under "hard parity across A/B/C". That claim was wrong as written: B and C necessarily
   receive memory context A does not, so literal token-level parity is unachievable. What is controlled is
   the *reasoning seat*, enumerated in rule 1. Memory-contributed input tokens are metered and reported, not
   equalized. — rules 1–3, invariants J-1/J-4.
2. **Claim-boundary rule added.** The original proposal controlled the comparison but never stated what each
   outcome licenses as a conclusion. — rule 9, invariant J-9.
3. **Consolidation model tightened from ceiling to identity.** The original made "same frozen model
   everywhere" a *recommended* setting under a capability ceiling. It is now *required* for the primary
   proof, with heterogeneous consolidation permitted only as a separately labelled variant. — rule 5,
   invariants J-6/J-10.
4. **Lifetime versus per-task wording disambiguated.** — §Lifetime versus per-task.

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
| 1 | **Decision-time reasoning-seat resources** (model, allowances, tools, decoding, stopping) | during an evaluated task | No | **Controlled parity** across A/B/C — identical seat definition |
| 2 | **Non-model retrieval/storage compute** (indexing, ranking, graph traversal, I/O) | during an evaluated task | No | Metered and reported; **not** equalized |
| 3 | **Injected-memory input tokens** | during an evaluated task | Partly — memory access *is* the experimental variable | **Not** equalized between A and B/C; B and C share one maximum budget; always metered |
| 4 | **Offline consolidation compute** | between tasks | **Yes — this is the mechanism** | **Never equalized**; declared, metered, reported |
| 5 | **Model identity / version** | every stage | No | Identical exact model in the reasoning seat *and* in model-based consolidation, for the primary proof |

### Lifetime versus per-task

Stated without ambiguity:

- **Decision-time / per-task reasoning resources are controlled** — the reasoning seat is identical across
  conditions and its allowances are equal.
- **Lifetime / offline MNEXA resources are not equalized away** — consolidation compute is the mechanism
  under test, and reducing it to the no-memory condition's level would remove the treatment.
- **Lifetime / offline resource usage is fully metered and reported** per condition.
- **Amortized cost can be calculated across tasks** from those figures, so the claim can be stated as
  performance at a given offline cost per experience.

Axis 2 is where the loophole lives. A "retrieval" step that calls a model to rerank candidates is not
retrieval compute — it is decision-time model compute wearing retrieval's clothes. The boundary must be
drawn by *whether a model is invoked*, not by which subsystem the code lives in.

Axis 3 is the distinction that makes literal compute parity impossible. Memory access is the experimental
variable; requiring A, B and C to receive equal input tokens would nullify the treatment exactly as
equalizing offline compute would. What is controlled is the *seat*, not the physical token count.

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

Controlled parity of the decision-time reasoning seat. Model-identity equality on the memory-construction
path for the primary proof. Offline and lifetime compute declared, metered and reported but never
equalized. Injected-memory budget equalized between B and C but not against A.

Benefits: controls each axis according to whether it is treatment or confound. Directly forecloses all four
failure modes listed in Context. Produces a claim whose scope is explicit. Every rule is mechanically
checkable.

Costs: more instrumentation than a single compute counter — every model invocation must route through one
metered client, and every stage must declare which seat it occupies. Requires the parity configuration to
be frozen and committed before the first evaluation run.

Failure mode: a model invocation that bypasses the metered client would silently break parity. J-5 exists
specifically to detect this by cross-checking against provider-reported usage.

Reversibility: high. Budgets and seat definitions are configuration; changing them after results exist is
itself a D3 change and preserves earlier results under the earlier contract version.

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

### Controlled reasoning-seat parity (decision time)

1. **Identical reasoning seat.** For the primary v0 comparison, A, B and C use the same:
   - reasoning model / provider / version, or a pinned snapshot where the provider offers one;
   - model-call allowance;
   - generation / output-token allowance;
   - tool permissions;
   - decoding configuration;
   - task-visible information other than the deliberately varied memory condition;
   - stopping policy.

   This is *controlled reasoning-seat parity*, not a claim of identical physical inference cost. Literal
   token-level or FLOP-level parity across A/B/C is neither achievable nor desirable, because memory access
   is the variable under test.

2. **Generation allowances are metered completely.** The generation-token allowance counts tokens the
   provider does not return in the visible response, including hidden reasoning tokens, wherever the
   provider reports them.

3. **Injected-memory tokens: metered, not equalized against A.** Input tokens contributed by the memory
   condition are **not** required to be equal between A and B/C — that difference is the experiment.
   They must be explicitly metered and reported per condition. **B and C must receive the same maximum
   injected-memory context budget**, so C cannot win merely by injecting more historical material.

4. **Every model invocation counts, wherever it lives.** Any model invocation used for query expansion,
   context construction, reranking, retrieval interpretation, reflection, or similar work counts as
   model/reasoning compute against rules 1–2. It cannot be hidden under "retrieval". Subsystem boundaries
   create no exemptions.

### Model identity on the memory-construction path

5. **The primary proof requires the same exact model.** Any model-based consolidation contributing to the
   primary v0 result must use the same model family and the same exact model/version as the reasoning seat.
   A stronger or external consolidation model must **not** participate in the primary v0 result. A
   heterogeneous or stronger consolidation model may be tested later as a separate experimental variant,
   clearly labelled as such; its result cannot be substituted for the strict primary proof.

   This is what keeps the first claim clean: *the model weights stayed fixed while useful intelligence
   accumulated externally through experience.*

6. **Baselines get comparable preparation in kind.** Whatever preparation condition B is permitted
   (embedding, chunking, indexing) is declared alongside C's, so C is not compared against a deliberately
   underbuilt retrieval baseline.

### Report, never equalize

7. **Offline and lifetime compute are metered and reported, not equalized.** Consolidation compute, total
   experiences ingested, and cumulative model calls across the condition's lifetime are recorded per
   condition and published with the result, so amortized per-task cost is computable.

8. **Parity configuration is frozen before execution.** The full parity configuration is committed before
   the first evaluation run and referenced by content hash from the experiment record. Changing it after
   observing results is a D3 change that preserves the earlier result under the earlier contract version.

### Claim boundaries

9. **What each outcome licenses.**

   - **C > A** demonstrates that the experienced MNEXA-equipped system provides an end-to-end advantage
     over the same reasoning model without persistent memory.
   - **C > B**, under equal injected-memory allowance and the decision-time reasoning controls above, is
     **required** before claiming that MNEXA's organization, consolidation and recall provide an advantage
     over conventional retrieval/RAG.
   - **C > A but C ≈ B** licenses the conclusion that *persistent external memory helped*. It does **not**
     license any claim that MNEXA's memory architecture is superior to conventional retrieval.
   - Where **C > B** holds, the gain may include the benefit of MNEXA's offline consolidation compute,
     because consolidation is intentionally part of the mechanism. That compute must therefore be measured
     and reported rather than hidden.

   Later ablations may isolate how much of the gain comes from consolidation, recall policy, memory
   structure and so on. This ADR does not define those ablations.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| J-1 | The controlled reasoning seat is identical across conditions across all seven dimensions in rule 1 | Hash the full seat descriptor per condition; assert all hashes equal |
| J-2 | Per-task model-call and generation-token allowances are equal across conditions and not exceeded | Meter per task; assert declared allowances equal and every actual ≤ allowance |
| J-3 | Hidden/reasoning tokens are counted, not just visible output | Record provider usage fields per call; assert the reasoning-token field is present and non-null where the provider reports it |
| J-4 | Injected-memory tokens are metered per condition, and B and C share one maximum budget | Token-count the injected block per task; assert `budget_B == budget_C`, each actual ≤ budget, and A's injected count is zero |
| J-5 | No model invocation on the decision path escapes metering | Route all invocations through one instrumented client; assert metered call count equals provider-reported call count per task |
| J-6 | For the primary proof, every model on the memory-construction path is the exact reasoning-seat model/version | Assert every model identity in construction-path provenance equals the reasoning-seat identity exactly |
| J-7 | Offline and lifetime compute are recorded per condition and amortized cost is computable | Assert the experiment record carries non-null offline totals and experience counts for each condition |
| J-8 | Parity configuration was frozen before the first evaluation run | Assert config content hash committed at a timestamp earlier than the first run's start |
| J-9 | No claim of advantage over conventional retrieval is published without a recorded C > B result under these controls | Assert any such claim in an experiment record cites a run where C > B held under rule 9's conditions |
| J-10 | Heterogeneous-consolidation runs are labelled variants and excluded from primary-proof aggregation | Assert every run whose construction-path model ≠ reasoning-seat model carries a variant label and is absent from primary aggregation |

J-6 is enforceable only because ADR-0002 rules 8–9 require model provenance on attributed content: the
identity of every model that touched the construction path is already recorded as historical fact. Parity
is checkable here as a direct consequence of the accepted provenance decision.

## Evidence and rationale

The vision states both halves of the conflict and never resolves it — 3.42 treats interchangeable
consolidation models as a feature of model independence, while 10.41 requires frozen weights for the
persistent-learning proof. The resolution adopted here is that model independence is a claim about *the
substrate surviving model replacement*, not a licence to import capability from a stronger model during the
very experiment that claims no such import occurred. Rule 5 preserves 3.42's intent for production and for
later labelled variants, while excluding it from the primary proof.

### Why "hard parity" was the wrong phrase

The original proposal described decision-time compute as under "hard parity across A/B/C". That was
imprecise in a way that mattered. B and C necessarily receive memory context that A does not, so their
input token counts, and therefore their physical inference cost, cannot be equal — and *should* not be, since
memory access is the variable under test. Stating parity at the level of physical compute would have made
the ADR either unsatisfiable or quietly violated at the first run.

What is genuinely controllable is the **seat**: the model, its allowances, its tools, its decoding
configuration, its stopping policy, and the task-visible information other than memory. Rule 1 enumerates
those seven dimensions so the control is checkable (J-1) rather than rhetorical, and rule 3 makes the
memory-contributed difference a *reported quantity* instead of a violated constraint.

### Why claim boundaries belong in this ADR

Controlling a comparison and interpreting it are different acts, and the second is where a controlled
experiment is most often over-read. Rule 9 fixes in advance what each outcome licenses, before any result
exists to motivate a generous reading. The `C > A but C ≈ B` case is the one that most needs pre-committing:
it is a real and informative result — persistent external memory helped — and it is also precisely the
result most likely to be reported as though it validated the architecture. `.claude/rules/scientific-method.md`
requires freezing evaluation rules before they judge the mechanism they evaluate; a claim-licensing rule is
part of that freeze.

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

**Newly required:** model-identity equality between the reasoning seat and the construction path for the
primary proof, with heterogeneous runs labelled as variants; per-task metering of calls,
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
