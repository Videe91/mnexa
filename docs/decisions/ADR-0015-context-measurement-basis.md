---
id: ADR-0015
status: proposed
date: 2026-09-10
scope: scientific
vision_refs:
  - docs/vision/05-recall-attention-machine-intuition.md
  - docs/vision/10-north-star-architecture-grand-proofs.md
spec_refs: []
supersedes: []
---

# ADR-0015 — Context Measurement Basis

**Tier: D2 (scientific / benchmark-adjacent).** Requires approval before context-budget parity can be verified.

Covers register entry **D-31**.

## Decision question

By what basis is context size measured, so that ADR-0003's injected-memory budget parity between conditions B
and C is enforceable and verifiable?

## Context

ADR-0003 rule 3 requires B and C to receive **the same maximum injected-memory context budget**, and J-4
requires token-counting the injected block. ADR-0014 rule 20 requires the measurement basis to be declared and
honestly labelled. Neither says what the basis is.

This is not bookkeeping. If size cannot be measured before submission, an equal *allowance* cannot be enforced
at all — only violated and detected afterwards. And if it cannot be attributed per segment, "memory-contributed
size" is unmeasurable, so the very quantity ADR-0003 rule 3 constrains has no value. **Without this decision
ADR-0003 rule 9's claim boundary cannot be checked**, and the experiment's central resource control becomes an
assertion.

### A distinction that governs the whole decision

**The budget is a ceiling, not a quota.** ADR-0003 rule 3 says *maximum*. Equal allowance does not mean equal
consumption, and C consuming less than its allowance while matching or beating B is precisely the compression
result vision 10.45 predicts. Measurement must therefore support:

- **enforcing an equal ceiling** — necessarily *before* submission;
- **recording actual consumption** — never equalised.

Any basis that can only measure after the call can audit the second and cannot enforce the first.

## Options considered

### A — Provider-reported token usage

Benefits: exact for the provider's own accounting; directly comparable to cost; requires no local model.

Costs: **available only after the call**, so it cannot enforce a preflight ceiling — only detect a breach once
the compute has been spent. Reported for the **whole request**, not per segment, so memory-contributed size —
the quantity ADR-0003 rule 3 actually constrains — is not derivable. Provider-dependent: a tokenizer change
makes historical numbers incomparable across time, which undermines longitudinal comparison.

### B — Pinned local tokenizer

Benefits: **preflight and per-segment**, so a ceiling can be enforced before submission and memory-contributed
size attributed to individual memories. Deterministic and pinnable, therefore reproducible under ADR-0011's
environment identity.

Costs: may disagree with the provider's actual tokenizer, so the enforced budget is not exactly the provider's
cost. Requires maintaining a tokenizer whose identity must be pinned and recorded.

### C — Characters or bytes

Benefits: exact, deterministic, provider-independent, per-segment, preflight, and **durable** — a character
count means the same thing in ten years regardless of tokenizer evolution.

Costs: a poor proxy for inference cost. Token-per-character ratios vary substantially by content type — code,
prose, non-Latin scripts — so two conditions holding equal character budgets can consume materially different
token counts. As a sole parity basis this is a real leak.

### D — Compound standard

Each of the three does something the others cannot, and the roles do not overlap:

| Need | Served by |
|---|---|
| Enforce an equal ceiling, preflight, per segment | **B** — nothing else can act before submission |
| Audit actual cost | **A** — nothing else reports what the provider charged |
| Model-independent durable evidence | **C** — nothing else survives tokenizer change |

**Recommendation: D**, with one discipline that keeps it from becoming ambiguous — see rule 1.

## Decision

*(Proposed. Not approved.)* Nine rules.

### One normative basis

1. **Exactly one basis is normative for parity enforcement: the pinned local tokenizer (B).** The other two are
   **recorded but never used for enforcement**. A compound standard is only safe if it is unambiguous which
   number *is* the budget; three co-equal measures would let a breach be argued away by choosing a favourable
   one.

2. **The enforcement basis must be preflight, deterministic and per-segment.** Preflight because a ceiling
   enforced after submission is not a ceiling. Deterministic because ADR-0011 requires reproducibility.
   Per-segment because ADR-0003 rule 3 constrains the *memory-contributed* portion, not the whole request.

3. **The tokenizer identity and version are pinned and recorded** on every `ContextAssembled` record, under
   ADR-0011's environment-identity rules. Changing it is a configuration change that must be visible in the
   record, not a silent drift.

### The recorded measures

4. **Provider-reported usage is recorded when available**, for cost auditing and for rule 6's divergence check.
   It is never the enforcement basis, and its absence never blocks a run.

5. **Character and byte counts are recorded per segment**, as model-independent evidence that remains
   interpretable after any tokenizer change.

6. **Divergence between the enforcement basis and provider-reported usage is measured and reported.** If the
   pinned tokenizer systematically understates or overstates the provider's accounting, equal enforced budgets
   may not mean equal actual cost — which would weaken exactly the parity ADR-0003 rule 3 exists to establish.
   The divergence is therefore a reported quantity, not an implementation detail. *What magnitude counts as
   material is a Benchmark Contract threshold, not settled here.*

### Honesty

7. **An estimate is never labelled exact.** Per ADR-0014 rule 20, the basis is stated with every measurement.
   The enforcement basis is exact **with respect to the pinned tokenizer** and approximate with respect to the
   provider; both statements are recorded, and neither is presented as the other.

### Parity scope

8. **Parity is enforced over the memory-contributed allowance only.** Total request input is **recorded, not
   equalised**.

   This follows from ADR-0003 rather than extending it. Rule 1 already fixes the reasoning seat's task-visible
   information identically across conditions, so non-memory portions do not differ by treatment; rule 3
   constrains the injected-memory allowance. Total-request equality would additionally be **impossible** for
   condition A, which injects no memory at all — so a total-equality rule could not span the three-way
   comparison it exists to serve.

   Where a non-memory portion does legitimately differ for treatment reasons, that difference is **reported**,
   never erased by padding or trimming to force totals to match.

9. **Consumption is recorded, never equalised.** Equal ceilings, unequal usage. C using less of its allowance
   than B while performing as well or better is a result, not a parity violation — and forcing consumption
   equality would destroy the ability to observe it.

### Invariants and how each is checked

| ID | Invariant | How checked |
|---|---|---|
| W-1 | Exactly one basis is normative for enforcement | Assert the enforcement basis is the pinned tokenizer; assert no enforcement path reads provider usage or character counts |
| W-2 | Budget enforcement occurs before submission | Assert the ceiling is evaluated preflight; assert no path submits first and checks after |
| W-3 | Memory-contributed size is attributable per segment | Assert per-segment sizes exist and sum consistently with the memory-contributed total |
| W-4 | Tokenizer identity and version are recorded per assembly | Assert non-null on every `ContextAssembled`; assert a change is visible between records |
| W-5 | Provider-reported usage is recorded where available | Assert the field is populated when the provider supplies it, and explicitly marked unavailable otherwise |
| W-6 | Character and byte counts are recorded per segment | Assert both present for every segment |
| W-7 | Divergence between enforcement basis and provider usage is computed and reported | Assert the experiment record carries the divergence per run where provider usage exists |
| W-8 | No measurement is labelled exact beyond its basis | Assert each recorded measure names its basis; assert tokenizer-based figures are not described as provider-exact |
| W-9 | `budget_B == budget_C` for the memory-contributed allowance, and A's is zero | Assert declared allowances equal for B and C under the enforcement basis (satisfies ADR-0003 J-4) |
| W-10 | Total request input is recorded but never equalised | Assert totals are recorded; assert no path pads or trims to force equality |
| W-11 | Consumption is never constrained to equality | Assert only the ceiling is enforced; assert actual usage below the ceiling is never adjusted |

## Evidence and rationale

**Option A is disqualified as an enforcement basis by timing alone**, and the reason is worth stating plainly:
a budget you can only check after spending the compute is not a budget. It would reduce ADR-0003 rule 3 from a
control to a post-hoc audit, and a run that breached parity would already have produced results — leaving the
choice between discarding them and reporting a known violation. Neither is acceptable for the primary proof.
A's second defect compounds this: whole-request granularity cannot isolate the memory-contributed portion, so
even as an audit it does not measure the constrained quantity.

**Option C's weakness is easy to underestimate.** Character counts feel neutral and exact, and they are — but
neutrality between *conditions* is what parity requires, not neutrality between *tokenizers*. If condition C's
memory representations are denser per character than condition B's retrieved chunks, equal character budgets
hand C more tokens, and the advantage would be invisible in the very measure used to police it. That is the
same shape of failure ADR-0012 rule 10 identified for post-filtered top-k: a check that passes while the thing
it protects has already been violated.

**Option B's known inaccuracy is acceptable because it is symmetric.** The pinned tokenizer may disagree with
the provider, but it disagrees the *same way* for B and for C, since ADR-0003 rule 1 fixes one model and this
ADR fixes one tokenizer. Parity is a comparison, and a consistent bias cancels in a comparison while an
asymmetric one does not. Rule 6 exists because that cancellation is an assumption worth measuring rather than
asserting — if divergence turns out to be content-dependent rather than uniform, it stops cancelling, and the
project should discover that from its own records rather than from a reviewer.

**Rule 1 is what makes a compound standard defensible rather than evasive.** Recording three numbers is only an
improvement if one of them is unambiguously the rule; otherwise a compound standard becomes a menu, and any
breach can be argued away by selecting the measure under which it did not occur. Designating the enforcement
basis and demoting the others to evidence keeps the compound structure honest.

**Rule 8's scope answer is a consequence of ADR-0003, not a new choice.** Enforcing total-request equality
would be impossible for condition A and redundant for B and C, since their non-memory portions are already
identical under rule 1. The one case that could tempt broadening — a non-memory portion differing for genuine
treatment reasons — is exactly the case that must be *reported* rather than normalised away, because padding to
equalise totals would inject content nobody chose in order to satisfy a metric.

**Rule 9 protects the result the experiment is trying to find.** Vision 10.45 predicts that consolidated
intelligence performs as well or better at *lower* per-task cognitive cost. Equalising consumption rather than
allowance would make that outcome structurally unobservable — the system would be prevented from demonstrating
the efficiency it is supposed to produce.

## Consequences

**Easier:** enforcing an equal ceiling before any compute is spent; attributing size per memory; verifying
ADR-0003 J-4 mechanically; keeping historical measurements interpretable after tokenizer changes; observing
efficiency gains rather than suppressing them.

**Harder:** a tokenizer must be maintained and pinned; three measures must be recorded per segment; divergence
must be computed per run; consumers must be disciplined about which measure is normative.

**Newly required:** a pinned tokenizer identity in environment configuration; per-segment token, character and
byte counts; provider-usage capture with an explicit unavailable marker; a divergence computation in the
experiment record.

**Constrained or unblocked:**

- **ADR-0003** — J-4 becomes mechanically checkable: `budget_B == budget_C` is now a statement about a defined
  quantity. Rule 9's claim boundary becomes verifiable, since the resource control it depends on can be
  demonstrated rather than asserted.
- **ADR-0014** — rule 20's "declared measurement basis" is now supplied.
- **D-14 (port surface)** — the assembly boundary must expose preflight measurement.
- **Benchmark Contract** — inherits the divergence-materiality threshold and any budget *values*; this ADR
  fixes the basis, never the numbers.

**No new durable decision uncovered.** Non-text segment measurement is out of scope because v0 context is text;
should non-text material enter later, the basis question reopens for it specifically.

## Reversibility

High. All three measures are recorded from the start, so changing which is normative later is a policy change
over data already captured — historical runs remain re-analysable under a different basis, which is precisely
why recording all three is worth its cost. Changing the pinned tokenizer is a configuration change visible in
the record (W-4), not a migration.

## Validation / falsification

Revisit if:

- divergence between the pinned tokenizer and provider usage proves **content-dependent** rather than uniform,
  which would break the symmetry argument and require either a provider-matched tokenizer or a wider parity
  margin; or
- provider usage is unavailable often enough that cost auditing becomes unreliable, which would weaken rule 6's
  check without affecting enforcement; or
- per-segment attribution proves impossible for some assembly strategy, indicating rule 2's per-segment
  requirement conflicts with a legitimate way of building context.

Evidence that conditions B and C received materially different actual token counts **despite** equal enforced
budgets would falsify the claim that a pinned local tokenizer is a sufficient parity basis, and would be a
finding about the measurement rather than about MNEXA.

## Outcome

Pending. No implementation and no experiment exist.
