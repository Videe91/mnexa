import importlib
import inspect

import pytest

from mnexa_context import ContextFrame


def _seed029():
    try:
        return importlib.import_module(
            "experiments.seed_growth_029"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 029 implementation "
            f"does not exist yet: {exc}"
        )


def _tasks029():
    try:
        return importlib.import_module(
            "experiments.make_tasks_029"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Seed Growth 029 task generator "
            f"does not exist yet: {exc}"
        )


def _frame():
    return ContextFrame.create(
        watermark=0,
        recall_intent="find exact retry rule",
        selected_memory_ids=(
            "m1",
            "m2",
            "m3",
        ),
        context_text=(
            "MEMORY 1\nretry exactly twenty-one times\n\n"
            "MEMORY 2\nretry at most sixteen times\n\n"
            "MEMORY 3\nretry at least eleven times"
        ),
        metadata={
            "experiment": "seed-growth-029",
        },
    )


def test_reasoning_pair_prepares_context_exactly_once():
    module = _seed029()

    calls = {
        "prepare": 0,
        "reason": 0,
    }

    frame = _frame()

    def prepare_context(
        recall_intent,
    ):
        calls["prepare"] += 1

        assert (
            recall_intent
            ==
            "find exact retry rule"
        )

        return frame

    def reasoner(
        prompt,
    ):
        calls["reason"] += 1

        return (
            "Retry exactly twenty-one times."
        )

    result = (
        module.prepare_and_reason_pair(
            prepare_context=(
                prepare_context
            ),

            recall_intent=(
                "find exact retry rule"
            ),

            task=(
                "State the exact retry-count rule."
            ),

            reasoner=(
                reasoner
            ),
        )
    )

    assert (
        calls["prepare"]
        == 1
    )

    assert (
        calls["reason"]
        == 2
    )

    assert (
        result[
            "context"
        ]
        is frame
    )


def test_both_reasoning_conditions_share_exact_hash():
    module = _seed029()

    frame = _frame()

    result = (
        module.prepare_and_reason_pair(
            prepare_context=(
                lambda recall_intent:
                    frame
            ),

            recall_intent="query",

            task="State the rule.",

            reasoner=(
                lambda prompt:
                    "answer"
            ),
        )
    )

    assert (
        result[
            "condition_a"
        ].context_evidence_sha256
        ==
        result[
            "condition_b"
        ].context_evidence_sha256
        ==
        frame.evidence_sha256
    )


def test_both_conditions_use_same_context_object():
    module = _seed029()

    frame = _frame()

    result = (
        module.prepare_and_reason_pair(
            prepare_context=(
                lambda recall_intent:
                    frame
            ),

            recall_intent="query",
            task="question",
            reasoner=(
                lambda prompt:
                    "answer"
            ),
        )
    )

    assert (
        result[
            "context_object_id"
        ]
        ==
        id(frame)
    )


def test_condition_a_has_no_competing_hypothesis_instruction():
    module = _seed029()

    prompts = []

    module.prepare_and_reason_pair(
        prepare_context=(
            lambda recall_intent:
                _frame()
        ),

        recall_intent="query",

        task="State the rule.",

        reasoner=(
            lambda prompt:
                prompts.append(
                    prompt
                )
                or
                "answer"
        ),
    )

    assert (
        module.COMPETING_HYPOTHESIS_INSTRUCTION
        not in
        prompts[0]
    )


def test_condition_b_has_competing_hypothesis_instruction():
    module = _seed029()

    prompts = []

    module.prepare_and_reason_pair(
        prepare_context=(
            lambda recall_intent:
                _frame()
        ),

        recall_intent="query",

        task="State the rule.",

        reasoner=(
            lambda prompt:
                prompts.append(
                    prompt
                )
                or
                "answer"
        ),
    )

    assert (
        module.COMPETING_HYPOTHESIS_INSTRUCTION
        in
        prompts[1]
    )


def test_reasoning_instruction_does_not_enter_context_frame():
    module = _seed029()

    frame = _frame()

    before = (
        frame.evidence_sha256
    )

    result = (
        module.prepare_and_reason_pair(
            prepare_context=(
                lambda recall_intent:
                    frame
            ),

            recall_intent="query",

            task="question",

            reasoner=(
                lambda prompt:
                    "answer"
            ),
        )
    )

    assert (
        frame.evidence_sha256
        ==
        before
    )

    assert (
        result[
            "context"
        ].verify_integrity()
        is True
    )


def test_context_must_be_context_frame():
    module = _seed029()

    with pytest.raises(
        TypeError,
        match="ContextFrame",
    ):
        module.prepare_and_reason_pair(
            prepare_context=(
                lambda recall_intent:
                    "not-a-context-frame"
            ),
            recall_intent="query",
            task="question",
            reasoner=(
                lambda prompt:
                    "answer"
            ),
        )


def test_corrupted_context_is_rejected():
    module = _seed029()

    import dataclasses

    frame = _frame()

    corrupted = (
        dataclasses.replace(
            frame,
            context_text="tampered",
        )
    )

    with pytest.raises(
        ValueError,
        match="integrity",
    ):
        module.prepare_and_reason_pair(
            prepare_context=(
                lambda recall_intent:
                    corrupted
            ),
            recall_intent="query",
            task="question",
            reasoner=(
                lambda prompt:
                    "answer"
            ),
        )


def test_context_renderer_is_deterministic():
    module = _seed029()

    bundles = {
        "a": {
            "compact_memory": "memory A"
        },
        "b": {
            "compact_memory": "memory B"
        },
    }

    first = (
        module.render_frozen_context(
            selected_family_ids=(
                "a",
                "b",
            ),
            rendered_memories={
                "a": "memory A",
                "b": "memory B",
            },
        )
    )

    second = (
        module.render_frozen_context(
            selected_family_ids=(
                "a",
                "b",
            ),
            rendered_memories={
                "a": "memory A",
                "b": "memory B",
            },
        )
    )

    assert first == second


def test_context_renderer_preserves_selection_order():
    module = _seed029()

    rendered = (
        module.render_frozen_context(
            selected_family_ids=(
                "b",
                "a",
            ),
            rendered_memories={
                "a": "AAA",
                "b": "BBB",
            },
        )
    )

    assert (
        rendered.index("BBB")
        <
        rendered.index("AAA")
    )


def test_pair_function_has_no_retrieval_or_model_inside_mnexa():
    module = _seed029()

    signature = inspect.signature(
        module.prepare_and_reason_pair
    )

    assert (
        "prepare_context"
        in signature.parameters
    )

    assert (
        "reasoner"
        in signature.parameters
    )

    prohibited = {
        "mnexa_reasoner",
        "mnexa_model",
        "grader",
        "target_family_id",
    }

    assert prohibited.isdisjoint(
        signature.parameters
    )


def test_029_has_twenty_unique_families():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    families = payload[
        "families"
    ]

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


def test_029_has_four_clusters_five_each():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    counts = {}

    for family in payload[
        "families"
    ]:

        cluster = (
            family[
                "interference_cluster"
            ]
        )

        counts[
            cluster
        ] = (
            counts.get(
                cluster,
                0,
            )
            +
            1
        )

    assert counts == {
        "retry-policy": 5,
        "lane-routing": 5,
        "channel-session": 5,
        "storage-finalization": 5,
    }


def test_every_family_has_strict_grader_metadata():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        assert (
            family[
                "decision_signature"
            ][
                "all_of"
            ]
        )

        assert (
            len(
                family[
                    "competing_signatures"
                ]
            )
            == 4
        )


def test_queries_are_context_only():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    for family in payload[
        "families"
    ]:

        assert (
            family[
                "degradation_mode"
            ]
            ==
            "context_only"
        )

        assert not any(
            value.startswith(
                "system:"
            )

            for value
            in family[
                "query_entities"
            ]
        )

        assert not any(
            value.startswith(
                "code:"
            )

            for value
            in family[
                "query_entities"
            ]
        )


def test_seed020_candidate_geometry_remains_five():
    tasks = _tasks029()

    from experiments.seed_growth_020 import (
        select_conjunctive_candidates,
    )

    from experiments.seed_growth_028 import (
        runtime_family,
    )

    payload = tasks.build_taskset()

    families = [
        runtime_family(
            family
        )

        for family
        in payload[
            "families"
        ]
    ]

    for family in families:

        route = (
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
            route[
                "candidate_count"
            ]
            == 5
        )

        assert (
            family["id"]
            in
            route[
                "candidate_family_ids"
            ]
        )


def test_taskset_freezes_seed027_retrieval_attention_stack():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    assert (
        payload[
            "retrieval_policy"
        ]
        ==
        "proposition_local_max_handle_scoring"
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
            "assembly_policy"
        ]
        ==
        "evidence_quorum_guarded_pareto"
    )

    assert (
        payload[
            "min_active_channels_for_pruning"
        ]
        == 2
    )

    assert (
        payload["top_k"]
        == 3
    )

    assert (
        payload["rrf_k"]
        == 60
    )


def test_only_reasoning_instruction_changes():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    assert (
        payload[
            "experimental_variable"
        ]
        ==
        "external model reasoning instruction only"
    )


def test_taskset_declares_one_context_two_reasoning_calls():
    tasks = _tasks029()

    payload = tasks.build_taskset()

    assert (
        payload[
            "context_preparations_per_family"
        ]
        == 1
    )

    assert (
        payload[
            "reasoning_calls_per_family"
        ]
        == 2
    )
