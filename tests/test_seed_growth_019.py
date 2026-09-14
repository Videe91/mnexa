import importlib
import inspect

import pytest


def _seed019():
    try:
        return importlib.import_module(
            "experiments.seed_growth_019"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 019 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks019():
    try:
        return importlib.import_module(
            "experiments.make_tasks_019"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 019 task generator "
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


def test_hierarchy_prefers_code_over_shared_system():
    module = _seed019()

    families = [
        _family(
            "alpha-r1",
            [
                "system:Alpha",
                "code:A-R1",
                "cluster:retry-policy",
            ],
        ),
        _family(
            "alpha-r2",
            [
                "system:Alpha",
                "code:A-R2",
                "cluster:lane-routing",
            ],
        ),
        _family(
            "beta-r1",
            [
                "system:Beta",
                "code:B-R1",
                "cluster:retry-policy",
            ],
        ),
    ]

    result = (
        module.select_hierarchical_candidates(
            query_entities=[
                "system:Alpha",
                "code:A-R1",
                "cluster:retry-policy",
            ],
            families=families,
        )
    )

    assert (
        result["selection_tier"]
        == "code"
    )

    assert (
        result["candidate_family_ids"]
        == ["alpha-r1"]
    )


def test_system_only_selects_system_neighborhood():
    module = _seed019()

    families = [
        _family(
            "alpha-a",
            [
                "system:Alpha",
                "code:A-1",
                "cluster:retry-policy",
            ],
        ),
        _family(
            "alpha-b",
            [
                "system:Alpha",
                "code:A-2",
                "cluster:lane-routing",
            ],
        ),
        _family(
            "beta-a",
            [
                "system:Beta",
                "code:B-1",
                "cluster:retry-policy",
            ],
        ),
    ]

    result = (
        module.select_hierarchical_candidates(
            query_entities=[
                "system:Alpha",
                "cluster:retry-policy",
            ],
            families=families,
        )
    )

    assert (
        result["selection_tier"]
        == "system"
    )

    assert (
        result["candidate_family_ids"]
        == [
            "alpha-a",
            "alpha-b",
        ]
    )


def test_cluster_only_selects_context_neighborhood():
    module = _seed019()

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
        _family(
            "gamma",
            [
                "system:Gamma",
                "code:G-1",
                "cluster:lane-routing",
                "domain:operations",
            ],
        ),
    ]

    result = (
        module.select_hierarchical_candidates(
            query_entities=[
                "cluster:retry-policy",
                "domain:operations",
            ],
            families=families,
        )
    )

    assert (
        result["selection_tier"]
        == "cluster"
    )

    assert (
        result["candidate_family_ids"]
        == [
            "alpha",
            "beta",
        ]
    )


def test_domain_is_used_after_cluster():
    module = _seed019()

    families = [
        _family(
            "alpha",
            [
                "system:Alpha",
                "code:A-1",
                "domain:payments",
            ],
        ),
        _family(
            "beta",
            [
                "system:Beta",
                "code:B-1",
                "domain:payments",
            ],
        ),
        _family(
            "gamma",
            [
                "system:Gamma",
                "code:G-1",
                "domain:storage",
            ],
        ),
    ]

    result = (
        module.select_hierarchical_candidates(
            query_entities=[
                "domain:payments",
            ],
            families=families,
        )
    )

    assert (
        result["selection_tier"]
        == "domain"
    )

    assert (
        result["candidate_family_ids"]
        == [
            "alpha",
            "beta",
        ]
    )


def test_unknown_context_falls_back_to_global_pool():
    module = _seed019()

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
        module.select_hierarchical_candidates(
            query_entities=[
                "cluster:unknown",
            ],
            families=families,
        )
    )

    assert (
        result["selection_tier"]
        == "global"
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


def test_router_has_no_oracle_parameters():
    module = _seed019()

    signature = inspect.signature(
        module.select_hierarchical_candidates
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


def test_hierarchy_records_matching_entities():
    module = _seed019()

    families = [
        _family(
            "alpha",
            [
                "system:Alpha",
                "code:A-1",
                "cluster:retry-policy",
            ],
        )
    ]

    result = (
        module.select_hierarchical_candidates(
            query_entities=[
                "code:A-1",
                "system:Alpha",
                "cluster:retry-policy",
            ],
            families=families,
        )
    )

    assert (
        result["matched_entities"]["alpha"]
        == ["code:A-1"]
    )


def test_effect_classification_rescue():
    module = _seed019()

    result = (
        module.classify_hierarchical_effect(
            current_pass=False,
            hierarchical_pass=True,
            current_visible=False,
            hierarchical_visible=True,
        )
    )

    assert result["task_rescue"] is True
    assert result["task_harm"] is False
    assert result["visibility_rescue"] is True


def test_effect_classification_harm():
    module = _seed019()

    result = (
        module.classify_hierarchical_effect(
            current_pass=True,
            hierarchical_pass=False,
            current_visible=True,
            hierarchical_visible=False,
        )
    )

    assert result["task_harm"] is True
    assert result["visibility_harm"] is True


def test_mode_aggregation():
    module = _seed019()

    rows = [
        {
            "degradation_mode": "system_only",
            "hierarchical": {
                "semantic_task_pass": True,
                "target_clause_visible": True,
                "wrong_family_clause_count": 1,
                "retrieval_precision": 0.5,
                "retrieval_recall": 1.0,
            },
            "hierarchical_selection": {
                "candidate_count": 4,
                "fallback_used": False,
            },
        },
        {
            "degradation_mode": "system_only",
            "hierarchical": {
                "semantic_task_pass": False,
                "target_clause_visible": False,
                "wrong_family_clause_count": 2,
                "retrieval_precision": 0.0,
                "retrieval_recall": 0.0,
            },
            "hierarchical_selection": {
                "candidate_count": 4,
                "fallback_used": False,
            },
        },
    ]

    result = (
        module.aggregate_mode_metrics(
            rows,
            condition="hierarchical",
            selection_key=(
                "hierarchical_selection"
            ),
        )
    )

    system = result["system_only"]

    assert system["families"] == 2
    assert system["task_passes"] == 1
    assert system["target_visible_families"] == 1

    assert (
        system["mean_candidate_count"]
        == 4.0
    )


def test_019_has_twenty_families():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    families = payload["families"]

    assert len(families) == 20

    assert len(
        {
            family["id"]
            for family in families
        }
    ) == 20


def test_019_has_five_systems_four_memories_each():
    tasks = _tasks019()

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
    assert set(counts.values()) == {4}


def test_019_has_four_clusters_five_each():
    tasks = _tasks019()

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


def test_degradation_modes_are_balanced():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload["families"]:

        mode = (
            family[
                "degradation_mode"
            ]
        )

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
        "system_only": 5,
        "context_only": 5,
    }


def test_all_codes_are_unique():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    codes = [
        family["code_name"]

        for family
        in payload["families"]
    ]

    assert len(codes) == 20
    assert len(set(codes)) == 20


def test_full_identity_query_has_system_and_code():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        if (
            family["degradation_mode"]
            != "full_identity"
        ):
            continue

        entities = family[
            "query_entities"
        ]

        assert any(
            entity.startswith(
                "system:"
            )
            for entity in entities
        )

        assert any(
            entity.startswith(
                "code:"
            )
            for entity in entities
        )


def test_code_only_query_has_no_system_anchor():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        if (
            family["degradation_mode"]
            != "code_only"
        ):
            continue

        entities = family[
            "query_entities"
        ]

        assert any(
            entity.startswith(
                "code:"
            )
            for entity in entities
        )

        assert not any(
            entity.startswith(
                "system:"
            )
            for entity in entities
        )


def test_system_only_query_has_no_code_anchor():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        if (
            family["degradation_mode"]
            != "system_only"
        ):
            continue

        entities = family[
            "query_entities"
        ]

        assert any(
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


def test_context_only_query_has_no_identity_anchor():
    tasks = _tasks019()

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


def test_query_prompt_respects_identity_degradation():
    tasks = _tasks019()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        mode = family[
            "degradation_mode"
        ]

        prompt = family[
            "query_prompt"
        ]

        system = family[
            "system_name"
        ]

        code = family[
            "code_name"
        ]

        if mode == "full_identity":
            assert system in prompt
            assert code in prompt

        elif mode == "code_only":
            assert code in prompt
            assert system not in prompt

        elif mode == "system_only":
            assert system in prompt
            assert code not in prompt

        elif mode == "context_only":
            assert system not in prompt
            assert code not in prompt


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks019()

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
    tasks = _tasks019()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert len(
            family["atomic_units"]
        ) == 4
