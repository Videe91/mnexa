import importlib
import inspect

import pytest

from experiments.make_tasks_008 import build_raw_source


def _seed012():
    try:
        return importlib.import_module(
            "experiments.seed_growth_012"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 012 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks012():
    try:
        return importlib.import_module(
            "experiments.make_tasks_012"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 012 task generator "
            f"does not exist yet: {exc}"
        )


def _source(
    authoritative_text: str,
):
    return build_raw_source(
        status="ZX-12 run status was FAIL.",
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
            "Observed diagnostic latency was 203 ms."
        ),
    )


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


def test_repair_prompt_has_no_oracle_family_argument():
    module = _seed012()

    signature = inspect.signature(
        module.build_structure_repair_prompt
    )

    assert (
        "family"
        not in signature.parameters
    )

    assert (
        "atomic_units"
        not in signature.parameters
    )


def test_repair_prompt_demands_split_and_qualifier_audit():
    module = _seed012()

    source = _source(
        "refresh the lease and wait 8 seconds; "
        "then retry exactly once."
    )

    initial_gate = {
        "admitted": [
            {
                "id": "P1",
                "source_quote": (
                    "refresh the lease and wait 8 seconds"
                ),
                "nucleus_quote": (
                    "refresh the lease and wait 8 seconds"
                ),
                "qualifiers": [],
                "source_start": 0,
                "source_end": 36,
                "nucleus_start": 0,
                "nucleus_end": 36,
            }
        ],
        "rejected": [],
    }

    prompt = (
        module.build_structure_repair_prompt(
            source_text=source,
            initial_gate=initial_gate,
        )
        .lower()
    )

    assert "split" in prompt
    assert "remove_qualifier" in prompt
    assert "reattach_qualifier" in prompt
    assert "keep" in prompt
    assert "compound" in prompt
    assert "exact source" in prompt
    assert "do not paraphrase" in prompt
    assert "qualifier" in prompt


def test_repair_parser_accepts_valid_operations():
    module = _seed012()

    raw = """
```json
{
  "operations": [
    {
      "op": "SPLIT",
      "target": "P1"
    },
    {
      "op": "REMOVE_QUALIFIER",
      "target": "P2"
    }
  ],
  "propositions": [
    {
      "source_quote": "refresh the lease",
      "nucleus_quote": "refresh the lease",
      "qualifiers": []
    }
  ]
}
```
""".strip()

    parsed = (
        module.parse_repair_proposal(
            raw
        )
    )

    assert len(
        parsed[
            "operations"
        ]
    ) == 2

    assert (
        parsed[
            "operations"
        ][0][
            "op"
        ]
        ==
        "SPLIT"
    )


def test_repair_parser_rejects_unknown_operation():
    module = _seed012()

    raw = """
```json
{
  "operations": [
    {
      "op": "MAGIC",
      "target": "P1"
    }
  ],
  "propositions": []
}
```
""".strip()

    with pytest.raises(
        ValueError
    ):
        module.parse_repair_proposal(
            raw
        )


def test_compound_first_pass_can_be_repaired_into_atomic_nuclei():
    module = _seed012()

    from experiments.seed_growth_011 import (
        admit_structured_propositions,
    )

    source = _source(
        "refresh the lease and wait 8 seconds."
    )

    repaired = {
        "propositions": [
            _prop(
                source_quote=(
                    "refresh the lease"
                ),
                nucleus_quote=(
                    "refresh the lease"
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
        ]
    }

    result = (
        admit_structured_propositions(
            proposal=repaired,
            source_text=source,
        )
    )

    nuclei = {
        proposition[
            "nucleus_quote"
        ]

        for proposition
        in result[
            "admitted"
        ]
    }

    assert nuclei == {
        "refresh the lease",
        "wait 8 seconds",
    }


def test_repair_can_remove_overattached_qualifier():
    module = _seed012()

    from experiments.seed_growth_011 import (
        admit_structured_propositions,
    )

    source = _source(
        "When ZX-12 occurs, refresh the lease. "
        "Wait 8 seconds."
    )

    repaired = {
        "propositions": [
            _prop(
                source_quote=(
                    "When ZX-12 occurs, refresh the lease"
                ),
                nucleus_quote=(
                    "refresh the lease"
                ),
                qualifiers=[
                    {
                        "type": "condition",
                        "source_quote": (
                            "When ZX-12 occurs"
                        ),
                    }
                ],
            ),
            _prop(
                source_quote=(
                    "Wait 8 seconds"
                ),
                nucleus_quote=(
                    "Wait 8 seconds"
                ),
                qualifiers=[],
            ),
        ]
    }

    result = (
        admit_structured_propositions(
            proposal=repaired,
            source_text=source,
        )
    )

    assert len(
        result[
            "admitted"
        ]
    ) == 2

    second = (
        result[
            "admitted"
        ][1]
    )

    assert (
        second[
            "qualifiers"
        ]
        == []
    )


def test_repair_cannot_invent_nucleus():
    module = _seed012()

    from experiments.seed_growth_011 import (
        admit_structured_propositions,
    )

    source = _source(
        "refresh the lease."
    )

    repaired = {
        "propositions": [
            _prop(
                source_quote=(
                    "refresh the lease"
                ),
                nucleus_quote=(
                    "restart the moon server"
                ),
            )
        ]
    }

    result = (
        admit_structured_propositions(
            proposal=repaired,
            source_text=source,
        )
    )

    assert (
        result[
            "admitted"
        ]
        == []
    )


def test_repair_cannot_invent_qualifier():
    module = _seed012()

    from experiments.seed_growth_011 import (
        admit_structured_propositions,
    )

    source = _source(
        "When ZX-12 occurs, refresh the lease."
    )

    repaired = {
        "propositions": [
            _prop(
                source_quote=(
                    "When ZX-12 occurs, refresh the lease"
                ),
                nucleus_quote=(
                    "refresh the lease"
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
        ]
    }

    result = (
        admit_structured_propositions(
            proposal=repaired,
            source_text=source,
        )
    )

    assert (
        result[
            "admitted"
        ]
        == []
    )


def test_challenge_survivor_count_detects_compound_nucleus():
    module = _seed012()

    family = {
        "structured_compound_challenges": [
            {
                "text": (
                    "refresh the lease and wait 8 seconds"
                )
            },
            {
                "text": (
                    "retry exactly once, but preserve request ID"
                )
            },
        ]
    }

    propositions = [
        {
            "nucleus_quote": (
                "refresh the lease and wait 8 seconds"
            )
        },
        {
            "nucleus_quote": (
                "retry exactly once"
            )
        },
        {
            "nucleus_quote": (
                "preserve request ID"
            )
        },
    ]

    assert (
        module.count_compound_challenge_survivors(
            propositions=propositions,
            family=family,
        )
        == 1
    )


def test_micro_qualifier_metrics_use_relation_totals():
    module = _seed012()

    metrics = (
        module.micro_qualifier_metrics(
            expected=28,
            admitted=48,
            matched=24,
        )
    )

    assert (
        metrics[
            "recall"
        ]
        ==
        pytest.approx(
            24 / 28
        )
    )

    assert (
        metrics[
            "precision"
        ]
        ==
        pytest.approx(
            24 / 48
        )
    )


def test_micro_qualifier_metrics_handle_zero_expected():
    module = _seed012()

    metrics = (
        module.micro_qualifier_metrics(
            expected=0,
            admitted=0,
            matched=0,
        )
    )

    assert (
        metrics[
            "recall"
        ]
        == 1.0
    )

    assert (
        metrics[
            "precision"
        ]
        == 1.0
    )


def test_repair_operations_are_counted():
    module = _seed012()

    payload = {
        "operations": [
            {
                "op": "SPLIT",
                "target": "P1",
            },
            {
                "op": "SPLIT",
                "target": "P2",
            },
            {
                "op": "KEEP",
                "target": "P3",
            },
            {
                "op": "REMOVE_QUALIFIER",
                "target": "P4",
            },
        ],
        "propositions": [],
    }

    counts = (
        module.count_repair_operations(
            payload
        )
    )

    assert (
        counts[
            "SPLIT"
        ]
        == 2
    )

    assert (
        counts[
            "KEEP"
        ]
        == 1
    )

    assert (
        counts[
            "REMOVE_QUALIFIER"
        ]
        == 1
    )

    assert (
        counts[
            "REATTACH_QUALIFIER"
        ]
        == 0
    )


def test_012_has_twenty_fresh_unique_families():
    tasks = _tasks012()

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


def test_012_uses_all_five_structural_styles():
    tasks = _tasks012()

    payload = (
        tasks.build_taskset()
    )

    assert set(
        family[
            "style"
        ]

        for family
        in payload[
            "families"
        ]
    ) == {
        "numbered",
        "conditional_ordering",
        "conjunction",
        "negation_scope",
        "mixed_ordering",
    }


def test_012_has_two_compound_challenges_per_family():
    tasks = _tasks012()

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

        for challenge in family[
            "structured_compound_challenges"
        ]:

            assert (
                family[
                    "raw_source"
                ].count(
                    challenge[
                        "text"
                    ]
                )
                == 1
            )


def test_012_expected_qualifier_annotations_are_grounded():
    tasks = _tasks012()

    payload = (
        tasks.build_taskset()
    )

    expected_total = 0

    for family in payload[
        "families"
    ]:

        source = (
            family[
                "raw_source"
            ]
        )

        for qualifier in family[
            "expected_qualifiers"
        ]:

            expected_total += 1

            assert (
                source.count(
                    qualifier[
                        "text"
                    ]
                )
                == 1
            )

    assert expected_total > 0


def test_012_transfer_requires_subset_not_entire_lesson():
    tasks = _tasks012()

    payload = (
        tasks.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        required = (
            family[
                "transfer_required_atom_ids"
            ]
        )

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
