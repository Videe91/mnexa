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
    "system_only",
    "context_only",
)


SYSTEMS = (
    (
        "AlderWorks",
        "AW",
    ),
    (
        "BirchWorks",
        "BW",
    ),
    (
        "CedarWorks",
        "CW",
    ),
    (
        "DeltaWorks",
        "DW",
    ),
    (
        "EmberWorks",
        "EW",
    ),
)


CLUSTERS = (
    "retry-policy",
    "lane-routing",
    "channel-session",
    "storage-finalization",
)


def _grader_for(
    system_index,
    cluster,
):
    if cluster == "retry-policy":

        graders = (
            _grader(
                (r"\bexactly\b",),
                (
                    r"\btwo\b",
                    r"\b2\b",
                    r"\btwice\b",
                ),
                (r"\bretr",),
            ),

            _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                ),
                (
                    r"\btwo\b",
                    r"\b2\b",
                    r"\btwice\b",
                ),
                (r"\bretr",),
            ),

            _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\btwo\b",
                    r"\b2\b",
                    r"\btwice\b",
                ),
                (r"\bretr",),
            ),

            _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (
                    r"\btimed[- ]out\b",
                ),
                (r"\brequest\b",),
            ),

            _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brenew",),
                (r"\blease\b",),
            ),
        )

        return graders[
            system_index
        ]

    if cluster == "lane-routing":

        colors = (
            "scarlet",
            "teal",
            "black",
            "white",
            "gold",
        )

        if system_index in (
            0,
            1,
            4,
        ):

            return _grader(
                (r"\bonly\b",),
                (
                    rf"\b{colors[system_index]}\b",
                ),
                (r"\blane\b",),
            )

        if system_index == 2:

            return _grader(
                (
                    r"\bdo\s+not\b",
                    r"\bnever\b",
                ),
                (r"\bblack\b",),
                (r"\blane\b",),
            )

        return _grader(
            (
                r"\bif\b",
                r"\bwhen\b",
            ),
            (r"\bsaturated\b",),
            (r"\bwhite\b",),
            (r"\blane\b",),
        )

    if cluster == "channel-session":

        graders = (
            _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bchannel\b",),
            ),

            _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bnonce\b",),
            ),

            _grader(
                (r"\bexactly\b",),
                (
                    r"\bfour\b",
                    r"\b4\b",
                ),
                (r"\bheartbeat\b",),
            ),

            _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (r"\b14\b",),
                (r"\bseconds?\b",),
            ),

            _grader(
                (
                    r"\bat\s+most\b",
                    r"\bmaximum\b",
                ),
                (
                    r"\bthree\b",
                    r"\b3\b",
                ),
                (r"\bchannel",),
            ),
        )

        return graders[
            system_index
        ]

    graders = (
        _grader(
            (r"\bonly\b",),
            (r"X-Alder-Final",),
            (r"\blocked\b",),
        ),

        _grader(
            (
                r"\bdo\s+not\b",
                r"\bnever\b",
            ),
            (r"\bfinaliz",),
            (r"\bbefore\b",),
            (r"\bmanifest\b",),
        ),

        _grader(
            (r"\bexactly\b",),
            (
                r"\bfive\b",
                r"\b5\b",
            ),
            (r"\bsignature\b",),
        ),

        _grader(
            (
                r"\bat\s+least\b",
                r"\bminimum\b",
            ),
            (
                r"\bfour\b",
                r"\b4\b",
            ),
            (r"\breplica",),
        ),

        _grader(
            (
                r"\bunless\b",
                r"\bonly\s+if\b",
            ),
            (r"\borigin\b",),
            (r"\bepoch\b",),
            (r"\bchang",),
            (r"\bpurge\b",),
        ),
    )

    return graders[
        system_index
    ]


def _cluster_rule(
    system_index,
    cluster,
):
    if cluster == "retry-policy":

        rows = (
            (
                "retry exactly twice",
                "Retry until the request succeeds.",
                "State the retry-count rule.",
                "exactly",
                "cardinality",
            ),

            (
                "retry at most twice",
                "Retry five times.",
                "State the maximum retry-count rule.",
                "at_most",
                "cardinality",
            ),

            (
                "retry at least twice",
                "Retry only once.",
                "State the minimum retry-count rule.",
                "at_least",
                "cardinality",
            ),

            (
                "never retry the timed-out request",
                "Retry the timed-out request.",
                (
                    "State the retry rule for "
                    "the timed-out request."
                ),
                "never",
                "polarity",
            ),

            (
                (
                    "retry only after renewing "
                    "the recovery lease"
                ),
                (
                    "Retry before renewing "
                    "the recovery lease."
                ),
                (
                    "State when retrying "
                    "is permitted."
                ),
                "only",
                "scope",
            ),
        )

        return rows[
            system_index
        ]

    if cluster == "lane-routing":

        rows = (
            (
                "move the task only to the scarlet lane",
                "Move the task to the teal lane.",
                "State the permitted lane.",
                "only",
                "scope",
            ),

            (
                "move the task only to the teal lane",
                "Move the task to the scarlet lane.",
                "State the permitted lane.",
                "only",
                "scope",
            ),

            (
                "do not move the task to the black lane",
                "Move the task to the black lane.",
                (
                    "State the rule governing "
                    "the black lane."
                ),
                "do_not",
                "polarity",
            ),

            (
                (
                    "if the queue is saturated, "
                    "move the task to the white lane"
                ),
                (
                    "Always move the task "
                    "to the white lane."
                ),
                (
                    "State the condition for moving "
                    "the task to the white lane."
                ),
                "when_if",
                "condition",
            ),

            (
                "move the task only to the gold lane",
                "Move the task to the teal lane.",
                "State the permitted lane.",
                "only",
                "scope",
            ),
        )

        return rows[
            system_index
        ]

    if cluster == "channel-session":

        rows = (
            (
                "open only a fresh transport channel",
                "Reuse the existing transport channel.",
                "State the transport-channel rule.",
                "only",
                "scope",
            ),

            (
                "never reuse the previous session nonce",
                "Reuse the previous session nonce.",
                "State the previous-session-nonce rule.",
                "never",
                "polarity",
            ),

            (
                "send exactly four heartbeat frames",
                "Send seven heartbeat frames.",
                (
                    "State the exact heartbeat-frame "
                    "count."
                ),
                "exactly",
                "cardinality",
            ),

            (
                "wait at least 14 seconds",
                "Reconnect immediately.",
                "State the minimum wait duration.",
                "at_least",
                "cardinality",
            ),

            (
                "keep at most three pending channels",
                "Keep eight pending channels.",
                (
                    "State the maximum "
                    "pending-channel count."
                ),
                "at_most",
                "cardinality",
            ),
        )

        return rows[
            system_index
        ]

    rows = (
        (
            "finalize only with X-Alder-Final: locked",
            "Finalize with any completion header.",
            "State the permitted finalization header.",
            "only",
            "scope",
        ),

        (
            "do not finalize before manifest verification",
            "Finalize before manifest verification.",
            "State the manifest/finalization rule.",
            "do_not",
            "polarity",
        ),

        (
            "apply exactly five signature blocks",
            "Apply two signature blocks.",
            "State the exact signature-block count.",
            "exactly",
            "cardinality",
        ),

        (
            "retain at least four replicas",
            "Retain one replica.",
            "State the minimum replica count.",
            "at_least",
            "cardinality",
        ),

        (
            (
                "do not purge the manifest unless "
                "the origin epoch changes"
            ),
            "Purge the manifest immediately.",
            (
                "State the condition under which "
                "the manifest may be purged."
            ),
            "unless",
            "condition",
        ),
    )

    return rows[
        system_index
    ]


def _atoms_for(
    semantic_clause,
    cluster,
):
    if cluster == "retry-policy":

        return [
            "refresh the recovery lease",
            "preserve the request fingerprint",
            semantic_clause,
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
            "record the channel generation",
        ]

    return [
        "verify the manifest checksum",
        semantic_clause,
        "preserve the upload fingerprint",
        "record the final generation",
    ]


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
        len(
            MODES
        )
    ]


def _query_entities(
    *,
    mode,
    system,
    code,
    cluster,
):
    base = [
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
            *base,
        ]

    if mode == "code_only":

        return [
            (
                "code:"
                +
                code
            ),
            *base,
        ]

    if mode == "system_only":

        return [
            (
                "system:"
                +
                system
            ),
            *base,
        ]

    return base


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
            f"The operation reports {code}. "
            +
            semantic_prompt
        )

    if mode == "system_only":

        return (
            f"For {system}, "
            +
            semantic_prompt
        )

    return semantic_prompt


def build_taskset():
    families = []

    serial = 201

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

            (
                semantic_clause,
                candidate_decision,
                semantic_prompt,
                semantic_operator,
                semantic_dimension,
            ) = (
                _cluster_rule(
                    system_index,
                    cluster,
                )
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
                    semantic_clause,
                    cluster,
                )
            )

            mode = (
                _mode_for(
                    system_index,
                    cluster_index,
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
                            candidate_decision
                        ),

                        atoms=(
                            atoms
                        ),

                        semantic_atom_index=2
                        if cluster
                        != "retry-policy"
                        else 3,

                        semantic_operator=(
                            semantic_operator
                        ),

                        semantic_dimension=(
                            semantic_dimension
                        ),

                        transfer_prompt=(
                            semantic_prompt
                        ),

                        semantic_grader=(
                            _grader_for(
                                system_index,
                                cluster,
                            )
                        ),

                        operator_note=(
                            "environmental load "
                            "may be elevated"
                        ),

                        latency=(
                            190
                            +
                            serial
                            %
                            90
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
                        semantic_prompt
                    ),
                )
            )

            families.append(
                family
            )

            serial += 1

    return {
        "experiment": (
            "seed-growth-019"
        ),

        "classification": (
            "exploratory-fresh-degraded-"
            "identity-activation-ablation"
        ),

        "pool_size": 20,

        "system_count": 5,

        "memories_per_system": 4,

        "cluster_count": 4,

        "memories_per_cluster": 5,

        "degradation_modes": list(
            MODES
        ),

        "hierarchy": [
            "code",
            "system",
            "cluster",
            "domain",
            "global",
        ],

        "hypothesis": (
            "Hierarchical addressing will degrade "
            "gracefully as exact identity information "
            "is removed, using code, system, contextual "
            "neighborhood, then global similarity without "
            "changing learned memories or downstream RRF."
        ),

        "conditions": {
            "A": (
                "Seed 018 exact system/code "
                "overlap else global fallback"
            ),

            "B": (
                "code then system then cluster "
                "then domain then global fallback"
            ),
        },

        "primary_metrics": [
            "task success by degradation mode",
            "target clause visibility",
            "candidate recall",
            "candidate precision",
            "wrong-memory presentation",
            "candidate-set size",
        ],

        "secondary_metrics": [
            "global fallback rate",
            "model-visible memory words",
            "semantic violations",
            "task rescue and harm",
        ],

        "families": (
            families
        ),
    }


def main():
    output = Path(
        "experiments/tasks_019.json"
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
