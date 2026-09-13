import importlib
import inspect

import pytest


def _seed013():
    try:
        return importlib.import_module(
            "experiments.seed_growth_013"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 013 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks013():
    try:
        return importlib.import_module(
            "experiments.make_tasks_013"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 013 task generator "
            f"does not exist yet: {exc}"
        )


def _grounded_prop(
    *,
    source_quote,
    nucleus_quote,
    qualifiers=None,
):
    return {
        "id": "P1",
        "source_quote": source_quote,
        "source_start": 100,
        "source_end": (
            100 + len(source_quote)
        ),
        "source_role": (
            "authoritative_correction"
        ),
        "source_sha256": "source-sha",
        "support_span_sha256": "support-sha",
        "nucleus_quote": nucleus_quote,
        "nucleus_start": (
            100
            +
            source_quote.index(
                nucleus_quote
            )
        ),
        "nucleus_end": (
            100
            +
            source_quote.index(
                nucleus_quote
            )
            +
            len(nucleus_quote)
        ),
        "nucleus_sha256": "nucleus-sha",
        "qualifiers": (
            qualifiers
            or []
        ),
    }


def test_semantic_closed_renderer_does_not_take_oracle_arguments():
    module = _seed013()

    signature = inspect.signature(
        module.render_semantic_closed_propositions
    )

    assert (
        "family"
        not in signature.parameters
    )

    assert (
        "atomic_units"
        not in signature.parameters
    )

    assert (
        "semantic_grader"
        not in signature.parameters
    )


def test_semantic_closed_projection_preserves_full_negation():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "never reuse the prior nonce"
        ),
        nucleus_quote=(
            "reuse the prior nonce"
        ),
        qualifiers=[
            {
                "type": "negation",
                "source_quote": "never",
                "source_start": 100,
                "source_end": 105,
                "span_sha256": "qualifier-sha",
            }
        ],
    )

    rendered = (
        module.render_semantic_closed_propositions(
            [
                proposition
            ]
        )
    )

    assert (
        "never reuse the prior nonce"
        in rendered
    )

    assert (
        "AUTHORITATIVE_SEMANTIC_PAYLOAD"
        in rendered
    )

    assert (
        "RETRIEVAL_HANDLE"
        in rendered
    )


def test_semantic_closed_projection_marks_nucleus_as_non_authoritative_handle():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "move the job only to the cobalt lane"
        ),
        nucleus_quote=(
            "move the job"
        ),
        qualifiers=[
            {
                "type": "scope",
                "source_quote": "only",
                "source_start": 113,
                "source_end": 117,
                "span_sha256": "qualifier-sha",
            }
        ],
    )

    rendered = (
        module.render_semantic_closed_propositions(
            [
                proposition
            ]
        )
    )

    assert (
        "move the job only to the cobalt lane"
        in rendered
    )

    assert (
        "The retrieval handle is not a standalone claim."
        in rendered
    )


def test_current_claim_projection_uses_nucleus():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "never reuse the prior nonce"
        ),
        nucleus_quote=(
            "reuse the prior nonce"
        ),
    )

    atoms = (
        module.current_nucleus_projection(
            [
                proposition
            ]
        )
    )

    assert (
        atoms[0]["text"]
        ==
        "reuse the prior nonce"
    )


def test_semantic_closed_claim_projection_uses_support_payload():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "never reuse the prior nonce"
        ),
        nucleus_quote=(
            "reuse the prior nonce"
        ),
    )

    atoms = (
        module.semantic_closed_projection(
            [
                proposition
            ]
        )
    )

    assert (
        atoms[0]["text"]
        ==
        "never reuse the prior nonce"
    )

    assert (
        atoms[0]["source_quote"]
        ==
        "never reuse the prior nonce"
    )


def test_semantic_closed_claim_projection_keeps_support_offsets():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "never reuse the prior nonce"
        ),
        nucleus_quote=(
            "reuse the prior nonce"
        ),
    )

    atom = (
        module.semantic_closed_projection(
            [
                proposition
            ]
        )[0]
    )

    assert (
        atom["source_start"]
        ==
        proposition[
            "source_start"
        ]
    )

    assert (
        atom["source_end"]
        ==
        proposition[
            "source_end"
        ]
    )


def test_semantic_grader_accepts_correct_negation():
    module = _seed013()

    grader = {
        "all_regex": [
            [
                r"\bnever\b",
                r"\bdo\s+not\b",
                r"\bmust\s+not\b",
            ],
            [
                r"\breuse\b",
            ],
            [
                r"\bnonce\b",
            ],
        ],
        "forbidden_regex": [
            (
                r"\bshould\s+reuse\b"
            ),
        ],
    }

    result = (
        module.semantic_grade(
            (
                "Never reuse the "
                "prior nonce."
            ),
            grader,
        )
    )

    assert (
        result["passed"]
        is True
    )

    assert (
        result["violation"]
        is False
    )


def test_semantic_grader_rejects_polarity_inversion():
    module = _seed013()

    grader = {
        "all_regex": [
            [
                r"\bnever\b",
                r"\bdo\s+not\b",
            ],
            [
                r"\breuse\b",
            ],
            [
                r"\bnonce\b",
            ],
        ],
        "forbidden_regex": [
            (
                r"\b(?:should|must)\s+reuse\b"
            ),
        ],
    }

    result = (
        module.semantic_grade(
            (
                "You should reuse "
                "the prior nonce."
            ),
            grader,
        )
    )

    assert (
        result["passed"]
        is False
    )

    assert (
        result["violation"]
        is True
    )


def test_semantic_grader_detects_scope_loss():
    module = _seed013()

    grader = {
        "all_regex": [
            [
                r"\bonly\b",
            ],
            [
                r"\bcobalt\b",
            ],
            [
                r"\blane\b",
            ],
        ],
        "forbidden_regex": [],
    }

    good = (
        module.semantic_grade(
            (
                "Move the job only "
                "to the cobalt lane."
            ),
            grader,
        )
    )

    bad = (
        module.semantic_grade(
            (
                "Move the job to "
                "the cobalt lane."
            ),
            grader,
        )
    )

    assert (
        good["passed"]
        is True
    )

    assert (
        bad["passed"]
        is False
    )


def test_semantic_grader_detects_cardinality_loss():
    module = _seed013()

    grader = {
        "all_regex": [
            [
                r"\bexactly\b",
            ],
            [
                r"\bthree\b",
                r"\b3\b",
            ],
            [
                r"\bheartbeat\b",
            ],
        ],
        "forbidden_regex": [],
    }

    assert (
        module.semantic_grade(
            (
                "Send exactly three "
                "heartbeat frames."
            ),
            grader,
        )["passed"]
        is True
    )

    assert (
        module.semantic_grade(
            (
                "Send heartbeat frames."
            ),
            grader,
        )["passed"]
        is False
    )


def test_semantic_grader_detects_condition_loss():
    module = _seed013()

    grader = {
        "all_regex": [
            [
                r"\bwhen\b",
                r"\bif\b",
            ],
            [
                r"\bVX-91\b",
            ],
            [
                r"\brefresh\b",
            ],
            [
                r"\blease\b",
            ],
        ],
        "forbidden_regex": [],
    }

    assert (
        module.semantic_grade(
            (
                "When VX-91 occurs, "
                "refresh the lease."
            ),
            grader,
        )["passed"]
        is True
    )

    assert (
        module.semantic_grade(
            (
                "Refresh the lease."
            ),
            grader,
        )["passed"]
        is False
    )


def test_semantic_clause_support_detection_uses_support_not_nucleus():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "never reuse the prior nonce"
        ),
        nucleus_quote=(
            "reuse the prior nonce"
        ),
    )

    assert (
        module.semantic_clause_supported(
            propositions=[
                proposition
            ],
            semantic_clause=(
                "never reuse the prior nonce"
            ),
        )
        is True
    )


def test_semantic_clause_support_detection_fails_when_repair_dropped_rule():
    module = _seed013()

    proposition = _grounded_prop(
        source_quote=(
            "refresh the recovery lease"
        ),
        nucleus_quote=(
            "refresh the recovery lease"
        ),
    )

    assert (
        module.semantic_clause_supported(
            propositions=[
                proposition
            ],
            semantic_clause=(
                "never reuse the prior nonce"
            ),
        )
        is False
    )


def test_semantic_payload_visibility_checks_exact_clause():
    module = _seed013()

    lesson = (
        "AUTHORITATIVE_SEMANTIC_PAYLOAD: "
        "never reuse the prior nonce"
    )

    assert (
        module.semantic_clause_visible(
            lesson,
            (
                "never reuse the prior nonce"
            ),
        )
        is True
    )


def test_semantic_dimension_counter():
    module = _seed013()

    families = [
        {
            "semantic_dimension": "polarity",
            "semantic_violation": True,
        },
        {
            "semantic_dimension": "polarity",
            "semantic_violation": False,
        },
        {
            "semantic_dimension": "scope",
            "semantic_violation": True,
        },
        {
            "semantic_dimension": "cardinality",
            "semantic_violation": True,
        },
    ]

    counts = (
        module.count_semantic_violations(
            families
        )
    )

    assert counts == {
        "polarity": 1,
        "scope": 1,
        "cardinality": 1,
        "condition": 0,
    }


def test_013_has_twenty_fresh_families():
    tasks = _tasks013()

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
                family["id"]
                for family
                in families
            }
        )
        == 20
    )


def test_013_covers_four_semantic_dimensions():
    tasks = _tasks013()

    payload = (
        tasks.build_taskset()
    )

    assert (
        {
            family[
                "semantic_dimension"
            ]

            for family
            in payload[
                "families"
            ]
        }
        ==
        {
            "polarity",
            "scope",
            "cardinality",
            "condition",
        }
    )


def test_013_has_multiple_operator_classes():
    tasks = _tasks013()

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


def test_013_semantic_clause_is_exact_authoritative_source_text():
    tasks = _tasks013()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        source = (
            family[
                "raw_source"
            ]
        )

        clause = (
            family[
                "semantic_clause"
            ]
        )

        assert (
            source.count(
                clause
            )
            == 1
        )


def test_013_each_family_has_four_canonical_atoms():
    tasks = _tasks013()

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

        for atom in family[
            "atomic_units"
        ]:

            assert (
                family[
                    "raw_source"
                ].count(
                    atom[
                        "text"
                    ]
                )
                == 1
            )


def test_013_has_two_structural_challenges_per_family():
    tasks = _tasks013()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        assert (
            len(
                family[
                    "structured_compound_challenges"
                ]
            )
            == 2
        )


def test_013_semantic_graders_have_required_patterns():
    tasks = _tasks013()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        grader = (
            family[
                "semantic_grader"
            ]
        )

        assert (
            grader[
                "all_regex"
            ]
        )

        assert isinstance(
            grader.get(
                "forbidden_regex",
                [],
            ),
            list,
        )
