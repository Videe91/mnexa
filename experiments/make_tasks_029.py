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
    ("KestrelWorks", "KW"),
    ("LumenWorks", "LW"),
    ("MeridianWorks", "MW"),
    ("NovaWorks", "NW"),
    ("OnyxWorks", "OW"),
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
                "retry exactly twenty-one times"
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
                r"\b(?:twenty[- ]one|21)\b",
                r"\bretr",
            ),
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\btwenty[- ]one\b",
                    r"\b21\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "retry at most sixteen times"
            ),
            "candidate": (
                "Retry twenty-five times."
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
                r"\b(?:sixteen|16)\b",
                r"\bretr",
            ),
            "grader": _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                    r"\bno\s+more\s+than\b",
                ),
                (
                    r"\bsixteen\b",
                    r"\b16\b",
                ),
                (r"\bretr",),
            ),
        },

        {
            "clause": (
                "retry at least eleven times"
            ),
            "candidate": (
                "Retry only three times."
            ),
            "prompt": (
                "State the minimum retry-count rule."
            ),
            "operator": "at_least",
            "dimension": "cardinality",
            "signature": _sig(
                r"\b(?:at\s+least|minimum)\b",
                r"\b(?:eleven|11)\b",
                r"\bretr",
            ),
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\beleven\b",
                    r"\b11\b",
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
            "signature": _sig(
                r"\b(?:never|do\s+not)\b",
                r"\bretr",
                r"\bchecksum\b",
                r"\breject",
            ),
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
                "retry only after rotating "
                "the recovery lease"
            ),
            "candidate": (
                "Retry before rotating "
                "the recovery lease."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-lease rotation."
            ),
            "operator": "only",
            "dimension": "scope",
            "signature": _sig(
                r"\bonly\b",
                r"\bafter\b",
                r"\brotat",
                r"\brecovery\b",
                r"\blease\b",
            ),
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
            "signature": _sig(
                r"\bonly\b",
                r"\boverflow\b",
                r"\bviolet\b",
                r"\blane\b",
            ),
            "grader": _grader(
                (r"\bonly\b",),
                (r"\boverflow\b",),
                (r"\bviolet\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "route replay tasks only "
                "through the rust lane"
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
            "signature": _sig(
                r"\bonly\b",
                r"\breplay\b",
                r"\brust\b",
                r"\blane\b",
            ),
            "grader": _grader(
                (r"\bonly\b",),
                (r"\breplay\b",),
                (r"\brust\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "do not route poisoned tasks "
                "through the cobalt lane"
            ),
            "candidate": (
                "Route poisoned tasks through "
                "the cobalt lane."
            ),
            "prompt": (
                "State the cobalt-lane rule "
                "for poisoned tasks."
            ),
            "operator": "do_not",
            "dimension": "polarity",
            "signature": _sig(
                r"\b(?:do\s+not|never)\b",
                r"\bpoison",
                r"\bcobalt\b",
                r"\blane\b",
            ),
            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bpoison",),
                (r"\bcobalt\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "if the queue is fractured, "
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
            "signature": _sig(
                r"\b(?:if|when)\b",
                r"\bfractur",
                r"\bsilver\b",
                r"\blane\b",
            ),
            "grader": _grader(
                (
                    r"\bif\b",
                    r"\bwhen\b",
                ),
                (r"\bfractur",),
                (r"\bsilver\b",),
                (r"\blane\b",),
            ),
        },

        {
            "clause": (
                "route quarantine tasks only "
                "through the fern lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the rust lane."
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
                r"\bfern\b",
                r"\blane\b",
            ),
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bquarantine\b",),
                (r"\bfern\b",),
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
            "signature": _sig(
                r"\bonly\b",
                r"\bfresh\b",
                r"\bsession\b",
                r"\bchannel\b",
                r"\blineage\b",
                r"\bmismatch\b",
            ),
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bsession\b",),
                (r"\bchannel\b",),
                (r"\blineage\b",),
                (r"\bmismatch\b",),
            ),
        },

        {
            "clause": (
                "never reuse the prior handshake proof"
            ),
            "candidate": (
                "Reuse the prior handshake proof."
            ),
            "prompt": (
                "State the handshake-proof reuse rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "signature": _sig(
                r"\b(?:never|do\s+not)\b",
                r"\breuse\b",
                r"\bhandshake\b",
                r"\bproof\b",
            ),
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bhandshake\b",),
                (r"\bproof\b",),
            ),
        },

        {
            "clause": (
                "send exactly twenty-one heartbeat frames"
            ),
            "candidate": (
                "Send seven heartbeat frames."
            ),
            "prompt": (
                "State the exact heartbeat-frame count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "signature": _sig(
                r"\bexactly\b",
                r"\b(?:twenty[- ]one|21)\b",
                r"\bheartbeat\b",
            ),
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\btwenty[- ]one\b",
                    r"\b21\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },

        {
            "clause": (
                "wait at least 53 seconds "
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
                r"\b(?:53|fifty[- ]three)\b",
                r"\bseconds?\b",
                r"\breconnect",
            ),
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\b53\b",
                    r"\bfifty[- ]three\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },

        {
            "clause": (
                "keep at most sixteen "
                "pending session channels"
            ),
            "candidate": (
                "Keep twenty-eight "
                "pending session channels."
            ),
            "prompt": (
                "State the maximum "
                "pending-session-channel count."
            ),
            "operator": "at_most",
            "dimension": "cardinality",
            "signature": _sig(
                (
                    r"\b(?:at\s+most|maximum|"
                    r"no\s+more\s+than)\b"
                ),
                r"\b(?:sixteen|16)\b",
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
                    r"\bsixteen\b",
                    r"\b16\b",
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
                "X-Kestrel-Seal: durable"
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
            "signature": _sig(
                r"\bonly\b",
                r"X-Kestrel-Seal",
                r"\bdurable\b",
            ),
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Kestrel-Seal",),
                (r"\bdurable\b",),
            ),
        },

        {
            "clause": (
                "do not finalize before "
                "lineage-proof verification"
            ),
            "candidate": (
                "Finalize before "
                "lineage-proof verification."
            ),
            "prompt": (
                "State the lineage-proof "
                "finalization rule."
            ),
            "operator": "do_not",
            "dimension": "polarity",
            "signature": _sig(
                r"\b(?:do\s+not|never)\b",
                r"\bfinaliz",
                r"\bbefore\b",
                r"\blineage\b",
                r"\bproof\b",
            ),
            "grader": _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bfinaliz",),
                (r"\bbefore\b",),
                (r"\blineage\b",),
                (r"\bproof\b",),
            ),
        },

        {
            "clause": (
                "apply exactly twenty-one signature blocks"
            ),
            "candidate": (
                "Apply eight signature blocks."
            ),
            "prompt": (
                "State the exact signature-block count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "signature": _sig(
                r"\bexactly\b",
                r"\b(?:twenty[- ]one|21)\b",
                r"\bsignature\b",
            ),
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\btwenty[- ]one\b",
                    r"\b21\b",
                ),
                (r"\bsignature\b",),
            ),
        },

        {
            "clause": (
                "retain at least seventeen durable replicas"
            ),
            "candidate": (
                "Retain five durable replicas."
            ),
            "prompt": (
                "State the minimum "
                "durable-replica count."
            ),
            "operator": "at_least",
            "dimension": "cardinality",
            "signature": _sig(
                r"\b(?:at\s+least|minimum)\b",
                r"\b(?:seventeen|17)\b",
                r"\bdurable\b",
                r"\breplica",
            ),
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bseventeen\b",
                    r"\b17\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },

        {
            "clause": (
                "do not purge the manifest unless "
                "the source epoch advances"
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
            "signature": _sig(
                r"\b(?:unless|only\s+if)\b",
                r"\bsource\b",
                r"\bepoch\b",
                r"\badvance",
                r"\bpurg",
            ),
            "grader": _grader(
                (
                    r"\bunless\b",
                    r"\bonly\s+if\b",
                ),
                (r"\bsource\b",),
                (r"\bepoch\b",),
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
            "preserve the session fingerprint",
            semantic_clause,
            "send one diagnostic probe",
            "record the session generation",
        ]

    return [
        "verify the storage checksum",
        semantic_clause,
        "preserve the upload fingerprint",
        "record the committed epoch",
    ]


def build_taskset():
    families = []

    serial = 1201

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
                            380
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

        competitors = []

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

            competitors.append(
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

        family[
            "competing_signatures"
        ] = (
            competitors
        )

    return {
        "experiment": (
            "seed-growth-029"
        ),

        "classification": (
            "exploratory-fresh-frozen-"
            "context-reasoning-ablation"
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

        "context_preparations_per_family": 1,

        "reasoning_calls_per_family": 2,

        "experimental_variable": (
            "external model reasoning instruction only"
        ),

        "principle": (
            "MNEXA fixes the evidence. "
            "The model is free to change how it "
            "reasons over that evidence."
        ),

        "conditions": {
            "A": (
                "one frozen MNEXA ContextFrame "
                "plus standard model reasoning"
            ),

            "B": (
                "the literal same ContextFrame "
                "plus competing-hypothesis "
                "model reasoning instruction"
            ),
        },

        "strict_success_definition": (
            "target decision signature present "
            "and zero competing decision signatures "
            "present in final answer"
        ),

        "frozen_invariants": [
            "one MNEXA context preparation per family",
            "same ContextFrame object for A and B",
            "same ContextFrame evidence_sha256",
            "same watermark",
            "same selected memory IDs",
            "same context text",
            "same learned memory bundles",
            "same source evidence",
            "same Seed 020 addressing",
            "same Seed 026 proposition-local scoring",
            "same Seed 022 channel abstention",
            "same RRF K",
            "same Seed 027 evidence quorum",
            "same task",
            "same model",
            "reasoning occurs outside MNEXA",
            "strict grader metadata removed before runtime",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_029.json"
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
