import importlib
import inspect

import pytest


def _seed027():
    try:
        return importlib.import_module(
            "experiments.seed_growth_027"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 027 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks027():
    try:
        return importlib.import_module(
            "experiments.make_tasks_027"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 027 task generator "
            f"does not exist yet: {exc}"
        )


def test_one_active_channel_preserves_top3():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
                "lexical": {
                    "a": None,
                    "b": None,
                    "c": None,
                    "d": None,
                    "e": None,
                },
            },
            active_channels=[
                "semantic",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result["dynamic_k"]
        == 3
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        [
            "a",
            "b",
            "c",
        ]
    )

    assert (
        result["quorum_met"]
        is False
    )

    assert (
        result["guard_mode"]
        ==
        "insufficient_channel_quorum"
    )

    assert (
        result["pareto_delegated"]
        is False
    )


def test_zero_active_channels_preserves_top3():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": None,
                    "b": None,
                    "c": None,
                    "d": None,
                    "e": None,
                },
                "lexical": {
                    "a": None,
                    "b": None,
                    "c": None,
                    "d": None,
                    "e": None,
                },
            },
            active_channels=[],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result["dynamic_k"]
        == 3
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        [
            "a",
            "b",
            "c",
        ]
    )

    assert (
        result["active_channel_count"]
        == 0
    )

    assert (
        result["quorum_met"]
        is False
    )


def test_single_channel_cannot_collapse_to_k1():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "winner",
                "target",
                "other",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "winner": 1.0,
                    "target": 2.0,
                    "other": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
            },
            active_channels=[
                "semantic",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        [
            "winner",
            "target",
            "other",
        ]
    )

    assert (
        "target"
        in result[
            "selected_family_ids"
        ]
    )


def test_two_active_channels_delegate_to_pareto():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
                "lexical": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result["quorum_met"]
        is True
    )

    assert (
        result["pareto_delegated"]
        is True
    )

    assert (
        result["dynamic_k"]
        == 1
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        ["a"]
    )


def test_two_channel_tradeoff_keeps_pareto_frontier():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
                "lexical": {
                    "b": 1.0,
                    "a": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result["dynamic_k"]
        == 2
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        [
            "a",
            "b",
        ]
    )


def test_quorum_uses_number_of_active_channels_not_declared_channels():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
                "lexical": {
                    "a": None,
                    "b": None,
                    "c": None,
                    "d": None,
                    "e": None,
                },
                "entity": {
                    "a": None,
                    "b": None,
                    "c": None,
                    "d": None,
                    "e": None,
                },
            },
            active_channels=[
                "semantic",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result["active_channel_count"]
        == 1
    )

    assert (
        result["quorum_met"]
        is False
    )


def test_exact_quorum_threshold_allows_pareto():
    module = _seed027()

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
                "lexical": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result["active_channel_count"]
        == 2
    )

    assert (
        result["quorum_met"]
        is True
    )


def test_quorum_selection_is_always_fused_prefix():
    module = _seed027()

    ordered = [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]

    result = (
        module.quorum_context_boundary(
            ordered_family_ids=ordered,
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                    "d": 4.0,
                    "e": 5.0,
                },
            },
            active_channels=[
                "semantic",
            ],
            max_k=3,
            min_active_channels=2,
        )
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        ordered[
            :result["dynamic_k"]
        ]
    )


def test_boundary_has_no_oracle_parameters():
    module = _seed027()

    signature = inspect.signature(
        module.quorum_context_boundary
    )

    prohibited = {
        "target_family_id",
        "semantic_clause",
        "semantic_grader",
        "correct_answer",
        "atomic_units",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_027_has_twenty_unique_families():
    tasks = _tasks027()

    payload = tasks.build_taskset()

    families = payload[
        "families"
    ]

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


def test_027_has_four_clusters_five_each():
    tasks = _tasks027()

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


def test_all_queries_are_context_only():
    tasks = _tasks027()

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

        entities = (
            family[
                "query_entities"
            ]
        )

        assert not any(
            value.startswith(
                "system:"
            )
            for value
            in entities
        )

        assert not any(
            value.startswith(
                "code:"
            )
            for value
            in entities
        )


def test_seed020_routing_still_returns_five():
    tasks = _tasks027()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    payload = (
        tasks.build_taskset()
    )

    families = (
        payload["families"]
    )

    for family in families:

        result = (
            select_conjunctive_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),
                families=families,
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
            in result[
                "candidate_family_ids"
            ]
        )


def test_each_cluster_shares_three_background_atoms():
    tasks = _tasks027()

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

    for cluster_families in (
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
            in cluster_families
        }

        assert (
            len(
                signatures
            )
            == 1
        )


def test_semantic_clauses_unique():
    tasks = _tasks027()

    payload = tasks.build_taskset()

    clauses = [
        family[
            "semantic_clause"
        ]

        for family
        in payload[
            "families"
        ]
    ]

    assert (
        len(clauses)
        ==
        len(set(clauses))
    )


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks027()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        assert (
            family[
                "raw_source"
            ].count(
                family[
                    "semantic_clause"
                ]
            )
            == 1
        )


def test_every_family_has_four_atomic_units():
    tasks = _tasks027()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        assert (
            len(
                family[
                    "atomic_units"
                ]
            )
            == 4
        )


def test_taskset_freezes_seed026_retrieval_stack():
    tasks = _tasks027()

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
            "baseline_assembly_policy"
        ]
        ==
        "pareto_safe_active_channel_frontier"
    )

    assert (
        payload["rrf_k"]
        == 60
    )

    assert (
        payload["top_k"]
        == 3
    )


def test_quorum_threshold_is_frozen_at_two():
    tasks = _tasks027()

    payload = tasks.build_taskset()

    assert (
        payload[
            "min_active_channels_for_pruning"
        ]
        == 2
    )


def test_only_assembly_safety_rule_changes():
    tasks = _tasks027()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "active-channel quorum guard on context pruning only"
    )
