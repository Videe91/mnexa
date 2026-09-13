from __future__ import annotations

import json

from pathlib import Path


def _family(
    *,
    id,
    system,
    code,
    experience_task,
    transfer_task,
    rule,
    task_regex,
    fidelity_extra,
):
    return {
        "id": id,

        "entities": [
            f"system:{system.lower()}",
            f"code:{code.lower()}",
        ],

        "experience": {
            "prompt": (
                f"{system} returns {code} "
                f"{experience_task} "
                "What should the operator do?"
            ),

            "feedback": (
                f"{system} runbook rule: "
                f"{code} {rule}"
            ),
        },

        "transfer": {
            "prompt": (
                f"{system} returns {code} "
                f"{transfer_task} "
                "What should the operator do?"
            ),
        },

        "task_grader": {
            "all_regex": (
                task_regex
            )
        },

        "fidelity_grader": {
            "all_regex": (
                task_regex
                + fidelity_extra
            )
        },
    }


def build_taskset():
    families = [

        # 01
        _family(
            id="xenonpay-a19",
            system="XenonPay",
            code="A19",
            experience_task=(
                "while capturing an invoice."
            ),
            transfer_task=(
                "while cancelling a subscription charge."
            ),
            rule=(
                "means wait 5 seconds, mint a new nonce, "
                "rotate the session token, retry exactly once "
                "with X-Xenon-Path: cobalt, and never reuse "
                "the prior nonce."
            ),
            task_regex=[
                [r"\b5\s*(?:seconds?|s)\b"],
                [r"\b(?:mint|minting|create|creating|generate|generating)\b.*\bnew\s+nonce\b"],
                [r"\b(?:rotate|rotating|refresh|refreshing)\b.*\bsession\s+token\b"],
                [r"\bretry\b.*\b(?:exactly\s+)?once\b"],
                [r"x-xenon-path.*cobalt"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breus(?:e|ing)?\b.*\b(?:prior|old)\s+nonce\b"
                ]
            ],
        ),

        # 02
        _family(
            id="birchqueue-r6",
            system="BirchQueue",
            code="R6",
            experience_task=(
                "while processing a document job."
            ),
            transfer_task=(
                "while processing a thumbnail job."
            ),
            rule=(
                "means obtain a new lease, move the job to "
                "the silver lane, requeue exactly twice, tag "
                "queue-mode=echo, and do not acknowledge the "
                "original dispatch."
            ),
            task_regex=[
                [r"\b(?:new|fresh)\s+lease\b"],
                [r"\bsilver\s+lane\b"],
                [r"\bre-?queue\b.*\b(?:twice|2\s+times?)\b"],
                [r"queue-mode\s*=\s*echo"],
            ],
            fidelity_extra=[
                [
                    r"(?:do\s+not|don.t|never)"
                    r".*\b(?:ack|acknowledge)\b"
                    r".*\boriginal\s+dispatch\b"
                ]
            ],
        ),

        # 03
        _family(
            id="prismstore-k27",
            system="PrismStore",
            code="K27",
            experience_task=(
                "while uploading a 120 MiB archive."
            ),
            transfer_task=(
                "while uploading a 60 MiB checkpoint."
            ),
            rule=(
                "requires a new upload session, multipart upload "
                "with 10 MiB chunks, CRC32C for every chunk, "
                "X-Prism-Final: jade on finalization, and never "
                "append to the previous upload session."
            ),
            task_regex=[
                [r"\b(?:new|fresh)\s+upload\s+session\b"],
                [r"\bmultipart\b"],
                [r"\b10\s*(?:mib|mb)\b"],
                [r"\bcrc32c\b"],
                [
                    r"\b(?:every|each|per)\b"
                    r".*\bchunks?\b"
                ],
                [r"x-prism-final.*jade"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bappend(?:ing)?\b.*\b(?:previous|old)"
                    r"\s+upload\s+session\b"
                ]
            ],
        ),

        # 04
        _family(
            id="meadowdb-q44",
            system="MeadowDB",
            code="Q44",
            experience_task=(
                "while writing an inventory update."
            ),
            transfer_task=(
                "while writing a pricing update."
            ),
            rule=(
                "means read the primary epoch, acquire the bronze "
                "lock, retry exactly once with X-Meadow-Epoch set "
                "to the primary epoch, and never increment the "
                "epoch locally."
            ),
            task_regex=[
                [
                    r"\b(?:read|reading|fetch|fetching|get|getting)\b"
                    r".*\bprimary\s+epoch\b"
                ],
                [r"\bbronze\s+lock\b"],
                [r"\bretry\b.*\b(?:exactly\s+)?once\b"],
                [r"x-meadow-epoch"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bincrement(?:ing)?\b.*\bepoch\b"
                    r".*\blocally\b"
                ]
            ],
        ),

        # 05
        _family(
            id="cobaltparser-u8",
            system="CobaltParser",
            code="U8",
            experience_task=(
                "with legacy state=J before schema validation."
            ),
            transfer_task=(
                "with legacy state=L before schema validation."
            ),
            rule=(
                "requires mapping J to hold, K to release, and "
                "L to review before normal schema validation, "
                "and the raw legacy state must never be validated."
            ),
            task_regex=[
                [r"\bl\b.*\breview\b"],
                [
                    r"\bbefore\b.*\b(?:schema\s+)?validation\b",
                    r"\bthen\b.*\bvalidat"
                ],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|must\s+not)"
                    r".*\bvalidat"
                    r".*\braw\s+legacy\s+state\b",
                    r"\braw\s+legacy\s+state\b"
                    r".*(?:never|do\s+not|must\s+not)"
                    r".*\bvalidat"
                ]
            ],
        ),

        # 06
        _family(
            id="solarrpc-d63",
            system="SolarRPC",
            code="D63",
            experience_task=(
                "during a customer-profile request."
            ),
            transfer_task=(
                "during an order-history request."
            ),
            rule=(
                "requires exactly three heartbeat frames 300 ms "
                "apart, then a new channel with a fresh correlation "
                "ID and X-Solar-Recover: d63; never reuse the prior "
                "correlation ID."
            ),
            task_regex=[
                [
                    r"(?:exactly\s+)?(?:three|3)"
                    r"\s+heartbeat"
                ],
                [r"\b300\s*(?:ms|milliseconds?)\b"],
                [r"\b(?:new|fresh)\s+channel\b"],
                [
                    r"\b(?:fresh|new)"
                    r"\s+correlation\s+id\b"
                ],
                [r"x-solar-recover.*d63"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breus(?:e|ing)?\b.*\b(?:prior|old)"
                    r"\s+correlation\s+id\b"
                ]
            ],
        ),

        # 07
        _family(
            id="willowcache-t5",
            system="WillowCache",
            code="T5",
            experience_task=(
                "while refreshing a script asset."
            ),
            transfer_task=(
                "while refreshing a stylesheet asset."
            ),
            rule=(
                "requires one HEAD request to origin, purge only "
                "the current zone shard, wait 6 seconds, issue one "
                "GET with X-Willow-Probe: 4, and never perform a "
                "global purge."
            ),
            task_regex=[
                [r"\b(?:one|1)\s+head\s+request\b"],
                [
                    r"\bpurge\b.*\bonly\b"
                    r".*\bcurrent\s+zone\s+shard\b"
                ],
                [r"\b6\s*(?:seconds?|s)\b"],
                [r"\b(?:one|1)\s+get\b"],
                [r"x-willow-probe.*4"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bglobal\s+purge\b"
                ]
            ],
        ),

        # 08
        _family(
            id="ironflow-p21",
            system="IronFlow",
            code="P21",
            experience_task=(
                "during invoice reconciliation."
            ),
            transfer_task=(
                "during payroll export."
            ),
            rule=(
                "requires cloning the latest checkpoint, marking "
                "the old run stale, restarting from the previous "
                "boundary exactly once with token p21-safe, and "
                "never resuming the failed step directly."
            ),
            task_regex=[
                [
                    r"\bclon(?:e|ing)"
                    r".*\blatest\s+checkpoint\b"
                ],
                [
                    r"\bmark(?:ing)?\b"
                    r".*\bold\s+run\b.*\bstale\b"
                ],
                [
                    r"\brestart"
                    r".*\bprevious\s+boundary\b"
                    r".*\b(?:exactly\s+)?once\b"
                ],
                [r"p21-safe"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bresum"
                    r".*\bfailed\s+step\b"
                ]
            ],
        ),

        # 09
        _family(
            id="novaindex-b14",
            system="NovaIndex",
            code="B14",
            experience_task=(
                "during catalog indexing."
            ),
            transfer_task=(
                "during customer indexing."
            ),
            rule=(
                "requires fetching a new cursor, switching to "
                "delta-read mode, replaying exactly two pages, "
                "setting X-Nova-Cursor: fresh, and never rewinding "
                "the old cursor."
            ),
            task_regex=[
                [r"\b(?:new|fresh)\s+cursor\b"],
                [r"\bdelta-read\b", r"\bdelta\s+read\b"],
                [
                    r"\breplay"
                    r".*\b(?:two|2)\s+pages?\b"
                ],
                [r"x-nova-cursor.*fresh"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\brewind(?:ing)?\b.*\b(?:old|prior)\s+cursor\b"
                ]
            ],
        ),

        # 10
        _family(
            id="mintledger-f32",
            system="MintLedger",
            code="F32",
            experience_task=(
                "while writing a settlement."
            ),
            transfer_task=(
                "while writing a rebate."
            ),
            rule=(
                "requires requesting the server nonce, acquiring "
                "the blue lock, retrying exactly twice with "
                "X-Mint-Nonce set to that server nonce, and never "
                "synthesizing a nonce locally."
            ),
            task_regex=[
                [
                    r"\b(?:request|requesting|get|getting|fetch|fetching)\b"
                    r".*\bserver\s+nonce\b"
                ],
                [r"\bblue\s+lock\b"],
                [
                    r"\bretry"
                    r".*\b(?:exactly\s+)?(?:twice|2\s+times?)\b"
                ],
                [r"x-mint-nonce"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bsynthesi[sz]"
                    r".*\bnonce\b.*\blocally\b"
                ]
            ],
        ),

        # 11
        _family(
            id="coralbus-y7",
            system="CoralBus",
            code="Y7",
            experience_task=(
                "while consuming an invoice event."
            ),
            transfer_task=(
                "while consuming an audit event."
            ),
            rule=(
                "requires a fresh checkpoint, replay exactly once "
                "from it with Replay-Class: coral, and never "
                "acknowledge the original message."
            ),
            task_regex=[
                [r"\b(?:fresh|new)\s+checkpoint\b"],
                [r"\breplay\b.*\b(?:exactly\s+)?once\b"],
                [r"replay-class.*coral"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\b(?:ack|acknowledge)"
                    r".*\boriginal\s+message\b"
                ]
            ],
        ),

        # 12
        _family(
            id="summitstore-w18",
            system="SummitStore",
            code="W18",
            experience_task=(
                "while uploading a 200 MiB backup."
            ),
            transfer_task=(
                "while uploading a 100 MiB snapshot."
            ),
            rule=(
                "requires a new upload ID, multipart upload using "
                "20 MiB chunks, SHA-512 for every chunk, "
                "X-Summit-Manifest: frost on finalization, and "
                "never reuse the previous upload ID."
            ),
            task_regex=[
                [r"\b(?:new|fresh)\s+upload\s+id\b"],
                [r"\bmultipart\b"],
                [r"\b20\s*(?:mib|mb)\b"],
                [r"\bsha-?512\b"],
                [
                    r"\b(?:every|each|per)"
                    r".*\bchunks?\b"
                ],
                [r"x-summit-manifest.*frost"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breus(?:e|ing)?\b.*\b(?:previous|old)"
                    r"\s+upload\s+id\b"
                ]
            ],
        ),

        # 13
        _family(
            id="emberdb-s29",
            system="EmberDB",
            code="S29",
            experience_task=(
                "during a balance query."
            ),
            transfer_task=(
                "during an inventory query."
            ),
            rule=(
                "requires refreshing the schema token, switching "
                "to snapshot mode, retrying exactly once while "
                "preserving the original request ID, and never "
                "reconnecting the session."
            ),
            task_regex=[
                [
                    r"\brefresh(?:ing)?\b"
                    r".*\bschema\s+token\b"
                ],
                [r"\bsnapshot\b"],
                [r"\bretry(?:ing)?\b.*\b(?:exactly\s+)?once\b"],
                [
                    r"\bpreserv"
                    r".*\boriginal\s+request\s+id\b"
                ],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breconnect(?:ing)?\b"
                    r".*\bsession\b"
                ]
            ],
        ),

        # 14
        _family(
            id="quillrpc-g12",
            system="QuillRPC",
            code="G12",
            experience_task=(
                "during a profile RPC."
            ),
            transfer_task=(
                "during a billing RPC."
            ),
            rule=(
                "requires exactly two heartbeat frames 175 ms "
                "apart, then a fresh channel carrying "
                "X-Quill-Recover: g12, and never reuse the "
                "previous stream ID."
            ),
            task_regex=[
                [
                    r"(?:exactly\s+)?(?:two|2)"
                    r"\s+heartbeat"
                ],
                [r"\b175\s*(?:ms|milliseconds?)\b"],
                [r"\b(?:fresh|new)\s+channel\b"],
                [r"x-quill-recover.*g12"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breus(?:e|ing)?\b.*\b(?:previous|old)"
                    r"\s+stream\s+id\b"
                ]
            ],
        ),

        # 15
        _family(
            id="harborqueue-n41",
            system="HarborQueue",
            code="N41",
            experience_task=(
                "for a report-generation job."
            ),
            transfer_task=(
                "for a media-processing job."
            ),
            rule=(
                "requires minting a new dispatch ID, moving the "
                "job to the teal lane, requeueing exactly once, "
                "tagging dispatch-mode=restored, and never "
                "acknowledging the original dispatch."
            ),
            task_regex=[
                [
                    r"\b(?:mint|minting|create|creating|generate|generating)"
                    r".*\bnew\s+dispatch\s+id\b"
                ],
                [r"\bteal\s+lane\b"],
                [r"\bre-?queue.*\b(?:exactly\s+)?once\b"],
                [r"dispatch-mode\s*=\s*restored"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\b(?:ack|acknowledge)"
                    r".*\boriginal\s+dispatch\b"
                ]
            ],
        ),

        # 16
        _family(
            id="pinecdn-c26",
            system="PineCDN",
            code="C26",
            experience_task=(
                "while refreshing a JavaScript asset."
            ),
            transfer_task=(
                "while refreshing an image asset."
            ),
            rule=(
                "requires one HEAD request, purging only the "
                "current POP shard, waiting 8 seconds, then one "
                "GET carrying X-Pine-Probe: 2, and never issuing "
                "a global purge."
            ),
            task_regex=[
                [r"\b(?:one|1)\s+head\s+request\b"],
                [
                    r"\bpurg(?:e|ing)"
                    r".*\bonly\b"
                    r".*\bcurrent\s+pop\s+shard\b"
                ],
                [r"\b8\s*(?:seconds?|s)\b"],
                [r"\b(?:one|1)\s+get\b"],
                [r"x-pine-probe.*2"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bglobal\s+purge\b"
                ]
            ],
        ),

        # 17
        _family(
            id="orbitflow-v15",
            system="OrbitFlow",
            code="V15",
            experience_task=(
                "during invoice export."
            ),
            transfer_task=(
                "during analytics export."
            ),
            rule=(
                "requires cloning the latest checkpoint, marking "
                "the old run superseded, restarting from the prior "
                "boundary exactly once with token v15-safe, and "
                "never resuming the failed node directly."
            ),
            task_regex=[
                [
                    r"\bclon(?:e|ing)"
                    r".*\blatest\s+checkpoint\b"
                ],
                [
                    r"\bmark"
                    r".*\bold\s+run\b"
                    r".*\bsuperseded\b"
                ],
                [
                    r"\brestart"
                    r".*\b(?:prior|previous)\s+boundary\b"
                    r".*\b(?:exactly\s+)?once\b"
                ],
                [r"v15-safe"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\bresum"
                    r".*\bfailed\s+node\b"
                ]
            ],
        ),

        # 18
        _family(
            id="tulipparser-m9",
            system="TulipParser",
            code="M9",
            experience_task=(
                "with legacy state=X before validation."
            ),
            transfer_task=(
                "with legacy state=Z before validation."
            ),
            rule=(
                "requires mapping X to queued, Y to blocked, "
                "and Z to ready before normal validation; never "
                "validate the raw legacy state."
            ),
            task_regex=[
                [r"\bz\b.*\bready\b"],
                [
                    r"\bbefore\b.*\bvalidation\b",
                    r"\bthen\b.*\bvalidat"
                ],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|must\s+not)"
                    r".*\bvalidat"
                    r".*\braw\s+legacy\s+state\b"
                ]
            ],
        ),

        # 19
        _family(
            id="glacierpay-h34",
            system="GlacierPay",
            code="H34",
            experience_task=(
                "while capturing an order payment."
            ),
            transfer_task=(
                "while issuing an order refund."
            ),
            rule=(
                "means wait 11 seconds, rotate the session key, "
                "mint a new idempotency key, retry exactly twice "
                "with X-Glacier-Mode: white, and never reuse the "
                "old idempotency key."
            ),
            task_regex=[
                [r"\b11\s*(?:seconds?|s)\b"],
                [
                    r"\b(?:rotate|rotating|refresh|refreshing)"
                    r".*\bsession\s+key\b"
                ],
                [
                    r"\b(?:mint|minting|create|creating|generate|generating)"
                    r".*\bnew\s+idempotency\s+key\b"
                ],
                [
                    r"\bretry"
                    r".*\b(?:exactly\s+)?(?:twice|2\s+times?)\b"
                ],
                [r"x-glacier-mode.*white"],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breus(?:e|ing)?\b.*\b(?:old|prior)"
                    r"\s+idempotency\s+key\b"
                ]
            ],
        ),

        # 20
        _family(
            id="velvetindex-j28",
            system="VelvetIndex",
            code="J28",
            experience_task=(
                "during product search."
            ),
            transfer_task=(
                "during account search."
            ),
            rule=(
                "requires fetching a fresh cursor from the leader, "
                "switching to shadow-read, retrying exactly once "
                "while preserving the original query ID, and never "
                "reopening the old snapshot."
            ),
            task_regex=[
                [
                    r"\b(?:fresh|new)\s+cursor\b"
                    r".*\bleader\b",
                    r"\bleader\b"
                    r".*\b(?:fresh|new)\s+cursor\b"
                ],
                [
                    r"\bshadow-read\b",
                    r"\bshadow\s+read\b"
                ],
                [r"\bretry(?:ing)?\b.*\b(?:exactly\s+)?once\b"],
                [
                    r"\bpreserv"
                    r".*\boriginal\s+query\s+id\b"
                ],
            ],
            fidelity_extra=[
                [
                    r"(?:never|do\s+not|don.t)"
                    r".*\breopen(?:ing)?\b"
                    r".*\b(?:old|previous)\s+snapshot\b"
                ]
            ],
        ),
    ]

    return {
        "experiment": (
            "seed-growth-004"
        ),

        "classification": (
            "exploratory-fresh-ablation"
        ),

        "hypothesis": (
            "Persistent experience improves task performance, "
            "and a targeted constraint-fidelity instruction "
            "reduces loss between recalled memory and decisions."
        ),

        "families": families,
    }


def main():
    output = Path(
        "experiments/tasks_004.json"
    )

    payload = build_taskset()

    output.write_text(
        json.dumps(
            payload,
            indent=2,
        )
        + "\n"
    )

    print(
        f"Wrote {len(payload['families'])} "
        f"families to {output}"
    )


if __name__ == "__main__":
    main()
