import json

from experiments.make_tasks_008 import build_taskset, build_raw_source
from experiments.seed_growth_008 import (
    AUTHORITATIVE_ROLE,
    INELIGIBLE_ROLES,
    admit_role_gated_atoms,
    authoritative_recall_precision,
    ensure_role_challenges,
    ground_span_atoms,
    parse_atom_proposal,
    parse_role_regions,
    role_for_span,
)


def _source():
    return build_raw_source(
        status="Run status was FAIL.",
        failed_decision="Restart the service.",
        authoritative_sentences=[
            "Refresh the recovery lease.",
            "Wait 5 seconds.",
            "Retry exactly once.",
            "Include X-Test-Recover: blue.",
        ],
        operator_note="Operator suspects transient network drift.",
        diagnostic_metadata="Observed diagnostic latency was 183 ms.",
    )


def _proposal(*texts):
    return {
        "atoms": [
            {
                "text": text,
                "source_quote": text,
            }
            for text in texts
        ]
    }


def test_role_regions_classify_exact_content_spans():
    source = _source()
    regions = parse_role_regions(source)

    authoritative = "Wait 5 seconds."
    start = source.index(authoritative)
    end = start + len(authoritative)

    assert role_for_span(start, end, regions) == AUTHORITATIVE_ROLE

    speculation = "Operator suspects transient network drift."
    start = source.index(speculation)
    end = start + len(speculation)

    assert role_for_span(start, end, regions) == "operator_note"


def test_span_only_grounding_accepts_grounded_nonknowledge():
    source = _source()
    proposal = _proposal(
        "Refresh the recovery lease.",
        "Operator suspects transient network drift.",
    )

    result = ground_span_atoms(
        proposal=proposal,
        source_text=source,
    )

    assert len(result["admitted"]) == 2
    assert {
        atom["source_role"]
        for atom in result["admitted"]
    } == {
        AUTHORITATIVE_ROLE,
        "operator_note",
    }


def test_role_gate_rejects_exact_but_ineligible_span():
    source = _source()
    proposal = _proposal(
        "Refresh the recovery lease.",
        "Operator suspects transient network drift.",
    )

    result = admit_role_gated_atoms(
        proposal=proposal,
        source_text=source,
    )

    assert [
        atom["text"]
        for atom in result["admitted"]
    ] == [
        "Refresh the recovery lease."
    ]

    assert any(
        rejection["reason"] == "ineligible_evidence_role"
        and rejection["source_role"] == "operator_note"
        for rejection in result["rejected"]
    )


def test_role_gate_rejects_failed_decision_status_and_metadata():
    source = _source()
    proposal = _proposal(
        "Run status was FAIL.",
        "Restart the service.",
        "Observed diagnostic latency was 183 ms.",
    )

    result = admit_role_gated_atoms(
        proposal=proposal,
        source_text=source,
    )

    assert result["admitted"] == []

    roles = {
        rejection["source_role"]
        for rejection in result["rejected"]
        if rejection["reason"] == "ineligible_evidence_role"
    }

    assert roles == {
        "status",
        "failed_decision",
        "diagnostic_metadata",
    }


def test_role_gate_still_rejects_citation_smuggling():
    source = _source()
    proposal = {
        "atoms": [
            {
                "text": "Restart the service.",
                "source_quote": "Refresh the recovery lease.",
            }
        ]
    }

    result = admit_role_gated_atoms(
        proposal=proposal,
        source_text=source,
    )

    assert result["admitted"] == []
    assert result["rejected"][0]["reason"] == "atom_not_equal_to_source_quote"


def test_authoritative_recall_precision_is_bounded():
    source = _source()
    expected = [
        "Refresh the recovery lease.",
        "Wait 5 seconds.",
        "Retry exactly once.",
        "Include X-Test-Recover: blue.",
    ]

    span_only = ground_span_atoms(
        proposal=_proposal(
            *expected,
            "Run status was FAIL.",
            "Restart the service.",
            "Operator suspects transient network drift.",
            "Observed diagnostic latency was 183 ms.",
        ),
        source_text=source,
    )

    metrics = authoritative_recall_precision(
        admitted_atoms=span_only["admitted"],
        expected_authoritative_texts=expected,
    )

    assert metrics["authoritative_recall"] == 1.0
    assert metrics["authoritative_precision"] == 0.5
    assert 0.0 <= metrics["authoritative_recall"] <= 1.0
    assert 0.0 <= metrics["authoritative_precision"] <= 1.0


def test_ensure_role_challenges_uses_same_proposal_for_b_and_c():
    source = _source()
    family = {
        "role_challenges": [
            {
                "role": "status",
                "text": "Run status was FAIL.",
            },
            {
                "role": "operator_note",
                "text": "Operator suspects transient network drift.",
            },
        ]
    }

    proposal, challenge_count = ensure_role_challenges(
        proposal=_proposal("Refresh the recovery lease."),
        family=family,
        source_text=source,
    )

    assert challenge_count == 2
    texts = {
        atom["text"]
        for atom in proposal["atoms"]
    }
    assert "Run status was FAIL." in texts
    assert "Operator suspects transient network drift." in texts


def test_atom_proposal_parser_accepts_json_fences():
    payload = {
        "atoms": [
            {
                "text": "Wait 5 seconds.",
                "source_quote": "Wait 5 seconds.",
            }
        ]
    }

    parsed = parse_atom_proposal(
        "```json\n"
        + json.dumps(payload)
        + "\n```"
    )

    assert parsed == payload


def test_008_has_twenty_fresh_unique_families():
    payload = build_taskset()
    families = payload["families"]

    assert len(families) == 20
    assert len({family["id"] for family in families}) == 20

    for family in families:
        assert family["experience"]["prompt"] != family["transfer"]["prompt"]
        assert len(family["authoritative_atoms"]) == 4
        assert family["transfer_required_atom_ids"]
        assert set(family["transfer_required_atom_ids"]).issubset(
            {atom["id"] for atom in family["authoritative_atoms"]}
        )


def test_008_fixture_roles_and_authoritative_spans_are_valid():
    payload = build_taskset()

    for family in payload["families"]:
        source = family["raw_source"]
        regions = parse_role_regions(source)

        assert {
            region["role"]
            for region in regions
        } == {
            AUTHORITATIVE_ROLE,
            *INELIGIBLE_ROLES,
        }

        for atom in family["authoritative_atoms"]:
            assert source.count(atom["text"]) == 1
            start = source.index(atom["text"])
            end = start + len(atom["text"])
            assert role_for_span(start, end, regions) == AUTHORITATIVE_ROLE

        for challenge in family["role_challenges"]:
            assert source.count(challenge["text"]) == 1
            start = source.index(challenge["text"])
            end = start + len(challenge["text"])
            assert role_for_span(start, end, regions) == challenge["role"]
            assert challenge["role"] in INELIGIBLE_ROLES
