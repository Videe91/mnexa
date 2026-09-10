# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** v0 decision audit complete. ADR-0002 accepted. Specification remains **blocked**
at a D3 approval boundary (ADR-0003).

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0002` — **accepted** 2026-09-10 after three owner-directed amendments.
The register `docs/decisions/v0-decision-register.md` holds the inventory of unresolved D2/D3 decisions
(now D-01 … D-21, one settled) plus 5 recorded vision tensions.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002 and ADR-0003 follow the
template in `docs/decisions/README.md`; every invariant carries a stated mechanical check; register entries
carry tier classification and vision references; no production code, tests, specification, benchmark
harness or plan were created.

**Open D2/D3 decisions:** 21 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-21); D-01 is
settled, 20 remain open.

- `ADR-0002` — experience/interpretation boundary and historical immutability — **accepted**. Settles D-01;
  partially settles D-06; pre-shapes D-07 and D-13.
- `ADR-0003` — resource and cognitive compute parity (D-08 + D-09) — **proposed, D3, awaiting owner
  review**.
- D-17 (hidden-evaluation isolation) surfaces as its own ADR after ADR-0003 resolves.
- D-21 (version pinning of interpretive derivation edges) was discovered while amending ADR-0002 and
  recorded rather than decided, since deciding it silently would have expanded the approved decision space.
- Remaining domain-model decisions resume after the experimental-validity ADRs, per owner sequencing.

**Known blockers:** ADR-0003 requires explicit owner approval. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits D-17 and the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Owner reviews `ADR-0003`. On acceptance, set its status to `accepted`, record the
approval context without rewriting the original rationale, then surface the hidden-evaluation isolation ADR
(D-17). Do not write MNEXA production code, the benchmark harness, the v0 specification, or an
implementation plan.
