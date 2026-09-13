from __future__ import annotations

import argparse
import hashlib
import json
import os

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


from experiments.seed_growth_008 import (
    AUTHORITATIVE_ROLE,
    normalize_span_text,
    parse_role_regions,
    role_for_span,
)

from experiments.seed_growth_011 import (
    admit_structured_propositions,
    structured_source_ancestry_valid,
)

from experiments.seed_growth_013 import (
    _build_repaired_structure,
    _run_memory_condition,
    render_semantic_closed_propositions,
    semantic_clause_supported,
    semantic_closed_projection,
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


def validate_authoritative_support(
    *,
    candidate,
    source_text: str,
):
    """
    Validate only the historical support.

    This deliberately does NOT inspect nucleus or qualifiers.

    That separation is the experiment.
    """

    if not isinstance(
        candidate,
        dict,
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "invalid_candidate"
            ),
        }

    source_quote = (
        candidate.get(
            "source_quote"
        )
    )

    if (
        not isinstance(
            source_quote,
            str,
        )
        or
        not source_quote
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "invalid_source_quote"
            ),
        }

    occurrence_count = (
        source_text.count(
            source_quote
        )
    )

    if occurrence_count != 1:
        return None, {
            "candidate": candidate,
            "reason": (
                "source_quote_not_unique"
            ),
            "occurrence_count": (
                occurrence_count
            ),
        }

    source_start = (
        source_text.index(
            source_quote
        )
    )

    source_end = (
        source_start
        +
        len(
            source_quote
        )
    )

    regions = (
        parse_role_regions(
            source_text
        )
    )

    source_role = (
        role_for_span(
            source_start,
            source_end,
            regions,
        )
    )

    if (
        source_role
        !=
        AUTHORITATIVE_ROLE
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "ineligible_source_role"
            ),
            "source_role": (
                source_role
            ),
            "source_start": (
                source_start
            ),
            "source_end": (
                source_end
            ),
        }

    return {
        "source_quote": (
            source_quote
        ),
        "source_start": (
            source_start
        ),
        "source_end": (
            source_end
        ),
        "source_role": (
            source_role
        ),
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
        "support_span_sha256": (
            _sha256_text(
                source_quote
            )
        ),
    }, None


def _support_is_covered(
    *,
    support,
    structured,
) -> bool:

    for proposition in structured:

        if (
            proposition[
                "source_start"
            ]
            <=
            support[
                "source_start"
            ]
            and
            proposition[
                "source_end"
            ]
            >=
            support[
                "source_end"
            ]
        ):
            return True

    return False


def reconcile_support_first(
    *,
    proposal,
    source_text: str,
    structured_gate=None,
):
    """
    Support-first admission.

    Stage 1:
        validate historical support.

    Stage 2:
        attempt structured admission.

    If support is valid but structure fails, exact support survives
    as unresolved grounded evidence.

    No family fixture, benchmark atom, semantic grader or oracle enters
    this function.
    """

    if structured_gate is None:
        structured_gate = (
            admit_structured_propositions(
                proposal=proposal,
                source_text=(
                    source_text
                ),
            )
        )

    structured = list(
        structured_gate[
            "admitted"
        ]
    )

    candidates = proposal.get(
        "propositions",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        candidates = []

    valid_supports = []
    hard_rejections = []

    for index, candidate in enumerate(
        candidates
    ):

        support, rejection = (
            validate_authoritative_support(
                candidate=candidate,
                source_text=(
                    source_text
                ),
            )
        )

        if rejection is not None:

            hard_rejections.append(
                {
                    **rejection,
                    "candidate_index": (
                        index
                    ),
                }
            )

            continue

        valid_supports.append(
            {
                **support,
                "candidate_index": (
                    index
                ),
            }
        )

    fallback = []

    seen_fallback_spans = set()

    covered_count = 0

    for support in valid_supports:

        if _support_is_covered(
            support=support,
            structured=structured,
        ):
            covered_count += 1
            continue

        span_key = (
            support[
                "source_start"
            ],
            support[
                "source_end"
            ],
        )

        if (
            span_key
            in
            seen_fallback_spans
        ):
            continue

        seen_fallback_spans.add(
            span_key
        )

        fallback.append(
            {
                "id": (
                    f"G{len(fallback) + 1}"
                ),
                "source_quote": (
                    support[
                        "source_quote"
                    ]
                ),
                "source_start": (
                    support[
                        "source_start"
                    ]
                ),
                "source_end": (
                    support[
                        "source_end"
                    ]
                ),
                "source_role": (
                    support[
                        "source_role"
                    ]
                ),
                "source_sha256": (
                    support[
                        "source_sha256"
                    ]
                ),
                "support_span_sha256": (
                    support[
                        "support_span_sha256"
                    ]
                ),
                "structure_status": (
                    "unresolved"
                ),
                "origin_candidate_indices": [
                    support[
                        "candidate_index"
                    ]
                ],
            }
        )

    return {
        "structured": (
            structured
        ),
        "fallback": (
            fallback
        ),
        "structured_rejections": (
            structured_gate[
                "rejected"
            ]
        ),
        "hard_rejections": (
            hard_rejections
        ),
        "valid_support_count": (
            len(
                valid_supports
            )
        ),
        "valid_supports_covered_by_structure": (
            covered_count
        ),
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
    }


def grounded_fallback_ancestry_valid(
    *,
    fallback,
    source_text: str,
) -> bool:

    start = fallback.get(
        "source_start"
    )

    end = fallback.get(
        "source_end"
    )

    if (
        not isinstance(
            start,
            int,
        )
        or
        not isinstance(
            end,
            int,
        )
    ):
        return False

    if (
        start < 0
        or
        end <= start
        or
        end > len(
            source_text
        )
    ):
        return False

    span = (
        source_text[
            start:end
        ]
    )

    if (
        span
        !=
        fallback.get(
            "source_quote"
        )
    ):
        return False

    if (
        fallback.get(
            "source_role"
        )
        !=
        AUTHORITATIVE_ROLE
    ):
        return False

    if (
        fallback.get(
            "source_sha256"
        )
        !=
        _sha256_text(
            source_text
        )
    ):
        return False

    if (
        fallback.get(
            "support_span_sha256"
        )
        !=
        _sha256_text(
            span
        )
    ):
        return False

    return True


def fallback_projection(
    fallback,
):
    """
    Project unresolved grounded support as exact support.

    No generated normalization occurs.
    """

    return [
        {
            "id": (
                item[
                    "id"
                ]
            ),
            "text": (
                item[
                    "source_quote"
                ]
            ),
            "source_quote": (
                item[
                    "source_quote"
                ]
            ),
            "source_start": (
                item[
                    "source_start"
                ]
            ),
            "source_end": (
                item[
                    "source_end"
                ]
            ),
            "source_role": (
                item[
                    "source_role"
                ]
            ),
            "source_sha256": (
                item[
                    "source_sha256"
                ]
            ),
            "span_sha256": (
                item[
                    "support_span_sha256"
                ]
            ),
            "structure_status": (
                "unresolved"
            ),
        }

        for item
        in fallback
    ]


def render_lossless_semantic_memory(
    *,
    structured,
    fallback,
) -> str:

    structured_text = (
        render_semantic_closed_propositions(
            structured
        )
    )

    if not fallback:
        return (
            structured_text
        )

    lines = [
        structured_text,
        "",
        "UNRESOLVED GROUNDED SUPPORT:",
        (
            "These records contain valid authoritative evidence "
            "whose structured normalization did not survive "
            "validation. Preserve the exact semantic payload. "
            "Do not infer replacement structure."
        ),
    ]

    for item in fallback:

        lines.append(
            "- "
            f"[{item['id']} "
            f"role={item['source_role']} "
            f"support_span="
            f"{item['source_start']}:"
            f"{item['source_end']} "
            f"structure_status="
            f"{item['structure_status']}]"
        )

        lines.append(
            "  UNRESOLVED_GROUNDED_SUPPORT: "
            +
            item[
                "source_quote"
            ]
        )

        lines.append(
            "  AUTHORITATIVE_SEMANTIC_PAYLOAD: "
            +
            item[
                "source_quote"
            ]
        )

    return "\n".join(
        lines
    )


def semantic_clause_survives(
    *,
    structured,
    fallback,
    semantic_clause: str,
) -> bool:

    if semantic_clause_supported(
        propositions=structured,
        semantic_clause=(
            semantic_clause
        ),
    ):
        return True

    target = (
        normalize_span_text(
            semantic_clause
        )
        .lower()
    )

    for item in fallback:

        support = (
            normalize_span_text(
                item[
                    "source_quote"
                ]
            )
            .lower()
        )

        if target in support:
            return True

    return False


def _visible_support_texts(
    *,
    structured,
    fallback,
):
    texts = {
        normalize_span_text(
            proposition[
                "source_quote"
            ]
        )
        .lower()

        for proposition
        in structured
    }

    texts.update(
        normalize_span_text(
            item[
                "source_quote"
            ]
        )
        .lower()

        for item
        in fallback
    )

    return texts


def count_recoverable_challenges_retained(
    *,
    family,
    structured,
    fallback,
):
    visible = (
        _visible_support_texts(
            structured=structured,
            fallback=fallback,
        )
    )

    return sum(
        1

        for challenge
        in family[
            "fallback_challenges"
        ][
            "recoverable"
        ]

        if (
            normalize_span_text(
                challenge[
                    "source_quote"
                ]
            )
            .lower()
            in
            visible
        )
    )


def count_recoverable_challenges_in_fallback(
    *,
    family,
    fallback,
):
    fallback_texts = {
        normalize_span_text(
            item[
                "source_quote"
            ]
        )
        .lower()

        for item
        in fallback
    }

    return sum(
        1

        for challenge
        in family[
            "fallback_challenges"
        ][
            "recoverable"
        ]

        if (
            normalize_span_text(
                challenge[
                    "source_quote"
                ]
            )
            .lower()
            in
            fallback_texts
        )
    )


def count_unsafe_challenge_admissions(
    *,
    family,
    structured,
    fallback,
):
    visible = (
        _visible_support_texts(
            structured=structured,
            fallback=fallback,
        )
    )

    counts = {
        "fabricated": 0,
        "nonauthoritative": 0,
    }

    for challenge in family[
        "fallback_challenges"
    ][
        "unsafe"
    ]:

        text = (
            normalize_span_text(
                challenge[
                    "source_quote"
                ]
            )
            .lower()
        )

        if text not in visible:
            continue

        counts[
            challenge[
                "kind"
            ]
        ] += 1

    counts[
        "total"
    ] = (
        counts[
            "fabricated"
        ]
        +
        counts[
            "nonauthoritative"
        ]
    )

    return counts


def ensure_fallback_challenges(
    *,
    repair_payload,
    family,
):
    """
    Inject the exact same adversarial candidate set before either
    condition is evaluated.

    One recoverable challenge:
        valid authoritative support + invalid structure.

    Two unsafe challenges:
        fabricated support
        non-authoritative real support
    """

    propositions = list(
        repair_payload.get(
            "propositions",
            [],
        )
    )

    injected = []

    for challenge in (
        family[
            "fallback_challenges"
        ][
            "recoverable"
        ]
        +
        family[
            "fallback_challenges"
        ][
            "unsafe"
        ]
    ):

        candidate = dict(
            challenge[
                "candidate"
            ]
        )

        candidate[
            "_fallback_challenge_id"
        ] = (
            challenge[
                "id"
            ]
        )

        candidate[
            "_fallback_challenge_kind"
        ] = (
            challenge[
                "kind"
            ]
        )

        propositions.append(
            candidate
        )

        injected.append(
            challenge[
                "id"
            ]
        )

    return {
        "propositions": (
            propositions
        )
    }, injected


def run_family_014(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
):
    family_dir = (
        Path(
            work_dir
        )
        /
        family[
            "id"
        ]
    )

    family_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_text = (
        family[
            "raw_source"
        ]
    )

    # ================================================================
    # ONE extraction + ONE repair.
    #
    # Shared by both conditions.
    # ================================================================

    repair_run = (
        _build_repaired_structure(
            family=family,
            model=model,
        )
    )

    raw_repair_payload = (
        repair_run[
            "repair_payload"
        ]
    )

    raw_repair_sha256 = (
        _sha256_json(
            raw_repair_payload
        )
    )

    (
        shared_repair_proposal,
        fallback_challenge_ids,
    ) = (
        ensure_fallback_challenges(
            repair_payload=(
                raw_repair_payload
            ),
            family=family,
        )
    )

    shared_repair_sha256 = (
        _sha256_json(
            shared_repair_proposal
        )
    )

    # ================================================================
    # CONDITION A
    #
    # Current all-or-nothing structured admission.
    # Then Seed 013 semantic-closed projection.
    # ================================================================

    current_gate = (
        admit_structured_propositions(
            proposal=(
                shared_repair_proposal
            ),
            source_text=(
                source_text
            ),
        )
    )

    current_structured = (
        current_gate[
            "admitted"
        ]
    )

    current_lesson = (
        render_semantic_closed_propositions(
            current_structured
        )
    )

    current_atoms = (
        semantic_closed_projection(
            current_structured
        )
    )

    current = (
        _run_memory_condition(
            condition_name=(
                "current_all_or_nothing"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                current_lesson
            ),
            evidence_atoms=(
                current_atoms
            ),
        )
    )

    current_clause_survives = (
        semantic_clause_supported(
            propositions=(
                current_structured
            ),
            semantic_clause=family[
                "semantic_clause"
            ],
        )
    )

    # ================================================================
    # CONDITION B
    #
    # SAME repair proposal.
    #
    # Keep current structured admissions.
    # Preserve exact authoritative support when structure fails.
    # ================================================================

    reconciled = (
        reconcile_support_first(
            proposal=(
                shared_repair_proposal
            ),
            source_text=(
                source_text
            ),
            structured_gate=(
                current_gate
            ),
        )
    )

    lossless_structured = (
        reconciled[
            "structured"
        ]
    )

    fallback = (
        reconciled[
            "fallback"
        ]
    )

    lossless_lesson = (
        render_lossless_semantic_memory(
            structured=(
                lossless_structured
            ),
            fallback=(
                fallback
            ),
        )
    )

    lossless_atoms = (
        semantic_closed_projection(
            lossless_structured
        )
        +
        fallback_projection(
            fallback
        )
    )

    lossless = (
        _run_memory_condition(
            condition_name=(
                "lossless_grounded_fallback"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                lossless_lesson
            ),
            evidence_atoms=(
                lossless_atoms
            ),
        )
    )

    lossless_clause_survives = (
        semantic_clause_survives(
            structured=(
                lossless_structured
            ),
            fallback=(
                fallback
            ),
            semantic_clause=family[
                "semantic_clause"
            ],
        )
    )

    # ================================================================
    # Controls
    # ================================================================

    same_source = (
        current[
            "source_evidence_sha256"
        ]
        ==
        lossless[
            "source_evidence_sha256"
        ]
    )

    if not same_source:
        raise RuntimeError(
            "014 invalid: source evidence differs."
        )

    current_structured_sha = (
        _sha256_json(
            current_structured
        )
    )

    lossless_structured_sha = (
        _sha256_json(
            lossless_structured
        )
    )

    same_structured = (
        current_structured_sha
        ==
        lossless_structured_sha
    )

    if not same_structured:
        raise RuntimeError(
            "014 invalid: structured admissions "
            "differ between conditions."
        )

    fallback_ancestry_valid = all(
        grounded_fallback_ancestry_valid(
            fallback=item,
            source_text=(
                source_text
            ),
        )

        for item
        in fallback
    )

    current_recoverable = (
        count_recoverable_challenges_retained(
            family=family,
            structured=(
                current_structured
            ),
            fallback=[],
        )
    )

    lossless_recoverable = (
        count_recoverable_challenges_retained(
            family=family,
            structured=(
                lossless_structured
            ),
            fallback=(
                fallback
            ),
        )
    )

    fallback_recoverable = (
        count_recoverable_challenges_in_fallback(
            family=family,
            fallback=(
                fallback
            ),
        )
    )

    unsafe = (
        count_unsafe_challenge_admissions(
            family=family,
            structured=(
                lossless_structured
            ),
            fallback=(
                fallback
            ),
        )
    )

    return {
        "family_id": (
            family[
                "id"
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

        "repair": {
            "initial_raw_model_response": (
                repair_run[
                    "initial_raw_response"
                ]
            ),
            "initial_parse_error": (
                repair_run[
                    "initial_parse_error"
                ]
            ),
            "repair_raw_model_response": (
                repair_run[
                    "repair_raw_response"
                ]
            ),
            "repair_parse_error": (
                repair_run[
                    "repair_parse_error"
                ]
            ),
            "raw_repair_payload_sha256": (
                raw_repair_sha256
            ),
            "shared_repair_proposal_sha256": (
                shared_repair_sha256
            ),
            "fallback_challenge_ids": (
                fallback_challenge_ids
            ),
            "shared_repair_proposal": (
                shared_repair_proposal
            ),
        },

        "current": {
            **current,
            "structured_propositions": (
                current_structured
            ),
            "structured_gate_rejections": (
                current_gate[
                    "rejected"
                ]
            ),
            "semantic_clause_survives_admission": (
                current_clause_survives
            ),
            "recoverable_challenges_retained": (
                current_recoverable
            ),
        },

        "lossless": {
            **lossless,
            "structured_propositions": (
                lossless_structured
            ),
            "fallback_records": (
                fallback
            ),
            "fallback_count": (
                len(
                    fallback
                )
            ),
            "hard_support_rejections": (
                reconciled[
                    "hard_rejections"
                ]
            ),
            "semantic_clause_survives_admission": (
                lossless_clause_survives
            ),
            "recoverable_challenges_retained": (
                lossless_recoverable
            ),
            "recoverable_challenges_using_fallback": (
                fallback_recoverable
            ),
            "fallback_ancestry_valid": (
                fallback_ancestry_valid
            ),
            "fabricated_support_challenges_admitted": (
                unsafe[
                    "fabricated"
                ]
            ),
            "nonauthoritative_support_challenges_admitted": (
                unsafe[
                    "nonauthoritative"
                ]
            ),
            "unsafe_support_challenges_admitted": (
                unsafe[
                    "total"
                ]
            ),
        },

        "same_source_evidence": (
            same_source
        ),

        "same_initial_structured_proposal": True,

        "same_repair_proposal": True,

        "same_structured_admissions": (
            same_structured
        ),

        "semantic_task_delta": (
            int(
                lossless[
                    "semantic_task_pass"
                ]
            )
            -
            int(
                current[
                    "semantic_task_pass"
                ]
            )
        ),

        "memory_word_delta": (
            lossless[
                "memory_word_count"
            ]
            -
            current[
                "memory_word_count"
            ]
        ),
    }


def _count(
    results,
    condition,
    metric,
):
    return sum(
        int(
            family[
                condition
            ].get(
                metric,
                False,
            )
        )

        for family
        in results
    )


def _sum_metric(
    results,
    condition,
    metric,
):
    return sum(
        int(
            family[
                condition
            ].get(
                metric,
                0,
            )
        )

        for family
        in results
    )


def _mean_metric(
    results,
    condition,
    metric,
):
    values = [
        float(
            family[
                condition
            ].get(
                metric,
                0,
            )
        )

        for family
        in results
    ]

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


def run_experiment_014(
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

    state_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = [
        run_family_014(
            family=family,
            work_dir=(
                state_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
        )

        for family
        in payload[
            "families"
        ]
    ]

    recoverable_challenges = sum(
        len(
            family[
                "fallback_challenges"
            ][
                "recoverable"
            ]
        )

        for family
        in payload[
            "families"
        ]
    )

    unsafe_challenges = sum(
        len(
            family[
                "fallback_challenges"
            ][
                "unsafe"
            ]
        )

        for family
        in payload[
            "families"
        ]
    )

    report = {
        "experiment": (
            "seed-growth-014"
        ),

        "classification": (
            "exploratory-fresh-lossless-"
            "rejection-grounded-fallback-ablation"
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
            len(
                results
            )
        ),

        "conditions": {
            "A": (
                "same_repair_proposal_"
                "all_or_nothing_structure_admission_"
                "semantic_closed_projection"
            ),
            "B": (
                "same_repair_proposal_"
                "support_first_lossless_fallback_"
                "semantic_closed_projection"
            ),
        },

        # ------------------------------------------------------------
        # Downstream semantic behavior
        # ------------------------------------------------------------

        "current_semantic_task_passes": (
            _count(
                results,
                "current",
                "semantic_task_pass",
            )
        ),

        "lossless_semantic_task_passes": (
            _count(
                results,
                "lossless",
                "semantic_task_pass",
            )
        ),

        "current_semantic_violations": (
            _count(
                results,
                "current",
                "semantic_violation",
            )
        ),

        "lossless_semantic_violations": (
            _count(
                results,
                "lossless",
                "semantic_violation",
            )
        ),

        # ------------------------------------------------------------
        # Did evidence survive admission?
        # ------------------------------------------------------------

        "current_semantic_clause_surviving_families": (
            _count(
                results,
                "current",
                "semantic_clause_survives_admission",
            )
        ),

        "lossless_semantic_clause_surviving_families": (
            _count(
                results,
                "lossless",
                "semantic_clause_survives_admission",
            )
        ),

        "current_exact_semantic_clause_visible_families": (
            _count(
                results,
                "current",
                "semantic_clause_visible",
            )
        ),

        "lossless_exact_semantic_clause_visible_families": (
            _count(
                results,
                "lossless",
                "semantic_clause_visible",
            )
        ),

        # ------------------------------------------------------------
        # Recoverable structural attacks
        # ------------------------------------------------------------

        "recoverable_structural_challenges": (
            recoverable_challenges
        ),

        "current_recoverable_challenges_retained": (
            _sum_metric(
                results,
                "current",
                "recoverable_challenges_retained",
            )
        ),

        "lossless_recoverable_challenges_retained": (
            _sum_metric(
                results,
                "lossless",
                "recoverable_challenges_retained",
            )
        ),

        "lossless_recoverable_challenges_using_fallback": (
            _sum_metric(
                results,
                "lossless",
                "recoverable_challenges_using_fallback",
            )
        ),

        # ------------------------------------------------------------
        # Unsafe support attacks
        # ------------------------------------------------------------

        "unsafe_support_challenges": (
            unsafe_challenges
        ),

        "lossless_fabricated_support_challenges_admitted": (
            _sum_metric(
                results,
                "lossless",
                "fabricated_support_challenges_admitted",
            )
        ),

        "lossless_nonauthoritative_support_challenges_admitted": (
            _sum_metric(
                results,
                "lossless",
                "nonauthoritative_support_challenges_admitted",
            )
        ),

        "lossless_unsafe_support_challenges_admitted": (
            _sum_metric(
                results,
                "lossless",
                "unsafe_support_challenges_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Fallback behavior
        # ------------------------------------------------------------

        "families_using_grounded_fallback": sum(
            int(
                family[
                    "lossless"
                ][
                    "fallback_count"
                ]
                > 0
            )

            for family
            in results
        ),

        "grounded_fallback_records": (
            _sum_metric(
                results,
                "lossless",
                "fallback_count",
            )
        ),

        "fallback_ancestry_valid_families": (
            _count(
                results,
                "lossless",
                "fallback_ancestry_valid",
            )
        ),

        # ------------------------------------------------------------
        # Knowledge / closed-world safety
        # ------------------------------------------------------------

        "current_complete_lessons": (
            _count(
                results,
                "current",
                "lesson_knowledge_complete",
            )
        ),

        "lossless_complete_lessons": (
            _count(
                results,
                "lossless",
                "lesson_knowledge_complete",
            )
        ),

        "current_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "current",
                "unsupported_claims_admitted",
            )
        ),

        "lossless_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "lossless",
                "unsupported_claims_admitted",
            )
        ),

        # ------------------------------------------------------------
        # Cost
        # ------------------------------------------------------------

        "mean_current_memory_words": (
            _mean_metric(
                results,
                "current",
                "memory_word_count",
            )
        ),

        "mean_lossless_memory_words": (
            _mean_metric(
                results,
                "lossless",
                "memory_word_count",
            )
        ),

        "initial_extraction_model_calls": (
            len(
                results
            )
        ),

        "repair_model_calls": (
            len(
                results
            )
        ),

        "current_projection_model_calls": 0,

        "lossless_reconciliation_model_calls": 0,

        "current_transfer_model_calls": (
            len(
                results
            )
        ),

        "lossless_transfer_model_calls": (
            len(
                results
            )
        ),

        # ------------------------------------------------------------
        # Strict controls
        # ------------------------------------------------------------

        "all_source_evidence_equal": (
            all(
                family[
                    "same_source_evidence"
                ]

                for family
                in results
            )
        ),

        "all_initial_structured_proposals_equal": (
            all(
                family[
                    "same_initial_structured_proposal"
                ]

                for family
                in results
            )
        ),

        "all_repair_proposals_equal": (
            all(
                family[
                    "same_repair_proposal"
                ]

                for family
                in results
            )
        ),

        "all_structured_admissions_equal": (
            all(
                family[
                    "same_structured_admissions"
                ]

                for family
                in results
            )
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
        output,
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
            "tasks_014.json"
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
        run_experiment_014(
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

        "current_semantic_task_passes",
        "lossless_semantic_task_passes",

        "current_semantic_violations",
        "lossless_semantic_violations",

        "current_semantic_clause_surviving_families",
        "lossless_semantic_clause_surviving_families",

        "current_exact_semantic_clause_visible_families",
        "lossless_exact_semantic_clause_visible_families",

        "recoverable_structural_challenges",
        "current_recoverable_challenges_retained",
        "lossless_recoverable_challenges_retained",
        "lossless_recoverable_challenges_using_fallback",

        "unsafe_support_challenges",
        "lossless_fabricated_support_challenges_admitted",
        "lossless_nonauthoritative_support_challenges_admitted",
        "lossless_unsafe_support_challenges_admitted",

        "families_using_grounded_fallback",
        "grounded_fallback_records",
        "fallback_ancestry_valid_families",

        "current_complete_lessons",
        "lossless_complete_lessons",

        "current_unsupported_claims_admitted",
        "lossless_unsupported_claims_admitted",

        "mean_current_memory_words",
        "mean_lossless_memory_words",

        "all_source_evidence_equal",
        "all_initial_structured_proposals_equal",
        "all_repair_proposals_equal",
        "all_structured_admissions_equal",
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
