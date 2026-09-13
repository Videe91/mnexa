# Seed Growth 013 — Semantic Closure

## Classification

Exploratory fresh semantic-closure projection ablation.

## Question

Can MNEXA preserve the decision-relevant meaning of grounded evidence
when a structured proposition's nucleus is narrower than the evidence
span that supports it?

## Motivation

Seed Growth 012 established that a grounded structure-repair pass can:

- increase nucleus recall;
- increase nucleus precision;
- eliminate compound nuclei;
- reduce qualifier over-attachment;
- preserve physical evidence ancestry.

It also exposed a more fundamental problem.

A proposition can be physically grounded while its reusable nucleus is
semantically weaker than its source.

Example:

Source:

`never reuse the prior nonce`

Structured representation:

nucleus:

`reuse the prior nonce`

qualifier:

`never`

If the nucleus is later projected as an independent claim, the system
may invert the operational meaning even though every character and
offset is genuinely grounded.

Therefore:

> exact provenance does not guarantee semantic preservation.

## Thesis

Seed 013 tests:

> The nucleus should function as a retrieval/indexing handle when its
> support span carries additional decision-relevant semantics. The
> exact authoritative support span should remain the model-visible
> semantic payload.

The proposed boundary is:

historical evidence
→ grounded structured proposition
→ nucleus as retrieval handle
→ exact support as semantic payload
→ reasoning

## Conditions

Both conditions use:

- the same raw evidence;
- one shared initial structured extraction;
- one shared grounded repair pass;
- the exact same repaired proposition set;
- the same model;
- the same transfer reasoner;
- the same retrieval system;
- the same transfer task.

### Condition A — Current Projection

The structured nucleus is projected as the reusable claim payload.

Conceptually:

`never reuse the prior nonce`

becomes:

nucleus:

`reuse the prior nonce`

claim payload:

`reuse the prior nonce`

### Condition B — Semantic-Closed Projection

The exact same proposition is retained.

The nucleus becomes only a retrieval handle.

The exact support span becomes the model-visible semantic payload.

Conceptually:

retrieval handle:

`reuse the prior nonce`

semantic payload:

`never reuse the prior nonce`

## Critical Control

Target:

`all_repaired_structured_propositions_equal == true`

Condition B receives no additional extraction or repair pass.

Only the projection from structured memory to reusable/model-visible
knowledge changes.

Historical evidence must also remain equal.

Target:

`all_source_evidence_equal == true`

## Semantic Challenge Classes

The fresh benchmark contains 20 families covering:

### Polarity

- `never`
- `do not`

### Scope / Exclusivity

- `only`

### Cardinality

- `exactly`
- `at least`
- `at most`

### Conditions / Exceptions

- `unless`
- `when`
- `if`

## Benchmark Principle

Every semantic target is physically present in authoritative source
evidence.

The experiment does not ask the system to infer hidden semantics from
outside knowledge.

It asks whether decision-relevant semantics already present in the
source survive the knowledge-projection boundary.

## Semantic Dimensions

Each family is assigned one benchmark dimension:

- polarity;
- scope;
- cardinality;
- condition.

A semantic violation means the final transfer answer fails the
pre-registered deterministic semantic contract for that family.

## Projection Eligibility Diagnostic

Seed 012 demonstrated that repair can sometimes delete otherwise valid
knowledge.

Therefore Seed 013 separately records:

`repaired_semantic_clause_supported_families`

This answers:

> Did the semantic evidence survive the repair stage at all?

The primary projection comparison can then also be examined only over
families where the repaired structure still contains exact support for
the semantic clause.

This distinguishes:

repair loss

from:

projection loss.

## Primary Metrics

### Semantic Task Passes

Count of final transfer answers that preserve the pre-registered
semantic contract.

### Polarity Violations

Examples:

- `never X` becoming `X`;
- `do not X` becoming `X`.

### Scope-Loss Violations

Example:

`only cobalt lane`

becoming:

`cobalt lane`

without exclusivity.

### Cardinality-Loss Violations

Examples:

- `exactly 3` becoming `3`;
- `at least 3` becoming `3`;
- `at most 2` becoming `2`.

### Condition-Loss Violations

Examples:

- `when X, do Y` becoming unconditional `do Y`;
- `do not X unless Z` losing the exception boundary.

### Exact Semantic Clause Visibility

Does the model-visible durable lesson contain the exact
decision-relevant clause?

## Safety Metrics

Targets:

`repaired_source_ancestry_valid_families == 20`

`current_unsupported_claims_admitted == 0`

`semantic_closed_unsupported_claims_admitted == 0`

## Resource Parity

Both conditions share:

- the same initial extraction call;
- the same repair call;
- the same repaired propositions.

Projection itself is deterministic in both conditions.

Therefore:

`current_projection_model_calls == 0`

`semantic_closed_projection_model_calls == 0`

Both conditions receive one transfer-reasoning call per family.

The semantic-closed condition may contain more model-visible words
because it deliberately preserves complete support payloads.

That cost is recorded rather than hidden.

## Scientific Interpretation

A successful result would show:

- semantic-closed task success > current projection;
- polarity violations decrease;
- scope-loss violations decrease;
- cardinality-loss violations decrease;
- condition-loss violations decrease;
- exact semantic clause visibility increases;
- unsupported claims remain zero;
- source ancestry remains valid;
- repaired proposition sets remain identical.

The strongest narrow claim would be:

> Exact evidence ancestry is insufficient by itself; preserving the
> authoritative semantic payload across the memory-to-claim boundary
> reduces meaning loss without requiring a new extraction pass.

## What Seed 013 Does Not Prove

It does not prove:

- universal natural-language entailment;
- universal semantic equivalence;
- causal understanding;
- truth beyond supplied evidence;
- contradiction resolution;
- safe multi-source synthesis;
- conventional-RAG superiority.

It tests one narrower boundary:

> Can exact grounded evidence retain its decision-relevant semantics
> when transformed into reusable knowledge?

## Frozen Components

No changes to:

- `mnexa_seed.py`
- canonical persistence
- retrieval
- embeddings
- ranking
- context budget
- source-role admission
- structured grounding gate
- repair mechanism
- transfer reasoner

Only the projection/rendering of an already repaired proposition is
ablated.

## Burn Rule

The fresh Seed 013 task set is burned after the first live execution.

Do not tune:

- projection wording;
- semantic graders;
- tasks;
- source clauses;
- repair prompt;
- transfer prompt

against the live result and rerun it as fresh evidence.
