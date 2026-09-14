from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re

from collections import (
    Counter,
    defaultdict,
)

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


from experiments.seed_growth_017 import (
    build_memory_bundle,
    build_memory_snapshot,
    evaluate_snapshot,
)

from experiments.seed_growth_019 import (
    evaluation_family,
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

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


TOP_K = 3


EPISTEMIC_INSTRUCTION = """
EPISTEMIC INSTRUCTION:

The memories available for this question are alternative candidate hypotheses, not cumulative facts. Some candidate rules may be mutually incompatible.

Select the single candidate rule whose decision-relevant evidence best answers the question.

Do not merge, list, or present incompatible candidate rules together as if they were simultaneously true.

State only the chosen rule, plus background facts only when they are necessary, non-conflicting, and directly relevant.
""".strip()


def competing_hypothesis_prompt(
    base_prompt,
):
    return (
        str(
            base_prompt
        ).rstrip()
        +
        "\n\n"
        +
        EPISTEMIC_INSTRUCTION
    )


def apply_competing_hypothesis_frame(
    evaluation_family_payload,
):
    payload = copy.deepcopy(
        evaluation_family_payload
    )

    has_transfer_obj = (
        "transfer" in payload
        and isinstance(
            payload["transfer"],
            dict,
        )
        and "prompt" in payload["transfer"]
    )

    has_transfer_prompt = (
        "transfer_prompt" in payload
    )

    if (
        not has_transfer_obj
        and not has_transfer_prompt
    ):

        raise KeyError(
            "transfer_prompt is required "
            "for competing-hypothesis framing"
        )

    if has_transfer_prompt:

        payload[
            "transfer_prompt"
        ] = (
            competing_hypothesis_prompt(
                payload[
                    "transfer_prompt"
                ]
            )
        )

    if has_transfer_obj:

        payload[
            "transfer"
        ][
            "prompt"
        ] = (
            competing_hypothesis_prompt(
                payload[
                    "transfer"
                ][
                    "prompt"
                ]
            )
        )

    return payload


def runtime_family(
    family,
):
    """
    Remove post-hoc benchmark grading metadata before the family enters
    memory formation, retrieval, assembly, or model reasoning.
    """

    result = copy.deepcopy(
        family
    )

    result.pop(
        "decision_signature",
        None,
    )

    result.pop(
        "competing_signatures",
        None,
    )

    return result


def signature_matches(
    text,
    signature,
):
    patterns = list(
        signature.get(
            "all_of",
            [],
        )
    )

    if not patterns:
        raise ValueError(
            "Decision signature must contain "
            "at least one all_of pattern."
        )

    return all(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        is not None

        for pattern
        in patterns
    )


def exclusive_decision_grade(
    *,
    decision_text,
    target_signature,
    competing_signatures,
):
    """
    Strict post-hoc decision grading.

    A clean pass requires:

        target rule present
        AND
        zero competing candidate-rule signatures present

    This grader is never supplied to the ranker, assembler, or reasoner.
    """

    target_present = (
        signature_matches(
            decision_text,
            target_signature,
        )
    )

    competing_hits = []

    for competitor in (
        competing_signatures
    ):

        if signature_matches(
            decision_text,
            competitor,
        ):

            competing_hits.append(
                {
                    "family_id": (
                        competitor[
                            "family_id"
                        ]
                    ),

                    "semantic_clause": (
                        competitor[
                            "semantic_clause"
                        ]
                    ),
                }
            )

    return {
        "target_rule_present": (
            target_present
        ),

        "competing_rule_hit_count": (
            len(
                competing_hits
            )
        ),

        "competing_family_ids": [
            item[
                "family_id"
            ]

            for item
            in competing_hits
        ],

        "competing_semantic_clauses": [
            item[
                "semantic_clause"
            ]

            for item
            in competing_hits
        ],

        "exclusive_correct_pass": (
            target_present
            and
            not competing_hits
        ),
    }


def canonical_selection_key(
    *,
    selected_family_ids,
    canonical_family_ids,
):
    selected = set(
        selected_family_ids
    )

    return tuple(
        family_id

        for family_id
        in canonical_family_ids

        if family_id
        in selected
    )


def _mean(
    values,
):
    values = list(
        values
    )

    if not values:
        return 0.0

    return (
        sum(values)
        /
        len(values)
    )


def _count_eval(
    rows,
    condition,
    metric,
):
    return sum(
        int(
            row[
                condition
            ][
                metric
            ]
        )

        for row
        in rows
    )


def _sum_eval(
    rows,
    condition,
    metric,
):
    return sum(
        float(
            row[
                condition
            ][
                metric
            ]
        )

        for row
        in rows
    )


def _count_grade(
    rows,
    condition,
    metric,
):
    return sum(
        int(
            row[
                condition
                +
                "_exclusive"
            ][
                metric
            ]
        )

        for row
        in rows
    )


def _aggregate_cluster_metrics(
    rows,
    *,
    condition,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "exclusive_passes": 0,
            "target_rule_present": 0,
            "competing_rule_mention_families": 0,
            "competing_rule_hits": 0,
            "semantic_task_passes": 0,
            "multi_memory_contexts": 0,
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
                condition
                +
                "_exclusive"
            ]
        )

        evaluation = (
            row[
                condition
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
            "semantic_task_passes"
        ] += int(
            evaluation[
                "semantic_task_pass"
            ]
        )

        bucket[
            "multi_memory_contexts"
        ] += int(
            evaluation[
                "memory_segment_count"
            ]
            > 1
        )

    output = {}

    for (
        cluster,
        bucket,
    ) in sorted(
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

            "target_rule_present_rate": (
                bucket[
                    "target_rule_present"
                ]
                /
                count
            ),
        }

    return output


def run_experiment_028(
    *,
    tasks_path,
    results_dir,
    model,
    embedder,
    meter,
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

    canonical_family_ids = [
        family[
            "id"
        ]

        for family
        in runtime_families
    ]

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

    snapshot_dir = (
        run_dir
        /
        "state"
        /
        "assembled_snapshots"
    )

    eval_dir = (
        run_dir
        /
        "state"
        /
        "evaluations"
    )

    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    eval_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ================================================================
    # MEMORY FORMATION — ONCE, SHARED
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

        compact_memory = (
            rendered_memory_from_bundle(
                bundles[
                    family_id
                ]
            )
        )

        retrieval_document = (
            retrieval_index_from_compact_memory(
                compact_memory=(
                    compact_memory
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

    # ================================================================
    # SNAPSHOT CACHE — SHARED BY BOTH CONDITIONS
    # ================================================================

    snapshot_cache = {}

    def snapshot_for(
        selected_family_ids,
    ):
        key = (
            canonical_selection_key(
                selected_family_ids=(
                    selected_family_ids
                ),

                canonical_family_ids=(
                    canonical_family_ids
                ),
            )
        )

        if not key:

            raise RuntimeError(
                "Assembled context may not be empty."
            )

        if key in snapshot_cache:

            return (
                snapshot_cache[
                    key
                ],
                key,
            )

        digest = (
            hashlib
            .sha256(
                "|".join(
                    key
                )
                .encode(
                    "utf-8"
                )
            )
            .hexdigest()[:16]
        )

        selected_families = [
            runtime_by_id[
                family_id
            ]

            for family_id
            in key
        ]

        snapshot = (
            build_memory_snapshot(
                db_path=(
                    snapshot_dir
                    /
                    (
                        "assembled_"
                        +
                        digest
                        +
                        ".sqlite3"
                    )
                ),

                families=(
                    selected_families
                ),

                bundles=bundles,

                embedder=embedder,
                meter=meter,
            )
        )

        snapshot_cache[
            key
        ] = (
            snapshot
        )

        return (
            snapshot,
            key,
        )

    clause_by_family = {
        family[
            "id"
        ]: (
            family[
                "semantic_clause"
            ]
        )

        for family
        in runtime_families
    }

    rows = []

    # ================================================================
    # SHARED RETRIEVAL + SHARED QUORUM ASSEMBLY
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

        routing = (
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
            routing[
                "candidate_family_ids"
            ]
        )

        if len(
            candidate_ids
        ) != 5:

            raise RuntimeError(
                "Seed 028 candidate geometry "
                f"violated for {family_id}."
            )

        query_text = (
            family[
                "query_prompt"
            ]
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

        full_order = (
            fused[
                "selected_family_ids"
            ]
        )

        boundary = (
            quorum_context_boundary(
                ordered_family_ids=(
                    full_order
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

        selected_ids = (
            boundary[
                "selected_family_ids"
            ]
        )

        (
            snapshot,
            snapshot_key,
        ) = (
            snapshot_for(
                selected_ids
            )
        )

        # ------------------------------------------------------------
        # CONDITION A — Current Seed 027 reasoning
        # ------------------------------------------------------------

        base_family = (
            evaluation_family(
                family
            )
        )

        base_eval = (
            evaluate_snapshot(
                snapshot_path=Path(
                    snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    eval_dir
                    /
                    (
                        "base_"
                        +
                        family_id
                        +
                        ".sqlite3"
                    )
                ),

                family=(
                    base_family
                ),

                model=model,
                embedder=embedder,
                meter=meter,

                clause_by_family=(
                    clause_by_family
                ),
            )
        )

        # ------------------------------------------------------------
        # CONDITION B — Same base query + fixed epistemic frame
        # ------------------------------------------------------------

        alternative_family = (
            apply_competing_hypothesis_frame(
                evaluation_family(
                    family
                )
            )
        )

        alternative_eval = (
            evaluate_snapshot(
                snapshot_path=Path(
                    snapshot[
                        "db_path"
                    ]
                ),

                eval_db_path=(
                    eval_dir
                    /
                    (
                        "alternative_"
                        +
                        family_id
                        +
                        ".sqlite3"
                    )
                ),

                family=(
                    alternative_family
                ),

                model=model,
                embedder=embedder,
                meter=meter,

                clause_by_family=(
                    clause_by_family
                ),
            )
        )

        # ------------------------------------------------------------
        # STRICT POST-HOC GRADING
        # ------------------------------------------------------------

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

        base_exclusive = (
            exclusive_decision_grade(
                decision_text=(
                    base_eval[
                        "transfer_decision"
                    ]
                ),

                target_signature=(
                    target_signature
                ),

                competing_signatures=(
                    competing_signatures
                ),
            )
        )

        alternative_exclusive = (
            exclusive_decision_grade(
                decision_text=(
                    alternative_eval[
                        "transfer_decision"
                    ]
                ),

                target_signature=(
                    target_signature
                ),

                competing_signatures=(
                    competing_signatures
                ),
            )
        )

        # ------------------------------------------------------------
        # CRITICAL PRESENTATION CONTROL
        # ------------------------------------------------------------

        memory_segments_equal = (
            base_eval[
                "memory_segments"
            ]
            ==
            alternative_eval[
                "memory_segments"
            ]
        )

        visible_family_ids_equal = (
            base_eval[
                "visible_family_ids"
            ]
            ==
            alternative_eval[
                "visible_family_ids"
            ]
        )

        memory_segment_count_equal = (
            base_eval[
                "memory_segment_count"
            ]
            ==
            alternative_eval[
                "memory_segment_count"
            ]
        )

        presentation_control_valid = (
            memory_segments_equal
            and
            visible_family_ids_equal
            and
            memory_segment_count_equal
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

                "semantic_operator": (
                    family[
                        "semantic_operator"
                    ]
                ),

                "semantic_dimension": (
                    family[
                        "semantic_dimension"
                    ]
                ),

                "query_prompt": (
                    family[
                        "query_prompt"
                    ]
                ),

                "query_entities": (
                    family[
                        "query_entities"
                    ]
                ),

                "routing": (
                    routing
                ),

                "channel_scores": (
                    local_raw[
                        "channel_scores"
                    ]
                ),

                "best_proposition_units": (
                    local_raw[
                        "best_units"
                    ]
                ),

                "fusion": (
                    fused
                ),

                "full_order": (
                    full_order
                ),

                "active_channels": (
                    fused[
                        "active_channels"
                    ]
                ),

                "active_channel_count": (
                    fused[
                        "active_channel_count"
                    ]
                ),

                "quorum_boundary": (
                    boundary
                ),

                "selected_family_ids": (
                    selected_ids
                ),

                "snapshot_key": (
                    snapshot_key
                ),

                "base": (
                    base_eval
                ),

                "alternative": (
                    alternative_eval
                ),

                "base_exclusive": (
                    base_exclusive
                ),

                "alternative_exclusive": (
                    alternative_exclusive
                ),

                "presentation_control": {
                    "memory_segments_equal": (
                        memory_segments_equal
                    ),

                    "visible_family_ids_equal": (
                        visible_family_ids_equal
                    ),

                    "memory_segment_count_equal": (
                        memory_segment_count_equal
                    ),

                    "valid": (
                        presentation_control_valid
                    ),
                },

                "paired": {
                    "exclusive_rescue": (
                        (
                            not
                            base_exclusive[
                                "exclusive_correct_pass"
                            ]
                        )
                        and
                        alternative_exclusive[
                            "exclusive_correct_pass"
                        ]
                    ),

                    "exclusive_harm": (
                        base_exclusive[
                            "exclusive_correct_pass"
                        ]
                        and
                        (
                            not
                            alternative_exclusive[
                                "exclusive_correct_pass"
                            ]
                        )
                    ),

                    "target_rule_rescue": (
                        (
                            not
                            base_exclusive[
                                "target_rule_present"
                            ]
                        )
                        and
                        alternative_exclusive[
                            "target_rule_present"
                        ]
                    ),

                    "target_rule_harm": (
                        base_exclusive[
                            "target_rule_present"
                        ]
                        and
                        (
                            not
                            alternative_exclusive[
                                "target_rule_present"
                            ]
                        )
                    ),

                    "competing_rule_hit_delta": (
                        alternative_exclusive[
                            "competing_rule_hit_count"
                        ]
                        -
                        base_exclusive[
                            "competing_rule_hit_count"
                        ]
                    ),

                    "semantic_task_delta": (
                        int(
                            alternative_eval[
                                "semantic_task_pass"
                            ]
                        )
                        -
                        int(
                            base_eval[
                                "semantic_task_pass"
                            ]
                        )
                    ),
                },
            }
        )

    # ================================================================
    # AGGREGATE
    # ================================================================

    task_count = len(
        rows
    )

    presentation_valid_rows = [
        row

        for row
        in rows

        if row[
            "presentation_control"
        ][
            "valid"
        ]
    ]

    multi_memory_rows = [
        row

        for row
        in rows

        if (
            row[
                "presentation_control"
            ][
                "valid"
            ]
            and
            row[
                "base"
            ][
                "memory_segment_count"
            ]
            > 1
        )
    ]

    active_channel_distribution = (
        Counter(
            row[
                "active_channel_count"
            ]

            for row
            in rows
        )
    )

    context_k_distribution = (
        Counter(
            len(
                row[
                    "selected_family_ids"
                ]
            )

            for row
            in rows
        )
    )

    report = {
        "experiment": (
            "seed-growth-028"
        ),

        "classification": (
            "exploratory-fresh-competing-"
            "hypothesis-reasoning-ablation"
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
            type(model).__name__,
        ),

        "embedder": getattr(
            embedder,
            "name",
            type(embedder).__name__,
        ),

        "meter": getattr(
            meter,
            "name",
            type(meter).__name__,
        ),

        "task_count": (
            task_count
        ),

        "pool_size": (
            len(
                runtime_families
            )
        ),

        "candidate_neighborhood_size": 5,

        "top_k": (
            TOP_K
        ),

        "rrf_k": (
            RRF_K
        ),

        "min_active_channels_for_pruning": (
            MIN_ACTIVE_CHANNELS
        ),

        "conditions": {
            "A": (
                "seed_027_standard_reasoning"
            ),

            "B": (
                "same_base_query_plus_competing_"
                "hypothesis_epistemic_instruction"
            ),
        },

        # ------------------------------------------------------------
        # MECHANISM EXERCISE
        # ------------------------------------------------------------

        "active_channel_count_distribution": {
            str(
                count
            ): (
                active_channel_distribution[
                    count
                ]
            )

            for count
            in sorted(
                active_channel_distribution
            )
        },

        "context_k_distribution": {
            str(k): (
                context_k_distribution[
                    k
                ]
            )

            for k
            in (
                1,
                2,
                3,
            )
        },

        "multi_memory_context_families": (
            len(
                multi_memory_rows
            )
        ),

        "single_memory_context_families": (
            sum(
                int(
                    row[
                        "base"
                    ][
                        "memory_segment_count"
                    ]
                    == 1
                )

                for row
                in presentation_valid_rows
            )
        ),

        # ------------------------------------------------------------
        # STRICT EXCLUSIVE METRICS
        # ------------------------------------------------------------

        "base_exclusive_correct_passes": (
            _count_grade(
                rows,
                "base",
                "exclusive_correct_pass",
            )
        ),

        "alternative_exclusive_correct_passes": (
            _count_grade(
                rows,
                "alternative",
                "exclusive_correct_pass",
            )
        ),

        "base_target_rule_present_families": (
            _count_grade(
                rows,
                "base",
                "target_rule_present",
            )
        ),

        "alternative_target_rule_present_families": (
            _count_grade(
                rows,
                "alternative",
                "target_rule_present",
            )
        ),

        "base_competing_rule_mention_families": sum(
            int(
                row[
                    "base_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "alternative_competing_rule_mention_families": sum(
            int(
                row[
                    "alternative_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in rows
        ),

        "base_total_competing_rule_hits": sum(
            int(
                row[
                    "base_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
            )

            for row
            in rows
        ),

        "alternative_total_competing_rule_hits": sum(
            int(
                row[
                    "alternative_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
            )

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
                    "target_rule_rescue"
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
                    "target_rule_harm"
                ]
            )

            for row
            in rows
        ),

        # ------------------------------------------------------------
        # STRICT METRICS — MULTI-MEMORY ONLY
        # ------------------------------------------------------------

        "multi_memory_base_exclusive_passes": sum(
            int(
                row[
                    "base_exclusive"
                ][
                    "exclusive_correct_pass"
                ]
            )

            for row
            in multi_memory_rows
        ),

        "multi_memory_alternative_exclusive_passes": sum(
            int(
                row[
                    "alternative_exclusive"
                ][
                    "exclusive_correct_pass"
                ]
            )

            for row
            in multi_memory_rows
        ),

        "multi_memory_base_competing_rule_mention_families": sum(
            int(
                row[
                    "base_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in multi_memory_rows
        ),

        "multi_memory_alternative_competing_rule_mention_families": sum(
            int(
                row[
                    "alternative_exclusive"
                ][
                    "competing_rule_hit_count"
                ]
                > 0
            )

            for row
            in multi_memory_rows
        ),

        # ------------------------------------------------------------
        # LEGACY SEMANTIC GRADER — SECONDARY
        # ------------------------------------------------------------

        "base_semantic_task_passes": (
            _count_eval(
                rows,
                "base",
                "semantic_task_pass",
            )
        ),

        "alternative_semantic_task_passes": (
            _count_eval(
                rows,
                "alternative",
                "semantic_task_pass",
            )
        ),

        "base_semantic_violation_families": (
            _count_eval(
                rows,
                "base",
                "semantic_violation",
            )
        ),

        "alternative_semantic_violation_families": (
            _count_eval(
                rows,
                "alternative",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # MEMORY / CONTEXT CONTROLS
        # ------------------------------------------------------------

        "presentation_control_valid_families": (
            len(
                presentation_valid_rows
            )
        ),

        "presentation_control_invalid_families": (
            task_count
            -
            len(
                presentation_valid_rows
            )
        ),

        "all_memory_segments_equal_between_conditions": all(
            row[
                "presentation_control"
            ][
                "memory_segments_equal"
            ]

            for row
            in rows
        ),

        "all_visible_family_ids_equal_between_conditions": all(
            row[
                "presentation_control"
            ][
                "visible_family_ids_equal"
            ]

            for row
            in rows
        ),

        "all_memory_segment_counts_equal_between_conditions": all(
            row[
                "presentation_control"
            ][
                "memory_segment_count_equal"
            ]

            for row
            in rows
        ),

        "presentation_causal_interpretation_valid": all(
            row[
                "presentation_control"
            ][
                "valid"
            ]

            for row
            in rows
        ),

        # ------------------------------------------------------------
        # CLUSTERS
        # ------------------------------------------------------------

        "base_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="base",
            )
        ),

        "alternative_cluster_metrics": (
            _aggregate_cluster_metrics(
                rows,
                condition="alternative",
            )
        ),

        # ------------------------------------------------------------
        # SAFETY
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # CONTROLS
        # ------------------------------------------------------------

        "all_candidate_routes_shared_between_conditions": True,

        "all_memory_bundles_shared_between_conditions": True,

        "all_source_evidence_shared_between_conditions": True,

        "all_proposition_units_shared_between_conditions": True,

        "all_channel_scores_shared_between_conditions": True,

        "all_channel_abstentions_shared_between_conditions": True,

        "all_fused_rankings_shared_between_conditions": True,

        "all_quorum_boundaries_shared_between_conditions": True,

        "all_selected_family_ids_shared_between_conditions": True,

        "all_snapshot_keys_shared_between_conditions": True,

        "same_base_transfer_question_between_conditions": True,

        "same_reasoner_between_conditions": True,

        "same_context_budget_configuration": True,

        "only_epistemic_reasoning_frame_differs": True,

        "exclusive_grader_model_calls": 0,

        "ranker_model_calls": 0,

        "assembler_model_calls": 0,

        "reasoner_calls_condition_a": (
            task_count
        ),

        "reasoner_calls_condition_b": (
            task_count
        ),

        "total_reasoner_calls": (
            task_count
            *
            2
        ),

        "strict_grader_metadata_removed_before_runtime": True,

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
            "experiments/"
            "tasks_028.json"
        ),
    )

    parser.add_argument(
        "--results",
        default=(
            "experiments/"
            "results"
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
        run_experiment_028(
            tasks_path=Path(
                args.tasks
            ),

            results_dir=Path(
                args.results
            ),

            model=model,
            embedder=embedder,
            meter=WordMeter(),
        )
    )

    keys = (
        "experiment",
        "taskset_sha256",

        "active_channel_count_distribution",
        "context_k_distribution",

        "multi_memory_context_families",
        "single_memory_context_families",

        "base_exclusive_correct_passes",
        "alternative_exclusive_correct_passes",

        "base_target_rule_present_families",
        "alternative_target_rule_present_families",

        "base_competing_rule_mention_families",
        "alternative_competing_rule_mention_families",

        "base_total_competing_rule_hits",
        "alternative_total_competing_rule_hits",

        "exclusive_rescue_families",
        "exclusive_harm_families",

        "target_rule_rescue_families",
        "target_rule_harm_families",

        "multi_memory_base_exclusive_passes",
        "multi_memory_alternative_exclusive_passes",

        "multi_memory_base_competing_rule_mention_families",
        "multi_memory_alternative_competing_rule_mention_families",

        "base_semantic_task_passes",
        "alternative_semantic_task_passes",

        "presentation_control_valid_families",
        "presentation_control_invalid_families",

        "all_memory_segments_equal_between_conditions",
        "all_visible_family_ids_equal_between_conditions",
        "all_memory_segment_counts_equal_between_conditions",

        "presentation_causal_interpretation_valid",

        "base_cluster_metrics",
        "alternative_cluster_metrics",

        "bundle_unsupported_claims_admitted",

        "all_candidate_routes_shared_between_conditions",
        "all_memory_bundles_shared_between_conditions",
        "all_source_evidence_shared_between_conditions",
        "all_proposition_units_shared_between_conditions",
        "all_channel_scores_shared_between_conditions",
        "all_channel_abstentions_shared_between_conditions",
        "all_fused_rankings_shared_between_conditions",
        "all_quorum_boundaries_shared_between_conditions",
        "all_selected_family_ids_shared_between_conditions",
        "all_snapshot_keys_shared_between_conditions",

        "same_base_transfer_question_between_conditions",
        "same_reasoner_between_conditions",

        "only_epistemic_reasoning_frame_differs",

        "exclusive_grader_model_calls",
        "ranker_model_calls",
        "assembler_model_calls",
        "total_reasoner_calls",
    )

    summary = {
        key: report[
            key
        ]

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
