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
        "id": (
            atom_id
        ),
        "text": (
            text
        ),
        "task_pattern": (
            pattern
        ),
    }


def _compose_authoritative(
    *,
    style: int,
    code: str,
    pieces,
):
    a1, a2, a3, a4 = pieces

    if style == 0:
        return (
            f"{a1}; "
            f"{a2}; "
            f"{a3}; "
            f"{a4}."
        )

    if style == 1:
        return (
            f"{a1} and {a2}; "
            f"{a3}, but {a4}."
        )

    if style == 2:
        return (
            f"1) {a1}; "
            f"2) {a2}; "
            f"3) {a3}; "
            f"4) {a4}."
        )

    if style == 3:
        return (
            f"When {code} is observed, "
            f"{a1}; then {a2}, "
            f"{a3}, and {a4}."
        )

    if style == 4:
        return (
            f"Recovery rule: "
            f"{a1}, {a2}; "
            f"{a3}; finally {a4}."
        )

    raise ValueError(
        f"Unknown style: {style}"
    )


def _compound_span(
    *,
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


def _family(
    *,
    index: int,
    spec,
):
    atoms = [
        _atom(
            f"A{atom_index}",
            text,
            pattern,
        )

        for atom_index, (
            text,
            pattern,
        )
        in enumerate(
            spec[
                "atoms"
            ],
            start=1,
        )
    ]

    pieces = [
        atom[
            "text"
        ]
        for atom
        in atoms
    ]

    style = (
        index
        % 5
    )

    authoritative_text = (
        _compose_authoritative(
            style=style,
            code=spec[
                "code"
            ],
            pieces=pieces,
        )
    )

    challenge_1 = (
        _compound_span(
            text=(
                authoritative_text
            ),
            left=pieces[
                0
            ],
            right=pieces[
                1
            ],
        )
    )

    challenge_2 = (
        _compound_span(
            text=(
                authoritative_text
            ),
            left=pieces[
                2
            ],
            right=pieces[
                3
            ],
        )
    )

    status = (
        f"{spec['code']} "
        "run status was FAIL."
    )

    operator_note = (
        "Operator suspects "
        +
        spec[
            "note"
        ]
        +
        "."
    )

    diagnostic = (
        "Observed diagnostic latency "
        f"was {spec['latency']} ms."
    )

    raw_source = (
        build_raw_source(
            status=status,
            failed_decision=(
                spec[
                    "candidate"
                ]
            ),
            authoritative_sentences=[
                authoritative_text
            ],
            operator_note=(
                operator_note
            ),
            diagnostic_metadata=(
                diagnostic
            ),
        )
    )

    required_ids = [
        f"A{required_index}"
        for required_index
        in spec[
            "required"
        ]
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
        "id": (
            spec[
                "id"
            ]
        ),
        "style": (
            style
        ),
        "entities": [
            (
                "system:"
                +
                spec[
                    "system"
                ].lower()
            ),
            (
                "code:"
                +
                spec[
                    "code"
                ].lower()
            ),
        ],
        "experience": {
            "prompt": (
                f"{spec['system']} "
                f"returns "
                f"{spec['code']} "
                f"{spec['experience']} "
                "What should the operator do?"
            )
        },
        "transfer": {
            "prompt": (
                f"{spec['system']} "
                f"returns "
                f"{spec['code']} "
                f"{spec['transfer']} "
                f"{spec['ask']}"
            )
        },
        "candidate_decision": (
            spec[
                "candidate"
            ]
        ),
        "authoritative_text": (
            authoritative_text
        ),
        "raw_source": (
            raw_source
        ),
        "atomic_units": (
            atoms
        ),
        "overlap_challenges": [
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
        "id": "neonpay-np81",
        "system": "NeonPay",
        "code": "NP-81",
        "experience": (
            "while capturing an invoice payment."
        ),
        "transfer": (
            "while adjusting a subscription."
        ),
        "ask": (
            "What wait duration and nonce rule are required?"
        ),
        "candidate": (
            "Restart the payment service and reuse the prior nonce."
        ),
        "note": (
            "gateway congestion may be transient"
        ),
        "latency": 181,
        "atoms": [
            (
                "refresh the recovery lease",
                r"refresh.{0,20}recovery\s+lease",
            ),
            (
                "wait 11 seconds",
                r"\b11\b.{0,10}seconds?",
            ),
            (
                "retry exactly once",
                r"retry.{0,12}exactly.{0,8}once",
            ),
            (
                "never reuse the prior nonce",
                r"(?:never|do.{0,8}not).{0,15}reuse.{0,15}prior\s+nonce",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },
    {
        "id": "cedarqueue-cq44",
        "system": "CedarQueue",
        "code": "CQ-44",
        "experience": (
            "while processing a report job."
        ),
        "transfer": (
            "while processing a thumbnail job."
        ),
        "ask": (
            "Which lane and replay count are required?"
        ),
        "candidate": (
            "Delete the job and restart every worker."
        ),
        "note": (
            "worker saturation may have occurred"
        ),
        "latency": 207,
        "atoms": [
            (
                "request a fresh checkpoint",
                r"fresh.{0,10}checkpoint",
            ),
            (
                "move the job to the cobalt lane",
                r"cobalt.{0,10}lane",
            ),
            (
                "replay exactly twice",
                r"replay.{0,12}exactly.{0,8}twice",
            ),
            (
                "preserve the original job ID",
                r"preserv.{0,15}original.{0,10}job.{0,8}id",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },
    {
        "id": "basaltstore-bs63",
        "system": "BasaltStore",
        "code": "BS-63",
        "experience": (
            "while uploading a backup object."
        ),
        "transfer": (
            "while uploading a snapshot."
        ),
        "ask": (
            "What chunk size and digest are required?"
        ),
        "candidate": (
            "Compress the object and upload it as one part."
        ),
        "note": (
            "compression overhead may have contributed"
        ),
        "latency": 246,
        "atoms": [
            (
                "start a new upload session",
                r"new.{0,10}upload.{0,10}session",
            ),
            (
                "use 18 MiB chunks",
                r"\b18\b.{0,8}(?:mib|mb).{0,10}chunks?",
            ),
            (
                "apply SHA-384 to every chunk",
                r"sha-?384.{0,18}(?:every|each).{0,8}chunk",
            ),
            (
                "finalize with X-Basalt-Mode: sealed",
                r"x-basalt-mode.{0,12}sealed",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },
    {
        "id": "willowdb-wd28",
        "system": "WillowDB",
        "code": "WD-28",
        "experience": (
            "while writing an inventory mutation."
        ),
        "transfer": (
            "while writing a pricing mutation."
        ),
        "ask": (
            "Which epoch source and lock are required?"
        ),
        "candidate": (
            "Increment the epoch locally and bypass locking."
        ),
        "note": (
            "leader churn may have occurred"
        ),
        "latency": 195,
        "atoms": [
            (
                "read the leader epoch",
                r"read.{0,10}leader.{0,10}epoch",
            ),
            (
                "acquire the violet lock",
                r"violet.{0,10}lock",
            ),
            (
                "retry exactly once",
                r"retry.{0,12}exactly.{0,8}once",
            ),
            (
                "preserve the original transaction ID",
                r"preserv.{0,15}original.{0,15}transaction.{0,8}id",
            ),
        ],
        "required": [
            1,
            2,
        ],
    },
    {
        "id": "lumenparser-lp37",
        "system": "LumenParser",
        "code": "LP-37",
        "experience": (
            "with a legacy J state."
        ),
        "transfer": (
            "with a legacy L state."
        ),
        "ask": (
            "What should L become and when must mapping occur?"
        ),
        "candidate": (
            "Drop the state field and treat the record as valid."
        ),
        "note": (
            "an old producer may still be active"
        ),
        "latency": 128,
        "atoms": [
            (
                "map J to queued",
                r"\bj\b.{0,12}queued",
            ),
            (
                "map K to blocked",
                r"\bk\b.{0,12}blocked",
            ),
            (
                "map L to review",
                r"\bl\b.{0,12}review",
            ),
            (
                "perform all mappings before schema validation",
                r"mapping.{0,20}before.{0,15}schema.{0,12}validation",
            ),
        ],
        "required": [
            3,
            4,
        ],
    },
    {
        "id": "orionrpc-or52",
        "system": "OrionRPC",
        "code": "OR-52",
        "experience": (
            "during a profile request."
        ),
        "transfer": (
            "during a billing request."
        ),
        "ask": (
            "How many heartbeats and what spacing are required?"
        ),
        "candidate": (
            "Close the channel and reuse the previous correlation ID."
        ),
        "note": (
            "stream jitter may have occurred"
        ),
        "latency": 302,
        "atoms": [
            (
                "send exactly five heartbeat frames",
                r"(?:five|5).{0,10}heartbeat.{0,10}frames?",
            ),
            (
                "space them 190 ms apart",
                r"\b190\b.{0,8}(?:ms|milliseconds?)",
            ),
            (
                "open a fresh channel",
                r"fresh.{0,10}channel",
            ),
            (
                "include X-Orion-Recover: or52",
                r"x-orion-recover.{0,12}or52",
            ),
        ],
        "required": [
            1,
            2,
        ],
    },
    {
        "id": "frostcdn-fc71",
        "system": "FrostCDN",
        "code": "FC-71",
        "experience": (
            "while refreshing a script asset."
        ),
        "transfer": (
            "while refreshing an image asset."
        ),
        "ask": (
            "Which shard may be purged and how long should you wait?"
        ),
        "candidate": (
            "Perform a global purge and restart all edge processes."
        ),
        "note": (
            "regional cache skew may be present"
        ),
        "latency": 174,
        "atoms": [
            (
                "issue one HEAD request to origin",
                r"head.{0,12}request.{0,16}origin",
            ),
            (
                "purge only the current edge shard",
                r"purge.{0,12}only.{0,18}current.{0,12}edge.{0,10}shard",
            ),
            (
                "wait 13 seconds",
                r"\b13\b.{0,10}seconds?",
            ),
            (
                "issue one GET with X-Frost-Probe: 9",
                r"get.{0,20}x-frost-probe.{0,10}9",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },
    {
        "id": "deltaflow-df35",
        "system": "DeltaFlow",
        "code": "DF-35",
        "experience": (
            "during invoice export."
        ),
        "transfer": (
            "during payroll export."
        ),
        "ask": (
            "Where must execution restart and which token is required?"
        ),
        "candidate": (
            "Resume the failed node using the old checkpoint."
        ),
        "note": (
            "checkpoint replication may have lagged"
        ),
        "latency": 233,
        "atoms": [
            (
                "clone the latest checkpoint",
                r"clone.{0,15}latest.{0,10}checkpoint",
            ),
            (
                "mark the previous run superseded",
                r"previous.{0,10}run.{0,15}superseded",
            ),
            (
                "restart from the prior boundary exactly once",
                r"restart.{0,20}prior.{0,12}boundary.{0,18}exactly.{0,8}once",
            ),
            (
                "carry token df35-safe",
                r"df35-safe",
            ),
        ],
        "required": [
            3,
            4,
        ],
    },
    {
        "id": "amberindex-ai64",
        "system": "AmberIndex",
        "code": "AI-64",
        "experience": (
            "during catalog indexing."
        ),
        "transfer": (
            "during account indexing."
        ),
        "ask": (
            "Which read mode and replay count are required?"
        ),
        "candidate": (
            "Rebuild the entire index and discard the cursor."
        ),
        "note": (
            "segment compaction may be incomplete"
        ),
        "latency": 221,
        "atoms": [
            (
                "fetch a fresh cursor from the leader",
                r"fresh.{0,12}cursor.{0,18}leader",
            ),
            (
                "switch to delta-read",
                r"delta[-\s]read",
            ),
            (
                "replay exactly five pages",
                r"replay.{0,12}exactly.{0,10}(?:five|5).{0,10}pages",
            ),
            (
                "preserve the original query ID",
                r"preserv.{0,15}original.{0,12}query.{0,8}id",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },
    {
        "id": "mossledger-ml23",
        "system": "MossLedger",
        "code": "ML-23",
        "experience": (
            "while posting a settlement."
        ),
        "transfer": (
            "while posting a rebate."
        ),
        "ask": (
            "Where must the nonce come from and how many retries are allowed?"
        ),
        "candidate": (
            "Generate a local nonce and bypass the lock."
        ),
        "note": (
            "nonce service delay may be involved"
        ),
        "latency": 279,
        "atoms": [
            (
                "request the server nonce",
                r"(?:request|get|fetch).{0,12}server.{0,10}nonce",
            ),
            (
                "acquire the amber lock",
                r"amber.{0,10}lock",
            ),
            (
                "retry exactly twice",
                r"retry.{0,12}exactly.{0,8}twice",
            ),
            (
                "set X-Moss-Nonce to the server nonce",
                r"x-moss-nonce.{0,20}server.{0,8}nonce",
            ),
        ],
        "required": [
            1,
            3,
        ],
    },
    {
        "id": "talonbus-tb87",
        "system": "TalonBus",
        "code": "TB-87",
        "experience": (
            "while consuming an invoice event."
        ),
        "transfer": (
            "while consuming an audit event."
        ),
        "ask": (
            "What acknowledgement rule and replay class are required?"
        ),
        "candidate": (
            "Acknowledge the event and retry it directly."
        ),
        "note": (
            "consumer rebalance may have occurred"
        ),
        "latency": 192,
        "atoms": [
            (
                "request a fresh checkpoint",
                r"fresh.{0,10}checkpoint",
            ),
            (
                "leave the original event unacknowledged",
                r"original.{0,12}event.{0,20}unacknowledged",
            ),
            (
                "replay exactly once",
                r"replay.{0,12}exactly.{0,8}once",
            ),
            (
                "use Replay-Class: talon",
                r"replay-class.{0,10}talon",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },
    {
        "id": "cometstore-cs46",
        "system": "CometStore",
        "code": "CS-46",
        "experience": (
            "while uploading an archive."
        ),
        "transfer": (
            "while uploading a snapshot."
        ),
        "ask": (
            "What chunk size and digest algorithm are required?"
        ),
        "candidate": (
            "Reuse the old upload ID and send a single part."
        ),
        "note": (
            "gateway load may be elevated"
        ),
        "latency": 315,
        "atoms": [
            (
                "use a new upload ID",
                r"new.{0,10}upload.{0,8}id",
            ),
            (
                "use 20 MiB chunks",
                r"\b20\b.{0,8}(?:mib|mb).{0,10}chunks?",
            ),
            (
                "apply BLAKE2b to every chunk",
                r"blake2b.{0,18}(?:every|each).{0,8}chunk",
            ),
            (
                "finalize with X-Comet-Manifest: strict",
                r"x-comet-manifest.{0,12}strict",
            ),
        ],
        "required": [
            2,
            3,
        ],
    },
    {
        "id": "fernsearch-fs32",
        "system": "FernSearch",
        "code": "FS-32",
        "experience": (
            "during a customer search."
        ),
        "transfer": (
            "during an inventory search."
        ),
        "ask": (
            "Which read mode and request-ID rule are required?"
        ),
        "candidate": (
            "Reconnect the session and generate a new request ID."
        ),
        "note": (
            "schema propagation may be delayed"
        ),
        "latency": 164,
        "atoms": [
            (
                "refresh the schema token",
                r"refresh.{0,12}schema.{0,10}token",
            ),
            (
                "switch to snapshot-read",
                r"snapshot[-\s]read",
            ),
            (
                "retry exactly once",
                r"retry.{0,12}exactly.{0,8}once",
            ),
            (
                "preserve the original request ID",
                r"preserv.{0,15}original.{0,12}request.{0,8}id",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },
    {
        "id": "aurumrpc-ar66",
        "system": "AurumRPC",
        "code": "AR-66",
        "experience": (
            "during a profile request."
        ),
        "transfer": (
            "during an order request."
        ),
        "ask": (
            "How many heartbeats and which recovery header are required?"
        ),
        "candidate": (
            "Reuse the old channel and previous correlation ID."
        ),
        "note": (
            "stream scheduling jitter may exist"
        ),
        "latency": 226,
        "atoms": [
            (
                "send exactly three heartbeat frames",
                r"(?:three|3).{0,10}heartbeat.{0,10}frames?",
            ),
            (
                "space them 225 ms apart",
                r"\b225\b.{0,8}(?:ms|milliseconds?)",
            ),
            (
                "open a new channel with a fresh correlation ID",
                r"new.{0,10}channel.{0,20}fresh.{0,15}correlation.{0,8}id",
            ),
            (
                "include X-Aurum-Recover: ar66",
                r"x-aurum-recover.{0,12}ar66",
            ),
        ],
        "required": [
            1,
            4,
        ],
    },
    {
        "id": "sprucequeue-sq53",
        "system": "SpruceQueue",
        "code": "SQ-53",
        "experience": (
            "for a report-generation job."
        ),
        "transfer": (
            "for a media-processing job."
        ),
        "ask": (
            "Which lane and dispatch mode are required?"
        ),
        "candidate": (
            "Cancel the job and delete its dispatch record."
        ),
        "note": (
            "dispatch fanout may have stalled"
        ),
        "latency": 202,
        "atoms": [
            (
                "mint a new dispatch ID",
                r"(?:mint|create|generate).{0,15}new.{0,10}dispatch.{0,8}id",
            ),
            (
                "move the job to the silver lane",
                r"silver.{0,10}lane",
            ),
            (
                "requeue exactly once",
                r"re-?queue.{0,12}exactly.{0,8}once",
            ),
            (
                "tag dispatch-mode=recovered",
                r"dispatch-mode.{0,8}recovered",
            ),
        ],
        "required": [
            2,
            4,
        ],
    },
    {
        "id": "silvercdn-sc24",
        "system": "SilverCDN",
        "code": "SC-24",
        "experience": (
            "while refreshing a stylesheet."
        ),
        "transfer": (
            "while refreshing an image."
        ),
        "ask": (
            "What request comes first and which shard may be purged?"
        ),
        "candidate": (
            "Purge every region and invalidate all cached objects."
        ),
        "note": (
            "one edge cluster may be lagging"
        ),
        "latency": 239,
        "atoms": [
            (
                "issue one HEAD request to origin",
                r"head.{0,12}request.{0,16}origin",
            ),
            (
                "purge only the current region shard",
                r"purge.{0,12}only.{0,18}current.{0,12}region.{0,10}shard",
            ),
            (
                "wait 10 seconds",
                r"\b10\b.{0,10}seconds?",
            ),
            (
                "issue one GET with X-Silver-Probe: 5",
                r"get.{0,20}x-silver-probe.{0,10}5",
            ),
        ],
        "required": [
            1,
            2,
        ],
    },
    {
        "id": "emberflow-ef79",
        "system": "EmberFlow",
        "code": "EF-79",
        "experience": (
            "during invoice reconciliation."
        ),
        "transfer": (
            "during analytics export."
        ),
        "ask": (
            "What checkpoint action and restart boundary are required?"
        ),
        "candidate": (
            "Restart the entire workflow and discard its checkpoint."
        ),
        "note": (
            "workflow-state replication may have lagged"
        ),
        "latency": 261,
        "atoms": [
            (
                "clone the latest checkpoint",
                r"clone.{0,15}latest.{0,10}checkpoint",
            ),
            (
                "mark the previous run stale",
                r"previous.{0,10}run.{0,12}stale",
            ),
            (
                "restart from the prior boundary exactly once",
                r"restart.{0,20}prior.{0,12}boundary.{0,18}exactly.{0,8}once",
            ),
            (
                "carry token ef79-safe",
                r"ef79-safe",
            ),
        ],
        "required": [
            1,
            3,
        ],
    },
    {
        "id": "ravenparser-rp18",
        "system": "RavenParser",
        "code": "RP-18",
        "experience": (
            "with a legacy M state."
        ),
        "transfer": (
            "with a legacy O state."
        ),
        "ask": (
            "What should O become and when must mapping occur?"
        ),
        "candidate": (
            "Drop the legacy state and default the record to valid."
        ),
        "note": (
            "a legacy producer may still be emitting old states"
        ),
        "latency": 137,
        "atoms": [
            (
                "map M to queued",
                r"\bm\b.{0,12}queued",
            ),
            (
                "map N to blocked",
                r"\bn\b.{0,12}blocked",
            ),
            (
                "map O to ready",
                r"\bo\b.{0,12}ready",
            ),
            (
                "perform all mappings before normal validation",
                r"mapping.{0,20}before.{0,15}normal.{0,12}validation",
            ),
        ],
        "required": [
            3,
            4,
        ],
    },
    {
        "id": "summitpay-sp57",
        "system": "SummitPay",
        "code": "SP-57",
        "experience": (
            "while capturing an order payment."
        ),
        "transfer": (
            "while adjusting a subscription."
        ),
        "ask": (
            "How long must the operator wait and what retry mode is required?"
        ),
        "candidate": (
            "Reverse the charge immediately and reuse the idempotency key."
        ),
        "note": (
            "acquirer congestion may be transient"
        ),
        "latency": 291,
        "atoms": [
            (
                "wait 17 seconds",
                r"\b17\b.{0,10}seconds?",
            ),
            (
                "rotate the session key",
                r"rotat.{0,12}session.{0,8}key",
            ),
            (
                "mint a new idempotency key",
                r"(?:mint|create|generate).{0,15}new.{0,15}idempotency.{0,8}key",
            ),
            (
                "retry exactly twice with X-Summit-Mode: white",
                r"retry.{0,15}exactly.{0,8}twice.{0,25}x-summit-mode.{0,12}white",
            ),
        ],
        "required": [
            1,
            4,
        ],
    },
    {
        "id": "ivoryindex-ii42",
        "system": "IvoryIndex",
        "code": "II-42",
        "experience": (
            "during product indexing."
        ),
        "transfer": (
            "during account indexing."
        ),
        "ask": (
            "Where should the cursor come from and which query ID must be retained?"
        ),
        "candidate": (
            "Delete the snapshot and rebuild the index."
        ),
        "note": (
            "snapshot compaction may have overlapped the query"
        ),
        "latency": 217,
        "atoms": [
            (
                "fetch a fresh cursor from the leader",
                r"fresh.{0,12}cursor.{0,18}leader",
            ),
            (
                "switch to shadow-read",
                r"shadow[-\s]read",
            ),
            (
                "retry exactly once",
                r"retry.{0,12}exactly.{0,8}once",
            ),
            (
                "preserve the original query ID",
                r"preserv.{0,15}original.{0,12}query.{0,8}id",
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
            index=index,
            spec=spec,
        )

        for index, spec
        in enumerate(
            SPECS
        )
    ]

    return {
        "experiment": (
            "seed-growth-010"
        ),
        "classification": (
            "exploratory-fresh-"
            "autonomous-atomic-boundary-discovery"
        ),
        "hypothesis": (
            "MNEXA can discover atomic proposition boundaries "
            "directly from raw authoritative evidence without "
            "receiving benchmark canonical boundaries, while "
            "the runtime preserves exact source ancestry and "
            "prevents overlapping final evidence atoms."
        ),
        "conditions": {
            "A": (
                "oracle canonical boundaries"
            ),
            "B": (
                "autonomous boundary discovery"
            ),
        },
        "primary_metrics": [
            "canonical boundary recall",
            "canonical boundary precision",
            "exact-boundary families",
            "invented spans admitted",
            "overlapping spans admitted",
            "source ancestry validity",
        ],
        "secondary_metrics": [
            "knowledge completeness",
            "transfer task sufficiency",
            "memory word count",
        ],
        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_010.json"
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
