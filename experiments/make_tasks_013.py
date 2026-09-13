from __future__ import annotations

import json
import re

from pathlib import Path


from experiments.make_tasks_008 import (
    build_raw_source,
)


def _regex_phrase(
    text: str,
):
    parts = (
        text.split()
    )

    return (
        r"\s+"
        .join(
            re.escape(
                part
            )
            for part
            in parts
        )
    )


def _atom(
    atom_id,
    text,
):
    return {
        "id": (
            atom_id
        ),
        "text": (
            text
        ),
        "task_pattern": (
            _regex_phrase(
                text
            )
        ),
    }


def _compound_span(
    text: str,
    left: str,
    right: str,
):
    start = (
        text.index(
            left
        )
    )

    end = (
        text.index(
            right
        )
        +
        len(
            right
        )
    )

    return (
        text[
            start:end
        ]
    )


def _grader(
    *groups,
    forbidden=None,
):
    return {
        "all_regex": [
            list(
                group
            )
            for group
            in groups
        ],
        "forbidden_regex": (
            list(
                forbidden
                or []
            )
        ),
    }


def _family(
    *,
    family_id,
    system,
    code,
    candidate_decision,
    atoms,
    semantic_atom_index,
    semantic_operator,
    semantic_dimension,
    transfer_prompt,
    semantic_grader,
    operator_note,
    latency,
):
    atomic_units = [
        _atom(
            f"A{index}",
            text,
        )

        for index, text
        in enumerate(
            atoms,
            start=1,
        )
    ]

    authoritative = (
        "; "
        .join(
            atoms
        )
        +
        "."
    )

    semantic_clause = (
        atoms[
            semantic_atom_index
            -
            1
        ]
    )

    challenge_1 = (
        _compound_span(
            authoritative,
            atoms[0],
            atoms[1],
        )
    )

    challenge_2 = (
        _compound_span(
            authoritative,
            atoms[2],
            atoms[3],
        )
    )

    raw_source = (
        build_raw_source(
            status=(
                f"{code} run status was FAIL."
            ),
            failed_decision=(
                candidate_decision
            ),
            authoritative_sentences=[
                authoritative
            ],
            operator_note=(
                operator_note
            ),
            diagnostic_metadata=(
                "Observed diagnostic latency "
                f"was {latency} ms."
            ),
        )
    )

    return {
        "id": (
            family_id
        ),

        "system": (
            system
        ),

        "code": (
            code
        ),

        "entities": [
            (
                "system:"
                +
                system.lower()
            ),
            (
                "code:"
                +
                code.lower()
            ),
        ],

        "experience": {
            "prompt": (
                f"{system} returns "
                f"{code}. "
                "What should the operator do?"
            )
        },

        "transfer": {
            "prompt": (
                transfer_prompt
            )
        },

        "candidate_decision": (
            candidate_decision
        ),

        "authoritative_text": (
            authoritative
        ),

        "raw_source": (
            raw_source
        ),

        "atomic_units": (
            atomic_units
        ),

        # Seed 012 repair prompt does not require hidden qualifiers for
        # Seed 013 scoring. Keep the field for compatibility.
        "expected_qualifiers": [],

        "structured_compound_challenges": [
            {
                "id": "C1",
                "text": (
                    challenge_1
                ),
                "covers_atom_ids": [
                    "A1",
                    "A2",
                ],
            },
            {
                "id": "C2",
                "text": (
                    challenge_2
                ),
                "covers_atom_ids": [
                    "A3",
                    "A4",
                ],
            },
        ],

        "semantic_atom_id": (
            f"A{semantic_atom_index}"
        ),

        "semantic_clause": (
            semantic_clause
        ),

        "semantic_operator": (
            semantic_operator
        ),

        "semantic_dimension": (
            semantic_dimension
        ),

        "semantic_grader": (
            semantic_grader
        ),

        "knowledge_grader": {
            "all_regex": [
                [
                    atom[
                        "task_pattern"
                    ]
                ]

                for atom
                in atomic_units
            ]
        },
    }


def _build_specs():
    return [

        # ============================================================
        # POLARITY — NEVER
        # ============================================================

        {
            "family_id": "aurorapay-ap-93",
            "system": "AuroraPay",
            "code": "AP-93",
            "candidate_decision": (
                "Reuse the prior nonce."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait 11 seconds",
                "retry exactly once",
                "never reuse the prior nonce",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "AuroraPay returns AP-93 again. "
                "State the rule governing reuse "
                "of the prior nonce."
            ),
            "semantic_grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                    r"\bmust\s+not\b",
                    r"\bshould\s+not\b",
                ),
                (
                    r"\breuse\b",
                ),
                (
                    r"\bnonce\b",
                ),
                forbidden=[
                    r"\b(?:should|must)\s+reuse\b",
                ],
            ),
            "operator_note": (
                "gateway congestion may be transient"
            ),
            "latency": 187,
        },

        {
            "family_id": "bronzrpc-br-47",
            "system": "BronzeRPC",
            "code": "BR-47",
            "candidate_decision": (
                "Reuse the previous correlation ID."
            ),
            "atoms": [
                "open a fresh channel",
                "send one probe frame",
                "never reuse the prior correlation ID",
                "preserve the trace token",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "BronzeRPC returns BR-47. "
                "State the rule for the prior "
                "correlation ID."
            ),
            "semantic_grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                    r"\bmust\s+not\b",
                ),
                (
                    r"\breuse\b",
                ),
                (
                    r"\bcorrelation\b",
                ),
                forbidden=[
                    (
                        r"\b(?:should|must)\s+reuse\b"
                    ),
                ],
            ),
            "operator_note": (
                "scheduler jitter may exist"
            ),
            "latency": 216,
        },

        {
            "family_id": "cedarauth-ca-62",
            "system": "CedarAuth",
            "code": "CA-62",
            "candidate_decision": (
                "Accept the expired token."
            ),
            "atoms": [
                "refresh the trust snapshot",
                "preserve the request fingerprint",
                "never accept the expired token",
                "issue one fresh challenge",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "CedarAuth returns CA-62. "
                "State the rule for an expired token."
            ),
            "semantic_grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                    r"\bmust\s+not\b",
                ),
                (
                    r"\baccept\b",
                ),
                (
                    r"\bexpired\b",
                ),
                (
                    r"\btoken\b",
                ),
                forbidden=[
                    (
                        r"\b(?:should|must)\s+accept\b"
                    ),
                ],
            ),
            "operator_note": (
                "clock skew may be transient"
            ),
            "latency": 173,
        },

        # ============================================================
        # POLARITY — DO NOT
        # ============================================================

        {
            "family_id": "deltabus-db-28",
            "system": "DeltaBus",
            "code": "DB-28",
            "candidate_decision": (
                "Acknowledge the original message."
            ),
            "atoms": [
                "clone the latest checkpoint",
                "mark the old delivery stale",
                "do not acknowledge the original message",
                "restart from the cloned checkpoint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "DeltaBus returns DB-28. "
                "State the acknowledgement rule "
                "for the original message."
            ),
            "semantic_grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bmust\s+not\b",
                    r"\bnever\b",
                ),
                (
                    r"\backnowledg",
                ),
                (
                    r"\boriginal\b",
                ),
                (
                    r"\bmessage\b",
                ),
                forbidden=[
                    (
                        r"\b(?:should|must)\s+"
                        r"acknowledge\b"
                    ),
                ],
            ),
            "operator_note": (
                "consumer lag may be elevated"
            ),
            "latency": 205,
        },

        {
            "family_id": "emberdb-ed-81",
            "system": "EmberDB",
            "code": "ED-81",
            "candidate_decision": (
                "Write directly to the standby shard."
            ),
            "atoms": [
                "read the current leader epoch",
                "acquire the violet lock",
                "do not write to the standby shard",
                "release the lock after commit",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "EmberDB returns ED-81. "
                "State the write rule for "
                "the standby shard."
            ),
            "semantic_grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bmust\s+not\b",
                    r"\bnever\b",
                ),
                (
                    r"\bwrite\b",
                ),
                (
                    r"\bstandby\b",
                ),
                (
                    r"\bshard\b",
                ),
                forbidden=[
                    (
                        r"\b(?:should|must)\s+write\b"
                    ),
                ],
            ),
            "operator_note": (
                "replication delay may exist"
            ),
            "latency": 228,
        },

        # ============================================================
        # SCOPE — ONLY
        # ============================================================

        {
            "family_id": "frostqueue-fq-56",
            "system": "FrostQueue",
            "code": "FQ-56",
            "candidate_decision": (
                "Move the job to any available lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job only to the cobalt lane",
                "replay exactly twice",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "FrostQueue returns FQ-56. "
                "State the lane restriction "
                "for moving the job."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bcobalt\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker saturation may exist"
            ),
            "latency": 239,
        },

        {
            "family_id": "granite-store-gs-72",
            "system": "GraniteStore",
            "code": "GS-72",
            "candidate_decision": (
                "Finalize with any completion header."
            ),
            "atoms": [
                "start a new upload session",
                "use 19 MiB chunks",
                "apply SHA-384 to every chunk",
                "finalize only with X-Granite-Final: strict",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "GraniteStore returns GS-72. "
                "State the permitted finalization "
                "header rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"X-Granite-Final",
                ),
                (
                    r"\bstrict\b",
                ),
            ),
            "operator_note": (
                "storage gateway load may be elevated"
            ),
            "latency": 263,
        },

        {
            "family_id": "harborrpc-hr-35",
            "system": "HarborRPC",
            "code": "HR-35",
            "candidate_decision": (
                "Reuse the existing channel."
            ),
            "atoms": [
                "send two heartbeat frames",
                "space them 175 ms apart",
                "open only a fresh channel",
                "preserve the trace ID",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "HarborRPC returns HR-35. "
                "State the channel restriction."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bfresh\b",
                ),
                (
                    r"\bchannel\b",
                ),
            ),
            "operator_note": (
                "stream jitter may exist"
            ),
            "latency": 292,
        },

        # ============================================================
        # CARDINALITY — EXACTLY
        # ============================================================

        {
            "family_id": "indigorpc-ir-64",
            "system": "IndigoRPC",
            "code": "IR-64",
            "candidate_decision": (
                "Send four heartbeat frames."
            ),
            "atoms": [
                "send exactly three heartbeat frames",
                "space them 210 ms apart",
                "open a fresh channel",
                "preserve the request ID",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "IndigoRPC returns IR-64. "
                "State the exact heartbeat-frame "
                "requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bexactly\b",
                ),
                (
                    r"\bthree\b",
                    r"\b3\b",
                ),
                (
                    r"\bheartbeat\b",
                ),
            ),
            "operator_note": (
                "scheduler jitter may exist"
            ),
            "latency": 304,
        },

        {
            "family_id": "jasperqueue-jq-49",
            "system": "JasperQueue",
            "code": "JQ-49",
            "candidate_decision": (
                "Replay until the job succeeds."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job to the silver lane",
                "retry exactly twice",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "JasperQueue returns JQ-49. "
                "State the exact retry count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bexactly\b",
                ),
                (
                    r"\btwice\b",
                    r"\b2\b",
                    r"\btwo\b",
                ),
                (
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "worker load may be elevated"
            ),
            "latency": 244,
        },

        {
            "family_id": "keystonecache-kc-77",
            "system": "KeystoneCache",
            "code": "KC-77",
            "candidate_decision": (
                "Retain two checkpoints."
            ),
            "atoms": [
                "refresh the manifest",
                "retain exactly four checkpoints",
                "seal the newest checkpoint",
                "drop stale temporary files",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "KeystoneCache returns KC-77. "
                "State the exact checkpoint "
                "retention requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bexactly\b",
                ),
                (
                    r"\bfour\b",
                    r"\b4\b",
                ),
                (
                    r"\bcheckpoint",
                ),
            ),
            "operator_note": (
                "cache pressure may be elevated"
            ),
            "latency": 196,
        },

        # ============================================================
        # CARDINALITY — AT LEAST
        # ============================================================

        {
            "family_id": "lattice-store-ls-31",
            "system": "LatticeStore",
            "code": "LS-31",
            "candidate_decision": (
                "Retain two replicas."
            ),
            "atoms": [
                "verify the manifest digest",
                "retain at least three replicas",
                "seal the latest replica",
                "record the replica epoch",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "LatticeStore returns LS-31. "
                "State the minimum replica "
                "requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bthree\b",
                    r"\b3\b",
                ),
                (
                    r"\breplica",
                ),
            ),
            "operator_note": (
                "replica lag may be transient"
            ),
            "latency": 277,
        },

        {
            "family_id": "mistralpay-mp-58",
            "system": "MistralPay",
            "code": "MP-58",
            "candidate_decision": (
                "Retry immediately."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait at least 12 seconds",
                "retry once",
                "preserve the payment fingerprint",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "MistralPay returns MP-58. "
                "State the minimum wait duration."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b12\b",
                    r"\btwelve\b",
                ),
                (
                    r"\bseconds?\b",
                ),
            ),
            "operator_note": (
                "gateway contention may exist"
            ),
            "latency": 184,
        },

        # ============================================================
        # CARDINALITY — AT MOST
        # ============================================================

        {
            "family_id": "nimbusapi-na-86",
            "system": "NimbusAPI",
            "code": "NA-86",
            "candidate_decision": (
                "Retry four times."
            ),
            "atoms": [
                "refresh the session token",
                "retry at most twice",
                "preserve the request fingerprint",
                "close the stale connection",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "NimbusAPI returns NA-86. "
                "State the maximum retry count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bno\s+more\s+than\b",
                    r"\bmaximum\b",
                ),
                (
                    r"\btwice\b",
                    r"\btwo\b",
                    r"\b2\b",
                ),
                (
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "upstream load may be elevated"
            ),
            "latency": 231,
        },

        {
            "family_id": "orbitlock-ol-43",
            "system": "OrbitLock",
            "code": "OL-43",
            "candidate_decision": (
                "Keep ten pending leases."
            ),
            "atoms": [
                "refresh the lock table",
                "keep at most five pending leases",
                "expire stale leases",
                "preserve the newest owner token",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "OrbitLock returns OL-43. "
                "State the maximum number of "
                "pending leases."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bno\s+more\s+than\b",
                    r"\bmaximum\b",
                ),
                (
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (
                    r"\blease",
                ),
            ),
            "operator_note": (
                "lock contention may exist"
            ),
            "latency": 221,
        },

        # ============================================================
        # CONDITION / EXCEPTION — UNLESS
        # ============================================================

        {
            "family_id": "pinecdn-pc-69",
            "system": "PineCDN",
            "code": "PC-69",
            "candidate_decision": (
                "Purge the cache immediately."
            ),
            "atoms": [
                "read the origin checksum",
                (
                    "do not purge the cache unless "
                    "the origin checksum changes"
                ),
                "issue one HEAD request",
                "preserve the edge generation ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "PineCDN returns PC-69. "
                "State the condition under which "
                "the cache may be purged."
            ),
            "semantic_grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (
                    r"\bchecksum\b",
                ),
                (
                    r"\bchang",
                ),
                (
                    r"\bpurge\b",
                ),
            ),
            "operator_note": (
                "origin latency may be elevated"
            ),
            "latency": 255,
        },

        {
            "family_id": "quartzsign-qs-52",
            "system": "QuartzSign",
            "code": "QS-52",
            "candidate_decision": (
                "Rotate the signing key immediately."
            ),
            "atoms": [
                "read the current epoch",
                (
                    "do not rotate the signing key unless "
                    "the epoch advances"
                ),
                "preserve the key fingerprint",
                "record the new epoch after rotation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "QuartzSign returns QS-52. "
                "State the condition required "
                "before rotating the signing key."
            ),
            "semantic_grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (
                    r"\bepoch\b",
                ),
                (
                    r"\badvance",
                ),
                (
                    r"\brotat",
                ),
            ),
            "operator_note": (
                "key service latency may exist"
            ),
            "latency": 269,
        },

        # ============================================================
        # CONDITION — WHEN / IF
        # ============================================================

        {
            "family_id": "ravenpay-rp-91",
            "system": "RavenPay",
            "code": "VX-91",
            "candidate_decision": (
                "Refresh the recovery lease immediately."
            ),
            "atoms": [
                "when VX-91 occurs, refresh the recovery lease",
                "wait 13 seconds",
                "retry once",
                "preserve the payment fingerprint",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the applicability rule for "
                "refreshing the recovery lease "
                "in RavenPay."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bVX-91\b",
                ),
                (
                    r"\brefresh\b",
                ),
                (
                    r"\blease\b",
                ),
            ),
            "operator_note": (
                "gateway congestion may exist"
            ),
            "latency": 191,
        },

        {
            "family_id": "saffrondb-sd-74",
            "system": "SaffronDB",
            "code": "SD-74",
            "candidate_decision": (
                "Route all writes to the leader."
            ),
            "atoms": [
                "read the shard mode",
                (
                    "if the shard is read-only, "
                    "route writes to the leader"
                ),
                "preserve the transaction ID",
                "record the leader epoch",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the applicability rule "
                "for routing writes to the leader "
                "in SaffronDB."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bread[- ]only\b",
                ),
                (
                    r"\broute\b",
                ),
                (
                    r"\bleader\b",
                ),
            ),
            "operator_note": (
                "replication lag may exist"
            ),
            "latency": 213,
        },

        {
            "family_id": "thistleparser-tp-67",
            "system": "ThistleParser",
            "code": "TP-67",
            "candidate_decision": (
                "Always map state Q to blocked."
            ),
            "atoms": [
                "read the schema version",
                (
                    "when schema version 7 appears, "
                    "map state Q to blocked"
                ),
                "preserve the original payload",
                "validate after the mapping step",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the condition governing "
                "when state Q should be mapped "
                "to blocked."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bversion\s+7\b",
                ),
                (
                    r"\bQ\b",
                ),
                (
                    r"\bblocked\b",
                ),
            ),
            "operator_note": (
                "a legacy producer may still be active"
            ),
            "latency": 149,
        },
    ]


def build_taskset():
    specs = (
        _build_specs()
    )

    families = [
        _family(
            **spec
        )

        for spec
        in specs
    ]

    return {
        "experiment": (
            "seed-growth-013"
        ),

        "classification": (
            "exploratory-fresh-semantic-"
            "closure-projection-ablation"
        ),

        "hypothesis": (
            "When the structured nucleus is used only as a retrieval "
            "handle and the exact authoritative support span is used "
            "as the model-visible semantic claim payload, MNEXA will "
            "reduce polarity, scope, cardinality, and condition loss "
            "without weakening source ancestry or claim support."
        ),

        "conditions": {
            "A": (
                "same repaired propositions; "
                "nucleus used as claim payload"
            ),
            "B": (
                "same repaired propositions; "
                "nucleus used only as retrieval handle; "
                "exact support span used as semantic payload"
            ),
        },

        "primary_metrics": [
            "semantic task success",
            "polarity violations",
            "scope-loss violations",
            "cardinality-loss violations",
            "condition-loss violations",
            "semantic clause visibility",
        ],

        "secondary_metrics": [
            "knowledge completeness",
            "memory word count",
            "unsupported claims",
        ],

        "control_invariants": [
            "all_source_evidence_equal",
            "all_repaired_structured_propositions_equal",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_013.json"
    )

    payload = (
        build_taskset()
    )

    output.write_text(
        json.dumps(
            payload,
            indent=2,
        )
        +
        "\n"
    )

    print(
        "Wrote "
        f"{len(payload['families'])} "
        f"families to "
        f"{output}"
    )


if __name__ == "__main__":
    main()
