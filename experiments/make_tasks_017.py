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
        # CLUSTER 1 — RETRY POLICY
        # ============================================================

        {
            "interference_cluster": "retry-policy",
            "family_id": "aster-api-aa-41",
            "system": "AsterAPI",
            "code": "AA-41",
            "candidate_decision": (
                "Retry continuously until success."
            ),
            "atoms": [
                "refresh the session token",
                "preserve the request fingerprint",
                "retry exactly twice",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "AsterAPI returns AA-41 again. "
                "State the retry-count rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bexactly\b",
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
                "upstream pressure may exist"
            ),
            "latency": 204,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "beryl-api-ba-42",
            "system": "BerylAPI",
            "code": "BA-42",
            "candidate_decision": (
                "Retry five times."
            ),
            "atoms": [
                "refresh the session token",
                "preserve the request fingerprint",
                "retry at most twice",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "BerylAPI returns BA-42 again. "
                "State the maximum retry-count rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
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
                "upstream pressure may exist"
            ),
            "latency": 207,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "cinder-api-ca-43",
            "system": "CinderAPI",
            "code": "CA-43",
            "candidate_decision": (
                "Retry only once."
            ),
            "atoms": [
                "refresh the session token",
                "preserve the request fingerprint",
                "retry at least twice",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "CinderAPI returns CA-43 again. "
                "State the minimum retry-count rule."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
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
                "upstream pressure may exist"
            ),
            "latency": 210,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "drift-api-da-44",
            "system": "DriftAPI",
            "code": "DA-44",
            "candidate_decision": (
                "Retry the failed request."
            ),
            "atoms": [
                "refresh the session token",
                "preserve the request fingerprint",
                "never retry the failed request",
                "close the stale connection",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "DriftAPI returns DA-44 again. "
                "State the retry rule for the failed request."
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
                    r"\bfailed\b",
                ),
                (
                    r"\brequest\b",
                ),
            ),
            "operator_note": (
                "upstream pressure may exist"
            ),
            "latency": 213,
        },

        {
            "interference_cluster": "retry-policy",
            "family_id": "ember-api-ea-45",
            "system": "EmberAPI",
            "code": "EA-45",
            "candidate_decision": (
                "Retry before refreshing the token."
            ),
            "atoms": [
                "preserve the request fingerprint",
                (
                    "retry only after refreshing "
                    "the session token"
                ),
                "close the stale connection",
                "record the retry generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "EmberAPI returns EA-45 again. "
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
                    r"\brefresh",
                ),
                (
                    r"\bsession\b",
                ),
                (
                    r"\btoken\b",
                ),
            ),
            "operator_note": (
                "upstream pressure may exist"
            ),
            "latency": 216,
        },

        # ============================================================
        # CLUSTER 2 — LANE ROUTING
        # ============================================================

        {
            "interference_cluster": "lane-routing",
            "family_id": "frost-queue-fq-51",
            "system": "FrostQueue",
            "code": "FQ-51",
            "candidate_decision": (
                "Move the job to the violet lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job only to the cobalt lane",
                "retry once",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "FrostQueue returns FQ-51 again. "
                "State the permitted lane."
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
            "latency": 241,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "grove-queue-gq-52",
            "system": "GroveQueue",
            "code": "GQ-52",
            "candidate_decision": (
                "Move the job to the cobalt lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job only to the violet lane",
                "retry once",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "GroveQueue returns GQ-52 again. "
                "State the permitted lane."
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
            "latency": 244,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "harbor-queue-hq-53",
            "system": "HarborQueue",
            "code": "HQ-53",
            "candidate_decision": (
                "Move the job to the cobalt lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "move the job only to the silver lane",
                "retry once",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "HarborQueue returns HQ-53 again. "
                "State the permitted lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"\bsilver\b",
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
            "interference_cluster": "lane-routing",
            "family_id": "iris-queue-iq-54",
            "system": "IrisQueue",
            "code": "IQ-54",
            "candidate_decision": (
                "Move the job to the amber lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                "do not move the job to the amber lane",
                "retry once",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "IrisQueue returns IQ-54 again. "
                "State the rule governing the amber lane."
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
                    r"\bamber\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker saturation may exist"
            ),
            "latency": 250,
        },

        {
            "interference_cluster": "lane-routing",
            "family_id": "juniper-queue-jq-55",
            "system": "JuniperQueue",
            "code": "JQ-55",
            "candidate_decision": (
                "Always move the job to the bronze lane."
            ),
            "atoms": [
                "request a fresh checkpoint",
                (
                    "if the queue is degraded, "
                    "move the job to the bronze lane"
                ),
                "retry once",
                "preserve the original job ID",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "when_if",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "JuniperQueue returns JQ-55. "
                "State the condition for moving the job "
                "to the bronze lane."
            ),
            "semantic_grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (
                    r"\bdegraded\b",
                ),
                (
                    r"\bbronze\b",
                ),
                (
                    r"\blane\b",
                ),
            ),
            "operator_note": (
                "worker saturation may exist"
            ),
            "latency": 253,
        },

        # ============================================================
        # CLUSTER 3 — CHANNEL / SESSION
        # ============================================================

        {
            "interference_cluster": "channel-session",
            "family_id": "kelp-rpc-kr-61",
            "system": "KelpRPC",
            "code": "KR-61",
            "candidate_decision": (
                "Reuse the existing channel."
            ),
            "atoms": [
                "preserve the trace fingerprint",
                "open only a fresh channel",
                "send one probe frame",
                "record the channel generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "KelpRPC returns KR-61. "
                "State the channel rule."
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
            "latency": 271,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "laurel-rpc-lr-62",
            "system": "LaurelRPC",
            "code": "LR-62",
            "candidate_decision": (
                "Reuse the previous correlation token."
            ),
            "atoms": [
                "open a fresh channel",
                "never reuse the previous correlation token",
                "send one probe frame",
                "preserve the trace fingerprint",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "never",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "LaurelRPC returns LR-62. "
                "State the correlation-token rule."
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
                "transport jitter may exist"
            ),
            "latency": 274,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "maple-rpc-mr-63",
            "system": "MapleRPC",
            "code": "MR-63",
            "candidate_decision": (
                "Send five heartbeat frames."
            ),
            "atoms": [
                "open a fresh channel",
                "send exactly three heartbeat frames",
                "preserve the trace fingerprint",
                "record the channel generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "MapleRPC returns MR-63. "
                "State the exact heartbeat-frame count."
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
                "transport jitter may exist"
            ),
            "latency": 277,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "north-rpc-nr-64",
            "system": "NorthRPC",
            "code": "NR-64",
            "candidate_decision": (
                "Open the channel immediately."
            ),
            "atoms": [
                "preserve the trace fingerprint",
                "wait at least 12 seconds",
                "open a fresh channel",
                "record the channel generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "NorthRPC returns NR-64. "
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
                "transport jitter may exist"
            ),
            "latency": 280,
        },

        {
            "interference_cluster": "channel-session",
            "family_id": "opal-rpc-or-65",
            "system": "OpalRPC",
            "code": "OR-65",
            "candidate_decision": (
                "Keep six pending channels."
            ),
            "atoms": [
                "refresh the channel table",
                "keep at most two pending channels",
                "expire stale channels",
                "preserve the newest channel token",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_most",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "OpalRPC returns OR-65. "
                "State the maximum pending-channel count."
            ),
            "semantic_grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\btwo\b",
                    r"\b2\b",
                ),
                (
                    r"\bchannel",
                ),
            ),
            "operator_note": (
                "transport jitter may exist"
            ),
            "latency": 283,
        },

        # ============================================================
        # CLUSTER 4 — STORAGE / FINALIZATION
        # ============================================================

        {
            "interference_cluster": "storage-finalization",
            "family_id": "pine-store-ps-71",
            "system": "PineStore",
            "code": "PS-71",
            "candidate_decision": (
                "Finalize with any completion header."
            ),
            "atoms": [
                "verify the manifest checksum",
                "preserve the upload fingerprint",
                (
                    "finalize only with "
                    "X-Pine-Final: sealed"
                ),
                "record the final generation",
            ],
            "semantic_atom_index": 3,
            "semantic_operator": "only",
            "semantic_dimension": "scope",
            "transfer_prompt": (
                "PineStore returns PS-71. "
                "State the permitted finalization header."
            ),
            "semantic_grader": _grader(
                (
                    r"\bonly\b",
                ),
                (
                    r"X-Pine-Final",
                ),
                (
                    r"\bsealed\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 301,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "quill-store-qs-72",
            "system": "QuillStore",
            "code": "QS-72",
            "candidate_decision": (
                "Finalize before checksum verification."
            ),
            "atoms": [
                "preserve the upload fingerprint",
                "do not finalize before checksum verification",
                "record the final generation",
                "seal the upload session",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "do_not",
            "semantic_dimension": "polarity",
            "transfer_prompt": (
                "QuillStore returns QS-72. "
                "State the checksum/finalization rule."
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
                    r"\bchecksum\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 304,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "raven-store-rs-73",
            "system": "RavenStore",
            "code": "RS-73",
            "candidate_decision": (
                "Apply two signature blocks."
            ),
            "atoms": [
                "verify the manifest checksum",
                "apply exactly four signature blocks",
                "preserve the upload fingerprint",
                "record the final generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "exactly",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "RavenStore returns RS-73. "
                "State the exact signature-block count."
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
                    r"\bsignature\b",
                ),
            ),
            "operator_note": (
                "storage pressure may exist"
            ),
            "latency": 307,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "spruce-store-ss-74",
            "system": "SpruceStore",
            "code": "SS-74",
            "candidate_decision": (
                "Retain one replica."
            ),
            "atoms": [
                "verify the manifest checksum",
                "retain at least three replicas",
                "preserve the upload fingerprint",
                "record the replica generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "at_least",
            "semantic_dimension": "cardinality",
            "transfer_prompt": (
                "SpruceStore returns SS-74. "
                "State the minimum replica count."
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
                "storage pressure may exist"
            ),
            "latency": 310,
        },

        {
            "interference_cluster": "storage-finalization",
            "family_id": "thistle-store-ts-75",
            "system": "ThistleStore",
            "code": "TS-75",
            "candidate_decision": (
                "Purge the manifest immediately."
            ),
            "atoms": [
                "read the origin generation",
                (
                    "do not purge the manifest unless "
                    "the origin generation changes"
                ),
                "preserve the upload fingerprint",
                "record the new origin generation",
            ],
            "semantic_atom_index": 2,
            "semantic_operator": "unless",
            "semantic_dimension": "condition",
            "transfer_prompt": (
                "ThistleStore returns TS-75. "
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
                "storage pressure may exist"
            ),
            "latency": 313,
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

        family[
            "entities"
        ] = list(
            dict.fromkeys(
                family[
                    "entities"
                ]
                +
                [
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

    family_ids = [
        family[
            "id"
        ]

        for family
        in families
    ]

    for index, family in enumerate(
        families
    ):

        family[
            "pool_position"
        ] = (
            index + 1
        )

        family[
            "distractor_family_ids"
        ] = [
            family_id

            for family_id
            in family_ids

            if (
                family_id
                !=
                family[
                    "id"
                ]
            )
        ]

        family[
            "near_neighbor_family_ids"
        ] = [
            other[
                "id"
            ]

            for other
            in families

            if (
                other[
                    "id"
                ]
                !=
                family[
                    "id"
                ]
            )
            and
            (
                other[
                    "interference_cluster"
                ]
                ==
                family[
                    "interference_cluster"
                ]
            )
        ]

    return {
        "experiment": (
            "seed-growth-017"
        ),

        "classification": (
            "exploratory-fresh-pooled-memory-"
            "interference-ablation"
        ),

        "pool_size": 20,

        "distractors_per_target": 19,

        "near_neighbors_per_target": 4,

        "hypothesis": (
            "MNEXA's compact accumulated memories should remain "
            "behaviorally useful when twenty learned memories coexist. "
            "Adding nineteen distractors should not materially reduce "
            "target-memory activation or downstream task success."
        ),

        "conditions": {
            "A": (
                "target compact memory alone"
            ),

            "B": (
                "same target compact memory plus all nineteen "
                "other learned memories"
            ),
        },

        "primary_metrics": [
            "semantic task success",
            "target semantic clause visibility",
            "wrong-family clause visibility",
            "model-visible retrieval precision",
            "model-visible retrieval recall",
            "paired retrieval regret",
        ],

        "secondary_metrics": [
            "exact wrong-rule decision contamination",
            "model-visible memory words",
            "model-visible memory segments",
            "cluster-level interference",
        ],

        "control_invariants": [
            "same target learned lesson",
            "same target source evidence",
            "same transfer query",
            "same compact renderer",
            "same context-budget configuration",
            "pooled evaluation from one frozen snapshot",
            "isolated evaluation from frozen snapshots",
            "byte-identical snapshot copies before evaluation",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_017.json"
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
