---
id: ADR-0015
status: accepted
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

**Approval:** accepted by owner 2026-09-10, following three owner-directed amendments made while the ADR was
still `proposed`. The record below is as amended and approved.

**Amendment history (all pre-acceptance, owner-directed):**

1. **Memory-contributed context defined precisely.** The original left the measured quantity unstated, allowing
   treatment-specific scaffolding to escape the budget by being called formatting, and gave no rule for
   mixed-provenance segments. — rules 8a–8d, W-12 … W-15.
2. **"Pinned local tokenizer" replaced by a pinned Context Measurement Profile.** A tokenizer identity alone
   does not determine a count — wrappers, role boundaries, normalization and special-token handling all
   contribute. — rules 1–3, W-1, W-4, W-16.
3. **Provider usage is secondary evidence, not ground truth or cost — and its divergence is not assumed to
   cancel.** The original justified the local basis partly by arguing measurement error is symmetric across B
   and C. **That argument was too strong**: B and C contain different memory text, so error can be
   content-dependent. — rules 4, 4a–4c, 6, W-5, W-7, W-17 … W-19.

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

1. **Exactly one basis is normative for parity enforcement: the pinned Context Measurement Profile.** The
   other two measures are **recorded but never used for enforcement**. A compound standard is only safe if it
   is unambiguous which number *is* the budget; three co-equal measures would let a breach be argued away by
   choosing a favourable one.

2. **The Context Measurement Profile is one immutable, pinned convention per primary experimental
   configuration.** A tokenizer identity alone does not determine a count. The profile must resolve enough to
   deterministically reproduce the normative count, including where relevant:

   - tokenizer implementation or artefact identity;
   - tokenizer version and hash;
   - normalization rules;
   - special-token handling;
   - model and message wrapper accounting;
   - role and message-boundary accounting;
   - tool-schema accounting where included;
   - canonicalization and serialization rules relevant to the normative count;
   - any other deterministic accounting rule the chosen model interface requires.

   It does **not** require provider-private tokenization internals, which are unavailable.

   **The profile is the normative experimental measurement convention.** It is not a claim to reproduce the
   provider's internal physical token accounting.

3. **The normative count is reproducible and preflight.** For a given canonical `ContextAssembled` input and a
   given pinned profile, the count must be reproducible. The B/C memory allowance is enforced using the profile
   **before** model invocation — a ceiling checked after submission is not a ceiling. The profile identity and
   hash are preserved in the relevant trace so historical parity can be audited later.

### The recorded measures

4. **Provider-reported usage is post-hoc audit evidence.** The term is deliberate: it is what the provider
   reported, **not** a universal token ground truth. It is recorded when available, never used for enforcement,
   and its absence never blocks a run.

4a. **Provider-reported categories are preserved as reported.** Raw categories and enough identity and
   semantics to understand what they mean are retained. Distinct categories are **not** silently collapsed into
   one number where the distinction — cached versus uncached input, for instance — materially affects resource
   analysis.

4b. **Provider usage is not monetary cost.** If monetary cost is calculated later, the applicable pricing
   schedule and billing semantics must be separately identifiable, because pricing changes without the
   historical invocation changing. This ADR does not design a financial-cost subsystem.

5. **Character and byte counts are recorded per segment** for the canonical presented material, as durable
   provider-independent descriptive evidence. **They are never represented as direct measures of inference
   compute.**

6. **Divergence is measured, and is not assumed to cancel.** The experiment record must permit comparing the
   normative profile measurement against provider-reported actual request usage wherever the latter exists.

   **Do not assume local measurement error cancels merely because B and C use the same model.** B and C contain
   different memory text, so measurement error can be content-dependent and therefore treatment-dependent.

   Where divergence is material, or systematically differs between treatments, it must be surfaced as a
   **resource-parity validity concern** — not hidden behind the observation that the normative budget passed.
   *Tolerance, diagnostic method and the consequence of material divergence are predeclared by the Benchmark
   Contract, not chosen here.*

### Honesty

7. **An estimate is never labelled exact.** Per ADR-0014 rule 20, the basis is stated with every measurement.
   The enforcement basis is exact **with respect to the pinned tokenizer** and approximate with respect to the
   provider; both statements are recorded, and neither is presented as the other.

### Parity scope

8. **Parity is enforced over the memory-contributed allowance only.** Total request input is **recorded, not
   equalised**.

8a. **"Memory-contributed" means model-visible material contributed by the persistent-memory treatment**, and
   is measured against the final `ContextAssembled` representation that would actually be supplied to the
   reasoning seat — **never** the size of the source memories before formatting or transformation.

   It includes, where applicable: recalled memory text; excerpts; summaries; model-generated memory
   transformations; memory-specific labels; citations and provenance displayed to the model; headers;
   separators; annotations; treatment-specific instructions; and any other model-visible scaffolding that
   exists **because** persistent memory is being supplied.

   **Treatment-specific material must not escape the memory budget by being classified as formatting.**
   Model-visible material that is genuinely common to the compared conditions — treatment-independent — may
   remain outside the allowance.

8b. **Mixed-provenance segments count in full.** ADR-0014 rule 7a permits one presented segment to derive from
   several sources — a persistent memory `M7` plus a live tool result `T3` synthesised into segment `S4`. For
   v0, fractional or subjective attribution is avoided:

   > **If a presented segment has any persistent-MNEXA-memory ancestry, the entire model-visible segment counts
   > toward the memory-contributed budget.**

   This may over-count, and that is the intended direction: it prevents memory content being laundered through
   mixed-source synthesis, and it is mechanically enforceable. A future version may supersede it with finer
   attribution **on evidence**.

8c. **Accounting is over presented model-visible material.** Where only an excerpt or transformation was
   presented, the full size of the underlying source object is **not** counted — only what actually appeared.

8d. **Condition A receives no artificial memory block.** A injects no persistent memory and is **never padded**
   with meaningless tokens to equalise context size. Its lack of persistent-memory context *is* the
   experimental condition.

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
| W-1 | Exactly one basis is normative for enforcement | Assert the enforcement basis is the pinned Context Measurement Profile; assert no enforcement path reads provider usage or character counts |
| W-2 | Budget enforcement occurs before submission | Assert the ceiling is evaluated preflight; assert no path submits first and checks after |
| W-3 | Memory-contributed size is attributable per segment | Assert per-segment sizes exist and sum consistently with the memory-contributed total |
| W-4 | Measurement-profile identity and hash are recorded per assembly | Assert non-null on every `ContextAssembled`; assert a profile change is visible between records |
| W-5 | Provider-reported usage is recorded where available | Assert the field is populated when the provider supplies it, and explicitly marked unavailable otherwise |
| W-6 | Character and byte counts are recorded per segment | Assert both present for every segment |
| W-7 | Divergence between enforcement basis and provider usage is computed and reported | Assert the experiment record carries the divergence per run where provider usage exists |
| W-8 | No measurement is labelled exact beyond its basis | Assert each recorded measure names its basis; assert profile-based figures are not described as provider-exact, and character counts are not described as compute measures |
| W-9 | `budget_B == budget_C` for the memory-contributed allowance, and A's is zero | Assert declared allowances equal for B and C under the enforcement basis (satisfies ADR-0003 J-4) |
| W-10 | Total request input is recorded but never equalised | Assert totals are recorded; assert no path pads or trims to force equality |
| W-11 | Consumption is never constrained to equality | Assert only the ceiling is enforced; assert actual usage below the ceiling is never adjusted, e.g. `B 1900/2000` alongside `C 1200/2000` is valid |
| W-12 | Memory-contributed size is measured on the presented representation, not the source | Assert the counted quantity is the `ContextAssembled` segment content; assert source-object size is never substituted |
| W-13 | Treatment-specific scaffolding is inside the memory budget | Assert labels, headers, separators, citations, annotations and treatment-specific instructions that exist because memory is supplied are counted; assert none is excluded as formatting |
| W-14 | Any segment with persistent-memory ancestry counts in full | Fixture synthesising a memory with a live tool result; assert the whole segment counts toward the memory allowance |
| W-15 | Condition A is never padded | Assert no synthetic memory block or filler is added to A |
| W-16 | The normative count is reproducible from canonical input plus profile | Recompute from the recorded `ContextAssembled` and profile; assert the count matches |
| W-17 | Provider-reported categories are preserved as reported | Assert distinct categories such as cached versus uncached are retained separately, not summed |
| W-18 | Provider usage is not treated as monetary cost | Assert no path derives cost without a separately identified pricing schedule |
| W-19 | Divergence is reported per treatment, not pooled | Assert divergence is computed separately for B and C so treatment-dependent error is visible |

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

**On the local basis's inaccuracy, an earlier draft argued too strongly.** It claimed the profile's
disagreement with the provider is symmetric across B and C, so a consistent bias cancels in a comparison.
**That argument does not hold.** B and C contain *different memory text* — retrieved chunks versus consolidated
representations — and tokenizer disagreement is content-dependent. A bias that varies with content is a bias
that varies with treatment, and treatment-dependent measurement error does not cancel; it is indistinguishable
from a treatment effect.

The profile is therefore justified on its *function*, not on an assumed cancellation: it is the only candidate
that can enforce a ceiling before compute is spent and attribute size per segment. Rule 6 exists because the
cancellation cannot be assumed — divergence must be computed **per treatment** (W-19) so a treatment-dependent
error is visible rather than pooled into an average that hides it. Where such divergence appears, it is a
resource-parity validity concern in its own right, and reporting that the normative budget passed is not an
answer to it.

**Rules 8a–8c decide what is actually being counted, which is where a budget is most easily evaded.** The
tempting reading of "memory-contributed" is *the memories*, but what reaches the model is memories plus the
apparatus that presents them — labels, citations, separators, and any instruction that exists only because
memory is being supplied. Classifying that apparatus as formatting would let condition C receive
treatment-specific prompt material outside the budget meant to constrain it, which is precisely the leak
ADR-0003 rule 3 exists to prevent.

Rule 8b takes the conservative side of a genuine trade. Fractional attribution across a synthesised segment
would be more accurate in principle and unenforceable in practice, since any split is a judgement. Counting the
whole segment over-counts C's memory usage — which disadvantages C — and that is the right direction for a rule
protecting against C gaining an unfair advantage. A rule whose error favours the treatment it constrains is not
a rule.

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

**Newly required:** a pinned Context Measurement Profile per experimental configuration, with identity and
hash recorded per assembly; per-segment profile, character and byte counts; provider-usage capture preserving
reported categories, with an explicit unavailable marker; a per-treatment divergence computation in the
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
should non-text material enter later, the basis question reopens for it specifically. The financial-cost
subsystem implied by rule 4b is likewise out of scope and is not registered, since v0 makes no cost claim.

## Reversibility

High. All three measures are recorded from the start, so changing which is normative later is a policy change
over data already captured — historical runs remain re-analysable under a different basis, which is precisely
why recording all three is worth its cost. Changing the pinned tokenizer is a configuration change visible in
the record (W-4), not a migration.

## Validation / falsification

Revisit if:

- divergence proves materially treatment-dependent, which rule 6 anticipates and W-19 is designed to expose —
  requiring either a provider-matched profile, a wider parity margin, or an explicit validity caveat on the
  affected result; or
- provider usage is unavailable often enough that cost auditing becomes unreliable, which would weaken rule 6's
  check without affecting enforcement; or
- per-segment attribution proves impossible for some assembly strategy, indicating rule 2's per-segment
  requirement conflicts with a legitimate way of building context.

Evidence that conditions B and C received materially different actual token counts **despite** equal enforced
budgets would falsify the claim that a pinned local tokenizer is a sufficient parity basis, and would be a
finding about the measurement rather than about MNEXA.

## Outcome

Pending. No implementation and no experiment exist.
