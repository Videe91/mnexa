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
        "PeregrineWorks",
        "PW",
    ),
    (
        "QuartzWorks",
        "QW",
    ),
    (
        "RowanWorks",
        "RW",
    ),
    (
        "SolaceWorks",
        "SW",
    ),
    (
        "TundraWorks",
        "TW",
    ),
)


CLUSTERS = (
    "retry-policy",
    "lane-routing",
    "channel-session",
    "storage-finalization",
)


RETRY_RULES = (
    {
        "clause": (
            "retry exactly five times"
        ),
        "candidate": (
            "Retry continuously until success."
        ),
        "prompt": (
            "State the exact retry-count rule."
        ),
        "operator": "exactly",
        "dimension": "cardinality",
        "grader": _grader(
            (r"\bexactly\b",),
            (
                r"\bfive\b",
                r"\b5\b",
            ),
            (r"\bretr",),
        ),
    },

    {
        "clause": (
            "retry at most six times"
        ),
        "candidate": (
            "Retry nine times."
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
                r"\bsix\b",
                r"\b6\b",
            ),
            (r"\bretr",),
        ),
    },

    {
        "clause": (
            "retry at least three times"
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
                r"\bthree\b",
                r"\b3\b",
            ),
            (r"\bretr",),
        ),
    },

    {
        "clause": (
            "never retry a signature-rejected request"
        ),
        "candidate": (
            "Retry the signature-rejected request."
        ),
        "prompt": (
            "State the signature-rejection retry rule."
        ),
        "operator": "never",
        "dimension": "polarity",
        "grader": _grader(
            (
                r"\bnever\b",
                r"\bdo\s+not\b",
            ),
            (r"\bretry\b",),
            (r"\bsignature\b",),
            (r"\breject",),
        ),
    },

    {
        "clause": (
            "retry only after renewing the recovery epoch"
        ),
        "candidate": (
            "Retry before renewing the recovery epoch."
        ),
        "prompt": (
            "State when retrying is permitted "
            "relative to recovery-epoch renewal."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"\bafter\b",),
            (r"\brenew",),
            (r"\brecovery\b",),
            (r"\bepoch\b",),
        ),
    },
)


LANE_RULES = (
    {
        "clause": (
            "route overflow tasks only through the magenta lane"
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
            (r"\bmagenta\b",),
            (r"\blane\b",),
            (r"\boverflow\b",),
        ),
    },

    {
        "clause": (
            "route replay tasks only through the bronze lane"
        ),
        "candidate": (
            "Route replay tasks through the magenta lane."
        ),
        "prompt": (
            "State the permitted lane for replay tasks."
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
            "do not route poisoned tasks through the lilac lane"
        ),
        "candidate": (
            "Route poisoned tasks through the lilac lane."
        ),
        "prompt": (
            "State the lilac-lane rule for poisoned tasks."
        ),
        "operator": "do_not",
        "dimension": "polarity",
        "grader": _grader(
            (
                r"\bdo\s+not\b",
                r"\bnever\b",
            ),
            (r"\bpoison",),
            (r"\blilac\b",),
            (r"\blane\b",),
        ),
    },

    {
        "clause": (
            "if the queue is fractured, "
            "route the task through the pearl lane"
        ),
        "candidate": (
            "Always route the task through the pearl lane."
        ),
        "prompt": (
            "State when the pearl lane should be used "
            "for queue pressure."
        ),
        "operator": "when_if",
        "dimension": "condition",
        "grader": _grader(
            (
                r"\bif\b",
                r"\bwhen\b",
            ),
            (r"\bfractured\b",),
            (r"\bpearl\b",),
            (r"\blane\b",),
        ),
    },

    {
        "clause": (
            "route quarantine tasks only through the ochre lane"
        ),
        "candidate": (
            "Route quarantine tasks through the bronze lane."
        ),
        "prompt": (
            "State the permitted lane for quarantine tasks."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"\bquarantine\b",),
            (r"\bochre\b",),
            (r"\blane\b",),
        ),
    },
)


CHANNEL_RULES = (
    {
        "clause": (
            "open only a fresh session channel "
            "after a generation split"
        ),
        "candidate": (
            "Reuse the existing channel after a generation split."
        ),
        "prompt": (
            "State the channel rule after a generation split."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"\bfresh\b",),
            (r"\bchannel\b",),
            (r"\bgeneration\b",),
            (r"\bsplit\b",),
        ),
    },

    {
        "clause": (
            "never reuse the previous epoch nonce"
        ),
        "candidate": (
            "Reuse the previous epoch nonce."
        ),
        "prompt": (
            "State the epoch-nonce reuse rule."
        ),
        "operator": "never",
        "dimension": "polarity",
        "grader": _grader(
            (
                r"\bnever\b",
                r"\bdo\s+not\b",
            ),
            (r"\breuse\b",),
            (r"\bepoch\b",),
            (r"\bnonce\b",),
        ),
    },

    {
        "clause": (
            "send exactly nine heartbeat frames"
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
                r"\bnine\b",
                r"\b9\b",
            ),
            (r"\bheartbeat\b",),
        ),
    },

    {
        "clause": (
            "wait at least 23 seconds before reconnecting"
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
                r"\b23\b",
                r"\btwenty[- ]three\b",
            ),
            (r"\bseconds?\b",),
            (r"\breconnect",),
        ),
    },

    {
        "clause": (
            "keep at most six pending session channels"
        ),
        "candidate": (
            "Keep twelve pending session channels."
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
                r"\bsix\b",
                r"\b6\b",
            ),
            (r"\bpending\b",),
            (r"\bchannel",),
        ),
    },
)


STORAGE_RULES = (
    {
        "clause": (
            "finalize only with X-Peregrine-Seal: committed"
        ),
        "candidate": (
            "Finalize with any completion header."
        ),
        "prompt": (
            "State the permitted committed finalization header."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"X-Peregrine-Seal",),
            (r"\bcommitted\b",),
        ),
    },

    {
        "clause": (
            "do not finalize before ledger digest verification"
        ),
        "candidate": (
            "Finalize before ledger digest verification."
        ),
        "prompt": (
            "State the ledger-digest finalization rule."
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
            (r"\bledger\b",),
            (r"\bdigest\b",),
        ),
    },

    {
        "clause": (
            "apply exactly nine signature blocks"
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
                r"\bnine\b",
                r"\b9\b",
            ),
            (r"\bsignature\b",),
        ),
    },

    {
        "clause": (
            "retain at least seven durable replicas"
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
                r"\bseven\b",
                r"\b7\b",
            ),
            (r"\bdurable\b",),
            (r"\breplica",),
        ),
    },

    {
        "clause": (
            "do not purge the manifest unless "
            "the origin epoch rolls forward"
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
                r"\broll",
                r"\bforward\b",
            ),
            (r"\bpurg",),
        ),
    },
)


RULES = {
    "retry-policy": (
        RETRY_RULES
    ),

    "lane-routing": (
        LANE_RULES
    ),

    "channel-session": (
        CHANNEL_RULES
    ),

    "storage-finalization": (
        STORAGE_RULES
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
            "record the routing epoch",
        ]

    if cluster == "channel-session":

        return [
            "preserve the transport fingerprint",
            semantic_clause,
            "send one diagnostic probe",
            "record the session epoch",
        ]

    return [
        "verify the storage digest",
        semantic_clause,
        "preserve the upload fingerprint",
        "record the committed generation",
    ]


def build_taskset():
    families = []

    serial = 501

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

                        # Existing convention in Seeds 020/021.
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
                            "neighboring memories use "
                            "similar operational vocabulary"
                        ),

                        latency=(
                            240
                            +
                            (
                                serial
                                %
                                60
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

            # Memory-side metadata.
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

            # Query-side metadata intentionally provides
            # exactly the same entity overlap for all five
            # members of the neighborhood.
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
            "seed-growth-022"
        ),

        "classification": (
            "exploratory-fresh-non-discriminative-"
            "channel-abstention-ablation"
        ),

        "pool_size": 20,

        "candidate_neighborhood_size": 5,

        "retrieval_top_k": 3,

        "rrf_k": 60,

        "ranking_representation": (
            "retrieval_handle_index"
        ),

        "experimental_variable": (
            "RRF tie and abstention policy only"
        ),

        "principle": (
            "No discrimination, no vote."
        ),

        "conditions": {
            "A": (
                "Seed 021 handle-index channel scores "
                "with sequential deterministic tie ranking"
            ),

            "B": (
                "identical channel scores with full-channel "
                "abstention and exact-tie midranks"
            ),
        },

        "frozen_invariants": [
            "same learned memories",
            "same evidence",
            "same Seed 020 candidate routing",
            "same five-memory candidate neighborhood",
            "same retrieval-handle documents",
            "same query",
            "same semantic scores",
            "same lexical scores",
            "same entity scores",
            "same RRF K",
            "same top K",
            "same authoritative presentation payload",
            "same transfer reasoner",
            "same context budget",
            "zero ranking model calls",
        ],

        "primary_metrics": [
            "target selected into top K",
            "target semantic clause visible",
            "semantic task success",
            "wrong-memory presentation",
            "wrong-rule contamination",
        ],

        "fusion_metrics": [
            "abstention count by channel",
            "artificial sequential tie count by channel",
            "active channel count",
            "selection rescue",
            "selection harm",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_022.json"
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
