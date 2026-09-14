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


MODES = (
    "full_identity",
    "code_only",
    "system_context",
    "context_only",
)


SYSTEMS = (
    (
        "FoxgloveWorks",
        "FW",
    ),
    (
        "GraniteWorks",
        "GW",
    ),
    (
        "HazelWorks",
        "HW",
    ),
    (
        "IndigoWorks",
        "IW",
    ),
    (
        "JuniperWorks",
        "JW",
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
            "retry exactly four times"
        ),
        "candidate": (
            "Retry until the request succeeds."
        ),
        "prompt": (
            "State the retry-count rule."
        ),
        "operator": "exactly",
        "dimension": "cardinality",
        "grader": _grader(
            (r"\bexactly\b",),
            (
                r"\bfour\b",
                r"\b4\b",
            ),
            (r"\bretr",),
        ),
    },

    {
        "clause": (
            "retry at most four times"
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
                r"\bfour\b",
                r"\b4\b",
            ),
            (r"\bretr",),
        ),
    },

    {
        "clause": (
            "retry at least four times"
        ),
        "candidate": (
            "Retry once."
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
                r"\bfour\b",
                r"\b4\b",
            ),
            (r"\bretr",),
        ),
    },

    {
        "clause": (
            "never retry the rejected request"
        ),
        "candidate": (
            "Retry the rejected request."
        ),
        "prompt": (
            "State the rejected-request retry rule."
        ),
        "operator": "never",
        "dimension": "polarity",
        "grader": _grader(
            (
                r"\bnever\b",
                r"\bdo\s+not\b",
            ),
            (r"\bretry\b",),
            (r"\brejected\b",),
            (r"\brequest\b",),
        ),
    },

    {
        "clause": (
            "retry only after rotating the recovery token"
        ),
        "candidate": (
            "Retry before rotating the recovery token."
        ),
        "prompt": (
            "State when retrying is permitted."
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
)


LANE_RULES = (
    {
        "clause": (
            "route the task only through the crimson lane"
        ),
        "candidate": (
            "Route the task through the azure lane."
        ),
        "prompt": (
            "State the permitted routing lane."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"\bcrimson\b",),
            (r"\blane\b",),
        ),
    },

    {
        "clause": (
            "route the task only through the azure lane"
        ),
        "candidate": (
            "Route the task through the crimson lane."
        ),
        "prompt": (
            "State the permitted routing lane."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"\bazure\b",),
            (r"\blane\b",),
        ),
    },

    {
        "clause": (
            "do not route the task through the obsidian lane"
        ),
        "candidate": (
            "Route the task through the obsidian lane."
        ),
        "prompt": (
            "State the rule governing the obsidian lane."
        ),
        "operator": "do_not",
        "dimension": "polarity",
        "grader": _grader(
            (
                r"\bdo\s+not\b",
                r"\bnever\b",
            ),
            (r"\broute\b",),
            (r"\bobsidian\b",),
            (r"\blane\b",),
        ),
    },

    {
        "clause": (
            "if the queue is throttled, "
            "route the task through the ivory lane"
        ),
        "candidate": (
            "Always route the task through the ivory lane."
        ),
        "prompt": (
            "State the condition for using the ivory lane."
        ),
        "operator": "when_if",
        "dimension": "condition",
        "grader": _grader(
            (
                r"\bif\b",
                r"\bwhen\b",
            ),
            (r"\bthrottled\b",),
            (r"\bivory\b",),
            (r"\blane\b",),
        ),
    },

    {
        "clause": (
            "route the task only through the emerald lane"
        ),
        "candidate": (
            "Route the task through the crimson lane."
        ),
        "prompt": (
            "State the permitted routing lane."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"\bemerald\b",),
            (r"\blane\b",),
        ),
    },
)


CHANNEL_RULES = (
    {
        "clause": (
            "open only a new session channel"
        ),
        "candidate": (
            "Reuse the existing session channel."
        ),
        "prompt": (
            "State the session-channel rule."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (
                r"\bnew\b",
                r"\bfresh\b",
            ),
            (r"\bchannel\b",),
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
            "State the handshake-nonce rule."
        ),
        "operator": "never",
        "dimension": "polarity",
        "grader": _grader(
            (
                r"\bnever\b",
                r"\bdo\s+not\b",
            ),
            (r"\breuse\b",),
            (r"\bnonce\b",),
        ),
    },

    {
        "clause": (
            "send exactly six heartbeat frames"
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
                r"\bsix\b",
                r"\b6\b",
            ),
            (r"\bheartbeat\b",),
        ),
    },

    {
        "clause": (
            "wait at least 17 seconds before reconnecting"
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
                r"\b17\b",
                r"\bseventeen\b",
            ),
            (r"\bseconds?\b",),
        ),
    },

    {
        "clause": (
            "keep at most four pending channels"
        ),
        "candidate": (
            "Keep nine pending channels."
        ),
        "prompt": (
            "State the maximum pending-channel count."
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
                r"\bfour\b",
                r"\b4\b",
            ),
            (r"\bchannel",),
        ),
    },
)


STORAGE_RULES = (
    {
        "clause": (
            "finalize only with X-Foxglove-Seal: ready"
        ),
        "candidate": (
            "Finalize with any completion header."
        ),
        "prompt": (
            "State the permitted finalization header."
        ),
        "operator": "only",
        "dimension": "scope",
        "grader": _grader(
            (r"\bonly\b",),
            (r"X-Foxglove-Seal",),
            (r"\bready\b",),
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
            "State the digest/finalization rule."
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
            "apply exactly six signature blocks"
        ),
        "candidate": (
            "Apply two signature blocks."
        ),
        "prompt": (
            "State the exact signature-block count."
        ),
        "operator": "exactly",
        "dimension": "cardinality",
        "grader": _grader(
            (r"\bexactly\b",),
            (
                r"\bsix\b",
                r"\b6\b",
            ),
            (r"\bsignature\b",),
        ),
    },

    {
        "clause": (
            "retain at least five replicas"
        ),
        "candidate": (
            "Retain one replica."
        ),
        "prompt": (
            "State the minimum replica count."
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
            "State the condition under which "
            "the manifest may be purged."
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
                r"\badvanc",
                r"\bchang",
            ),
            (r"\bpurge\b",),
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


def _mode_for(
    system_index,
    cluster_index,
):
    return MODES[
        (
            system_index
            +
            cluster_index
        )
        %
        4
    ]


def _atoms_for(
    *,
    cluster,
    semantic_clause,
):
    if cluster == "retry-policy":

        return [
            "refresh the recovery credential",
            semantic_clause,
            "preserve the request fingerprint",
            "close the stale connection",
        ]

    if cluster == "lane-routing":

        return [
            "request a fresh checkpoint",
            semantic_clause,
            "retry once",
            "preserve the original task ID",
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


def _query_entities(
    *,
    mode,
    system,
    code,
    cluster,
):
    context = [
        "domain:operations",
        (
            "cluster:"
            +
            cluster
        ),
    ]

    if mode == "full_identity":

        return [
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

            *context,
        ]

    if mode == "code_only":

        return [
            (
                "code:"
                +
                code
            ),

            *context,
        ]

    if mode == "system_context":

        return [
            (
                "system:"
                +
                system
            ),

            *context,
        ]

    return (
        context
    )


def _query_prompt(
    *,
    mode,
    system,
    code,
    semantic_prompt,
):
    if mode == "full_identity":

        return (
            f"{system} reports {code}. "
            +
            semantic_prompt
        )

    if mode == "code_only":

        return (
            f"Operation {code}. "
            +
            semantic_prompt
        )

    if mode == "system_context":

        return (
            f"For {system}, "
            +
            semantic_prompt
        )

    return (
        semantic_prompt
    )


def build_taskset():
    families = []

    serial = 301

    for (
        system_index,
        (
            system,
            prefix,
        ),
    ) in enumerate(
        SYSTEMS
    ):

        for (
            cluster_index,
            cluster,
        ) in enumerate(
            CLUSTERS
        ):

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

            mode = (
                _mode_for(
                    system_index,
                    cluster_index,
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

                        # All Seed 020 fixtures place the
                        # semantic atom second.
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
                            "environmental pressure "
                            "may be elevated"
                        ),

                        latency=(
                            200
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
                mode
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
            ] = (
                _query_entities(
                    mode=mode,
                    system=system,
                    code=code,
                    cluster=cluster,
                )
            )

            family[
                "query_prompt"
            ] = (
                _query_prompt(
                    mode=mode,
                    system=system,
                    code=code,

                    semantic_prompt=(
                        rule[
                            "prompt"
                        ]
                    ),
                )
            )

            families.append(
                family
            )

            serial += 1

    return {
        "experiment": (
            "seed-growth-020"
        ),

        "classification": (
            "exploratory-fresh-conjunctive-"
            "address-refinement-ablation"
        ),

        "pool_size": 20,

        "system_count": 5,

        "memories_per_system": 4,

        "cluster_count": 4,

        "memories_per_cluster": 5,

        "degradation_modes": list(
            MODES
        ),

        "principle": (
            "Strong identity constrains. "
            "Context refines."
        ),

        "conditions": {
            "A": (
                "Seed 019 first-successful "
                "hierarchical addressing"
            ),

            "B": (
                "conjunctive refinement using "
                "compatible weaker metadata"
            ),
        },

        "expected_candidate_geometry": {
            "full_identity": {
                "A": 1,
                "B": 1,
            },

            "code_only": {
                "A": 1,
                "B": 1,
            },

            "system_context": {
                "A": 4,
                "B": 1,
            },

            "context_only": {
                "A": 5,
                "B": 5,
            },
        },

        "same_state_control": (
            "When A and B produce the same canonical "
            "candidate set, they share the exact frozen "
            "candidate snapshot and the exact same transfer "
            "evaluation. No second model call is made."
        ),

        "hypothesis": (
            "Combining compatible identity and contextual "
            "address signals will remove residual system-level "
            "interference without weakening exact-code or "
            "context-only activation."
        ),

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_020.json"
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
