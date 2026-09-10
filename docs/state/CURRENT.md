# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** ADR-0002 … ADR-0010 accepted. Object model, reference semantics, episode construction
and the temporal model are settled. Specification remains **blocked** on **D-10** (recall reproducibility),
which has no ADR drafted.

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0010` — **accepted** 2026-09-10 after three owner-directed amendments,
carrying an approved refinement now noted in ADR-0004 and ADR-0006. The register `docs/decisions/v0-decision-register.md` holds the inventory of D2/D3 decisions (D-01 … D-26) plus 5
recorded vision tensions, one of which (T-1) ADR-0007 resolved.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002, ADR-0003 and ADR-0004 follow
the template in `docs/decisions/README.md`; all 138 invariants (14 I-, 10 J-, 17 K-, 10 L-, 21 M-, 11 N-, 16 P-,
15 Q-, 24 R-) carry stated mechanical checks; no placeholder text remains; register entries carry tier classification and vision
references; no production code, tests, specification, benchmark harness or plan were created.

**Open D2/D3 decisions:** 26 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-26); D-01, D-02,
D-03, D-05, D-08, D-09, D-17, D-21, D-22 and D-24 are settled, 16 remain open.

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
- `ADR-0007` — canonical v0 object set and plane assignment — **accepted**. Settles D-02. Three canonical
  objects (ExperienceRecord, Entity, Interpretation); eleven concepts demoted; criterion β for plane
  assignment. Event-type list is provisional, not closed.
- `ADR-0008` — historical-to-historical reference semantics — **accepted**. Settles D-24. Structural edges
  admitted on evidence, backward-only, inline when known at commit and `RelationshipRecorded` when discovered
  later. Unblocked D-12.
- `ADR-0009` — episode construction and boundary authority — **accepted**. Settles D-03. Episodes carry
  opaque MNEXA identity; external session keys are evidence only; validation establishes admissibility, not
  boundary truth; episodes form at consolidation only.
- `ADR-0010` — temporal and ordering semantics — **accepted**. Settles D-05. Four temporal concepts;
  `commit_sequence` as visibility linearization with `AS_OF(N)` immutability; eligibility distinguished from
  activation and from attributed use. Its rule 21 epoch refinement is recorded in ADR-0004 and ADR-0006 under
  *Subsequent refinement*, without rewriting their accepted history.
- **D-10 (recall reproducibility) is the next blocker** — chosen by specification impact plus upstream
  position. It holds the knowledge-watermark carrier and the activation boundary that D-12 and D-13 both
  need. No ADR drafted; awaiting owner direction.
- D-26 (episode lineage revision targeting policy) was discovered while amending ADR-0009 and recorded rather
  than decided.
- D-23 (supersession classification) and D-25 (episode split/merge) remain **deferred**: neither is required
  for a correct v0 spec.
- Remaining after D-05: D-04, D-06, D-07, D-10 … D-16, D-18 … D-20, D-23, D-25, D-26.

**Known blockers:** D-10 requires an accepted ADR before the Context Frame and Recall contracts may be
written, and before D-12 and D-13 can be settled. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Surface **D-10** (recall reproducibility) as a proposed ADR, on owner direction. Do not write MNEXA production code, the benchmark
harness, the v0 specification, or an implementation plan.
