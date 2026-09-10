# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** ADR-0002 … ADR-0006 accepted. Domain-model work has begun: `ADR-0007` proposes the
canonical v0 object set. Specification remains **blocked** at that D3 approval boundary.

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0007` — **proposed** 2026-09-10. The register
`docs/decisions/v0-decision-register.md` holds the inventory of D2/D3 decisions (D-01 … D-24) plus 5 recorded
vision tensions, one of which (T-1) ADR-0007 resolves.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002, ADR-0003 and ADR-0004 follow
the template in `docs/decisions/README.md`; all 80 invariants (14 I-, 10 J-, 17 K-, 10 L-, 21 M-, 8 N-) carry
stated mechanical checks; no placeholder text remains; register entries carry tier classification and vision
references; no production code, tests, specification, benchmark harness or plan were created.

**Open D2/D3 decisions:** 24 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-24); D-01, D-08,
D-09, D-17, D-21 and D-22 are settled, 18 remain open.

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
- `ADR-0007` — canonical v0 object set and plane assignment (D-02) — **proposed, D3, awaiting owner
  review**. Three canonical objects (ExperienceRecord, Entity, Interpretation); eleven concepts demoted to
  event types or projections; adopts criterion β for plane assignment.
- D-03 (episode construction authority) is **narrowed, not blocked**: ADR-0007 fixes Episode's plane, leaving
  D-03 purely about who draws boundaries, when, and how they are revised.
- D-24 (historical-to-historical reference semantics) was discovered while drafting ADR-0007 and recorded
  rather than decided. **D-12 is blocked on it.**
- D-23 (supersession change classification) remains **deferred**: not required for a correct v0 spec.
- Remaining after D-02: D-03 … D-07, D-10 … D-16, D-18 … D-20, D-23, D-24.

**Known blockers:** `ADR-0007` requires explicit owner approval before the domain model may be written. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Owner reviews `ADR-0007`. On acceptance, set its status to `accepted`, record the
approval context without rewriting the original rationale, then surface D-03 (episode construction
authority) as its own ADR. Do not write MNEXA production code, the benchmark
harness, the v0 specification, or an implementation plan.
