from __future__ import annotations

import json

from pathlib import Path


from experiments.make_tasks_008 import (
    build_raw_source,
)


def _atom(
    atom_id,
    text,
    pattern,
):
    return {
        "id": atom_id,
        "text": text,
        "task_pattern": pattern,
    }


def _build_atoms(
    definitions,
):
    return [
        _atom(
            f"A{index}",
            text,
            pattern,
        )

        for index, (
            text,
            pattern,
        )
        in enumerate(
            definitions,
            start=1,
        )
    ]


def _family(
    *,
    id,
    system,
    code,
    experience,
    transfer,
    candidate,
    note,
    latency,
    atom_definitions,
    required_indices,
):
    atoms = (
        _build_atoms(
            atom_definitions
        )
    )

    status = (
        f"{code} run status was FAIL."
    )

    operator_note = (
        f"Operator suspects {note}."
    )

    metadata = (
        "Observed diagnostic latency "
        f"was {latency} ms."
    )

    raw_source = (
        build_raw_source(
            status=status,
            failed_decision=(
                candidate
            ),
            authoritative_sentences=[
                atom[
                    "text"
                ]
                for atom
                in atoms
            ],
            operator_note=(
                operator_note
            ),
            diagnostic_metadata=(
                metadata
            ),
        )
    )

    # Two deliberate compound-but-perfectly-grounded
    # authoritative spans.
    compound_1 = (
        atoms[0][
            "text"
        ]
        + " "
        + atoms[1][
            "text"
        ]
    )

    compound_2 = (
        atoms[2][
            "text"
        ]
        + " "
        + atoms[3][
            "text"
        ]
    )

    required_ids = [
        f"A{index}"
        for index
        in required_indices
    ]

    by_id = {
        atom[
            "id"
        ]: atom
        for atom
        in atoms
    }

    required_atoms = [
        by_id[
            atom_id
        ]
        for atom_id
        in required_ids
    ]

    return {
        "id": id,

        "entities": [
            f"system:{system.lower()}",
            f"code:{code.lower()}",
        ],

        "experience": {
            "prompt": (
                f"{system} returns {code} "
                f"{experience} "
                "What should the operator do?"
            )
        },

        "transfer": {
            "prompt": (
                f"{system} returns {code} "
                f"{transfer}"
            )
        },

        "candidate_decision": (
            candidate
        ),

        "raw_source": (
            raw_source
        ),

        "atomic_units": (
            atoms
        ),

        "atomicity_challenges": [
            {
                "id": "C1",
                "text": (
                    compound_1
                ),
                "covers_atom_ids": [
                    "A1",
                    "A2",
                ],
            },
            {
                "id": "C2",
                "text": (
                    compound_2
                ),
                "covers_atom_ids": [
                    "A3",
                    "A4",
                ],
            },
        ],

        "transfer_required_atom_ids": (
            required_ids
        ),

        "knowledge_grader": {
            "all_regex": [
                [
                    atom[
                        "task_pattern"
                    ]
                ]

                for atom
                in atoms
            ]
        },

        "transfer_grader": {
            "all_regex": [
                [
                    atom[
                        "task_pattern"
                    ]
                ]

                for atom
                in required_atoms
            ]
        },
    }


SPECS = [

    {
        "id": "vectorpay-vp62",
        "system": "VectorPay",
        "code": "VP-62",
        "experience": (
            "while capturing an invoice payment."
        ),
        "transfer": (
            "while adjusting a subscription. "
            "What wait duration and recovery header are required?"
        ),
        "candidate": (
            "Restart the payment service and clear the cache."
        ),
        "note": (
            "gateway congestion may be involved"
        ),
        "latency": 184,
        "atoms": [
            (
                "Refresh the recovery lease.",
                r"refresh.*recovery\s+lease",
            ),
            (
                "Wait 9 seconds.",
                r"\b9\s*seconds?\b",
            ),
            (
                "Retry exactly once.",
                r"retry.*exactly\s+once",
            ),
            (
                "Include X-Vector-Recover: copper.",
                r"x-vector-recover.*copper",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },

    {
        "id": "maplequeue-mq27",
        "system": "MapleQueue",
        "code": "MQ-27",
        "experience": (
            "while rendering a document job."
        ),
        "transfer": (
            "while processing an image job. "
            "Which lane and replay count are required?"
        ),
        "candidate": (
            "Delete the message and restart all workers."
        ),
        "note": (
            "worker saturation may have occurred"
        ),
        "latency": 208,
        "atoms": [
            (
                "Request a fresh checkpoint.",
                r"fresh\s+checkpoint",
            ),
            (
                "Move the job to the amber lane.",
                r"amber\s+lane",
            ),
            (
                "Replay exactly once from the checkpoint.",
                r"replay.*exactly\s+once",
            ),
            (
                "Use Replay-Class: maple.",
                r"replay-class.*maple",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },

    {
        "id": "cobaltstore-cs91",
        "system": "CobaltStore",
        "code": "CS-91",
        "experience": (
            "while uploading a 160 MiB archive."
        ),
        "transfer": (
            "while uploading an 80 MiB snapshot. "
            "What chunk size and digest are required?"
        ),
        "candidate": (
            "Compress the file and send one large part."
        ),
        "note": (
            "compression overhead may have contributed"
        ),
        "latency": 249,
        "atoms": [
            (
                "Start a new upload session.",
                r"new\s+upload\s+session",
            ),
            (
                "Use multipart upload with 16 MiB chunks.",
                r"multipart.*16\s*(?:mib|mb)",
            ),
            (
                "Attach SHA-512 to every chunk.",
                r"sha-?512.*(?:every|each|per).*chunk",
            ),
            (
                "Include X-Cobalt-Final: strict on finalization.",
                r"x-cobalt-final.*strict",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },

    {
        "id": "brambledb-bd38",
        "system": "BrambleDB",
        "code": "BD-38",
        "experience": (
            "while writing an inventory mutation."
        ),
        "transfer": (
            "while writing a pricing mutation. "
            "Which epoch and lock are required?"
        ),
        "candidate": (
            "Restart the node and increment the epoch locally."
        ),
        "note": (
            "leader churn may have occurred"
        ),
        "latency": 197,
        "atoms": [
            (
                "Read the primary epoch.",
                r"read.*primary\s+epoch",
            ),
            (
                "Acquire the bronze lock.",
                r"bronze\s+lock",
            ),
            (
                "Retry exactly once.",
                r"retry.*exactly\s+once",
            ),
            (
                "Set X-Bramble-Epoch to the primary epoch.",
                r"x-bramble-epoch.*primary\s+epoch",
            ),
        ],
        "required": [
            1,
            2,
        ],
    },

    {
        "id": "irisparser-ip14",
        "system": "IrisParser",
        "code": "IP-14",
        "experience": (
            "with legacy state=D before validation."
        ),
        "transfer": (
            "with legacy state=F before validation. "
            "What should F map to and when?"
        ),
        "candidate": (
            "Drop the state field and default to valid."
        ),
        "note": (
            "a legacy producer may still be active"
        ),
        "latency": 131,
        "atoms": [
            (
                "Map D to queued.",
                r"\bd\b.*\bqueued\b",
            ),
            (
                "Map E to blocked.",
                r"\be\b.*\bblocked\b",
            ),
            (
                "Map F to review.",
                r"\bf\b.*\breview\b",
            ),
            (
                "Perform the mapping before normal validation.",
                r"before.*normal\s+validation",
            ),
        ],
        "required": [
            3,
            4,
        ],
    },

    {
        "id": "zenithrpc-zr73",
        "system": "ZenithRPC",
        "code": "ZR-73",
        "experience": (
            "during a profile request."
        ),
        "transfer": (
            "during a billing request. "
            "How many heartbeats and which recovery header are required?"
        ),
        "candidate": (
            "Close the connection and reuse the old correlation ID."
        ),
        "note": (
            "stream jitter may have occurred"
        ),
        "latency": 304,
        "atoms": [
            (
                "Send exactly four heartbeat frames.",
                r"(?:four|4)\s+heartbeat",
            ),
            (
                "Space the heartbeat frames 210 ms apart.",
                r"\b210\s*(?:ms|milliseconds?)\b",
            ),
            (
                "Open a new channel with a fresh correlation ID.",
                r"new\s+channel.*fresh\s+correlation\s+id",
            ),
            (
                "Include X-Zenith-Recover: zr73.",
                r"x-zenith-recover.*zr73",
            ),
        ],
        "required": [
            1,
            4,
        ],
    },

    {
        "id": "glaciercdn-gc25",
        "system": "GlacierCDN",
        "code": "GC-25",
        "experience": (
            "while refreshing a JavaScript asset."
        ),
        "transfer": (
            "while refreshing an image asset. "
            "Which shard may be purged and how long should you wait?"
        ),
        "candidate": (
            "Perform a global purge and restart every edge worker."
        ),
        "note": (
            "regional cache skew may exist"
        ),
        "latency": 176,
        "atoms": [
            (
                "Issue one HEAD request to origin.",
                r"(?:one|1)\s+head\s+request",
            ),
            (
                "Purge only the current POP shard.",
                r"purge.*only.*current\s+pop\s+shard",
            ),
            (
                "Wait 7 seconds.",
                r"\b7\s*seconds?\b",
            ),
            (
                "Issue one GET with X-Glacier-Probe: 6.",
                r"(?:one|1)\s+get.*x-glacier-probe.*6",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },

    {
        "id": "meadowflow-mf44",
        "system": "MeadowFlow",
        "code": "MF-44",
        "experience": (
            "during invoice reconciliation."
        ),
        "transfer": (
            "during payroll export. "
            "Where should execution restart and which token must be carried?"
        ),
        "candidate": (
            "Resume the failed node using the same checkpoint."
        ),
        "note": (
            "checkpoint replication may have lagged"
        ),
        "latency": 235,
        "atoms": [
            (
                "Clone the latest checkpoint.",
                r"clone.*latest\s+checkpoint",
            ),
            (
                "Mark the old run superseded.",
                r"old\s+run.*superseded",
            ),
            (
                "Restart from the previous boundary exactly once.",
                r"restart.*previous\s+boundary.*exactly\s+once",
            ),
            (
                "Carry token mf44-safe.",
                r"mf44-safe",
            ),
        ],
        "required": [
            3,
            4,
        ],
    },

    {
        "id": "opalindex-oi57",
        "system": "OpalIndex",
        "code": "OI-57",
        "experience": (
            "during catalog indexing."
        ),
        "transfer": (
            "during account indexing. "
            "Which read mode and replay count are required?"
        ),
        "candidate": (
            "Rebuild the index and discard the current cursor."
        ),
        "note": (
            "segment compaction may be incomplete"
        ),
        "latency": 223,
        "atoms": [
            (
                "Fetch a fresh cursor from the leader.",
                r"fresh\s+cursor.*leader",
            ),
            (
                "Switch to delta-read.",
                r"delta[-\s]read",
            ),
            (
                "Replay exactly three pages.",
                r"replay.*exactly\s+(?:three|3)\s+pages",
            ),
            (
                "Set X-Opal-Cursor: fresh.",
                r"x-opal-cursor.*fresh",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },

    {
        "id": "birchledger-bl32",
        "system": "BirchLedger",
        "code": "BL-32",
        "experience": (
            "while posting a settlement."
        ),
        "transfer": (
            "while posting a rebate. "
            "Where should the nonce come from and how many retries are allowed?"
        ),
        "candidate": (
            "Synthesize a nonce locally and bypass the lock."
        ),
        "note": (
            "nonce-service latency may be involved"
        ),
        "latency": 282,
        "atoms": [
            (
                "Request the server nonce.",
                r"(?:request|fetch|get).*server\s+nonce",
            ),
            (
                "Acquire the teal lock.",
                r"teal\s+lock",
            ),
            (
                "Retry exactly twice.",
                r"retry.*exactly\s+twice",
            ),
            (
                "Set X-Birch-Nonce to the server nonce.",
                r"x-birch-nonce.*server\s+nonce",
            ),
        ],
        "required": [
            1,
            3,
        ],
    },

    {
        "id": "quartzbus-qb19",
        "system": "QuartzBus",
        "code": "QB-19",
        "experience": (
            "while consuming an invoice event."
        ),
        "transfer": (
            "while consuming an audit event. "
            "Which checkpoint and replay class should be used?"
        ),
        "candidate": (
            "Acknowledge the original message and retry it directly."
        ),
        "note": (
            "consumer rebalance may have occurred"
        ),
        "latency": 196,
        "atoms": [
            (
                "Request a fresh checkpoint.",
                r"fresh\s+checkpoint",
            ),
            (
                "Replay exactly once from the checkpoint.",
                r"replay.*exactly\s+once",
            ),
            (
                "Use Replay-Class: quartz.",
                r"replay-class.*quartz",
            ),
            (
                "Leave the original message unacknowledged.",
                r"original\s+message.*unacknowledged",
            ),
        ],
        "required": [
            1,
            3,
        ],
    },

    {
        "id": "aurorastore-as68",
        "system": "AuroraStore",
        "code": "AS-68",
        "experience": (
            "while uploading a 240 MiB backup."
        ),
        "transfer": (
            "while uploading a 120 MiB snapshot. "
            "What chunk size and checksum are required?"
        ),
        "candidate": (
            "Reuse the old upload ID and send a single part."
        ),
        "note": (
            "gateway load may be elevated"
        ),
        "latency": 317,
        "atoms": [
            (
                "Use a new upload ID.",
                r"new\s+upload\s+id",
            ),
            (
                "Use multipart upload with 24 MiB chunks.",
                r"multipart.*24\s*(?:mib|mb)",
            ),
            (
                "Apply BLAKE3 to every chunk.",
                r"blake3.*(?:every|each|per).*chunk",
            ),
            (
                "Include X-Aurora-Manifest: polar on finalization.",
                r"x-aurora-manifest.*polar",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },

    {
        "id": "cedarsearch-ce26",
        "system": "CedarSearch",
        "code": "CE-26",
        "experience": (
            "during a customer search."
        ),
        "transfer": (
            "during an inventory search. "
            "Which read mode and request-ID rule should be used?"
        ),
        "candidate": (
            "Reconnect the session and generate a new request ID."
        ),
        "note": (
            "schema propagation may be delayed"
        ),
        "latency": 166,
        "atoms": [
            (
                "Refresh the schema token.",
                r"refresh.*schema\s+token",
            ),
            (
                "Switch to snapshot-read.",
                r"snapshot[-\s]read",
            ),
            (
                "Retry exactly once.",
                r"retry.*exactly\s+once",
            ),
            (
                "Preserve the original request ID.",
                r"preserv.*original\s+request\s+id",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },

    {
        "id": "prismrpc-pr47",
        "system": "PrismRPC",
        "code": "PR-47",
        "experience": (
            "during a profile RPC."
        ),
        "transfer": (
            "during a payment RPC. "
            "What heartbeat spacing and recovery header are required?"
        ),
        "candidate": (
            "Reuse the prior stream ID and restart the RPC service."
        ),
        "note": (
            "stream scheduling jitter may be present"
        ),
        "latency": 228,
        "atoms": [
            (
                "Send exactly two heartbeat frames.",
                r"(?:two|2)\s+heartbeat",
            ),
            (
                "Space the heartbeat frames 175 ms apart.",
                r"\b175\s*(?:ms|milliseconds?)\b",
            ),
            (
                "Open a fresh channel.",
                r"fresh\s+channel",
            ),
            (
                "Include X-Prism-Recover: pr47.",
                r"x-prism-recover.*pr47",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },

    {
        "id": "emberqueue-eq83",
        "system": "EmberQueue",
        "code": "EQ-83",
        "experience": (
            "for a report-generation job."
        ),
        "transfer": (
            "for a media-processing job. "
            "Which lane and dispatch mode are required?"
        ),
        "candidate": (
            "Cancel the job and delete the dispatch record."
        ),
        "note": (
            "dispatch fanout may have stalled"
        ),
        "latency": 204,
        "atoms": [
            (
                "Mint a new dispatch ID.",
                r"(?:mint|create|generate).*new\s+dispatch\s+id",
            ),
            (
                "Move the job to the silver lane.",
                r"silver\s+lane",
            ),
            (
                "Requeue exactly once.",
                r"re-?queue.*exactly\s+once",
            ),
            (
                "Tag dispatch-mode=restored.",
                r"dispatch-mode\s*=\s*restored",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },

    {
        "id": "mistcdn-mc54",
        "system": "MistCDN",
        "code": "MC-54",
        "experience": (
            "while refreshing a CSS asset."
        ),
        "transfer": (
            "while refreshing an image asset. "
            "What request is issued first and which shard may be purged?"
        ),
        "candidate": (
            "Purge every region and invalidate all cached assets."
        ),
        "note": (
            "one edge cluster may be lagging"
        ),
        "latency": 241,
        "atoms": [
            (
                "Issue one HEAD request to origin.",
                r"(?:one|1)\s+head\s+request",
            ),
            (
                "Purge only the current region shard.",
                r"purge.*only.*current\s+region\s+shard",
            ),
            (
                "Wait 12 seconds.",
                r"\b12\s*seconds?\b",
            ),
            (
                "Issue one GET with X-Mist-Probe: 7.",
                r"(?:one|1)\s+get.*x-mist-probe.*7",
            ),
        ],
        "required": [
            1,
            2,
        ],
    },

    {
        "id": "solsticeflow-sf39",
        "system": "SolsticeFlow",
        "code": "SF-39",
        "experience": (
            "during invoice export."
        ),
        "transfer": (
            "during analytics export. "
            "Which checkpoint action and restart boundary are required?"
        ),
        "candidate": (
            "Restart the full workflow and discard the checkpoint."
        ),
        "note": (
            "workflow-state replication may have lagged"
        ),
        "latency": 264,
        "atoms": [
            (
                "Clone the latest checkpoint.",
                r"clone.*latest\s+checkpoint",
            ),
            (
                "Mark the old run stale.",
                r"old\s+run.*stale",
            ),
            (
                "Restart from the previous boundary exactly once.",
                r"restart.*previous\s+boundary.*exactly\s+once",
            ),
            (
                "Carry token sf39-safe.",
                r"sf39-safe",
            ),
        ],
        "required": [
            1,
            3,
        ],
    },

    {
        "id": "coralparser-cp12",
        "system": "CoralParser",
        "code": "CP-12",
        "experience": (
            "with legacy state=U before validation."
        ),
        "transfer": (
            "with legacy state=W before validation. "
            "What should W map to and when?"
        ),
        "candidate": (
            "Drop the legacy field and default the record to valid."
        ),
        "note": (
            "an old producer may still emit legacy states"
        ),
        "latency": 139,
        "atoms": [
            (
                "Map U to queued.",
                r"\bu\b.*\bqueued\b",
            ),
            (
                "Map V to blocked.",
                r"\bv\b.*\bblocked\b",
            ),
            (
                "Map W to ready.",
                r"\bw\b.*\bready\b",
            ),
            (
                "Perform the mapping before normal validation.",
                r"before.*normal\s+validation",
            ),
        ],
        "required": [
            3,
            4,
        ],
    },

    {
        "id": "northpay-np76",
        "system": "NorthPay",
        "code": "NP-76",
        "experience": (
            "while capturing an order payment."
        ),
        "transfer": (
            "while issuing a subscription adjustment. "
            "How long should the operator wait and how many retries are allowed?"
        ),
        "candidate": (
            "Refund the customer immediately and reverse the charge."
        ),
        "note": (
            "acquirer congestion may be transient"
        ),
        "latency": 294,
        "atoms": [
            (
                "Wait 15 seconds.",
                r"\b15\s*seconds?\b",
            ),
            (
                "Rotate the session key.",
                r"rotat.*session\s+key",
            ),
            (
                "Mint a new idempotency key.",
                r"(?:mint|create|generate).*new\s+idempotency\s+key",
            ),
            (
                "Retry exactly twice with X-North-Mode: black.",
                r"retry.*exactly\s+twice.*x-north-mode.*black",
            ),
        ],
        "required": [
            1,
            4,
        ],
    },

    {
        "id": "velvetindex-vi43",
        "system": "VelvetIndex",
        "code": "VI-43",
        "experience": (
            "during product search."
        ),
        "transfer": (
            "during account search. "
            "Which cursor source and query-ID rule are required?"
        ),
        "candidate": (
            "Delete the snapshot and rebuild the index."
        ),
        "note": (
            "snapshot compaction may have overlapped the query"
        ),
        "latency": 219,
        "atoms": [
            (
                "Fetch a fresh cursor from the leader.",
                r"fresh\s+cursor.*leader",
            ),
            (
                "Switch to shadow-read.",
                r"shadow[-\s]read",
            ),
            (
                "Retry exactly once.",
                r"retry.*exactly\s+once",
            ),
            (
                "Preserve the original query ID.",
                r"preserv.*original\s+query\s+id",
            ),
        ],
        "required": [
            1,
            4,
        ],
    },
]


def build_taskset():
    families = [
        _family(
            id=spec[
                "id"
            ],
            system=spec[
                "system"
            ],
            code=spec[
                "code"
            ],
            experience=spec[
                "experience"
            ],
            transfer=spec[
                "transfer"
            ],
            candidate=spec[
                "candidate"
            ],
            note=spec[
                "note"
            ],
            latency=spec[
                "latency"
            ],
            atom_definitions=spec[
                "atoms"
            ],
            required_indices=spec[
                "required"
            ],
        )

        for spec
        in SPECS
    ]

    return {
        "experiment": (
            "seed-growth-009"
        ),

        "classification": (
            "exploratory-fresh-"
            "evidence-atomicity-ablation"
        ),

        "hypothesis": (
            "Source grounding and evidence-role eligibility "
            "are insufficient to define a reusable evidence "
            "atom. A deterministic atomic-boundary admission "
            "gate should reject compound and partial spans "
            "while retaining individually reusable "
            "authoritative propositions."
        ),

        "primary_metrics": [
            "atomic_recall",
            "atomic_precision",
            "compound_atoms_admitted",
            "atomicity_challenge_rejections",
        ],

        "secondary_metrics": [
            "knowledge_completeness",
            "task_sufficiency",
            "memory_word_count",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_009.json"
    )

    payload = (
        build_taskset()
    )

    output.write_text(
        json.dumps(
            payload,
            indent=2,
        )
        + "\n"
    )

    print(
        f"Wrote "
        f"{len(payload['families'])} "
        f"families to {output}"
    )


if __name__ == "__main__":
    main()
