from experiments.make_tasks_009 import build_taskset

from experiments.seed_growth_008 import (
    admit_role_gated_atoms,
)

from experiments.seed_growth_009 import (
    admit_atomic_role_atoms,
    atomic_recall_precision,
    ensure_atomicity_challenges,
    locate_atomic_units,
    span_atomicity_classification,
)


def _family():
    return build_taskset()["families"][0]


def _proposal(*texts):
    return {
        "atoms": [
            {
                "text": text,
                "source_quote": text,
            }
            for text in texts
        ]
    }


def test_exact_atomic_span_is_classified_as_atomic():
    family = _family()

    units = locate_atomic_units(
        source_text=family["raw_source"],
        family=family,
    )

    unit = units[0]

    result = span_atomicity_classification(
        start=unit["source_start"],
        end=unit["source_end"],
        units=units,
    )

    assert result == "exact_atomic_unit"


def test_compound_span_crosses_atomic_boundaries():
    family = _family()

    units = locate_atomic_units(
        source_text=family["raw_source"],
        family=family,
    )

    challenge = family[
        "atomicity_challenges"
    ][0]

    start = family[
        "raw_source"
    ].index(
        challenge["text"]
    )

    end = (
        start
        + len(
            challenge["text"]
        )
    )

    result = span_atomicity_classification(
        start=start,
        end=end,
        units=units,
    )

    assert result == "crosses_atomic_boundaries"


def test_current_role_gate_accepts_authoritative_compound():
    family = _family()

    challenge = family[
        "atomicity_challenges"
    ][0]

    proposal = _proposal(
        challenge["text"]
    )

    result = admit_role_gated_atoms(
        proposal=proposal,
        source_text=family[
            "raw_source"
        ],
    )

    assert len(
        result["admitted"]
    ) == 1

    assert (
        result[
            "admitted"
        ][0][
            "source_role"
        ]
        ==
        "authoritative_correction"
    )


def test_atomicity_gate_rejects_authoritative_compound():
    family = _family()

    challenge = family[
        "atomicity_challenges"
    ][0]

    result = admit_atomic_role_atoms(
        proposal=_proposal(
            challenge["text"]
        ),
        source_text=family[
            "raw_source"
        ],
        family=family,
    )

    assert result[
        "admitted"
    ] == []

    assert any(
        rejection[
            "reason"
        ]
        ==
        "crosses_atomic_boundaries"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_atomicity_gate_accepts_all_exact_units():
    family = _family()

    texts = [
        atom["text"]
        for atom
        in family[
            "atomic_units"
        ]
    ]

    result = admit_atomic_role_atoms(
        proposal=_proposal(
            *texts
        ),
        source_text=family[
            "raw_source"
        ],
        family=family,
    )

    assert len(
        result["admitted"]
    ) == 4

    assert result[
        "rejected"
    ] == []


def test_atomicity_gate_rejects_partial_atomic_unit():
    family = _family()

    unit_text = family[
        "atomic_units"
    ][0]["text"]

    # Remove the final word while keeping
    # a real exact substring of the source.
    partial = (
        unit_text
        .rstrip(".")
        .rsplit(
            " ",
            1,
        )[0]
    )

    assert (
        partial
        in family[
            "raw_source"
        ]
    )

    result = admit_atomic_role_atoms(
        proposal=_proposal(
            partial
        ),
        source_text=family[
            "raw_source"
        ],
        family=family,
    )

    assert result[
        "admitted"
    ] == []

    assert any(
        rejection[
            "reason"
        ]
        ==
        "partial_atomic_unit"

        for rejection
        in result[
            "rejected"
        ]
    )


def test_atomic_recall_precision_is_bounded():
    family = _family()

    proposal = _proposal(
        *[
            atom["text"]
            for atom
            in family[
                "atomic_units"
            ]
        ],
        *[
            challenge[
                "text"
            ]
            for challenge
            in family[
                "atomicity_challenges"
            ]
        ],
    )

    current = admit_role_gated_atoms(
        proposal=proposal,
        source_text=family[
            "raw_source"
        ],
    )

    atomic = admit_atomic_role_atoms(
        proposal=proposal,
        source_text=family[
            "raw_source"
        ],
        family=family,
    )

    current_metrics = (
        atomic_recall_precision(
            admitted_atoms=current[
                "admitted"
            ],
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    atomic_metrics = (
        atomic_recall_precision(
            admitted_atoms=atomic[
                "admitted"
            ],
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    assert (
        current_metrics[
            "atomic_recall"
        ]
        == 1.0
    )

    assert (
        current_metrics[
            "atomic_precision"
        ]
        < 1.0
    )

    assert (
        atomic_metrics[
            "atomic_recall"
        ]
        == 1.0
    )

    assert (
        atomic_metrics[
            "atomic_precision"
        ]
        == 1.0
    )

    for metrics in (
        current_metrics,
        atomic_metrics,
    ):
        assert (
            0.0
            <= metrics[
                "atomic_recall"
            ]
            <= 1.0
        )

        assert (
            0.0
            <= metrics[
                "atomic_precision"
            ]
            <= 1.0
        )


def test_atomicity_challenges_are_shared_between_conditions():
    family = _family()

    proposal = {
        "atoms": []
    }

    shared, injected = (
        ensure_atomicity_challenges(
            proposal=proposal,
            family=family,
            source_text=family[
                "raw_source"
            ],
        )
    )

    assert injected == 2

    texts = {
        atom["text"]
        for atom
        in shared[
            "atoms"
        ]
    }

    for challenge in family[
        "atomicity_challenges"
    ]:
        assert (
            challenge[
                "text"
            ]
            in texts
        )


def test_009_has_twenty_fresh_unique_families():
    payload = build_taskset()

    families = payload[
        "families"
    ]

    assert len(
        families
    ) == 20

    assert len(
        {
            family["id"]
            for family
            in families
        }
    ) == 20

    for family in families:
        assert (
            family[
                "experience"
            ]["prompt"]
            !=
            family[
                "transfer"
            ]["prompt"]
        )

        assert len(
            family[
                "atomic_units"
            ]
        ) == 4

        assert len(
            family[
                "atomicity_challenges"
            ]
        ) == 2

        assert family[
            "transfer_required_atom_ids"
        ]


def test_009_fixture_atomic_boundaries_are_valid():
    payload = build_taskset()

    for family in payload[
        "families"
    ]:

        units = locate_atomic_units(
            source_text=family[
                "raw_source"
            ],
            family=family,
        )

        assert len(
            units
        ) == 4

        for unit in units:
            assert (
                unit[
                    "source_role"
                ]
                ==
                "authoritative_correction"
            )

        for challenge in family[
            "atomicity_challenges"
        ]:
            text = challenge[
                "text"
            ]

            assert (
                family[
                    "raw_source"
                ].count(
                    text
                )
                == 1
            )

            start = (
                family[
                    "raw_source"
                ].index(
                    text
                )
            )

            end = (
                start
                + len(text)
            )

            assert (
                span_atomicity_classification(
                    start=start,
                    end=end,
                    units=units,
                )
                ==
                "crosses_atomic_boundaries"
            )
