# 31. Seed Growth 028 — Competing-Hypothesis Reasoning

## Hypothesis

When uncertainty-preserving attention (Seed 027 Quorum) expands active context to multiple candidate memories, adding an explicit epistemic reasoning frame to the transfer prompt prevents the reasoner from conflating mutually incompatible candidate rules into a single decision.

## Principle

> Preserve alternatives without conflating them.

## Implementation & Framing

Condition A uses standard transfer reasoning. Condition B appends a fixed epistemic instruction to the same base query:

```text
EPISTEMIC INSTRUCTION:
The memories available for this question are alternative candidate hypotheses, not cumulative facts.
Some candidate rules may be mutually incompatible.
Select the single candidate rule whose decision-relevant evidence best answers the question.
Do not merge, list, or present incompatible candidate rules together as if they were simultaneously true.
State only the chosen rule...
```

- **Strict Post-Hoc Exclusive Grader**: Target rule present AND 0 competing candidate rule hits. Metadata isolated via `runtime_family()`.
- **Zero Model Calls for Context Assembly/Grading**: 0 ranker model calls, 0 assembler model calls, 0 grader model calls.

## Live Execution Results

- **Run ID**: `20260914T115754Z`
- **Taskset SHA256**: `2d24af18b2b344420b74e7c448fe95e56eb24f113ec3cbffd13e818456f34a6d`
- **Model**: `gpt-4o-mini`
- **Embedder**: `sentence-transformers/all-MiniLM-L6-v2`

| Metric | Condition A (Standard Reasoning) | Condition B (Competing Hypothesis) | Diagnostic Impact |
| :--- | :---: | :---: | :---: |
| **Presentation Causal Validity** | Valid: 15/20 | Valid: 15/20 | `presentation_causal_interpretation_valid = false` (5 leaks) |
| **Target Rule Present Rate** | 19 / 20 (95.0%) | 18 / 20 (90.0%) | -1 target rule present |
| **Competing Rule Mentions** | 3 families (3 hits) | **2 families (2 hits)** | **-1 family (-33.3%)** |
| **Strict Exclusive Correct Passes** | 17 / 20 (85.0%) | **18 / 20 (90.0%)** | **+1 pass (+5.0%)** |
| **Multi-Memory Exclusive Passes** | 5 / 8 (62.5%) | **6 / 8 (75.0%)** | **+1 pass (+12.5%)** |
| **Multi-Memory Competing Mentions**| 3 / 8 (37.5%) | **2 / 8 (25.0%)** | **-1 family (-12.5%)** |
| **Exclusive Rescues / Harms** | - | **2 Rescues / 1 Harm** | Net +1 |
| **Admitted Unsupported Claims** | 0 | 0 | Clean safety |

## Cluster Breakdown (Strict Exclusive Pass Rate)

| Cluster | Condition A Exclusive Pass | Condition B Exclusive Pass | Competing Hits A | Competing Hits B | Multi-Memory Contexts |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `channel-session` | 5/5 (100%) | 5/5 (100%) | 0 | 0 | 3 |
| `lane-routing` | 5/5 (100%) | 5/5 (100%) | 0 | 0 | 1 |
| `retry-policy` | 3/5 (60%) | 3/5 (60%) | 2 | 2 | 5 |
| `storage-finalization` | 4/5 (80%) | **5/5 (100%)** | 1 | **0** | 4 |

## Key Findings

1. **Presentation Control Leakage Identified**: In 5 of 20 families, appending the epistemic prompt to `seed.decide(query_text)` altered the query string passed to memory activation, causing different memory segments to be returned (`presentation_causal_interpretation_valid = false`). This invalidates a strict pure-presentation causal claim and highlights an architectural requirement: **Recall query and reasoner prompt must be decoupled in the runtime API**.
2. **Competing Rule Reduction in Storage-Finalization**: In `storage-finalization`, epistemic framing successfully eliminated competing rule mentions (1 -> 0 hits), boosting exclusive pass rate from 80% to 100%.
3. **Strict Exclusive Pass Rate Improved**: Exclusive correctness rose from 17/20 (85%) to 18/20 (90%), with 2 rescues and 1 harm.
4. **Persistent Distractor Challenge**: In `retry-policy`, 2 families continued to mention competing rules ("at least ten" vs "exactly nineteen"), demonstrating that prompt instructions alone are insufficient to resolve structural rule competition when distractor propositions remain in active context.

## Conclusion

Epistemic framing modestly improves exclusive decision clarity (17 -> 18 passes, -33% competing mentions), but live execution revealed a key architectural constraint: passing reasoner instructions through `seed.decide(prompt)` leaks into memory retrieval. Full decoupling of recall addressing from reasoner instructions is required for clean epistemic arbitration.
