from __future__ import annotations

import json
import re
from pathlib import Path


ROLE_ORDER = (
    "status",
    "failed_decision",
    "authoritative_correction",
    "operator_note",
    "diagnostic_metadata",
)


def build_raw_source(
    *,
    status: str,
    failed_decision: str,
    authoritative_sentences,
    operator_note: str,
    diagnostic_metadata: str,
) -> str:
    sections = {
        "status": status,
        "failed_decision": failed_decision,
        "authoritative_correction": " ".join(authoritative_sentences),
        "operator_note": operator_note,
        "diagnostic_metadata": diagnostic_metadata,
    }

    chunks = []

    for role in ROLE_ORDER:
        chunks.append(f"<<<ROLE:{role}>>>")
        chunks.append(sections[role])
        chunks.append(f"<<<END_ROLE:{role}>>>")

    return "\n".join(chunks)


def _atom(
    atom_id: str,
    text: str,
    pattern: str,
):
    return {
        "id": atom_id,
        "text": text,
        "task_pattern": pattern,
    }


def _regex_exactish(text: str) -> str:
    return re.escape(text.rstrip("."))


def _family(
    *,
    id,
    system,
    code,
    experience,
    transfer,
    candidate,
    atoms,
    required_ids,
    note,
    latency,
):
    status = f"{code} run status was FAIL."
    operator_note = f"Operator suspects {note}."
    metadata = f"Observed diagnostic latency was {latency} ms."

    raw_source = build_raw_source(
        status=status,
        failed_decision=candidate,
        authoritative_sentences=[atom["text"] for atom in atoms],
        operator_note=operator_note,
        diagnostic_metadata=metadata,
    )

    by_id = {atom["id"]: atom for atom in atoms}
    required_atoms = [by_id[atom_id] for atom_id in required_ids]

    role_challenges = [
        {
            "role": "status",
            "text": status,
        },
        {
            "role": "failed_decision",
            "text": candidate,
        },
        {
            "role": "operator_note",
            "text": operator_note,
        },
        {
            "role": "diagnostic_metadata",
            "text": metadata,
        },
    ]

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
            "prompt": f"{system} returns {code} {transfer}"
        },

        "candidate_decision": candidate,

        "raw_source": raw_source,

        "authoritative_atoms": atoms,

        "transfer_required_atom_ids": required_ids,

        "knowledge_grader": {
            "all_regex": [
                [atom["task_pattern"]]
                for atom in atoms
            ]
        },

        "transfer_grader": {
            "all_regex": [
                [atom["task_pattern"]]
                for atom in required_atoms
            ]
        },

        "role_challenges": role_challenges,

        "nonknowledge_regex": [
            _regex_exactish(challenge["text"])
            for challenge in role_challenges
        ],
    }


def build_taskset():
    families = [
        _family(
            id="helixpay-zr41",
            system="HelixPay",
            code="ZR-41",
            experience="while capturing an invoice payment.",
            transfer=(
                "while issuing a billing adjustment. "
                "What retry timing and recovery header should be used?"
            ),
            candidate="Restart the payment service and clear the session cache.",
            atoms=[
                _atom(
                    "A1",
                    "Refresh the recovery lease.",
                    r"refresh.*recovery\s+lease",
                ),
                _atom(
                    "A2",
                    "Wait 8 seconds.",
                    r"\b8\s*seconds?\b",
                ),
                _atom(
                    "A3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Include X-Helix-Recover: bronze.",
                    r"x-helix-recover.*bronze",
                ),
            ],
            required_ids=["A2", "A4"],
            note="a transient routing issue may be involved",
            latency=183,
        ),

        _family(
            id="juniperqueue-jp17",
            system="JuniperQueue",
            code="JP-17",
            experience="while processing a document-render job.",
            transfer=(
                "while processing a thumbnail job. "
                "Which lane and replay rule should be used?"
            ),
            candidate="Delete the message and restart the worker pool.",
            atoms=[
                _atom(
                    "A1",
                    "Request a fresh checkpoint.",
                    r"fresh\s+checkpoint",
                ),
                _atom(
                    "A2",
                    "Move the job to the violet lane.",
                    r"violet\s+lane",
                ),
                _atom(
                    "A3",
                    "Replay exactly once from the checkpoint.",
                    r"replay.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Use Replay-Class: juniper.",
                    r"replay-class.*juniper",
                ),
            ],
            required_ids=["A2", "A3"],
            note="worker saturation may explain the failure",
            latency=211,
        ),

        _family(
            id="marblestore-ms72",
            system="MarbleStore",
            code="MS-72",
            experience="while uploading a 144 MiB archive.",
            transfer=(
                "while uploading a 72 MiB snapshot. "
                "What multipart chunk size and digest are required?"
            ),
            candidate="Compress the object and send it as one large part.",
            atoms=[
                _atom(
                    "A1",
                    "Start a new upload session.",
                    r"new\s+upload\s+session",
                ),
                _atom(
                    "A2",
                    "Use multipart upload with 12 MiB chunks.",
                    r"multipart.*12\s*(?:mib|mb)",
                ),
                _atom(
                    "A3",
                    "Attach SHA3-384 to every chunk.",
                    r"sha3-?384.*(?:every|each|per).*chunk",
                ),
                _atom(
                    "A4",
                    "Include X-Marble-Final: strict on finalization.",
                    r"x-marble-final.*strict",
                ),
            ],
            required_ids=["A2", "A3"],
            note="object compression overhead may be contributing",
            latency=247,
        ),

        _family(
            id="kestreldb-kd29",
            system="KestrelDB",
            code="KD-29",
            experience="while writing an inventory mutation.",
            transfer=(
                "while writing a pricing mutation. "
                "Which epoch source and lock are required?"
            ),
            candidate="Restart the database node and increment the epoch locally.",
            atoms=[
                _atom(
                    "A1",
                    "Read the primary epoch.",
                    r"read.*primary\s+epoch",
                ),
                _atom(
                    "A2",
                    "Acquire the silver lock.",
                    r"silver\s+lock",
                ),
                _atom(
                    "A3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Set X-Kestrel-Epoch to the primary epoch.",
                    r"x-kestrel-epoch.*primary\s+epoch",
                ),
            ],
            required_ids=["A1", "A2"],
            note="leader election churn may have occurred",
            latency=194,
        ),

        _family(
            id="lotusparser-lp08",
            system="LotusParser",
            code="LP-08",
            experience="with legacy state=P before validation.",
            transfer=(
                "with legacy state=R before validation. "
                "What should R map to, and when should mapping occur?"
            ),
            candidate="Drop the state field and default the record to accepted.",
            atoms=[
                _atom(
                    "A1",
                    "Map P to queued.",
                    r"\bp\b.*\bqueued\b",
                ),
                _atom(
                    "A2",
                    "Map Q to blocked.",
                    r"\bq\b.*\bblocked\b",
                ),
                _atom(
                    "A3",
                    "Map R to review.",
                    r"\br\b.*\breview\b",
                ),
                _atom(
                    "A4",
                    "Perform the mapping before normal validation.",
                    r"before.*normal\s+validation",
                ),
            ],
            required_ids=["A3", "A4"],
            note="the legacy producer may still be active",
            latency=126,
        ),

        _family(
            id="beaconrpc-br64",
            system="BeaconRPC",
            code="BR-64",
            experience="during a customer-profile request.",
            transfer=(
                "during an order-history request. "
                "How many heartbeat frames are required and what recovery header must be sent?"
            ),
            candidate="Close the connection and reuse the prior correlation ID.",
            atoms=[
                _atom(
                    "A1",
                    "Send exactly three heartbeat frames.",
                    r"(?:three|3)\s+heartbeat",
                ),
                _atom(
                    "A2",
                    "Space the heartbeat frames 260 ms apart.",
                    r"\b260\s*(?:ms|milliseconds?)\b",
                ),
                _atom(
                    "A3",
                    "Open a new channel with a fresh correlation ID.",
                    r"new\s+channel.*fresh\s+correlation\s+id",
                ),
                _atom(
                    "A4",
                    "Include X-Beacon-Recover: br64.",
                    r"x-beacon-recover.*br64",
                ),
            ],
            required_ids=["A1", "A4"],
            note="the old channel may have experienced jitter",
            latency=305,
        ),

        _family(
            id="tundracdn-tc33",
            system="TundraCDN",
            code="TC-33",
            experience="while refreshing a JavaScript asset.",
            transfer=(
                "while refreshing a stylesheet asset. "
                "Which shard should be purged and how long should the operator wait?"
            ),
            candidate="Perform a global purge and restart every edge process.",
            atoms=[
                _atom(
                    "A1",
                    "Issue one HEAD request to origin.",
                    r"(?:one|1)\s+head\s+request",
                ),
                _atom(
                    "A2",
                    "Purge only the current zone shard.",
                    r"purge.*only.*current\s+zone\s+shard",
                ),
                _atom(
                    "A3",
                    "Wait 6 seconds.",
                    r"\b6\s*seconds?\b",
                ),
                _atom(
                    "A4",
                    "Issue one GET with X-Tundra-Probe: 4.",
                    r"(?:one|1)\s+get.*x-tundra-probe.*4",
                ),
            ],
            required_ids=["A2", "A3"],
            note="regional cache skew may be present",
            latency=172,
        ),

        _family(
            id="cypressflow-cf18",
            system="CypressFlow",
            code="CF-18",
            experience="during invoice reconciliation.",
            transfer=(
                "during payroll export. "
                "From where should the workflow restart and which token must be carried?"
            ),
            candidate="Resume the failed node directly and reuse the same checkpoint.",
            atoms=[
                _atom(
                    "A1",
                    "Clone the latest checkpoint.",
                    r"clone.*latest\s+checkpoint",
                ),
                _atom(
                    "A2",
                    "Mark the old run superseded.",
                    r"old\s+run.*superseded",
                ),
                _atom(
                    "A3",
                    "Restart from the previous boundary exactly once.",
                    r"restart.*previous\s+boundary.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Carry token cf18-safe.",
                    r"cf18-safe",
                ),
            ],
            required_ids=["A3", "A4"],
            note="checkpoint replication may have lagged",
            latency=238,
        ),

        _family(
            id="rubyindex-ri52",
            system="RubyIndex",
            code="RI-52",
            experience="during catalog indexing.",
            transfer=(
                "during customer indexing. "
                "Which read mode and page replay count are required?"
            ),
            candidate="Rebuild the entire index and discard the cursor.",
            atoms=[
                _atom(
                    "A1",
                    "Fetch a fresh cursor from the leader.",
                    r"fresh\s+cursor.*leader",
                ),
                _atom(
                    "A2",
                    "Switch to shadow-read.",
                    r"shadow[-\s]read",
                ),
                _atom(
                    "A3",
                    "Replay exactly four pages.",
                    r"replay.*exactly\s+(?:four|4)\s+pages",
                ),
                _atom(
                    "A4",
                    "Set X-Ruby-Cursor: fresh.",
                    r"x-ruby-cursor.*fresh",
                ),
            ],
            required_ids=["A2", "A3"],
            note="segment compaction may have been incomplete",
            latency=221,
        ),

        _family(
            id="pineledger-pl46",
            system="PineLedger",
            code="PL-46",
            experience="while posting a settlement.",
            transfer=(
                "while posting a rebate. "
                "Where must the nonce come from and how many retries are allowed?"
            ),
            candidate="Synthesize a nonce locally and bypass the lock.",
            atoms=[
                _atom(
                    "A1",
                    "Request the server nonce.",
                    r"(?:request|fetch|get).*server\s+nonce",
                ),
                _atom(
                    "A2",
                    "Acquire the indigo lock.",
                    r"indigo\s+lock",
                ),
                _atom(
                    "A3",
                    "Retry exactly twice.",
                    r"retry.*exactly\s+twice",
                ),
                _atom(
                    "A4",
                    "Set X-Pine-Nonce to the server nonce.",
                    r"x-pine-nonce.*server\s+nonce",
                ),
            ],
            required_ids=["A1", "A3"],
            note="nonce service delay may be involved",
            latency=287,
        ),

        _family(
            id="alderbus-ab15",
            system="AlderBus",
            code="AB-15",
            experience="while consuming an invoice event.",
            transfer=(
                "while consuming an audit event. "
                "What checkpoint and replay class should be used?"
            ),
            candidate="Acknowledge the original message and retry the same event.",
            atoms=[
                _atom(
                    "A1",
                    "Request a fresh checkpoint.",
                    r"fresh\s+checkpoint",
                ),
                _atom(
                    "A2",
                    "Replay exactly once from the checkpoint.",
                    r"replay.*exactly\s+once",
                ),
                _atom(
                    "A3",
                    "Use Replay-Class: alder.",
                    r"replay-class.*alder",
                ),
                _atom(
                    "A4",
                    "Leave the original message unacknowledged.",
                    r"original\s+message.*unacknowledged",
                ),
            ],
            required_ids=["A1", "A3"],
            note="consumer group rebalance may be related",
            latency=198,
        ),

        _family(
            id="deltastore-ds84",
            system="DeltaStore",
            code="DS-84",
            experience="while uploading a 200 MiB backup.",
            transfer=(
                "while uploading a 100 MiB model snapshot. "
                "What chunk size and checksum are required?"
            ),
            candidate="Reuse the old upload ID and send a single large part.",
            atoms=[
                _atom(
                    "A1",
                    "Use a new upload ID.",
                    r"new\s+upload\s+id",
                ),
                _atom(
                    "A2",
                    "Use multipart upload with 25 MiB chunks.",
                    r"multipart.*25\s*(?:mib|mb)",
                ),
                _atom(
                    "A3",
                    "Apply BLAKE3 to every chunk.",
                    r"blake3.*(?:every|each|per).*chunk",
                ),
                _atom(
                    "A4",
                    "Include X-Delta-Manifest: glacier on finalization.",
                    r"x-delta-manifest.*glacier",
                ),
            ],
            required_ids=["A2", "A3"],
            note="the storage gateway may be under pressure",
            latency=319,
        ),

        _family(
            id="harbordb-hd71",
            system="HarborDB",
            code="HD-71",
            experience="during a customer-balance query.",
            transfer=(
                "during an inventory query. "
                "Which read mode and request ID rule should be used?"
            ),
            candidate="Reconnect the session and generate a new request ID.",
            atoms=[
                _atom(
                    "A1",
                    "Refresh the schema token.",
                    r"refresh.*schema\s+token",
                ),
                _atom(
                    "A2",
                    "Switch to snapshot-read.",
                    r"snapshot[-\s]read",
                ),
                _atom(
                    "A3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Preserve the original request ID.",
                    r"preserv.*original\s+request\s+id",
                ),
            ],
            required_ids=["A2", "A4"],
            note="schema propagation may be delayed",
            latency=164,
        ),

        _family(
            id="summitrpc-sr26",
            system="SummitRPC",
            code="SR-26",
            experience="during a profile RPC.",
            transfer=(
                "during a billing RPC. "
                "What heartbeat spacing and recovery header are required?"
            ),
            candidate="Reuse the old stream ID and restart the RPC service.",
            atoms=[
                _atom(
                    "A1",
                    "Send exactly two heartbeat frames.",
                    r"(?:two|2)\s+heartbeat",
                ),
                _atom(
                    "A2",
                    "Space the heartbeat frames 190 ms apart.",
                    r"\b190\s*(?:ms|milliseconds?)\b",
                ),
                _atom(
                    "A3",
                    "Open a fresh channel.",
                    r"fresh\s+channel",
                ),
                _atom(
                    "A4",
                    "Include X-Summit-Recover: sr26.",
                    r"x-summit-recover.*sr26",
                ),
            ],
            required_ids=["A2", "A4"],
            note="stream scheduling jitter may be present",
            latency=226,
        ),

        _family(
            id="copperqueue-cq31",
            system="CopperQueue",
            code="CQ-31",
            experience="for a report-generation job.",
            transfer=(
                "for a media-processing job. "
                "Which lane and dispatch mode should be used?"
            ),
            candidate="Cancel the job and delete the dispatch record.",
            atoms=[
                _atom(
                    "A1",
                    "Mint a new dispatch ID.",
                    r"(?:mint|create|generate).*new\s+dispatch\s+id",
                ),
                _atom(
                    "A2",
                    "Move the job to the teal lane.",
                    r"teal\s+lane",
                ),
                _atom(
                    "A3",
                    "Requeue exactly once.",
                    r"re-?queue.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Tag dispatch-mode=recovered.",
                    r"dispatch-mode\s*=\s*recovered",
                ),
            ],
            required_ids=["A2", "A4"],
            note="dispatch fanout may have stalled",
            latency=201,
        ),

        _family(
            id="frostcdn-fc67",
            system="FrostCDN",
            code="FC-67",
            experience="while refreshing a JavaScript asset.",
            transfer=(
                "while refreshing an image asset. "
                "What request should be sent first and which shard may be purged?"
            ),
            candidate="Purge every POP and invalidate all cached objects.",
            atoms=[
                _atom(
                    "A1",
                    "Issue one HEAD request to origin.",
                    r"(?:one|1)\s+head\s+request",
                ),
                _atom(
                    "A2",
                    "Purge only the current POP shard.",
                    r"purge.*only.*current\s+pop\s+shard",
                ),
                _atom(
                    "A3",
                    "Wait 11 seconds.",
                    r"\b11\s*seconds?\b",
                ),
                _atom(
                    "A4",
                    "Issue one GET with X-Frost-Probe: 9.",
                    r"(?:one|1)\s+get.*x-frost-probe.*9",
                ),
            ],
            required_ids=["A1", "A2"],
            note="one edge cluster may be lagging",
            latency=243,
        ),

        _family(
            id="amberflow-af52",
            system="AmberFlow",
            code="AF-52",
            experience="during invoice export.",
            transfer=(
                "during analytics export. "
                "Which checkpoint action and restart boundary are required?"
            ),
            candidate="Restart the entire workflow and discard the checkpoint.",
            atoms=[
                _atom(
                    "A1",
                    "Clone the latest checkpoint.",
                    r"clone.*latest\s+checkpoint",
                ),
                _atom(
                    "A2",
                    "Mark the old run stale.",
                    r"old\s+run.*stale",
                ),
                _atom(
                    "A3",
                    "Restart from the previous boundary exactly once.",
                    r"restart.*previous\s+boundary.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Carry token af52-safe.",
                    r"af52-safe",
                ),
            ],
            required_ids=["A1", "A3"],
            note="workflow state replication may be delayed",
            latency=266,
        ),

        _family(
            id="willowparser-wp09",
            system="WillowParser",
            code="WP-09",
            experience="with legacy state=L before validation.",
            transfer=(
                "with legacy state=N before validation. "
                "What should N map to, and when should mapping occur?"
            ),
            candidate="Drop the legacy field and default the record to valid.",
            atoms=[
                _atom(
                    "A1",
                    "Map L to queued.",
                    r"\bl\b.*\bqueued\b",
                ),
                _atom(
                    "A2",
                    "Map M to blocked.",
                    r"\bm\b.*\bblocked\b",
                ),
                _atom(
                    "A3",
                    "Map N to ready.",
                    r"\bn\b.*\bready\b",
                ),
                _atom(
                    "A4",
                    "Perform the mapping before normal validation.",
                    r"before.*normal\s+validation",
                ),
            ],
            required_ids=["A3", "A4"],
            note="a legacy producer may still be emitting old symbols",
            latency=138,
        ),

        _family(
            id="granitepay-gp58",
            system="GranitePay",
            code="GP-58",
            experience="while capturing an order payment.",
            transfer=(
                "while issuing a subscription adjustment. "
                "How long should the operator wait and how many retries are allowed?"
            ),
            candidate="Refund the customer and reverse the original charge.",
            atoms=[
                _atom(
                    "A1",
                    "Wait 14 seconds.",
                    r"\b14\s*seconds?\b",
                ),
                _atom(
                    "A2",
                    "Rotate the session key.",
                    r"rotat.*session\s+key",
                ),
                _atom(
                    "A3",
                    "Mint a new idempotency key.",
                    r"(?:mint|create|generate).*new\s+idempotency\s+key",
                ),
                _atom(
                    "A4",
                    "Retry exactly twice with X-Granite-Mode: white.",
                    r"retry.*exactly\s+twice.*x-granite-mode.*white",
                ),
            ],
            required_ids=["A1", "A4"],
            note="the acquirer may have transient congestion",
            latency=291,
        ),

        _family(
            id="silverindex-si36",
            system="SilverIndex",
            code="SI-36",
            experience="during product search.",
            transfer=(
                "during account search. "
                "Which cursor source and query-ID rule are required?"
            ),
            candidate="Delete the current snapshot and rebuild the search index.",
            atoms=[
                _atom(
                    "A1",
                    "Fetch a fresh cursor from the leader.",
                    r"fresh\s+cursor.*leader",
                ),
                _atom(
                    "A2",
                    "Switch to delta-read.",
                    r"delta[-\s]read",
                ),
                _atom(
                    "A3",
                    "Retry exactly once.",
                    r"retry.*exactly\s+once",
                ),
                _atom(
                    "A4",
                    "Preserve the original query ID.",
                    r"preserv.*original\s+query\s+id",
                ),
            ],
            required_ids=["A1", "A4"],
            note="snapshot compaction may have overlapped the query",
            latency=217,
        ),
    ]

    return {
        "experiment": "seed-growth-008",
        "classification": "exploratory-fresh-evidence-role-ablation",
        "hypothesis": (
            "Exact source-span grounding is necessary but insufficient for reusable knowledge. "
            "A deterministic evidence-role gate should preserve authoritative knowledge while "
            "rejecting exact spans from status, failed attempts, speculation, and diagnostic metadata."
        ),
        "primary_metrics": [
            "authoritative_recall",
            "authoritative_precision",
            "ineligible_atoms_admitted",
            "role_challenge_rejections",
        ],
        "secondary_metrics": [
            "knowledge_completeness",
            "transfer_task_sufficiency",
            "transfer_nonknowledge_leak",
        ],
        "families": families,
    }


def main():
    output = Path("experiments/tasks_008.json")
    payload = build_taskset()
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {len(payload['families'])} families to {output}")


if __name__ == "__main__":
    main()
