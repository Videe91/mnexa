from __future__ import annotations

import json

from pathlib import Path


def _family(
    *,
    id,
    system,
    code,
    experience,
    transfer,
    candidate,
    correction,
    required,
    contamination,
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
                f"{experience} "
                "What should the operator do?"
            )
        },

        "transfer": {
            "prompt": (
                f"{system} returns {code} "
                f"{transfer} "
                "What should the operator do?"
            )
        },

        "candidate_decision": (
            candidate
        ),

        "correction": (
            correction
        ),

        "correct_grader": {
            "all_regex": [
                [pattern]
                for pattern
                in required
            ]
        },

        "contamination_regex": (
            contamination
        ),
    }


def build_taskset():

    families = [

        _family(
            id="asterpay-px77",
            system="AsterPay",
            code="PX-77",
            experience="while capturing an invoice payment.",
            transfer="while cancelling a subscription charge.",
            candidate=(
                "Restart the payment service, clear the local cache, "
                "and then retry the request."
            ),
            correction=(
                "PX-77 requires refreshing the recovery lease, "
                "waiting 4 seconds, retrying exactly once, and "
                "including X-Aster-Recover: blue."
            ),
            required=[
                r"refresh.*recovery\s+lease",
                r"\b4\s*seconds?\b",
                r"retry.*exactly\s+once",
                r"x-aster-recover.*blue",
            ],
            contamination=[
                r"restart.*payment\s+service",
                r"clear.*local\s+cache",
            ],
        ),

        _family(
            id="granitequeue-l13",
            system="GraniteQueue",
            code="L13",
            experience="while processing a document job.",
            transfer="while processing a thumbnail job.",
            candidate=(
                "Delete the original message and restart the worker."
            ),
            correction=(
                "L13 requires requesting a fresh checkpoint, "
                "moving the job to the amber lane, replaying "
                "exactly once from that checkpoint, and using "
                "Replay-Class: granite."
            ),
            required=[
                r"fresh\s+checkpoint",
                r"amber\s+lane",
                r"replay.*exactly\s+once",
                r"replay-class.*granite",
            ],
            contamination=[
                r"delete.*original\s+message",
                r"restart.*worker",
            ],
        ),

        _family(
            id="ivorystore-c48",
            system="IvoryStore",
            code="C48",
            experience="while uploading a 96 MiB archive.",
            transfer="while uploading a 64 MiB checkpoint.",
            candidate=(
                "Compress the file and retry using a single-part upload."
            ),
            correction=(
                "C48 requires a new upload session, multipart upload "
                "with 8 MiB chunks, SHA3-256 for every chunk, and "
                "X-Ivory-Final: strict on finalization."
            ),
            required=[
                r"new\s+upload\s+session",
                r"multipart",
                r"\b8\s*(?:mib|mb)\b",
                r"sha3-?256",
                r"(?:every|each|per).*chunk",
                r"x-ivory-final.*strict",
            ],
            contamination=[
                r"compress.*file",
                r"single[-\s]+part",
            ],
        ),

        _family(
            id="amberdb-t22",
            system="AmberDB",
            code="T22",
            experience="while writing an inventory update.",
            transfer="while writing a pricing update.",
            candidate=(
                "Restart the database node and synthesize a new "
                "epoch locally before retrying."
            ),
            correction=(
                "T22 requires reading the primary epoch, acquiring "
                "the violet lock, and retrying exactly once with "
                "X-Amber-Epoch set to the primary epoch."
            ),
            required=[
                r"read.*primary\s+epoch",
                r"violet\s+lock",
                r"retry.*exactly\s+once",
                r"x-amber-epoch.*primary\s+epoch",
            ],
            contamination=[
                r"restart.*database",
                r"synthesi[sz].*epoch",
            ],
        ),

        _family(
            id="marshparser-v3",
            system="MarshParser",
            code="V3",
            experience="with legacy state=A before validation.",
            transfer="with legacy state=C before validation.",
            candidate=(
                "Drop the legacy state field and validate the "
                "remaining payload."
            ),
            correction=(
                "V3 requires mapping A to ready, B to hold, and "
                "C to reject before normal schema validation."
            ),
            required=[
                r"\bc\b.*\breject",
                r"before.*(?:schema\s+)?validation",
            ],
            contamination=[
                r"drop.*legacy\s+state",
                r"remove.*state\s+field",
            ],
        ),

        _family(
            id="orbitrpc-n64",
            system="OrbitRPC",
            code="N64",
            experience="during a customer-profile request.",
            transfer="during an order-history request.",
            candidate=(
                "Close the connection and reuse the prior "
                "correlation ID on reconnect."
            ),
            correction=(
                "N64 requires exactly two heartbeat frames "
                "220 ms apart, then a new channel with a fresh "
                "correlation ID and X-Orbit-Recover: n64."
            ),
            required=[
                r"(?:two|2)\s+heartbeat",
                r"\b220\s*(?:ms|milliseconds?)\b",
                r"new\s+channel",
                r"fresh\s+correlation\s+id",
                r"x-orbit-recover.*n64",
            ],
            contamination=[
                r"close.*connection",
                r"reuse.*correlation\s+id",
            ],
        ),

        _family(
            id="sprucecdn-b51",
            system="SpruceCDN",
            code="B51",
            experience="while refreshing a script asset.",
            transfer="while refreshing a stylesheet asset.",
            candidate=(
                "Perform a global purge and restart the edge service."
            ),
            correction=(
                "B51 requires one HEAD request to origin, purging "
                "only the current region shard, waiting 5 seconds, "
                "then issuing one GET with X-Spruce-Probe: 3."
            ),
            required=[
                r"(?:one|1)\s+head\s+request",
                r"only.*current\s+region\s+shard",
                r"\b5\s*seconds?\b",
                r"(?:one|1)\s+get",
                r"x-spruce-probe.*3",
            ],
            contamination=[
                r"global\s+purge",
                r"restart.*edge\s+service",
            ],
        ),

        _family(
            id="quartzflow-r27",
            system="QuartzFlow",
            code="R27",
            experience="during invoice reconciliation.",
            transfer="during payroll export.",
            candidate=(
                "Resume the failed step directly and keep using "
                "the same checkpoint."
            ),
            correction=(
                "R27 requires cloning the latest checkpoint, "
                "marking the old run superseded, restarting from "
                "the previous boundary exactly once, and carrying "
                "token r27-safe."
            ),
            required=[
                r"clon(?:e|ing).*latest\s+checkpoint",
                r"old\s+run.*superseded",
                r"restart.*previous\s+boundary.*exactly\s+once",
                r"r27-safe",
            ],
            contamination=[
                r"resume.*failed\s+step",
                r"keep.*same\s+checkpoint",
            ],
        ),

        _family(
            id="jadeindex-x11",
            system="JadeIndex",
            code="X11",
            experience="during catalog indexing.",
            transfer="during customer indexing.",
            candidate=(
                "Rebuild the entire index and discard the existing cursor."
            ),
            correction=(
                "X11 requires fetching a fresh cursor from the leader, "
                "switching to delta-read, replaying exactly two pages, "
                "and setting X-Jade-Cursor: fresh."
            ),
            required=[
                r"fresh\s+cursor.*leader",
                r"delta[-\s]read",
                r"replay.*(?:two|2)\s+pages",
                r"x-jade-cursor.*fresh",
            ],
            contamination=[
                r"rebuild.*entire\s+index",
                r"discard.*cursor",
            ],
        ),

        _family(
            id="silverledger-a42",
            system="SilverLedger",
            code="A42",
            experience="while posting a settlement.",
            transfer="while posting a rebate.",
            candidate=(
                "Synthesize a nonce locally and bypass the lock "
                "before retrying."
            ),
            correction=(
                "A42 requires requesting the server nonce, acquiring "
                "the blue lock, retrying exactly twice, and setting "
                "X-Silver-Nonce to the server nonce."
            ),
            required=[
                r"(?:request|fetch|get).*server\s+nonce",
                r"blue\s+lock",
                r"retry.*(?:exactly\s+)?twice",
                r"x-silver-nonce.*server\s+nonce",
            ],
            contamination=[
                r"synthesi[sz].*nonce",
                r"bypass.*lock",
            ],
        ),

        _family(
            id="maplebus-e16",
            system="MapleBus",
            code="E16",
            experience="while consuming an invoice event.",
            transfer="while consuming an audit event.",
            candidate=(
                "Acknowledge the original event and retry the same message."
            ),
            correction=(
                "E16 requires requesting a fresh checkpoint, "
                "replaying exactly once from that checkpoint, and "
                "using Replay-Class: maple."
            ),
            required=[
                r"fresh\s+checkpoint",
                r"replay.*exactly\s+once",
                r"replay-class.*maple",
            ],
            contamination=[
                r"acknowledge.*original",
                r"retry.*same\s+message",
            ],
        ),

        _family(
            id="froststore-m55",
            system="FrostStore",
            code="M55",
            experience="while uploading a 200 MiB backup.",
            transfer="while uploading a 100 MiB snapshot.",
            candidate=(
                "Reuse the previous upload ID and send the file "
                "as one large single part."
            ),
            correction=(
                "M55 requires a new upload ID, multipart upload "
                "with 20 MiB chunks, SHA-512 for every chunk, and "
                "X-Frost-Manifest: ice on finalization."
            ),
            required=[
                r"new\s+upload\s+id",
                r"multipart",
                r"\b20\s*(?:mib|mb)\b",
                r"sha-?512",
                r"(?:every|each|per).*chunk",
                r"x-frost-manifest.*ice",
            ],
            contamination=[
                r"reuse.*upload\s+id",
                r"single\s+part",
            ],
        ),

        _family(
            id="cinderdb-h8",
            system="CinderDB",
            code="H8",
            experience="during a customer-balance query.",
            transfer="during an inventory query.",
            candidate=(
                "Reconnect the session and generate a new request ID."
            ),
            correction=(
                "H8 requires refreshing the schema token, switching "
                "to snapshot-read, retrying exactly once, and "
                "preserving the original request ID."
            ),
            required=[
                r"refresh.*schema\s+token",
                r"snapshot[-\s]read",
                r"retry.*exactly\s+once",
                r"preserv.*original\s+request\s+id",
            ],
            contamination=[
                r"reconnect.*session",
                r"(?:generate|create).*new\s+request\s+id",
            ],
        ),

        _family(
            id="pearlrpc-j33",
            system="PearlRPC",
            code="J33",
            experience="during a profile RPC.",
            transfer="during a billing RPC.",
            candidate=(
                "Reuse the previous stream ID and restart the RPC service."
            ),
            correction=(
                "J33 requires exactly three heartbeat frames "
                "180 ms apart, then a fresh channel carrying "
                "X-Pearl-Recover: j33."
            ),
            required=[
                r"(?:three|3)\s+heartbeat",
                r"\b180\s*(?:ms|milliseconds?)\b",
                r"fresh\s+channel",
                r"x-pearl-recover.*j33",
            ],
            contamination=[
                r"reuse.*stream\s+id",
                r"restart.*rpc\s+service",
            ],
        ),

        _family(
            id="oakqueue-s72",
            system="OakQueue",
            code="S72",
            experience="for a report-generation job.",
            transfer="for a media-processing job.",
            candidate=(
                "Cancel the job and delete the existing dispatch record."
            ),
            correction=(
                "S72 requires minting a new dispatch ID, moving "
                "the job to the teal lane, requeueing exactly once, "
                "and tagging dispatch-mode=restored."
            ),
            required=[
                r"(?:mint|create|generate).*new\s+dispatch\s+id",
                r"teal\s+lane",
                r"re-?queue.*exactly\s+once",
                r"dispatch-mode\s*=\s*restored",
            ],
            contamination=[
                r"cancel.*job",
                r"delete.*dispatch\s+record",
            ],
        ),

        _family(
            id="cloudcdn-k25",
            system="CloudCDN",
            code="K25",
            experience="while refreshing a JavaScript asset.",
            transfer="while refreshing an image asset.",
            candidate=(
                "Purge all regions and invalidate all cached assets."
            ),
            correction=(
                "K25 requires one HEAD request, purging only the "
                "current POP shard, waiting 9 seconds, then one GET "
                "with X-Cloud-Probe: 7."
            ),
            required=[
                r"(?:one|1)\s+head\s+request",
                r"only.*current\s+pop\s+shard",
                r"\b9\s*seconds?\b",
                r"(?:one|1)\s+get",
                r"x-cloud-probe.*7",
            ],
            contamination=[
                r"purge.*all\s+regions",
                r"invalidate.*all.*assets",
            ],
        ),

        _family(
            id="deltaflow-z19",
            system="DeltaFlow",
            code="Z19",
            experience="during invoice export.",
            transfer="during analytics export.",
            candidate=(
                "Restart the entire workflow from the beginning "
                "and discard the current checkpoint."
            ),
            correction=(
                "Z19 requires cloning the latest checkpoint, marking "
                "the old run stale, restarting from the previous "
                "boundary exactly once, and carrying token z19-safe."
            ),
            required=[
                r"clon(?:e|ing).*latest\s+checkpoint",
                r"old\s+run.*stale",
                r"restart.*previous\s+boundary.*exactly\s+once",
                r"z19-safe",
            ],
            contamination=[
                r"restart.*entire\s+workflow",
                r"discard.*checkpoint",
            ],
        ),

        _family(
            id="violetparser-q7",
            system="VioletParser",
            code="Q7",
            experience="with legacy state=X before validation.",
            transfer="with legacy state=Z before validation.",
            candidate=(
                "Drop the state field and default the record to approved."
            ),
            correction=(
                "Q7 requires mapping X to queued, Y to blocked, "
                "and Z to ready before normal validation."
            ),
            required=[
                r"\bz\b.*\bready\b",
                r"before.*validation",
            ],
            contamination=[
                r"drop.*state\s+field",
                r"default.*approved",
            ],
        ),

        _family(
            id="northpay-f61",
            system="NorthPay",
            code="F61",
            experience="while capturing an order payment.",
            transfer="while issuing a subscription adjustment.",
            candidate=(
                "Refund the customer immediately and reverse the charge."
            ),
            correction=(
                "F61 requires waiting 12 seconds, rotating the "
                "session key, minting a new idempotency key, retrying "
                "exactly twice, and using X-North-Mode: silver."
            ),
            required=[
                r"\b12\s*seconds?\b",
                r"rotat.*session\s+key",
                r"(?:mint|create|generate).*new\s+idempotency\s+key",
                r"retry.*(?:exactly\s+)?twice",
                r"x-north-mode.*silver",
            ],
            contamination=[
                r"refund.*customer",
                r"reverse.*charge",
            ],
        ),

        _family(
            id="copperindex-w29",
            system="CopperIndex",
            code="W29",
            experience="during product search.",
            transfer="during account search.",
            candidate=(
                "Delete the current snapshot and rebuild the search index."
            ),
            correction=(
                "W29 requires fetching a fresh cursor from the leader, "
                "switching to shadow-read, retrying exactly once, and "
                "preserving the original query ID."
            ),
            required=[
                r"fresh\s+cursor.*leader",
                r"shadow[-\s]read",
                r"retry.*exactly\s+once",
                r"preserv.*original\s+query\s+id",
            ],
            contamination=[
                r"delete.*snapshot",
                r"rebuild.*search\s+index",
            ],
        ),
    ]

    return {
        "experiment": (
            "seed-growth-005"
        ),

        "classification": (
            "exploratory-fresh-"
            "consolidation-ablation"
        ),

        "hypothesis": (
            "Evidence-disciplined consolidation reduces "
            "the propagation of unsupported content from "
            "failed decisions while retaining knowledge "
            "grounded by authoritative corrections."
        ),

        "fixture": (
            "Each family contains a controlled failed "
            "decision plus an authoritative correction. "
            "Conditions B and C receive identical source "
            "evidence and differ only in consolidation policy."
        ),

        "families": (
            families
        ),
    }


def main():

    output = Path(
        "experiments/tasks_005.json"
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
        f"Wrote "
        f"{len(payload['families'])} "
        f"families to {output}"
    )


if __name__ == "__main__":
    main()
