import importlib
import inspect

import pytest


def _seed023():
    try:
        return importlib.import_module(
            "experiments.seed_growth_023"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 023 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks023():
    try:
        return importlib.import_module(
            "experiments.make_tasks_023"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 023 task generator "
            f"does not exist yet: {exc}"
        )


def test_largest_gap_after_first_selects_k1():
    module = _seed023()

    result = (
        module.dynamic_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            rrf_scores={
                "a": 0.050,
                "b": 0.035,
                "c": 0.034,
                "d": 0.033,
                "e": 0.032,
            },
            max_k=3,
        )
    )

    assert result["dynamic_k"] == 1
    assert result["selected_family_ids"] == ["a"]


def test_largest_gap_after_second_selects_k2():
    module = _seed023()

    result = (
        module.dynamic_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            rrf_scores={
                "a": 0.050,
                "b": 0.048,
                "c": 0.035,
                "d": 0.034,
                "e": 0.033,
            },
            max_k=3,
        )
    )

    assert result["dynamic_k"] == 2

    assert result["selected_family_ids"] == [
        "a",
        "b",
    ]


def test_largest_gap_after_third_selects_k3():
    module = _seed023()

    result = (
        module.dynamic_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            rrf_scores={
                "a": 0.050,
                "b": 0.049,
                "c": 0.048,
                "d": 0.030,
                "e": 0.029,
            },
            max_k=3,
        )
    )

    assert result["dynamic_k"] == 3

    assert result["selected_family_ids"] == [
        "a",
        "b",
        "c",
    ]


def test_equal_gaps_choose_larger_k_conservatively():
    module = _seed023()

    result = (
        module.dynamic_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            rrf_scores={
                "a": 0.050,
                "b": 0.040,
                "c": 0.030,
                "d": 0.020,
                "e": 0.019,
            },
            max_k=3,
        )
    )

    assert result["gaps"] == pytest.approx(
        [
            0.010,
            0.010,
            0.010,
        ]
    )

    assert result["dynamic_k"] == 3


def test_boundary_never_exceeds_max_k():
    module = _seed023()

    result = (
        module.dynamic_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            rrf_scores={
                "a": 5.0,
                "b": 4.0,
                "c": 3.0,
                "d": 1.0,
                "e": 0.0,
            },
            max_k=3,
        )
    )

    assert 1 <= result["dynamic_k"] <= 3


def test_boundary_requires_one_extra_score_after_max_k():
    module = _seed023()

    with pytest.raises(
        ValueError,
        match="at least 4 ranked candidates",
    ):
        module.dynamic_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
            ],
            rrf_scores={
                "a": 3.0,
                "b": 2.0,
                "c": 1.0,
            },
            max_k=3,
        )


def test_safe_compaction_classification():
    module = _seed023()

    result = (
        module.classify_assembly_effect(
            target_family_id="a",
            fixed_selected_ids=[
                "a",
                "b",
                "c",
            ],
            dynamic_selected_ids=[
                "a",
            ],
        )
    )

    assert (
        result["assembly_class"]
        == "safe_compaction"
    )

    assert result["target_retained"] is True
    assert result["distractors_removed"] == 2


def test_over_pruning_classification():
    module = _seed023()

    result = (
        module.classify_assembly_effect(
            target_family_id="c",
            fixed_selected_ids=[
                "a",
                "b",
                "c",
            ],
            dynamic_selected_ids=[
                "a",
            ],
        )
    )

    assert (
        result["assembly_class"]
        == "over_pruning"
    )

    assert result["target_retained"] is False


def test_upstream_rank_miss_classification():
    module = _seed023()

    result = (
        module.classify_assembly_effect(
            target_family_id="d",
            fixed_selected_ids=[
                "a",
                "b",
                "c",
            ],
            dynamic_selected_ids=[
                "a",
                "b",
            ],
        )
    )

    assert (
        result["assembly_class"]
        == "upstream_rank_miss"
    )


def test_no_change_classification():
    module = _seed023()

    result = (
        module.classify_assembly_effect(
            target_family_id="a",
            fixed_selected_ids=[
                "a",
                "b",
                "c",
            ],
            dynamic_selected_ids=[
                "a",
                "b",
                "c",
            ],
        )
    )

    assert (
        result["assembly_class"]
        == "no_change"
    )


def test_dynamic_selection_is_always_prefix_of_fixed_top3():
    module = _seed023()

    full_order = [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]

    result = (
        module.dynamic_context_boundary(
            ordered_family_ids=full_order,
            rrf_scores={
                "a": 0.050,
                "b": 0.049,
                "c": 0.040,
                "d": 0.039,
                "e": 0.038,
            },
            max_k=3,
        )
    )

    fixed = full_order[:3]

    assert (
        result["selected_family_ids"]
        ==
        fixed[
            :result["dynamic_k"]
        ]
    )


def test_boundary_function_has_no_oracle_parameters():
    module = _seed023()

    signature = inspect.signature(
        module.dynamic_context_boundary
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


def test_023_has_twenty_unique_families():
    tasks = _tasks023()

    payload = tasks.build_taskset()

    families = payload["families"]

    assert len(families) == 20

    assert (
        len(
            {
                family["id"]
                for family in families
            }
        )
        == 20
    )


def test_023_has_four_clusters_five_each():
    tasks = _tasks023()

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


def test_every_023_query_is_context_only():
    tasks = _tasks023()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            family["degradation_mode"]
            == "context_only"
        )

        entities = (
            family[
                "query_entities"
            ]
        )

        assert not any(
            x.startswith("system:")
            for x in entities
        )

        assert not any(
            x.startswith("code:")
            for x in entities
        )

        assert any(
            x.startswith("cluster:")
            for x in entities
        )


def test_seed020_routing_returns_five_candidates():
    tasks = _tasks023()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    payload = tasks.build_taskset()
    families = payload["families"]

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

        assert result["candidate_count"] == 5

        assert (
            family["id"]
            in
            result["candidate_family_ids"]
        )


def test_entity_channel_is_frozen_non_discriminative():
    tasks = _tasks023()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    from experiments.seed_growth_021 import (
        _entity_score,
    )

    payload = tasks.build_taskset()
    families = payload["families"]

    by_id = {
        family["id"]: family
        for family in families
    }

    for family in families:

        routing = (
            select_conjunctive_candidates(
                query_entities=(
                    family["query_entities"]
                ),
                families=families,
            )
        )

        scores = [
            _entity_score(
                family["query_entities"],
                by_id[
                    candidate_id
                ]["entities"],
            )
            for candidate_id
            in routing[
                "candidate_family_ids"
            ]
        ]

        assert scores == [
            2.0,
            2.0,
            2.0,
            2.0,
            2.0,
        ]


def test_taskset_freezes_seed022_fusion():
    tasks = _tasks023()

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

    assert payload["rrf_k"] == 60


def test_only_context_boundary_is_declared_variable():
    tasks = _tasks023()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "context assembly boundary only"
    )


def test_all_semantic_clauses_unique():
    tasks = _tasks023()

    payload = tasks.build_taskset()

    clauses = [
        family["semantic_clause"]
        for family
        in payload["families"]
    ]

    assert len(clauses) == len(
        set(clauses)
    )


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks023()

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


def test_every_family_has_four_atomic_units():
    tasks = _tasks023()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            len(
                family["atomic_units"]
            )
            == 4
        )
