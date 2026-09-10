# MNEXA Experiments

Experiments are first-class evidence artifacts. They test whether MNEXA's mechanisms create measurable intelligence gains; they are not substitutes for software tests.

Use sequential IDs: `EXP-0001-<slug>.md`.

Every experiment should predeclare its hypothesis, primary metric, baselines, benchmark version, controlled variables, model/configuration, dataset/task version, hidden-evaluation boundary, stopping rule, and raw-result location before execution.

After execution, append observations, metrics, uncertainty/sample size, interpretation, anomalies, and decision impact. Preserve negative and null results.

Benchmark or metric changes made after observing results require versioning and, when they affect what counts as proof, a D3 decision.
