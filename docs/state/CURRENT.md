# Current MNEXA State

**Phase:** MNEXA v0 — specification phase, decision audit stage

**Current milestone:** ADR-0002 … ADR-0016 accepted. The v0 cognitive loop is structurally complete except for
consolidation. Specification remains **blocked** on **D-18** (failure semantics, idempotency and ledger
durability), which has no ADR drafted.

**Branch:** `spec/mnexa-v0`

**Canonical vision:** `docs/vision/00-README.md`

**Active specification:** None. `docs/specs/0001-mnexa-v0.md` is **not written** and must not be written
until the durable decisions it depends on are accepted.

**Active implementation plan:** None.

**Last completed artifact:** `ADR-0016` — **accepted** 2026-09-10 after three owner-directed amendments,
carrying two approved refinements now recorded in ADR-0008. The register `docs/decisions/v0-decision-register.md` holds the inventory of D2/D3 decisions (D-01 … D-26) plus 5
recorded vision tensions, one of which (T-1) ADR-0007 resolved.

**Verification:** Documentation-only change. Verified by inspection: ADR-0002, ADR-0003 and ADR-0004 follow
the template in `docs/decisions/README.md`; all 267 invariants (14 I-, 10 J-, 17 K-, 10 L-, 21 M-, 11 N-, 16 P-,
15 Q-, 24 R-, 25 S-, 14 T-, 13 U-, 28 V-, 19 W-, 30 X-) carry stated mechanical checks; no placeholder text remains; register entries carry tier classification and vision
references; no production code, tests, specification, benchmark harness or plan were created.

**Open D2/D3 decisions:** 33 recorded in `docs/decisions/v0-decision-register.md` (D-01 … D-33); D-01, D-02,
D-03, D-05, D-08, D-09, D-10, D-12, D-13, D-17, D-21, D-22, D-24, D-27, D-28 and D-31 are settled, 17 remain
open — of which D-19, D-23, D-25 and **D-30** are deferred.

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
- `ADR-0011` — recall reproducibility and evidence contract — **accepted**. Settles D-10. Historical replay
  mandatory and independent of the live retriever; content recoverable, not merely hashed; `AS_OF(N)` bound as
  a fixed snapshot before retrieval; recall read-only; `RecallPerformed` event type. **Unblocked D-13.**
- `ADR-0012` — v0 retrieval channel set — **accepted**. Settles D-27. Three channels — semantic, lexical/exact
  and entity — as three addressing modes; head-as-of-N default candidate pool; entity channel consumes but
  never establishes identity.
- `ADR-0013` — cognitive-cycle knowledge snapshot scope — **accepted**. Settles D-28. One watermark per cycle
  governing persistent intelligence only; arriving commits do not invalidate a cycle; authorization is not
  frozen. `CognitiveCycle` is a correlation identity, **not** a fourth canonical object.
- `ADR-0014` — activation and context trace — **accepted**. Settles D-13 (narrowed). Atomic `ContextAssembled`
  with an ordered segment manifest and separate many-to-many returned-item disposition; `PRESENTED` normative,
  `MemoryActivated` a projection; the trace is never an authorization side channel. Carried two approved
  refinements to ADR-0007 and ADR-0008. **Unblocked D-12 and D-30.**
- `ADR-0015` — context measurement basis — **accepted**. Settles D-31. Compound standard with exactly one
  normative preflight basis, the pinned Context Measurement Profile; memory-contributed context defined over
  presented model-visible material; divergence measured per treatment, never assumed to cancel.
- `ADR-0016` — decision, prediction, action and outcome evidence — **accepted**. Settles D-12. Four event
  kinds; the action boundary is dispatch, not attempt; absence of outcome or action is absence of evidence,
  never failure; structural edges have no transitive closure. Added `decided_from` and
  `produced_from_context` to ADR-0008, recorded there under *Subsequent refinements*. **Unblocked D-07** and
  satisfied D-30's binding deferral condition.
- **D-18 (failure semantics, idempotency and ledger durability) is the next blocker** — chosen over D-07 by
  specification impact: D-18 blocks elements 10, 21 and 22; D-07 blocks element 16 alone.
- D-33 (external side-effect evidence durability) was discovered while amending ADR-0016. **Not covered by
  D-18**, which owns MNEXA's own ledger write path; D-33 is the dual-commit problem across an external
  boundary. Depends on D-18.
- **D-30 (credit attribution) is DEFERRED from v0** under four stated conditions — see its register entry. The
  binding one: D-12 must record decision→outcome linkage so a later standard has raw material.
- D-32 (trace authorization label propagation) minimum invariant is in force; mechanism registered not
  designed.
- D-29 (authorization and revocation temporal semantics) was discovered while amending ADR-0013; ADR-0013
  rule 8 states the minimum invariant in force, the mechanism is registered not designed.
- Tension **T-3** reassigned from D-13 to D-30.
- D-26 (episode lineage revision targeting policy) was discovered while amending ADR-0009 and recorded rather
  than decided.
- D-23 (supersession classification) and D-25 (episode split/merge) remain **deferred**: neither is required
  for a correct v0 spec.
- Remaining after D-05: D-04, D-06, D-07, D-10 … D-16, D-18 … D-20, D-23, D-25, D-26.

**Known blockers:** D-18 requires an accepted ADR before the experience-capture, idempotency and failure
elements may be written. Per `.claude/rules/decisions.md`, work does
not proceed past an unapproved D3 boundary. The v0 specification additionally awaits the remaining
domain-model decisions.

**Experiments in progress:** None. No benchmark contract exists.

**Next approved action:** Surface **D-18** (failure semantics, idempotency and ledger durability) as a
proposed ADR, on owner direction. Do not write MNEXA production code, the benchmark
harness, the v0 specification, or an implementation plan.
