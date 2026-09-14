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
    ("UmberWorks", "UW"),
    ("VelaWorks", "VW"),
    ("WillowWorks", "WW"),
    ("XeniaWorks", "XW"),
    ("YarrowWorks", "YW"),
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
            "clause": "retry exactly six times",
            "candidate": "Retry until success.",
            "prompt": "State the exact retry-count rule.",
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (r"\bsix\b", r"\b6\b"),
                (r"\bretr",),
            ),
        },
        {
            "clause": "retry at most seven times",
            "candidate": "Retry ten times.",
            "prompt": "State the maximum retry-count rule.",
            "operator": "at_most",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (r"\bseven\b", r"\b7\b"),
                (r"\bretr",),
            ),
        },
        {
            "clause": "retry at least four times",
            "candidate": "Retry only once.",
            "prompt": "State the minimum retry-count rule.",
            "operator": "at_least",
            "dimension": "cardinality",
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (r"\bfour\b", r"\b4\b"),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "never retry a certificate-rejected request"
            ),
            "candidate": (
                "Retry the certificate-rejected request."
            ),
            "prompt": (
                "State the certificate-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bcertificate\b",),
                (r"\breject",),
            ),
        },
        {
            "clause": (
                "retry only after refreshing "
                "the recovery generation"
            ),
            "candidate": (
                "Retry before refreshing "
                "the recovery generation."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-generation refresh."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brefresh",),
                (r"\brecovery\b",),
                (r"\bgeneration\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only through the coral lane"
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
                (r"\bcoral\b",),
                (r"\blane\b",),
                (r"\boverflow\b",),
            ),
        },
        {
            "clause": (
                "route replay tasks only through the indigo lane"
            ),
            "candidate": (
                "Route replay tasks through the coral lane."
            ),
            "prompt": (
                "State the permitted lane for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bindigo\b",),
                (r"\blane\b",),
                (r"\breplay\b",),
            ),
        },
        {
            "clause": (
                "do not route poisoned tasks "
                "through the copper lane"
            ),
            "candidate": (
                "Route poisoned tasks through the copper lane."
            ),
            "prompt": (
                "State the copper-lane rule for poisoned tasks."
            ),
            "operator": "do_not",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bpoison",),
                (r"\bcopper\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "if the queue is starved, "
                "route the task through the alabaster lane"
            ),
            "candidate": (
                "Always route the task through "
                "the alabaster lane."
            ),
            "prompt": (
                "State when the alabaster lane "
                "should be used."
            ),
            "operator": "when_if",
            "dimension": "condition",
            "grader": _grader(
                (r"\bif\b", r"\bwhen\b"),
                (r"\bstarved\b",),
                (r"\balabaster\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "route quarantine tasks only "
                "through the saffron lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the indigo lane."
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
                (r"\bsaffron\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh session channel "
                "after a lineage mismatch"
            ),
            "candidate": (
                "Reuse the current session channel "
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
                "never reuse the previous session token"
            ),
            "candidate": (
                "Reuse the previous session token."
            ),
            "prompt": (
                "State the previous-session-token reuse rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bsession\b",),
                (r"\btoken\b",),
            ),
        },
        {
            "clause": (
                "send exactly ten heartbeat frames"
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
                (r"\bten\b", r"\b10\b"),
                (r"\bheartbeat\b",),
            ),
        },
        {
            "clause": (
                "wait at least 29 seconds "
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
                    r"\b29\b",
                    r"\btwenty[- ]nine\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },
        {
            "clause": (
                "keep at most seven pending session channels"
            ),
            "candidate": (
                "Keep fourteen pending session channels."
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
                (r"\bseven\b", r"\b7\b"),
                (r"\bpending\b",),
                (r"\bchannel",),
            ),
        },
    ),

    "storage-finalization": (
        {
            "clause": (
                "finalize only with "
                "X-Umber-Seal: durable"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted durable "
                "finalization header."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Umber-Seal",),
                (r"\bdurable\b",),
            ),
        },
        {
            "clause": (
                "do not finalize before "
                "commit digest verification"
            ),
            "candidate": (
                "Finalize before commit digest verification."
            ),
            "prompt": (
                "State the commit-digest finalization rule."
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
                (r"\bcommit\b",),
                (r"\bdigest\b",),
            ),
        },
        {
            "clause": (
                "apply exactly ten signature blocks"
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
                (r"\bten\b", r"\b10\b"),
                (r"\bsignature\b",),
            ),
        },
        {
            "clause": (
                "retain at least eight durable replicas"
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
                (r"\beight\b", r"\b8\b"),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },
        {
            "clause": (
                "do not purge the manifest unless "
                "the source epoch increments"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the source-epoch condition "
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
                (r"\bepoch\b",),
                (r"\bincrement",),
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

    serial = 601

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
                            260
                            +
                            (
                                serial
                                %
                                50
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
            "seed-growth-023"
        ),

        "classification": (
            "exploratory-fresh-confidence-gated-"
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
            "context assembly boundary only"
        ),

        "principle": (
            "Confidence determines context breadth."
        ),

        "conditions": {
            "A": (
                "Seed 022 abstaining RRF "
                "with fixed Top-K=3"
            ),

            "B": (
                "same ranking and scores with "
                "largest-gap dynamic prefix K in {1,2,3}"
            ),
        },

        "dynamic_rule": (
            "Compute adjacent RRF score gaps after ranks "
            "1, 2, and 3. Select the prefix ending at the "
            "largest gap. On exact maximum-gap ties, choose "
            "the larger K."
        ),

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
            "same complete ranking",
            "same authoritative presentation representation",
            "same transfer query",
            "same reasoner",
            "same context budget configuration",
            "zero model calls for context-boundary selection",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_023.json"
    )

    payload = build_taskset()

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
