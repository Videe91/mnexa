# Seed Growth 019 — Degraded Identity Activation

## Question

Can MNEXA preserve useful memory activation as exact identity
information is progressively removed?

## Principle

> Addressing should degrade gracefully.

## Conditions

A — Seed 018 exact identity overlap else global fallback.

B — hierarchical activation:

code
→ system
→ cluster
→ domain
→ global fallback

Downstream semantic, lexical, entity retrieval and RRF remain unchanged.

## Pool

20 memories.

5 systems × 4 semantic neighborhoods.

Each system owns four memories.

Each semantic neighborhood spans five systems.

## Degradation Modes

Five families each:

- full_identity
- code_only
- system_only
- context_only

## Expected Candidate Geometry

Full identity:

A may retain the four memories sharing the system because Seed 018
matches any identity-anchor overlap.

B should prefer the unique code and narrow to one.

Code only:

A and B should normally narrow to one.

System only:

A and B should normally narrow to four.

Context only:

A falls back to all twenty memories.

B should normally narrow to the five-memory cluster neighborhood.

## Primary Metrics

- task success by degradation mode
- target clause visibility
- candidate recall
- candidate precision
- candidate-set size
- wrong-memory presentation
- global fallback frequency

## Controls

Both conditions must use:

- identical learned target memory
- identical source evidence
- identical compact representation
- identical transfer query
- identical context budget
- identical downstream retrieval implementation
- identical transfer reasoner

Routers use zero model calls.

The hierarchical router must not receive:

- family ID
- semantic clause
- semantic grader
- correct answer
- canonical atoms

## Scientific Boundary

Seed 019 does not test fuzzy entity linking or learned identity
resolution.

It tests deterministic graceful degradation across already-available
runtime metadata.

## Burn Rule

The fresh task set is burned after the first live execution.
