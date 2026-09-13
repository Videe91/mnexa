import importlib
import inspect

import pytest

from experiments.make_tasks_008 import build_raw_source
from experiments.seed_growth_008 import AUTHORITATIVE_ROLE


def _seed010():
    try:
        return importlib.import_module(
            "experiments.seed_growth_010"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 010 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks010():
    try:
        return importlib.import_module(
            "experiments.make_tasks_010"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 010 task generator "
            f"does not exist yet: {exc}"
        )


def _source(
    authoritative_text: str,
):
    return build_raw_source(
        status=(
            "ZX-10 run status was FAIL."
        ),
        failed_decision=(
            "Restart every worker."
        ),
        authoritative_sentences=[
            authoritative_text
        ],
        operator_note=(
            "Operator suspects congestion."
        ),
        diagnostic_metadata=(
            "Observed latency was 199 ms."
        ),
    )


def _proposal(
    *texts,
):
    return {
        "atoms": [
            {
                "text": text,
                "source_quote": text,
            }
            for text in texts
        ]
    }


def test_autonomous_gate_does_not_accept_family_or_oracle_boundaries():
    module = _seed010()

    signature = inspect.signature(
        module.admit_autonomous_atoms
    )

    assert (
        "family"
        not in signature.parameters
    )

    assert (
        "atomic_units"
        not in signature.parameters
    )


def test_discovery_prompt_demands_exact_minimal_source_spans():
    module = _seed010()

    prompt = (
        module.build_autonomous_boundary_prompt(
            _source(
                "refresh the lease and wait 8 seconds; "
                "retry exactly once."
            )
        )
        .lower()
    )

    assert "minimal" in prompt
    assert "exact" in prompt
    assert "source" in prompt
    assert "authoritative" in prompt
    assert "do not paraphrase" in prompt
    assert "conjunction" in prompt
    assert "semicolon" in prompt


def test_autonomous_gate_accepts_non_overlapping_authoritative_atoms():
    module = _seed010()

    source = _source(
        "refresh the lease and wait 8 seconds; "
        "retry exactly once; preserve the request id."
    )

    proposal = _proposal(
        "refresh the lease",
        "wait 8 seconds",
        "retry exactly once",
        "preserve the request id",
    )

    result = (
        module.admit_autonomous_atoms(
            proposal=proposal,
            source_text=source,
        )
    )

    assert len(
        result["admitted"]
    ) == 4

    assert not result[
        "rejected"
    ]

    assert all(
        atom["source_role"]
        ==
        AUTHORITATIVE_ROLE

        for atom
        in result[
            "admitted"
        ]
    )


def test_autonomous_gate_rejects_invented_span():
    module = _seed010()

    source = _source(
        "refresh the lease and wait 8 seconds."
    )

    result = (
        module.admit_autonomous_atoms(
            proposal=_proposal(
                "restart the moon server"
            ),
            source_text=source,
        )
    )

    assert result[
        "admitted"
    ] == []

    assert any(
        rejection[
            "reason"
        ]
        ==
        "source_quote_not_unique"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_autonomous_gate_rejects_non_authoritative_role():
    module = _seed010()

    source = _source(
        "refresh the lease and wait 8 seconds."
    )

    result = (
        module.admit_autonomous_atoms(
            proposal=_proposal(
                "ZX-10 run status was FAIL."
            ),
            source_text=source,
        )
    )

    assert result[
        "admitted"
    ] == []

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


def test_minimal_first_admission_rejects_overlapping_compound():
    module = _seed010()

    source = _source(
        "refresh the lease and wait 8 seconds; "
        "retry exactly once."
    )

    result = (
        module.admit_autonomous_atoms(
            proposal=_proposal(
                "refresh the lease",
                "wait 8 seconds",
                (
                    "refresh the lease "
                    "and wait 8 seconds"
                ),
                "retry exactly once",
            ),
            source_text=source,
        )
    )

    admitted = {
        atom[
            "text"
        ]
        for atom
        in result[
            "admitted"
        ]
    }

    assert (
        "refresh the lease"
        in admitted
    )

    assert (
        "wait 8 seconds"
        in admitted
    )

    assert (
        "retry exactly once"
        in admitted
    )

    assert (
        "refresh the lease and wait 8 seconds"
        not in admitted
    )

    assert any(
        rejection[
            "reason"
        ]
        ==
        "overlaps_admitted_span"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_runtime_never_admits_overlapping_final_spans():
    module = _seed010()

    source = _source(
        "refresh the lease and wait 8 seconds; "
        "retry exactly once; preserve request id."
    )

    result = (
        module.admit_autonomous_atoms(
            proposal=_proposal(
                "refresh the lease",
                "wait 8 seconds",
                (
                    "refresh the lease "
                    "and wait 8 seconds"
                ),
                "retry exactly once",
                "preserve request id",
            ),
            source_text=source,
        )
    )

    assert (
        module.count_overlapping_pairs(
            result[
                "admitted"
            ]
        )
        == 0
    )


def test_source_ancestry_validation():
    module = _seed010()

    source = _source(
        "refresh the lease and wait 8 seconds."
    )

    result = (
        module.admit_autonomous_atoms(
            proposal=_proposal(
                "refresh the lease",
                "wait 8 seconds",
            ),
            source_text=source,
        )
    )

    assert all(
        module.source_ancestry_valid(
            atom=atom,
            source_text=source,
        )

        for atom
        in result[
            "admitted"
        ]
    )


def test_boundary_metrics_are_exact_and_bounded():
    module = _seed010()

    expected = [
        {
            "id": "A1",
            "text": "refresh the lease",
        },
        {
            "id": "A2",
            "text": "wait 8 seconds",
        },
        {
            "id": "A3",
            "text": "retry exactly once",
        },
        {
            "id": "A4",
            "text": "preserve request id",
        },
    ]

    admitted = [
        {
            "text": "refresh the lease"
        },
        {
            "text": "wait 8 seconds"
        },
        {
            "text": "retry exactly once"
        },
        {
            "text": (
                "retry exactly once; "
                "preserve request id"
            )
        },
    ]

    metrics = (
        module.canonical_boundary_metrics(
            admitted_atoms=admitted,
            expected_units=expected,
        )
    )

    assert (
        metrics[
            "canonical_recall"
        ]
        == 0.75
    )

    assert (
        metrics[
            "canonical_precision"
        ]
        == 0.75
    )

    assert (
        metrics[
            "exact_matches"
        ]
        == 3
    )

    assert (
        0.0
        <= metrics[
            "canonical_recall"
        ]
        <= 1.0
    )

    assert (
        0.0
        <= metrics[
            "canonical_precision"
        ]
        <= 1.0
    )


def test_overlap_challenges_are_injected_without_changing_source():
    module = _seed010()
    task_module = _tasks010()

    family = (
        task_module
        .build_taskset()[
            "families"
        ][0]
    )

    proposal = {
        "atoms": []
    }

    source_before = (
        family[
            "raw_source"
        ]
    )

    shared, injected = (
        module.ensure_overlap_challenges(
            proposal=proposal,
            family=family,
            source_text=source_before,
        )
    )

    assert injected == 2

    assert (
        family[
            "raw_source"
        ]
        ==
        source_before
    )

    texts = {
        atom[
            "text"
        ]
        for atom
        in shared[
            "atoms"
        ]
    }

    for challenge in family[
        "overlap_challenges"
    ]:
        assert (
            challenge[
                "text"
            ]
            in texts
        )


def test_oracle_upper_bound_reconstructs_all_canonical_units():
    module = _seed010()
    task_module = _tasks010()

    family = (
        task_module
        .build_taskset()[
            "families"
        ][0]
    )

    atoms = (
        module.oracle_atoms_from_family(
            source_text=family[
                "raw_source"
            ],
            family=family,
        )
    )

    assert len(
        atoms
    ) == 4

    metrics = (
        module.canonical_boundary_metrics(
            admitted_atoms=atoms,
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    assert (
        metrics[
            "canonical_recall"
        ]
        == 1.0
    )

    assert (
        metrics[
            "canonical_precision"
        ]
        == 1.0
    )


def test_010_has_twenty_fresh_unique_families():
    task_module = _tasks010()

    payload = (
        task_module.build_taskset()
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

    assert len(
        {
            family[
                "style"
            ]
            for family
            in families
        }
    ) >= 5


def test_010_canonical_units_are_unique_physical_source_spans():
    module = _seed010()
    task_module = _tasks010()

    payload = (
        task_module.build_taskset()
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

        for unit in family[
            "atomic_units"
        ]:

            assert (
                source.count(
                    unit[
                        "text"
                    ]
                )
                == 1
            )

        oracle = (
            module.oracle_atoms_from_family(
                source_text=source,
                family=family,
            )
        )

        assert len(
            oracle
        ) == 4

        assert all(
            atom[
                "source_role"
            ]
            ==
            AUTHORITATIVE_ROLE

            for atom
            in oracle
        )


def test_010_overlap_challenges_cross_multiple_canonical_units():
    module = _seed010()
    task_module = _tasks010()

    payload = (
        task_module.build_taskset()
    )

    for family in payload[
        "families"
    ]:

        oracle = (
            module.oracle_atoms_from_family(
                source_text=family[
                    "raw_source"
                ],
                family=family,
            )
        )

        for challenge in family[
            "overlap_challenges"
        ]:

            text = challenge[
                "text"
            ]

            source = family[
                "raw_source"
            ]

            assert (
                source.count(
                    text
                )
                == 1
            )

            start = (
                source.index(
                    text
                )
            )

            end = (
                start
                + len(
                    text
                )
            )

            overlaps = [
                atom

                for atom
                in oracle

                if (
                    max(
                        start,
                        atom[
                            "source_start"
                        ],
                    )
                    <
                    min(
                        end,
                        atom[
                            "source_end"
                        ],
                    )
                )
            ]

            assert len(
                overlaps
            ) >= 2


def test_transfer_requests_only_subset_of_atomic_knowledge():
    task_module = _tasks010()

    payload = (
        task_module.build_taskset()
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
