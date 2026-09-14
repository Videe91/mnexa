import importlib
import inspect

import pytest


def _seed021():
    try:
        return importlib.import_module(
            "experiments.seed_growth_021"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 021 implementation does not exist yet: "
            f"{exc}"
        )


def _tasks021():
    try:
        return importlib.import_module(
            "experiments.make_tasks_021"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 021 task generator does not exist yet: "
            f"{exc}"
        )


class ZeroEmbedder:
    def embed(self, text):
        return [0.0, 0.0, 0.0]


def test_extracts_normalized_retrieval_handles():
    module = _seed021()

    compact = """
COMPACT SEMANTIC MEMORY

EVIDENCE:
[E1 role=authoritative_correction span=0:30] preserve the request token
[E2 role=authoritative_correction span=31:70] retry at most four times

REFERENCES:
[P1] HANDLE="preserve the request token" -> E1
[P2] HANDLE="retry" -> E2
  META scope="at most four times"
""".strip()

    result = (
        module.retrieval_index_from_compact_memory(
            compact_memory=compact,
            entities=[
                "system:Alpha",
                "cluster:retry-policy",
            ],
        )
    )

    assert 'HANDLE="preserve the request token"' in result
    assert 'HANDLE="retry"' in result
    assert 'META scope="at most four times"' in result


def test_unresolved_support_remains_searchable_without_inventing_claim():
    module = _seed021()

    compact = """
COMPACT SEMANTIC MEMORY

EVIDENCE:
[E1 role=authoritative_correction span=0:55] never reuse the previous handshake nonce

REFERENCES:
[G1] UNRESOLVED -> E1
""".strip()

    result = (
        module.retrieval_index_from_compact_memory(
            compact_memory=compact,
            entities=[
                "cluster:channel-session",
            ],
        )
    )

    assert (
        "UNRESOLVED_GROUNDED_SUPPORT="
        '"never reuse the previous handshake nonce"'
        in result
    )

    assert "UNRESOLVED -> E1" in result


def test_retrieval_index_does_not_copy_entire_compact_memory():
    module = _seed021()

    compact = """
COMPACT SEMANTIC MEMORY

Exact EVIDENCE text is authoritative.
This boilerplate should not become retrieval material.

EVIDENCE:
[E1 role=authoritative_correction span=0:20] retry at most twice

REFERENCES:
[P1] HANDLE="retry" -> E1
  META scope="at most twice"
""".strip()

    result = (
        module.retrieval_index_from_compact_memory(
            compact_memory=compact,
            entities=[
                "cluster:retry-policy",
            ],
        )
    )

    assert (
        "This boilerplate should not become retrieval material."
        not in result
    )

    assert 'HANDLE="retry"' in result


def test_address_metadata_is_kept_in_retrieval_index():
    module = _seed021()

    compact = """
COMPACT SEMANTIC MEMORY

EVIDENCE:
[E1 role=authoritative_correction span=0:10] retry once

REFERENCES:
[P1] HANDLE="retry once" -> E1
""".strip()

    result = (
        module.retrieval_index_from_compact_memory(
            compact_memory=compact,
            entities=[
                "system:Alpha",
                "code:A-1",
                "domain:operations",
                "cluster:retry-policy",
            ],
        )
    )

    assert "system:Alpha" in result
    assert "code:A-1" in result
    assert "domain:operations" in result
    assert "cluster:retry-policy" in result


def test_rendered_memory_extraction_finds_compact_payload():
    module = _seed021()

    bundle = {
        "other": "not this",
        "nested": {
            "rendered": (
                "COMPACT SEMANTIC MEMORY\n"
                "EVIDENCE:\n"
                "[E1 role=x] retry once"
            )
        },
    }

    result = (
        module.rendered_memory_from_bundle(
            bundle
        )
    )

    assert result.startswith(
        "COMPACT SEMANTIC MEMORY"
    )


def test_ranker_has_no_oracle_parameters():
    module = _seed021()

    signature = inspect.signature(
        module.rank_candidate_ids
    )

    prohibited = {
        "target_family_id",
        "semantic_clause",
        "semantic_grader",
        "correct_answer",
        "atomic_units",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_ranker_returns_top_k_only():
    module = _seed021()

    documents = {
        "a": "retry maximum four",
        "b": "retry minimum two",
        "c": "never retry timeout",
        "d": "retry only after lease",
        "e": "retry exactly three",
    }

    entities = {
        family_id: [
            "cluster:retry-policy",
            "domain:operations",
        ]
        for family_id in documents
    }

    result = (
        module.rank_candidate_ids(
            query_text=(
                "maximum retry rule "
                "cluster:retry-policy"
            ),
            query_entities=[
                "cluster:retry-policy",
                "domain:operations",
            ],
            candidate_family_ids=list(
                documents
            ),
            documents=documents,
            entities_by_family=entities,
            embedder=ZeroEmbedder(),
            top_k=3,
        )
    )

    assert len(
        result["selected_family_ids"]
    ) == 3


def test_lexical_signal_can_break_semantic_and_entity_ties():
    module = _seed021()

    documents = {
        "maximum": (
            "HANDLE retry "
            "META at most maximum four"
        ),
        "minimum": (
            "HANDLE retry "
            "META at least minimum four"
        ),
        "exact": (
            "HANDLE retry "
            "META exactly four"
        ),
    }

    entities = {
        family_id: [
            "cluster:retry-policy",
        ]
        for family_id in documents
    }

    result = (
        module.rank_candidate_ids(
            query_text=(
                "maximum retry count"
            ),
            query_entities=[
                "cluster:retry-policy",
            ],
            candidate_family_ids=[
                "maximum",
                "minimum",
                "exact",
            ],
            documents=documents,
            entities_by_family=entities,
            embedder=ZeroEmbedder(),
            top_k=1,
        )
    )

    assert (
        result[
            "selected_family_ids"
        ]
        ==
        ["maximum"]
    )


def test_rrf_is_deterministic():
    module = _seed021()

    documents = {
        "a": "alpha retry",
        "b": "beta retry",
        "c": "gamma retry",
    }

    entities = {
        key: ["cluster:retry-policy"]
        for key in documents
    }

    kwargs = {
        "query_text": "beta retry",
        "query_entities": [
            "cluster:retry-policy"
        ],
        "candidate_family_ids": [
            "a",
            "b",
            "c",
        ],
        "documents": documents,
        "entities_by_family": entities,
        "embedder": ZeroEmbedder(),
        "top_k": 2,
    }

    first = (
        module.rank_candidate_ids(
            **kwargs
        )
    )

    second = (
        module.rank_candidate_ids(
            **kwargs
        )
    )

    assert (
        first["selected_family_ids"]
        ==
        second["selected_family_ids"]
    )

    assert (
        first["rrf_scores"]
        ==
        second["rrf_scores"]
    )


def test_equal_selected_sets_reuse_evaluation():
    module = _seed021()

    assert (
        module.requires_second_evaluation(
            full_selected_ids=[
                "a",
                "b",
                "c",
            ],
            handle_selected_ids=[
                "c",
                "a",
                "b",
            ],
            canonical_family_ids=[
                "a",
                "b",
                "c",
                "d",
            ],
        )
        is False
    )


def test_different_selected_sets_require_second_evaluation():
    module = _seed021()

    assert (
        module.requires_second_evaluation(
            full_selected_ids=[
                "a",
                "b",
                "c",
            ],
            handle_selected_ids=[
                "a",
                "b",
                "d",
            ],
            canonical_family_ids=[
                "a",
                "b",
                "c",
                "d",
            ],
        )
        is True
    )


def test_selection_metrics_target_present():
    module = _seed021()

    metrics = (
        module.posthoc_selection_metrics(
            target_family_id="b",
            selected_family_ids=[
                "a",
                "b",
                "c",
            ],
        )
    )

    assert metrics["target_selected"] is True
    assert metrics["selection_recall"] == 1.0
    assert metrics["selection_precision"] == pytest.approx(
        1 / 3
    )


def test_selection_metrics_target_absent():
    module = _seed021()

    metrics = (
        module.posthoc_selection_metrics(
            target_family_id="d",
            selected_family_ids=[
                "a",
                "b",
                "c",
            ],
        )
    )

    assert metrics["target_selected"] is False
    assert metrics["selection_recall"] == 0.0
    assert metrics["selection_precision"] == 0.0


def test_021_has_twenty_unique_families():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    families = payload["families"]

    assert len(families) == 20

    assert (
        len(
            {
                family["id"]
                for family in families
            }
        )
        == 20
    )


def test_021_has_four_clusters_five_each():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload["families"]:

        cluster = (
            family[
                "interference_cluster"
            ]
        )

        counts[cluster] = (
            counts.get(
                cluster,
                0,
            )
            + 1
        )

    assert counts == {
        "retry-policy": 5,
        "lane-routing": 5,
        "channel-session": 5,
        "storage-finalization": 5,
    }


def test_all_021_queries_are_context_only():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            family["degradation_mode"]
            == "context_only"
        )

        entities = (
            family[
                "query_entities"
            ]
        )

        assert not any(
            entity.startswith(
                "system:"
            )
            for entity in entities
        )

        assert not any(
            entity.startswith(
                "code:"
            )
            for entity in entities
        )

        assert any(
            entity.startswith(
                "cluster:"
            )
            for entity in entities
        )


def test_conjunctive_routing_geometry_is_five_candidates():
    tasks = _tasks021()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    payload = tasks.build_taskset()

    families = payload["families"]

    for family in families:

        selection = (
            select_conjunctive_candidates(
                query_entities=(
                    family[
                        "query_entities"
                    ]
                ),
                families=families,
            )
        )

        assert (
            selection[
                "candidate_count"
            ]
            == 5
        )

        assert (
            family["id"]
            in
            selection[
                "candidate_family_ids"
            ]
        )


def test_all_semantic_clauses_are_unique():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    clauses = [
        family[
            "semantic_clause"
        ]
        for family
        in payload["families"]
    ]

    assert (
        len(clauses)
        ==
        len(set(clauses))
    )


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    for family in payload["families"]:

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


def test_every_family_has_four_atomic_units():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            len(
                family[
                    "atomic_units"
                ]
            )
            == 4
        )


def test_taskset_freezes_top_k_and_rrf_constant():
    tasks = _tasks021()

    payload = tasks.build_taskset()

    assert (
        payload[
            "retrieval_top_k"
        ]
        == 3
    )

    assert (
        payload[
            "rrf_k"
        ]
        == 60
    )
