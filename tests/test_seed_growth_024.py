import importlib
import inspect

import pytest


def _seed024():
    try:
        return importlib.import_module(
            "experiments.seed_growth_024"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 024 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks024():
    try:
        return importlib.import_module(
            "experiments.make_tasks_024"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 024 task generator "
            f"does not exist yet: {exc}"
        )


def test_single_channel_winner():
    module = _seed024()

    result = module.channel_top_winners(
        channel_ranks={
            "semantic": {
                "a": 1.0,
                "b": 2.0,
                "c": 3.0,
            },
        },
        active_channels=[
            "semantic",
        ],
    )

    assert result == {
        "semantic": ["a"],
    }


def test_exact_top_tie_preserves_all_channel_winners():
    module = _seed024()

    result = module.channel_top_winners(
        channel_ranks={
            "semantic": {
                "a": 1.5,
                "b": 1.5,
                "c": 3.0,
            },
        },
        active_channels=[
            "semantic",
        ],
    )

    assert result == {
        "semantic": [
            "a",
            "b",
        ],
    }


def test_abstained_channels_are_not_used():
    module = _seed024()

    result = module.channel_top_winners(
        channel_ranks={
            "semantic": {
                "a": 1.0,
                "b": 2.0,
            },
            "entity": {
                "a": None,
                "b": None,
            },
        },
        active_channels=[
            "semantic",
        ],
    )

    assert result == {
        "semantic": ["a"],
    }


def test_full_channel_agreement_selects_k1():
    module = _seed024()

    result = (
        module.consensus_context_boundary(
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

    assert result["dynamic_k"] == 1

    assert (
        result["selected_family_ids"]
        ==
        ["a"]
    )

    assert (
        result["consensus_class"]
        ==
        "full_agreement"
    )


def test_two_channel_disagreement_selects_k2():
    module = _seed024()

    result = (
        module.consensus_context_boundary(
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

    assert result["dynamic_k"] == 2

    assert (
        result["selected_family_ids"]
        ==
        [
            "a",
            "b",
        ]
    )

    assert (
        result["consensus_class"]
        ==
        "channel_disagreement"
    )


def test_channel_winner_at_fused_rank3_selects_k3():
    module = _seed024()

    result = (
        module.consensus_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "c": 1.0,
                    "a": 2.0,
                    "b": 3.0,
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

    assert result["dynamic_k"] == 3

    assert (
        result["selected_family_ids"]
        ==
        [
            "a",
            "b",
            "c",
        ]
    )


def test_channel_winner_outside_top3_falls_back_to_k3():
    module = _seed024()

    result = (
        module.consensus_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "d": 1.0,
                    "a": 2.0,
                    "b": 3.0,
                    "c": 4.0,
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

    assert result["dynamic_k"] == 3

    assert (
        result["winner_outside_max_k"]
        is True
    )

    assert (
        result["consensus_class"]
        ==
        "winner_outside_max_k"
    )


def test_top_tie_can_expand_context_to_k2():
    module = _seed024()

    result = (
        module.consensus_context_boundary(
            ordered_family_ids=[
                "a",
                "b",
                "c",
                "d",
                "e",
            ],
            channel_ranks={
                "semantic": {
                    "a": 1.5,
                    "b": 1.5,
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

    assert result["dynamic_k"] == 2

    assert set(
        result["channel_winner_family_ids"]
    ) == {
        "a",
        "b",
    }


def test_no_active_channels_conservatively_falls_back_to_max_k():
    module = _seed024()

    result = (
        module.consensus_context_boundary(
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

    assert result["dynamic_k"] == 3

    assert (
        result["consensus_class"]
        ==
        "no_active_channels"
    )


def test_dynamic_selection_is_always_fused_prefix():
    module = _seed024()

    ordered = [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]

    result = (
        module.consensus_context_boundary(
            ordered_family_ids=ordered,
            channel_ranks={
                "semantic": {
                    "b": 1.0,
                    "a": 2.0,
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
        result["selected_family_ids"]
        ==
        ordered[
            :result["dynamic_k"]
        ]
    )


def test_boundary_function_has_no_oracle_parameters():
    module = _seed024()

    signature = inspect.signature(
        module.consensus_context_boundary
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


def test_024_has_twenty_unique_families():
    tasks = _tasks024()

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


def test_024_has_four_clusters_five_each():
    tasks = _tasks024()

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


def test_every_024_query_is_context_only():
    tasks = _tasks024()

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


def test_seed020_routing_returns_five_candidates():
    tasks = _tasks024()

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


def test_entity_channel_is_non_discriminative():
    tasks = _tasks024()

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


def test_taskset_freezes_seed022_stack():
    tasks = _tasks024()

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

    assert (
        payload[
            "rrf_k"
        ]
        == 60
    )


def test_only_context_boundary_policy_changes():
    tasks = _tasks024()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "context assembly policy only"
    )


def test_all_semantic_clauses_unique():
    tasks = _tasks024()

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
    tasks = _tasks024()

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
    tasks = _tasks024()

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
