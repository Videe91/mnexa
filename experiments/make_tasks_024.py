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
    ("ZenithWorks", "ZW"),
    ("AlderWorks", "AW"),
    ("BrambleWorks", "BW"),
    ("CobaltWorks", "CW"),
    ("DeltaWorks", "DW"),
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
                "retry exactly eight times"
            ),
            "candidate": (
                "Retry until success."
            ),
            "prompt": (
                "State the exact retry-count rule."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\beight\b",
                    r"\b8\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "retry at most nine times"
            ),
            "candidate": (
                "Retry twelve times."
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
                    r"\bnine\b",
                    r"\b9\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "retry at least five times"
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
                    r"\bfive\b",
                    r"\b5\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "never retry a policy-rejected request"
            ),
            "candidate": (
                "Retry the policy-rejected request."
            ),
            "prompt": (
                "State the policy-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bpolicy\b",),
                (r"\breject",),
            ),
        },
        {
            "clause": (
                "retry only after rotating "
                "the recovery token"
            ),
            "candidate": (
                "Retry before rotating "
                "the recovery token."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-token rotation."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brotat",),
                (r"\brecovery\b",),
                (r"\btoken\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only "
                "through the violet lane"
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
                (r"\bviolet\b",),
                (r"\blane\b",),
                (r"\boverflow\b",),
            ),
        },
        {
            "clause": (
                "route replay tasks only "
                "through the cyan lane"
            ),
            "candidate": (
                "Route replay tasks through "
                "the violet lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bcyan\b",),
                (r"\blane\b",),
                (r"\breplay\b",),
            ),
        },
        {
            "clause": (
                "do not route poisoned tasks "
                "through the maroon lane"
            ),
            "candidate": (
                "Route poisoned tasks through "
                "the maroon lane."
            ),
            "prompt": (
                "State the maroon-lane rule "
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
                (r"\bmaroon\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "if the queue is cold, "
                "route the task through the silver lane"
            ),
            "candidate": (
                "Always route the task "
                "through the silver lane."
            ),
            "prompt": (
                "State when the silver lane "
                "should be used."
            ),
            "operator": "when_if",
            "dimension": "condition",
            "grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (r"\bcold\b",),
                (r"\bsilver\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "route quarantine tasks only "
                "through the lime lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the cyan lane."
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
                (r"\blime\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh session channel "
                "after a lease mismatch"
            ),
            "candidate": (
                "Reuse the current session channel "
                "after a lease mismatch."
            ),
            "prompt": (
                "State the channel rule "
                "after a lease mismatch."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bchannel\b",),
                (r"\blease\b",),
                (r"\bmismatch\b",),
            ),
        },
        {
            "clause": (
                "never reuse the prior handshake key"
            ),
            "candidate": (
                "Reuse the prior handshake key."
            ),
            "prompt": (
                "State the handshake-key reuse rule."
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
                (r"\bkey\b",),
            ),
        },
        {
            "clause": (
                "send exactly twelve heartbeat frames"
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
                    r"\btwelve\b",
                    r"\b12\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },
        {
            "clause": (
                "wait at least 31 seconds "
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
                    r"\b31\b",
                    r"\bthirty[- ]one\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },
        {
            "clause": (
                "keep at most eight "
                "pending session channels"
            ),
            "candidate": (
                "Keep sixteen pending session channels."
            ),
            "prompt": (
                "State the maximum "
                "pending-session-channel count."
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
                    r"\beight\b",
                    r"\b8\b",
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
                "X-Zenith-Seal: locked"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted locked "
                "finalization header."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Zenith-Seal",),
                (r"\blocked\b",),
            ),
        },
        {
            "clause": (
                "do not finalize before "
                "receipt digest verification"
            ),
            "candidate": (
                "Finalize before "
                "receipt digest verification."
            ),
            "prompt": (
                "State the receipt-digest "
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
                (r"\bdigest\b",),
            ),
        },
        {
            "clause": (
                "apply exactly twelve signature blocks"
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
                    r"\btwelve\b",
                    r"\b12\b",
                ),
                (r"\bsignature\b",),
            ),
        },
        {
            "clause": (
                "retain at least nine durable replicas"
            ),
            "candidate": (
                "Retain one durable replica."
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
                    r"\bnine\b",
                    r"\b9\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },
        {
            "clause": (
                "do not purge the manifest unless "
                "the source generation increments"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the source-generation condition "
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
                (r"\bgeneration\b",),
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
        "verify the storage digest",
        semantic_clause,
        "preserve the upload fingerprint",
        "record the committed generation",
    ]


def build_taskset():
    families = []

    serial = 701

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
                            280
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
            "seed-growth-024"
        ),

        "classification": (
            "exploratory-fresh-channel-consensus-"
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
            "Agreement permits compression. "
            "Disagreement preserves breadth."
        ),

        "conditions": {
            "A": (
                "Seed 022 abstaining RRF "
                "with fixed Top-K=3"
            ),

            "B": (
                "same fused ranking with smallest "
                "Top-K prefix preserving every active "
                "channel top winner, bounded by K=3"
            ),
        },

        "consensus_rule": (
            "Find every top-ranked memory from each active "
            "discriminative retrieval channel. Choose the "
            "smallest fused-ranking prefix containing all "
            "such winners when they lie inside Top-3. "
            "If any channel winner lies outside Top-3, "
            "retain Top-3."
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
            "same complete fused ranking",
            "same authoritative presentation representation",
            "same transfer query",
            "same reasoner",
            "same context budget configuration",
            "zero model calls for context-boundary selection",
        ],

        "primary_metrics": [
            "target retention",
            "over-pruning",
            "safe compaction",
            "context K",
            "distractor reduction",
        ],

        "secondary_metrics": [
            "semantic task success",
            "target visibility",
            "wrong memory presentation",
            "wrong rule contamination",
            "memory words",
            "memory segments",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_024.json"
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
