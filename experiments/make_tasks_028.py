from __future__ import annotations

import copy
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
    ("FableWorks", "FW"),
    ("GarnetWorks", "GW"),
    ("HelixWorks", "HW"),
    ("IvoryWorks", "IW"),
    ("JuniperWorks", "JW"),
)


CLUSTERS = (
    "retry-policy",
    "lane-routing",
    "channel-session",
    "storage-finalization",
)


def _sig(
    *patterns,
):
    return {
        "all_of": list(
            patterns
        )
    }


RULES = {
    "retry-policy": (
        {
            "clause": (
                "retry exactly nineteen times"
            ),
            "candidate": (
                "Retry indefinitely."
            ),
            "prompt": (
                "State the exact retry-count rule."
            ),
            "operator": "exactly",
            "dimension": "cardinality",

            "signature": _sig(
                r"\bexactly\b",
                r"\b(?:nineteen|19)\b",
                r"\bretr",
            ),

            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bnineteen\b",
                    r"\b19\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "retry at most fifteen times"
            ),
            "candidate": (
                "Retry twenty-two times."
            ),
            "prompt": (
                "State the maximum retry-count rule."
            ),
            "operator": "at_most",
            "dimension": "cardinality",

            "signature": _sig(
                (
                    r"\b(?:at\s+most|maximum|"
                    r"no\s+more\s+than)\b"
                ),
                r"\b(?:fifteen|15)\b",
                r"\bretr",
            ),

            "grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bfifteen\b",
                    r"\b15\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "retry at least ten times"
            ),
            "candidate": (
                "Retry only twice."
            ),
            "prompt": (
                "State the minimum retry-count rule."
            ),
            "operator": "at_least",
            "dimension": "cardinality",

            "signature": _sig(
                r"\b(?:at\s+least|minimum)\b",
                r"\b(?:ten|10)\b",
                r"\bretr",
            ),

            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bten\b",
                    r"\b10\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "never retry a payload-rejected request"
            ),
            "candidate": (
                "Retry the payload-rejected request."
            ),
            "prompt": (
                "State the payload-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",

            "signature": _sig(
                r"\b(?:never|do\s+not)\b",
                r"\bretr",
                r"\bpayload\b",
                r"\breject",
            ),

            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bpayload\b",),
                (r"\breject",),
            ),
        },

        {
            "clause": (
                "retry only after renewing "
                "the recovery epoch"
            ),
            "candidate": (
                "Retry before renewing "
                "the recovery epoch."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-epoch renewal."
            ),
            "operator": "only",
            "dimension": "scope",

            "signature": _sig(
                r"\bonly\b",
                r"\bafter\b",
                r"\brenew",
                r"\brecovery\b",
                r"\bepoch\b",
            ),

            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brenew",),
                (r"\brecovery\b",),
                (r"\bepoch\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only "
                "through the sapphire lane"
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

            "signature": _sig(
                r"\bonly\b",
                r"\boverflow\b",
                r"\bsapphire\b",
                r"\blane\b",
            ),

            "grader": _grader(
                (r"\bonly\b",),
                (r"\boverflow\b",),
                (r"\bsapphire\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "route replay tasks only "
                "through the ochre lane"
            ),
            "candidate": (
                "Route replay tasks through "
                "the sapphire lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",

            "signature": _sig(
                r"\bonly\b",
                r"\breplay\b",
                r"\bochre\b",
                r"\blane\b",
            ),

            "grader": _grader(
                (r"\bonly\b",),
                (r"\breplay\b",),
                (r"\bochre\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "do not route poisoned tasks "
                "through the charcoal lane"
            ),
            "candidate": (
                "Route poisoned tasks through "
                "the charcoal lane."
            ),
            "prompt": (
                "State the charcoal-lane rule "
                "for poisoned tasks."
            ),
            "operator": "do_not",
            "dimension": "polarity",

            "signature": _sig(
                r"\b(?:do\s+not|never)\b",
                r"\bpoison",
                r"\bcharcoal\b",
                r"\blane\b",
            ),

            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bpoison",),
                (r"\bcharcoal\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "if the queue is fractured, "
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

            "signature": _sig(
                r"\b(?:if|when)\b",
                r"\bfractur",
                r"\bpearl\b",
                r"\blane\b",
            ),

            "grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (r"\bfractur",),
                (r"\bpearl\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "route quarantine tasks only "
                "through the sage lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the ochre lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for quarantine tasks."
            ),
            "operator": "only",
            "dimension": "scope",

            "signature": _sig(
                r"\bonly\b",
                r"\bquarantine\b",
                r"\bsage\b",
                r"\blane\b",
            ),

            "grader": _grader(
                (r"\bonly\b",),
                (r"\bquarantine\b",),
                (r"\bsage\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh relay channel "
                "after a credential mismatch"
            ),
            "candidate": (
                "Reuse the current relay channel "
                "after a credential mismatch."
            ),
            "prompt": (
                "State the channel rule "
                "after a credential mismatch."
            ),
            "operator": "only",
            "dimension": "scope",

            "signature": _sig(
                r"\bonly\b",
                r"\bfresh\b",
                r"\brelay\b",
                r"\bchannel\b",
                r"\bcredential\b",
                r"\bmismatch\b",
            ),

            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\brelay\b",),
                (r"\bchannel\b",),
                (r"\bcredential\b",),
                (r"\bmismatch\b",),
            ),
        },

        {
            "clause": (
                "never reuse the prior exchange nonce"
            ),
            "candidate": (
                "Reuse the prior exchange nonce."
            ),
            "prompt": (
                "State the exchange-nonce reuse rule."
            ),
            "operator": "never",
            "dimension": "polarity",

            "signature": _sig(
                r"\b(?:never|do\s+not)\b",
                r"\breuse\b",
                r"\bexchange\b",
                r"\bnonce\b",
            ),

            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bexchange\b",),
                (r"\bnonce\b",),
            ),
        },

        {
            "clause": (
                "send exactly nineteen heartbeat frames"
            ),
            "candidate": (
                "Send five heartbeat frames."
            ),
            "prompt": (
                "State the exact heartbeat-frame count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",

            "signature": _sig(
                r"\bexactly\b",
                r"\b(?:nineteen|19)\b",
                r"\bheartbeat\b",
            ),

            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bnineteen\b",
                    r"\b19\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },

        {
            "clause": (
                "wait at least 47 seconds "
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

            "signature": _sig(
                r"\b(?:at\s+least|minimum)\b",
                r"\b(?:47|forty[- ]seven)\b",
                r"\bseconds?\b",
                r"\breconnect",
            ),

            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b47\b",
                    r"\bforty[- ]seven\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },

        {
            "clause": (
                "keep at most fourteen "
                "pending relay channels"
            ),
            "candidate": (
                "Keep twenty-four "
                "pending relay channels."
            ),
            "prompt": (
                "State the maximum "
                "pending-relay-channel count."
            ),
            "operator": "at_most",
            "dimension": "cardinality",

            "signature": _sig(
                (
                    r"\b(?:at\s+most|maximum|"
                    r"no\s+more\s+than)\b"
                ),
                r"\b(?:fourteen|14)\b",
                r"\bpending\b",
                r"\bchannel",
            ),

            "grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bfourteen\b",
                    r"\b14\b",
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
                "X-Fable-Seal: accepted"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted accepted "
                "finalization header."
            ),
            "operator": "only",
            "dimension": "scope",

            "signature": _sig(
                r"\bonly\b",
                r"X-Fable-Seal",
                r"\baccepted\b",
            ),

            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Fable-Seal",),
                (r"\baccepted\b",),
            ),
        },

        {
            "clause": (
                "do not finalize before "
                "artifact-proof verification"
            ),
            "candidate": (
                "Finalize before "
                "artifact-proof verification."
            ),
            "prompt": (
                "State the artifact-proof "
                "finalization rule."
            ),
            "operator": "do_not",
            "dimension": "polarity",

            "signature": _sig(
                r"\b(?:do\s+not|never)\b",
                r"\bfinaliz",
                r"\bbefore\b",
                r"\bartifact\b",
                r"\bproof\b",
            ),

            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bfinaliz",),
                (r"\bbefore\b",),
                (r"\bartifact\b",),
                (r"\bproof\b",),
            ),
        },

        {
            "clause": (
                "apply exactly nineteen signature blocks"
            ),
            "candidate": (
                "Apply six signature blocks."
            ),
            "prompt": (
                "State the exact signature-block count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",

            "signature": _sig(
                r"\bexactly\b",
                r"\b(?:nineteen|19)\b",
                r"\bsignature\b",
            ),

            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bnineteen\b",
                    r"\b19\b",
                ),
                (r"\bsignature\b",),
            ),
        },

        {
            "clause": (
                "retain at least fifteen durable replicas"
            ),
            "candidate": (
                "Retain four durable replicas."
            ),
            "prompt": (
                "State the minimum "
                "durable-replica count."
            ),
            "operator": "at_least",
            "dimension": "cardinality",

            "signature": _sig(
                r"\b(?:at\s+least|minimum)\b",
                r"\b(?:fifteen|15)\b",
                r"\bdurable\b",
                r"\breplica",
            ),

            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bfifteen\b",
                    r"\b15\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },

        {
            "clause": (
                "do not purge the manifest unless "
                "the source cycle advances"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the source-cycle condition "
                "for manifest purging."
            ),
            "operator": "unless",
            "dimension": "condition",

            "signature": _sig(
                r"\b(?:unless|only\s+if)\b",
                r"\bsource\b",
                r"\bcycle\b",
                r"\badvance",
                r"\bpurg",
            ),

            "grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (r"\bsource\b",),
                (r"\bcycle\b",),
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
        "record the committed cycle",
    ]


def build_taskset():
    families = []

    serial = 1101

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
                            "and represent potentially "
                            "competing decision rules"
                        ),

                        latency=(
                            360
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

            family[
                "decision_signature"
            ] = copy.deepcopy(
                rule[
                    "signature"
                ]
            )

            families.append(
                family
            )

            serial += 1

    # ================================================================
    # STRICT POST-HOC COMPETING-RULE GRADER
    # ================================================================

    by_cluster = {}

    for family in families:

        by_cluster.setdefault(
            family[
                "interference_cluster"
            ],
            [],
        ).append(
            family
        )

    for family in families:

        family[
            "competing_signatures"
        ] = []

        for competitor in (
            by_cluster[
                family[
                    "interference_cluster"
                ]
            ]
        ):

            if (
                competitor[
                    "id"
                ]
                ==
                family[
                    "id"
                ]
            ):

                continue

            family[
                "competing_signatures"
            ].append(
                {
                    "family_id": (
                        competitor[
                            "id"
                        ]
                    ),

                    "semantic_clause": (
                        competitor[
                            "semantic_clause"
                        ]
                    ),

                    "all_of": copy.deepcopy(
                        competitor[
                            "decision_signature"
                        ][
                            "all_of"
                        ]
                    ),
                }
            )

    return {
        "experiment": (
            "seed-growth-028"
        ),

        "classification": (
            "exploratory-fresh-competing-"
            "hypothesis-reasoning-ablation"
        ),

        "pool_size": 20,

        "candidate_neighborhood_size": 5,

        "top_k": 3,

        "rrf_k": 60,

        "retrieval_policy": (
            "proposition_local_max_handle_scoring"
        ),

        "fusion_policy": (
            "non_discriminative_channel_abstention"
        ),

        "assembly_policy": (
            "evidence_quorum_guarded_pareto"
        ),

        "min_active_channels_for_pruning": 2,

        "experimental_variable": (
            "competing-hypothesis "
            "epistemic reasoning frame only"
        ),

        "principle": (
            "Preserve alternatives without "
            "conflating them."
        ),

        "conditions": {
            "A": (
                "Seed 027 reasoning over "
                "the selected memory context"
            ),

            "B": (
                "same selected memory context and "
                "same base question plus fixed "
                "competing-hypothesis instruction"
            ),
        },

        "strict_success_definition": (
            "target decision signature present "
            "and zero competing decision signatures "
            "present in final answer"
        ),

        "frozen_invariants": [
            "same learned memory bundles",
            "same source evidence",
            "same Seed 020 addressing",
            "same five-memory candidate neighborhoods",
            "same Seed 021 retrieval handles",
            "same Seed 026 proposition-local scoring",
            "same Seed 022 channel abstention",
            "same RRF K",
            "same Seed 027 evidence quorum",
            "same selected candidate IDs",
            "same snapshot",
            "same reasoner model",
            "same context budget configuration",
            "same base transfer question",
            "strict grader metadata removed before runtime",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_028.json"
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
