import importlib
import inspect

import pytest

from experiments.make_tasks_008 import build_raw_source


def _seed011():
    try:
        return importlib.import_module(
            "experiments.seed_growth_011"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 011 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks011():
    try:
        return importlib.import_module(
            "experiments.make_tasks_011"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 011 task generator "
            f"does not exist yet: {exc}"
        )


def _source(
    authoritative_text: str,
):
    return build_raw_source(
        status="ZX-11 run status was FAIL.",
        failed_decision=(
            "Restart every worker."
        ),
        authoritative_sentences=[
            authoritative_text
        ],
        operator_note=(
            "Operator suspects transient congestion."
        ),
        diagnostic_metadata=(
            "Observed diagnostic latency was 187 ms."
        ),
    )


def _structured_proposal(
    *propositions,
):
    return {
        "propositions": list(
            propositions
        )
    }


def _prop(
    *,
    source_quote,
    nucleus_quote,
    qualifiers=None,
):
    return {
        "source_quote": (
            source_quote
        ),
        "nucleus_quote": (
            nucleus_quote
        ),
        "qualifiers": (
            qualifiers
            or []
        ),
    }


def test_structured_gate_does_not_accept_oracle_boundary_arguments():
    module = _seed011()

    signature = inspect.signature(
        module.admit_structured_propositions
    )

    assert (
        "family"
        not in signature.parameters
    )

    assert (
        "atomic_units"
        not in signature.parameters
    )


def test_structured_prompt_requires_nucleus_and_literal_ancestry():
    module = _seed011()

    prompt = (
        module
        .build_structured_proposition_prompt(
            _source(
                "When ZX-11 occurs, "
                "refresh the recovery lease; "
                "then wait 8 seconds."
            )
        )
        .lower()
    )

    assert "source_quote" in prompt
    assert "nucleus_quote" in prompt
    assert "qualifiers" in prompt
    assert "exact" in prompt
    assert "authoritative" in prompt
    assert "do not paraphrase" in prompt
    assert "condition" in prompt
    assert "ordering" in prompt


def test_numbered_prefix_can_be_support_without_being_nucleus():
    module = _seed011()

    source = _source(
        "1) refresh the recovery lease; "
        "2) wait 8 seconds."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "1) refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                )
            ),
            source_text=source,
        )
    )

    assert len(
        result["admitted"]
    ) == 1

    proposition = (
        result[
            "admitted"
        ][0]
    )

    assert (
        proposition[
            "source_quote"
        ]
        ==
        "1) refresh the recovery lease"
    )

    assert (
        proposition[
            "nucleus_quote"
        ]
        ==
        "refresh the recovery lease"
    )

    assert (
        proposition[
            "nucleus_start"
        ]
        >
        proposition[
            "source_start"
        ]
    )


def test_condition_qualifier_is_grounded_inside_support():
    module = _seed011()

    source = _source(
        "When ZX-11 occurs, "
        "refresh the recovery lease; "
        "then wait 8 seconds."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "When ZX-11 occurs, "
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                    qualifiers=[
                        {
                            "type": "condition",
                            "source_quote": (
                                "When ZX-11 occurs"
                            ),
                        }
                    ],
                )
            ),
            source_text=source,
        )
    )

    assert len(
        result[
            "admitted"
        ]
    ) == 1

    qualifier = (
        result[
            "admitted"
        ][0][
            "qualifiers"
        ][0]
    )

    assert (
        qualifier[
            "type"
        ]
        ==
        "condition"
    )

    assert (
        qualifier[
            "source_quote"
        ]
        ==
        "When ZX-11 occurs"
    )


def test_ordering_qualifier_is_grounded_inside_support():
    module = _seed011()

    source = _source(
        "refresh the recovery lease; "
        "then wait 8 seconds."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "then wait 8 seconds"
                    ),
                    nucleus_quote=(
                        "wait 8 seconds"
                    ),
                    qualifiers=[
                        {
                            "type": "ordering",
                            "source_quote": "then",
                        }
                    ],
                )
            ),
            source_text=source,
        )
    )

    assert len(
        result[
            "admitted"
        ]
    ) == 1

    assert (
        result[
            "admitted"
        ][0][
            "nucleus_quote"
        ]
        ==
        "wait 8 seconds"
    )


def test_invented_nucleus_is_rejected():
    module = _seed011()

    source = _source(
        "refresh the recovery lease."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "restart the moon server"
                    ),
                )
            ),
            source_text=source,
        )
    )

    assert (
        result[
            "admitted"
        ]
        == []
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "nucleus_not_unique_in_source_quote"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_invented_qualifier_is_rejected():
    module = _seed011()

    source = _source(
        "When ZX-11 occurs, "
        "refresh the recovery lease."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "When ZX-11 occurs, "
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                    qualifiers=[
                        {
                            "type": "condition",
                            "source_quote": (
                                "When the moon is blue"
                            ),
                        }
                    ],
                )
            ),
            source_text=source,
        )
    )

    assert (
        result[
            "admitted"
        ]
        == []
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "qualifier_not_unique_in_source_quote"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_non_authoritative_support_is_rejected():
    module = _seed011()

    source = _source(
        "refresh the recovery lease."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "ZX-11 run status was FAIL."
                    ),
                    nucleus_quote=(
                        "ZX-11 run status was FAIL."
                    ),
                )
            ),
            source_text=source,
        )
    )

    assert (
        result[
            "admitted"
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
            "rejected"
        ]
    )


def test_unknown_qualifier_type_is_rejected():
    module = _seed011()

    source = _source(
        "When ZX-11 occurs, "
        "refresh the recovery lease."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "When ZX-11 occurs, "
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                    qualifiers=[
                        {
                            "type": "magic",
                            "source_quote": (
                                "When ZX-11 occurs"
                            ),
                        }
                    ],
                )
            ),
            source_text=source,
        )
    )

    assert (
        result[
            "admitted"
        ]
        == []
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "unsupported_qualifier_type"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_smaller_nuclei_win_over_compound_nucleus():
    module = _seed011()

    source = _source(
        "refresh the recovery lease "
        "and wait 8 seconds."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                ),
                _prop(
                    source_quote=(
                        "wait 8 seconds"
                    ),
                    nucleus_quote=(
                        "wait 8 seconds"
                    ),
                ),
                _prop(
                    source_quote=(
                        "refresh the recovery lease "
                        "and wait 8 seconds"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease "
                        "and wait 8 seconds"
                    ),
                ),
            ),
            source_text=source,
        )
    )

    admitted = {
        proposition[
            "nucleus_quote"
        ]
        for proposition
        in result[
            "admitted"
        ]
    }

    assert (
        "refresh the recovery lease"
        in admitted
    )

    assert (
        "wait 8 seconds"
        in admitted
    )

    assert (
        "refresh the recovery lease "
        "and wait 8 seconds"
        not in admitted
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "nucleus_overlaps_admitted_nucleus"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_structured_final_nuclei_do_not_overlap():
    module = _seed011()

    source = _source(
        "refresh the recovery lease "
        "and wait 8 seconds; "
        "retry exactly once."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                ),
                _prop(
                    source_quote=(
                        "wait 8 seconds"
                    ),
                    nucleus_quote=(
                        "wait 8 seconds"
                    ),
                ),
                _prop(
                    source_quote=(
                        "retry exactly once"
                    ),
                    nucleus_quote=(
                        "retry exactly once"
                    ),
                ),
                _prop(
                    source_quote=(
                        "refresh the recovery lease "
                        "and wait 8 seconds"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease "
                        "and wait 8 seconds"
                    ),
                ),
            ),
            source_text=source,
        )
    )

    assert (
        module.count_nucleus_overlaps(
            result[
                "admitted"
            ]
        )
        == 0
    )


def test_structured_source_ancestry_is_verifiable():
    module = _seed011()

    source = _source(
        "When ZX-11 occurs, "
        "refresh the recovery lease."
    )

    result = (
        module.admit_structured_propositions(
            proposal=_structured_proposal(
                _prop(
                    source_quote=(
                        "When ZX-11 occurs, "
                        "refresh the recovery lease"
                    ),
                    nucleus_quote=(
                        "refresh the recovery lease"
                    ),
                    qualifiers=[
                        {
                            "type": "condition",
                            "source_quote": (
                                "When ZX-11 occurs"
                            ),
                        }
                    ],
                )
            ),
            source_text=source,
        )
    )

    assert (
        module.structured_source_ancestry_valid(
            proposition=(
                result[
                    "admitted"
                ][0]
            ),
            source_text=source,
        )
        is True
    )


def test_structured_parser_accepts_json_fence():
    module = _seed011()

    text = """
```json
{
  "propositions": [
    {
      "source_quote": "then wait 8 seconds",
      "nucleus_quote": "wait 8 seconds",
      "qualifiers": [
        {
          "type": "ordering",
          "source_quote": "then"
        }
      ]
    }
  ]
}
```
""".strip()

    parsed = (
        module.parse_structured_proposal(
            text
        )
    )

    assert (
        parsed[
            "propositions"
        ][0][
            "nucleus_quote"
        ]
        ==
        "wait 8 seconds"
    )


def test_nucleus_metrics_are_bounded():
    module = _seed011()

    expected = [
        {
            "id": "A1",
            "text": (
                "refresh the recovery lease"
            ),
        },
        {
            "id": "A2",
            "text": (
                "wait 8 seconds"
            ),
        },
        {
            "id": "A3",
            "text": (
                "retry exactly once"
            ),
        },
        {
            "id": "A4",
            "text": (
                "never reuse the prior nonce"
            ),
        },
    ]

    admitted = [
        {
            "nucleus_quote": (
                "refresh the recovery lease"
            ),
        },
        {
            "nucleus_quote": (
                "wait 8 seconds"
            ),
        },
        {
            "nucleus_quote": (
                "retry exactly once"
            ),
        },
        {
            "nucleus_quote": (
                "retry exactly once "
                "and never reuse the prior nonce"
            ),
        },
    ]

    metrics = (
        module.canonical_nucleus_metrics(
            admitted_propositions=(
                admitted
            ),
            expected_units=expected,
        )
    )

    assert (
        metrics[
            "nucleus_recall"
        ]
        == 0.75
    )

    assert (
        metrics[
            "nucleus_precision"
        ]
        == 0.75
    )

    assert (
        0.0
        <= metrics[
            "nucleus_recall"
        ]
        <= 1.0
    )

    assert (
        0.0
        <= metrics[
            "nucleus_precision"
        ]
        <= 1.0
    )


def test_qualifier_metrics_measure_nucleus_qualified_relation():
    module = _seed011()

    expected_units = [
        {
            "id": "A1",
            "text": (
                "refresh the recovery lease"
            ),
        }
    ]

    expected_qualifiers = [
        {
            "atom_id": "A1",
            "type": "condition",
            "text": (
                "When ZX-11 occurs"
            ),
        }
    ]

    admitted = [
        {
            "nucleus_quote": (
                "refresh the recovery lease"
            ),
            "qualifiers": [
                {
                    "type": "condition",
                    "source_quote": (
                        "When ZX-11 occurs"
                    ),
                }
            ],
        }
    ]

    metrics = (
        module.qualifier_metrics(
            admitted_propositions=(
                admitted
            ),
            expected_units=(
                expected_units
            ),
            expected_qualifiers=(
                expected_qualifiers
            ),
        )
    )

    assert (
        metrics[
            "qualifier_recall"
        ]
        == 1.0
    )

    assert (
        metrics[
            "qualifier_precision"
        ]
        == 1.0
    )

    assert (
        metrics[
            "complete"
        ]
        is True
    )


def test_structured_challenges_are_injected():
    module = _seed011()
    tasks = _tasks011()

    family = (
        tasks
        .build_taskset()[
            "families"
        ][0]
    )

    proposal = {
        "propositions": []
    }

    shared, injected = (
        module
        .ensure_structured_compound_challenges(
            proposal=proposal,
            family=family,
            source_text=family[
                "raw_source"
            ],
        )
    )

    assert injected == 2

    nuclei = {
        proposition[
            "nucleus_quote"
        ]
        for proposition
        in shared[
            "propositions"
        ]
    }

    for challenge in family[
        "structured_compound_challenges"
    ]:
        assert (
            challenge[
                "text"
            ]
            in nuclei
        )


def test_011_has_twenty_fresh_families_and_five_styles():
    tasks = _tasks011()

    payload = (
        tasks.build_taskset()
    )

    families = payload[
        "families"
    ]

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

    assert set(
        family[
            "style"
        ]
        for family
        in families
    ) == {
        "numbered",
        "conditional_ordering",
        "conjunction",
        "negation_scope",
        "mixed_ordering",
    }


def test_011_canonical_nuclei_are_exact_source_substrings():
    tasks = _tasks011()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        source = family[
            "raw_source"
        ]

        assert len(
            family[
                "atomic_units"
            ]
        ) == 4

        for atom in family[
            "atomic_units"
        ]:
            assert (
                source.count(
                    atom[
                        "text"
                    ]
                )
                == 1
            )


def test_011_expected_qualifiers_are_exact_source_substrings():
    tasks = _tasks011()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        source = family[
            "raw_source"
        ]

        for qualifier in family[
            "expected_qualifiers"
        ]:
            assert (
                source.count(
                    qualifier[
                        "text"
                    ]
                )
                == 1
            )


def test_011_compound_challenges_cross_multiple_nuclei():
    module = _seed011()
    tasks = _tasks011()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        for challenge in family[
            "structured_compound_challenges"
        ]:

            assert (
                module.compound_span_covers_multiple_units(
                    span_text=(
                        challenge[
                            "text"
                        ]
                    ),
                    source_text=family[
                        "raw_source"
                    ],
                    expected_units=family[
                        "atomic_units"
                    ],
                )
                is True
            )


def test_transfer_requires_only_subset_of_knowledge():
    tasks = _tasks011()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        required = family[
            "transfer_required_atom_ids"
        ]

        assert len(
            required
        ) == 2

        assert set(
            required
        ).issubset(
            {
                "A1",
                "A2",
                "A3",
                "A4",
            }
        )
