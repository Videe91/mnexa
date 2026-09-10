# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** v0 decision audit complete. ADR-0002 … ADR-0006 accepted. Experimental-validity and
provenance-semantics decisions are settled. Specification remains **blocked** on the domain model: **D-02**
(canonical object set), tightly coupled to **D-03**.

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0006` — **accepted** 2026-09-10 after two owner-directed precision
amendments. The register `docs/decisions/v0-decision-register.md` holds the inventory of D2/D3 decisions
(D-01 … D-23) plus 5 recorded vision tensions.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002, ADR-0003 and ADR-0004 follow
the template in `docs/decisions/README.md`; all 72 invariants (14 I-, 10 J-, 17 K-, 10 L-, 21 M-) carry stated
mechanical checks; no placeholder text remains; register entries carry tier classification and vision
references; no production code, tests, specification, benchmark harness or plan were created.

**Open D2/D3 decisions:** 23 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-23); D-01, D-08,
D-09, D-17, D-21 and D-22 are settled, 17 remain open.

- `ADR-0002` — experience/interpretation boundary and historical immutability — **accepted**. Settles D-01;
  partially settles D-06; pre-shapes D-07 and D-13.
- `ADR-0003` — resource and cognitive compute parity — **accepted**. Settles D-08 and D-09. Adds claim
  boundaries governing what each of C>A, C>B and C≈B licenses as a conclusion.
- `ADR-0004` — hidden evaluation isolation — **accepted**. Settles D-17. Adds the evaluation epoch, the
  one-way Evaluation Evidence Sink, and the SEALED → EXPOSED → RETIRED exposure lifecycle.
- `ADR-0005` — version pinning of interpretive derivation edges — **accepted**. Settles D-21. Strict
  commit-order preexistence; derivation edge set covered by version content identity.
- `ADR-0006` — stale dependency policy — **accepted**. Settles D-22. Four-state derived freshness
  assessment that never mutates a version; revalidation creates new epistemic history rather than restoring
  a version.
- **D-02 (canonical object set) is the next blocker**, tightly coupled to D-03 (episode definition and
  construction authority). No ADR drafted yet — awaiting owner direction on whether to surface them as one
  ADR or two.
- D-23 (supersession change classification) is **deferred**: not required for a correct v0 spec, since
  ADR-0006's uniform treatment of supersessions is complete and safe on its own.
- Remaining after D-02/D-03: D-04 … D-07, D-10 … D-16, D-18 … D-20, D-23.

**Known blockers:** D-02 requires an accepted ADR before the domain model may be written. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Surface **D-02** (canonical object set for v0) as a proposed ADR, after owner
direction on whether D-03 belongs in the same ADR or a separate one. Do not write MNEXA production code, the benchmark
harness, the v0 specification, or an implementation plan.
