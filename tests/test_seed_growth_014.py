import importlib
import inspect

import pytest

from experiments.make_tasks_008 import build_raw_source


def _seed014():
    try:
        return importlib.import_module(
            "experiments.seed_growth_014"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 014 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks014():
    try:
        return importlib.import_module(
            "experiments.make_tasks_014"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 014 task generator "
            f"does not exist yet: {exc}"
        )


def _source(
    authoritative_text: str,
):
    return build_raw_source(
        status="ZX-14 run status was FAIL.",
        failed_decision=(
            "Reuse the unsafe value."
        ),
        authoritative_sentences=[
            authoritative_text
        ],
        operator_note=(
            "Operator suspects transient congestion."
        ),
        diagnostic_metadata=(
            "Observed diagnostic latency was 211 ms."
        ),
    )


def _recoverable_candidate():
    return {
        "source_quote": (
            "never reuse the prior nonce"
        ),
        "nucleus_quote": (
            "never reuse the prior nonce"
        ),
        "qualifiers": [
            {
                "type": "negation",
                "source_quote": "never",
            }
        ],
    }


def test_support_first_gate_has_no_oracle_arguments():
    module = _seed014()

    signature = inspect.signature(
        module.reconcile_support_first
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


def test_valid_support_survives_invalid_structure():
    module = _seed014()

    source = _source(
        "refresh the lease; "
        "never reuse the prior nonce."
    )

    proposal = {
        "propositions": [
            _recoverable_candidate()
        ]
    }

    result = (
        module.reconcile_support_first(
            proposal=proposal,
            source_text=source,
        )
    )

    assert (
        result[
            "structured"
        ]
        == []
    )

    assert len(
        result[
            "fallback"
        ]
    ) == 1

    fallback = (
        result[
            "fallback"
        ][0]
    )

    assert (
        fallback[
            "source_quote"
        ]
        ==
        "never reuse the prior nonce"
    )

    assert (
        fallback[
            "structure_status"
        ]
        ==
        "unresolved"
    )


def test_fabricated_support_is_not_preserved():
    module = _seed014()

    source = _source(
        "never reuse the prior nonce."
    )

    proposal = {
        "propositions": [
            {
                "source_quote": (
                    "restart the moon server"
                ),
                "nucleus_quote": (
                    "restart the moon server"
                ),
                "qualifiers": [],
            }
        ]
    }

    result = (
        module.reconcile_support_first(
            proposal=proposal,
            source_text=source,
        )
    )

    assert (
        result[
            "fallback"
        ]
        == []
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "source_quote_not_unique"

        for rejection
        in result[
            "hard_rejections"
        ]
    )


def test_non_authoritative_support_is_not_preserved():
    module = _seed014()

    source = _source(
        "never reuse the prior nonce."
    )

    proposal = {
        "propositions": [
            {
                "source_quote": (
                    "Reuse the unsafe value."
                ),
                "nucleus_quote": (
                    "Reuse the unsafe value."
                ),
                "qualifiers": [],
            }
        ]
    }

    result = (
        module.reconcile_support_first(
            proposal=proposal,
            source_text=source,
        )
    )

    assert (
        result[
            "fallback"
        ]
        == []
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "ineligible_source_role"

        for rejection
        in result[
            "hard_rejections"
        ]
    )


def test_valid_structured_support_does_not_create_duplicate_fallback():
    module = _seed014()

    source = _source(
        "never reuse the prior nonce."
    )

    proposal = {
        "propositions": [
            {
                "source_quote": (
                    "never reuse the prior nonce"
                ),
                "nucleus_quote": (
                    "never reuse the prior nonce"
                ),
                "qualifiers": [],
            }
        ]
    }

    result = (
        module.reconcile_support_first(
            proposal=proposal,
            source_text=source,
        )
    )

    assert len(
        result[
            "structured"
        ]
    ) == 1

    assert (
        result[
            "fallback"
        ]
        == []
    )


def test_larger_structured_support_covers_smaller_valid_support():
    module = _seed014()

    source = _source(
        "refresh the lease; "
        "never reuse the prior nonce."
    )

    proposal = {
        "propositions": [
            {
                "source_quote": (
                    "refresh the lease; "
                    "never reuse the prior nonce"
                ),
                "nucleus_quote": (
                    "refresh the lease"
                ),
                "qualifiers": [],
            },
            _recoverable_candidate(),
        ]
    }

    result = (
        module.reconcile_support_first(
            proposal=proposal,
            source_text=source,
        )
    )

    assert len(
        result[
            "structured"
        ]
    ) == 1

    assert (
        result[
            "fallback"
        ]
        == []
    )

    assert (
        result[
            "valid_supports_covered_by_structure"
        ]
        >= 1
    )


def test_fallback_ancestry_is_exact():
    module = _seed014()

    source = _source(
        "never reuse the prior nonce."
    )

    result = (
        module.reconcile_support_first(
            proposal={
                "propositions": [
                    _recoverable_candidate()
                ]
            },
            source_text=source,
        )
    )

    fallback = (
        result[
            "fallback"
        ][0]
    )

    assert (
        module.grounded_fallback_ancestry_valid(
            fallback=fallback,
            source_text=source,
        )
        is True
    )


def test_fallback_projection_uses_exact_support():
    module = _seed014()

    fallback = {
        "id": "G1",
        "source_quote": (
            "never reuse the prior nonce"
        ),
        "source_start": 100,
        "source_end": 127,
        "source_role": (
            "authoritative_correction"
        ),
        "source_sha256": "source",
        "support_span_sha256": "span",
        "structure_status": "unresolved",
    }

    projected = (
        module.fallback_projection(
            [
                fallback
            ]
        )
    )

    assert (
        projected[
            0
        ][
            "text"
        ]
        ==
        "never reuse the prior nonce"
    )

    assert (
        projected[
            0
        ][
            "source_quote"
        ]
        ==
        "never reuse the prior nonce"
    )


def test_lossless_renderer_exposes_unresolved_support():
    module = _seed014()

    fallback = {
        "id": "G1",
        "source_quote": (
            "never reuse the prior nonce"
        ),
        "source_start": 100,
        "source_end": 127,
        "source_role": (
            "authoritative_correction"
        ),
        "source_sha256": "source",
        "support_span_sha256": "span",
        "structure_status": "unresolved",
    }

    rendered = (
        module.render_lossless_semantic_memory(
            structured=[],
            fallback=[
                fallback
            ],
        )
    )

    assert (
        "never reuse the prior nonce"
        in rendered
    )

    assert (
        "UNRESOLVED_GROUNDED_SUPPORT"
        in rendered
    )

    assert (
        "AUTHORITATIVE_SEMANTIC_PAYLOAD"
        in rendered
    )


def test_semantic_clause_can_survive_via_fallback():
    module = _seed014()

    fallback = {
        "id": "G1",
        "source_quote": (
            "never reuse the prior nonce"
        ),
    }

    assert (
        module.semantic_clause_survives(
            structured=[],
            fallback=[
                fallback
            ],
            semantic_clause=(
                "never reuse the prior nonce"
            ),
        )
        is True
    )


def test_unsafe_challenge_counter():
    module = _seed014()

    family = {
        "fallback_challenges": {
            "unsafe": [
                {
                    "id": "U1",
                    "kind": "fabricated",
                    "source_quote": "fabricated rule",
                },
                {
                    "id": "U2",
                    "kind": "nonauthoritative",
                    "source_quote": "unsafe old decision",
                },
            ]
        }
    }

    fallback = [
        {
            "source_quote": (
                "unrelated valid support"
            )
        }
    ]

    counts = (
        module.count_unsafe_challenge_admissions(
            family=family,
            structured=[],
            fallback=fallback,
        )
    )

    assert counts == {
        "fabricated": 0,
        "nonauthoritative": 0,
        "total": 0,
    }


def test_recoverable_challenge_retention_counter():
    module = _seed014()

    family = {
        "fallback_challenges": {
            "recoverable": [
                {
                    "id": "R1",
                    "source_quote": (
                        "never reuse the prior nonce"
                    ),
                }
            ]
        }
    }

    fallback = [
        {
            "source_quote": (
                "never reuse the prior nonce"
            )
        }
    ]

    assert (
        module.count_recoverable_challenges_retained(
            family=family,
            structured=[],
            fallback=fallback,
        )
        == 1
    )


def test_014_has_twenty_fresh_unique_families():
    tasks = _tasks014()

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


def test_014_covers_all_semantic_dimensions():
    tasks = _tasks014()

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


def test_014_covers_all_operator_classes():
    tasks = _tasks014()

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


def test_each_family_has_one_recoverable_and_two_unsafe_challenges():
    tasks = _tasks014()

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


def test_recoverable_challenge_support_is_exact_authoritative_text():
    tasks = _tasks014()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        challenge = (
            family[
                "fallback_challenges"
            ][
                "recoverable"
            ][0]
        )

        assert (
            family[
                "raw_source"
            ].count(
                challenge[
                    "source_quote"
                ]
            )
            == 1
        )

        assert (
            challenge[
                "source_quote"
            ]
            ==
            family[
                "semantic_clause"
            ]
        )


def test_fabricated_challenge_is_absent_from_source():
    tasks = _tasks014()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        fabricated = [
            challenge

            for challenge
            in family[
                "fallback_challenges"
            ][
                "unsafe"
            ]

            if (
                challenge[
                    "kind"
                ]
                ==
                "fabricated"
            )
        ][0]

        assert (
            fabricated[
                "source_quote"
            ]
            not in
            family[
                "raw_source"
            ]
        )


def test_nonauthoritative_challenge_is_real_source_text():
    tasks = _tasks014()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        challenge = [
            challenge

            for challenge
            in family[
                "fallback_challenges"
            ][
                "unsafe"
            ]

            if (
                challenge[
                    "kind"
                ]
                ==
                "nonauthoritative"
            )
        ][0]

        assert (
            family[
                "raw_source"
            ].count(
                challenge[
                    "source_quote"
                ]
            )
            == 1
        )

        assert (
            challenge[
                "source_quote"
            ]
            ==
            family[
                "candidate_decision"
            ]
        )


def test_014_still_has_structural_attack_challenges():
    tasks = _tasks014()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        assert len(
            family[
                "structured_compound_challenges"
            ]
        ) == 2
