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
            "family_id": "lunar-pay-lp-88",
            "system": "LunarPay",
            "code": "LP-88",
            "candidate_decision": (
                "Reuse the previous authorization nonce."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait 21 seconds",
                "retry exactly once",
                "never reuse the previous authorization nonce",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "LunarPay returns LP-88. "
                "State the rule governing reuse of the "
                "previous authorization nonce."
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
                    r"\bauthorization\b",
                ),
                (
                    r"\bnonce\b",
                ),
            ),
            "operator_note": (
                "gateway pressure may be temporary"
            ),
            "latency": 204,
        },

        {
            "family_id": "meridian-rpc-mr-47",
            "system": "MeridianRPC",
            "code": "MR-47",
            "candidate_decision": (
                "Reuse the retired correlation token."
            ),
            "atoms": [
                "open a fresh transport channel",
                "send three probe frames",
                "never reuse the retired correlation token",
                "preserve the trace fingerprint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "MeridianRPC returns MR-47. "
                "State the rule for the retired correlation token."
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
                    r"\bcorrelation\b",
                ),
                (
                    r"\btoken\b",
                ),
            ),
            "operator_note": (
                "network jitter may exist"
            ),
            "latency": 233,
        },

        {
            "family_id": "nova-auth-na-62",
            "system": "NovaAuth",
            "code": "NA-62",
            "candidate_decision": (
                "Accept the superseded credential."
            ),
            "atoms": [
                "refresh the trust snapshot",
                "preserve the request fingerprint",
                "never accept the superseded credential",
                "issue one fresh challenge",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "NovaAuth returns NA-62. "
                "State the rule for a superseded credential."
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
                    r"\bsuperseded\b",
                ),
                (
                    r"\bcredential\b",
                ),
            ),
            "operator_note": (
                "trust propagation may be delayed"
            ),
            "latency": 183,
        },

        # ============================================================
        # DO NOT
        # ============================================================

        {
            "family_id": "onyx-bus-ob-35",
            "system": "OnyxBus",
            "code": "OB-35",
            "candidate_decision": (
                "Acknowledge the rejected envelope."
            ),
            "atoms": [
                "clone the newest checkpoint",
                "mark the rejected delivery stale",
                "do not acknowledge the rejected envelope",
                "restart from the cloned checkpoint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "OnyxBus returns OB-35. "
                "State the acknowledgement rule "
                "for the rejected envelope."
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
                    r"\brejected\b",
                ),
                (
                    r"\benvelope\b",
                ),
            ),
            "operator_note": (
                "consumer backlog may be elevated"
            ),
            "latency": 216,
        },

        {
            "family_id": "prairie-db-pd-81",
            "system": "PrairieDB",
            "code": "PD-81",
            "candidate_decision": (
                "Write directly to the passive shard."
            ),
            "atoms": [
                "read the active leader generation",
                "acquire the silver lock",
                "do not write to the passive shard",
                "release the lock after commit",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "PrairieDB returns PD-81. "
                "State the write rule for the passive shard."
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
                    r"\bshard\b",
                ),
            ),
            "operator_note": (
                "replication lag may be elevated"
            ),
            "latency": 242,
        },

        # ============================================================
        # ONLY
        # ============================================================

        {
            "family_id": "quartz-queue-qq-60",
            "system": "QuartzQueue",
            "code": "QQ-60",
            "candidate_decision": (
                "Move the task to any available lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the task only to the indigo lane",
                "retry exactly twice",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "QuartzQueue returns QQ-60. "
                "State the permitted lane restriction."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bindigo\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker saturation may exist"
            ),
            "latency": 251,
        },

        {
            "family_id": "river-store-rs-90",
            "system": "RiverStore",
            "code": "RS-90",
            "candidate_decision": (
                "Finalize with any completion header."
            ),
            "atoms": [
                "start a fresh upload session",
                "use 33 MiB chunks",
                "apply SHA-512 to every chunk",
                "finalize only with X-River-Final: sealed",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "RiverStore returns RS-90. "
                "State the permitted finalization header rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"X-River-Final",
                ),
                (
                    r"\bsealed\b",
                ),
            ),
            "operator_note": (
                "storage pressure may be elevated"
            ),
            "latency": 283,
        },

        {
            "family_id": "solstice-rpc-sr-28",
            "system": "SolsticeRPC",
            "code": "SR-28",
            "candidate_decision": (
                "Reuse the current transport channel."
            ),
            "atoms": [
                "send four heartbeat frames",
                "space them 195 ms apart",
                "open only a fresh transport channel",
                "preserve the request fingerprint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "SolsticeRPC returns SR-28. "
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
            "latency": 306,
        },

        # ============================================================
        # EXACTLY
        # ============================================================

        {
            "family_id": "tundra-rpc-tr-56",
            "system": "TundraRPC",
            "code": "TR-56",
            "candidate_decision": (
                "Send seven heartbeat frames."
            ),
            "atoms": [
                "send exactly six heartbeat frames",
                "space them 225 ms apart",
                "open a new channel",
                "preserve the correlation fingerprint",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "TundraRPC returns TR-56. "
                "State the exact heartbeat-frame requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bexactly\b",
                ),
                (
                    r"\bsix\b",
                    r"\b6\b",
                ),
                (
                    r"\bheartbeat\b",
                ),
            ),
            "operator_note": (
                "transport jitter may be present"
            ),
            "latency": 315,
        },

        {
            "family_id": "ultraviolet-queue-uq-67",
            "system": "UltravioletQueue",
            "code": "UQ-67",
            "candidate_decision": (
                "Retry until the operation succeeds."
            ),
            "atoms": [
                "request a new checkpoint",
                "move the task to the amber lane",
                "retry exactly five times",
                "preserve the original dispatch ID",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "UltravioletQueue returns UQ-67. "
                "State the exact retry count."
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
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "queue pressure may be elevated"
            ),
            "latency": 258,
        },

        # ============================================================
        # AT LEAST
        # ============================================================

        {
            "family_id": "vale-store-vs-42",
            "system": "ValeStore",
            "code": "VS-42",
            "candidate_decision": (
                "Retain two replicas."
            ),
            "atoms": [
                "verify the manifest digest",
                "retain at least six replicas",
                "seal the newest replica",
                "record the replica generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "ValeStore returns VS-42. "
                "State the minimum replica requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bsix\b",
                    r"\b6\b",
                ),
                (
                    r"\breplica",
                ),
            ),
            "operator_note": (
                "replica synchronization may lag"
            ),
            "latency": 291,
        },

        {
            "family_id": "wren-pay-wp-73",
            "system": "WrenPay",
            "code": "WP-73",
            "candidate_decision": (
                "Retry immediately."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait at least 22 seconds",
                "retry once",
                "preserve the settlement fingerprint",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "WrenPay returns WP-73. "
                "State the minimum wait duration."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b22\b",
                    r"\btwenty[- ]two\b",
                ),
                (
                    r"\bseconds?\b",
                ),
            ),
            "operator_note": (
                "gateway congestion may be elevated"
            ),
            "latency": 198,
        },

        # ============================================================
        # AT MOST
        # ============================================================

        {
            "family_id": "xenial-api-xa-84",
            "system": "XenialAPI",
            "code": "XA-84",
            "candidate_decision": (
                "Retry eight times."
            ),
            "atoms": [
                "refresh the session token",
                "retry at most five times",
                "preserve the request fingerprint",
                "close the stale connection",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "XenialAPI returns XA-84. "
                "State the maximum retry count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "upstream pressure may be elevated"
            ),
            "latency": 246,
        },

        {
            "family_id": "yew-lock-yl-49",
            "system": "YewLock",
            "code": "YL-49",
            "candidate_decision": (
                "Keep sixteen pending leases."
            ),
            "atoms": [
                "refresh the lock table",
                "keep at most eight pending leases",
                "expire stale leases",
                "preserve the newest owner token",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "YewLock returns YL-49. "
                "State the maximum pending-lease count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\beight\b",
                    r"\b8\b",
                ),
                (
                    r"\blease",
                ),
            ),
            "operator_note": (
                "lock contention may exist"
            ),
            "latency": 231,
        },

        # ============================================================
        # UNLESS
        # ============================================================

        {
            "family_id": "zinnia-cdn-zc-70",
            "system": "ZinniaCDN",
            "code": "ZC-70",
            "candidate_decision": (
                "Purge the edge partition immediately."
            ),
            "atoms": [
                "read the origin generation",
                (
                    "do not purge the edge partition unless "
                    "the origin generation changes"
                ),
                "issue one HEAD request",
                "preserve the edge generation ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "ZinniaCDN returns ZC-70. "
                "State the condition under which "
                "the edge partition may be purged."
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
            "latency": 268,
        },

        {
            "family_id": "alpine-sign-as-57",
            "system": "AlpineSign",
            "code": "AS-57",
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
                "AlpineSign returns AS-57. "
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
            "latency": 281,
        },

        # ============================================================
        # WHEN / IF
        # ============================================================

        {
            "family_id": "beacon-pay-bp-98",
            "system": "BeaconPay",
            "code": "BP-98",
            "candidate_decision": (
                "Refresh the recovery lease unconditionally."
            ),
            "atoms": [
                "when BP-98 occurs, refresh the recovery lease",
                "wait 23 seconds",
                "retry once",
                "preserve the settlement fingerprint",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the applicability rule for refreshing "
                "the BeaconPay recovery lease."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bBP-98\b",
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
            "latency": 209,
        },

        {
            "family_id": "cascade-db-cd-76",
            "system": "CascadeDB",
            "code": "CD-76",
            "candidate_decision": (
                "Route every write to the leader."
            ),
            "atoms": [
                "read the shard state",
                (
                    "if the shard is quarantined, "
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
                "writes to the CascadeDB leader."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bquarantined\b",
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
            "latency": 223,
        },

        {
            "family_id": "delta-parser-dp-68",
            "system": "DeltaParser",
            "code": "DP-68",
            "candidate_decision": (
                "Always map state T to blocked."
            ),
            "atoms": [
                "read the schema generation",
                (
                    "when schema generation 13 appears, "
                    "map state T to blocked"
                ),
                "preserve the original payload",
                "validate after the mapping step",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the condition governing when "
                "state T should be mapped to blocked."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bgeneration\s+13\b",
                ),
                (
                    r"\bT\b",
                ),
                (
                    r"\bblocked\b",
                ),
            ),
            "operator_note": (
                "a legacy producer may remain active"
            ),
            "latency": 161,
        },

        {
            "family_id": "ember-cache-ec-39",
            "system": "EmberCache",
            "code": "EC-39",
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
                "EmberCache should rebuild its local index."
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
            "latency": 211,
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
            "seed-growth-016"
        ),

        "classification": (
            "exploratory-fresh-compact-"
            "semantic-stability-ablation"
        ),

        "transfer_attempts_per_condition": 3,

        "hypothesis": (
            "The semantic difference observed in Seed 015 is "
            "primarily stochastic rather than a systematic failure "
            "of compact semantic memory. Across repeated independent "
            "transfer calls, compact memory should retain comparable "
            "per-call, majority-family, and operator-level semantic "
            "stability while preserving its context reduction."
        ),

        "conditions": {
            "A": (
                "verbose Seed 014 lossless semantic memory"
            ),

            "B": (
                "compact Seed 015 evidence-index memory"
            ),
        },

        "primary_metrics": [
            "per-call semantic pass rate",
            "majority-family semantic success",
            "unanimous-family semantic success",
            "operator-specific semantic stability",
        ],

        "secondary_metrics": [
            "semantic violations",
            "exact semantic clause visibility",
            "complete lessons",
            "memory words",
            "unsupported claims",
        ],

        "control_invariants": [
            "all_source_evidence_equal",
            "all_initial_structured_proposals_equal",
            "all_repair_proposals_equal",
            "all_structured_admissions_equal",
            "all_fallback_records_equal",
            "replicate lesson equality",
            "replicate memory-size equality",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_016.json"
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
