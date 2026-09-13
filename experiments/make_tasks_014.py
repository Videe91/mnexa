from __future__ import annotations

import json

from pathlib import Path


from experiments.make_tasks_013 import (
    _family,
    _grader,
)


def _challenge_qualifier(
    family,
):
    operator = (
        family[
            "semantic_operator"
        ]
    )

    clause = (
        family[
            "semantic_clause"
        ]
    )

    if operator == "never":
        return {
            "type": "negation",
            "source_quote": "never",
        }

    if operator == "do_not":
        return {
            "type": "negation",
            "source_quote": "do not",
        }

    if operator == "only":
        return {
            "type": "scope",
            "source_quote": "only",
        }

    if operator == "exactly":
        return {
            "type": "scope",
            "source_quote": "exactly",
        }

    if operator == "at_least":
        return {
            "type": "scope",
            "source_quote": "at least",
        }

    if operator == "at_most":
        return {
            "type": "scope",
            "source_quote": "at most",
        }

    if operator == "unless":
        return {
            "type": "condition",
            "source_quote": "unless",
        }

    if operator == "when_if":

        lowered = (
            clause.lower()
        )

        if (
            lowered.startswith(
                "when "
            )
        ):
            token = "when"

        elif (
            lowered.startswith(
                "if "
            )
        ):
            token = "if"

        else:
            raise RuntimeError(
                "when_if family must "
                "start with when/if."
            )

        return {
            "type": "condition",
            "source_quote": token,
        }

    raise RuntimeError(
        f"Unsupported semantic operator: "
        f"{operator}"
    )


def _add_fallback_challenges(
    family,
):
    semantic_clause = (
        family[
            "semantic_clause"
        ]
    )

    qualifier = (
        _challenge_qualifier(
            family
        )
    )

    # Valid authoritative support,
    # deliberately invalid structured representation:
    #
    # qualifier physically overlaps the nucleus.
    recoverable = {
        "id": (
            f"{family['id']}-R1"
        ),
        "kind": "recoverable",
        "source_quote": (
            semantic_clause
        ),
        "candidate": {
            "source_quote": (
                semantic_clause
            ),
            "nucleus_quote": (
                semantic_clause
            ),
            "qualifiers": [
                qualifier
            ],
        },
    }

    fabricated_text = (
        "fabricated fallback instruction "
        +
        family[
            "code"
        ]
    )

    fabricated = {
        "id": (
            f"{family['id']}-U1"
        ),
        "kind": "fabricated",
        "source_quote": (
            fabricated_text
        ),
        "candidate": {
            "source_quote": (
                fabricated_text
            ),
            "nucleus_quote": (
                fabricated_text
            ),
            "qualifiers": [],
        },
    }

    nonauthoritative_text = (
        family[
            "candidate_decision"
        ]
    )

    nonauthoritative = {
        "id": (
            f"{family['id']}-U2"
        ),
        "kind": "nonauthoritative",
        "source_quote": (
            nonauthoritative_text
        ),
        "candidate": {
            "source_quote": (
                nonauthoritative_text
            ),
            "nucleus_quote": (
                nonauthoritative_text
            ),
            "qualifiers": [],
        },
    }

    return {
        **family,

        "fallback_challenges": {
            "recoverable": [
                recoverable
            ],
            "unsafe": [
                fabricated,
                nonauthoritative,
            ],
        },
    }


def _build_specs():
    return [

        # ============================================================
        # POLARITY — NEVER
        # ============================================================

        {
            "family_id": "umbra-pay-up-84",
            "system": "UmbraPay",
            "code": "UP-84",
            "candidate_decision": (
                "Reuse the old idempotency key."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait 14 seconds",
                "retry exactly once",
                "never reuse the old idempotency key",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "UmbraPay returns UP-84 again. "
                "State the rule governing reuse "
                "of the old idempotency key."
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
                    r"\bidempotency\b",
                ),
                (
                    r"\bkey\b",
                ),
            ),
            "operator_note": (
                "gateway pressure may be transient"
            ),
            "latency": 193,
        },

        {
            "family_id": "verdant-rpc-vr-42",
            "system": "VerdantRPC",
            "code": "VR-42",
            "candidate_decision": (
                "Reuse the stale correlation ID."
            ),
            "atoms": [
                "open a fresh channel",
                "send two heartbeat frames",
                "never reuse the stale correlation ID",
                "preserve the trace token",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "VerdantRPC returns VR-42. "
                "State the rule for the stale "
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
            ),
            "operator_note": (
                "transport jitter may exist"
            ),
            "latency": 227,
        },

        {
            "family_id": "willow-auth-wa-63",
            "system": "WillowAuth",
            "code": "WA-63",
            "candidate_decision": (
                "Accept the revoked credential."
            ),
            "atoms": [
                "refresh the trust snapshot",
                "preserve the request fingerprint",
                "never accept the revoked credential",
                "issue one fresh challenge",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "WillowAuth returns WA-63. "
                "State the rule for a revoked credential."
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
                    r"\brevoked\b",
                ),
            ),
            "operator_note": (
                "trust propagation may be delayed"
            ),
            "latency": 176,
        },

        # ============================================================
        # POLARITY — DO NOT
        # ============================================================

        {
            "family_id": "xenon-bus-xb-31",
            "system": "XenonBus",
            "code": "XB-31",
            "candidate_decision": (
                "Acknowledge the original event."
            ),
            "atoms": [
                "clone the current checkpoint",
                "mark the failed delivery stale",
                "do not acknowledge the original event",
                "restart from the cloned checkpoint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "XenonBus returns XB-31. "
                "State the acknowledgement rule "
                "for the original event."
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
                    r"\bevent\b",
                ),
            ),
            "operator_note": (
                "consumer lag may be elevated"
            ),
            "latency": 208,
        },

        {
            "family_id": "yarrow-db-yd-76",
            "system": "YarrowDB",
            "code": "YD-76",
            "candidate_decision": (
                "Write to the replica shard."
            ),
            "atoms": [
                "read the current leader epoch",
                "acquire the amber lock",
                "do not write to the replica shard",
                "release the lock after commit",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "YarrowDB returns YD-76. "
                "State the write rule for "
                "the replica shard."
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
                    r"\breplica\b",
                ),
                (
                    r"\bshard\b",
                ),
            ),
            "operator_note": (
                "replica synchronization may lag"
            ),
            "latency": 232,
        },

        # ============================================================
        # SCOPE — ONLY
        # ============================================================

        {
            "family_id": "zephyr-queue-zq-57",
            "system": "ZephyrQueue",
            "code": "ZQ-57",
            "candidate_decision": (
                "Move the job to any available lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job only to the bronze lane",
                "replay exactly twice",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "ZephyrQueue returns ZQ-57. "
                "State the permitted lane restriction."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bbronze\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker pressure may be elevated"
            ),
            "latency": 245,
        },

        {
            "family_id": "alder-store-as-88",
            "system": "AlderStore",
            "code": "AS-88",
            "candidate_decision": (
                "Finalize with any manifest header."
            ),
            "atoms": [
                "start a new upload session",
                "use 27 MiB chunks",
                "apply SHA-512 to every chunk",
                "finalize only with X-Alder-Final: sealed",
            ],
            "semantic_atom_index": 4,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "AlderStore returns AS-88. "
                "State the permitted finalization header."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"X-Alder-Final",
                ),
                (
                    r"\bsealed\b",
                ),
            ),
            "operator_note": (
                "storage load may be elevated"
            ),
            "latency": 271,
        },

        {
            "family_id": "birch-rpc-bi-26",
            "system": "BirchRPC",
            "code": "BI-26",
            "candidate_decision": (
                "Reuse the current channel."
            ),
            "atoms": [
                "send three heartbeat frames",
                "space them 185 ms apart",
                "open only a new channel",
                "preserve the request fingerprint",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "BirchRPC returns BI-26. "
                "State the channel restriction."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bnew\b",
                ),
                (
                    r"\bchannel\b",
                ),
            ),
            "operator_note": (
                "stream scheduling may be unstable"
            ),
            "latency": 297,
        },

        # ============================================================
        # CARDINALITY — EXACTLY
        # ============================================================

        {
            "family_id": "cypress-rpc-cr-53",
            "system": "CypressRPC",
            "code": "CR-53",
            "candidate_decision": (
                "Send five heartbeat frames."
            ),
            "atoms": [
                "send exactly four heartbeat frames",
                "space them 205 ms apart",
                "open a fresh channel",
                "preserve the correlation ID",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "CypressRPC returns CR-53. "
                "State the exact heartbeat requirement."
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
                    r"\bheartbeat\b",
                ),
            ),
            "operator_note": (
                "transport jitter may exist"
            ),
            "latency": 308,
        },

        {
            "family_id": "dune-queue-dq-64",
            "system": "DuneQueue",
            "code": "DQ-64",
            "candidate_decision": (
                "Retry until the operation succeeds."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job to the jade lane",
                "retry exactly three times",
                "preserve the dispatch ID",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "DuneQueue returns DQ-64. "
                "State the exact retry count."
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
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "queue load may be elevated"
            ),
            "latency": 249,
        },

        # ============================================================
        # CARDINALITY — AT LEAST
        # ============================================================

        {
            "family_id": "elm-store-es-39",
            "system": "ElmStore",
            "code": "ES-39",
            "candidate_decision": (
                "Retain one replica."
            ),
            "atoms": [
                "verify the manifest",
                "retain at least four replicas",
                "seal the newest replica",
                "record the replica epoch",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "ElmStore returns ES-39. "
                "State the minimum replica requirement."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bfour\b",
                    r"\b4\b",
                ),
                (
                    r"\breplica",
                ),
            ),
            "operator_note": (
                "replica lag may exist"
            ),
            "latency": 282,
        },

        {
            "family_id": "fir-pay-fp-71",
            "system": "FirPay",
            "code": "FP-71",
            "candidate_decision": (
                "Retry immediately."
            ),
            "atoms": [
                "refresh the recovery lease",
                "wait at least 15 seconds",
                "retry once",
                "preserve the payment fingerprint",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "FirPay returns FP-71. "
                "State the minimum wait duration."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b15\b",
                    r"\bfifteen\b",
                ),
                (
                    r"\bseconds?\b",
                ),
            ),
            "operator_note": (
                "gateway congestion may exist"
            ),
            "latency": 189,
        },

        # ============================================================
        # CARDINALITY — AT MOST
        # ============================================================

        {
            "family_id": "grove-api-ga-82",
            "system": "GroveAPI",
            "code": "GA-82",
            "candidate_decision": (
                "Retry six times."
            ),
            "atoms": [
                "refresh the session token",
                "retry at most three times",
                "preserve the request fingerprint",
                "close the stale connection",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "GroveAPI returns GA-82. "
                "State the maximum retry count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bthree\b",
                    r"\b3\b",
                ),
                (
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "upstream load may be elevated"
            ),
            "latency": 236,
        },

        {
            "family_id": "hazel-lock-hl-45",
            "system": "HazelLock",
            "code": "HL-45",
            "candidate_decision": (
                "Keep twelve pending leases."
            ),
            "atoms": [
                "refresh the lock table",
                "keep at most six pending leases",
                "expire stale leases",
                "preserve the newest owner token",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "HazelLock returns HL-45. "
                "State the maximum pending-lease count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bsix\b",
                    r"\b6\b",
                ),
                (
                    r"\blease",
                ),
            ),
            "operator_note": (
                "lock contention may exist"
            ),
            "latency": 224,
        },

        # ============================================================
        # CONDITION — UNLESS
        # ============================================================

        {
            "family_id": "iris-cdn-ic-68",
            "system": "IrisCDN",
            "code": "IC-68",
            "candidate_decision": (
                "Purge the shard immediately."
            ),
            "atoms": [
                "read the origin generation",
                (
                    "do not purge the shard unless "
                    "the origin generation changes"
                ),
                "issue one HEAD request",
                "preserve the edge generation ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "IrisCDN returns IC-68. "
                "State the condition under which "
                "the shard may be purged."
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
            "latency": 259,
        },

        {
            "family_id": "juniper-sign-js-54",
            "system": "JuniperSign",
            "code": "JS-54",
            "candidate_decision": (
                "Rotate the signing key immediately."
            ),
            "atoms": [
                "read the active epoch",
                (
                    "do not rotate the signing key unless "
                    "the active epoch advances"
                ),
                "preserve the key fingerprint",
                "record the new epoch after rotation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "JuniperSign returns JS-54. "
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
                "key-service delay may exist"
            ),
            "latency": 273,
        },

        # ============================================================
        # CONDITION — WHEN / IF
        # ============================================================

        {
            "family_id": "kelp-pay-kp-96",
            "system": "KelpPay",
            "code": "KP-96",
            "candidate_decision": (
                "Refresh the lease unconditionally."
            ),
            "atoms": [
                "when KP-96 occurs, refresh the recovery lease",
                "wait 16 seconds",
                "retry once",
                "preserve the payment fingerprint",
            ],
            "semantic_atom_index": 1,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the applicability rule "
                "for refreshing the KelpPay "
                "recovery lease."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bKP-96\b",
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
            "latency": 197,
        },

        {
            "family_id": "laurel-db-ld-73",
            "system": "LaurelDB",
            "code": "LD-73",
            "candidate_decision": (
                "Route every write to the leader."
            ),
            "atoms": [
                "read the shard mode",
                (
                    "if the shard is frozen, "
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
                "in LaurelDB."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bfrozen\b",
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
            "latency": 217,
        },

        {
            "family_id": "maple-parser-mp-65",
            "system": "MapleParser",
            "code": "MP-65",
            "candidate_decision": (
                "Always map state R to blocked."
            ),
            "atoms": [
                "read the schema generation",
                (
                    "when schema generation 9 appears, "
                    "map state R to blocked"
                ),
                "preserve the original payload",
                "validate after the mapping step",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the condition governing "
                "when state R should be mapped "
                "to blocked."
            ),
            "semantic_grader": _grader(
                (
                    r"\bwhen\b",
                    r"\bif\b",
                ),
                (
                    r"\bgeneration\s+9\b",
                ),
                (
                    r"\bR\b",
                ),
                (
                    r"\bblocked\b",
                ),
            ),
            "operator_note": (
                "a legacy producer may still be active"
            ),
            "latency": 153,
        },

        {
            "family_id": "north-cache-nc-37",
            "system": "NorthCache",
            "code": "NC-37",
            "candidate_decision": (
                "Always rebuild the local index."
            ),
            "atoms": [
                "read the manifest version",
                (
                    "if the manifest version changes, "
                    "rebuild the local index"
                ),
                "preserve the active cursor",
                "record the new manifest version",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "State the condition governing "
                "when NorthCache should rebuild "
                "the local index."
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
                    r"\bversion\b",
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
            "latency": 202,
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
            "seed-growth-014"
        ),

        "classification": (
            "exploratory-fresh-lossless-"
            "rejection-grounded-fallback-ablation"
        ),

        "hypothesis": (
            "When structured normalization fails but its exact "
            "historical support remains uniquely grounded and "
            "authoritative, retaining that support as unresolved "
            "grounded evidence will prevent knowledge loss without "
            "admitting fabricated or non-authoritative fallback data."
        ),

        "conditions": {
            "A": (
                "current all-or-nothing structured admission "
                "plus semantic-closed projection"
            ),

            "B": (
                "same repair proposal with support-first "
                "lossless grounded fallback plus "
                "semantic-closed projection"
            ),
        },

        "primary_metrics": [
            "semantic clause survival",
            "semantic task success",
            "recoverable structural challenge retention",
            "unsafe fallback challenge admission",
        ],

        "secondary_metrics": [
            "knowledge completeness",
            "fallback count",
            "memory word count",
        ],

        "control_invariants": [
            "all_source_evidence_equal",
            "all_initial_structured_proposals_equal",
            "all_repair_proposals_equal",
            "all_structured_admissions_equal",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_014.json"
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
