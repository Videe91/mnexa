from __future__ import annotations

import json

from pathlib import Path


from experiments.make_tasks_013 import (
    _family,
    _grader,
)

from experiments.make_tasks_014 import (
    _add_fallback_challenges,
)


def _build_specs():
    return [

        # ============================================================
        # NEVER
        # ============================================================

        {
            "family_id": "opal-pay-op-85",
            "system": "OpalPay",
            "code": "OP-85",
            "candidate_decision": (
                "Reuse the previous settlement nonce."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait 17 seconds",
                "retry exactly once",
                "never reuse the previous settlement nonce",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "OpalPay returns OP-85. "
                "State the rule for reuse of the "
                "previous settlement nonce."
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
                    r"\bsettlement\b",
                ),
                (
                    r"\bnonce\b",
                ),
            ),
            "operator_note": (
                "gateway contention may be temporary"
            ),
            "latency": 201,
        },

        {
            "family_id": "pearl-rpc-pr-46",
            "system": "PearlRPC",
            "code": "PR-46",
            "candidate_decision": (
                "Reuse the old request token."
            ),
            "atoms": [
                "open a fresh transport channel",
                "send two probe frames",
                "never reuse the old request token",
                "preserve the trace fingerprint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "PearlRPC returns PR-46. "
                "State the rule for the old request token."
            ),
            "semantic_grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (
                    r"\breuse\b",
                ),
                (
                    r"\brequest\b",
                ),
                (
                    r"\btoken\b",
                ),
            ),
            "operator_note": (
                "network jitter may exist"
            ),
            "latency": 229,
        },

        {
            "family_id": "quince-auth-qa-61",
            "system": "QuinceAuth",
            "code": "QA-61",
            "candidate_decision": (
                "Accept the retired credential."
            ),
            "atoms": [
                "refresh the trust snapshot",
                "preserve the request fingerprint",
                "never accept the retired credential",
                "issue one new challenge",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "QuinceAuth returns QA-61. "
                "State the rule for a retired credential."
            ),
            "semantic_grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (
                    r"\baccept\b",
                ),
                (
                    r"\bretired\b",
                ),
                (
                    r"\bcredential\b",
                ),
            ),
            "operator_note": (
                "trust replication may lag"
            ),
            "latency": 181,
        },

        # ============================================================
        # DO NOT
        # ============================================================

        {
            "family_id": "reed-bus-rb-34",
            "system": "ReedBus",
            "code": "RB-34",
            "candidate_decision": (
                "Acknowledge the failed envelope."
            ),
            "atoms": [
                "clone the latest checkpoint",
                "mark the previous delivery stale",
                "do not acknowledge the failed envelope",
                "restart from the cloned checkpoint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "ReedBus returns RB-34. "
                "State the acknowledgement rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                    r"\bmust\s+not\b",
                ),
                (
                    r"\backnowledg",
                ),
                (
                    r"\bfailed\b",
                ),
                (
                    r"\benvelope\b",
                ),
            ),
            "operator_note": (
                "consumer backlog may be elevated"
            ),
            "latency": 214,
        },

        {
            "family_id": "sable-db-sd-79",
            "system": "SableDB",
            "code": "SD-79",
            "candidate_decision": (
                "Write directly to the passive replica."
            ),
            "atoms": [
                "read the current leader generation",
                "acquire the copper lock",
                "do not write to the passive replica",
                "release the lock after commit",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "SableDB returns SD-79. "
                "State the write rule for the passive replica."
            ),
            "semantic_grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (
                    r"\bwrite\b",
                ),
                (
                    r"\bpassive\b",
                ),
                (
                    r"\breplica\b",
                ),
            ),
            "operator_note": (
                "replication lag may be elevated"
            ),
            "latency": 238,
        },

        # ============================================================
        # ONLY
        # ============================================================

        {
            "family_id": "topaz-queue-tq-59",
            "system": "TopazQueue",
            "code": "TQ-59",
            "candidate_decision": (
                "Move the task to any available lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the task only to the violet lane",
                "retry exactly twice",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "TopazQueue returns TQ-59. "
                "State the permitted lane restriction."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bviolet\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker saturation may exist"
            ),
            "latency": 247,
        },

        {
            "family_id": "umber-store-us-89",
            "system": "UmberStore",
            "code": "US-89",
            "candidate_decision": (
                "Finalize using any completion header."
            ),
            "atoms": [
                "start a fresh upload session",
                "use 31 MiB chunks",
                "apply SHA-384 to every chunk",
                "finalize only with X-Umber-Final: locked",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "UmberStore returns US-89. "
                "State the permitted finalization header."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"X-Umber-Final",
                ),
                (
                    r"\blocked\b",
                ),
            ),
            "operator_note": (
                "storage load may be elevated"
            ),
            "latency": 279,
        },

        {
            "family_id": "violet-rpc-vr-27",
            "system": "VioletRPC",
            "code": "VR-27",
            "candidate_decision": (
                "Reuse the existing transport channel."
            ),
            "atoms": [
                "send three heartbeat frames",
                "space them 190 ms apart",
                "open only a fresh transport channel",
                "preserve the request fingerprint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "VioletRPC returns VR-27. "
                "State the transport-channel restriction."
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
                "stream scheduling may be unstable"
            ),
            "latency": 301,
        },

        # ============================================================
        # EXACTLY
        # ============================================================

        {
            "family_id": "walnut-rpc-wr-55",
            "system": "WalnutRPC",
            "code": "WR-55",
            "candidate_decision": (
                "Send six heartbeat frames."
            ),
            "atoms": [
                "send exactly five heartbeat frames",
                "space them 215 ms apart",
                "open a new channel",
                "preserve the correlation fingerprint",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "WalnutRPC returns WR-55. "
                "State the exact heartbeat-frame requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bexactly\b",
                ),
                (
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (
                    r"\bheartbeat\b",
                ),
            ),
            "operator_note": (
                "transport jitter may be present"
            ),
            "latency": 311,
        },

        {
            "family_id": "xylem-queue-xq-66",
            "system": "XylemQueue",
            "code": "XQ-66",
            "candidate_decision": (
                "Retry until the operation succeeds."
            ),
            "atoms": [
                "request a new checkpoint",
                "move the task to the coral lane",
                "retry exactly four times",
                "preserve the original dispatch ID",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "XylemQueue returns XQ-66. "
                "State the exact retry count."
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
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "queue pressure may be elevated"
            ),
            "latency": 253,
        },

        # ============================================================
        # AT LEAST
        # ============================================================

        {
            "family_id": "yucca-store-ys-41",
            "system": "YuccaStore",
            "code": "YS-41",
            "candidate_decision": (
                "Retain two replicas."
            ),
            "atoms": [
                "verify the manifest digest",
                "retain at least five replicas",
                "seal the newest replica",
                "record the replica generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "YuccaStore returns YS-41. "
                "State the minimum replica requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (
                    r"\breplica",
                ),
            ),
            "operator_note": (
                "replica synchronization may lag"
            ),
            "latency": 286,
        },

        {
            "family_id": "zenith-pay-zp-72",
            "system": "ZenithPay",
            "code": "ZP-72",
            "candidate_decision": (
                "Retry immediately."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait at least 18 seconds",
                "retry once",
                "preserve the settlement fingerprint",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "ZenithPay returns ZP-72. "
                "State the minimum wait duration."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b18\b",
                    r"\beighteen\b",
                ),
                (
                    r"\bseconds?\b",
                ),
            ),
            "operator_note": (
                "gateway congestion may be elevated"
            ),
            "latency": 194,
        },

        # ============================================================
        # AT MOST
        # ============================================================

        {
            "family_id": "acorn-api-aa-83",
            "system": "AcornAPI",
            "code": "AA-83",
            "candidate_decision": (
                "Retry seven times."
            ),
            "atoms": [
                "refresh the session token",
                "retry at most four times",
                "preserve the request fingerprint",
                "close the stale connection",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "AcornAPI returns AA-83. "
                "State the maximum retry count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bfour\b",
                    r"\b4\b",
                ),
                (
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "upstream pressure may be elevated"
            ),
            "latency": 241,
        },

        {
            "family_id": "briar-lock-bl-48",
            "system": "BriarLock",
            "code": "BL-48",
            "candidate_decision": (
                "Keep fifteen pending leases."
            ),
            "atoms": [
                "refresh the lock table",
                "keep at most seven pending leases",
                "expire stale leases",
                "preserve the newest owner token",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "BriarLock returns BL-48. "
                "State the maximum pending-lease count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bseven\b",
                    r"\b7\b",
                ),
                (
                    r"\blease",
                ),
            ),
            "operator_note": (
                "lock contention may exist"
            ),
            "latency": 226,
        },

        # ============================================================
        # UNLESS
        # ============================================================

        {
            "family_id": "coral-cdn-cc-69",
            "system": "CoralCDN",
            "code": "CC-69",
            "candidate_decision": (
                "Purge the edge shard immediately."
            ),
            "atoms": [
                "read the origin generation",
                (
                    "do not purge the edge shard unless "
                    "the origin generation changes"
                ),
                "issue one HEAD request",
                "preserve the edge generation ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "CoralCDN returns CC-69. "
                "State the condition under which "
                "the edge shard may be purged."
            ),
            "semantic_grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (
                    r"\bgeneration\b",
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
            "latency": 264,
        },

        {
            "family_id": "drift-sign-ds-56",
            "system": "DriftSign",
            "code": "DS-56",
            "candidate_decision": (
                "Rotate the signing key immediately."
            ),
            "atoms": [
                "read the active generation",
                (
                    "do not rotate the signing key unless "
                    "the active generation advances"
                ),
                "preserve the signing fingerprint",
                "record the new generation after rotation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "DriftSign returns DS-56. "
                "State the condition required before key rotation."
            ),
            "semantic_grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (
                    r"\bgeneration\b",
                ),
                (
                    r"\badvance",
                ),
                (
                    r"\brotat",
                ),
            ),
            "operator_note": (
                "key-service latency may exist"
            ),
            "latency": 276,
        },

        # ============================================================
        # WHEN / IF
        # ============================================================

        {
            "family_id": "elm-pay-ep-97",
            "system": "ElmPay",
            "code": "EP-97",
            "candidate_decision": (
                "Refresh the recovery lease unconditionally."
            ),
            "atoms": [
                "when EP-97 occurs, refresh the recovery lease",
                "wait 19 seconds",
                "retry once",
                "preserve the settlement fingerprint",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the applicability rule for "
                "refreshing the ElmPay recovery lease."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bEP-97\b",
                ),
                (
                    r"\brefresh\b",
                ),
                (
                    r"\blease\b",
                ),
            ),
            "operator_note": (
                "gateway pressure may exist"
            ),
            "latency": 203,
        },

        {
            "family_id": "fjord-db-fd-75",
            "system": "FjordDB",
            "code": "FD-75",
            "candidate_decision": (
                "Route every write to the leader."
            ),
            "atoms": [
                "read the shard state",
                (
                    "if the shard is suspended, "
                    "route writes to the leader"
                ),
                "preserve the transaction fingerprint",
                "record the leader generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the applicability rule for routing "
                "writes to the FjordDB leader."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bsuspended\b",
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
            "latency": 219,
        },

        {
            "family_id": "garnet-parser-gp-67",
            "system": "GarnetParser",
            "code": "GP-67",
            "candidate_decision": (
                "Always map state S to blocked."
            ),
            "atoms": [
                "read the schema generation",
                (
                    "when schema generation 11 appears, "
                    "map state S to blocked"
                ),
                "preserve the original payload",
                "validate after the mapping step",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the condition governing when "
                "state S should be mapped to blocked."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bgeneration\s+11\b",
                ),
                (
                    r"\bS\b",
                ),
                (
                    r"\bblocked\b",
                ),
            ),
            "operator_note": (
                "a legacy producer may remain active"
            ),
            "latency": 157,
        },

        {
            "family_id": "hemlock-cache-hc-38",
            "system": "HemlockCache",
            "code": "HC-38",
            "candidate_decision": (
                "Always rebuild the local index."
            ),
            "atoms": [
                "read the manifest generation",
                (
                    "if the manifest generation changes, "
                    "rebuild the local index"
                ),
                "preserve the active cursor",
                "record the new manifest generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the condition governing when "
                "HemlockCache should rebuild its local index."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bmanifest\b",
                ),
                (
                    r"\bgeneration\b",
                ),
                (
                    r"\bchang",
                ),
                (
                    r"\brebuild\b",
                ),
            ),
            "operator_note": (
                "manifest propagation may be delayed"
            ),
            "latency": 207,
        },
    ]


def build_taskset():
    families = [
        _add_fallback_challenges(
            _family(
                **spec
            )
        )

        for spec
        in _build_specs()
    ]

    return {
        "experiment": (
            "seed-growth-015"
        ),

        "classification": (
            "exploratory-fresh-semantic-"
            "closure-compaction-ablation"
        ),

        "hypothesis": (
            "Representing each unique grounded support span once "
            "and referencing it from multiple retrieval handles "
            "will preserve the semantic correctness and closed-world "
            "safety of lossless semantic memory while reducing "
            "model-visible memory size."
        ),

        "conditions": {
            "A": (
                "seed 014 lossless semantic memory "
                "with repeated support rendering"
            ),

            "B": (
                "same structure and fallback records "
                "with unique exact evidence index "
                "and lightweight references"
            ),
        },

        "primary_metrics": [
            "semantic task success",
            "semantic violations",
            "exact semantic clause visibility",
            "mean model-visible memory words",
        ],

        "secondary_metrics": [
            "complete lessons",
            "duplicate support occurrences removed",
            "unique support count",
            "unsupported claims",
        ],

        "control_invariants": [
            "all_source_evidence_equal",
            "all_initial_structured_proposals_equal",
            "all_repair_proposals_equal",
            "all_structured_admissions_equal",
            "all_fallback_records_equal",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_015.json"
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
        "families to "
        f"{output}"
    )


if __name__ == "__main__":
    main()
