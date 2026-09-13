import json

from experiments.make_tasks_007 import build_taskset

from experiments.seed_growth_007 import (
    admit_claims,
    admit_grounded_atoms,
    build_atom_discovery_prompt,
    build_claim_ancestry_prompt,
    normalize_claim_text,
    parse_atom_proposal,
    parse_claim_proposal,
    run_family_007,
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


class ClaimAncestryModel007:
    name = "claim-ancestry-007-test-model"

    def generate(self, prompt):
        low = prompt.lower()

        # ----------------------------------------------------------
        # Condition C atom discovery
        # ----------------------------------------------------------
        if "raw evidence atomization" in low:
            payload = {
                "atoms": [
                    {
                        "text": "Refresh the recovery lease.",
                        "source_quote": "Refresh the recovery lease.",
                    },
                    {
                        "text": "Wait 4 seconds.",
                        "source_quote": "Wait 4 seconds.",
                    },
                    {
                        "text": "Retry exactly once.",
                        "source_quote": "Retry exactly once.",
                    },
                    {
                        "text": "Include X-Test-Recover: blue.",
                        "source_quote": "Include X-Test-Recover: blue.",
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
        # Condition B / C claim consolidation
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
                ]
            }
            return Generation(
                text=json.dumps(payload),
                input_tokens=None,
                output_tokens=None,
                response_id=None,
            )

        # ----------------------------------------------------------
        # Transfer reasoning
        # ----------------------------------------------------------
        if (
            "decision-fidelity requirement" in low
            and "x-test-recover" in low
        ):
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
    raw_correction = (
        "AX9 authoritative correction: "
        "Refresh the recovery lease. "
        "Wait 4 seconds. "
        "Retry exactly once. "
        "Include X-Test-Recover: blue."
    )

    return {
        "id": "test-ax9-007",

        "entities": [
            "system:testsystem",
            "code:ax9",
        ],

        "experience": {
            "prompt": "TestSystem returns AX9 during operation A."
        },

        "transfer": {
            "prompt": "TestSystem returns AX9 during operation B."
        },

        "candidate_decision": "Restart the payment service.",

        "correction": raw_correction,

        "oracle_evidence_atoms": [
            {
                "id": "E1",
                "text": "Refresh the recovery lease.",
                "source_quote": "Refresh the recovery lease.",
                "task_pattern": r"refresh.*recovery\s+lease",
            },
            {
                "id": "E2",
                "text": "Wait 4 seconds.",
                "source_quote": "Wait 4 seconds.",
                "task_pattern": r"\b4\s*seconds?\b",
            },
            {
                "id": "E3",
                "text": "Retry exactly once.",
                "source_quote": "Retry exactly once.",
                "task_pattern": r"retry.*exactly\s+once",
            },
            {
                "id": "E4",
                "text": "Include X-Test-Recover: blue.",
                "source_quote": "Include X-Test-Recover: blue.",
                "task_pattern": r"x-test-recover.*blue",
            },
        ],

        "adversarial_atom_challenges": [
            {
                "text": "Restart the payment service.",
                "source_quote": "Restart the payment service.",
            },
            {
                "text": "Restart the payment service.",
                "source_quote": "Refresh the recovery lease.",
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

        "transfer_grader": {
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


def test_atom_proposal_parser_handles_json():
    proposal = parse_atom_proposal(
        json.dumps(
            {
                "atoms": [
                    {
                        "text": "Wait 4 seconds.",
                        "source_quote": "Wait 4 seconds.",
                    }
                ]
            }
        )
    )

    assert proposal["atoms"][0]["text"] == "Wait 4 seconds."


def test_grounding_accepts_valid_quote():
    family = _family()

    result = admit_grounded_atoms(
        {
            "atoms": [
                {
                    "text": "Wait 4 seconds.",
                    "source_quote": "Wait 4 seconds.",
                }
            ]
        },
        family["correction"],
    )

    assert len(result["admitted"]) == 1
    assert result["admitted"][0]["text"] == "Wait 4 seconds."
    assert not result["rejected"]


def test_grounding_rejects_nonexistent_quote():
    family = _family()

    result = admit_grounded_atoms(
        {
            "atoms": [
                {
                    "text": "Restart the payment service.",
                    "source_quote": "Restart the payment service.",
                }
            ]
        },
        family["correction"],
    )

    assert not result["admitted"]
    assert result["rejected"][0]["reason"] == "quote_not_in_source"


def test_grounding_rejects_citation_smuggling():
    family = _family()

    result = admit_grounded_atoms(
        {
            "atoms": [
                {
                    "text": "Restart the payment service.",
                    "source_quote": "Refresh the recovery lease.",
                }
            ]
        },
        family["correction"],
    )

    assert not result["admitted"]
    assert result["rejected"][0]["reason"] == "claim_not_equal_to_quote"


def test_run_family_007_executes_all_conditions(tmp_path):
    result = run_family_007(
        family=_family(),
        work_dir=tmp_path,
        model=ClaimAncestryModel007(),
        embedder=FakeEmbedder(),
        meter=WordMeter(),
    )

    assert result["same_source_evidence"] is True
    assert result["mnexa_raw_span"]["task_success"] is True
    assert result["mnexa_raw_span"]["adversarial_atom_rejections"] == 2
    assert result["mnexa_raw_span"]["ungrounded_atoms_admitted"] == 0


def test_007_has_twenty_fresh_families():
    payload = build_taskset()

    families = payload["families"]

    assert len(families) == 20

    ids = [family["id"] for family in families]

    assert len(ids) == len(set(ids))

    for family in families:
        assert (
            family["experience"]["prompt"]
            != family["transfer"]["prompt"]
        )

        atoms = family["oracle_evidence_atoms"]

        assert len(atoms) >= 4

        for atom in atoms:
            assert atom["source_quote"] in family["correction"]

        challenges = family["adversarial_atom_challenges"]
        assert len(challenges) == 2
