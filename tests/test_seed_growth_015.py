import importlib
import inspect

import pytest


def _seed015():
    try:
        return importlib.import_module(
            "experiments.seed_growth_015"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 015 implementation does not exist yet: "
            f"{exc}"
        )


def _tasks015():
    try:
        return importlib.import_module(
            "experiments.make_tasks_015"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 015 task generator does not exist yet: "
            f"{exc}"
        )


def _structured(
    *,
    pid,
    source_quote,
    source_start,
    nucleus_quote,
    nucleus_start,
):
    source_end = (
        source_start
        +
        len(source_quote)
    )

    nucleus_end = (
        nucleus_start
        +
        len(nucleus_quote)
    )

    return {
        "id": pid,
        "source_quote": source_quote,
        "source_start": source_start,
        "source_end": source_end,
        "source_role": "authoritative_correction",
        "source_sha256": "source-sha",
        "support_span_sha256": (
            f"support-{source_start}-{source_end}"
        ),
        "nucleus_quote": nucleus_quote,
        "nucleus_start": nucleus_start,
        "nucleus_end": nucleus_end,
        "nucleus_sha256": (
            f"nucleus-{nucleus_start}-{nucleus_end}"
        ),
        "qualifiers": [],
    }


def _fallback(
    *,
    gid,
    source_quote,
    source_start,
):
    return {
        "id": gid,
        "source_quote": source_quote,
        "source_start": source_start,
        "source_end": (
            source_start
            +
            len(source_quote)
        ),
        "source_role": "authoritative_correction",
        "source_sha256": "source-sha",
        "support_span_sha256": (
            f"fallback-{source_start}"
        ),
        "structure_status": "unresolved",
    }


def test_compact_renderer_has_no_oracle_arguments():
    module = _seed015()

    signature = inspect.signature(
        module.render_compact_semantic_memory
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


def test_identical_support_is_emitted_once():
    module = _seed015()

    support = (
        "refresh the lease; "
        "wait 12 seconds; "
        "never reuse the nonce"
    )

    structured = [
        _structured(
            pid="P1",
            source_quote=support,
            source_start=100,
            nucleus_quote="refresh the lease",
            nucleus_start=100,
        ),
        _structured(
            pid="P2",
            source_quote=support,
            source_start=100,
            nucleus_quote="wait 12 seconds",
            nucleus_start=119,
        ),
        _structured(
            pid="P3",
            source_quote=support,
            source_start=100,
            nucleus_quote="never reuse the nonce",
            nucleus_start=136,
        ),
    ]

    rendered = (
        module.render_compact_semantic_memory(
            structured=structured,
            fallback=[],
        )
    )

    assert (
        rendered.count(
            support
        )
        == 1
    )


def test_multiple_handles_reference_one_evidence_record():
    module = _seed015()

    support = (
        "refresh the lease; "
        "never reuse the nonce"
    )

    structured = [
        _structured(
            pid="P1",
            source_quote=support,
            source_start=50,
            nucleus_quote="refresh the lease",
            nucleus_start=50,
        ),
        _structured(
            pid="P2",
            source_quote=support,
            source_start=50,
            nucleus_quote="never reuse the nonce",
            nucleus_start=69,
        ),
    ]

    payload = (
        module.build_compact_memory(
            structured=structured,
            fallback=[],
        )
    )

    assert len(
        payload[
            "evidence"
        ]
    ) == 1

    assert (
        payload[
            "references"
        ][0][
            "evidence_id"
        ]
        ==
        "E1"
    )

    assert (
        payload[
            "references"
        ][1][
            "evidence_id"
        ]
        ==
        "E1"
    )


def test_distinct_support_spans_get_distinct_evidence_ids():
    module = _seed015()

    structured = [
        _structured(
            pid="P1",
            source_quote="refresh the lease",
            source_start=10,
            nucleus_quote="refresh the lease",
            nucleus_start=10,
        ),
        _structured(
            pid="P2",
            source_quote="never reuse the nonce",
            source_start=40,
            nucleus_quote="never reuse the nonce",
            nucleus_start=40,
        ),
    ]

    payload = (
        module.build_compact_memory(
            structured=structured,
            fallback=[],
        )
    )

    assert [
        item[
            "id"
        ]
        for item
        in payload[
            "evidence"
        ]
    ] == [
        "E1",
        "E2",
    ]


def test_fallback_support_is_indexed_as_evidence():
    module = _seed015()

    fallback = [
        _fallback(
            gid="G1",
            source_quote=(
                "do not acknowledge the original event"
            ),
            source_start=200,
        )
    ]

    payload = (
        module.build_compact_memory(
            structured=[],
            fallback=fallback,
        )
    )

    assert len(
        payload[
            "evidence"
        ]
    ) == 1

    assert (
        payload[
            "evidence"
        ][0][
            "text"
        ]
        ==
        "do not acknowledge the original event"
    )

    assert (
        payload[
            "references"
        ][0][
            "reference_type"
        ]
        ==
        "unresolved"
    )


def test_compact_projection_emits_unique_support_claims():
    module = _seed015()

    support = (
        "move the job only to the cobalt lane"
    )

    structured = [
        _structured(
            pid="P1",
            source_quote=support,
            source_start=100,
            nucleus_quote="move the job",
            nucleus_start=100,
        ),
        _structured(
            pid="P2",
            source_quote=support,
            source_start=100,
            nucleus_quote="cobalt lane",
            nucleus_start=125,
        ),
    ]

    projected = (
        module.compact_semantic_projection(
            structured=structured,
            fallback=[],
        )
    )

    assert len(
        projected
    ) == 1

    assert (
        projected[
            0
        ][
            "text"
        ]
        ==
        support
    )


def test_compact_projection_preserves_exact_offsets():
    module = _seed015()

    proposition = (
        _structured(
            pid="P1",
            source_quote=(
                "retry at most twice"
            ),
            source_start=77,
            nucleus_quote=(
                "retry at most twice"
            ),
            nucleus_start=77,
        )
    )

    projected = (
        module.compact_semantic_projection(
            structured=[
                proposition
            ],
            fallback=[],
        )
    )

    assert (
        projected[
            0
        ][
            "source_start"
        ]
        ==
        77
    )

    assert (
        projected[
            0
        ][
            "source_end"
        ]
        ==
        96
    )


def test_references_all_resolve_to_existing_evidence():
    module = _seed015()

    structured = [
        _structured(
            pid="P1",
            source_quote="refresh the lease",
            source_start=10,
            nucleus_quote="refresh the lease",
            nucleus_start=10,
        ),
    ]

    fallback = [
        _fallback(
            gid="G1",
            source_quote="never reuse the nonce",
            source_start=50,
        )
    ]

    payload = (
        module.build_compact_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    evidence_ids = {
        item[
            "id"
        ]
        for item
        in payload[
            "evidence"
        ]
    }

    assert all(
        reference[
            "evidence_id"
        ]
        in evidence_ids

        for reference
        in payload[
            "references"
        ]
    )


def test_compact_renderer_marks_handle_as_non_authoritative():
    module = _seed015()

    structured = [
        _structured(
            pid="P1",
            source_quote=(
                "never reuse the prior nonce"
            ),
            source_start=10,
            nucleus_quote=(
                "reuse the prior nonce"
            ),
            nucleus_start=16,
        )
    ]

    rendered = (
        module.render_compact_semantic_memory(
            structured=structured,
            fallback=[],
        )
    )

    assert (
        "retrieval handles are not standalone claims"
        in rendered.lower()
    )


def test_compact_renderer_preserves_exact_semantic_clause():
    module = _seed015()

    clause = (
        "never reuse the prior nonce"
    )

    structured = [
        _structured(
            pid="P1",
            source_quote=clause,
            source_start=10,
            nucleus_quote=(
                "reuse the prior nonce"
            ),
            nucleus_start=16,
        )
    ]

    rendered = (
        module.render_compact_semantic_memory(
            structured=structured,
            fallback=[],
        )
    )

    assert (
        clause
        in rendered
    )


def test_compaction_stats_detect_duplicate_support_removal():
    module = _seed015()

    support = (
        "refresh the lease; wait 12 seconds"
    )

    structured = [
        _structured(
            pid="P1",
            source_quote=support,
            source_start=10,
            nucleus_quote="refresh the lease",
            nucleus_start=10,
        ),
        _structured(
            pid="P2",
            source_quote=support,
            source_start=10,
            nucleus_quote="wait 12 seconds",
            nucleus_start=29,
        ),
    ]

    stats = (
        module.compaction_stats(
            structured=structured,
            fallback=[],
        )
    )

    assert (
        stats[
            "input_support_occurrences"
        ]
        == 2
    )

    assert (
        stats[
            "unique_support_records"
        ]
        == 1
    )

    assert (
        stats[
            "duplicate_support_occurrences_removed"
        ]
        == 1
    )


def test_compact_memory_is_smaller_on_duplicate_fixture():
    module = _seed015()

    support = (
        "refresh the recovery lease; "
        "wait 14 seconds; "
        "retry exactly once; "
        "never reuse the old nonce"
    )

    structured = [
        _structured(
            pid="P1",
            source_quote=support,
            source_start=100,
            nucleus_quote="refresh the recovery lease",
            nucleus_start=100,
        ),
        _structured(
            pid="P2",
            source_quote=support,
            source_start=100,
            nucleus_quote="wait 14 seconds",
            nucleus_start=128,
        ),
        _structured(
            pid="P3",
            source_quote=support,
            source_start=100,
            nucleus_quote="retry exactly once",
            nucleus_start=145,
        ),
        _structured(
            pid="P4",
            source_quote=support,
            source_start=100,
            nucleus_quote="never reuse the old nonce",
            nucleus_start=165,
        ),
    ]

    verbose = (
        module.render_verbose_reference_fixture(
            structured=structured,
        )
    )

    compact = (
        module.render_compact_semantic_memory(
            structured=structured,
            fallback=[],
        )
    )

    assert (
        len(
            compact.split()
        )
        <
        len(
            verbose.split()
        )
    )


def test_015_has_twenty_fresh_unique_families():
    tasks = _tasks015()

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


def test_015_covers_four_semantic_dimensions():
    tasks = _tasks015()

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


def test_015_covers_operator_classes():
    tasks = _tasks015()

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


def test_each_family_retains_014_fallback_attacks():
    tasks = _tasks015()

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


def test_each_family_has_four_canonical_atoms():
    tasks = _tasks015()

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


def test_semantic_clause_is_exact_source_text():
    tasks = _tasks015()

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
