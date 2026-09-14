# Ledger 35 — ADR-0018 Ledger Failure Idempotency & Durability

**Date:** 2026-09-14  
**Status:** Completed & Validated  
**Classification:** Durable Persistence & Logical-Write Idempotency Gate  
**Principle:** *Identical logical write requests must produce identical commit outcomes; conflicting reuses of an idempotency key must fail atomically.*

---

## 1. Executive Summary

This slice implements ADR-0018 logical-write idempotency and durability across MNEXA's append-only commit ledger (`MnexaSeed`).

All write entry points (`event()`, `observe()`, `learn()`, `record_external_decision()`, `observe_outcome()`) now accept an optional `idempotency_key: str | None`. When supplied:
1. MNEXA computes a canonical SHA-256 fingerprint (`_canonical_request_sha256`) of caller-controlled logical intent (excluding generated UUIDs, commit sequence, or embeddings).
2. Executes inside a single atomic `BEGIN IMMEDIATE` SQLite transaction.
3. If `idempotency_key` is already committed with an identical request fingerprint, returns the original committed `Item` without advancing the watermark or duplicating commits.
4. If `idempotency_key` is reused for a different request payload, raises `IdempotencyConflict` without mutating database state.
5. If a transaction fails mid-flight, SQLite transaction rollback ensures neither `commits` nor `write_idempotency` records are exposed.

---

## 2. Invariants & Controls Verified

| Test Function | Verification Target | Result |
| :--- | :--- | :---: |
| `test_same_key_same_event_returns_original_commit` | Retrying identical key + payload returns original commit, watermark unchanged, 1 commit row. | PASSED |
| `test_metadata_key_order_does_not_change_request_identity` | Sorted metadata serialization produces identical request fingerprint. | PASSED |
| `test_same_key_different_request_is_rejected_without_mutation` | Conflicting request raises `IdempotencyConflict` with zero state mutation. | PASSED |
| `test_different_keys_preserve_identical_real_events` | Distinct idempotency keys produce separate commits even for identical text. | PASSED |
| `test_legacy_no_key_calls_remain_independent_writes` | `idempotency_key=None` preserves legacy behavior as independent writes. | PASSED |
| `test_retry_survives_database_restart` | Idempotency mapping persists across database restart. | PASSED |
| `test_failed_atomic_write_exposes_neither_half` | Transaction rollback on trigger failure leaves 0 commits and 0 idempotency records. | PASSED |
| `test_generated_interpretation_identity_is_stable_on_retry` | Retried `learn()` call returns original interpretation object ID and version. | PASSED |
| `test_observation_capture_can_be_retried_safely` | Retried `observe()` call returns original observation commit. | PASSED |

---

## 3. Full Test Suite Telemetry

- **New Test File:** `tests/test_ledger_idempotency.py` (9 tests)
- **Living Loop Test Suite:** 16 / 16 passed
- **Total Test Suite:** 501 / 501 passed in 0.49s
