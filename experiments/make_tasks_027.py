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
    ("AsterWorks", "AS"),
    ("BerylWorks", "BW"),
    ("CinderWorks", "CW"),
    ("DriftWorks", "DW"),
    ("EmberWorks", "EW"),
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
                "retry exactly seventeen times"
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
                    r"\bseventeen\b",
                    r"\b17\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "retry at most thirteen times"
            ),
            "candidate": (
                "Retry nineteen times."
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
                    r"\bthirteen\b",
                    r"\b13\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "retry at least eight times"
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
                    r"\beight\b",
                    r"\b8\b",
                ),
                (r"\bretr",),
            ),
        },
        {
            "clause": (
                "never retry a schema-rejected request"
            ),
            "candidate": (
                "Retry the schema-rejected request."
            ),
            "prompt": (
                "State the schema-rejection retry rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\bretry\b",),
                (r"\bschema\b",),
                (r"\breject",),
            ),
        },
        {
            "clause": (
                "retry only after rotating "
                "the recovery epoch"
            ),
            "candidate": (
                "Retry before rotating "
                "the recovery epoch."
            ),
            "prompt": (
                "State when retrying is permitted "
                "relative to recovery-epoch rotation."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bafter\b",),
                (r"\brotat",),
                (r"\brecovery\b",),
                (r"\bepoch\b",),
            ),
        },
    ),

    "lane-routing": (
        {
            "clause": (
                "route overflow tasks only "
                "through the indigo lane"
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
                (r"\bindigo\b",),
                (r"\blane\b",),
                (r"\boverflow\b",),
            ),
        },
        {
            "clause": (
                "route replay tasks only "
                "through the copper lane"
            ),
            "candidate": (
                "Route replay tasks through "
                "the indigo lane."
            ),
            "prompt": (
                "State the permitted lane "
                "for replay tasks."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bcopper\b",),
                (r"\blane\b",),
                (r"\breplay\b",),
            ),
        },
        {
            "clause": (
                "do not route poisoned tasks "
                "through the slate lane"
            ),
            "candidate": (
                "Route poisoned tasks through "
                "the slate lane."
            ),
            "prompt": (
                "State the slate-lane rule "
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
                (r"\bslate\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "if the queue is fragmented, "
                "route the task through the coral lane"
            ),
            "candidate": (
                "Always route the task "
                "through the coral lane."
            ),
            "prompt": (
                "State when the coral lane "
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
                (r"\bcoral\b",),
                (r"\blane\b",),
            ),
        },
        {
            "clause": (
                "route quarantine tasks only "
                "through the moss lane"
            ),
            "candidate": (
                "Route quarantine tasks through "
                "the copper lane."
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
                (r"\bmoss\b",),
                (r"\blane\b",),
            ),
        },
    ),

    "channel-session": (
        {
            "clause": (
                "open only a fresh relay channel "
                "after a certificate mismatch"
            ),
            "candidate": (
                "Reuse the current relay channel "
                "after a certificate mismatch."
            ),
            "prompt": (
                "State the channel rule "
                "after a certificate mismatch."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"\bfresh\b",),
                (r"\bchannel\b",),
                (r"\bcertificate\b",),
                (r"\bmismatch\b",),
            ),
        },
        {
            "clause": (
                "never reuse the prior exchange salt"
            ),
            "candidate": (
                "Reuse the prior exchange salt."
            ),
            "prompt": (
                "State the exchange-salt reuse rule."
            ),
            "operator": "never",
            "dimension": "polarity",
            "grader": _grader(
                (
                    r"\bnever\b",
                    r"\bdo\s+not\b",
                ),
                (r"\breuse\b",),
                (r"\bexchange\b",),
                (r"\bsalt\b",),
            ),
        },
        {
            "clause": (
                "send exactly seventeen heartbeat frames"
            ),
            "candidate": (
                "Send five heartbeat frames."
            ),
            "prompt": (
                "State the exact heartbeat-frame count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bseventeen\b",
                    r"\b17\b",
                ),
                (r"\bheartbeat\b",),
            ),
        },
        {
            "clause": (
                "wait at least 43 seconds "
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
                    r"\b43\b",
                    r"\bforty[- ]three\b",
                ),
                (r"\bseconds?\b",),
                (r"\breconnect",),
            ),
        },
        {
            "clause": (
                "keep at most twelve pending relay channels"
            ),
            "candidate": (
                "Keep twenty pending relay channels."
            ),
            "prompt": (
                "State the maximum "
                "pending-relay-channel count."
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
                (r"\bpending\b",),
                (r"\bchannel",),
            ),
        },
    ),

    "storage-finalization": (
        {
            "clause": (
                "finalize only with "
                "X-Aster-Seal: committed"
            ),
            "candidate": (
                "Finalize with any completion header."
            ),
            "prompt": (
                "State the permitted committed "
                "finalization header."
            ),
            "operator": "only",
            "dimension": "scope",
            "grader": _grader(
                (r"\bonly\b",),
                (r"X-Aster-Seal",),
                (r"\bcommitted\b",),
            ),
        },
        {
            "clause": (
                "do not finalize before "
                "receipt-proof verification"
            ),
            "candidate": (
                "Finalize before "
                "receipt-proof verification."
            ),
            "prompt": (
                "State the receipt-proof "
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
                (r"\bproof\b",),
            ),
        },
        {
            "clause": (
                "apply exactly seventeen signature blocks"
            ),
            "candidate": (
                "Apply six signature blocks."
            ),
            "prompt": (
                "State the exact signature-block count."
            ),
            "operator": "exactly",
            "dimension": "cardinality",
            "grader": _grader(
                (r"\bexactly\b",),
                (
                    r"\bseventeen\b",
                    r"\b17\b",
                ),
                (r"\bsignature\b",),
            ),
        },
        {
            "clause": (
                "retain at least thirteen durable replicas"
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
            "grader": _grader(
                (
                    r"\bat\s+least\b",
                    r"\bminimum\b",
                ),
                (
                    r"\bthirteen\b",
                    r"\b13\b",
                ),
                (r"\bdurable\b",),
                (r"\breplica",),
            ),
        },
        {
            "clause": (
                "do not purge the manifest unless "
                "the origin revision advances"
            ),
            "candidate": (
                "Purge the manifest immediately."
            ),
            "prompt": (
                "State the origin-revision condition "
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

    serial = 1001

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
                            340
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
            "seed-growth-027"
        ),

        "classification": (
            "exploratory-fresh-evidence-quorum-"
            "attention-ablation"
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

        "baseline_assembly_policy": (
            "pareto_safe_active_channel_frontier"
        ),

        "experimental_assembly_policy": (
            "evidence_quorum_guarded_pareto"
        ),

        "min_active_channels_for_pruning": 2,

        "experimental_variable": (
            "active-channel quorum guard "
            "on context pruning only"
        ),

        "principle": (
            "One signal may rank. "
            "Multiple distinct active signals "
            "are required to prune."
        ),

        "conditions": {
            "A": (
                "Seed 026 proposition-local retrieval "
                "with existing Pareto assembly"
            ),

            "B": (
                "same ranking and fusion; Pareto pruning "
                "allowed only when at least two retrieval "
                "channels remain active"
            ),
        },

        "frozen_invariants": [
            "same learned memory bundles",
            "same source evidence",
            "same Seed 020 addressing",
            "same five-memory candidate neighborhoods",
            "same Seed 021 retrieval handles",
            "same Seed 026 proposition-local scoring",
            "same semantic scores",
            "same lexical scores",
            "same entity scores",
            "same Seed 022 abstention",
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
        "experiments/tasks_027.json"
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
