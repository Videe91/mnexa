from __future__ import annotations

import json

from pathlib import Path


from experiments.make_tasks_011 import (
    _family,
    _parser_spec,
    _payment_spec,
    _queue_spec,
    _rpc_spec,
    _storage_spec,
)


def _build_specs():
    return [

        # ------------------------------------------------------------
        # PAYMENTS
        # ------------------------------------------------------------

        _payment_spec(
            system="AquilaPay",
            code="AQ-83",
            wait=14,
            latency=188,
        ),

        _payment_spec(
            system="BorealPay",
            code="BR-46",
            wait=10,
            latency=197,
        ),

        _payment_spec(
            system="CinderPay",
            code="CN-71",
            wait=18,
            latency=211,
        ),

        _payment_spec(
            system="DahliaPay",
            code="DH-33",
            wait=6,
            latency=179,
        ),

        # ------------------------------------------------------------
        # QUEUES
        # ------------------------------------------------------------

        _queue_spec(
            system="EonQueue",
            code="EO-72",
            lane="bronze",
            latency=218,
        ),

        _queue_spec(
            system="FableQueue",
            code="FB-58",
            lane="cobalt",
            latency=229,
        ),

        _queue_spec(
            system="GarnetQueue",
            code="GN-84",
            lane="amber",
            latency=241,
        ),

        _queue_spec(
            system="HearthQueue",
            code="HT-39",
            lane="jade",
            latency=212,
        ),

        # ------------------------------------------------------------
        # STORAGE
        # ------------------------------------------------------------

        _storage_spec(
            system="IndigoStore",
            code="IN-67",
            chunk=15,
            digest="SHA-256",
            header=(
                "X-Indigo-Final: sealed"
            ),
            latency=268,
        ),

        _storage_spec(
            system="JasperStore",
            code="JS-29",
            chunk=21,
            digest="SHA-384",
            header=(
                "X-Jasper-Final: strict"
            ),
            latency=278,
        ),

        _storage_spec(
            system="KeystoneStore",
            code="KS-94",
            chunk=17,
            digest="BLAKE3",
            header=(
                "X-Keystone-Final: sealed"
            ),
            latency=292,
        ),

        _storage_spec(
            system="LarchStore",
            code="LR-52",
            chunk=23,
            digest="SHA-512",
            header=(
                "X-Larch-Final: strict"
            ),
            latency=257,
        ),

        # ------------------------------------------------------------
        # PARSERS
        # ------------------------------------------------------------

        _parser_spec(
            system="MicaParser",
            code="MC-43",
            symbols=(
                "A",
                "B",
                "C",
            ),
            latency=132,
        ),

        _parser_spec(
            system="NectarParser",
            code="NC-76",
            symbols=(
                "D",
                "E",
                "F",
            ),
            latency=141,
        ),

        _parser_spec(
            system="OspreyParser",
            code="OP-28",
            symbols=(
                "K",
                "L",
                "M",
            ),
            latency=148,
        ),

        _parser_spec(
            system="PrairieParser",
            code="PP-91",
            symbols=(
                "X",
                "Y",
                "Z",
            ),
            latency=155,
        ),

        # ------------------------------------------------------------
        # RPC
        # ------------------------------------------------------------

        _rpc_spec(
            system="QuillRPC",
            code="QR-64",
            heartbeat_count=3,
            spacing=195,
            latency=301,
        ),

        _rpc_spec(
            system="RuneRPC",
            code="RN-37",
            heartbeat_count=4,
            spacing=220,
            latency=313,
        ),

        _rpc_spec(
            system="StrataRPC",
            code="ST-82",
            heartbeat_count=2,
            spacing=185,
            latency=287,
        ),

        _rpc_spec(
            system="TimberRPC",
            code="TM-55",
            heartbeat_count=5,
            spacing=230,
            latency=322,
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
            "seed-growth-012"
        ),

        "classification": (
            "exploratory-fresh-grounded-"
            "structure-repair-ablation"
        ),

        "hypothesis": (
            "A second grounded structure-audit pass can repair "
            "compound nuclei and over-attached qualifiers from an "
            "identical first-pass structured proposal while preserving "
            "exact source ancestry, authoritative-role admission, and "
            "closed-world claim safety."
        ),

        "conditions": {
            "A": (
                "one-pass structured extraction"
            ),
            "B": (
                "same initial proposal plus "
                "grounded structure repair"
            ),
        },

        "primary_metrics": [
            "nucleus recall",
            "nucleus precision",
            "compound nuclei admitted",
            "qualifier micro recall",
            "qualifier micro precision",
            "compound challenge survival",
        ],

        "secondary_metrics": [
            "lesson completeness",
            "transfer task success",
            "memory word count",
            "repair operation counts",
        ],

        "control_invariants": [
            "all_source_evidence_equal",
            "all_initial_structured_proposals_equal",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_012.json"
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
