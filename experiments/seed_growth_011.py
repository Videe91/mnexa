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


from experiments.seed_growth import (
    grade_text,
)

from experiments.seed_growth_004 import (
    make_fidelity_reasoner,
)

from experiments.seed_growth_006 import (
    admit_claims,
)

from experiments.seed_growth_008 import (
    AUTHORITATIVE_ROLE,
    normalize_span_text,
    parse_atom_proposal,
    parse_role_regions,
    render_role_aware_claims,
    role_for_span,
)

from experiments.seed_growth_009 import (
    locate_atomic_units,
)

from experiments.seed_growth_010 import (
    admit_autonomous_atoms,
    build_autonomous_boundary_prompt,
    canonical_boundary_metrics,
    count_overlapping_pairs,
    ensure_overlap_challenges,
    source_ancestry_valid,
)

from mnexa_seed import (
    MnexaSeed,
)


ALLOWED_QUALIFIER_TYPES = {
    "condition",
    "ordering",
    "scope",
    "negation",
}


STRUCTURED_PROPOSITION_INSTRUCTION = """
GROUNDED STRUCTURED PROPOSITION EXTRACTION

You are converting authoritative historical evidence into reusable
structured propositions.

The source contains role markers.

Only content inside the authoritative_correction role may become
reusable knowledge.

IMPORTANT DISTINCTION

The exact historical wording and the reusable proposition are related
but are not required to have identical boundaries.

For every proposition provide:

1. source_quote
   - an exact contiguous substring from authoritative_correction
   - it may include syntax such as:
     * numbered-list prefixes
     * conjunctions
     * condition phrases
     * ordering words
     * punctuation
   - it must contain the proposition nucleus

2. nucleus_quote
   - the smallest exact contiguous substring inside source_quote that
     states the reusable operational proposition
   - it must itself also be literal source text
   - do not paraphrase it

3. qualifiers
   - semantic context that materially constrains the nucleus
   - each qualifier must contain:
       type
       source_quote
   - allowed types:
       condition
       ordering
       scope
       negation
   - every qualifier source_quote must itself be an exact substring
     inside the proposition source_quote

EXAMPLES

Source:

1) refresh the recovery lease;

Valid:

{
  "source_quote": "1) refresh the recovery lease",
  "nucleus_quote": "refresh the recovery lease",
  "qualifiers": []
}

Source:

When ZX-11 occurs, refresh the recovery lease

Valid:

{
  "source_quote": "When ZX-11 occurs, refresh the recovery lease",
  "nucleus_quote": "refresh the recovery lease",
  "qualifiers": [
    {
      "type": "condition",
      "source_quote": "When ZX-11 occurs"
    }
  ]
}

Source:

then wait 8 seconds

Valid:

{
  "source_quote": "then wait 8 seconds",
  "nucleus_quote": "wait 8 seconds",
  "qualifiers": [
    {
      "type": "ordering",
      "source_quote": "then"
    }
  ]
}

RULES

1. Extract independently reusable operational propositions.

2. Preserve all decision-critical details:
   - numbers
   - units
   - counts
   - identifiers
   - headers
   - retry limits
   - negations
   - scope restrictions
   - ordering requirements

3. Do not paraphrase source_quote.

4. Do not paraphrase nucleus_quote.

5. Do not invent qualifier text.

6. Do not infer facts not physically present in the source.

7. Do not include failed_decision, status, operator_note, or
   diagnostic_metadata content.

8. A conjunction such as "and" or "but" is not automatically a
   semantic qualifier. Include only qualifiers that materially constrain
   meaning.

9. Keep negation such as "never" or "only" inside the nucleus when it
   directly changes the proposition itself.

10. Do not include private reasoning.

Return JSON only:

{
  "propositions": [
    {
      "source_quote": "<exact source substring>",
      "nucleus_quote": "<exact proposition substring>",
      "qualifiers": [
        {
          "type": "condition|ordering|scope|negation",
          "source_quote": "<exact qualifier substring>"
        }
      ]
    }
  ]
}
""".strip()


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


def _strip_json_fence(
    text: str,
) -> str:

    text = text.strip()

    if not text.startswith(
        "```"
    ):
        return text

    lines = (
        text.splitlines()
    )

    if lines:
        lines = lines[
            1:
        ]

    if (
        lines
        and
        lines[-1]
        .strip()
        .startswith(
            "```"
        )
    ):
        lines = lines[
            :-1
        ]

    return (
        "\n"
        .join(
            lines
        )
        .strip()
    )


def parse_structured_proposal(
    text: str,
):
    payload = json.loads(
        _strip_json_fence(
            text
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Structured proposal "
            "must be a JSON object."
        )

    propositions = (
        payload.get(
            "propositions"
        )
    )

    if not isinstance(
        propositions,
        list,
    ):
        raise ValueError(
            "Structured proposal "
            "must contain a "
            "propositions list."
        )

    return payload


def build_structured_proposition_prompt(
    source_text: str,
) -> str:

    return (
        STRUCTURED_PROPOSITION_INSTRUCTION
        + "\n\n"
        + "SOURCE:\n"
        + source_text
    )


def _span_overlap(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:

    return (
        max(
            start_a,
            start_b,
        )
        <
        min(
            end_a,
            end_b,
        )
    )


def count_nucleus_overlaps(
    propositions,
) -> int:

    total = 0

    for index, left in enumerate(
        propositions
    ):

        for right in propositions[
            index + 1:
        ]:

            if _span_overlap(
                left[
                    "nucleus_start"
                ],
                left[
                    "nucleus_end"
                ],
                right[
                    "nucleus_start"
                ],
                right[
                    "nucleus_end"
                ],
            ):
                total += 1

    return total


def _ground_structured_candidate(
    *,
    candidate,
    source_text: str,
    regions,
):
    if not isinstance(
        candidate,
        dict,
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "invalid_proposition"
            ),
        }

    source_quote = (
        candidate.get(
            "source_quote"
        )
    )

    nucleus_quote = (
        candidate.get(
            "nucleus_quote"
        )
    )

    qualifiers = (
        candidate.get(
            "qualifiers",
            [],
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
                "missing_source_quote"
            ),
        }

    if (
        not isinstance(
            nucleus_quote,
            str,
        )
        or
        not nucleus_quote
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "missing_nucleus_quote"
            ),
        }

    if not isinstance(
        qualifiers,
        list,
    ):
        return None, {
            "candidate": candidate,
            "reason": (
                "qualifiers_not_list"
            ),
        }

    source_count = (
        source_text.count(
            source_quote
        )
    )

    if source_count != 1:
        return None, {
            "candidate": candidate,
            "reason": (
                "source_quote_not_unique"
            ),
            "occurrence_count": (
                source_count
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
        }

    nucleus_count = (
        source_quote.count(
            nucleus_quote
        )
    )

    if nucleus_count != 1:
        return None, {
            "candidate": candidate,
            "reason": (
                "nucleus_not_unique_in_source_quote"
            ),
            "occurrence_count": (
                nucleus_count
            ),
        }

    nucleus_relative_start = (
        source_quote.index(
            nucleus_quote
        )
    )

    nucleus_start = (
        source_start
        +
        nucleus_relative_start
    )

    nucleus_end = (
        nucleus_start
        +
        len(
            nucleus_quote
        )
    )

    grounded_qualifiers = []

    seen_qualifier_spans = set()

    for qualifier in qualifiers:

        if not isinstance(
            qualifier,
            dict,
        ):
            return None, {
                "candidate": candidate,
                "reason": (
                    "invalid_qualifier"
                ),
            }

        qualifier_type = (
            qualifier.get(
                "type"
            )
        )

        qualifier_quote = (
            qualifier.get(
                "source_quote"
            )
        )

        if (
            qualifier_type
            not in
            ALLOWED_QUALIFIER_TYPES
        ):
            return None, {
                "candidate": candidate,
                "reason": (
                    "unsupported_qualifier_type"
                ),
                "qualifier_type": (
                    qualifier_type
                ),
            }

        if (
            not isinstance(
                qualifier_quote,
                str,
            )
            or
            not qualifier_quote
        ):
            return None, {
                "candidate": candidate,
                "reason": (
                    "invalid_qualifier_quote"
                ),
            }

        qualifier_count = (
            source_quote.count(
                qualifier_quote
            )
        )

        if qualifier_count != 1:
            return None, {
                "candidate": candidate,
                "reason": (
                    "qualifier_not_unique_in_source_quote"
                ),
                "qualifier": (
                    qualifier
                ),
                "occurrence_count": (
                    qualifier_count
                ),
            }

        relative_start = (
            source_quote.index(
                qualifier_quote
            )
        )

        qualifier_start = (
            source_start
            +
            relative_start
        )

        qualifier_end = (
            qualifier_start
            +
            len(
                qualifier_quote
            )
        )

        qualifier_span = (
            qualifier_start,
            qualifier_end,
        )

        if (
            qualifier_span
            in
            seen_qualifier_spans
        ):
            return None, {
                "candidate": candidate,
                "reason": (
                    "duplicate_qualifier_span"
                ),
            }

        if _span_overlap(
            qualifier_start,
            qualifier_end,
            nucleus_start,
            nucleus_end,
        ):
            return None, {
                "candidate": candidate,
                "reason": (
                    "qualifier_overlaps_nucleus"
                ),
                "qualifier": (
                    qualifier
                ),
            }

        seen_qualifier_spans.add(
            qualifier_span
        )

        grounded_qualifiers.append(
            {
                "type": (
                    qualifier_type
                ),
                "source_quote": (
                    qualifier_quote
                ),
                "source_start": (
                    qualifier_start
                ),
                "source_end": (
                    qualifier_end
                ),
                "span_sha256": (
                    _sha256_text(
                        qualifier_quote
                    )
                ),
            }
        )

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
        "nucleus_quote": (
            nucleus_quote
        ),
        "nucleus_start": (
            nucleus_start
        ),
        "nucleus_end": (
            nucleus_end
        ),
        "nucleus_sha256": (
            _sha256_text(
                nucleus_quote
            )
        ),
        "qualifiers": (
            grounded_qualifiers
        ),
    }, None


def _assign_proposition_ids(
    propositions,
):
    ordered = sorted(
        propositions,
        key=lambda proposition: (
            proposition[
                "nucleus_start"
            ],
            proposition[
                "nucleus_end"
            ],
        ),
    )

    return [
        {
            "id": (
                f"P{index}"
            ),
            **{
                key: value
                for key, value
                in proposition.items()
                if key != "id"
            },
        }

        for index, proposition
        in enumerate(
            ordered,
            start=1,
        )
    ]


def admit_structured_propositions(
    *,
    proposal,
    source_text: str,
):
    """
    Grounded structured-proposition admission.

    IMPORTANT:
    This runtime gate receives no benchmark family and no hidden
    canonical proposition boundaries.

    It validates only:

    - exact authoritative support span
    - exact nucleus ancestry
    - exact qualifier ancestry
    - supported qualifier types
    - duplicate nuclei
    - non-overlapping final nuclei

    When candidate nuclei overlap, shorter nuclei are considered first.
    """

    regions = (
        parse_role_regions(
            source_text
        )
    )

    candidates = (
        proposal.get(
            "propositions",
            [],
        )
    )

    if not isinstance(
        candidates,
        list,
    ):
        candidates = []

    grounded = []
    rejected = []

    for candidate in candidates:

        proposition, rejection = (
            _ground_structured_candidate(
                candidate=(
                    candidate
                ),
                source_text=(
                    source_text
                ),
                regions=(
                    regions
                ),
            )
        )

        if rejection is not None:
            rejected.append(
                rejection
            )
            continue

        grounded.append(
            proposition
        )

    grounded.sort(
        key=lambda proposition: (
            (
                proposition[
                    "nucleus_end"
                ]
                -
                proposition[
                    "nucleus_start"
                ]
            ),
            proposition[
                "nucleus_start"
            ],
            (
                proposition[
                    "source_end"
                ]
                -
                proposition[
                    "source_start"
                ]
            ),
        )
    )

    admitted = []

    seen_nucleus_spans = set()

    for proposition in grounded:

        nucleus_span = (
            proposition[
                "nucleus_start"
            ],
            proposition[
                "nucleus_end"
            ],
        )

        if (
            nucleus_span
            in
            seen_nucleus_spans
        ):
            rejected.append(
                {
                    "candidate": {
                        "source_quote": (
                            proposition[
                                "source_quote"
                            ]
                        ),
                        "nucleus_quote": (
                            proposition[
                                "nucleus_quote"
                            ]
                        ),
                    },
                    "reason": (
                        "duplicate_nucleus_span"
                    ),
                }
            )

            continue

        overlapping = [
            existing

            for existing
            in admitted

            if _span_overlap(
                proposition[
                    "nucleus_start"
                ],
                proposition[
                    "nucleus_end"
                ],
                existing[
                    "nucleus_start"
                ],
                existing[
                    "nucleus_end"
                ],
            )
        ]

        if overlapping:

            rejected.append(
                {
                    "candidate": {
                        "source_quote": (
                            proposition[
                                "source_quote"
                            ]
                        ),
                        "nucleus_quote": (
                            proposition[
                                "nucleus_quote"
                            ]
                        ),
                    },
                    "reason": (
                        "nucleus_overlaps_admitted_nucleus"
                    ),
                    "nucleus_start": (
                        proposition[
                            "nucleus_start"
                        ]
                    ),
                    "nucleus_end": (
                        proposition[
                            "nucleus_end"
                        ]
                    ),
                    "overlaps": [
                        {
                            "id": (
                                existing.get(
                                    "id"
                                )
                            ),
                            "nucleus_quote": (
                                existing[
                                    "nucleus_quote"
                                ]
                            ),
                            "nucleus_start": (
                                existing[
                                    "nucleus_start"
                                ]
                            ),
                            "nucleus_end": (
                                existing[
                                    "nucleus_end"
                                ]
                            ),
                        }

                        for existing
                        in overlapping
                    ],
                }
            )

            continue

        admitted.append(
            proposition
        )

        seen_nucleus_spans.add(
            nucleus_span
        )

    return {
        "admitted": (
            _assign_proposition_ids(
                admitted
            )
        ),
        "rejected": (
            rejected
        ),
        "source_sha256": (
            _sha256_text(
                source_text
            )
        ),
    }


def structured_source_ancestry_valid(
    *,
    proposition,
    source_text: str,
) -> bool:

    source_start = (
        proposition.get(
            "source_start"
        )
    )

    source_end = (
        proposition.get(
            "source_end"
        )
    )

    nucleus_start = (
        proposition.get(
            "nucleus_start"
        )
    )

    nucleus_end = (
        proposition.get(
            "nucleus_end"
        )
    )

    if not all(
        isinstance(
            value,
            int,
        )
        for value
        in (
            source_start,
            source_end,
            nucleus_start,
            nucleus_end,
        )
    ):
        return False

    if (
        source_start < 0
        or
        source_end
        <=
        source_start
        or
        nucleus_start
        <
        source_start
        or
        nucleus_end
        >
        source_end
        or
        nucleus_end
        <=
        nucleus_start
        or
        source_end
        >
        len(
            source_text
        )
    ):
        return False

    source_span = (
        source_text[
            source_start:
            source_end
        ]
    )

    nucleus_span = (
        source_text[
            nucleus_start:
            nucleus_end
        ]
    )

    if (
        source_span
        !=
        proposition.get(
            "source_quote"
        )
    ):
        return False

    if (
        nucleus_span
        !=
        proposition.get(
            "nucleus_quote"
        )
    ):
        return False

    if (
        proposition.get(
            "source_role"
        )
        !=
        AUTHORITATIVE_ROLE
    ):
        return False

    if (
        proposition.get(
            "source_sha256"
        )
        !=
        _sha256_text(
            source_text
        )
    ):
        return False

    if (
        proposition.get(
            "support_span_sha256"
        )
        !=
        _sha256_text(
            source_span
        )
    ):
        return False

    if (
        proposition.get(
            "nucleus_sha256"
        )
        !=
        _sha256_text(
            nucleus_span
        )
    ):
        return False

    for qualifier in proposition.get(
        "qualifiers",
        [],
    ):

        q_start = (
            qualifier.get(
                "source_start"
            )
        )

        q_end = (
            qualifier.get(
                "source_end"
            )
        )

        if (
            not isinstance(
                q_start,
                int,
            )
            or
            not isinstance(
                q_end,
                int,
            )
        ):
            return False

        if (
            q_start
            <
            source_start
            or
            q_end
            >
            source_end
            or
            q_end
            <=
            q_start
        ):
            return False

        quote = (
            source_text[
                q_start:q_end
            ]
        )

        if (
            quote
            !=
            qualifier.get(
                "source_quote"
            )
        ):
            return False

        if (
            qualifier.get(
                "span_sha256"
            )
            !=
            _sha256_text(
                quote
            )
        ):
            return False

    return True


def canonical_nucleus_metrics(
    *,
    admitted_propositions,
    expected_units,
):
    expected = {
        normalize_span_text(
            unit[
                "text"
            ]
        )
        for unit
        in expected_units
    }

    admitted = {
        normalize_span_text(
            proposition[
                "nucleus_quote"
            ]
        )
        for proposition
        in admitted_propositions
    }

    matched = (
        expected
        &
        admitted
    )

    recall = (
        len(
            matched
        )
        /
        len(
            expected
        )

        if expected
        else 1.0
    )

    precision = (
        len(
            matched
        )
        /
        len(
            admitted
        )

        if admitted
        else (
            1.0
            if not expected
            else 0.0
        )
    )

    return {
        "nucleus_recall": (
            recall
        ),
        "nucleus_precision": (
            precision
        ),
        "exact_nucleus_matches": (
            len(
                matched
            )
        ),
        "expected_nuclei": (
            len(
                expected
            )
        ),
        "admitted_nuclei": (
            len(
                admitted
            )
        ),
        "complete": (
            admitted
            ==
            expected
        ),
    }


def qualifier_metrics(
    *,
    admitted_propositions,
    expected_units,
    expected_qualifiers,
):
    atom_text = {
        unit[
            "id"
        ]: (
            normalize_span_text(
                unit[
                    "text"
                ]
            )
        )

        for unit
        in expected_units
    }

    expected = {
        (
            atom_text[
                qualifier[
                    "atom_id"
                ]
            ],
            qualifier[
                "type"
            ],
            normalize_span_text(
                qualifier[
                    "text"
                ]
            ),
        )

        for qualifier
        in expected_qualifiers
    }

    admitted = set()

    for proposition in admitted_propositions:

        nucleus = (
            normalize_span_text(
                proposition[
                    "nucleus_quote"
                ]
            )
        )

        for qualifier in proposition.get(
            "qualifiers",
            [],
        ):

            admitted.add(
                (
                    nucleus,
                    qualifier[
                        "type"
                    ],
                    normalize_span_text(
                        qualifier[
                            "source_quote"
                        ]
                    ),
                )
            )

    matched = (
        expected
        &
        admitted
    )

    recall = (
        len(
            matched
        )
        /
        len(
            expected
        )

        if expected
        else 1.0
    )

    precision = (
        len(
            matched
        )
        /
        len(
            admitted
        )

        if admitted
        else (
            1.0
            if not expected
            else 0.0
        )
    )

    return {
        "qualifier_recall": (
            recall
        ),
        "qualifier_precision": (
            precision
        ),
        "expected_qualifiers": (
            len(
                expected
            )
        ),
        "admitted_qualifiers": (
            len(
                admitted
            )
        ),
        "matched_qualifiers": (
            len(
                matched
            )
        ),
        "complete": (
            admitted
            ==
            expected
        ),
    }


def render_structured_propositions(
    propositions,
) -> str:

    if not propositions:
        return (
            "SUPPORTED STRUCTURED "
            "PROPOSITIONS:\n"
            "(none admitted)"
        )

    lines = [
        "SUPPORTED STRUCTURED "
        "PROPOSITIONS:"
    ]

    for proposition in propositions:

        lines.append(
            "- "
            f"[{proposition['id']} "
            f"role="
            f"{proposition['source_role']} "
            f"evidence_span="
            f"{proposition['source_start']}:"
            f"{proposition['source_end']} "
            f"nucleus_span="
            f"{proposition['nucleus_start']}:"
            f"{proposition['nucleus_end']}] "
            f"{proposition['nucleus_quote']}"
        )

        for qualifier in proposition.get(
            "qualifiers",
            [],
        ):

            lines.append(
                "  - "
                f"qualifier["
                f"{qualifier['type']}"
                f"] "
                f"span="
                f"{qualifier['source_start']}:"
                f"{qualifier['source_end']} "
                f"{qualifier['source_quote']}"
            )

    return "\n".join(
        lines
    )


def _nucleus_atom_projection(
    propositions,
):
    return [
        {
            "id": (
                proposition[
                    "id"
                ]
            ),
            "text": (
                proposition[
                    "nucleus_quote"
                ]
            ),
            "source_quote": (
                proposition[
                    "nucleus_quote"
                ]
            ),
            "source_start": (
                proposition[
                    "nucleus_start"
                ]
            ),
            "source_end": (
                proposition[
                    "nucleus_end"
                ]
            ),
            "source_role": (
                proposition[
                    "source_role"
                ]
            ),
            "source_sha256": (
                proposition[
                    "source_sha256"
                ]
            ),
            "span_sha256": (
                proposition[
                    "nucleus_sha256"
                ]
            ),
        }

        for proposition
        in propositions
    ]


def _claim_audit(
    evidence_atoms,
):
    proposal = {
        "claims": [
            {
                "text": (
                    atom[
                        "text"
                    ]
                ),
                "evidence_ids": [
                    atom[
                        "id"
                    ]
                ],
            }

            for atom
            in evidence_atoms
        ]
    }

    return admit_claims(
        proposal,
        evidence_atoms,
    )


def _proposal_contains_nucleus(
    proposal,
    nucleus: str,
) -> bool:

    target = (
        normalize_span_text(
            nucleus
        )
    )

    for proposition in proposal.get(
        "propositions",
        [],
    ):

        if not isinstance(
            proposition,
            dict,
        ):
            continue

        candidate = (
            proposition.get(
                "nucleus_quote"
            )
        )

        if (
            isinstance(
                candidate,
                str,
            )
            and
            normalize_span_text(
                candidate
            )
            ==
            target
        ):
            return True

    return False


def ensure_structured_compound_challenges(
    *,
    proposal,
    family,
    source_text: str,
):
    """
    Inject pre-registered, physically real, authoritative but compound
    nuclei if the structured extractor did not propose them itself.

    This guarantees the generic nucleus-overlap gate is attacked.

    The admission gate still receives no benchmark canonical boundary
    map.
    """

    propositions = list(
        proposal.get(
            "propositions",
            [],
        )
    )

    injected = 0

    for challenge in family[
        "structured_compound_challenges"
    ]:

        text = (
            challenge[
                "text"
            ]
        )

        if (
            source_text.count(
                text
            )
            != 1
        ):
            raise RuntimeError(
                "Structured compound "
                "challenge must occur "
                "exactly once: "
                f"{family['id']} "
                f":: {text!r}"
            )

        if _proposal_contains_nucleus(
            {
                "propositions": (
                    propositions
                )
            },
            text,
        ):
            continue

        propositions.append(
            {
                "source_quote": (
                    text
                ),
                "nucleus_quote": (
                    text
                ),
                "qualifiers": [],
                "_structured_compound_challenge": (
                    True
                ),
            }
        )

        injected += 1

    return {
        "propositions": (
            propositions
        )
    }, injected


def compound_span_covers_multiple_units(
    *,
    span_text: str,
    source_text: str,
    expected_units,
) -> bool:

    if (
        source_text.count(
            span_text
        )
        != 1
    ):
        return False

    span_start = (
        source_text.index(
            span_text
        )
    )

    span_end = (
        span_start
        +
        len(
            span_text
        )
    )

    overlaps = 0

    for unit in expected_units:

        text = (
            unit[
                "text"
            ]
        )

        if (
            source_text.count(
                text
            )
            != 1
        ):
            continue

        start = (
            source_text.index(
                text
            )
        )

        end = (
            start
            +
            len(
                text
            )
        )

        if _span_overlap(
            span_start,
            span_end,
            start,
            end,
        ):
            overlaps += 1

    return (
        overlaps
        >= 2
    )


def _compound_nucleus_count(
    *,
    propositions,
    family,
):
    return sum(
        1

        for proposition
        in propositions

        if compound_span_covers_multiple_units(
            span_text=(
                proposition[
                    "nucleus_quote"
                ]
            ),
            source_text=family[
                "raw_source"
            ],
            expected_units=family[
                "atomic_units"
            ],
        )
    )


def _structured_challenge_rejections(
    *,
    gate_result,
    family,
):
    challenge_texts = {
        normalize_span_text(
            challenge[
                "text"
            ]
        )

        for challenge
        in family[
            "structured_compound_challenges"
        ]
    }

    rejected = set()

    for rejection in gate_result[
        "rejected"
    ]:

        if (
            rejection.get(
                "reason"
            )
            !=
            "nucleus_overlaps_admitted_nucleus"
        ):
            continue

        candidate = (
            rejection.get(
                "candidate"
            )
        )

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        nucleus = (
            candidate.get(
                "nucleus_quote"
            )
        )

        if isinstance(
            nucleus,
            str,
        ):
            rejected.add(
                normalize_span_text(
                    nucleus
                )
            )

    return len(
        challenge_texts
        &
        rejected
    )


def _source_evidence_text(
    candidate_decision: str,
    outcome_text: str,
) -> str:

    return (
        "DECISION: "
        +
        candidate_decision
        +
        "\nOUTCOME: "
        +
        outcome_text
    )


def _controlled_candidate_reasoner(
    candidate_decision: str,
):
    def reasoner(
        task: str,
        context: str,
    ) -> str:

        return (
            candidate_decision
        )

    return reasoner


def _run_memory_condition(
    *,
    condition_name: str,
    family,
    family_dir: Path,
    model,
    embedder,
    meter,
    lesson_text: str,
    evidence_atoms,
):
    db_path = (
        family_dir
        /
        f"{condition_name}.sqlite3"
    )

    if db_path.exists():
        db_path.unlink()

    mnexa = MnexaSeed(
        db_path,
        embedder=embedder,
        meter=meter,
    )

    try:

        first_decision = (
            mnexa.decide(
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
                "Controlled failed decision changed."
            )

        outcome_text = (
            "EVALUATION RECORD:\n"
            +
            family[
                "raw_source"
            ]
        )

        outcome = (
            mnexa.observe_outcome(
                first_decision.record_id,
                outcome_text,
                success=False,
            )
        )

        source_evidence = (
            _source_evidence_text(
                first_decision.text,
                outcome_text,
            )
        )

        def consolidator(
            evidence: str,
        ) -> str:
            return lesson_text

        lesson = (
            mnexa.consolidate(
                first_decision.record_id,
                consolidator,
            )
        )

        transfer = (
            mnexa.decide(
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

        claim_audit = (
            _claim_audit(
                evidence_atoms
            )
        )

        memory_text = "\n".join(
            transfer.memory_segments
        )

        lesson_complete = (
            grade_text(
                lesson.text,
                family[
                    "knowledge_grader"
                ],
            )
        )

        transfer_sufficient = (
            grade_text(
                transfer.text,
                family[
                    "transfer_grader"
                ],
            )
        )

        return {
            "candidate_decision": (
                first_decision.text
            ),
            "outcome": (
                outcome_text
            ),
            "outcome_id": (
                outcome.object_id
            ),
            "source_evidence_sha256": (
                _sha256_text(
                    source_evidence
                )
            ),
            "lesson": (
                lesson.text
            ),
            "lesson_id": (
                lesson.object_id
            ),
            "lesson_knowledge_complete": (
                lesson_complete
            ),
            "transfer_decision": (
                transfer.text
            ),
            "transfer_task_sufficient": (
                transfer_sufficient
            ),
            "task_success": (
                transfer_sufficient
            ),
            "memory_segments": list(
                transfer.memory_segments
            ),
            "memory_word_count": (
                meter.count(
                    memory_text
                )
            ),
            "claims_admitted": (
                len(
                    claim_audit[
                        "admitted"
                    ]
                )
            ),
            "unsupported_claims_admitted": (
                claim_audit[
                    "unsupported_claims_admitted"
                ]
            ),
        }

    finally:
        mnexa.close()


def _count_invented_structured_components(
    *,
    propositions,
    source_text: str,
):
    invented_nuclei = 0
    invented_qualifiers = 0

    for proposition in propositions:

        if (
            source_text.count(
                proposition[
                    "nucleus_quote"
                ]
            )
            != 1
        ):
            invented_nuclei += 1

        for qualifier in proposition.get(
            "qualifiers",
            [],
        ):

            if (
                source_text.count(
                    qualifier[
                        "source_quote"
                    ]
                )
                != 1
            ):
                invented_qualifiers += 1

    return (
        invented_nuclei,
        invented_qualifiers,
    )


def run_family_011(
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
    # A — SEED 010 FLAT AUTONOMOUS SPAN DISCOVERY
    # ================================================================

    flat_raw_response = (
        model
        .generate(
            build_autonomous_boundary_prompt(
                source_text
            )
        )
        .text
        .strip()
    )

    try:

        flat_proposal = (
            parse_atom_proposal(
                flat_raw_response
            )
        )

        flat_parse_error = None

    except Exception as exc:

        flat_proposal = {
            "atoms": []
        }

        flat_parse_error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    flat_shared, flat_injected = (
        ensure_overlap_challenges(
            proposal=(
                flat_proposal
            ),
            family=family,
            source_text=(
                source_text
            ),
        )
    )

    flat_gate = (
        admit_autonomous_atoms(
            proposal=(
                flat_shared
            ),
            source_text=(
                source_text
            ),
        )
    )

    flat_atoms = (
        flat_gate[
            "admitted"
        ]
    )

    flat_lesson_text = (
        render_role_aware_claims(
            atoms=(
                flat_atoms
            )
        )
        if flat_atoms
        else
        "SUPPORTED CLAIMS:\n"
    )

    flat = (
        _run_memory_condition(
            condition_name=(
                "flat_autonomous"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                flat_lesson_text
            ),
            evidence_atoms=(
                flat_atoms
            ),
        )
    )

    flat_metrics = (
        canonical_boundary_metrics(
            admitted_atoms=(
                flat_atoms
            ),
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    flat_ancestry_valid = all(
        source_ancestry_valid(
            atom=atom,
            source_text=(
                source_text
            ),
        )

        for atom
        in flat_atoms
    )

    # ================================================================
    # B — STRUCTURED PROPOSITION EXTRACTION
    # ================================================================

    structured_raw_response = (
        model
        .generate(
            build_structured_proposition_prompt(
                source_text
            )
        )
        .text
        .strip()
    )

    try:

        structured_proposal = (
            parse_structured_proposal(
                structured_raw_response
            )
        )

        structured_parse_error = None

    except Exception as exc:

        structured_proposal = {
            "propositions": []
        }

        structured_parse_error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    structured_shared, structured_injected = (
        ensure_structured_compound_challenges(
            proposal=(
                structured_proposal
            ),
            family=family,
            source_text=(
                source_text
            ),
        )
    )

    structured_gate = (
        admit_structured_propositions(
            proposal=(
                structured_shared
            ),
            source_text=(
                source_text
            ),
        )
    )

    structured_propositions = (
        structured_gate[
            "admitted"
        ]
    )

    structured_lesson_text = (
        render_structured_propositions(
            structured_propositions
        )
    )

    structured_evidence_atoms = (
        _nucleus_atom_projection(
            structured_propositions
        )
    )

    structured = (
        _run_memory_condition(
            condition_name=(
                "structured_propositions"
            ),
            family=family,
            family_dir=(
                family_dir
            ),
            model=model,
            embedder=embedder,
            meter=meter,
            lesson_text=(
                structured_lesson_text
            ),
            evidence_atoms=(
                structured_evidence_atoms
            ),
        )
    )

    nucleus_metrics = (
        canonical_nucleus_metrics(
            admitted_propositions=(
                structured_propositions
            ),
            expected_units=family[
                "atomic_units"
            ],
        )
    )

    q_metrics = (
        qualifier_metrics(
            admitted_propositions=(
                structured_propositions
            ),
            expected_units=family[
                "atomic_units"
            ],
            expected_qualifiers=family[
                "expected_qualifiers"
            ],
        )
    )

    structured_ancestry_valid = all(
        structured_source_ancestry_valid(
            proposition=(
                proposition
            ),
            source_text=(
                source_text
            ),
        )

        for proposition
        in structured_propositions
    )

    (
        invented_nuclei,
        invented_qualifiers,
    ) = (
        _count_invented_structured_components(
            propositions=(
                structured_propositions
            ),
            source_text=(
                source_text
            ),
        )
    )

    nonauthoritative = sum(
        1

        for proposition
        in structured_propositions

        if (
            proposition[
                "source_role"
            ]
            !=
            AUTHORITATIVE_ROLE
        )
    )

    compound_nuclei = (
        _compound_nucleus_count(
            propositions=(
                structured_propositions
            ),
            family=family,
        )
    )

    challenge_rejections = (
        _structured_challenge_rejections(
            gate_result=(
                structured_gate
            ),
            family=family,
        )
    )

    same_source = (
        flat[
            "source_evidence_sha256"
        ]
        ==
        structured[
            "source_evidence_sha256"
        ]
    )

    if not same_source:
        raise RuntimeError(
            "011 invalid: flat and structured "
            "conditions received different "
            "historical source evidence."
        )

    return {
        "family_id": (
            family[
                "id"
            ]
        ),
        "style": (
            family[
                "style"
            ]
        ),

        "flat": {
            **flat,
            "raw_model_response": (
                flat_raw_response
            ),
            "parse_error": (
                flat_parse_error
            ),
            "model_proposal_count": (
                len(
                    flat_proposal.get(
                        "atoms",
                        [],
                    )
                )
            ),
            "challenge_injections": (
                flat_injected
            ),
            "admitted_atoms": (
                flat_atoms
            ),
            "source_ancestry_valid": (
                flat_ancestry_valid
            ),
            "overlapping_span_pairs": (
                count_overlapping_pairs(
                    flat_atoms
                )
            ),
            **flat_metrics,
        },

        "structured": {
            **structured,
            "raw_model_response": (
                structured_raw_response
            ),
            "parse_error": (
                structured_parse_error
            ),
            "model_proposal_count": (
                len(
                    structured_proposal.get(
                        "propositions",
                        [],
                    )
                )
            ),
            "challenge_injections": (
                structured_injected
            ),
            "admitted_propositions": (
                structured_propositions
            ),
            "source_ancestry_valid": (
                structured_ancestry_valid
            ),
            "invented_nuclei_admitted": (
                invented_nuclei
            ),
            "invented_qualifiers_admitted": (
                invented_qualifiers
            ),
            "nonauthoritative_propositions_admitted": (
                nonauthoritative
            ),
            "overlapping_nucleus_pairs": (
                count_nucleus_overlaps(
                    structured_propositions
                )
            ),
            "compound_nuclei_admitted": (
                compound_nuclei
            ),
            "structured_compound_challenge_rejections": (
                challenge_rejections
            ),
            **nucleus_metrics,
            **{
                "qualifier_recall": (
                    q_metrics[
                        "qualifier_recall"
                    ]
                ),
                "qualifier_precision": (
                    q_metrics[
                        "qualifier_precision"
                    ]
                ),
                "qualifier_expected": (
                    q_metrics[
                        "expected_qualifiers"
                    ]
                ),
                "qualifier_admitted": (
                    q_metrics[
                        "admitted_qualifiers"
                    ]
                ),
                "qualifier_matched": (
                    q_metrics[
                        "matched_qualifiers"
                    ]
                ),
                "qualifiers_complete": (
                    q_metrics[
                        "complete"
                    ]
                ),
            },
        },

        "same_source_evidence": (
            same_source
        ),

        "task_delta_flat_to_structured": (
            int(
                structured[
                    "task_success"
                ]
            )
            -
            int(
                flat[
                    "task_success"
                ]
            )
        ),

        "memory_word_delta_flat_to_structured": (
            structured[
                "memory_word_count"
            ]
            -
            flat[
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
                0.0,
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


def run_experiment_011(
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
        run_family_011(
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

    report = {
        "experiment": (
            "seed-growth-011"
        ),
        "classification": (
            "exploratory-fresh-grounded-"
            "structured-proposition-ablation"
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
                "seed010_flat_autonomous_"
                "exact_span_atomization"
            ),
            "B": (
                "grounded_structured_"
                "proposition_extraction"
            ),
        },

        "flat_task_passes": (
            _count(
                results,
                "flat",
                "task_success",
            )
        ),
        "structured_task_passes": (
            _count(
                results,
                "structured",
                "task_success",
            )
        ),

        "flat_complete_lessons": (
            _count(
                results,
                "flat",
                "lesson_knowledge_complete",
            )
        ),
        "structured_complete_lessons": (
            _count(
                results,
                "structured",
                "lesson_knowledge_complete",
            )
        ),

        "mean_flat_nucleus_recall": (
            _mean_metric(
                results,
                "flat",
                "canonical_recall",
            )
        ),
        "mean_structured_nucleus_recall": (
            _mean_metric(
                results,
                "structured",
                "nucleus_recall",
            )
        ),

        "mean_flat_nucleus_precision": (
            _mean_metric(
                results,
                "flat",
                "canonical_precision",
            )
        ),
        "mean_structured_nucleus_precision": (
            _mean_metric(
                results,
                "structured",
                "nucleus_precision",
            )
        ),

        "flat_exact_nucleus_families": (
            _count(
                results,
                "flat",
                "complete",
            )
        ),
        "structured_exact_nucleus_families": (
            _count(
                results,
                "structured",
                "complete",
            )
        ),

        "mean_structured_qualifier_recall": (
            _mean_metric(
                results,
                "structured",
                "qualifier_recall",
            )
        ),
        "mean_structured_qualifier_precision": (
            _mean_metric(
                results,
                "structured",
                "qualifier_precision",
            )
        ),
        "structured_full_qualifier_families": (
            _count(
                results,
                "structured",
                "qualifiers_complete",
            )
        ),

        "structured_source_ancestry_valid_families": (
            _count(
                results,
                "structured",
                "source_ancestry_valid",
            )
        ),

        "structured_invented_nuclei_admitted": (
            _sum_metric(
                results,
                "structured",
                "invented_nuclei_admitted",
            )
        ),
        "structured_invented_qualifiers_admitted": (
            _sum_metric(
                results,
                "structured",
                "invented_qualifiers_admitted",
            )
        ),
        "structured_nonauthoritative_propositions_admitted": (
            _sum_metric(
                results,
                "structured",
                "nonauthoritative_propositions_admitted",
            )
        ),
        "structured_overlapping_nucleus_pairs": (
            _sum_metric(
                results,
                "structured",
                "overlapping_nucleus_pairs",
            )
        ),
        "structured_compound_nuclei_admitted": (
            _sum_metric(
                results,
                "structured",
                "compound_nuclei_admitted",
            )
        ),
        "structured_unsupported_claims_admitted": (
            _sum_metric(
                results,
                "structured",
                "unsupported_claims_admitted",
            )
        ),

        "structured_compound_challenges": sum(
            len(
                family[
                    "structured_compound_challenges"
                ]
            )

            for family
            in payload[
                "families"
            ]
        ),

        "structured_compound_challenge_rejections": (
            _sum_metric(
                results,
                "structured",
                "structured_compound_challenge_rejections",
            )
        ),

        "mean_flat_memory_words": (
            _mean_metric(
                results,
                "flat",
                "memory_word_count",
            )
        ),
        "mean_structured_memory_words": (
            _mean_metric(
                results,
                "structured",
                "memory_word_count",
            )
        ),

        "flat_extraction_model_calls": (
            len(
                results
            )
        ),
        "structured_extraction_model_calls": (
            len(
                results
            )
        ),

        "all_source_evidence_equal": (
            all(
                family[
                    "same_source_evidence"
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
            "tasks_011.json"
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
        run_experiment_011(
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
        "flat_task_passes",
        "structured_task_passes",
        "flat_complete_lessons",
        "structured_complete_lessons",
        "mean_flat_nucleus_recall",
        "mean_structured_nucleus_recall",
        "mean_flat_nucleus_precision",
        "mean_structured_nucleus_precision",
        "flat_exact_nucleus_families",
        "structured_exact_nucleus_families",
        "mean_structured_qualifier_recall",
        "mean_structured_qualifier_precision",
        "structured_full_qualifier_families",
        "structured_source_ancestry_valid_families",
        "structured_invented_nuclei_admitted",
        "structured_invented_qualifiers_admitted",
        "structured_nonauthoritative_propositions_admitted",
        "structured_overlapping_nucleus_pairs",
        "structured_compound_nuclei_admitted",
        "structured_unsupported_claims_admitted",
        "structured_compound_challenges",
        "structured_compound_challenge_rejections",
        "mean_flat_memory_words",
        "mean_structured_memory_words",
        "all_source_evidence_equal",
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
