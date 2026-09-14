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


SYSTEMS = (
    ("EchoWorks", "EW"),
    ("FlintWorks", "FW"),
    ("GroveWorks", "GW"),
    ("HarborWorks", "HW"),
    ("IonWorks", "IW"),
)


CLUSTERS = (
    "retry-policy",
    "lane-routing",
    "channel-session",
    "storage-finalization",
)


RULES = {
    "retry-policy": (
        {
            "clause": "retry exactly eleven times",
            "candidate": "Retry indefinitely.",
            "prompt": "State the exact retry-count rule.",
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (r"\beleven\b", r"\b11\b"),
                (r"\bretr",),
            ),
        },
        {
            "clause": "retry at most ten times",
            "candidate": "Retry fourteen times.",
            "prompt": "State the maximum retry-count rule.",
            "operator": "at_most",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (r"\bten\b", r"\b10\b"),
                (r"\bretr",),
            ),
        },
        {
            "clause": "retry at least six times",
            "candidate": "Retry only twice.",
            "prompt": "State the minimum retry-count rule.",
            "operator": "at_least",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (r"\bsix\b", r"\b6\b"),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "never retry an authorization-rejected request"
            ),
            "candidate": (
                "Retry the authorization-rejected request."
            ),
            "prompt": (
                "State the authorization-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bauthorization\b",),
                (r"\breject",),
            ),
        },
        {
            "clause": (
                "retry only after renewing "
                "the recovery generation"
            ),
            "candidate": (
                "Retry before renewing "
                "the recovery generation."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-generation renewal."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brenew",),
                (r"\brecovery\b",),
                (r"\bgeneration\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only "
                "through the azure lane"
            ),
            "candidate": (
                "Route overflow tasks through any lane."
            ),
            "prompt": (
                "State the permitted lane for overflow tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bazure\b",),
                (r"\blane\b",),
                (r"\boverflow\b",),
            ),
        },
        {
            "clause": (
                "route replay tasks only "
                "through the crimson lane"
            ),
            "candidate": (
                "Route replay tasks through the azure lane."
            ),
            "prompt": (
                "State the permitted lane for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bcrimson\b",),
                (r"\blane\b",),
                (r"\breplay\b",),
            ),
        },
        {
            "clause": (
                "do not route poisoned tasks "
                "through the graphite lane"
            ),
            "candidate": (
                "Route poisoned tasks through "
                "the graphite lane."
            ),
            "prompt": (
                "State the graphite-lane rule "
                "for poisoned tasks."
            ),
            "operator": "do_not",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bpoison",),
                (r"\bgraphite\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "if the queue is stalled, "
                "route the task through the ivory lane"
            ),
            "candidate": (
                "Always route the task "
                "through the ivory lane."
            ),
            "prompt": (
                "State when the ivory lane "
                "should be used."
            ),
            "operator": "when_if",
            "dimension": "condition",
            "grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (r"\bstalled\b",),
                (r"\bivory\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "route quarantine tasks only "
                "through the amber lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the crimson lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for quarantine tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bquarantine\b",),
                (r"\bamber\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh transport channel "
                "after a lineage mismatch"
            ),
            "candidate": (
                "Reuse the current transport channel "
                "after a lineage mismatch."
            ),
            "prompt": (
                "State the channel rule "
                "after a lineage mismatch."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bchannel\b",),
                (r"\blineage\b",),
                (r"\bmismatch\b",),
            ),
        },
        {
            "clause": (
                "never reuse the previous handshake token"
            ),
            "candidate": (
                "Reuse the previous handshake token."
            ),
            "prompt": (
                "State the handshake-token reuse rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bhandshake\b",),
                (r"\btoken\b",),
            ),
        },
        {
            "clause": (
                "send exactly thirteen heartbeat frames"
            ),
            "candidate": (
                "Send three heartbeat frames."
            ),
            "prompt": (
                "State the exact heartbeat-frame count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bthirteen\b",
                    r"\b13\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },
        {
            "clause": (
                "wait at least 37 seconds "
                "before reconnecting"
            ),
            "candidate": (
                "Reconnect immediately."
            ),
            "prompt": (
                "State the minimum reconnect wait."
            ),
            "operator": "at_least",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b37\b",
                    r"\bthirty[- ]seven\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },
        {
            "clause": (
                "keep at most nine pending transport channels"
            ),
            "candidate": (
                "Keep eighteen pending transport channels."
            ),
            "prompt": (
                "State the maximum pending-transport-channel count."
            ),
            "operator": "at_most",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bnine\b",
                    r"\b9\b",
                ),
                (r"\bpending\b",),
                (r"\bchannel",),
            ),
        },
    ),

    "storage-finalization": (
        {
            "clause": (
                "finalize only with "
                "X-Echo-Seal: verified"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted verified "
                "finalization header."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Echo-Seal",),
                (r"\bverified\b",),
            ),
        },
        {
            "clause": (
                "do not finalize before "
                "receipt checksum verification"
            ),
            "candidate": (
                "Finalize before "
                "receipt checksum verification."
            ),
            "prompt": (
                "State the receipt-checksum "
                "finalization rule."
            ),
            "operator": "do_not",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bfinaliz",),
                (r"\bbefore\b",),
                (r"\breceipt\b",),
                (r"\bchecksum\b",),
            ),
        },
        {
            "clause": (
                "apply exactly thirteen signature blocks"
            ),
            "candidate": (
                "Apply four signature blocks."
            ),
            "prompt": (
                "State the exact signature-block count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bthirteen\b",
                    r"\b13\b",
                ),
                (r"\bsignature\b",),
            ),
        },
        {
            "clause": (
                "retain at least ten durable replicas"
            ),
            "candidate": (
                "Retain two durable replicas."
            ),
            "prompt": (
                "State the minimum durable-replica count."
            ),
            "operator": "at_least",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bten\b",
                    r"\b10\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },
        {
            "clause": (
                "do not purge the manifest unless "
                "the origin generation advances"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the origin-generation condition "
                "for manifest purging."
            ),
            "operator": "unless",
            "dimension": "condition",
            "grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (r"\borigin\b",),
                (r"\bgeneration\b",),
                (r"\badvance",),
                (r"\bpurg",),
            ),
        },
    ),
}


def _atoms_for(
    *,
    cluster,
    semantic_clause,
):
    if cluster == "retry-policy":

        return [
            "refresh the recovery marker",
            semantic_clause,
            "preserve the request fingerprint",
            "close the expired connection",
        ]

    if cluster == "lane-routing":

        return [
            "request a fresh routing checkpoint",
            semantic_clause,
            "preserve the original task fingerprint",
            "record the routing generation",
        ]

    if cluster == "channel-session":

        return [
            "preserve the transport fingerprint",
            semantic_clause,
            "send one diagnostic probe",
            "record the session generation",
        ]

    return [
        "verify the storage checksum",
        semantic_clause,
        "preserve the upload fingerprint",
        "record the committed generation",
    ]


def build_taskset():
    families = []

    serial = 801

    for (
        system_index,
        (
            system,
            prefix,
        ),
    ) in enumerate(
        SYSTEMS
    ):

        for cluster in CLUSTERS:

            rule = (
                RULES[
                    cluster
                ][
                    system_index
                ]
            )

            code = (
                f"{prefix}-{serial}"
            )

            family_id = (
                system.lower()
                +
                "-"
                +
                cluster
                +
                "-"
                +
                str(serial)
            )

            atoms = (
                _atoms_for(
                    cluster=cluster,

                    semantic_clause=(
                        rule[
                            "clause"
                        ]
                    ),
                )
            )

            family = (
                _add_fallback_challenges(
                    _family(
                        family_id=(
                            family_id
                        ),

                        system=system,
                        code=code,

                        candidate_decision=(
                            rule[
                                "candidate"
                            ]
                        ),

                        atoms=atoms,

                        semantic_atom_index=2,

                        semantic_operator=(
                            rule[
                                "operator"
                            ]
                        ),

                        semantic_dimension=(
                            rule[
                                "dimension"
                            ]
                        ),

                        transfer_prompt=(
                            rule[
                                "prompt"
                            ]
                        ),

                        semantic_grader=(
                            rule[
                                "grader"
                            ]
                        ),

                        operator_note=(
                            "neighboring memories contain "
                            "closely related operational rules"
                        ),

                        latency=(
                            300
                            +
                            (
                                serial
                                %
                                40
                            )
                        ),
                    )
                )
            )

            family[
                "system_name"
            ] = system

            family[
                "code_name"
            ] = code

            family[
                "interference_cluster"
            ] = cluster

            family[
                "degradation_mode"
            ] = (
                "context_only"
            )

            family[
                "entities"
            ] = [
                (
                    "system:"
                    +
                    system
                ),

                (
                    "code:"
                    +
                    code
                ),

                "domain:operations",

                (
                    "cluster:"
                    +
                    cluster
                ),
            ]

            family[
                "query_entities"
            ] = [
                "domain:operations",

                (
                    "cluster:"
                    +
                    cluster
                ),
            ]

            family[
                "query_prompt"
            ] = (
                rule[
                    "prompt"
                ]
            )

            families.append(
                family
            )

            serial += 1

    return {
        "experiment": (
            "seed-growth-025"
        ),

        "classification": (
            "exploratory-fresh-pareto-safe-"
            "context-assembly-ablation"
        ),

        "pool_size": 20,

        "candidate_neighborhood_size": 5,

        "ranking_representation": (
            "retrieval_handle_index"
        ),

        "fusion_policy": (
            "non_discriminative_channel_abstention"
        ),

        "rrf_k": 60,

        "fixed_top_k": 3,

        "dynamic_max_k": 3,

        "experimental_variable": (
            "context assembly policy only"
        ),

        "principle": (
            "Do not discard a memory if no other "
            "memory clearly beats it across every "
            "active retrieval signal."
        ),

        "conditions": {
            "A": (
                "Seed 022 abstaining RRF "
                "with fixed Top-K=3"
            ),

            "B": (
                "same complete fused ranking with "
                "Pareto-safe active-channel frontier "
                "context assembly"
            ),
        },

        "frozen_invariants": [
            "same learned memories",
            "same source evidence",
            "same Seed 020 routing",
            "same five-memory candidate neighborhood",
            "same Seed 021 retrieval-handle representation",
            "same semantic scores",
            "same lexical scores",
            "same entity scores",
            "same Seed 022 abstention policy",
            "same exact-tie midranks",
            "same RRF K",
            "same complete fused ranking",
            "same authoritative presentation representation",
            "same transfer query",
            "same reasoner",
            "same context budget configuration",
            "zero model calls for context assembly",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_025.json"
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
