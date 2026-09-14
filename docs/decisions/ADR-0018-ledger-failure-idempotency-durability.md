---
title: ADR-0018 — Ledger Failure Idempotency & Durability
status: accepted
date: 2026-09-14
---

# ADR-0018 — Ledger Failure Idempotency & Durability

**Approval:** accepted by owner 2026-09-14 after review of the explicit logical-write idempotency-key design.

## Context

MNEXA is an append-only persistent intelligence substrate backed by SQLite commit logs.
Network retries, worker restarts, or concurrent runtime calls may submit identical logical write requests (observations, decisions, or learned interpretations) multiple times.

Without explicit logical-write idempotency keys:
1. Duplicate logical commits pollute the event stream.
2. Watermarks increment unnecessarily on duplicate submissions.
3. Network retries produce duplicate memory records.

## Decision

1. **Explicit Logical Write Idempotency Keys**: `event()`, `observe()`, `learn()`, `record_external_decision()` accept an optional `idempotency_key: str | None`.
2. **Request Fingerprinting**: When an `idempotency_key` is provided, MNEXA computes a canonical SHA-256 fingerprint (`_canonical_request_sha256`) of the write request (kind, text, entities, refs, metadata).
3. **Atomic Transaction**: The write commit and `write_idempotency` mapping are inserted atomically within a single `BEGIN IMMEDIATE` SQLite transaction.
4. **Idempotency Guarantee**:
   - If `idempotency_key` has not been seen: insert commit and record idempotency key.
   - If `idempotency_key` has been seen with identical request fingerprint: return original commit record without advancing watermark or creating duplicate commits.
   - If `idempotency_key` has been seen with a different request payload: raise `IdempotencyConflict` exception without mutating database state or advancing watermark.
5. **No Key Provided**: Writes without an `idempotency_key` remain independent, distinct commits.
