import importlib
import inspect

import pytest


def _seed025():
    try:
        return importlib.import_module(
            "experiments.seed_growth_025"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 025 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks025():
    try:
        return importlib.import_module(
            "experiments.make_tasks_025"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 025 task generator "
            f"does not exist yet: {exc}"
        )


def test_strictly_better_candidate_dominates():
    module = _seed025()

    assert (
        module.candidate_dominates(
            candidate_a="a",
            candidate_b="b",
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                },
                "lexical": {
                    "a": 2.0,
                    "b": 3.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
        )
        is True
    )


def test_tradeoff_does_not_dominate():
    module = _seed025()

    assert (
        module.candidate_dominates(
            candidate_a="a",
            candidate_b="b",
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                },
                "lexical": {
                    "a": 3.0,
                    "b": 1.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
        )
        is False
    )


def test_exact_tie_does_not_count_as_domination():
    module = _seed025()

    assert (
        module.candidate_dominates(
            candidate_a="a",
            candidate_b="b",
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 1.0,
                },
                "lexical": {
                    "a": 2.0,
                    "b": 2.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
        )
        is False
    )


def test_pareto_frontier_excludes_dominated_candidate():
    module = _seed025()

    result = (
        module.pareto_frontier(
            candidate_family_ids=[
                "a",
                "b",
                "c",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                },
                "lexical": {
                    "a": 1.0,
                    "b": 3.0,
                    "c": 2.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
        )
    )

    assert (
        result[
            "frontier_family_ids"
        ]
        ==
        ["a"]
    )

    assert set(
        result[
            "dominated_family_ids"
        ]
    ) == {
        "b",
        "c",
    }


def test_tradeoff_candidates_both_survive_frontier():
    module = _seed025()

    result = (
        module.pareto_frontier(
            candidate_family_ids=[
                "a",
                "b",
                "c",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.0,
                    "b": 3.0,
                    "c": 2.0,
                },
                "lexical": {
                    "a": 3.0,
                    "b": 1.0,
                    "c": 2.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
        )
    )

    assert set(
        result[
            "frontier_family_ids"
        ]
    ) == {
        "a",
        "b",
        "c",
    }


def test_seed024_failure_shape_preserves_fused_rank3():
    module = _seed025()

    ordered = [
        "alder",
        "delta",
        "target",
        "bramble",
        "cobalt",
    ]

    result = (
        module.pareto_context_boundary(
            ordered_family_ids=ordered,
            channel_ranks={
                "semantic": {
                    "alder": 1.0,
                    "bramble": 2.0,
                    "cobalt": 3.0,
                    "target": 4.0,
                    "delta": 5.0,
                },
                "lexical": {
                    "delta": 1.0,
                    "target": 2.0,
                    "alder": 3.0,
                    "cobalt": 4.0,
                    "bramble": 5.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
            max_k=3,
        )
    )

    assert "target" in (
        result[
            "frontier_family_ids"
        ]
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
            "alder",
            "delta",
            "target",
        ]
    )


def test_single_dominant_frontier_selects_k1():
    module = _seed025()

    result = (
        module.pareto_context_boundary(
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
        )
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


def test_frontier_reaching_rank2_selects_k2():
    module = _seed025()

    result = (
        module.pareto_context_boundary(
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
        )
    )

    assert (
        result["dynamic_k"]
        == 2
    )

    assert set(
        result[
            "frontier_family_ids"
        ]
    ) == {
        "a",
        "b",
    }


def test_frontier_outside_top3_falls_back_to_k3():
    module = _seed025()

    result = (
        module.pareto_context_boundary(
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
                    "d": 1.0,
                    "c": 2.0,
                    "b": 3.0,
                    "a": 4.0,
                    "e": 5.0,
                },
            },
            active_channels=[
                "semantic",
                "lexical",
            ],
            max_k=3,
        )
    )

    assert (
        result[
            "frontier_outside_max_k"
        ]
        is True
    )

    assert (
        result["dynamic_k"]
        == 3
    )


def test_no_active_channels_falls_back_to_k3():
    module = _seed025()

    result = (
        module.pareto_context_boundary(
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
            },
            active_channels=[],
            max_k=3,
        )
    )

    assert (
        result["dynamic_k"]
        == 3
    )

    assert (
        result["frontier_class"]
        ==
        "no_active_channels"
    )


def test_dynamic_selection_is_always_fused_prefix():
    module = _seed025()

    ordered = [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]

    result = (
        module.pareto_context_boundary(
            ordered_family_ids=ordered,
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
    module = _seed025()

    signature = inspect.signature(
        module.pareto_context_boundary
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


def test_025_has_twenty_unique_families():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    assert (
        len(
            payload["families"]
        )
        == 20
    )

    assert (
        len(
            {
                family["id"]
                for family
                in payload["families"]
            }
        )
        == 20
    )


def test_025_has_four_clusters_five_each():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload["families"]:

        cluster = (
            family[
                "interference_cluster"
            ]
        )

        counts[cluster] = (
            counts.get(
                cluster,
                0,
            )
            + 1
        )

    assert counts == {
        "retry-policy": 5,
        "lane-routing": 5,
        "channel-session": 5,
        "storage-finalization": 5,
    }


def test_every_query_is_context_only():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        entities = (
            family[
                "query_entities"
            ]
        )

        assert (
            family[
                "degradation_mode"
            ]
            ==
            "context_only"
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


def test_seed020_routing_returns_five():
    tasks = _tasks025()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    payload = tasks.build_taskset()

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
            in
            result[
                "candidate_family_ids"
            ]
        )


def test_taskset_freezes_existing_retrieval_stack():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    assert (
        payload[
            "ranking_representation"
        ]
        ==
        "retrieval_handle_index"
    )

    assert (
        payload[
            "fusion_policy"
        ]
        ==
        "non_discriminative_channel_abstention"
    )

    assert (
        payload["rrf_k"]
        == 60
    )

    assert (
        payload[
            "fixed_top_k"
        ]
        == 3
    )

    assert (
        payload[
            "dynamic_max_k"
        ]
        == 3
    )


def test_only_context_policy_changes():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "context assembly policy only"
    )


def test_semantic_clauses_unique():
    tasks = _tasks025()

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


def test_semantic_clause_occurs_once():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    for family in payload["families"]:

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


def test_every_family_has_four_atoms():
    tasks = _tasks025()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            len(
                family[
                    "atomic_units"
                ]
            )
            == 4
        )
