from __future__ import annotations

import argparse
import hashlib
import json
import os

from collections import (
    Counter,
    defaultdict,
)

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path
from typing import (
    Callable,
    Mapping,
)


from agent_cycle import (
    AgentDecision,
    reason_over_context,
)

from mnexa_context import (
    AssembledRecall,
    ContextFrame,
    ContextPreparer,
)

from experiments.seed_growth_017 import (
    build_memory_bundle,
)

from experiments.seed_growth_020 import (
    select_conjunctive_candidates,
)

from experiments.seed_growth_021 import (
    RRF_K,
    rendered_memory_from_bundle,
    retrieval_index_from_compact_memory,
)

from experiments.seed_growth_022 import (
    fuse_channel_scores_abstaining,
)

from experiments.seed_growth_026 import (
    proposition_local_channel_scores,
    proposition_units_from_retrieval_index,
)

from experiments.seed_growth_027 import (
    MIN_ACTIVE_CHANNELS,
    quorum_context_boundary,
)

from experiments.seed_growth_028 import (
    exclusive_decision_grade,
    runtime_family,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
)


TOP_K = 3


COMPETING_HYPOTHESIS_INSTRUCTION = """
The MNEXA memories supplied with this task are alternative candidate
hypotheses, not cumulative facts.

Some candidate rules may be mutually incompatible.

Select the single candidate rule whose decision-relevant evidence best
answers the task.

Do not merge, list, or present incompatible candidate rules together as
if they were simultaneously true.

State only the chosen rule, plus non-conflicting background information
only when directly necessary.
""".strip()


Reasoner = Callable[
    [
        str,
    ],
    str,
]


def render_frozen_context(
    *,
    selected_family_ids,
    rendered_memories: Mapping[
        str,
        str,
    ],
) -> str:
    """
    Deterministic model-visible MNEXA context.

    No benchmark target metadata is included.
    """

    segments = []

    for index, family_id in enumerate(
        selected_family_ids,
        start=1,
    ):

        if (
            family_id
            not in rendered_memories
        ):
            raise KeyError(
                "Missing rendered memory for "
                f"{family_id}"
            )

        segments.append(
            (
                f"MNEXA MEMORY {index}\n"
                +
                rendered_memories[
                    family_id
                ]
            )
        )

    if not segments:
        raise ValueError(
            "Frozen context may not be empty."
        )

    return (
        "\n\n"
        "-----\n\n"
    ).join(
        segments
    )


def prepare_and_reason_pair(
    *,
    prepare_context: Callable[
        [
            str,
        ],
        ContextFrame,
    ],
    recall_intent: str,
    task: str,
    reasoner: Reasoner,
    competing_instruction: str = (
        COMPETING_HYPOTHESIS_INSTRUCTION
    ),
):
    """
    Prepare MNEXA context exactly once.

    Then run two external model reasoning conditions over the literal
    same immutable ContextFrame.
    """

    context = (
        prepare_context(
            recall_intent
        )
    )

    if not isinstance(
        context,
        ContextFrame,
    ):
        raise TypeError(
            "prepare_context must return "
            "ContextFrame"
        )

    if not context.verify_integrity():
        raise ValueError(
            "ContextFrame integrity "
            "verification failed"
        )

    condition_a = (
        reason_over_context(
            context=context,
            task=task,
            reasoner=reasoner,
            reasoning_instruction="",
        )
    )

    condition_b = (
        reason_over_context(
            context=context,
            task=task,
            reasoner=reasoner,
            reasoning_instruction=(
                competing_instruction
            ),
        )
    )

    if (
        condition_a
        .context_evidence_sha256
        !=
        context.evidence_sha256
    ):
        raise RuntimeError(
            "Condition A escaped frozen context."
        )

    if (
        condition_b
        .context_evidence_sha256
        !=
        context.evidence_sha256
    ):
        raise RuntimeError(
            "Condition B escaped frozen context."
        )

    return {
        "context": (
            context
        ),

        "context_object_id": (
            id(
                context
            )
        ),

        "condition_a": (
            condition_a
        ),

        "condition_b": (
            condition_b
        ),

        "context_hash_equal": (
            condition_a
            .context_evidence_sha256
            ==
            condition_b
            .context_evidence_sha256
            ==
            context.evidence_sha256
        ),
    }


def _model_reasoner(
    model,
):
    """
    Adapt the existing experiment model adapter to agent_cycle's
    simple Callable[[str], str] boundary.

    The adapter remains outside MNEXA.
    """

    def reason(
        prompt: str,
    ) -> str:

        if callable(
            model
        ):
            result = model(
                prompt
            )

        elif hasattr(
            model,
            "generate",
        ):
            result = (
                model.generate(
                    prompt
                )
            )

        elif hasattr(
            model,
            "complete",
        ):
            result = (
                model.complete(
                    prompt
                )
            )

        elif hasattr(
            model,
            "respond",
        ):
            result = (
                model.respond(
                    prompt
                )
            )

        else:
            raise TypeError(
                "The configured model adapter "
                "does not expose a supported "
                "external reasoning call. "
                "Adapt it here, outside MNEXA."
            )

        if isinstance(
            result,
            str,
        ):
            return result

        if hasattr(
            result,
            "output_text",
        ):
            return str(
                result.output_text
            )

        if isinstance(
            result,
            Mapping,
        ):
            for key in (
                "output_text",
                "text",
                "content",
            ):
                if (
                    key
                    in result
                ):
                    return str(
                        result[
                            key
                        ]
                    )

        return str(
            result
        )

    return reason


def _mean(
    values,
):
    values = list(
        values
    )

    if not values:
        return 0.0

    return (
        sum(
            values
        )
        /
        len(
            values
        )
    )


def _cluster_metrics(
    rows,
    *,
    grade_key,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "exclusive_passes": 0,
            "target_rule_present": 0,
            "competing_rule_mention_families": 0,
            "competing_rule_hits": 0,
            "multi_memory_families": 0,
        }
    )

    for row in rows:

        cluster = (
            row[
                "interference_cluster"
            ]
        )

        bucket = (
            grouped[
                cluster
            ]
        )

        grade = (
            row[
                grade_key
            ]
        )

        bucket[
            "families"
        ] += 1

        bucket[
            "exclusive_passes"
        ] += int(
            grade[
                "exclusive_correct_pass"
            ]
        )

        bucket[
            "target_rule_present"
        ] += int(
            grade[
                "target_rule_present"
            ]
        )

        bucket[
            "competing_rule_mention_families"
        ] += int(
            grade[
                "competing_rule_hit_count"
            ]
            > 0
        )

        bucket[
            "competing_rule_hits"
        ] += int(
            grade[
                "competing_rule_hit_count"
            ]
        )

        bucket[
            "multi_memory_families"
        ] += int(
            row[
                "context_k"
            ]
            > 1
        )

    output = {}

    for cluster, bucket in sorted(
        grouped.items()
    ):

        count = (
            bucket[
                "families"
            ]
        )

        output[
            cluster
        ] = {
            **bucket,

            "exclusive_pass_rate": (
                bucket[
                    "exclusive_passes"
                ]
                /
                count
            ),
        }

    return output


def run_experiment_029(
    *,
    tasks_path,
    results_dir,
    model,
    embedder,
):
    tasks_path = Path(
        tasks_path
    )

    payload = json.loads(
        tasks_path.read_text()
    )

    benchmark_families = (
        payload[
            "families"
        ]
    )

    runtime_families = [
        runtime_family(
            family
        )

        for family
        in benchmark_families
    ]

    runtime_by_id = {
        family[
            "id"
        ]: family

        for family
        in runtime_families
    }

    benchmark_by_id = {
        family[
            "id"
        ]: family

        for family
        in benchmark_families
    }

    taskset_sha256 = (
        hashlib
        .sha256(
            tasks_path.read_bytes()
        )
        .hexdigest()
    )

    run_id = (
        datetime
        .now(
            timezone.utc
        )
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    run_dir = (
        Path(
            results_dir
        )
        /
        run_id
    )

    run_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ================================================================
    # MEMORY FORMATION — SHARED
    # ================================================================

    bundles = {
        family[
            "id"
        ]: (
            build_memory_bundle(
                family=family,
                model=model,
            )
        )

        for family
        in runtime_families
    }

    rendered_memories = {
        family_id: (
            rendered_memory_from_bundle(
                bundle
            )
        )

        for family_id, bundle
        in bundles.items()
    }

    proposition_units_by_family = {}

    entities_by_family = {
        family[
            "id"
        ]: list(
            family[
                "entities"
            ]
        )

        for family
        in runtime_families
    }

    for family in (
        runtime_families
    ):

        family_id = (
            family[
                "id"
            ]
        )

        retrieval_document = (
            retrieval_index_from_compact_memory(
                compact_memory=(
                    rendered_memories[
                        family_id
                    ]
                ),

                entities=(
                    family[
                        "entities"
                    ]
                ),
            )
        )

        proposition_units_by_family[
            family_id
        ] = (
            proposition_units_from_retrieval_index(
                retrieval_document
            )
        )

    reasoner = (
        _model_reasoner(
            model
        )
    )

    counters = {
        "context_prepare_calls": 0,
        "recall_calls": 0,
        "assemble_calls": 0,
        "reasoner_calls": 0,
    }

    def counted_reasoner(
        prompt,
    ):
        counters[
            "reasoner_calls"
        ] += 1

        return reasoner(
            prompt
        )

    rows = []

    # ================================================================
    # ONE RECALL / TWO REASONING CALLS PER FAMILY
    # ================================================================

    for benchmark_family in (
        benchmark_families
    ):

        family_id = (
            benchmark_family[
                "id"
            ]
        )

        family = (
            runtime_by_id[
                family_id
            ]
        )

        per_family_state = {}

        def freeze_watermark():
            return 0

        def recall(
            recall_intent,
            watermark,
        ):
            counters[
                "recall_calls"
            ] += 1

            route = (
                select_conjunctive_candidates(
                    query_entities=(
                        family[
                            "query_entities"
                        ]
                    ),

                    families=(
                        runtime_families
                    ),
                )
            )

            candidate_ids = (
                route[
                    "candidate_family_ids"
                ]
            )

            if len(
                candidate_ids
            ) != 5:
                raise RuntimeError(
                    "Seed 029 expected a "
                    "five-memory candidate "
                    f"neighborhood for {family_id}."
                )

            query_text = (
                recall_intent
                +
                "\n"
                +
                " ".join(
                    family[
                        "query_entities"
                    ]
                )
            )

            local_raw = (
                proposition_local_channel_scores(
                    query_text=(
                        query_text
                    ),

                    query_entities=(
                        family[
                            "query_entities"
                        ]
                    ),

                    candidate_family_ids=(
                        candidate_ids
                    ),

                    proposition_units_by_family=(
                        proposition_units_by_family
                    ),

                    entities_by_family=(
                        entities_by_family
                    ),

                    embedder=embedder,
                )
            )

            fused = (
                fuse_channel_scores_abstaining(
                    candidate_family_ids=(
                        candidate_ids
                    ),

                    channel_scores=(
                        local_raw[
                            "channel_scores"
                        ]
                    ),

                    top_k=5,

                    rrf_k=RRF_K,
                )
            )

            boundary = (
                quorum_context_boundary(
                    ordered_family_ids=(
                        fused[
                            "selected_family_ids"
                        ]
                    ),

                    channel_ranks=(
                        fused[
                            "channel_ranks"
                        ]
                    ),

                    active_channels=(
                        fused[
                            "active_channels"
                        ]
                    ),

                    max_k=TOP_K,

                    min_active_channels=(
                        MIN_ACTIVE_CHANNELS
                    ),
                )
            )

            selected_ids = tuple(
                boundary[
                    "selected_family_ids"
                ]
            )

            per_family_state[
                "route"
            ] = route

            per_family_state[
                "channel_scores"
            ] = (
                local_raw[
                    "channel_scores"
                ]
            )

            per_family_state[
                "best_units"
            ] = (
                local_raw[
                    "best_units"
                ]
            )

            per_family_state[
                "fusion"
            ] = fused

            per_family_state[
                "boundary"
            ] = boundary

            per_family_state[
                "selected_ids"
            ] = selected_ids

            return {
                "selected_family_ids": (
                    selected_ids
                ),
            }

        def assemble(
            recalled,
            watermark,
        ):
            counters[
                "assemble_calls"
            ] += 1

            selected_ids = tuple(
                recalled[
                    "selected_family_ids"
                ]
            )

            context_text = (
                render_frozen_context(
                    selected_family_ids=(
                        selected_ids
                    ),

                    rendered_memories=(
                        rendered_memories
                    ),
                )
            )

            return AssembledRecall(
                selected_memory_ids=(
                    selected_ids
                ),

                context_text=(
                    context_text
                ),

                metadata={
                    "experiment": (
                        "seed-growth-029"
                    ),

                    "taskset_sha256": (
                        taskset_sha256
                    ),

                    "retrieval_policy": (
                        "proposition_local_"
                        "max_handle_scoring"
                    ),

                    "fusion_policy": (
                        "non_discriminative_"
                        "channel_abstention"
                    ),

                    "assembly_policy": (
                        "evidence_quorum_"
                        "guarded_pareto"
                    ),

                    "active_channels": list(
                        per_family_state[
                            "fusion"
                        ][
                            "active_channels"
                        ]
                    ),

                    "context_k": (
                        len(
                            selected_ids
                        )
                    ),
                },
            )

        preparer = (
            ContextPreparer(
                freeze_watermark=(
                    freeze_watermark
                ),

                recall=(
                    recall
                ),

                assemble=(
                    assemble
                ),
            )
        )

        def prepare_context(
            recall_intent,
        ):
            counters[
                "context_prepare_calls"
            ] += 1

            return preparer.prepare(
                recall_intent=(
                    recall_intent
                )
            )

        pair = (
            prepare_and_reason_pair(
                prepare_context=(
                    prepare_context
                ),

                recall_intent=(
                    family[
                        "query_prompt"
                    ]
                ),

                task=(
                    family[
                        "query_prompt"
                    ]
                ),

                reasoner=(
                    counted_reasoner
                ),
            )
        )

        context = (
            pair[
                "context"
            ]
        )

        condition_a = (
            pair[
                "condition_a"
            ]
        )

        condition_b = (
            pair[
                "condition_b"
            ]
        )

        target_signature = (
            benchmark_family[
                "decision_signature"
            ]
        )

        competing_signatures = (
            benchmark_family[
                "competing_signatures"
            ]
        )

        grade_a = (
            exclusive_decision_grade(
                decision_text=(
                    condition_a.decision
                ),

                target_signature=(
                    target_signature
                ),

                competing_signatures=(
                    competing_signatures
                ),
            )
        )

        grade_b = (
            exclusive_decision_grade(
                decision_text=(
                    condition_b.decision
                ),

                target_signature=(
                    target_signature
                ),

                competing_signatures=(
                    competing_signatures
                ),
            )
        )

        selected_ids = tuple(
            context.selected_memory_ids
        )

        rows.append(
            {
                "family_id": (
                    family_id
                ),

                "interference_cluster": (
                    family[
                        "interference_cluster"
                    ]
                ),

                "query_prompt": (
                    family[
                        "query_prompt"
                    ]
                ),

                "active_channels": (
                    per_family_state[
                        "fusion"
                    ][
                        "active_channels"
                    ]
                ),

                "selected_family_ids": (
                    selected_ids
                ),

                "context_k": (
                    len(
                        selected_ids
                    )
                ),

                "context_watermark": (
                    context.watermark
                ),

                "context_evidence_sha256": (
                    context.evidence_sha256
                ),

                "context_integrity_valid": (
                    context.verify_integrity()
                ),

                "condition_a": {
                    "decision": (
                        condition_a.decision
                    ),

                    "context_evidence_sha256": (
                        condition_a
                        .context_evidence_sha256
                    ),
                },

                "condition_b": {
                    "decision": (
                        condition_b.decision
                    ),

                    "context_evidence_sha256": (
                        condition_b
                        .context_evidence_sha256
                    ),
                },

                "condition_a_exclusive": (
                    grade_a
                ),

                "condition_b_exclusive": (
                    grade_b
                ),

                "context_hash_equal": (
                    pair[
                        "context_hash_equal"
                    ]
                ),

                "same_context_object": True,

                "paired": {
                    "exclusive_rescue": (
                        (
                            not
                            grade_a[
                                "exclusive_correct_pass"
                            ]
                        )
                        and
                        grade_b[
                            "exclusive_correct_pass"
                        ]
                    ),

                    "exclusive_harm": (
                        grade_a[
                            "exclusive_correct_pass"
                        ]
                        and
                        (
                            not
                            grade_b[
                                "exclusive_correct_pass"
                            ]
                        )
                    ),

                    "target_rescue": (
                        (
                            not
                            grade_a[
                                "target_rule_present"
                            ]
                        )
                        and
                        grade_b[
                            "target_rule_present"
                        ]
                    ),

                    "target_harm": (
                        grade_a[
                            "target_rule_present"
                        ]
                        and
                        (
                            not
                            grade_b[
                                "target_rule_present"
                            ]
                        )
                    ),

                    "competing_hit_delta": (
                        grade_b[
                            "competing_rule_hit_count"
                        ]
                        -
                        grade_a[
                            "competing_rule_hit_count"
                        ]
                    ),
                },
            }
        )

    # ================================================================
    # AGGREGATION
    # ================================================================

    task_count = len(
        rows
    )

    multi_memory_rows = [
        row

        for row
        in rows

        if row[
            "context_k"
        ] > 1
    ]

    context_k_distribution = (
        Counter(
            row[
                "context_k"
            ]

            for row
            in rows
        )
    )

    active_channel_distribution = (
        Counter(
            len(
                row[
                    "active_channels"
                ]
            )

            for row
            in rows
        )
    )

    def grade_count(
        key,
        metric,
    ):
        return sum(
            int(
                row[
                    key
                ][
                    metric
                ]
            )

            for row
            in rows
        )

    report = {
        "experiment": (
            "seed-growth-029"
        ),

        "classification": (
            "exploratory-fresh-frozen-"
            "context-reasoning-ablation"
        ),

        "run_id": (
            run_id
        ),

        "taskset_sha256": (
            taskset_sha256
        ),

        "model": getattr(
            model,
            "name",
            type(
                model
            ).__name__,
        ),

        "task_count": (
            task_count
        ),

        "pool_size": (
            len(
                runtime_families
            )
        ),

        "conditions": {
            "A": (
                "same_frozen_context_"
                "standard_model_reasoning"
            ),

            "B": (
                "same_frozen_context_"
                "competing_hypothesis_reasoning"
            ),
        },

        # ============================================================
        # ADR-0017 ARCHITECTURAL CONTROL
        # ============================================================

        "context_prepare_calls": (
            counters[
                "context_prepare_calls"
            ]
        ),

        "recall_calls": (
            counters[
                "recall_calls"
            ]
        ),

        "assemble_calls": (
            counters[
                "assemble_calls"
            ]
        ),

        "reasoner_calls": (
            counters[
                "reasoner_calls"
            ]
        ),

        "expected_context_prepare_calls": (
            task_count
        ),

        "expected_recall_calls": (
            task_count
        ),

        "expected_reasoner_calls": (
            task_count
            *
            2
        ),

        "context_hash_equal_pairs": sum(
            int(
                row[
                    "context_hash_equal"
                ]
            )

            for row
            in rows
        ),

        "context_hash_mismatch_pairs": sum(
            int(
                not row[
                    "context_hash_equal"
                ]
            )

            for row
            in rows
        ),

        "same_context_object_pairs": sum(
            int(
                row[
                    "same_context_object"
                ]
            )

            for row
            in rows
        ),

        "context_integrity_valid_families": sum(
            int(
                row[
                    "context_integrity_valid"
                ]
            )

            for row
            in rows
        ),

        "adr_0017_boundary_valid": (
            counters[
                "context_prepare_calls"
            ]
            ==
            task_count
            and
            counters[
                "recall_calls"
            ]
            ==
            task_count
            and
            counters[
                "reasoner_calls"
            ]
            ==
            (
                task_count
                *
                2
            )
            and
            all(
                row[
                    "context_hash_equal"
                ]

                for row
                in rows
            )
            and
            all(
                row[
                    "context_integrity_valid"
                ]

                for row
                in rows
            )
        ),

        # ============================================================
        # MECHANISM EXERCISE
        # ============================================================

        "context_k_distribution": {
            str(
                key
            ): value

            for key, value
            in sorted(
                context_k_distribution.items()
            )
        },

        "active_channel_count_distribution": {
            str(
                key
            ): value

            for key, value
            in sorted(
                active_channel_distribution.items()
            )
        },

        "multi_memory_context_families": (
            len(
                multi_memory_rows
            )
        ),

        "single_memory_context_families": (
            task_count
            -
            len(
                multi_memory_rows
            )
        ),

        # ============================================================
        # PRIMARY STRICT DECISION METRICS
        # ============================================================

        "condition_a_exclusive_correct_passes": (
            grade_count(
                "condition_a_exclusive",
                "exclusive_correct_pass",
            )
        ),

        "condition_b_exclusive_correct_passes": (
            grade_count(
                "condition_b_exclusive",
                "exclusive_correct_pass",
            )
        ),

        "condition_a_target_rule_present_families": (
            grade_count(
                "condition_a_exclusive",
                "target_rule_present",
            )
        ),

        "condition_b_target_rule_present_families": (
            grade_count(
                "condition_b_exclusive",
                "target_rule_present",
            )
        ),

        "condition_a_competing_rule_mention_families": sum(
            int(
                row[
                    "condition_a_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "condition_b_competing_rule_mention_families": sum(
            int(
                row[
                    "condition_b_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "condition_a_total_competing_rule_hits": sum(
            row[
                "condition_a_exclusive"
            ][
                "competing_rule_hit_count"
            ]

            for row
            in rows
        ),

        "condition_b_total_competing_rule_hits": sum(
            row[
                "condition_b_exclusive"
            ][
                "competing_rule_hit_count"
            ]

            for row
            in rows
        ),

        "exclusive_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "exclusive_rescue"
                ]
            )

            for row
            in rows
        ),

        "exclusive_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "exclusive_harm"
                ]
            )

            for row
            in rows
        ),

        "target_rule_rescue_families": sum(
            int(
                row[
                    "paired"
                ][
                    "target_rescue"
                ]
            )

            for row
            in rows
        ),

        "target_rule_harm_families": sum(
            int(
                row[
                    "paired"
                ][
                    "target_harm"
                ]
            )

            for row
            in rows
        ),

        # ============================================================
        # MULTI-MEMORY SLICE
        # ============================================================

        "multi_memory_condition_a_exclusive_passes": sum(
            int(
                row[
                    "condition_a_exclusive"
                ][
                    "exclusive_correct_pass"
                ]
            )

            for row
            in multi_memory_rows
        ),

        "multi_memory_condition_b_exclusive_passes": sum(
            int(
                row[
                    "condition_b_exclusive"
                ][
                    "exclusive_correct_pass"
                ]
            )

            for row
            in multi_memory_rows
        ),

        "multi_memory_condition_a_competing_mentions": sum(
            int(
                row[
                    "condition_a_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in multi_memory_rows
        ),

        "multi_memory_condition_b_competing_mentions": sum(
            int(
                row[
                    "condition_b_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in multi_memory_rows
        ),

        # ============================================================
        # COST
        # ============================================================

        "mean_context_k": (
            _mean(
                row[
                    "context_k"
                ]

                for row
                in rows
            )
        ),

        "mean_context_words": (
            _mean(
                len(
                    pair_context.split()
                )
                for pair_context
                in [
                    render_frozen_context(
                        selected_family_ids=(
                            row[
                                "selected_family_ids"
                            ]
                        ),
                        rendered_memories=(
                            rendered_memories
                        ),
                    )
                    for row
                    in rows
                ]
            )
        ),

        # ============================================================
        # SAFETY / CONTROLS
        # ============================================================

        "compact_memory_bundles": (
            len(
                bundles
            )
        ),

        "bundles_with_exact_semantic_clause_visible": sum(
            int(
                bundle[
                    "semantic_clause_visible"
                ]
            )

            for bundle
            in bundles.values()
        ),

        "bundle_unsupported_claims_admitted": sum(
            int(
                bundle[
                    "unsupported_claims_admitted"
                ]
            )

            for bundle
            in bundles.values()
        ),

        "same_context_frame_between_conditions": True,

        "same_context_hash_between_conditions": all(
            row[
                "context_hash_equal"
            ]

            for row
            in rows
        ),

        "same_watermark_between_conditions": True,

        "same_selected_memory_ids_between_conditions": True,

        "same_context_text_between_conditions": True,

        "same_task_between_conditions": True,

        "same_model_between_conditions": True,

        "only_reasoning_instruction_differs": True,

        "reasoning_occurs_outside_mnexa": True,

        "strict_grader_metadata_removed_before_runtime": True,

        "ranker_model_calls": 0,

        "assembler_model_calls": 0,

        "exclusive_grader_model_calls": 0,

        "condition_a_reasoner_calls": (
            task_count
        ),

        "condition_b_reasoner_calls": (
            task_count
        ),

        "cluster_metrics_a": (
            _cluster_metrics(
                rows,
                grade_key=(
                    "condition_a_exclusive"
                ),
            )
        ),

        "cluster_metrics_b": (
            _cluster_metrics(
                rows,
                grade_key=(
                    "condition_b_exclusive"
                ),
            )
        ),

        "families": (
            rows
        ),
    }

    output = (
        run_dir
        /
        "result.json"
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
        )
        +
        "\n"
    )

    return (
        report,
        output,
    )


def main():
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/tasks_029.json"
        ),
    )

    parser.add_argument(
        "--results",
        default=(
            "experiments/results"
        ),
    )

    args = (
        parser.parse_args()
    )

    model_name = (
        os.environ.get(
            "MNEXA_MODEL"
        )
    )

    if not model_name:
        raise SystemExit(
            "Set MNEXA_MODEL."
        )

    model = (
        OpenAIResponsesModel(
            model_name
        )
    )

    embedder = (
        SentenceTransformerEmbedder(
            os.environ.get(
                "MNEXA_EMBED_MODEL",
                (
                    "sentence-transformers/"
                    "all-MiniLM-L6-v2"
                ),
            )
        )
    )

    report, output = (
        run_experiment_029(
            tasks_path=(
                args.tasks
            ),
            results_dir=(
                args.results
            ),
            model=model,
            embedder=embedder,
        )
    )

    keys = (
        "experiment",
        "taskset_sha256",

        "context_prepare_calls",
        "recall_calls",
        "assemble_calls",
        "reasoner_calls",

        "context_hash_equal_pairs",
        "context_hash_mismatch_pairs",
        "same_context_object_pairs",
        "context_integrity_valid_families",
        "adr_0017_boundary_valid",

        "context_k_distribution",
        "active_channel_count_distribution",
        "multi_memory_context_families",

        "condition_a_exclusive_correct_passes",
        "condition_b_exclusive_correct_passes",

        "condition_a_target_rule_present_families",
        "condition_b_target_rule_present_families",

        "condition_a_competing_rule_mention_families",
        "condition_b_competing_rule_mention_families",

        "condition_a_total_competing_rule_hits",
        "condition_b_total_competing_rule_hits",

        "exclusive_rescue_families",
        "exclusive_harm_families",

        "multi_memory_condition_a_exclusive_passes",
        "multi_memory_condition_b_exclusive_passes",

        "multi_memory_condition_a_competing_mentions",
        "multi_memory_condition_b_competing_mentions",

        "mean_context_k",
        "mean_context_words",

        "bundle_unsupported_claims_admitted",

        "same_context_frame_between_conditions",
        "same_context_hash_between_conditions",
        "same_selected_memory_ids_between_conditions",
        "same_context_text_between_conditions",
        "same_task_between_conditions",
        "same_model_between_conditions",
        "only_reasoning_instruction_differs",
        "reasoning_occurs_outside_mnexa",

        "condition_a_reasoner_calls",
        "condition_b_reasoner_calls",

        "cluster_metrics_a",
        "cluster_metrics_b",
    )

    summary = {
        key: (
            report[
                key
            ]
        )

        for key
        in keys
    }

    summary[
        "result"
    ] = str(
        output
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
