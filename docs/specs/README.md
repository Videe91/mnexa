# MNEXA Specifications

Specifications define **what must be true** after accepted decisions are implemented.

They are narrower than the vision and more concrete than ADRs. A spec should identify its governing vision/ADR references, scope, invariants, domain objects, interfaces, failure semantics, acceptance criteria, and explicit non-goals.

Specs must not contain `TBD` placeholders when approved for implementation. Unresolved D2/D3 questions belong in proposed ADRs first.

The first planned specification is the MNEXA v0 technical specification covering the smallest loop needed to test persistent learning outside model weights:

`Experience → Memory → Context/Recall → Decision/Outcome → Consolidation → Measurable Improvement`
