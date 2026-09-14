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
    ("QuartzWorks", "QW"),
    ("RookWorks", "RW"),
    ("SableWorks", "SW"),
    ("TundraWorks", "TW"),
    ("ValeWorks", "VW"),
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
            "clause": (
                "retry exactly fourteen times"
            ),
            "candidate": (
                "Retry indefinitely."
            ),
            "prompt": (
                "State the exact retry-count rule."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bfourteen\b",
                    r"\b14\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "retry at most twelve times"
            ),
            "candidate": (
                "Retry sixteen times."
            ),
            "prompt": (
                "State the maximum retry-count rule."
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
                    r"\btwelve\b",
                    r"\b12\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "retry at least seven times"
            ),
            "candidate": (
                "Retry only twice."
            ),
            "prompt": (
                "State the minimum retry-count rule."
            ),
            "operator": "at_least",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bseven\b",
                    r"\b7\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "never retry an integrity-rejected request"
            ),
            "candidate": (
                "Retry the integrity-rejected request."
            ),
            "prompt": (
                "State the integrity-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bintegrity\b",),
                (r"\breject",),
            ),
        },
        {
            "clause": (
                "retry only after renewing "
                "the recovery lease"
            ),
            "candidate": (
                "Retry before renewing "
                "the recovery lease."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-lease renewal."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brenew",),
                (r"\brecovery\b",),
                (r"\blease\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only "
                "through the teal lane"
            ),
            "candidate": (
                "Route overflow tasks through any lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for overflow tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bteal\b",),
                (r"\blane\b",),
                (r"\boverflow\b",),
            ),
        },
        {
            "clause": (
                "route replay tasks only "
                "through the bronze lane"
            ),
            "candidate": (
                "Route replay tasks through "
                "the teal lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bbronze\b",),
                (r"\blane\b",),
                (r"\breplay\b",),
            ),
        },
        {
            "clause": (
                "do not route poisoned tasks "
                "through the magenta lane"
            ),
            "candidate": (
                "Route poisoned tasks through "
                "the magenta lane."
            ),
            "prompt": (
                "State the magenta-lane rule "
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
                (r"\bmagenta\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "if the queue is fragmented, "
                "route the task through the pearl lane"
            ),
            "candidate": (
                "Always route the task "
                "through the pearl lane."
            ),
            "prompt": (
                "State when the pearl lane "
                "should be used."
            ),
            "operator": "when_if",
            "dimension": "condition",
            "grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (r"\bfragment",),
                (r"\bpearl\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "route quarantine tasks only "
                "through the olive lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the bronze lane."
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
                (r"\bolive\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh transport channel "
                "after an epoch mismatch"
            ),
            "candidate": (
                "Reuse the current transport channel "
                "after an epoch mismatch."
            ),
            "prompt": (
                "State the channel rule "
                "after an epoch mismatch."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bchannel\b",),
                (r"\bepoch\b",),
                (r"\bmismatch\b",),
            ),
        },
        {
            "clause": (
                "never reuse the previous challenge nonce"
            ),
            "candidate": (
                "Reuse the previous challenge nonce."
            ),
            "prompt": (
                "State the challenge-nonce reuse rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bchallenge\b",),
                (r"\bnonce\b",),
            ),
        },
        {
            "clause": (
                "send exactly fifteen heartbeat frames"
            ),
            "candidate": (
                "Send four heartbeat frames."
            ),
            "prompt": (
                "State the exact heartbeat-frame count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bfifteen\b",
                    r"\b15\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },
        {
            "clause": (
                "wait at least 41 seconds "
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
                    r"\b41\b",
                    r"\bforty[- ]one\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },
        {
            "clause": (
                "keep at most eleven "
                "pending transport channels"
            ),
            "candidate": (
                "Keep twenty pending "
                "transport channels."
            ),
            "prompt": (
                "State the maximum "
                "pending-transport-channel count."
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
                    r"\beleven\b",
                    r"\b11\b",
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
                "X-Quartz-Seal: sealed"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted sealed "
                "finalization header."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Quartz-Seal",),
                (r"\bsealed\b",),
            ),
        },
        {
            "clause": (
                "do not finalize before "
                "checksum-proof verification"
            ),
            "candidate": (
                "Finalize before "
                "checksum-proof verification."
            ),
            "prompt": (
                "State the checksum-proof "
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
                (r"\bchecksum\b",),
                (r"\bproof\b",),
            ),
        },
        {
            "clause": (
                "apply exactly fifteen signature blocks"
            ),
            "candidate": (
                "Apply five signature blocks."
            ),
            "prompt": (
                "State the exact signature-block count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bfifteen\b",
                    r"\b15\b",
                ),
                (r"\bsignature\b",),
            ),
        },
        {
            "clause": (
                "retain at least twelve durable replicas"
            ),
            "candidate": (
                "Retain three durable replicas."
            ),
            "prompt": (
                "State the minimum "
                "durable-replica count."
            ),
            "operator": "at_least",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\btwelve\b",
                    r"\b12\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },
        {
            "clause": (
                "do not purge the manifest unless "
                "the source revision advances"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the source-revision condition "
                "for manifest purging."
            ),
            "operator": "unless",
            "dimension": "condition",
            "grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (r"\bsource\b",),
                (r"\brevision\b",),
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
        "record the committed revision",
    ]


def build_taskset():
    families = []

    serial = 901

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
                            "neighboring memories share "
                            "three background propositions "
                            "and differ primarily in one "
                            "decision-relevant proposition"
                        ),

                        latency=(
                            320
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
            "seed-growth-026"
        ),

        "classification": (
            "exploratory-fresh-proposition-local-"
            "retrieval-ablation"
        ),

        "pool_size": 20,

        "candidate_neighborhood_size": 5,

        "top_k": 3,

        "rrf_k": 60,

        "fusion_policy": (
            "non_discriminative_channel_abstention"
        ),

        "assembly_policy": (
            "pareto_safe_active_channel_frontier"
        ),

        "experimental_variable": (
            "semantic and lexical retrieval "
            "scoring granularity only"
        ),

        "principle": (
            "Retrieve the proposition, "
            "not the memory blob."
        ),

        "conditions": {
            "A": (
                "existing whole retrieval-handle "
                "document semantic/lexical scoring"
            ),

            "B": (
                "same underlying retrieval handles "
                "scored independently with memory score "
                "equal to best proposition-level match"
            ),
        },

        "frozen_invariants": [
            "same learned memory bundles",
            "same source evidence",
            "same Seed 020 addressing",
            "same five-memory candidate neighborhoods",
            "same Seed 021 retrieval handles",
            "same query",
            "same embedder",
            "same lexical similarity function",
            "same entity channel",
            "same Seed 022 abstention",
            "same exact-tie midranks",
            "same RRF K",
            "same Seed 025 Pareto assembly",
            "same authoritative reasoning payload",
            "same reasoner",
            "same context budget configuration",
            "zero ranker model calls",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_026.json"
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
