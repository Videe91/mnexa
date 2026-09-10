# Scientific Method Rules

MNEXA's central thesis must be earned by reproducible evidence.

## Tests versus experiments

Tests answer: "Does the implementation satisfy its contract?"

Experiments answer: "Does this mechanism make the system measurably better under a controlled comparison?"

Passing tests never substitutes for experimental proof.

## Benchmark integrity

Before implementing a mechanism that will be evaluated, freeze the relevant benchmark contract. The contract must define task populations, train/experience versus hidden-evaluation boundaries, primary metrics, allowed tools, model configuration, stopping rules, and comparison baselines.

Do not inspect, retrieve, memorize, prompt with, tune against, or special-case hidden evaluation instances.

If a benchmark rule changes after results are observed, record the change as a D3 decision and preserve the earlier result under the earlier benchmark version.

## Controlled comparisons

Where the hypothesis concerns MNEXA memory, hold constant everything practical except the memory condition. A typical comparison is:

- frozen model + no persistent memory
- same frozen model + conventional retrieval baseline
- same frozen model + MNEXA

Record deviations explicitly.

## Reproducibility

Every experiment record must identify at minimum:

- experiment ID
- hypothesis
- repository commit
- model/provider and exact model identifier
- model parameters relevant to reproducibility
- tool set
- dataset/task-set version
- benchmark contract version
- random seed(s), when applicable
- memory condition
- primary and secondary metrics
- raw-result location
- execution timestamp/environment notes

## Evidence discipline

- Write the hypothesis and primary metric before running the experiment.
- Preserve negative, null, and contradictory results.
- Do not cherry-pick runs without recording the selection rule.
- Separate observation from interpretation.
- Report uncertainty and sample size.
- Treat simulation/replay as weaker evidence than independent real execution where the distinction matters.
- A mechanism that cannot beat a simpler baseline should not be promoted merely because its architecture is elegant.

## Outcome loop

Unexpected results are first-class project inputs. When evidence contradicts an accepted architectural belief, create a decision issue/ADR rather than explaining the contradiction away.
