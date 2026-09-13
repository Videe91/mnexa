from __future__ import annotations

import json

from pathlib import Path


def _atom(
    evidence_id,
    text,
    task_pattern,
):
    return {
        "id": evidence_id,
        "text": text,
        "source_quote": text,
        "task_pattern": task_pattern,
    }


def _family(
    *,
    id,
    system,
    code,
    experience,
    transfer,
    candidate,
    atoms,
    contamination,
    candidate_bad_claim=None,
):
    correction = (
        f"{code} authoritative correction: "
        + " ".join(atom["text"] for atom in atoms)
    )

    bad_claim_text = (
        candidate_bad_claim
        if candidate_bad_claim
        else candidate.split(".")[0] + "."
    )

    return {
        "id": id,

        "entities": [
            f"system:{system.lower()}",
            f"code:{code.lower()}",
        ],

        "experience": {
            "prompt": (
                f"{system} returns {code} {experience} "
                "What should the operator do?"
            )
        },

        "transfer": {
            "prompt": (
                f"{system} returns {code} {transfer} "
                "What should the operator do?"
            )
        },

        "candidate_decision": candidate,

        "correction": correction,

        "oracle_evidence_atoms": atoms,

        "adversarial_atom_challenges": [
            {
                "text": bad_claim_text,
                "source_quote": bad_claim_text,
            },
            {
                "text": bad_claim_text,
                "source_quote": atoms[0]["text"],
            },
        ],

        "correct_grader": {
            "all_regex": [
                [atom["task_pattern"]]
                for atom in atoms
            ]
        },

        "transfer_grader": {
            "all_regex": [
                [atom["task_pattern"]]
                for atom in atoms
            ]
        },

        "contamination_regex": contamination,
    }


def build_taskset():
    families = [
        _family(
            id="lumenpay-kx31-007",
            system="LumenPay",
            code="KX-31",
            experience="while capturing an invoice payment.",
            transfer="while cancelling a subscription charge.",
            candidate="Restart the payment service and clear the local cache.",
            atoms=[
                _atom(
                    "E1",
                    "Refresh the recovery lease.",
                    r"refresh.*recovery\s+lease",
                ),
                _atom(
                    "E2",
                    "Wait 6 seconds.",
                    r"\b6\s*seconds?\b",
                ),
                _atom(
                    "E3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Include X-Lumen-Recover: amber.",
                    r"x-lumen-recover.*amber",
                ),
            ],
            contamination=[
                r"restart.*payment\s+service",
                r"clear.*local\s+cache",
            ],
        ),

        _family(
            id="ashqueue-d14-007",
            system="AshQueue",
            code="D14",
            experience="while processing a document job.",
            transfer="while processing a thumbnail job.",
            candidate="Delete the original message and restart the worker.",
            atoms=[
                _atom(
                    "E1",
                    "Request a fresh checkpoint.",
                    r"(?:request|obtain).*fresh\s+checkpoint",
                ),
                _atom(
                    "E2",
                    "Move the job to the gold lane.",
                    r"gold\s+lane",
                ),
                _atom(
                    "E3",
                    "Replay exactly once from the checkpoint.",
                    r"replay.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Use Replay-Class: ash.",
                    r"replay-class.*ash",
                ),
            ],
            contamination=[
                r"delete.*original\s+message",
                r"restart.*worker",
            ],
        ),

        _family(
            id="onyxstore-r62-007",
            system="OnyxStore",
            code="R62",
            experience="while uploading a 108 MiB archive.",
            transfer="while uploading a 72 MiB checkpoint.",
            candidate="Compress the file and use a single-part upload.",
            atoms=[
                _atom(
                    "E1",
                    "Start a new upload session.",
                    r"new\s+upload\s+session",
                ),
                _atom(
                    "E2",
                    "Use multipart upload with 9 MiB chunks.",
                    r"multipart.*9\s*(?:mib|mb)",
                ),
                _atom(
                    "E3",
                    "Attach BLAKE2b to every chunk.",
                    r"blake2b.*(?:every|each|per).*chunk",
                ),
                _atom(
                    "E4",
                    "Include X-Onyx-Final: strict on finalization.",
                    r"x-onyx-final.*strict",
                ),
            ],
            contamination=[
                r"compress.*file",
                r"single[-\s]+part",
            ],
        ),

        _family(
            id="ferndb-p73-007",
            system="FernDB",
            code="P73",
            experience="while writing an inventory update.",
            transfer="while writing a pricing update.",
            candidate="Restart the database node and increment the epoch locally.",
            atoms=[
                _atom(
                    "E1",
                    "Read the primary epoch.",
                    r"read.*primary\s+epoch",
                ),
                _atom(
                    "E2",
                    "Acquire the copper lock.",
                    r"copper\s+lock",
                ),
                _atom(
                    "E3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Set X-Fern-Epoch to the primary epoch.",
                    r"x-fern-epoch.*primary\s+epoch",
                ),
            ],
            contamination=[
                r"restart.*database",
                r"increment.*epoch.*locally",
            ],
        ),

        _family(
            id="sableparser-m4-007",
            system="SableParser",
            code="M4",
            experience="with legacy state=A before validation.",
            transfer="with legacy state=C before validation.",
            candidate="Drop the state field and default the record to approved.",
            atoms=[
                _atom(
                    "E1",
                    "Map A to hold.",
                    r"\ba\b.*\bhold\b",
                ),
                _atom(
                    "E2",
                    "Map B to release.",
                    r"\bb\b.*\brelease\b",
                ),
                _atom(
                    "E3",
                    "Map C to review.",
                    r"\bc\b.*\breview\b",
                ),
                _atom(
                    "E4",
                    "Perform the mapping before normal validation.",
                    r"before.*normal\s+validation",
                ),
            ],
            contamination=[
                r"drop.*state\s+field",
                r"default.*approved",
            ],
        ),

        _family(
            id="horizonrpc-q28-007",
            system="HorizonRPC",
            code="Q28",
            experience="during a customer-profile request.",
            transfer="during an order-history request.",
            candidate="Close the connection and reuse the old correlation ID.",
            atoms=[
                _atom(
                    "E1",
                    "Send exactly two heartbeat frames.",
                    r"(?:two|2)\s+heartbeat",
                ),
                _atom(
                    "E2",
                    "Space the heartbeat frames 240 ms apart.",
                    r"\b240\s*(?:ms|milliseconds?)\b",
                ),
                _atom(
                    "E3",
                    "Open a new channel with a fresh correlation ID.",
                    r"new\s+channel.*fresh\s+correlation\s+id",
                ),
                _atom(
                    "E4",
                    "Include X-Horizon-Recover: q28.",
                    r"x-horizon-recover.*q28",
                ),
            ],
            contamination=[
                r"close.*connection",
                r"reuse.*correlation\s+id",
            ],
        ),

        _family(
            id="borealcdn-l52-007",
            system="BorealCDN",
            code="L52",
            experience="while refreshing a JavaScript asset.",
            transfer="while refreshing a stylesheet asset.",
            candidate="Perform a global purge and restart the edge service.",
            atoms=[
                _atom(
                    "E1",
                    "Issue one HEAD request to origin.",
                    r"(?:one|1)\s+head\s+request",
                ),
                _atom(
                    "E2",
                    "Purge only the current zone shard.",
                    r"purge.*only.*current\s+zone\s+shard",
                ),
                _atom(
                    "E3",
                    "Wait 7 seconds.",
                    r"\b7\s*seconds?\b",
                ),
                _atom(
                    "E4",
                    "Issue one GET with X-Boreal-Probe: 5.",
                    r"(?:one|1)\s+get.*x-boreal-probe.*5",
                ),
            ],
            contamination=[
                r"global\s+purge",
                r"restart.*edge\s+service",
            ],
        ),

        _family(
            id="echoflow-t19-007",
            system="EchoFlow",
            code="T19",
            experience="during invoice reconciliation.",
            transfer="during payroll export.",
            candidate="Resume the failed step directly and keep using the same checkpoint.",
            atoms=[
                _atom(
                    "E1",
                    "Clone the latest checkpoint.",
                    r"clone.*latest\s+checkpoint",
                ),
                _atom(
                    "E2",
                    "Mark the old run stale.",
                    r"old\s+run.*stale",
                ),
                _atom(
                    "E3",
                    "Restart from the previous boundary exactly once.",
                    r"restart.*previous\s+boundary.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Carry token t19-safe.",
                    r"t19-safe",
                ),
            ],
            contamination=[
                r"resume.*failed\s+step",
                r"keep.*same\s+checkpoint",
            ],
        ),

        _family(
            id="garnetindex-v44-007",
            system="GarnetIndex",
            code="V44",
            experience="during catalog indexing.",
            transfer="during customer indexing.",
            candidate="Rebuild the entire index and discard the existing cursor.",
            atoms=[
                _atom(
                    "E1",
                    "Fetch a fresh cursor from the leader.",
                    r"fresh\s+cursor.*leader",
                ),
                _atom(
                    "E2",
                    "Switch to delta-read.",
                    r"delta[-\s]read",
                ),
                _atom(
                    "E3",
                    "Replay exactly three pages.",
                    r"replay.*exactly\s+(?:three|3)\s+pages",
                ),
                _atom(
                    "E4",
                    "Set X-Garnet-Cursor: fresh.",
                    r"x-garnet-cursor.*fresh",
                ),
            ],
            contamination=[
                r"rebuild.*entire\s+index",
                r"discard.*cursor",
            ],
        ),

        _family(
            id="driftledger-h26-007",
            system="DriftLedger",
            code="H26",
            experience="while posting a settlement.",
            transfer="while posting a rebate.",
            candidate="Synthesize a nonce locally and bypass the lock.",
            atoms=[
                _atom(
                    "E1",
                    "Request the server nonce.",
                    r"(?:request|fetch|get).*server\s+nonce",
                ),
                _atom(
                    "E2",
                    "Acquire the indigo lock.",
                    r"indigo\s+lock",
                ),
                _atom(
                    "E3",
                    "Retry exactly twice.",
                    r"retry.*exactly\s+twice",
                ),
                _atom(
                    "E4",
                    "Set X-Drift-Nonce to the server nonce.",
                    r"x-drift-nonce.*server\s+nonce",
                ),
            ],
            contamination=[
                r"synthesi[sz].*nonce",
                r"bypass.*lock",
            ],
        ),

        _family(
            id="mossbus-j8-007",
            system="MossBus",
            code="J8",
            experience="while consuming an invoice event.",
            transfer="while consuming an audit event.",
            candidate="Acknowledge the original message and retry the same event.",
            atoms=[
                _atom(
                    "E1",
                    "Request a fresh checkpoint.",
                    r"fresh\s+checkpoint",
                ),
                _atom(
                    "E2",
                    "Replay exactly once from the checkpoint.",
                    r"replay.*exactly\s+once",
                ),
                _atom(
                    "E3",
                    "Use Replay-Class: moss.",
                    r"replay-class.*moss",
                ),
                _atom(
                    "E4",
                    "Do not acknowledge the original message.",
                    r"(?:do\s+not|never).*acknowledge.*original\s+message",
                ),
            ],
            contamination=[
                r"acknowledge.*original\s+message",
                r"retry.*same\s+event",
            ],
        ),

        _family(
            id="polarstore-c37-007",
            system="PolarStore",
            code="C37",
            experience="while uploading a 180 MiB backup.",
            transfer="while uploading a 90 MiB snapshot.",
            candidate="Reuse the previous upload ID and send one large part.",
            atoms=[
                _atom(
                    "E1",
                    "Use a new upload ID.",
                    r"new\s+upload\s+id",
                ),
                _atom(
                    "E2",
                    "Use multipart upload with 18 MiB chunks.",
                    r"multipart.*18\s*(?:mib|mb)",
                ),
                _atom(
                    "E3",
                    "Apply SHA-384 to every chunk.",
                    r"sha-?384.*(?:every|each|per).*chunk",
                ),
                _atom(
                    "E4",
                    "Include X-Polar-Manifest: frost on finalization.",
                    r"x-polar-manifest.*frost",
                ),
            ],
            contamination=[
                r"reuse.*upload\s+id",
                r"one\s+large\s+part",
            ],
        ),

        _family(
            id="slatedb-n15-007",
            system="SlateDB",
            code="N15",
            experience="during a customer-balance query.",
            transfer="during an inventory query.",
            candidate="Reconnect the session and generate a new request ID.",
            atoms=[
                _atom(
                    "E1",
                    "Refresh the schema token.",
                    r"refresh.*schema\s+token",
                ),
                _atom(
                    "E2",
                    "Switch to snapshot-read.",
                    r"snapshot[-\s]read",
                ),
                _atom(
                    "E3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Preserve the original request ID.",
                    r"preserv.*original\s+request\s+id",
                ),
            ],
            contamination=[
                r"reconnect.*session",
                r"(?:generate|create).*new\s+request\s+id",
            ],
        ),

        _family(
            id="crestrpc-b66-007",
            system="CrestRPC",
            code="B66",
            experience="during a profile RPC.",
            transfer="during a billing RPC.",
            candidate="Reuse the previous stream ID and restart the RPC service.",
            atoms=[
                _atom(
                    "E1",
                    "Send exactly three heartbeat frames.",
                    r"(?:three|3)\s+heartbeat",
                ),
                _atom(
                    "E2",
                    "Space the heartbeat frames 160 ms apart.",
                    r"\b160\s*(?:ms|milliseconds?)\b",
                ),
                _atom(
                    "E3",
                    "Open a fresh channel.",
                    r"fresh\s+channel",
                ),
                _atom(
                    "E4",
                    "Include X-Crest-Recover: b66.",
                    r"x-crest-recover.*b66",
                ),
            ],
            contamination=[
                r"reuse.*stream\s+id",
                r"restart.*rpc\s+service",
            ],
        ),

        _family(
            id="limequeue-g24-007",
            system="LimeQueue",
            code="G24",
            experience="for a report-generation job.",
            transfer="for a media-processing job.",
            candidate="Cancel the job and delete the existing dispatch record.",
            atoms=[
                _atom(
                    "E1",
                    "Mint a new dispatch ID.",
                    r"(?:mint|create|generate).*new\s+dispatch\s+id",
                ),
                _atom(
                    "E2",
                    "Move the job to the lilac lane.",
                    r"lilac\s+lane",
                ),
                _atom(
                    "E3",
                    "Requeue exactly once.",
                    r"re-?queue.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Tag dispatch-mode=restored.",
                    r"dispatch-mode\s*=\s*restored",
                ),
            ],
            contamination=[
                r"cancel.*job",
                r"delete.*dispatch\s+record",
            ],
        ),

        _family(
            id="nimbuscdn-a58-007",
            system="NimbusCDN",
            code="A58",
            experience="while refreshing a JavaScript asset.",
            transfer="while refreshing an image asset.",
            candidate="Purge all POPs and invalidate every cached asset.",
            atoms=[
                _atom(
                    "E1",
                    "Issue one HEAD request to origin.",
                    r"(?:one|1)\s+head\s+request",
                ),
                _atom(
                    "E2",
                    "Purge only the current POP shard.",
                    r"purge.*only.*current\s+pop\s+shard",
                ),
                _atom(
                    "E3",
                    "Wait 10 seconds.",
                    r"\b10\s*seconds?\b",
                ),
                _atom(
                    "E4",
                    "Issue one GET with X-Nimbus-Probe: 8.",
                    r"(?:one|1)\s+get.*x-nimbus-probe.*8",
                ),
            ],
            contamination=[
                r"purge.*all\s+pop",
                r"invalidate.*every.*cached\s+asset",
            ],
        ),

        _family(
            id="brookflow-w13-007",
            system="BrookFlow",
            code="W13",
            experience="during invoice export.",
            transfer="during analytics export.",
            candidate="Restart the entire workflow and discard the checkpoint.",
            atoms=[
                _atom(
                    "E1",
                    "Clone the latest checkpoint.",
                    r"clone.*latest\s+checkpoint",
                ),
                _atom(
                    "E2",
                    "Mark the old run superseded.",
                    r"old\s+run.*superseded",
                ),
                _atom(
                    "E3",
                    "Restart from the previous boundary exactly once.",
                    r"restart.*previous\s+boundary.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Carry token w13-safe.",
                    r"w13-safe",
                ),
            ],
            contamination=[
                r"restart.*entire\s+workflow",
                r"discard.*checkpoint",
            ],
        ),

        _family(
            id="reedparser-f5-007",
            system="ReedParser",
            code="F5",
            experience="with legacy state=X before validation.",
            transfer="with legacy state=Z before validation.",
            candidate="Drop the state field and default the record to approved.",
            atoms=[
                _atom(
                    "E1",
                    "Map X to queued.",
                    r"\bx\b.*\bqueued\b",
                ),
                _atom(
                    "E2",
                    "Map Y to blocked.",
                    r"\by\b.*\bblocked\b",
                ),
                _atom(
                    "E3",
                    "Map Z to ready.",
                    r"\bz\b.*\bready\b",
                ),
                _atom(
                    "E4",
                    "Perform the mapping before normal validation.",
                    r"before.*normal\s+validation",
                ),
            ],
            contamination=[
                r"drop.*state\s+field",
                r"default.*approved",
            ],
        ),

        _family(
            id="alpinepay-s41-007",
            system="AlpinePay",
            code="S41",
            experience="while capturing an order payment.",
            transfer="while issuing a subscription adjustment.",
            candidate="Refund the customer immediately and reverse the charge.",
            atoms=[
                _atom(
                    "E1",
                    "Wait 13 seconds.",
                    r"\b13\s*seconds?\b",
                ),
                _atom(
                    "E2",
                    "Rotate the session key.",
                    r"rotat.*session\s+key",
                ),
                _atom(
                    "E3",
                    "Mint a new idempotency key.",
                    r"(?:mint|create|generate).*new\s+idempotency\s+key",
                ),
                _atom(
                    "E4",
                    "Retry exactly twice with X-Alpine-Mode: silver.",
                    r"retry.*exactly\s+twice.*x-alpine-mode.*silver",
                ),
            ],
            contamination=[
                r"refund.*customer",
                r"reverse.*charge",
            ],
        ),

        _family(
            id="indigoindex-z27-007",
            system="IndigoIndex",
            code="Z27",
            experience="during product search.",
            transfer="during account search.",
            candidate="Delete the current snapshot and rebuild the search index.",
            atoms=[
                _atom(
                    "E1",
                    "Fetch a fresh cursor from the leader.",
                    r"fresh\s+cursor.*leader",
                ),
                _atom(
                    "E2",
                    "Switch to shadow-read.",
                    r"shadow[-\s]read",
                ),
                _atom(
                    "E3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "E4",
                    "Preserve the original query ID.",
                    r"preserv.*original\s+query\s+id",
                ),
            ],
            contamination=[
                r"delete.*snapshot",
                r"rebuild.*search\s+index",
            ],
        ),
    ]

    return {
        "experiment": "seed-growth-007",
        "classification": "exploratory-fresh-raw-evidence-atomization-ablation",
        "hypothesis": (
            "Raw evidence atomization via deterministic span grounding "
            "enforces span-level ancestry without relying on pre-registered "
            "oracle evidence atoms, preventing ungrounded propositions from "
            "entering persistent memory while maintaining transfer success."
        ),
        "families": families,
    }


def main():
    output = Path("experiments/tasks_007.json")
    payload = build_taskset()
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {len(payload['families'])} families to {output}")


if __name__ == "__main__":
    main()
