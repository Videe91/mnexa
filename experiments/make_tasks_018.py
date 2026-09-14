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


def _specs():
    return [

        # ============================================================
        # RETRY POLICY
        # ============================================================

        {
            "interference_cluster": "retry-policy",
            "family_id": "birch-api-br-101",
            "system": "BirchAPI",
            "code": "BR-101",
            "candidate_decision": (
                "Retry until the call succeeds."
            ),
            "atoms": [
                "refresh the authorization lease",
                "preserve the request fingerprint",
                "retry exactly three times",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "BirchAPI returns BR-101 again. "
                "State the retry-count rule."
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
                "upstream load may be transient"
            ),
            "latency": 202,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "cedar-api-cd-102",
            "system": "CedarAPI",
            "code": "CD-102",
            "candidate_decision": (
                "Retry six times."
            ),
            "atoms": [
                "refresh the authorization lease",
                "preserve the request fingerprint",
                "retry at most three times",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "CedarAPI returns CD-102 again. "
                "State the maximum retry-count rule."
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
                "upstream load may be transient"
            ),
            "latency": 205,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "dogwood-api-dw-103",
            "system": "DogwoodAPI",
            "code": "DW-103",
            "candidate_decision": (
                "Retry only once."
            ),
            "atoms": [
                "refresh the authorization lease",
                "preserve the request fingerprint",
                "retry at least three times",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "DogwoodAPI returns DW-103 again. "
                "State the minimum retry-count rule."
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
                    r"\bretr",
                ),
            ),
            "operator_note": (
                "upstream load may be transient"
            ),
            "latency": 208,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "elm-api-el-104",
            "system": "ElmAPI",
            "code": "EL-104",
            "candidate_decision": (
                "Retry the timed-out request."
            ),
            "atoms": [
                "refresh the authorization lease",
                "preserve the request fingerprint",
                "never retry the timed-out request",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "ElmAPI returns EL-104 again. "
                "State the retry rule for the timed-out request."
            ),
            "semantic_grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                    r"\bmust\s+not\b",
                ),
                (
                    r"\bretry\b",
                ),
                (
                    r"\btimed[- ]out\b",
                ),
                (
                    r"\brequest\b",
                ),
            ),
            "operator_note": (
                "upstream load may be transient"
            ),
            "latency": 211,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "fir-api-fr-105",
            "system": "FirAPI",
            "code": "FR-105",
            "candidate_decision": (
                "Retry before renewing the authorization lease."
            ),
            "atoms": [
                "preserve the request fingerprint",
                (
                    "retry only after renewing "
                    "the authorization lease"
                ),
                "close the stale connection",
                "record the retry generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "FirAPI returns FR-105 again. "
                "State when retrying is permitted."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bafter\b",
                ),
                (
                    r"\brenew",
                ),
                (
                    r"\bauthorization\b",
                ),
                (
                    r"\blease\b",
                ),
            ),
            "operator_note": (
                "upstream load may be transient"
            ),
            "latency": 214,
        },

        # ============================================================
        # LANE ROUTING
        # ============================================================

        {
            "interference_cluster": "lane-routing",
            "family_id": "gale-queue-gq-111",
            "system": "GaleQueue",
            "code": "GQ-111",
            "candidate_decision": (
                "Move the task to the teal lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the task only to the scarlet lane",
                "retry once",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "GaleQueue returns GQ-111 again. "
                "State the permitted lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bscarlet\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker pressure may be elevated"
            ),
            "latency": 238,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "heath-queue-hq-112",
            "system": "HeathQueue",
            "code": "HQ-112",
            "candidate_decision": (
                "Move the task to the scarlet lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the task only to the teal lane",
                "retry once",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "HeathQueue returns HQ-112 again. "
                "State the permitted lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bteal\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker pressure may be elevated"
            ),
            "latency": 241,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "ivory-queue-iq-113",
            "system": "IvoryQueue",
            "code": "IQ-113",
            "candidate_decision": (
                "Move the task to the scarlet lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the task only to the gold lane",
                "retry once",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "IvoryQueue returns IQ-113 again. "
                "State the permitted lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bgold\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker pressure may be elevated"
            ),
            "latency": 244,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "jade-queue-jq-114",
            "system": "JadeQueue",
            "code": "JQ-114",
            "candidate_decision": (
                "Move the task to the black lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "do not move the task to the black lane",
                "retry once",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "JadeQueue returns JQ-114 again. "
                "State the rule governing the black lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (
                    r"\bmove\b",
                ),
                (
                    r"\bblack\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker pressure may be elevated"
            ),
            "latency": 247,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "kestrel-queue-kq-115",
            "system": "KestrelQueue",
            "code": "KQ-115",
            "candidate_decision": (
                "Always move the task to the white lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                (
                    "if the queue is saturated, "
                    "move the task to the white lane"
                ),
                "retry once",
                "preserve the original task ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "KestrelQueue returns KQ-115. "
                "State the condition for moving the task "
                "to the white lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bsaturated\b",
                ),
                (
                    r"\bwhite\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker pressure may be elevated"
            ),
            "latency": 250,
        },

        # ============================================================
        # CHANNEL / SESSION
        # ============================================================

        {
            "interference_cluster": "channel-session",
            "family_id": "larch-rpc-lr-121",
            "system": "LarchRPC",
            "code": "LR-121",
            "candidate_decision": (
                "Reuse the existing transport channel."
            ),
            "atoms": [
                "preserve the trace fingerprint",
                "open only a fresh transport channel",
                "send one probe frame",
                "record the channel generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "LarchRPC returns LR-121. "
                "State the transport-channel rule."
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
                "transport jitter may exist"
            ),
            "latency": 268,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "moss-rpc-ms-122",
            "system": "MossRPC",
            "code": "MS-122",
            "candidate_decision": (
                "Reuse the previous session nonce."
            ),
            "atoms": [
                "open a fresh transport channel",
                "never reuse the previous session nonce",
                "send one probe frame",
                "preserve the trace fingerprint",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "MossRPC returns MS-122. "
                "State the previous-session-nonce rule."
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
                    r"\bsession\b",
                ),
                (
                    r"\bnonce\b",
                ),
            ),
            "operator_note": (
                "transport jitter may exist"
            ),
            "latency": 271,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "nettle-rpc-nt-123",
            "system": "NettleRPC",
            "code": "NT-123",
            "candidate_decision": (
                "Send seven heartbeat frames."
            ),
            "atoms": [
                "open a fresh transport channel",
                "send exactly four heartbeat frames",
                "preserve the trace fingerprint",
                "record the channel generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "NettleRPC returns NT-123. "
                "State the exact heartbeat-frame count."
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
            "latency": 274,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "oak-rpc-ok-124",
            "system": "OakRPC",
            "code": "OK-124",
            "candidate_decision": (
                "Open the channel immediately."
            ),
            "atoms": [
                "preserve the trace fingerprint",
                "wait at least 14 seconds",
                "open a fresh transport channel",
                "record the channel generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "OakRPC returns OK-124. "
                "State the minimum wait duration."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b14\b",
                    r"\bfourteen\b",
                ),
                (
                    r"\bseconds?\b",
                ),
            ),
            "operator_note": (
                "transport jitter may exist"
            ),
            "latency": 277,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "pebble-rpc-pb-125",
            "system": "PebbleRPC",
            "code": "PB-125",
            "candidate_decision": (
                "Keep eight pending channels."
            ),
            "atoms": [
                "refresh the channel table",
                "keep at most three pending channels",
                "expire stale channels",
                "preserve the newest channel token",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "PebbleRPC returns PB-125. "
                "State the maximum pending-channel count."
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
                    r"\bchannel",
                ),
            ),
            "operator_note": (
                "transport jitter may exist"
            ),
            "latency": 280,
        },

        # ============================================================
        # STORAGE / FINALIZATION
        # ============================================================

        {
            "interference_cluster": "storage-finalization",
            "family_id": "quartz-store-qs-131",
            "system": "QuartzStore",
            "code": "QS-131",
            "candidate_decision": (
                "Finalize with any completion header."
            ),
            "atoms": [
                "verify the manifest checksum",
                "preserve the upload fingerprint",
                (
                    "finalize only with "
                    "X-Quartz-Final: locked"
                ),
                "record the final generation",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "QuartzStore returns QS-131. "
                "State the permitted finalization header."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"X-Quartz-Final",
                ),
                (
                    r"\blocked\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 298,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "rowan-store-rw-132",
            "system": "RowanStore",
            "code": "RW-132",
            "candidate_decision": (
                "Finalize before manifest verification."
            ),
            "atoms": [
                "preserve the upload fingerprint",
                "do not finalize before manifest verification",
                "record the final generation",
                "seal the upload session",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "RowanStore returns RW-132. "
                "State the manifest/finalization rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (
                    r"\bfinaliz",
                ),
                (
                    r"\bbefore\b",
                ),
                (
                    r"\bmanifest\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 301,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "sorrel-store-sr-133",
            "system": "SorrelStore",
            "code": "SR-133",
            "candidate_decision": (
                "Apply two signature blocks."
            ),
            "atoms": [
                "verify the manifest checksum",
                "apply exactly five signature blocks",
                "preserve the upload fingerprint",
                "record the final generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "SorrelStore returns SR-133. "
                "State the exact signature-block count."
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
                    r"\bsignature\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 304,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "tamarind-store-tm-134",
            "system": "TamarindStore",
            "code": "TM-134",
            "candidate_decision": (
                "Retain one replica."
            ),
            "atoms": [
                "verify the manifest checksum",
                "retain at least four replicas",
                "preserve the upload fingerprint",
                "record the replica generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "TamarindStore returns TM-134. "
                "State the minimum replica count."
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
                "storage pressure may exist"
            ),
            "latency": 307,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "umber-store-um-135",
            "system": "UmberStore",
            "code": "UM-135",
            "candidate_decision": (
                "Purge the manifest immediately."
            ),
            "atoms": [
                "read the origin epoch",
                (
                    "do not purge the manifest unless "
                    "the origin epoch changes"
                ),
                "preserve the upload fingerprint",
                "record the new origin epoch",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "UmberStore returns UM-135. "
                "State the condition under which "
                "the manifest may be purged."
            ),
            "semantic_grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (
                    r"\borigin\b",
                ),
                (
                    r"\bepoch\b",
                ),
                (
                    r"\bchang",
                ),
                (
                    r"\bpurge\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 310,
        },
    ]


def build_taskset():
    families = []

    for spec in _specs():

        cluster = (
            spec[
                "interference_cluster"
            ]
        )

        family_args = {
            key: value

            for key, value
            in spec.items()

            if (
                key
                !=
                "interference_cluster"
            )
        }

        family = (
            _add_fallback_challenges(
                _family(
                    **family_args
                )
            )
        )

        family[
            "interference_cluster"
        ] = (
            cluster
        )

        # Explicitly establish the addressing vocabulary.
        #
        # Do not depend on whatever entity defaults _family()
        # may currently provide.
        family[
            "entities"
        ] = list(
            dict.fromkeys(
                [
                    entity

                    for entity
                    in family.get(
                        "entities",
                        []
                    )

                    if (
                        not entity.startswith(
                            "system:"
                        )
                        and
                        not entity.startswith(
                            "code:"
                        )
                    )
                ]
                +
                [
                    (
                        "system:"
                        +
                        spec[
                            "system"
                        ]
                    ),

                    (
                        "code:"
                        +
                        spec[
                            "code"
                        ]
                    ),

                    "domain:recovery",

                    (
                        "cluster:"
                        +
                        cluster
                    ),
                ]
            )
        )

        families.append(
            family
        )

    return {
        "experiment": (
            "seed-growth-018"
        ),

        "classification": (
            "exploratory-fresh-identity-"
            "anchored-activation-ablation"
        ),

        "pool_size": 20,

        "identity_anchor_prefixes": [
            "system:",
            "code:",
        ],

        "hypothesis": (
            "Exact identity addressing before similarity ranking "
            "will restore target-memory activation under pooled "
            "interference while leaving learned memory, compact "
            "representation, downstream ranking, context budget, "
            "and transfer reasoning unchanged."
        ),

        "principle": (
            "Identity narrows. Similarity ranks."
        ),

        "conditions": {
            "A": (
                "current full-pool semantic lexical entity RRF"
            ),

            "B": (
                "same full memory pool with exact system/code "
                "identity candidate selection before unchanged RRF"
            ),
        },

        "primary_metrics": [
            "semantic task success",
            "target semantic clause visibility",
            "wrong-family memory presentation",
            "retrieval precision",
            "retrieval recall",
            "activation rescue",
        ],

        "secondary_metrics": [
            "identity candidate count",
            "identity fallback frequency",
            "wrong-rule contamination",
            "model-visible memory words",
            "model-visible memory segments",
        ],

        "control_invariants": [
            "same target learned lesson",
            "same target source evidence",
            "same transfer query",
            "same compact renderer",
            "same downstream retrieval implementation",
            "same context budget",
            "same transfer reasoner",
            "zero model calls for identity routing",
            "router does not receive benchmark target ID",
            "router does not receive semantic clause or grader",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_018.json"
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
        f"families to {output}"
    )


if __name__ == "__main__":
    main()
