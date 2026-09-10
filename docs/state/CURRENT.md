# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** v0 decision audit complete. Specification is **blocked** at a D3 approval boundary.

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** amended `ADR-0002` (proposed). The register
`docs/decisions/v0-decision-register.md` holds the inventory of 20 unresolved D2/D3 decisions required to
make the v0 specification precise, plus 5 recorded vision tensions.

**Verification:** Documentation-only change. Verified by inspection: register entries carry tier
classification and vision references; ADR-0002 follows the template in `docs/decisions/README.md`; no
production code, tests, spec or plan were created.

**Open D2/D3 decisions:** 20 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-20).

- `ADR-0002` — experience/interpretation boundary and historical immutability — **proposed (amended
  2026-09-10 on owner direction), D3, awaiting owner approval**. Blocks D-02, D-03, D-04, D-05, D-06, D-07,
  D-13 and therefore the whole domain model.
- D-08, D-09, D-17 (experimental validity) are **queued next** by owner sequencing decision, ahead of the
  remaining domain-model decisions. Recommended decomposition: two ADRs — resource parity (D-08 + D-09) and
  hidden-evaluation isolation (D-17).
- All other entries remain unsurfaced pending sequencing.

**Known blockers:** ADR-0002 requires explicit owner approval before the v0 specification may be written.
Per `.claude/rules/decisions.md`, work does not proceed past an unapproved D3 boundary.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Owner reviews amended `ADR-0002`. On acceptance, set its status to `accepted`,
record the approval context without rewriting the original rationale, then surface the resource-parity ADR
(D-08 + D-09) followed by the hidden-evaluation isolation ADR (D-17), per the owner sequencing decision.
Do not write MNEXA production code, the benchmark harness, the v0 specification, or an implementation plan.
