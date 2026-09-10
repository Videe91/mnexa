# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** v0 decision audit complete. ADR-0002 and ADR-0003 accepted. Specification remains
**blocked** at a D3 approval boundary (ADR-0004).

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0003` — **accepted** 2026-09-10 after four owner-directed precision
amendments. The register `docs/decisions/v0-decision-register.md` holds the inventory of D2/D3 decisions
(D-01 … D-21) plus 5 recorded vision tensions.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002, ADR-0003 and ADR-0004 follow
the template in `docs/decisions/README.md`; all 32 invariants (I-1..I-8/I-9a/I-9b/I-9c/I-10..I-12, J-1..J-10,
K-1..K-8) carry stated mechanical checks; no placeholder text remains; register entries carry tier classification and vision
references; no production code, tests, specification, benchmark harness or plan were created.

**Open D2/D3 decisions:** 21 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-21); D-01,
D-08 and D-09 are settled, 18 remain open.

- `ADR-0002` — experience/interpretation boundary and historical immutability — **accepted**. Settles D-01;
  partially settles D-06; pre-shapes D-07 and D-13.
- `ADR-0003` — resource and cognitive compute parity — **accepted**. Settles D-08 and D-09. Adds claim
  boundaries governing what each of C>A, C>B and C≈B licenses as a conclusion.
- `ADR-0004` — hidden evaluation isolation (D-17) — **proposed, D3, awaiting owner review**.
- D-21 (version pinning of interpretive derivation edges) surfaces **next**, immediately after D-17, per
  owner sequencing. The owner's stated expectation (pin derivation edges; allow mutable heads for
  discovery) is recorded in the register as a *proposed* position, explicitly not accepted.
- Remaining domain-model decisions resume after D-21.

**Known blockers:** ADR-0004 requires explicit owner approval. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits D-21 and the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Owner reviews `ADR-0004`. On acceptance, set its status to `accepted`, record the
approval context without rewriting the original rationale, then surface D-21 as its own ADR. Do not write
MNEXA production code, the benchmark harness, the v0 specification, or an implementation plan.
