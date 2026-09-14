import importlib
import inspect

import pytest


def _seed018():
    try:
        return importlib.import_module(
            "experiments.seed_growth_018"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 018 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks018():
    try:
        return importlib.import_module(
            "experiments.make_tasks_018"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 018 task generator "
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


def test_identity_anchors_only_include_system_and_code():
    module = _seed018()

    anchors = (
        module.identity_anchors(
            [
                "system:BerylAPI",
                "code:BA-42",
                "domain:recovery",
                "cluster:retry-policy",
                "retry",
            ]
        )
    )

    assert anchors == (
        "code:BA-42",
        "system:BerylAPI",
    )


def test_context_entities_are_not_identity_anchors():
    module = _seed018()

    assert (
        module.identity_anchors(
            [
                "domain:recovery",
                "cluster:retry-policy",
            ]
        )
        == ()
    )


def test_exact_code_anchor_selects_target():
    module = _seed018()

    families = [
        _family(
            "alpha",
            [
                "system:AlphaAPI",
                "code:AA-1",
                "domain:recovery",
            ],
        ),
        _family(
            "beta",
            [
                "system:BetaAPI",
                "code:BA-2",
                "domain:recovery",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "code:BA-2",
                "domain:recovery",
            ],
            families=families,
        )
    )

    assert (
        result[
            "candidate_family_ids"
        ]
        == [
            "beta"
        ]
    )

    assert (
        result[
            "fallback_used"
        ]
        is False
    )


def test_exact_system_anchor_selects_target():
    module = _seed018()

    families = [
        _family(
            "alpha",
            [
                "system:AlphaAPI",
                "code:AA-1",
            ],
        ),
        _family(
            "beta",
            [
                "system:BetaAPI",
                "code:BA-2",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "system:AlphaAPI",
            ],
            families=families,
        )
    )

    assert (
        result[
            "candidate_family_ids"
        ]
        == [
            "alpha"
        ]
    )


def test_shared_context_does_not_select_distractors():
    module = _seed018()

    families = [
        _family(
            "alpha",
            [
                "system:AlphaAPI",
                "code:AA-1",
                "domain:recovery",
                "cluster:retry-policy",
            ],
        ),
        _family(
            "beta",
            [
                "system:BetaAPI",
                "code:BA-2",
                "domain:recovery",
                "cluster:retry-policy",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "system:AlphaAPI",
                "code:AA-1",
                "domain:recovery",
                "cluster:retry-policy",
            ],
            families=families,
        )
    )

    assert (
        result[
            "candidate_family_ids"
        ]
        == [
            "alpha"
        ]
    )


def test_multiple_exact_identity_matches_remain_candidates():
    module = _seed018()

    families = [
        _family(
            "alpha",
            [
                "system:SharedSystem",
                "code:AA-1",
            ],
        ),
        _family(
            "beta",
            [
                "system:SharedSystem",
                "code:BA-2",
            ],
        ),
        _family(
            "gamma",
            [
                "system:Gamma",
                "code:GA-3",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "system:SharedSystem",
            ],
            families=families,
        )
    )

    assert (
        result[
            "candidate_family_ids"
        ]
        == [
            "alpha",
            "beta",
        ]
    )


def test_no_anchor_match_falls_back_to_full_pool():
    module = _seed018()

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
                "code:B-2",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "system:Unknown",
                "domain:recovery",
            ],
            families=families,
        )
    )

    assert (
        result[
            "fallback_used"
        ]
        is True
    )

    assert (
        result[
            "candidate_family_ids"
        ]
        == [
            "alpha",
            "beta",
        ]
    )


def test_no_identity_anchor_in_query_falls_back():
    module = _seed018()

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
                "code:B-2",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "domain:recovery",
                "cluster:retry-policy",
            ],
            families=families,
        )
    )

    assert (
        result[
            "fallback_used"
        ]
        is True
    )

    assert len(
        result[
            "candidate_family_ids"
        ]
    ) == 2


def test_router_has_no_oracle_arguments():
    module = _seed018()

    signature = inspect.signature(
        module.select_identity_candidates
    )

    prohibited = {
        "target_family_id",
        "semantic_clause",
        "semantic_grader",
        "correct_answer",
        "atomic_units",
    }

    assert (
        prohibited
        .isdisjoint(
            signature.parameters
        )
    )


def test_router_records_matched_anchors():
    module = _seed018()

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
                "code:B-2",
            ],
        ),
    ]

    result = (
        module.select_identity_candidates(
            query_entities=[
                "system:Beta",
                "code:B-2",
            ],
            families=families,
        )
    )

    assert (
        result[
            "matches"
        ][
            "beta"
        ]
        == [
            "code:B-2",
            "system:Beta",
        ]
    )


def test_candidate_precision_one_for_target_only():
    module = _seed018()

    result = (
        module.posthoc_candidate_metrics(
            target_family_id="beta",
            candidate_family_ids=[
                "beta"
            ],
        )
    )

    assert (
        result[
            "target_selected"
        ]
        is True
    )

    assert (
        result[
            "candidate_precision"
        ]
        == 1.0
    )


def test_candidate_precision_detects_extra_candidates():
    module = _seed018()

    result = (
        module.posthoc_candidate_metrics(
            target_family_id="beta",
            candidate_family_ids=[
                "alpha",
                "beta",
                "gamma",
            ],
        )
    )

    assert (
        result[
            "candidate_precision"
        ]
        ==
        pytest.approx(
            1 / 3
        )
    )


def test_activation_rescue():
    module = _seed018()

    result = (
        module.classify_activation_effect(
            current_pass=False,
            anchored_pass=True,
            current_target_visible=False,
            anchored_target_visible=True,
        )
    )

    assert (
        result[
            "activation_rescue"
        ]
        is True
    )

    assert (
        result[
            "activation_harm"
        ]
        is False
    )

    assert (
        result[
            "visibility_rescue"
        ]
        is True
    )


def test_activation_harm():
    module = _seed018()

    result = (
        module.classify_activation_effect(
            current_pass=True,
            anchored_pass=False,
            current_target_visible=True,
            anchored_target_visible=False,
        )
    )

    assert (
        result[
            "activation_rescue"
        ]
        is False
    )

    assert (
        result[
            "activation_harm"
        ]
        is True
    )


def test_cluster_aggregation():
    module = _seed018()

    rows = [
        {
            "interference_cluster": "retry-policy",
            "current": {
                "semantic_task_pass": False,
                "target_clause_visible": False,
                "wrong_family_clause_count": 3,
            },
            "anchored": {
                "semantic_task_pass": True,
                "target_clause_visible": True,
                "wrong_family_clause_count": 0,
            },
        },
        {
            "interference_cluster": "retry-policy",
            "current": {
                "semantic_task_pass": True,
                "target_clause_visible": True,
                "wrong_family_clause_count": 2,
            },
            "anchored": {
                "semantic_task_pass": True,
                "target_clause_visible": True,
                "wrong_family_clause_count": 0,
            },
        },
    ]

    result = (
        module.aggregate_activation_clusters(
            rows,
            "anchored",
        )
    )

    retry = (
        result[
            "retry-policy"
        ]
    )

    assert (
        retry[
            "families"
        ]
        == 2
    )

    assert (
        retry[
            "task_passes"
        ]
        == 2
    )

    assert (
        retry[
            "target_visible_families"
        ]
        == 2
    )

    assert (
        retry[
            "wrong_family_clause_occurrences"
        ]
        == 0
    )


def test_018_has_twenty_fresh_unique_families():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

    families = (
        payload[
            "families"
        ]
    )

    assert len(
        families
    ) == 20

    assert len(
        {
            family[
                "id"
            ]
            for family
            in families
        }
    ) == 20


def test_018_has_four_clusters_of_five():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

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


def test_each_family_has_two_unique_identity_anchors():
    tasks = _tasks018()
    module = _seed018()

    payload = (
        tasks.build_taskset()
    )

    all_anchors = []

    for family in payload[
        "families"
    ]:

        anchors = (
            module.identity_anchors(
                family[
                    "entities"
                ]
            )
        )

        assert (
            len(
                anchors
            )
            == 2
        )

        all_anchors.extend(
            anchors
        )

    assert (
        len(
            all_anchors
        )
        == 40
    )

    assert (
        len(
            set(
                all_anchors
            )
        )
        == 40
    )


def test_every_family_still_has_shared_context_entities():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        assert (
            "domain:recovery"
            in
            family[
                "entities"
            ]
        )

        assert (
            "cluster:"
            +
            family[
                "interference_cluster"
            ]
            in
            family[
                "entities"
            ]
        )


def test_every_target_has_nineteen_available_distractors():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

    family_ids = {
        family[
            "id"
        ]
        for family
        in payload[
            "families"
        ]
    }

    for family in payload[
        "families"
    ]:

        distractors = (
            family_ids
            -
            {
                family[
                    "id"
                ]
            }
        )

        assert len(
            distractors
        ) == 19


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

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


def test_every_family_has_four_canonical_atoms():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        assert len(
            family[
                "atomic_units"
            ]
        ) == 4


def test_taskset_declares_identity_policy():
    tasks = _tasks018()

    payload = (
        tasks.build_taskset()
    )

    assert (
        payload[
            "identity_anchor_prefixes"
        ]
        == [
            "system:",
            "code:",
        ]
    )

    assert (
        payload[
            "pool_size"
        ]
        == 20
    )
