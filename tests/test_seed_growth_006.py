import json

from experiments.make_tasks_006 import build_taskset

from experiments.seed_growth_006 import (
    admit_claims,
    build_claim_ancestry_prompt,
    normalize_claim_text,
    parse_claim_proposal,
    run_family_006,
)

from model_adapter import Generation


class FakeEmbedder:
    vocab = (
        "ax9",
        "lease",
        "restart",
        "recover",
    )

    def embed(self, text):
        words = text.lower().split()

        return [
            float(
                sum(
                    token in word
                    for word in words
                )
            )
            for token in self.vocab
        ]


class WordMeter:
    name = "word-meter-v1"

    def count(self, text):
        return len(text.split())


class ClaimAncestryModel:
    name = "claim-ancestry-test-model"

    def generate(self, prompt):
        low = prompt.lower()

        # ----------------------------------------------------------
        # Condition C consolidation
        # ----------------------------------------------------------

        if "claim ancestry consolidation" in low:
            payload = {
                "claims": [
                    {
                        "text": "Refresh the recovery lease.",
                        "evidence_ids": ["E1"],
                    },
                    {
                        "text": "Wait 4 seconds.",
                        "evidence_ids": ["E2"],
                    },
                    {
                        "text": "Retry exactly once.",
                        "evidence_ids": ["E3"],
                    },
                    {
                        "text": "Include X-Test-Recover: blue.",
                        "evidence_ids": ["E4"],
                    },

                    # Model attempts to smuggle unsupported
                    # content under a real citation.
                    {
                        "text": "Restart the payment service.",
                        "evidence_ids": ["E1"],
                    },
                ]
            }

            return Generation(
                text=json.dumps(payload),
                input_tokens=None,
                output_tokens=None,
                response_id=None,
            )

        # ----------------------------------------------------------
        # Condition B consolidation
        # ----------------------------------------------------------

        if (
            "epistemically disciplined consolidation"
            in low
        ):
            text = """
TRIGGER:
Restarting the payment service.

REUSABLE RULE:
Restart the payment service, refresh the recovery lease,
wait 4 seconds, retry exactly once, and include
X-Test-Recover: blue.

CRITICAL CONSTRAINTS:
- Refresh the recovery lease.
- Wait 4 seconds.
- Retry exactly once.
- Include X-Test-Recover: blue.
""".strip()

            return Generation(
                text=text,
                input_tokens=None,
                output_tokens=None,
                response_id=None,
            )

        # ----------------------------------------------------------
        # Transfer reasoning
        # ----------------------------------------------------------

        if (
            "decision-fidelity requirement"
            in low
            and "x-test-recover" in low
        ):
            if (
                "restart the payment service"
                in low
            ):
                text = (
                    "Restart the payment service. "
                    "Refresh the recovery lease. "
                    "Wait 4 seconds. "
                    "Retry exactly once. "
                    "Include X-Test-Recover: blue."
                )
            else:
                text = (
                    "Refresh the recovery lease. "
                    "Wait 4 seconds. "
                    "Retry exactly once. "
                    "Include X-Test-Recover: blue."
                )

            return Generation(
                text=text,
                input_tokens=None,
                output_tokens=None,
                response_id=None,
            )

        return Generation(
            text="Consult documentation.",
            input_tokens=None,
            output_tokens=None,
            response_id=None,
        )


def _family():
    return {
        "id": "test-ax9",

        "entities": [
            "system:testsystem",
            "code:ax9",
        ],

        "experience": {
            "prompt": (
                "TestSystem returns AX9 "
                "during operation A."
            )
        },

        "transfer": {
            "prompt": (
                "TestSystem returns AX9 "
                "during operation B."
            )
        },

        "candidate_decision": (
            "Restart the payment service."
        ),

        "correction": (
            "AX9 authoritative correction: "
            "Refresh the recovery lease. "
            "Wait 4 seconds. "
            "Retry exactly once. "
            "Include X-Test-Recover: blue."
        ),

        "evidence_atoms": [
            {
                "id": "E1",
                "text": "Refresh the recovery lease.",
                "task_pattern": (
                    r"refresh.*recovery\s+lease"
                ),
            },
            {
                "id": "E2",
                "text": "Wait 4 seconds.",
                "task_pattern": (
                    r"\b4\s*seconds?\b"
                ),
            },
            {
                "id": "E3",
                "text": "Retry exactly once.",
                "task_pattern": (
                    r"retry.*exactly\s+once"
                ),
            },
            {
                "id": "E4",
                "text": "Include X-Test-Recover: blue.",
                "task_pattern": (
                    r"x-test-recover.*blue"
                ),
            },
        ],

        "correct_grader": {
            "all_regex": [
                [r"refresh.*recovery\s+lease"],
                [r"\b4\s*seconds?\b"],
                [r"retry.*exactly\s+once"],
                [r"x-test-recover.*blue"],
            ]
        },

        "contamination_regex": [
            r"restart.*payment\s+service",
        ],
    }


def test_normalization_is_stable():
    assert (
        normalize_claim_text(
            " Refresh the recovery lease. "
        )
        ==
        normalize_claim_text(
            "refresh the recovery lease"
        )
    )


def test_claim_proposal_parser_handles_json():
    proposal = parse_claim_proposal(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Wait 4 seconds.",
                        "evidence_ids": ["E2"],
                    }
                ]
            }
        )
    )

    assert (
        proposal["claims"][0]["text"]
        ==
        "Wait 4 seconds."
    )


def test_admission_accepts_exact_supported_claim():
    family = _family()

    result = admit_claims(
        {
            "claims": [
                {
                    "text": "Wait 4 seconds.",
                    "evidence_ids": ["E2"],
                }
            ]
        },
        family["evidence_atoms"],
    )

    assert len(
        result["admitted"]
    ) == 1

    assert (
        result["admitted"][0][
            "evidence_ids"
        ]
        ==
        ["E2"]
    )

    assert not result[
        "rejected"
    ]


def test_admission_rejects_unsupported_text_even_with_real_id():
    family = _family()

    result = admit_claims(
        {
            "claims": [
                {
                    "text": (
                        "Restart the payment service."
                    ),
                    "evidence_ids": ["E1"],
                }
            ]
        },
        family["evidence_atoms"],
    )

    assert not result[
        "admitted"
    ]

    assert (
        result["rejected"][0][
            "reason"
        ]
        ==
        "claim_not_equal_to_cited_evidence"
    )


def test_admission_rejects_unknown_evidence():
    family = _family()

    result = admit_claims(
        {
            "claims": [
                {
                    "text": "Wait 4 seconds.",
                    "evidence_ids": ["E999"],
                }
            ]
        },
        family["evidence_atoms"],
    )

    assert not result[
        "admitted"
    ]

    assert (
        result["rejected"][0][
            "reason"
        ]
        ==
        "unknown_evidence"
    )


def test_admission_requires_one_atomic_evidence_parent():
    family = _family()

    result = admit_claims(
        {
            "claims": [
                {
                    "text": "Wait 4 seconds.",
                    "evidence_ids": [
                        "E1",
                        "E2",
                    ],
                }
            ]
        },
        family["evidence_atoms"],
    )

    assert not result[
        "admitted"
    ]

    assert (
        result["rejected"][0][
            "reason"
        ]
        ==
        "non_atomic_ancestry"
    )


def test_prompt_contains_evidence_ids():
    family = _family()

    prompt = build_claim_ancestry_prompt(
        evidence=(
            "DECISION: Restart service.\n"
            "OUTCOME: authoritative correction."
        ),
        family=family,
    )

    low = prompt.lower()

    assert (
        "claim ancestry consolidation"
        in low
    )

    assert "e1" in low
    assert "e2" in low

    assert (
        "copy the evidence atom text exactly"
        in low
    )


def test_claim_ancestry_blocks_unsupported_memory(
    tmp_path,
):
    result = run_family_006(
        family=_family(),
        work_dir=tmp_path,
        model=ClaimAncestryModel(),
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    current = result[
        "mnexa_evidence_disciplined"
    ]

    ancestry = result[
        "mnexa_claim_ancestry"
    ]

    assert result[
        "same_source_evidence"
    ] is True

    # Current policy can still carry an unsupported
    # proposition into memory.
    assert current[
        "lesson_contaminated"
    ] is True

    assert current[
        "transfer_contaminated"
    ] is True

    assert current[
        "task_success"
    ] is False

    # Claim ancestry rejects the smuggled proposition.
    assert ancestry[
        "lesson_contaminated"
    ] is False

    assert ancestry[
        "transfer_contaminated"
    ] is False

    assert ancestry[
        "task_success"
    ] is True

    assert ancestry[
        "ancestry_coverage"
    ] == 1.0

    assert ancestry[
        "unsupported_claims_admitted"
    ] == 0

    assert ancestry[
        "rejected_claim_count"
    ] == 1


def test_006_has_twenty_fresh_unique_families():
    payload = build_taskset()

    families = payload[
        "families"
    ]

    assert len(
        families
    ) == 20

    ids = [
        family["id"]
        for family in families
    ]

    assert len(
        ids
    ) == len(
        set(ids)
    )

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

        atoms = family[
            "evidence_atoms"
        ]

        assert len(atoms) >= 4

        evidence_ids = [
            atom["id"]
            for atom in atoms
        ]

        assert len(
            evidence_ids
        ) == len(
            set(evidence_ids)
        )


def test_006_fixture_integrity():
    from experiments.seed_growth import (
        grade_text,
    )

    from experiments.seed_growth_006 import (
        contains_any_regex,
    )

    payload = build_taskset()

    for family in payload[
        "families"
    ]:

        correction = family[
            "correction"
        ]

        assert grade_text(
            correction,
            family[
                "correct_grader"
            ],
        ), family["id"]

        assert contains_any_regex(
            family[
                "candidate_decision"
            ],
            family[
                "contamination_regex"
            ],
        ), family["id"]

        assert not contains_any_regex(
            correction,
            family[
                "contamination_regex"
            ],
        ), family["id"]

        for atom in family[
            "evidence_atoms"
        ]:
            assert (
                atom["text"]
                in correction
            ), (
                family["id"],
                atom["id"],
            )
