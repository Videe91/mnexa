from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil

from collections import defaultdict

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


from experiments.seed_growth_004 import (
    make_fidelity_reasoner,
)

from experiments.seed_growth_011 import (
    admit_structured_propositions,
)

from experiments.seed_growth_013 import (
    _build_repaired_structure,
    _claim_audit,
    _controlled_candidate_reasoner,
    semantic_clause_visible,
    semantic_grade,
)

from experiments.seed_growth_014 import (
    ensure_fallback_challenges,
    reconcile_support_first,
)

from experiments.seed_growth_015 import (
    compact_semantic_projection,
    render_compact_semantic_memory,
)

from mnexa_seed import (
    MnexaSeed,
)


def _sha256_text(
    text: str,
) -> str:

    return (
        hashlib
        .sha256(
            text.encode(
                "utf-8"
            )
        )
        .hexdigest()
    )


def _sha256_json(
    payload,
) -> str:

    return _sha256_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )
    )


def _sha256_file(
    path: Path,
) -> str:

    digest = (
        hashlib.sha256()
    )

    with Path(
        path
    ).open(
        "rb"
    ) as handle:

        while True:

            chunk = (
                handle.read(
                    1024 * 1024
                )
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return (
        digest.hexdigest()
    )


def _normalize(
    text: str,
) -> str:

    return " ".join(
        text.lower().split()
    )


def evaluation_db_name(
    *,
    condition: str,
    family_id: str,
) -> str:

    safe_family = (
        family_id
        .replace(
            "/",
            "-"
        )
    )

    return (
        f"eval_{condition}_"
        f"{safe_family}.sqlite3"
    )


def analyze_model_visible_memory(
    *,
    memory_segments,
    target_family_id: str,
    clause_by_family,
):
    """
    Exact-clause analysis of the model-visible memory returned by the
    current MNEXA decision pipeline.

    In this experiment, `memory_segments` are the memories that became
    available to the reasoner.

    Since there is exactly one relevant family per transfer query:

        recall = 1 if target semantic clause is visible else 0

        precision =
            target visible / number of identifiable family clauses
            visible in context

    This is deliberately narrow. It does not claim semantic detection
    of paraphrased distractors.
    """

    context = _normalize(
        "\n".join(
            memory_segments
        )
    )

    visible_family_ids = []

    for family_id, clause in (
        clause_by_family.items()
    ):

        if (
            _normalize(
                clause
            )
            in
            context
        ):

            visible_family_ids.append(
                family_id
            )

    target_visible = (
        target_family_id
        in
        visible_family_ids
    )

    wrong_family_ids = [
        family_id

        for family_id
        in visible_family_ids

        if (
            family_id
            !=
            target_family_id
        )
    ]

    identifiable = (
        len(
            visible_family_ids
        )
    )

    if (
        target_visible
        and
        identifiable
    ):

        precision = (
            1.0
            /
            identifiable
        )

    else:

        precision = 0.0

    return {
        "target_clause_visible": (
            target_visible
        ),

        "visible_family_ids": (
            visible_family_ids
        ),

        "wrong_family_ids": (
            wrong_family_ids
        ),

        "wrong_family_clause_count": (
            len(
                wrong_family_ids
            )
        ),

        "identifiable_family_clause_count": (
            identifiable
        ),

        "retrieval_recall": (
            1.0
            if target_visible
            else 0.0
        ),

        "retrieval_precision": (
            precision
        ),
    }


def analyze_decision_contamination(
    *,
    decision_text: str,
    target_family_id: str,
    clause_by_family,
):
    """
    Narrow exact-clause contamination metric.

    This records only exact wrong-family clauses emitted in the final
    decision. It intentionally does not claim to detect all possible
    semantic paraphrases.
    """

    normalized = (
        _normalize(
            decision_text
        )
    )

    wrong_family_ids = []

    for family_id, clause in (
        clause_by_family.items()
    ):

        if (
            family_id
            ==
            target_family_id
        ):
            continue

        if (
            _normalize(
                clause
            )
            in
            normalized
        ):

            wrong_family_ids.append(
                family_id
            )

    return {
        "wrong_rule_contamination": (
            bool(
                wrong_family_ids
            )
        ),

        "wrong_family_ids": (
            wrong_family_ids
        ),

        "wrong_family_clause_count": (
            len(
                wrong_family_ids
            )
        ),
    }


def classify_paired_regret(
    *,
    isolated_pass: bool,
    pooled_pass: bool,
    pooled_target_visible: bool,
    pooled_wrong_family_clause_count: int,
):
    """
    Paired interference regret.

    The target knowledge exists in both conditions.

    Therefore:

        isolated passes
        pooled fails

    is the narrow behavioral signal that adding other accumulated
    memories harmed the result.
    """

    regret = (
        isolated_pass
        and
        not pooled_pass
    )

    return {
        "retrieval_regret": (
            regret
        ),

        "target_omission_regret": (
            regret
            and
            not pooled_target_visible
        ),

        "contamination_regret": (
            regret
            and
            pooled_wrong_family_clause_count
            > 0
        ),
    }


def aggregate_cluster_metrics(
    rows,
    condition,
):
    grouped = defaultdict(
        lambda: {
            "families": 0,
            "task_passes": 0,
            "target_visible_families": 0,
            "wrong_family_clause_occurrences": 0,
            "families_with_wrong_memory": 0,
            "precision_sum": 0.0,
            "recall_sum": 0.0,
        }
    )

    for row in rows:

        cluster = (
            row[
                "interference_cluster"
            ]
        )

        metrics = (
            row[
                condition
            ]
        )

        bucket = (
            grouped[
                cluster
            ]
        )

        bucket[
            "families"
        ] += 1

        bucket[
            "task_passes"
        ] += int(
            metrics[
                "semantic_task_pass"
            ]
        )

        bucket[
            "target_visible_families"
        ] += int(
            metrics[
                "target_clause_visible"
            ]
        )

        bucket[
            "wrong_family_clause_occurrences"
        ] += int(
            metrics[
                "wrong_family_clause_count"
            ]
        )

        bucket[
            "families_with_wrong_memory"
        ] += int(
            metrics[
                "wrong_family_clause_count"
            ]
            > 0
        )

        bucket[
            "precision_sum"
        ] += float(
            metrics[
                "retrieval_precision"
            ]
        )

        bucket[
            "recall_sum"
        ] += float(
            metrics[
                "retrieval_recall"
            ]
        )

    result = {}

    for cluster, bucket in sorted(
        grouped.items()
    ):

        families = (
            bucket[
                "families"
            ]
        )

        result[
            cluster
        ] = {
            "families": (
                families
            ),

            "task_passes": (
                bucket[
                    "task_passes"
                ]
            ),

            "task_pass_rate": (
                bucket[
                    "task_passes"
                ]
                /
                families
                if families
                else 0.0
            ),

            "target_visible_families": (
                bucket[
                    "target_visible_families"
                ]
            ),

            "wrong_family_clause_occurrences": (
                bucket[
                    "wrong_family_clause_occurrences"
                ]
            ),

            "families_with_wrong_memory": (
                bucket[
                    "families_with_wrong_memory"
                ]
            ),

            "mean_retrieval_precision": (
                bucket[
                    "precision_sum"
                ]
                /
                families
                if families
                else 0.0
            ),

            "mean_retrieval_recall": (
                bucket[
                    "recall_sum"
                ]
                /
                families
                if families
                else 0.0
            ),
        }

    return result


def build_memory_bundle(
    *,
    family,
    model,
):
    """
    Build the compact, lossless memory for one family exactly once.

    The exact same lesson text is later learned into:

        A. the isolated snapshot
        B. the pooled snapshot
    """

    source_text = (
        family[
            "raw_source"
        ]
    )

    repair_run = (
        _build_repaired_structure(
            family=family,
            model=model,
        )
    )

    (
        shared_repair_proposal,
        fallback_challenge_ids,
    ) = (
        ensure_fallback_challenges(
            repair_payload=(
                repair_run[
                    "repair_payload"
                ]
            ),
            family=family,
        )
    )

    structured_gate = (
        admit_structured_propositions(
            proposal=(
                shared_repair_proposal
            ),
            source_text=(
                source_text
            ),
        )
    )

    reconciled = (
        reconcile_support_first(
            proposal=(
                shared_repair_proposal
            ),
            source_text=(
                source_text
            ),
            structured_gate=(
                structured_gate
            ),
        )
    )

    structured = (
        reconciled[
            "structured"
        ]
    )

    fallback = (
        reconciled[
            "fallback"
        ]
    )

    lesson_text = (
        render_compact_semantic_memory(
            structured=structured,
            fallback=fallback,
        )
    )

    evidence_atoms = (
        compact_semantic_projection(
            structured=structured,
            fallback=fallback,
        )
    )

    claim_audit = (
        _claim_audit(
            evidence_atoms
        )
    )

    return {
        "family_id": (
            family[
                "id"
            ]
        ),

        "lesson_text": (
            lesson_text
        ),

        "lesson_sha256": (
            _sha256_text(
                lesson_text
            )
        ),

        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),

        "repair_proposal_sha256": (
            _sha256_json(
                shared_repair_proposal
            )
        ),

        "structured_sha256": (
            _sha256_json(
                structured
            )
        ),

        "fallback_sha256": (
            _sha256_json(
                fallback
            )
        ),

        "fallback_challenge_ids": (
            fallback_challenge_ids
        ),

        "structured": (
            structured
        ),

        "fallback": (
            fallback
        ),

        "evidence_atoms": (
            evidence_atoms
        ),

        "semantic_clause_visible": (
            semantic_clause_visible(
                lesson_text,
                family[
                    "semantic_clause"
                ],
            )
        ),

        "unsupported_claims_admitted": (
            claim_audit[
                "unsupported_claims_admitted"
            ]
        ),

        "initial_raw_response": (
            repair_run[
                "initial_raw_response"
            ]
        ),

        "repair_raw_response": (
            repair_run[
                "repair_raw_response"
            ]
        ),
    }


def _source_evidence_text(
    *,
    candidate_decision: str,
    raw_source: str,
) -> str:

    outcome_text = (
        "EVALUATION RECORD:\n"
        +
        raw_source
    )

    return (
        "DECISION: "
        +
        candidate_decision
        +
        "\nOUTCOME: "
        +
        outcome_text
    )


def learn_family_into_seed(
    *,
    seed,
    family,
    bundle,
):
    """
    Materialize a pre-built compact lesson into a MnexaSeed state.

    No extraction or repair model call occurs here.
    """

    first_decision = (
        seed.decide(
            family[
                "experience"
            ][
                "prompt"
            ],
            tuple(
                family[
                    "entities"
                ]
            ),
            _controlled_candidate_reasoner(
                family[
                    "candidate_decision"
                ]
            ),
        )
    )

    if (
        first_decision.text
        !=
        family[
            "candidate_decision"
        ]
    ):

        raise RuntimeError(
            "Controlled candidate decision changed."
        )

    outcome_text = (
        "EVALUATION RECORD:\n"
        +
        family[
            "raw_source"
        ]
    )

    outcome = (
        seed.observe_outcome(
            first_decision.record_id,
            outcome_text,
            success=False,
        )
    )

    def consolidator(
        evidence: str,
    ) -> str:

        return (
            bundle[
                "lesson_text"
            ]
        )

    lesson = (
        seed.consolidate(
            first_decision.record_id,
            consolidator,
        )
    )

    if (
        lesson.text
        !=
        bundle[
            "lesson_text"
        ]
    ):

        raise RuntimeError(
            "Snapshot lesson differs from frozen "
            "memory bundle."
        )

    source_evidence = (
        _source_evidence_text(
            candidate_decision=(
                first_decision.text
            ),
            raw_source=(
                family[
                    "raw_source"
                ]
            ),
        )
    )

    return {
        "decision_id": (
            first_decision.record_id
        ),

        "outcome_id": (
            outcome.object_id
        ),

        "lesson_id": (
            lesson.object_id
        ),

        "lesson_sha256": (
            _sha256_text(
                lesson.text
            )
        ),

        "source_evidence_sha256": (
            _sha256_text(
                source_evidence
            )
        ),
    }


def build_memory_snapshot(
    *,
    db_path: Path,
    families,
    bundles,
    embedder,
    meter,
):
    db_path = Path(
        db_path
    )

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if db_path.exists():
        db_path.unlink()

    seed = (
        MnexaSeed(
            db_path,
            embedder=embedder,
            meter=meter,
        )
    )

    learned = []

    try:

        for family in families:

            learned.append(
                {
                    "family_id": (
                        family[
                            "id"
                        ]
                    ),

                    **learn_family_into_seed(
                        seed=seed,
                        family=family,
                        bundle=(
                            bundles[
                                family[
                                    "id"
                                ]
                            ]
                        ),
                    ),
                }
            )

        watermark = (
            seed.watermark()
        )

    finally:

        seed.close()

    return {
        "db_path": (
            str(
                db_path
            )
        ),

        "snapshot_sha256": (
            _sha256_file(
                db_path
            )
        ),

        "watermark": (
            watermark
        ),

        "memory_count": (
            len(
                families
            )
        ),

        "learned": (
            learned
        ),
    }


def evaluate_snapshot(
    *,
    snapshot_path: Path,
    eval_db_path: Path,
    family,
    model,
    embedder,
    meter,
    clause_by_family,
):
    """
    Copy a closed pre-evaluation SQLite snapshot.

    Evaluation therefore writes only to its private copy.
    """

    snapshot_path = Path(
        snapshot_path
    )

    eval_db_path = Path(
        eval_db_path
    )

    eval_db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if eval_db_path.exists():
        eval_db_path.unlink()

    snapshot_sha256 = (
        _sha256_file(
            snapshot_path
        )
    )

    shutil.copy2(
        snapshot_path,
        eval_db_path,
    )

    copied_sha256 = (
        _sha256_file(
            eval_db_path
        )
    )

    if (
        copied_sha256
        !=
        snapshot_sha256
    ):

        raise RuntimeError(
            "Evaluation snapshot copy changed bytes."
        )

    seed = (
        MnexaSeed(
            eval_db_path,
            embedder=embedder,
            meter=meter,
        )
    )

    try:

        pre_eval_watermark = (
            seed.watermark()
        )

        transfer = (
            seed.decide(
                family[
                    "transfer"
                ][
                    "prompt"
                ],
                tuple(
                    family[
                        "entities"
                    ]
                ),
                make_fidelity_reasoner(
                    model
                ),
            )
        )

        post_eval_watermark = (
            seed.watermark()
        )

        semantic = (
            semantic_grade(
                transfer.text,
                family[
                    "semantic_grader"
                ],
            )
        )

        visible = (
            analyze_model_visible_memory(
                memory_segments=(
                    transfer.memory_segments
                ),
                target_family_id=(
                    family[
                        "id"
                    ]
                ),
                clause_by_family=(
                    clause_by_family
                ),
            )
        )

        contamination = (
            analyze_decision_contamination(
                decision_text=(
                    transfer.text
                ),
                target_family_id=(
                    family[
                        "id"
                    ]
                ),
                clause_by_family=(
                    clause_by_family
                ),
            )
        )

        memory_text = "\n".join(
            transfer.memory_segments
        )

        return {
            "snapshot_sha256": (
                snapshot_sha256
            ),

            "copied_snapshot_sha256": (
                copied_sha256
            ),

            "pre_eval_watermark": (
                pre_eval_watermark
            ),

            "post_eval_watermark": (
                post_eval_watermark
            ),

            "transfer_decision": (
                transfer.text
            ),

            "semantic_task_pass": (
                semantic[
                    "passed"
                ]
            ),

            "semantic_violation": (
                semantic[
                    "violation"
                ]
            ),

            "semantic_required_ok": (
                semantic[
                    "required_ok"
                ]
            ),

            "semantic_forbidden_hits": (
                semantic[
                    "forbidden_hits"
                ]
            ),

            "memory_segments": list(
                transfer.memory_segments
            ),

            "memory_segment_count": (
                len(
                    transfer.memory_segments
                )
            ),

            "memory_word_count": (
                meter.count(
                    memory_text
                )
            ),

            **visible,

            "wrong_rule_contamination": (
                contamination[
                    "wrong_rule_contamination"
                ]
            ),

            "wrong_rule_family_ids": (
                contamination[
                    "wrong_family_ids"
                ]
            ),

            "wrong_rule_clause_count": (
                contamination[
                    "wrong_family_clause_count"
                ]
            ),
        }

    finally:

        seed.close()


def run_family_pair(
    *,
    family,
    isolated_snapshot,
    pooled_snapshot,
    eval_dir: Path,
    model,
    embedder,
    meter,
    clause_by_family,
):
    family_id = (
        family[
            "id"
        ]
    )

    isolated = (
        evaluate_snapshot(
            snapshot_path=Path(
                isolated_snapshot[
                    "db_path"
                ]
            ),
            eval_db_path=(
                Path(
                    eval_dir
                )
                /
                evaluation_db_name(
                    condition=(
                        "isolated"
                    ),
                    family_id=(
                        family_id
                    ),
                )
            ),
            family=family,
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )
    )

    pooled = (
        evaluate_snapshot(
            snapshot_path=Path(
                pooled_snapshot[
                    "db_path"
                ]
            ),
            eval_db_path=(
                Path(
                    eval_dir
                )
                /
                evaluation_db_name(
                    condition=(
                        "pooled"
                    ),
                    family_id=(
                        family_id
                    ),
                )
            ),
            family=family,
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )
    )

    regret = (
        classify_paired_regret(
            isolated_pass=(
                isolated[
                    "semantic_task_pass"
                ]
            ),
            pooled_pass=(
                pooled[
                    "semantic_task_pass"
                ]
            ),
            pooled_target_visible=(
                pooled[
                    "target_clause_visible"
                ]
            ),
            pooled_wrong_family_clause_count=(
                pooled[
                    "wrong_family_clause_count"
                ]
            ),
        )
    )

    return {
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

        "semantic_clause": (
            family[
                "semantic_clause"
            ]
        ),

        "pool_position": (
            family[
                "pool_position"
            ]
        ),

        "distractor_count": (
            len(
                family[
                    "distractor_family_ids"
                ]
            )
        ),

        "near_neighbor_count": (
            len(
                family[
                    "near_neighbor_family_ids"
                ]
            )
        ),

        "isolated": (
            isolated
        ),

        "pooled": (
            pooled
        ),

        "paired": {
            **regret,

            "task_delta": (
                int(
                    pooled[
                        "semantic_task_pass"
                    ]
                )
                -
                int(
                    isolated[
                        "semantic_task_pass"
                    ]
                )
            ),

            "retrieval_precision_delta": (
                pooled[
                    "retrieval_precision"
                ]
                -
                isolated[
                    "retrieval_precision"
                ]
            ),

            "retrieval_recall_delta": (
                pooled[
                    "retrieval_recall"
                ]
                -
                isolated[
                    "retrieval_recall"
                ]
            ),

            "memory_word_delta": (
                pooled[
                    "memory_word_count"
                ]
                -
                isolated[
                    "memory_word_count"
                ]
            ),
        },
    }


def _count(
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


def _sum(
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


def run_experiment_017(
    *,
    tasks_path: Path,
    results_dir: Path,
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

    families = (
        payload[
            "families"
        ]
    )

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

    state_dir = (
        run_dir
        /
        "state"
    )

    snapshot_dir = (
        state_dir
        /
        "snapshots"
    )

    eval_dir = (
        state_dir
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
    # STEP 1 — BUILD EACH LEARNED MEMORY ONCE
    # ================================================================

    bundles = {}

    for family in families:

        bundle = (
            build_memory_bundle(
                family=family,
                model=model,
            )
        )

        bundles[
            family[
                "id"
            ]
        ] = (
            bundle
        )

    # ================================================================
    # STEP 2 — BUILD ONE POOLED PRE-EVALUATION SNAPSHOT
    #
    # No evaluation writes to this database.
    # ================================================================

    pooled_snapshot = (
        build_memory_snapshot(
            db_path=(
                snapshot_dir
                /
                "pooled_base.sqlite3"
            ),
            families=(
                families
            ),
            bundles=(
                bundles
            ),
            embedder=embedder,
            meter=meter,
        )
    )

    # ================================================================
    # STEP 3 — BUILD ONE ISOLATED PRE-EVALUATION SNAPSHOT PER TARGET
    # ================================================================

    isolated_snapshots = {}

    for family in families:

        family_id = (
            family[
                "id"
            ]
        )

        isolated_snapshots[
            family_id
        ] = (
            build_memory_snapshot(
                db_path=(
                    snapshot_dir
                    /
                    (
                        "isolated_"
                        +
                        family_id
                        +
                        ".sqlite3"
                    )
                ),
                families=[
                    family
                ],
                bundles=(
                    bundles
                ),
                embedder=embedder,
                meter=meter,
            )
        )

    # ================================================================
    # STEP 4 — FROZEN PAIRED EVALUATIONS
    # ================================================================

    clause_by_family = {
        family[
            "id"
        ]: (
            family[
                "semantic_clause"
            ]
        )

        for family
        in families
    }

    results = [
        run_family_pair(
            family=family,
            isolated_snapshot=(
                isolated_snapshots[
                    family[
                        "id"
                    ]
                ]
            ),
            pooled_snapshot=(
                pooled_snapshot
            ),
            eval_dir=(
                eval_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            clause_by_family=(
                clause_by_family
            ),
        )

        for family
        in families
    ]

    family_count = (
        len(
            results
        )
    )

    isolated_passes = (
        _count(
            results,
            "isolated",
            "semantic_task_pass",
        )
    )

    pooled_passes = (
        _count(
            results,
            "pooled",
            "semantic_task_pass",
        )
    )

    retrieval_regret = sum(
        int(
            row[
                "paired"
            ][
                "retrieval_regret"
            ]
        )

        for row
        in results
    )

    omission_regret = sum(
        int(
            row[
                "paired"
            ][
                "target_omission_regret"
            ]
        )

        for row
        in results
    )

    contamination_regret = sum(
        int(
            row[
                "paired"
            ][
                "contamination_regret"
            ]
        )

        for row
        in results
    )

    pooled_hash = (
        pooled_snapshot[
            "snapshot_sha256"
        ]
    )

    report = {
        "experiment": (
            "seed-growth-017"
        ),

        "classification": (
            "exploratory-fresh-pooled-memory-"
            "interference-ablation"
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

        "embedder": getattr(
            embedder,
            "name",
            type(
                embedder
            ).__name__,
        ),

        "meter": getattr(
            meter,
            "name",
            type(
                meter
            ).__name__,
        ),

        "task_count": (
            family_count
        ),

        "pool_size": (
            len(
                families
            )
        ),

        "distractors_per_target": (
            len(
                families
            )
            -
            1
        ),

        "near_neighbors_per_target": (
            payload[
                "near_neighbors_per_target"
            ]
        ),

        "conditions": {
            "A": (
                "isolated_compact_memory_target_only"
            ),

            "B": (
                "pooled_compact_memory_target_plus_"
                "nineteen_distractors"
            ),
        },

        # ------------------------------------------------------------
        # Behavioral performance
        # ------------------------------------------------------------

        "isolated_task_passes": (
            isolated_passes
        ),

        "pooled_task_passes": (
            pooled_passes
        ),

        "isolated_task_pass_rate": (
            isolated_passes
            /
            family_count
            if family_count
            else 0.0
        ),

        "pooled_task_pass_rate": (
            pooled_passes
            /
            family_count
            if family_count
            else 0.0
        ),

        "isolated_semantic_violations": (
            _count(
                results,
                "isolated",
                "semantic_violation",
            )
        ),

        "pooled_semantic_violations": (
            _count(
                results,
                "pooled",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # Model-visible retrieval
        # ------------------------------------------------------------

        "isolated_target_clause_visible_families": (
            _count(
                results,
                "isolated",
                "target_clause_visible",
            )
        ),

        "pooled_target_clause_visible_families": (
            _count(
                results,
                "pooled",
                "target_clause_visible",
            )
        ),

        "isolated_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "isolated"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in results
        ),

        "pooled_families_with_wrong_memory_presented": sum(
            int(
                row[
                    "pooled"
                ][
                    "wrong_family_clause_count"
                ]
                > 0
            )

            for row
            in results
        ),

        "isolated_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "isolated",
                "wrong_family_clause_count",
            )
        ),

        "pooled_wrong_family_clause_occurrences": int(
            _sum(
                results,
                "pooled",
                "wrong_family_clause_count",
            )
        ),

        "mean_isolated_retrieval_precision": (
            _mean(
                row[
                    "isolated"
                ][
                    "retrieval_precision"
                ]

                for row
                in results
            )
        ),

        "mean_pooled_retrieval_precision": (
            _mean(
                row[
                    "pooled"
                ][
                    "retrieval_precision"
                ]

                for row
                in results
            )
        ),

        "mean_isolated_retrieval_recall": (
            _mean(
                row[
                    "isolated"
                ][
                    "retrieval_recall"
                ]

                for row
                in results
            )
        ),

        "mean_pooled_retrieval_recall": (
            _mean(
                row[
                    "pooled"
                ][
                    "retrieval_recall"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # Final-decision contamination
        # ------------------------------------------------------------

        "isolated_wrong_rule_contamination_families": (
            _count(
                results,
                "isolated",
                "wrong_rule_contamination",
            )
        ),

        "pooled_wrong_rule_contamination_families": (
            _count(
                results,
                "pooled",
                "wrong_rule_contamination",
            )
        ),

        # ------------------------------------------------------------
        # Retrieval regret
        # ------------------------------------------------------------

        "paired_retrieval_regret_families": (
            retrieval_regret
        ),

        "paired_target_omission_regret_families": (
            omission_regret
        ),

        "paired_contamination_regret_families": (
            contamination_regret
        ),

        # ------------------------------------------------------------
        # Context cost
        # ------------------------------------------------------------

        "mean_isolated_memory_words": (
            _mean(
                row[
                    "isolated"
                ][
                    "memory_word_count"
                ]

                for row
                in results
            )
        ),

        "mean_pooled_memory_words": (
            _mean(
                row[
                    "pooled"
                ][
                    "memory_word_count"
                ]

                for row
                in results
            )
        ),

        "mean_isolated_memory_segments": (
            _mean(
                row[
                    "isolated"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        "mean_pooled_memory_segments": (
            _mean(
                row[
                    "pooled"
                ][
                    "memory_segment_count"
                ]

                for row
                in results
            )
        ),

        # ------------------------------------------------------------
        # Cluster analysis
        # ------------------------------------------------------------

        "isolated_cluster_metrics": (
            aggregate_cluster_metrics(
                results,
                "isolated",
            )
        ),

        "pooled_cluster_metrics": (
            aggregate_cluster_metrics(
                results,
                "pooled",
            )
        ),

        # ------------------------------------------------------------
        # Learning / safety
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
        # Resource accounting
        # ------------------------------------------------------------

        "initial_extraction_model_calls": (
            family_count
        ),

        "repair_model_calls": (
            family_count
        ),

        "isolated_transfer_model_calls": (
            family_count
        ),

        "pooled_transfer_model_calls": (
            family_count
        ),

        "snapshot_construction_model_calls": 0,

        # ------------------------------------------------------------
        # Strict controls
        # ------------------------------------------------------------

        "all_target_lessons_identical_between_conditions": all(
            (
                isolated_snapshots[
                    family[
                        "id"
                    ]
                ][
                    "learned"
                ][0][
                    "lesson_sha256"
                ]
                ==
                bundles[
                    family[
                        "id"
                    ]
                ][
                    "lesson_sha256"
                ]
            )

            and

            any(
                (
                    learned[
                        "family_id"
                    ]
                    ==
                    family[
                        "id"
                    ]
                )
                and
                (
                    learned[
                        "lesson_sha256"
                    ]
                    ==
                    bundles[
                        family[
                            "id"
                        ]
                    ][
                        "lesson_sha256"
                    ]
                )

                for learned
                in pooled_snapshot[
                    "learned"
                ]
            )

            for family
            in families
        ),

        "all_target_source_evidence_equal": all(
            (
                isolated_snapshots[
                    family[
                        "id"
                    ]
                ][
                    "learned"
                ][0][
                    "source_evidence_sha256"
                ]
                ==
                next(
                    learned[
                        "source_evidence_sha256"
                    ]

                    for learned
                    in pooled_snapshot[
                        "learned"
                    ]

                    if (
                        learned[
                            "family_id"
                        ]
                        ==
                        family[
                            "id"
                        ]
                    )
                )
            )

            for family
            in families
        ),

        "all_transfer_queries_equal": True,

        "all_compact_renderers_equal": True,

        "all_context_budget_configuration_equal": True,

        "all_pooled_evaluations_from_same_snapshot": all(
            row[
                "pooled"
            ][
                "snapshot_sha256"
            ]
            ==
            pooled_hash

            for row
            in results
        ),

        "all_isolated_evaluations_from_frozen_snapshots": all(
            row[
                "isolated"
            ][
                "snapshot_sha256"
            ]
            ==
            isolated_snapshots[
                row[
                    "family_id"
                ]
            ][
                "snapshot_sha256"
            ]

            for row
            in results
        ),

        "all_snapshot_copies_byte_identical_before_evaluation": all(
            (
                row[
                    "isolated"
                ][
                    "snapshot_sha256"
                ]
                ==
                row[
                    "isolated"
                ][
                    "copied_snapshot_sha256"
                ]
            )

            and

            (
                row[
                    "pooled"
                ][
                    "snapshot_sha256"
                ]
                ==
                row[
                    "pooled"
                ][
                    "copied_snapshot_sha256"
                ]
            )

            for row
            in results
        ),

        "pooled_snapshot": (
            pooled_snapshot
        ),

        "families": (
            results
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
        output
    )


def main():
    from model_adapter import (
        OpenAIResponsesModel,
        SentenceTransformerEmbedder,
        WordMeter,
    )

    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--tasks",
        default=(
            "experiments/"
            "tasks_017.json"
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
        run_experiment_017(
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

        "pool_size",
        "distractors_per_target",
        "near_neighbors_per_target",

        "isolated_task_passes",
        "pooled_task_passes",

        "isolated_task_pass_rate",
        "pooled_task_pass_rate",

        "isolated_semantic_violations",
        "pooled_semantic_violations",

        "isolated_target_clause_visible_families",
        "pooled_target_clause_visible_families",

        "isolated_families_with_wrong_memory_presented",
        "pooled_families_with_wrong_memory_presented",

        "isolated_wrong_family_clause_occurrences",
        "pooled_wrong_family_clause_occurrences",

        "mean_isolated_retrieval_precision",
        "mean_pooled_retrieval_precision",

        "mean_isolated_retrieval_recall",
        "mean_pooled_retrieval_recall",

        "isolated_wrong_rule_contamination_families",
        "pooled_wrong_rule_contamination_families",

        "paired_retrieval_regret_families",
        "paired_target_omission_regret_families",
        "paired_contamination_regret_families",

        "mean_isolated_memory_words",
        "mean_pooled_memory_words",

        "mean_isolated_memory_segments",
        "mean_pooled_memory_segments",

        "isolated_cluster_metrics",
        "pooled_cluster_metrics",

        "bundles_with_exact_semantic_clause_visible",
        "bundle_unsupported_claims_admitted",

        "all_target_lessons_identical_between_conditions",
        "all_target_source_evidence_equal",
        "all_transfer_queries_equal",
        "all_compact_renderers_equal",
        "all_context_budget_configuration_equal",
        "all_pooled_evaluations_from_same_snapshot",
        "all_isolated_evaluations_from_frozen_snapshots",
        "all_snapshot_copies_byte_identical_before_evaluation",
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
