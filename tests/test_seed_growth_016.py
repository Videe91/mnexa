import importlib

import pytest


def _seed016():
    try:
        return importlib.import_module(
            "experiments.seed_growth_016"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 016 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks016():
    try:
        return importlib.import_module(
            "experiments.make_tasks_016"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 016 task generator "
            f"does not exist yet: {exc}"
        )


def test_transfer_attempt_count_is_three():
    module = _seed016()

    assert (
        module.TRANSFER_ATTEMPTS_PER_CONDITION
        == 3
    )


def test_replicate_names_are_unique():
    module = _seed016()

    names = (
        module.replicate_condition_names(
            "compact",
            3,
        )
    )

    assert names == [
        "compact_r1",
        "compact_r2",
        "compact_r3",
    ]

    assert len(
        set(names)
    ) == 3


def test_stability_summary_majority_but_not_unanimous():
    module = _seed016()

    summary = (
        module.summarize_boolean_replicates(
            [
                True,
                True,
                False,
            ]
        )
    )

    assert (
        summary[
            "attempts"
        ]
        == 3
    )

    assert (
        summary[
            "passes"
        ]
        == 2
    )

    assert (
        summary[
            "pass_rate"
        ]
        ==
        pytest.approx(
            2 / 3
        )
    )

    assert (
        summary[
            "majority_pass"
        ]
        is True
    )

    assert (
        summary[
            "unanimous_pass"
        ]
        is False
    )


def test_stability_summary_unanimous():
    module = _seed016()

    summary = (
        module.summarize_boolean_replicates(
            [
                True,
                True,
                True,
            ]
        )
    )

    assert (
        summary[
            "majority_pass"
        ]
        is True
    )

    assert (
        summary[
            "unanimous_pass"
        ]
        is True
    )


def test_stability_summary_all_fail():
    module = _seed016()

    summary = (
        module.summarize_boolean_replicates(
            [
                False,
                False,
                False,
            ]
        )
    )

    assert (
        summary[
            "passes"
        ]
        == 0
    )

    assert (
        summary[
            "majority_pass"
        ]
        is False
    )

    assert (
        summary[
            "unanimous_pass"
        ]
        is False
    )


def test_three_attempt_majority_requires_two_passes():
    module = _seed016()

    assert (
        module.is_majority_pass(
            passes=2,
            attempts=3,
        )
        is True
    )

    assert (
        module.is_majority_pass(
            passes=1,
            attempts=3,
        )
        is False
    )


def test_replicate_lessons_must_be_identical():
    module = _seed016()

    replicates = [
        {
            "lesson": "same lesson",
            "memory_word_count": 42,
        },
        {
            "lesson": "same lesson",
            "memory_word_count": 42,
        },
        {
            "lesson": "same lesson",
            "memory_word_count": 42,
        },
    ]

    result = (
        module.replicate_memory_consistent(
            replicates
        )
    )

    assert (
        result[
            "lesson_text_equal"
        ]
        is True
    )

    assert (
        result[
            "memory_word_count_equal"
        ]
        is True
    )


def test_replicate_memory_check_detects_difference():
    module = _seed016()

    replicates = [
        {
            "lesson": "lesson A",
            "memory_word_count": 42,
        },
        {
            "lesson": "lesson B",
            "memory_word_count": 43,
        },
    ]

    result = (
        module.replicate_memory_consistent(
            replicates
        )
    )

    assert (
        result[
            "lesson_text_equal"
        ]
        is False
    )

    assert (
        result[
            "memory_word_count_equal"
        ]
        is False
    )


def test_operator_stability_aggregates_attempts():
    module = _seed016()

    rows = [
        {
            "semantic_operator": "only",
            "summary": {
                "attempts": 3,
                "passes": 2,
                "majority_pass": True,
                "unanimous_pass": False,
            },
        },
        {
            "semantic_operator": "only",
            "summary": {
                "attempts": 3,
                "passes": 3,
                "majority_pass": True,
                "unanimous_pass": True,
            },
        },
        {
            "semantic_operator": "never",
            "summary": {
                "attempts": 3,
                "passes": 3,
                "majority_pass": True,
                "unanimous_pass": True,
            },
        },
    ]

    result = (
        module.aggregate_operator_stability(
            rows
        )
    )

    assert (
        result[
            "only"
        ][
            "attempts"
        ]
        == 6
    )

    assert (
        result[
            "only"
        ][
            "passes"
        ]
        == 5
    )

    assert (
        result[
            "only"
        ][
            "majority_family_passes"
        ]
        == 2
    )

    assert (
        result[
            "only"
        ][
            "unanimous_family_passes"
        ]
        == 1
    )

    assert (
        result[
            "never"
        ][
            "pass_rate"
        ]
        == 1.0
    )


def test_dimension_stability_aggregates_attempts():
    module = _seed016()

    rows = [
        {
            "semantic_dimension": "scope",
            "summary": {
                "attempts": 3,
                "passes": 2,
                "majority_pass": True,
                "unanimous_pass": False,
            },
        },
        {
            "semantic_dimension": "scope",
            "summary": {
                "attempts": 3,
                "passes": 3,
                "majority_pass": True,
                "unanimous_pass": True,
            },
        },
    ]

    result = (
        module.aggregate_dimension_stability(
            rows
        )
    )

    assert (
        result[
            "scope"
        ][
            "attempts"
        ]
        == 6
    )

    assert (
        result[
            "scope"
        ][
            "passes"
        ]
        == 5
    )


def test_016_has_twenty_fresh_unique_families():
    tasks = _tasks016()

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


def test_016_covers_four_semantic_dimensions():
    tasks = _tasks016()

    payload = (
        tasks.build_taskset()
    )

    assert {
        family[
            "semantic_dimension"
        ]

        for family
        in payload[
            "families"
        ]
    } == {
        "polarity",
        "scope",
        "cardinality",
        "condition",
    }


def test_016_covers_all_operator_classes():
    tasks = _tasks016()

    payload = (
        tasks.build_taskset()
    )

    operators = {
        family[
            "semantic_operator"
        ]

        for family
        in payload[
            "families"
        ]
    }

    assert {
        "never",
        "do_not",
        "only",
        "exactly",
        "at_least",
        "at_most",
        "unless",
        "when_if",
    }.issubset(
        operators
    )


def test_each_family_keeps_fallback_attacks():
    tasks = _tasks016()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        challenges = (
            family[
                "fallback_challenges"
            ]
        )

        assert len(
            challenges[
                "recoverable"
            ]
        ) == 1

        assert len(
            challenges[
                "unsafe"
            ]
        ) == 2


def test_semantic_clause_is_exact_source_text():
    tasks = _tasks016()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        clause = (
            family[
                "semantic_clause"
            ]
        )

        assert (
            family[
                "raw_source"
            ].count(
                clause
            )
            == 1
        )


def test_each_family_has_four_canonical_atoms():
    tasks = _tasks016()

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


def test_experiment_declares_three_transfer_attempts():
    tasks = _tasks016()

    payload = (
        tasks.build_taskset()
    )

    assert (
        payload[
            "transfer_attempts_per_condition"
        ]
        == 3
    )
