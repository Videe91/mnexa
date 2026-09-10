# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** v0 decision audit complete. ADR-0002, ADR-0003 and ADR-0004 accepted. The three
experimental-validity decisions are settled. Specification remains **blocked** at a D3 approval boundary
(ADR-0005).

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0004` — **accepted** 2026-09-10 after two owner-directed amendments. The
register `docs/decisions/v0-decision-register.md` holds the inventory of D2/D3 decisions (D-01 … D-22) plus
5 recorded vision tensions.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002, ADR-0003 and ADR-0004 follow
the template in `docs/decisions/README.md`; all 48 invariants (14 I-, 10 J-, 17 K-, 7 L-) carry stated
mechanical checks; no placeholder text remains; register entries carry tier classification and vision
references; no production code, tests, specification, benchmark harness or plan were created.

**Open D2/D3 decisions:** 22 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-22); D-01,
D-08, D-09 and D-17 are settled, 18 remain open.

- `ADR-0002` — experience/interpretation boundary and historical immutability — **accepted**. Settles D-01;
  partially settles D-06; pre-shapes D-07 and D-13.
- `ADR-0003` — resource and cognitive compute parity — **accepted**. Settles D-08 and D-09. Adds claim
  boundaries governing what each of C>A, C>B and C≈B licenses as a conclusion.
- `ADR-0004` — hidden evaluation isolation — **accepted**. Settles D-17. Adds the evaluation epoch, the
  one-way Evaluation Evidence Sink, and the SEALED → EXPOSED → RETIRED exposure lifecycle.
- `ADR-0005` — version pinning of interpretive derivation edges (D-21) — **proposed, D3, awaiting owner
  review**. Reclassified D2 → D3; rationale in the register.
- D-22 (re-derivation policy for stale abstractions) was discovered while drafting ADR-0005 and recorded
  rather than decided.
- Remaining domain-model decisions (D-02 … D-07, D-10 … D-16, D-18 … D-20, D-22) resume after D-21.

**Known blockers:** ADR-0005 requires explicit owner approval. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Owner reviews `ADR-0005`. On acceptance, set its status to `accepted`, record the
approval context without rewriting the original rationale, then resume the remaining domain-model decisions
in dependency order (D-02, D-03, D-04, D-05, D-06 …). Do not write MNEXA production code, the benchmark
harness, the v0 specification, or an implementation plan.
