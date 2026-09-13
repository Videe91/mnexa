from __future__ import annotations

import json
import re

from pathlib import Path


from experiments.make_tasks_008 import (
    build_raw_source,
)


STYLE_NAMES = (
    "numbered",
    "conditional_ordering",
    "conjunction",
    "negation_scope",
    "mixed_ordering",
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


def _compose_authoritative(
    *,
    style_index: int,
    code: str,
    pieces,
):
    a1, a2, a3, a4 = (
        pieces
    )

    if style_index == 0:

        text = (
            f"1) {a1}; "
            f"2) {a2}; "
            f"3) {a3}; "
            f"4) {a4}."
        )

        qualifiers = []

    elif style_index == 1:

        text = (
            f"When {code} occurs, "
            f"{a1}; "
            f"then {a2}; "
            f"{a3}; "
            f"finally {a4}."
        )

        qualifiers = [
            {
                "atom_id": "A1",
                "type": "condition",
                "text": (
                    f"When {code} occurs"
                ),
            },
            {
                "atom_id": "A2",
                "type": "ordering",
                "text": "then",
            },
            {
                "atom_id": "A4",
                "type": "ordering",
                "text": "finally",
            },
        ]

    elif style_index == 2:

        text = (
            f"{a1} and {a2}; "
            f"{a3}, but {a4}."
        )

        qualifiers = []

    elif style_index == 3:

        # Semantic scope / negation is intentionally encoded
        # inside the canonical nuclei themselves.
        text = (
            f"{a1}; "
            f"{a2}; "
            f"{a3}; "
            f"{a4}."
        )

        qualifiers = []

    elif style_index == 4:

        text = (
            f"If {code} recurs, "
            f"{a1}; "
            f"after that, {a2}; "
            f"afterward, {a3}; "
            f"finally, {a4}."
        )

        qualifiers = [
            {
                "atom_id": "A1",
                "type": "condition",
                "text": (
                    f"If {code} recurs"
                ),
            },
            {
                "atom_id": "A2",
                "type": "ordering",
                "text": (
                    "after that"
                ),
            },
            {
                "atom_id": "A3",
                "type": "ordering",
                "text": (
                    "afterward"
                ),
            },
            {
                "atom_id": "A4",
                "type": "ordering",
                "text": (
                    "finally"
                ),
            },
        ]

    else:
        raise ValueError(
            f"Unknown style index: "
            f"{style_index}"
        )

    return (
        text,
        qualifiers,
    )


def _family(
    *,
    index,
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

    style_index = (
        index
        % len(
            STYLE_NAMES
        )
    )

    style = (
        STYLE_NAMES[
            style_index
        ]
    )

    (
        authoritative_text,
        expected_qualifiers,
    ) = (
        _compose_authoritative(
            style_index=(
                style_index
            ),
            code=spec[
                "code"
            ],
            pieces=(
                pieces
            ),
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
            status=(
                status
            ),
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

    challenges = [
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
        "expected_qualifiers": (
            expected_qualifiers
        ),

        # Seed 010 flat-baseline attack set.
        "overlap_challenges": (
            challenges
        ),

        # Seed 011 structured-nucleus attack set.
        "structured_compound_challenges": (
            challenges
        ),

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


def _payment_spec(
    *,
    system,
    code,
    wait,
    latency,
):
    return {
        "id": (
            f"{system.lower()}-"
            f"{code.lower()}"
        ),
        "system": (
            system
        ),
        "code": (
            code
        ),
        "experience": (
            "while capturing an invoice payment."
        ),
        "transfer": (
            "while adjusting a subscription."
        ),
        "ask": (
            "What wait duration and nonce rule "
            "are required?"
        ),
        "candidate": (
            "Restart the payment service "
            "and reuse the prior nonce."
        ),
        "note": (
            "gateway congestion may be transient"
        ),
        "latency": (
            latency
        ),
        "atoms": [
            (
                "refresh the recovery lease",
                (
                    r"refresh.{0,20}"
                    r"recovery\s+lease"
                ),
            ),
            (
                f"wait {wait} seconds",
                (
                    rf"\b{wait}\b"
                    r".{0,8}seconds?"
                ),
            ),
            (
                "retry exactly once",
                (
                    r"retry.{0,12}"
                    r"exactly.{0,8}once"
                ),
            ),
            (
                "never reuse the prior nonce",
                (
                    r"(?:never|do.{0,8}not)"
                    r".{0,18}reuse"
                    r".{0,18}prior"
                    r".{0,10}nonce"
                ),
            ),
        ],
        "required": [
            2,
            4,
        ],
    }


def _queue_spec(
    *,
    system,
    code,
    lane,
    latency,
):
    return {
        "id": (
            f"{system.lower()}-"
            f"{code.lower()}"
        ),
        "system": (
            system
        ),
        "code": (
            code
        ),
        "experience": (
            "while processing a report job."
        ),
        "transfer": (
            "while processing a media job."
        ),
        "ask": (
            "Which lane and replay count "
            "are required?"
        ),
        "candidate": (
            "Delete the job and restart "
            "the worker pool."
        ),
        "note": (
            "worker saturation may have occurred"
        ),
        "latency": (
            latency
        ),
        "atoms": [
            (
                "request a fresh checkpoint",
                (
                    r"fresh.{0,10}checkpoint"
                ),
            ),
            (
                (
                    "move the job only to the "
                    f"{lane} lane"
                ),
                (
                    r"move.{0,18}job"
                    r".{0,18}only"
                    rf".{0,18}{re.escape(lane)}"
                    r".{0,10}lane"
                ),
            ),
            (
                "replay exactly twice",
                (
                    r"replay.{0,12}"
                    r"exactly.{0,8}twice"
                ),
            ),
            (
                "preserve the original job ID",
                (
                    r"preserv.{0,18}"
                    r"original.{0,12}"
                    r"job.{0,8}id"
                ),
            ),
        ],
        "required": [
            2,
            3,
        ],
    }


def _storage_spec(
    *,
    system,
    code,
    chunk,
    digest,
    header,
    latency,
):
    return {
        "id": (
            f"{system.lower()}-"
            f"{code.lower()}"
        ),
        "system": (
            system
        ),
        "code": (
            code
        ),
        "experience": (
            "while uploading a backup archive."
        ),
        "transfer": (
            "while uploading a model snapshot."
        ),
        "ask": (
            "What chunk size and digest "
            "are required?"
        ),
        "candidate": (
            "Reuse the old upload ID "
            "and send one large part."
        ),
        "note": (
            "storage gateway load may be elevated"
        ),
        "latency": (
            latency
        ),
        "atoms": [
            (
                "start a new upload session",
                (
                    r"new.{0,10}upload"
                    r".{0,10}session"
                ),
            ),
            (
                f"use {chunk} MiB chunks",
                (
                    rf"\b{chunk}\b"
                    r".{0,8}(?:mib|mb)"
                    r".{0,10}chunks?"
                ),
            ),
            (
                (
                    f"apply {digest} "
                    "to every chunk"
                ),
                (
                    re.escape(
                        digest
                    )
                    +
                    r".{0,18}"
                    r"(?:every|each)"
                    r".{0,10}chunk"
                ),
            ),
            (
                (
                    "finalize only with "
                    f"{header}"
                ),
                (
                    r"finaliz.{0,18}"
                    r"only.{0,18}"
                    +
                    re.escape(
                        header
                    )
                ),
            ),
        ],
        "required": [
            2,
            3,
        ],
    }


def _parser_spec(
    *,
    system,
    code,
    symbols,
    latency,
):
    first, second, third = (
        symbols
    )

    return {
        "id": (
            f"{system.lower()}-"
            f"{code.lower()}"
        ),
        "system": (
            system
        ),
        "code": (
            code
        ),
        "experience": (
            f"with legacy state={first}."
        ),
        "transfer": (
            f"with legacy state={third}."
        ),
        "ask": (
            f"What should {third} become "
            "and when must mapping occur?"
        ),
        "candidate": (
            "Drop the legacy state field "
            "and default the record to valid."
        ),
        "note": (
            "a legacy producer may still be active"
        ),
        "latency": (
            latency
        ),
        "atoms": [
            (
                f"map {first} to queued",
                (
                    rf"\b{re.escape(first)}\b"
                    r".{0,12}queued"
                ),
            ),
            (
                f"map {second} to blocked",
                (
                    rf"\b{re.escape(second)}\b"
                    r".{0,12}blocked"
                ),
            ),
            (
                f"map {third} to review",
                (
                    rf"\b{re.escape(third)}\b"
                    r".{0,12}review"
                ),
            ),
            (
                (
                    "perform all mappings before "
                    "normal validation"
                ),
                (
                    r"mapping.{0,20}"
                    r"before.{0,15}"
                    r"normal.{0,12}"
                    r"validation"
                ),
            ),
        ],
        "required": [
            3,
            4,
        ],
    }


def _rpc_spec(
    *,
    system,
    code,
    heartbeat_count,
    spacing,
    latency,
):
    heartbeat_word = {
        2: "two",
        3: "three",
        4: "four",
        5: "five",
    }[
        heartbeat_count
    ]

    return {
        "id": (
            f"{system.lower()}-"
            f"{code.lower()}"
        ),
        "system": (
            system
        ),
        "code": (
            code
        ),
        "experience": (
            "during a profile request."
        ),
        "transfer": (
            "during a billing request."
        ),
        "ask": (
            "How many heartbeats and which "
            "channel rule are required?"
        ),
        "candidate": (
            "Reuse the old channel and "
            "previous correlation ID."
        ),
        "note": (
            "stream scheduling jitter may exist"
        ),
        "latency": (
            latency
        ),
        "atoms": [
            (
                (
                    "send exactly "
                    f"{heartbeat_word} "
                    "heartbeat frames"
                ),
                (
                    rf"(?:{heartbeat_word}|"
                    rf"{heartbeat_count})"
                    r".{0,10}heartbeat"
                    r".{0,10}frames?"
                ),
            ),
            (
                (
                    "space them "
                    f"{spacing} ms apart"
                ),
                (
                    rf"\b{spacing}\b"
                    r".{0,8}(?:ms|milliseconds?)"
                ),
            ),
            (
                "open only a fresh channel",
                (
                    r"open.{0,12}only"
                    r".{0,12}fresh"
                    r".{0,10}channel"
                ),
            ),
            (
                (
                    "never reuse the prior "
                    "correlation ID"
                ),
                (
                    r"(?:never|do.{0,8}not)"
                    r".{0,18}reuse"
                    r".{0,18}prior"
                    r".{0,15}correlation"
                    r".{0,8}id"
                ),
            ),
        ],
        "required": [
            1,
            3,
        ],
    }


def _build_specs():
    return [

        _payment_spec(
            system="NovaPay",
            code="NP-92",
            wait=12,
            latency=181,
        ),
        _payment_spec(
            system="HelioPay",
            code="HP-74",
            wait=9,
            latency=193,
        ),
        _payment_spec(
            system="DriftPay",
            code="DP-63",
            wait=16,
            latency=204,
        ),
        _payment_spec(
            system="ArcPay",
            code="AP-29",
            wait=7,
            latency=176,
        ),

        _queue_spec(
            system="SableQueue",
            code="SQ-61",
            lane="amber",
            latency=214,
        ),
        _queue_spec(
            system="NimbusQueue",
            code="NQ-32",
            lane="violet",
            latency=226,
        ),
        _queue_spec(
            system="FlintQueue",
            code="FQ-85",
            lane="silver",
            latency=238,
        ),
        _queue_spec(
            system="EchoQueue",
            code="EQ-47",
            lane="teal",
            latency=207,
        ),

        _storage_spec(
            system="QuartzStore",
            code="QS-72",
            chunk=14,
            digest="SHA-384",
            header="X-Quartz-Final: strict",
            latency=265,
        ),
        _storage_spec(
            system="PineStore",
            code="PS-48",
            chunk=22,
            digest="BLAKE3",
            header="X-Pine-Final: sealed",
            latency=273,
        ),
        _storage_spec(
            system="OrbitStore",
            code="OS-93",
            chunk=18,
            digest="SHA-512",
            header="X-Orbit-Final: strict",
            latency=289,
        ),
        _storage_spec(
            system="ValeStore",
            code="VS-26",
            chunk=26,
            digest="BLAKE2b",
            header="X-Vale-Final: sealed",
            latency=251,
        ),

        _parser_spec(
            system="MossParser",
            code="MP-41",
            symbols=(
                "G",
                "H",
                "J",
            ),
            latency=129,
        ),
        _parser_spec(
            system="LatticeParser",
            code="LT-68",
            symbols=(
                "P",
                "Q",
                "R",
            ),
            latency=136,
        ),
        _parser_spec(
            system="CedarParser",
            code="CP-95",
            symbols=(
                "S",
                "T",
                "U",
            ),
            latency=143,
        ),
        _parser_spec(
            system="BloomParser",
            code="BP-24",
            symbols=(
                "V",
                "W",
                "X",
            ),
            latency=151,
        ),

        _rpc_spec(
            system="AtlasRPC",
            code="AX-73",
            heartbeat_count=3,
            spacing=205,
            latency=297,
        ),
        _rpc_spec(
            system="EmberRPC",
            code="ER-54",
            heartbeat_count=4,
            spacing=180,
            latency=309,
        ),
        _rpc_spec(
            system="CobaltRPC",
            code="CR-82",
            heartbeat_count=2,
            spacing=240,
            latency=283,
        ),
        _rpc_spec(
            system="ValeRPC",
            code="VR-31",
            heartbeat_count=5,
            spacing=215,
            latency=318,
        ),
    ]


def build_taskset():
    specs = (
        _build_specs()
    )

    families = [
        _family(
            index=index,
            spec=spec,
        )

        for index, spec
        in enumerate(
            specs
        )
    ]

    return {
        "experiment": (
            "seed-growth-011"
        ),
        "classification": (
            "exploratory-fresh-grounded-"
            "structured-proposition-ablation"
        ),
        "hypothesis": (
            "Separating exact support span from reusable proposition "
            "nucleus and grounded semantic qualifiers will improve "
            "autonomous proposition recovery without weakening source "
            "ancestry, role gating, or closed-world claim admission."
        ),
        "conditions": {
            "A": (
                "seed010 flat autonomous exact-span atomization"
            ),
            "B": (
                "grounded structured proposition extraction"
            ),
        },
        "primary_metrics": [
            "canonical nucleus recall",
            "canonical nucleus precision",
            "qualifier recall",
            "qualifier precision",
            "compound nuclei admitted",
            "source ancestry validity",
        ],
        "secondary_metrics": [
            "lesson knowledge completeness",
            "transfer task sufficiency",
            "memory word count",
        ],
        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_011.json"
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
