import importlib
import inspect

import pytest


def _seed020():
    try:
        return importlib.import_module(
            "experiments.seed_growth_020"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 020 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks020():
    try:
        return importlib.import_module(
            "experiments.make_tasks_020"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 020 task generator "
            f"does not exist yet: {exc}"
        )


def _family(
    family_id,
    entities,
):
    return {
        "id": family_id,
        "entities": entities,
    }


def test_system_then_cluster_refines_to_one_candidate():
    module = _seed020()

    families = [
        _family(
            "alpha-retry",
            [
                "system:Alpha",
                "code:A-1",
                "cluster:retry-policy",
                "domain:operations",
            ],
        ),
        _family(
            "alpha-lane",
            [
                "system:Alpha",
                "code:A-2",
                "cluster:lane-routing",
                "domain:operations",
            ],
        ),
        _family(
            "beta-retry",
            [
                "system:Beta",
                "code:B-1",
                "cluster:retry-policy",
                "domain:operations",
            ],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "system:Alpha",
                "cluster:lane-routing",
                "domain:operations",
            ],
            families=families,
        )
    )

    assert (
        result["candidate_family_ids"]
        == ["alpha-lane"]
    )

    assert (
        result["seed_tier"]
        == "system"
    )

    assert (
        result["accepted_refinement_tiers"]
        == ["cluster"]
    )

    assert (
        result["candidate_count"]
        == 1
    )


def test_code_remains_strongest_address():
    module = _seed020()

    families = [
        _family(
            "alpha-retry",
            [
                "system:Alpha",
                "code:A-1",
                "cluster:retry-policy",
            ],
        ),
        _family(
            "alpha-lane",
            [
                "system:Alpha",
                "code:A-2",
                "cluster:lane-routing",
            ],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "code:A-2",
                "system:Alpha",
                "cluster:lane-routing",
            ],
            families=families,
        )
    )

    assert (
        result["candidate_family_ids"]
        == ["alpha-lane"]
    )

    assert (
        result["seed_tier"]
        == "code"
    )

    assert (
        result["fallback_used"]
        is False
    )


def test_compatible_weaker_context_does_not_broaden():
    module = _seed020()

    families = [
        _family(
            "alpha",
            [
                "system:Alpha",
                "code:A-1",
                "cluster:retry-policy",
                "domain:operations",
            ],
        ),
        _family(
            "beta",
            [
                "system:Beta",
                "code:B-1",
                "cluster:retry-policy",
                "domain:operations",
            ],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "code:A-1",
                "cluster:retry-policy",
                "domain:operations",
            ],
            families=families,
        )
    )

    assert (
        result["candidate_family_ids"]
        == ["alpha"]
    )

    assert (
        result["accepted_refinement_tiers"]
        == []
    )

    statuses = {
        row["tier"]: row["status"]
        for row in result["tier_trace"]
    }

    assert (
        statuses["cluster"]
        == "compatible_no_change"
    )


def test_conflicting_context_cannot_erase_exact_code():
    module = _seed020()

    families = [
        _family(
            "alpha",
            [
                "system:Alpha",
                "code:A-1",
                "cluster:retry-policy",
            ],
        ),
        _family(
            "beta",
            [
                "system:Beta",
                "code:B-1",
                "cluster:lane-routing",
            ],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "code:A-1",
                "cluster:lane-routing",
            ],
            families=families,
        )
    )

    assert (
        result["candidate_family_ids"]
        == ["alpha"]
    )

    assert (
        result["rejected_refinement_tiers"]
        == ["cluster"]
    )

    assert (
        result["empty_intersection_protections"]
        == 1
    )


def test_unmatched_code_can_degrade_to_system():
    module = _seed020()

    families = [
        _family(
            "alpha",
            [
                "system:Alpha",
                "code:A-1",
            ],
        ),
        _family(
            "beta",
            [
                "system:Beta",
                "code:B-1",
            ],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "code:UNKNOWN",
                "system:Alpha",
            ],
            families=families,
        )
    )

    assert (
        result["seed_tier"]
        == "system"
    )

    assert (
        result["candidate_family_ids"]
        == ["alpha"]
    )


def test_context_only_uses_cluster_neighborhood():
    module = _seed020()

    families = [
        _family(
            "alpha",
            [
                "system:Alpha",
                "cluster:retry-policy",
                "domain:operations",
            ],
        ),
        _family(
            "beta",
            [
                "system:Beta",
                "cluster:retry-policy",
                "domain:operations",
            ],
        ),
        _family(
            "gamma",
            [
                "system:Gamma",
                "cluster:lane-routing",
                "domain:operations",
            ],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "cluster:retry-policy",
                "domain:operations",
            ],
            families=families,
        )
    )

    assert (
        result["seed_tier"]
        == "cluster"
    )

    assert (
        result["candidate_family_ids"]
        == [
            "alpha",
            "beta",
        ]
    )


def test_no_matching_address_falls_back_global():
    module = _seed020()

    families = [
        _family(
            "alpha",
            ["system:Alpha"],
        ),
        _family(
            "beta",
            ["system:Beta"],
        ),
    ]

    result = (
        module.select_conjunctive_candidates(
            query_entities=[
                "cluster:unknown",
            ],
            families=families,
        )
    )

    assert (
        result["fallback_used"]
        is True
    )

    assert (
        result["candidate_family_ids"]
        == [
            "alpha",
            "beta",
        ]
    )


def test_router_has_no_oracle_arguments():
    module = _seed020()

    signature = inspect.signature(
        module.select_conjunctive_candidates
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


def test_canonical_candidate_key_ignores_input_order():
    module = _seed020()

    canonical = [
        "alpha",
        "beta",
        "gamma",
    ]

    left = (
        module.canonical_candidate_key(
            candidate_family_ids=[
                "beta",
                "alpha",
            ],
            canonical_family_ids=canonical,
        )
    )

    right = (
        module.canonical_candidate_key(
            candidate_family_ids=[
                "alpha",
                "beta",
            ],
            canonical_family_ids=canonical,
        )
    )

    assert left == (
        "alpha",
        "beta",
    )

    assert left == right


def test_equal_candidate_sets_do_not_require_second_evaluation():
    module = _seed020()

    canonical = [
        "alpha",
        "beta",
        "gamma",
    ]

    assert (
        module.requires_second_evaluation(
            baseline_candidate_ids=[
                "alpha",
                "beta",
            ],
            conjunctive_candidate_ids=[
                "beta",
                "alpha",
            ],
            canonical_family_ids=canonical,
        )
        is False
    )


def test_different_candidate_sets_require_second_evaluation():
    module = _seed020()

    canonical = [
        "alpha",
        "beta",
        "gamma",
    ]

    assert (
        module.requires_second_evaluation(
            baseline_candidate_ids=[
                "alpha",
                "beta",
            ],
            conjunctive_candidate_ids=[
                "alpha",
            ],
            canonical_family_ids=canonical,
        )
        is True
    )


def test_posthoc_effect_detects_rescue():
    module = _seed020()

    result = (
        module.classify_conjunctive_effect(
            baseline_pass=False,
            conjunctive_pass=True,
            baseline_visible=False,
            conjunctive_visible=True,
        )
    )

    assert result["task_rescue"] is True
    assert result["task_harm"] is False
    assert result["visibility_rescue"] is True


def test_020_has_twenty_unique_families():
    tasks = _tasks020()

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


def test_020_has_five_systems_four_memories_each():
    tasks = _tasks020()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload["families"]:

        system = family["system_name"]

        counts[system] = (
            counts.get(
                system,
                0,
            )
            + 1
        )

    assert len(counts) == 5

    assert set(
        counts.values()
    ) == {4}


def test_020_has_four_clusters_five_each():
    tasks = _tasks020()

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


def test_020_modes_are_balanced():
    tasks = _tasks020()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload["families"]:

        mode = family[
            "degradation_mode"
        ]

        counts[mode] = (
            counts.get(
                mode,
                0,
            )
            + 1
        )

    assert counts == {
        "full_identity": 5,
        "code_only": 5,
        "system_context": 5,
        "context_only": 5,
    }


def test_system_context_contains_system_and_cluster_but_no_code():
    tasks = _tasks020()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        if (
            family["degradation_mode"]
            != "system_context"
        ):
            continue

        entities = family[
            "query_entities"
        ]

        assert any(
            x.startswith("system:")
            for x in entities
        )

        assert any(
            x.startswith("cluster:")
            for x in entities
        )

        assert not any(
            x.startswith("code:")
            for x in entities
        )


def test_context_only_contains_no_identity():
    tasks = _tasks020()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        if (
            family["degradation_mode"]
            != "context_only"
        ):
            continue

        entities = family[
            "query_entities"
        ]

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


def test_all_semantic_clauses_are_unique():
    tasks = _tasks020()

    payload = tasks.build_taskset()

    clauses = [
        family["semantic_clause"]
        for family
        in payload["families"]
    ]

    assert (
        len(clauses)
        ==
        len(set(clauses))
    )


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks020()

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
    tasks = _tasks020()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            len(
                family["atomic_units"]
            )
            == 4
        )


def test_fixture_geometry_produces_fifteen_equal_candidate_pairs():
    tasks = _tasks020()

    from experiments.seed_growth_019 import (
        select_hierarchical_candidates,
    )

    module = _seed020()

    payload = tasks.build_taskset()
    families = payload["families"]

    canonical = [
        family["id"]
        for family in families
    ]

    equal = 0

    for family in families:

        baseline = (
            select_hierarchical_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),
                families=families,
            )
        )

        conjunctive = (
            module.select_conjunctive_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),
                families=families,
            )
        )

        if not module.requires_second_evaluation(
            baseline_candidate_ids=(
                baseline[
                    "candidate_family_ids"
                ]
            ),
            conjunctive_candidate_ids=(
                conjunctive[
                    "candidate_family_ids"
                ]
            ),
            canonical_family_ids=canonical,
        ):
            equal += 1

    assert equal == 15


def test_system_context_geometry_is_four_vs_one():
    tasks = _tasks020()

    from experiments.seed_growth_019 import (
        select_hierarchical_candidates,
    )

    module = _seed020()

    payload = tasks.build_taskset()
    families = payload["families"]

    for family in families:

        if (
            family["degradation_mode"]
            != "system_context"
        ):
            continue

        baseline = (
            select_hierarchical_candidates(
                query_entities=(
                    family["query_entities"]
                ),
                families=families,
            )
        )

        conjunctive = (
            module.select_conjunctive_candidates(
                query_entities=(
                    family["query_entities"]
                ),
                families=families,
            )
        )

        assert (
            baseline["candidate_count"]
            == 4
        )

        assert (
            conjunctive["candidate_count"]
            == 1
        )
