import importlib
import inspect

import pytest


def _seed026():
    try:
        return importlib.import_module(
            "experiments.seed_growth_026"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 026 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks026():
    try:
        return importlib.import_module(
            "experiments.make_tasks_026"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 026 task generator "
            f"does not exist yet: {exc}"
        )


class KeywordEmbedder:
    name = "keyword-test-embedder"

    def embed(
        self,
        text,
    ):
        text = text.lower()

        if (
            "minimum retry"
            in text
            or
            "at least seven"
            in text
        ):
            return [
                1.0,
                0.0,
                0.0,
            ]

        if (
            "exactly fourteen"
            in text
        ):
            return [
                0.0,
                1.0,
                0.0,
            ]

        return [
            0.0,
            0.0,
            1.0,
        ]

    def encode(
        self,
        text,
    ):
        return self.embed(
            text
        )


def test_parser_splits_handles_into_independent_units():
    module = _seed026()

    index = """
ADDRESS system:QuartzWorks
ADDRESS domain:operations

[P1] HANDLE="refresh the recovery marker" -> E1
[P2] HANDLE="retry at least seven times" -> E2
  META cardinality="at least seven times"
[P3] HANDLE="preserve the request fingerprint" -> E3
"""

    units = (
        module.proposition_units_from_retrieval_index(
            index
        )
    )

    assert units == [
        "HANDLE: refresh the recovery marker",
        (
            "HANDLE: retry at least seven times\n"
            'META cardinality="at least seven times"'
        ),
        "HANDLE: preserve the request fingerprint",
    ]


def test_parser_does_not_turn_address_metadata_into_proposition():
    module = _seed026()

    index = """
ADDRESS system:QuartzWorks
ADDRESS code:QW-901
ADDRESS domain:operations
ADDRESS cluster:retry-policy
[P1] HANDLE="retry exactly fourteen times" -> E1
"""

    units = (
        module.proposition_units_from_retrieval_index(
            index
        )
    )

    assert units == [
        "HANDLE: retry exactly fourteen times"
    ]

    assert not any(
        "QuartzWorks"
        in unit
        for unit
        in units
    )


def test_unresolved_grounded_support_remains_retrievable_unit():
    module = _seed026()

    index = """
[G1] UNRESOLVED_GROUNDED_SUPPORT="do not retry a rejected request"
"""

    units = (
        module.proposition_units_from_retrieval_index(
            index
        )
    )

    assert units == [
        (
            "UNRESOLVED_GROUNDED_SUPPORT: "
            "do not retry a rejected request"
        )
    ]


def test_meta_attaches_only_to_preceding_handle():
    module = _seed026()

    index = """
[P1] HANDLE="retry" -> E1
  META ordering="only after renewing the lease"
[P2] HANDLE="preserve the fingerprint" -> E2
"""

    units = (
        module.proposition_units_from_retrieval_index(
            index
        )
    )

    assert units[0] == (
        "HANDLE: retry\n"
        'META ordering="only after renewing the lease"'
    )

    assert units[1] == (
        "HANDLE: preserve the fingerprint"
    )


def test_parser_rejects_document_without_proposition_units():
    module = _seed026()

    with pytest.raises(
        ValueError,
        match="No proposition-local retrieval units",
    ):
        module.proposition_units_from_retrieval_index(
            """
            ADDRESS domain:operations
            ADDRESS cluster:retry-policy
            """
        )


def test_local_semantic_scoring_selects_best_proposition():
    module = _seed026()

    result = (
        module.proposition_local_channel_scores(
            query_text=(
                "State the minimum retry rule."
            ),

            query_entities=[
                "domain:operations",
                "cluster:retry-policy",
            ],

            candidate_family_ids=[
                "exact",
                "minimum",
            ],

            proposition_units_by_family={
                "exact": [
                    (
                        "HANDLE: retry exactly "
                        "fourteen times"
                    ),
                    (
                        "HANDLE: preserve the "
                        "request fingerprint"
                    ),
                ],

                "minimum": [
                    (
                        "HANDLE: retry at least "
                        "seven times"
                    ),
                    (
                        "HANDLE: preserve the "
                        "request fingerprint"
                    ),
                ],
            },

            entities_by_family={
                "exact": [
                    "domain:operations",
                    "cluster:retry-policy",
                ],

                "minimum": [
                    "domain:operations",
                    "cluster:retry-policy",
                ],
            },

            embedder=KeywordEmbedder(),
        )
    )

    semantic = (
        result[
            "channel_scores"
        ][
            "semantic"
        ]
    )

    assert (
        semantic["minimum"]
        >
        semantic["exact"]
    )

    assert (
        "at least seven"
        in
        result[
            "best_units"
        ][
            "semantic"
        ][
            "minimum"
        ]
    )


def test_local_lexical_scoring_uses_best_matching_unit():
    module = _seed026()

    result = (
        module.proposition_local_channel_scores(
            query_text=(
                "retry at least seven times"
            ),

            query_entities=[
                "domain:operations",
                "cluster:retry-policy",
            ],

            candidate_family_ids=[
                "exact",
                "minimum",
            ],

            proposition_units_by_family={
                "exact": [
                    (
                        "HANDLE: retry exactly "
                        "fourteen times"
                    ),
                    (
                        "HANDLE: preserve fingerprint"
                    ),
                ],

                "minimum": [
                    (
                        "HANDLE: retry at least "
                        "seven times"
                    ),
                    (
                        "HANDLE: preserve fingerprint"
                    ),
                ],
            },

            entities_by_family={
                "exact": [
                    "domain:operations",
                    "cluster:retry-policy",
                ],

                "minimum": [
                    "domain:operations",
                    "cluster:retry-policy",
                ],
            },

            embedder=KeywordEmbedder(),
        )
    )

    lexical = (
        result[
            "channel_scores"
        ][
            "lexical"
        ]
    )

    assert (
        lexical["minimum"]
        >
        lexical["exact"]
    )


def test_entity_channel_is_unchanged_by_local_scoring():
    module = _seed026()

    result = (
        module.proposition_local_channel_scores(
            query_text="retry",

            query_entities=[
                "domain:operations",
                "cluster:retry-policy",
            ],

            candidate_family_ids=[
                "a",
                "b",
            ],

            proposition_units_by_family={
                "a": [
                    "HANDLE: retry exactly fourteen times"
                ],
                "b": [
                    "HANDLE: retry at least seven times"
                ],
            },

            entities_by_family={
                "a": [
                    "system:A",
                    "domain:operations",
                    "cluster:retry-policy",
                ],

                "b": [
                    "system:B",
                    "domain:operations",
                    "cluster:retry-policy",
                ],
            },

            embedder=KeywordEmbedder(),
        )
    )

    entity = (
        result[
            "channel_scores"
        ][
            "entity"
        ]
    )

    assert entity == {
        "a": 2.0,
        "b": 2.0,
    }


def test_local_scoring_counts_each_proposition_comparison():
    module = _seed026()

    result = (
        module.proposition_local_channel_scores(
            query_text="retry",

            query_entities=[
                "domain:operations",
                "cluster:retry-policy",
            ],

            candidate_family_ids=[
                "a",
                "b",
            ],

            proposition_units_by_family={
                "a": [
                    "HANDLE: one",
                    "HANDLE: two",
                ],

                "b": [
                    "HANDLE: three",
                    "HANDLE: four",
                    "HANDLE: five",
                ],
            },

            entities_by_family={
                "a": [],
                "b": [],
            },

            embedder=KeywordEmbedder(),
        )
    )

    assert (
        result[
            "semantic_comparisons"
        ]
        == 5
    )

    assert (
        result[
            "lexical_comparisons"
        ]
        == 5
    )


def test_local_ranker_has_no_oracle_parameters():
    module = _seed026()

    signature = inspect.signature(
        module.proposition_local_channel_scores
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


def test_target_rank_helper():
    module = _seed026()

    assert (
        module.target_rank(
            [
                "a",
                "target",
                "c",
            ],
            "target",
        )
        == 2
    )


def test_026_has_twenty_unique_families():
    tasks = _tasks026()

    payload = tasks.build_taskset()

    families = payload["families"]

    assert len(families) == 20

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


def test_026_has_four_clusters_five_each():
    tasks = _tasks026()

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


def test_026_queries_are_context_only():
    tasks = _tasks026()

    payload = tasks.build_taskset()

    for family in payload["families"]:

        assert (
            family[
                "degradation_mode"
            ]
            ==
            "context_only"
        )

        entities = (
            family[
                "query_entities"
            ]
        )

        assert not any(
            value.startswith(
                "system:"
            )
            for value
            in entities
        )

        assert not any(
            value.startswith(
                "code:"
            )
            for value
            in entities
        )


def test_seed020_candidate_geometry_is_five():
    tasks = _tasks026()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    payload = tasks.build_taskset()
    families = payload["families"]

    for family in families:

        result = (
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
            result[
                "candidate_count"
            ]
            == 5
        )

        assert (
            family["id"]
            in
            result[
                "candidate_family_ids"
            ]
        )


def test_each_cluster_shares_three_background_atoms():
    tasks = _tasks026()

    payload = tasks.build_taskset()

    clusters = {}

    for family in payload["families"]:

        clusters.setdefault(
            family[
                "interference_cluster"
            ],
            [],
        ).append(
            family
        )

    for families in clusters.values():

        backgrounds = {
            (
                family[
                    "atomic_units"
                ][0]["text"],
                family[
                    "atomic_units"
                ][2]["text"],
                family[
                    "atomic_units"
                ][3]["text"],
            )

            for family
            in families
        }

        assert len(backgrounds) == 1


def test_semantic_clauses_are_unique():
    tasks = _tasks026()

    payload = tasks.build_taskset()

    clauses = [
        family[
            "semantic_clause"
        ]

        for family
        in payload[
            "families"
        ]
    ]

    assert len(clauses) == len(
        set(clauses)
    )


def test_semantic_clause_occurs_once_in_source():
    tasks = _tasks026()

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
    tasks = _tasks026()

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


def test_taskset_freezes_pareto_attention():
    tasks = _tasks026()

    payload = tasks.build_taskset()

    assert (
        payload[
            "assembly_policy"
        ]
        ==
        "pareto_safe_active_channel_frontier"
    )

    assert (
        payload[
            "fusion_policy"
        ]
        ==
        "non_discriminative_channel_abstention"
    )

    assert (
        payload[
            "rrf_k"
        ]
        == 60
    )

    assert (
        payload[
            "top_k"
        ]
        == 3
    )


def test_only_scoring_granularity_changes():
    tasks = _tasks026()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "semantic and lexical retrieval scoring granularity only"
    )
