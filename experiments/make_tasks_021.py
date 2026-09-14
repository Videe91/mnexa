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
    (
        "KestrelWorks",
        "KW",
    ),
    (
        "LumenWorks",
        "LW",
    ),
    (
        "MarbleWorks",
        "MW",
    ),
    (
        "NimbusWorks",
        "NW",
    ),
    (
        "OrchidWorks",
        "OW",
    ),
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
                "retry exactly three times"
            ),
            "candidate": (
                "Retry until the operation succeeds."
            ),
            "prompt": (
                "State the exact retry-count rule."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bthree\b",
                    r"\b3\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "retry at most five times"
            ),
            "candidate": (
                "Retry eight times."
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
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "retry at least two times"
            ),
            "candidate": (
                "Retry only once."
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
                    r"\btwo\b",
                    r"\b2\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "never retry a checksum-rejected request"
            ),
            "candidate": (
                "Retry the checksum-rejected request."
            ),
            "prompt": (
                "State the checksum-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bchecksum\b",),
                (r"\breject",),
            ),
        },

        {
            "clause": (
                "retry only after rotating the recovery lease"
            ),
            "candidate": (
                "Retry before rotating the recovery lease."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-lease rotation."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brotat",),
                (r"\brecovery\b",),
                (r"\blease\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only through the amber lane"
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
                (r"\bamber\b",),
                (r"\blane\b",),
                (r"\boverflow\b",),
            ),
        },

        {
            "clause": (
                "route replay tasks only through the cobalt lane"
            ),
            "candidate": (
                "Route replay tasks through the amber lane."
            ),
            "prompt": (
                "State the permitted lane for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bcobalt\b",),
                (r"\blane\b",),
                (r"\breplay\b",),
            ),
        },

        {
            "clause": (
                "do not route poisoned tasks through the silver lane"
            ),
            "candidate": (
                "Route poisoned tasks through the silver lane."
            ),
            "prompt": (
                "State the silver-lane rule for poisoned tasks."
            ),
            "operator": "do_not",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bpoison",),
                (r"\bsilver\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "if the backlog is saturated, "
                "route the task through the ivory lane"
            ),
            "candidate": (
                "Always route the task through the ivory lane."
            ),
            "prompt": (
                "State when the ivory lane should be used "
                "for backlog pressure."
            ),
            "operator": "when_if",
            "dimension": "condition",
            "grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (r"\bbacklog\b",),
                (r"\bsaturated\b",),
                (r"\bivory\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "route quarantine tasks only through the jade lane"
            ),
            "candidate": (
                "Route quarantine tasks through the cobalt lane."
            ),
            "prompt": (
                "State the permitted lane for quarantine tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bquarantine\b",),
                (r"\bjade\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh transport channel "
                "after a generation mismatch"
            ),
            "candidate": (
                "Reuse the existing channel after a generation mismatch."
            ),
            "prompt": (
                "State the channel rule after a generation mismatch."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bchannel\b",),
                (r"\bgeneration\b",),
                (r"\bmismatch\b",),
            ),
        },

        {
            "clause": (
                "never reuse the prior handshake nonce"
            ),
            "candidate": (
                "Reuse the prior handshake nonce."
            ),
            "prompt": (
                "State the handshake-nonce reuse rule."
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
                (r"\bnonce\b",),
            ),
        },

        {
            "clause": (
                "send exactly seven heartbeat frames"
            ),
            "candidate": (
                "Send two heartbeat frames."
            ),
            "prompt": (
                "State the exact heartbeat-frame count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bseven\b",
                    r"\b7\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },

        {
            "clause": (
                "wait at least 19 seconds before reconnecting"
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
                    r"\b19\b",
                    r"\bnineteen\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },

        {
            "clause": (
                "keep at most five pending session channels"
            ),
            "candidate": (
                "Keep ten pending session channels."
            ),
            "prompt": (
                "State the maximum pending-session-channel count."
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
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (r"\bpending\b",),
                (r"\bchannel",),
            ),
        },
    ),

    "storage-finalization": (
        {
            "clause": (
                "finalize only with X-Kestrel-Seal: stable"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted stable finalization header."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Kestrel-Seal",),
                (r"\bstable\b",),
            ),
        },

        {
            "clause": (
                "do not finalize before digest verification"
            ),
            "candidate": (
                "Finalize before digest verification."
            ),
            "prompt": (
                "State the digest-verification finalization rule."
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
                (r"\bdigest\b",),
            ),
        },

        {
            "clause": (
                "apply exactly eight signature blocks"
            ),
            "candidate": (
                "Apply three signature blocks."
            ),
            "prompt": (
                "State the exact signature-block count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\beight\b",
                    r"\b8\b",
                ),
                (r"\bsignature\b",),
            ),
        },

        {
            "clause": (
                "retain at least six durable replicas"
            ),
            "candidate": (
                "Retain one durable replica."
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
                    r"\bsix\b",
                    r"\b6\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },

        {
            "clause": (
                "do not purge the manifest unless "
                "the origin epoch advances"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the origin-epoch condition "
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
                (r"\bepoch\b",),
                (
                    r"\badvance",
                    r"\bchang",
                ),
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
            "refresh the recovery lease",
            semantic_clause,
            "preserve the request fingerprint",
            "close the stale connection",
        ]

    if cluster == "lane-routing":

        return [
            "request a fresh routing checkpoint",
            semantic_clause,
            "preserve the original task ID",
            "record the routing generation",
        ]

    if cluster == "channel-session":

        return [
            "preserve the trace fingerprint",
            semantic_clause,
            "send one probe frame",
            "record the session generation",
        ]

    return [
        "verify the manifest digest",
        semantic_clause,
        "preserve the upload fingerprint",
        "record the final generation",
    ]


def build_taskset():
    families = []

    serial = 401

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
                str(
                    serial
                )
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

                        system=(
                            system
                        ),

                        code=(
                            code
                        ),

                        candidate_decision=(
                            rule[
                                "candidate"
                            ]
                        ),

                        atoms=(
                            atoms
                        ),

                        # Same convention proven by Seed 020.
                        # Semantic atom is the second atom.
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
                            "highly similar operational language"
                        ),

                        latency=(
                            220
                            +
                            (
                                serial
                                %
                                70
                            )
                        ),
                    )
                )
            )

            family[
                "system_name"
            ] = (
                system
            )

            family[
                "code_name"
            ] = (
                code
            )

            family[
                "interference_cluster"
            ] = (
                cluster
            )

            family[
                "degradation_mode"
            ] = (
                "context_only"
            )

            # Stored memory keeps complete addressing metadata.
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

            # Retrieval query deliberately has no exact identity.
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

            # No system/code leak into query text.
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
            "seed-growth-021"
        ),

        "classification": (
            "exploratory-fresh-retrieval-"
            "handle-separation-ablation"
        ),

        "pool_size": 20,

        "candidate_neighborhood_size": 5,

        "retrieval_top_k": 3,

        "rrf_k": 60,

        "query_mode": (
            "context_only"
        ),

        "principle": (
            "Retrieval handles locate knowledge; "
            "authoritative support supplies meaning."
        ),

        "conditions": {
            "A": (
                "conjunctive-routed five-memory "
                "neighborhood ranked using complete "
                "compact semantic memory"
            ),

            "B": (
                "same five-memory neighborhood and "
                "same three-channel RRF ranked using "
                "retrieval-handle index only"
            ),
        },

        "frozen_invariants": [
            "same learned memory bundles",
            "same conjunctive candidate routing",
            "same candidate population",
            "same semantic ranking algorithm",
            "same lexical ranking algorithm",
            "same entity ranking algorithm",
            "same RRF constant",
            "same top-k",
            "same authoritative presentation payload",
            "same transfer query",
            "same transfer reasoner",
            "same context budget",
            "zero model calls for retrieval-handle ranking",
        ],

        "primary_metrics": [
            "target selected into top-k",
            "target clause visible",
            "wrong memory presented",
            "retrieval precision",
            "retrieval recall",
            "semantic task success",
        ],

        "secondary_metrics": [
            "retrieval index word count",
            "wrong-rule contamination",
            "cluster-level performance",
            "selection rescue",
            "task rescue",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_021.json"
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
