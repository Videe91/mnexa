import importlib

import pytest


def _seed017():
    try:
        return importlib.import_module(
            "experiments.seed_growth_017"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 017 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks017():
    try:
        return importlib.import_module(
            "experiments.make_tasks_017"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 017 task generator "
            f"does not exist yet: {exc}"
        )


def test_context_analysis_target_only():
    module = _seed017()

    clauses = {
        "alpha": (
            "retry exactly twice"
        ),
        "beta": (
            "retry at most twice"
        ),
    }

    result = (
        module.analyze_model_visible_memory(
            memory_segments=[
                (
                    "[interpretive] "
                    "retry exactly twice"
                )
            ],
            target_family_id="alpha",
            clause_by_family=clauses,
        )
    )

    assert (
        result[
            "target_clause_visible"
        ]
        is True
    )

    assert (
        result[
            "wrong_family_clause_count"
        ]
        == 0
    )

    assert (
        result[
            "retrieval_recall"
        ]
        == 1.0
    )

    assert (
        result[
            "retrieval_precision"
        ]
        == 1.0
    )


def test_context_analysis_detects_interference():
    module = _seed017()

    clauses = {
        "alpha": (
            "retry exactly twice"
        ),
        "beta": (
            "retry at most twice"
        ),
        "gamma": (
            "retry at least twice"
        ),
    }

    result = (
        module.analyze_model_visible_memory(
            memory_segments=[
                (
                    "retry exactly twice\n"
                    "retry at most twice\n"
                    "retry at least twice"
                )
            ],
            target_family_id="alpha",
            clause_by_family=clauses,
        )
    )

    assert (
        result[
            "target_clause_visible"
        ]
        is True
    )

    assert (
        result[
            "wrong_family_clause_count"
        ]
        == 2
    )

    assert set(
        result[
            "wrong_family_ids"
        ]
    ) == {
        "beta",
        "gamma",
    }

    assert (
        result[
            "retrieval_recall"
        ]
        == 1.0
    )

    assert (
        result[
            "retrieval_precision"
        ]
        ==
        pytest.approx(
            1 / 3
        )
    )


def test_context_analysis_target_missing():
    module = _seed017()

    clauses = {
        "alpha": (
            "retry exactly twice"
        ),
        "beta": (
            "retry at most twice"
        ),
    }

    result = (
        module.analyze_model_visible_memory(
            memory_segments=[
                "retry at most twice"
            ],
            target_family_id="alpha",
            clause_by_family=clauses,
        )
    )

    assert (
        result[
            "target_clause_visible"
        ]
        is False
    )

    assert (
        result[
            "retrieval_recall"
        ]
        == 0.0
    )

    assert (
        result[
            "retrieval_precision"
        ]
        == 0.0
    )


def test_wrong_rule_decision_contamination():
    module = _seed017()

    clauses = {
        "alpha": (
            "retry exactly twice"
        ),
        "beta": (
            "retry at most twice"
        ),
        "gamma": (
            "never retry the failed request"
        ),
    }

    result = (
        module.analyze_decision_contamination(
            decision_text=(
                "Retry at most twice."
            ),
            target_family_id="alpha",
            clause_by_family=clauses,
        )
    )

    assert (
        result[
            "wrong_rule_contamination"
        ]
        is True
    )

    assert (
        result[
            "wrong_family_ids"
        ]
        == [
            "beta"
        ]
    )


def test_no_wrong_rule_decision_contamination():
    module = _seed017()

    clauses = {
        "alpha": (
            "retry exactly twice"
        ),
        "beta": (
            "retry at most twice"
        ),
    }

    result = (
        module.analyze_decision_contamination(
            decision_text=(
                "Retry exactly twice."
            ),
            target_family_id="alpha",
            clause_by_family=clauses,
        )
    )

    assert (
        result[
            "wrong_rule_contamination"
        ]
        is False
    )


def test_paired_retrieval_regret():
    module = _seed017()

    result = (
        module.classify_paired_regret(
            isolated_pass=True,
            pooled_pass=False,
            pooled_target_visible=False,
            pooled_wrong_family_clause_count=3,
        )
    )

    assert (
        result[
            "retrieval_regret"
        ]
        is True
    )

    assert (
        result[
            "target_omission_regret"
        ]
        is True
    )

    assert (
        result[
            "contamination_regret"
        ]
        is True
    )


def test_no_regret_when_both_pass():
    module = _seed017()

    result = (
        module.classify_paired_regret(
            isolated_pass=True,
            pooled_pass=True,
            pooled_target_visible=True,
            pooled_wrong_family_clause_count=2,
        )
    )

    assert (
        result[
            "retrieval_regret"
        ]
        is False
    )

    assert (
        result[
            "target_omission_regret"
        ]
        is False
    )


def test_regret_requires_isolated_success():
    module = _seed017()

    result = (
        module.classify_paired_regret(
            isolated_pass=False,
            pooled_pass=False,
            pooled_target_visible=False,
            pooled_wrong_family_clause_count=4,
        )
    )

    assert (
        result[
            "retrieval_regret"
        ]
        is False
    )


def test_snapshot_eval_names_are_unique():
    module = _seed017()

    names = [
        module.evaluation_db_name(
            condition="pooled",
            family_id="alpha",
        ),
        module.evaluation_db_name(
            condition="pooled",
            family_id="beta",
        ),
        module.evaluation_db_name(
            condition="isolated",
            family_id="alpha",
        ),
    ]

    assert (
        len(
            names
        )
        ==
        len(
            set(
                names
            )
        )
    )


def test_cluster_summary_aggregates():
    module = _seed017()

    rows = [
        {
            "interference_cluster": (
                "retry-policy"
            ),
            "pooled": {
                "semantic_task_pass": True,
                "target_clause_visible": True,
                "wrong_family_clause_count": 2,
                "retrieval_precision": 1 / 3,
                "retrieval_recall": 1.0,
            },
        },
        {
            "interference_cluster": (
                "retry-policy"
            ),
            "pooled": {
                "semantic_task_pass": False,
                "target_clause_visible": False,
                "wrong_family_clause_count": 1,
                "retrieval_precision": 0.0,
                "retrieval_recall": 0.0,
            },
        },
    ]

    result = (
        module.aggregate_cluster_metrics(
            rows,
            "pooled",
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
        == 1
    )

    assert (
        retry[
            "target_visible_families"
        ]
        == 1
    )

    assert (
        retry[
            "wrong_family_clause_occurrences"
        ]
        == 3
    )


def test_017_has_twenty_fresh_unique_families():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

    families = (
        payload[
            "families"
        ]
    )

    assert (
        len(
            families
        )
        == 20
    )

    assert (
        len(
            {
                family[
                    "id"
                ]

                for family
                in families
            }
        )
        == 20
    )


def test_017_has_four_interference_clusters():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

    clusters = {
        family[
            "interference_cluster"
        ]

        for family
        in payload[
            "families"
        ]
    }

    assert clusters == {
        "retry-policy",
        "lane-routing",
        "channel-session",
        "storage-finalization",
    }


def test_each_cluster_has_five_families():
    tasks = _tasks017()

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

    assert set(
        counts.values()
    ) == {
        5
    }


def test_each_target_has_nineteen_distractors():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        assert (
            len(
                family[
                    "distractor_family_ids"
                ]
            )
            == 19
        )

        assert (
            family[
                "id"
            ]
            not in
            family[
                "distractor_family_ids"
            ]
        )


def test_each_target_has_four_near_neighbors():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        assert (
            len(
                family[
                    "near_neighbor_family_ids"
                ]
            )
            == 4
        )


def test_each_family_has_shared_and_unique_entities():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        entities = set(
            family[
                "entities"
            ]
        )

        assert (
            "domain:recovery"
            in entities
        )

        assert (
            (
                "cluster:"
                +
                family[
                    "interference_cluster"
                ]
            )
            in entities
        )

        assert any(
            entity.startswith(
                "system:"
            )

            for entity
            in entities
        )

        assert any(
            entity.startswith(
                "code:"
            )

            for entity
            in entities
        )


def test_all_semantic_clauses_are_unique():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

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
        len(
            clauses
        )
        ==
        len(
            set(
                clauses
            )
        )
    )


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks017()

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


def test_each_family_has_four_canonical_atoms():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

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


def test_taskset_declares_pool_size():
    tasks = _tasks017()

    payload = (
        tasks.build_taskset()
    )

    assert (
        payload[
            "pool_size"
        ]
        == 20
    )

    assert (
        payload[
            "distractors_per_target"
        ]
        == 19
    )

    assert (
        payload[
            "near_neighbors_per_target"
        ]
        == 4
    )
