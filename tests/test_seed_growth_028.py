import importlib
import inspect
import re

import pytest


def _seed028():
    try:
        return importlib.import_module(
            "experiments.seed_growth_028"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 028 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks028():
    try:
        return importlib.import_module(
            "experiments.make_tasks_028"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 028 task generator "
            f"does not exist yet: {exc}"
        )


def test_competing_hypothesis_prompt_preserves_base_question():
    module = _seed028()

    base = "State the exact retry-count rule."

    framed = (
        module.competing_hypothesis_prompt(
            base
        )
    )

    assert base in framed

    assert (
        "alternative candidate hypotheses"
        in framed
    )

    assert (
        "Do not merge"
        in framed
    )


def test_competing_hypothesis_prompt_requires_single_rule():
    module = _seed028()

    framed = (
        module.competing_hypothesis_prompt(
            "State the rule."
        )
    )

    assert (
        "single candidate rule"
        in framed
    )

    assert (
        "incompatible candidate rules"
        in framed
    )


def test_signature_matches_when_all_parts_present():
    module = _seed028()

    signature = {
        "all_of": [
            r"\bexactly\b",
            r"\b(?:nineteen|19)\b",
            r"\bretr",
        ]
    }

    assert (
        module.signature_matches(
            (
                "The rule is to retry "
                "exactly nineteen times."
            ),
            signature,
        )
        is True
    )


def test_signature_does_not_match_partial_rule():
    module = _seed028()

    signature = {
        "all_of": [
            r"\bexactly\b",
            r"\b(?:nineteen|19)\b",
            r"\bretr",
        ]
    }

    assert (
        module.signature_matches(
            "Retry at most nineteen times.",
            signature,
        )
        is False
    )


def test_exclusive_grade_passes_clean_target_only_answer():
    module = _seed028()

    result = (
        module.exclusive_decision_grade(
            decision_text=(
                "Retry exactly nineteen times."
            ),

            target_signature={
                "all_of": [
                    r"\bexactly\b",
                    r"\b(?:nineteen|19)\b",
                    r"\bretr",
                ]
            },

            competing_signatures=[
                {
                    "family_id": "other",
                    "semantic_clause": (
                        "retry at least ten times"
                    ),
                    "all_of": [
                        r"\bat\s+least\b",
                        r"\b(?:ten|10)\b",
                        r"\bretr",
                    ],
                }
            ],
        )
    )

    assert (
        result[
            "target_rule_present"
        ]
        is True
    )

    assert (
        result[
            "competing_rule_hit_count"
        ]
        == 0
    )

    assert (
        result[
            "exclusive_correct_pass"
        ]
        is True
    )


def test_exclusive_grade_rejects_target_plus_competitor():
    module = _seed028()

    result = (
        module.exclusive_decision_grade(
            decision_text=(
                "Retry exactly nineteen times "
                "and retry at least ten times."
            ),

            target_signature={
                "all_of": [
                    r"\bexactly\b",
                    r"\b(?:nineteen|19)\b",
                    r"\bretr",
                ]
            },

            competing_signatures=[
                {
                    "family_id": "other",
                    "semantic_clause": (
                        "retry at least ten times"
                    ),
                    "all_of": [
                        r"\bat\s+least\b",
                        r"\b(?:ten|10)\b",
                        r"\bretr",
                    ],
                }
            ],
        )
    )

    assert (
        result[
            "target_rule_present"
        ]
        is True
    )

    assert (
        result[
            "competing_rule_hit_count"
        ]
        == 1
    )

    assert (
        result[
            "exclusive_correct_pass"
        ]
        is False
    )


def test_exclusive_grade_rejects_competitor_without_target():
    module = _seed028()

    result = (
        module.exclusive_decision_grade(
            decision_text=(
                "Retry at least ten times."
            ),

            target_signature={
                "all_of": [
                    r"\bexactly\b",
                    r"\b(?:nineteen|19)\b",
                    r"\bretr",
                ]
            },

            competing_signatures=[
                {
                    "family_id": "other",
                    "semantic_clause": (
                        "retry at least ten times"
                    ),
                    "all_of": [
                        r"\bat\s+least\b",
                        r"\b(?:ten|10)\b",
                        r"\bretr",
                    ],
                }
            ],
        )
    )

    assert (
        result[
            "target_rule_present"
        ]
        is False
    )

    assert (
        result[
            "exclusive_correct_pass"
        ]
        is False
    )


def test_multiple_competing_rules_are_all_recorded():
    module = _seed028()

    result = (
        module.exclusive_decision_grade(
            decision_text=(
                "Retry exactly nineteen times. "
                "Retry at most fifteen times. "
                "Retry at least ten times."
            ),

            target_signature={
                "all_of": [
                    r"\bexactly\b",
                    r"\b(?:nineteen|19)\b",
                    r"\bretr",
                ]
            },

            competing_signatures=[
                {
                    "family_id": "maximum",
                    "semantic_clause": (
                        "retry at most fifteen times"
                    ),
                    "all_of": [
                        r"\bat\s+most\b",
                        r"\b(?:fifteen|15)\b",
                        r"\bretr",
                    ],
                },
                {
                    "family_id": "minimum",
                    "semantic_clause": (
                        "retry at least ten times"
                    ),
                    "all_of": [
                        r"\bat\s+least\b",
                        r"\b(?:ten|10)\b",
                        r"\bretr",
                    ],
                },
            ],
        )
    )

    assert (
        result[
            "competing_rule_hit_count"
        ]
        == 2
    )

    assert set(
        result[
            "competing_family_ids"
        ]
    ) == {
        "maximum",
        "minimum",
    }


def test_runtime_family_strips_exclusive_grader_metadata():
    module = _seed028()

    family = {
        "id": "x",
        "query_prompt": "question",
        "decision_signature": {
            "all_of": ["target"]
        },
        "competing_signatures": [
            {
                "family_id": "y",
                "all_of": ["other"],
            }
        ],
        "entities": [],
    }

    runtime = (
        module.runtime_family(
            family
        )
    )

    assert (
        "decision_signature"
        not in runtime
    )

    assert (
        "competing_signatures"
        not in runtime
    )

    assert (
        runtime["id"]
        ==
        "x"
    )


def test_apply_frame_changes_only_prompt_field():
    module = _seed028()

    evaluation = {
        "id": "family",
        "transfer_prompt": (
            "State the exact retry-count rule."
        ),
        "semantic_clause": (
            "retry exactly nineteen times"
        ),
    }

    framed = (
        module.apply_competing_hypothesis_frame(
            evaluation
        )
    )

    assert (
        framed["id"]
        ==
        evaluation["id"]
    )

    assert (
        framed["semantic_clause"]
        ==
        evaluation[
            "semantic_clause"
        ]
    )

    assert (
        framed["transfer_prompt"]
        !=
        evaluation["transfer_prompt"]
    )

    assert (
        evaluation["transfer_prompt"]
        in
        framed["transfer_prompt"]
    )


def test_apply_frame_does_not_mutate_original():
    module = _seed028()

    evaluation = {
        "transfer_prompt": (
            "State the rule."
        )
    }

    original = dict(
        evaluation
    )

    module.apply_competing_hypothesis_frame(
        evaluation
    )

    assert (
        evaluation
        ==
        original
    )


def test_apply_frame_requires_transfer_prompt():
    module = _seed028()

    with pytest.raises(
        KeyError,
        match="transfer_prompt",
    ):
        module.apply_competing_hypothesis_frame(
            {
                "id": "x",
            }
        )


def test_exclusive_grader_has_no_model_dependency():
    module = _seed028()

    signature = inspect.signature(
        module.exclusive_decision_grade
    )

    assert (
        "model"
        not in signature.parameters
    )

    assert (
        "embedder"
        not in signature.parameters
    )


def test_028_has_twenty_unique_families():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    families = (
        payload["families"]
    )

    assert len(
        families
    ) == 20

    assert (
        len(
            {
                family["id"]
                for family
                in families
            }
        )
        == 20
    )


def test_028_has_four_clusters_five_each():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload[
        "families"
    ]:

        cluster = (
            family[
                "interference_cluster"
            ]
        )

        counts[
            cluster
        ] = (
            counts.get(
                cluster,
                0,
            )
            +
            1
        )

    assert counts == {
        "retry-policy": 5,
        "lane-routing": 5,
        "channel-session": 5,
        "storage-finalization": 5,
    }


def test_every_family_has_target_signature():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        signature = (
            family[
                "decision_signature"
            ]
        )

        assert signature[
            "all_of"
        ]

        text = (
            family[
                "semantic_clause"
            ]
        )

        assert all(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            for pattern
            in signature[
                "all_of"
            ]
        )


def test_every_family_has_four_competing_signatures():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        assert (
            len(
                family[
                    "competing_signatures"
                ]
            )
            == 4
        )

        assert all(
            competitor[
                "family_id"
            ]
            !=
            family[
                "id"
            ]

            for competitor
            in family[
                "competing_signatures"
            ]
        )


def test_competing_signatures_are_cluster_local():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    by_id = {
        family["id"]: family

        for family
        in payload[
            "families"
        ]
    }

    for family in payload[
        "families"
    ]:

        for competitor in (
            family[
                "competing_signatures"
            ]
        ):

            assert (
                by_id[
                    competitor[
                        "family_id"
                    ]
                ][
                    "interference_cluster"
                ]
                ==
                family[
                    "interference_cluster"
                ]
            )


def test_target_signature_does_not_match_competing_clauses():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        target_patterns = (
            family[
                "decision_signature"
            ][
                "all_of"
            ]
        )

        for competitor in (
            family[
                "competing_signatures"
            ]
        ):

            competitor_text = (
                competitor[
                    "semantic_clause"
                ]
            )

            assert not all(
                re.search(
                    pattern,
                    competitor_text,
                    flags=re.IGNORECASE,
                )

                for pattern
                in target_patterns
            )


def test_queries_are_context_only():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        assert (
            family[
                "degradation_mode"
            ]
            ==
            "context_only"
        )

        assert not any(
            entity.startswith(
                "system:"
            )

            for entity
            in family[
                "query_entities"
            ]
        )

        assert not any(
            entity.startswith(
                "code:"
            )

            for entity
            in family[
                "query_entities"
            ]
        )


def test_seed020_candidate_geometry_is_five():
    tasks = _tasks028()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    payload = tasks.build_taskset()

    runtime_families = [
        {
            key: value

            for key, value
            in family.items()

            if key
            not in {
                "decision_signature",
                "competing_signatures",
            }
        }

        for family
        in payload[
            "families"
        ]
    ]

    for family in runtime_families:

        result = (
            select_conjunctive_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),

                families=(
                    runtime_families
                ),
            )
        )

        assert (
            result[
                "candidate_count"
            ]
            == 5
        )

        assert (
            family["id"]
            in
            result[
                "candidate_family_ids"
            ]
        )


def test_each_cluster_shares_three_background_atoms():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    clusters = {}

    for family in payload[
        "families"
    ]:

        clusters.setdefault(
            family[
                "interference_cluster"
            ],
            [],
        ).append(
            family
        )

    for families in (
        clusters.values()
    ):

        signatures = {
            (
                family[
                    "atomic_units"
                ][0]["text"],

                family[
                    "atomic_units"
                ][2]["text"],

                family[
                    "atomic_units"
                ][3]["text"],
            )

            for family
            in families
        }

        assert (
            len(
                signatures
            )
            == 1
        )


def test_taskset_freezes_seed027_stack():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    assert (
        payload[
            "retrieval_policy"
        ]
        ==
        "proposition_local_max_handle_scoring"
    )

    assert (
        payload[
            "fusion_policy"
        ]
        ==
        "non_discriminative_channel_abstention"
    )

    assert (
        payload[
            "assembly_policy"
        ]
        ==
        "evidence_quorum_guarded_pareto"
    )

    assert (
        payload[
            "min_active_channels_for_pruning"
        ]
        == 2
    )

    assert (
        payload[
            "top_k"
        ]
        == 3
    )

    assert (
        payload[
            "rrf_k"
        ]
        == 60
    )


def test_only_reasoning_frame_changes():
    tasks = _tasks028()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "competing-hypothesis epistemic reasoning frame only"
    )
