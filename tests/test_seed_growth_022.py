import importlib
import inspect

import pytest


def _seed022():
    try:
        return importlib.import_module(
            "experiments.seed_growth_022"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 022 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks022():
    try:
        return importlib.import_module(
            "experiments.make_tasks_022"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 022 task generator "
            f"does not exist yet: {exc}"
        )


def test_constant_channel_is_non_discriminative():
    module = _seed022()

    assert (
        module.channel_is_non_discriminative(
            {
                "a": 2.0,
                "b": 2.0,
                "c": 2.0,
            }
        )
        is True
    )


def test_channel_with_real_difference_is_discriminative():
    module = _seed022()

    assert (
        module.channel_is_non_discriminative(
            {
                "a": 2.0,
                "b": 2.0,
                "c": 1.0,
            }
        )
        is False
    )


def test_average_tie_ranks_give_equal_votes():
    module = _seed022()

    ranks = (
        module.average_tie_ranks(
            candidate_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            scores={
                "a": 10.0,
                "b": 10.0,
                "c": 5.0,
                "d": 1.0,
                "e": 1.0,
            },
        )
    )

    assert ranks["a"] == 1.5
    assert ranks["b"] == 1.5
    assert ranks["c"] == 3.0
    assert ranks["d"] == 4.5
    assert ranks["e"] == 4.5


def test_fully_tied_entity_channel_abstains():
    module = _seed022()

    result = (
        module.fuse_channel_scores_abstaining(
            candidate_family_ids=[
                "a",
                "b",
                "c",
            ],
            channel_scores={
                "semantic": {
                    "a": 0.9,
                    "b": 0.5,
                    "c": 0.1,
                },
                "lexical": {
                    "a": 0.8,
                    "b": 0.4,
                    "c": 0.2,
                },
                "entity": {
                    "a": 2.0,
                    "b": 2.0,
                    "c": 2.0,
                },
            },
            top_k=2,
            rrf_k=60,
        )
    )

    assert (
        result["abstained_channels"]
        == ["entity"]
    )

    assert set(
        result["active_channels"]
    ) == {
        "semantic",
        "lexical",
    }

    assert (
        result[
            "channel_contributions"
        ][
            "entity"
        ]
        ==
        {
            "a": 0.0,
            "b": 0.0,
            "c": 0.0,
        }
    )

    assert (
        result["selected_family_ids"][0]
        == "a"
    )


def test_partial_ties_receive_equal_rrf_contribution():
    module = _seed022()

    result = (
        module.fuse_channel_scores_abstaining(
            candidate_family_ids=[
                "a",
                "b",
                "c",
            ],
            channel_scores={
                "semantic": {
                    "a": 0.9,
                    "b": 0.9,
                    "c": 0.1,
                },
            },
            top_k=3,
            rrf_k=60,
        )
    )

    contributions = (
        result[
            "channel_contributions"
        ][
            "semantic"
        ]
    )

    assert (
        contributions["a"]
        ==
        contributions["b"]
    )

    assert (
        contributions["a"]
        >
        contributions["c"]
    )


def test_all_channels_abstaining_is_explicit_and_deterministic():
    module = _seed022()

    result = (
        module.fuse_channel_scores_abstaining(
            candidate_family_ids=[
                "a",
                "b",
                "c",
            ],
            channel_scores={
                "semantic": {
                    "a": 1.0,
                    "b": 1.0,
                    "c": 1.0,
                },
                "lexical": {
                    "a": 0.0,
                    "b": 0.0,
                    "c": 0.0,
                },
                "entity": {
                    "a": 2.0,
                    "b": 2.0,
                    "c": 2.0,
                },
            },
            top_k=2,
            rrf_k=60,
        )
    )

    assert (
        result[
            "all_channels_abstained"
        ]
        is True
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


def test_abstaining_ranker_has_no_oracle_parameters():
    module = _seed022()

    signature = inspect.signature(
        module.fuse_channel_scores_abstaining
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


def test_sequential_tie_bias_detector():
    module = _seed022()

    assert (
        module.channel_has_artificial_sequential_tie(
            scores={
                "a": 2.0,
                "b": 2.0,
                "c": 2.0,
            },
            ranks={
                "a": 1,
                "b": 2,
                "c": 3,
            },
        )
        is True
    )


def test_no_sequential_tie_bias_when_scores_differ():
    module = _seed022()

    assert (
        module.channel_has_artificial_sequential_tie(
            scores={
                "a": 3.0,
                "b": 2.0,
                "c": 1.0,
            },
            ranks={
                "a": 1,
                "b": 2,
                "c": 3,
            },
        )
        is False
    )


def test_equal_selected_sets_do_not_require_second_evaluation():
    module = _seed022()

    assert (
        module.requires_second_evaluation(
            baseline_selected_ids=[
                "a",
                "b",
                "c",
            ],
            abstaining_selected_ids=[
                "c",
                "a",
                "b",
            ],
            canonical_family_ids=[
                "a",
                "b",
                "c",
                "d",
            ],
        )
        is False
    )


def test_different_selected_sets_require_second_evaluation():
    module = _seed022()

    assert (
        module.requires_second_evaluation(
            baseline_selected_ids=[
                "a",
                "b",
                "c",
            ],
            abstaining_selected_ids=[
                "a",
                "b",
                "d",
            ],
            canonical_family_ids=[
                "a",
                "b",
                "c",
                "d",
            ],
        )
        is True
    )


def test_022_has_twenty_unique_families():
    tasks = _tasks022()

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


def test_022_has_four_clusters_five_each():
    tasks = _tasks022()

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
    tasks = _tasks022()

    payload = tasks.build_taskset()

    for family in payload["families"]:

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
            entity.startswith(
                "system:"
            )
            for entity in entities
        )

        assert not any(
            entity.startswith(
                "code:"
            )
            for entity in entities
        )

        assert any(
            entity.startswith(
                "cluster:"
            )
            for entity in entities
        )


def test_seed_020_routing_gives_five_candidates():
    tasks = _tasks022()

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


def test_entity_channel_is_exactly_tied_inside_every_neighborhood():
    tasks = _tasks022()

    from experiments.seed_growth_021 import (
        _entity_score,
    )

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
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
                    family[
                        "query_entities"
                    ]
                ),
                families=families,
            )
        )

        scores = [
            _entity_score(
                family[
                    "query_entities"
                ],
                by_id[
                    candidate_id
                ][
                    "entities"
                ],
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


def test_all_semantic_clauses_are_unique():
    tasks = _tasks022()

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
    tasks = _tasks022()

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
    tasks = _tasks022()

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


def test_taskset_freezes_seed_021_handle_representation():
    tasks = _tasks022()

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
            "retrieval_top_k"
        ]
        == 3
    )

    assert (
        payload[
            "rrf_k"
        ]
        == 60
    )


def test_only_fusion_policy_is_declared_variable():
    tasks = _tasks022()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "RRF tie and abstention policy only"
    )
