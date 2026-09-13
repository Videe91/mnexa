from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from mnexa_seed import MnexaSeed

from experiments.seed_growth import (
    grade_text,
)

from experiments.seed_growth_004 import (
    make_fidelity_reasoner,
)

from experiments.seed_growth_006 import (
    CLAIM_ANCESTRY_INSTRUCTION,
    admit_claims,
    build_claim_ancestry_prompt,
    contains_any_regex,
    make_claim_ancestry_consolidator,
    normalize_claim_text,
    parse_claim_proposal,
    render_admitted_claims,
)

from model_adapter import (
    OpenAIResponsesModel,
    SentenceTransformerEmbedder,
    WordMeter,
)


RAW_ATOMIZATION_INSTRUCTION = """
RAW EVIDENCE ATOMIZATION

You are extracting atomic facts from authoritative historical evidence.

This experiment uses a DETERMINISTIC SPAN GROUNDING admission rule.

Rules:

1. Extract distinct, atomic operational propositions.
2. For each proposition, provide:
   - "text": clean statement of the atomic proposition
   - "source_quote": EXACT substring quote from the raw evidence text
3. Do not paraphrase or alter the source_quote.
4. Do not include propositions that do not exist as exact quotes in the evidence.
5. Do not include private reasoning.

Return JSON only:

{
  "atoms": [
    {
      "text": "<proposition text>",
      "source_quote": "<exact source quote>"
    }
  ]
}
""".strip()


def _strip_json_fence(
    text: str,
) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def parse_atom_proposal(text: str):
    payload = json.loads(_strip_json_fence(text))

    if not isinstance(payload, dict):
        raise ValueError("Atom proposal must be a JSON object.")

    atoms = payload.get("atoms")

    if not isinstance(atoms, list):
        raise ValueError("Atom proposal must contain an atoms list.")

    return payload


def admit_grounded_atoms(
    proposal,
    raw_evidence: str,
):
    """
    v0 deterministic span grounding.

    Admits an evidence atom only if:
    1. source_quote is present in raw_evidence.
    2. source_quote occurs EXACTLY ONCE in raw_evidence (unique span).
    3. normalized(text) == normalized(source_quote).

    Returns admitted atoms with offsets, hashes, and rejection reasons.
    """
    admitted = []
    rejected = []
    admitted_spans = set()

    atoms = proposal.get("atoms", [])

    for index, item in enumerate(atoms):
        if not isinstance(item, dict):
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "atom_not_object",
                }
            )
            continue

        text = item.get("text")
        source_quote = item.get("source_quote")

        if not isinstance(text, str) or not text.strip():
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "missing_text",
                }
            )
            continue

        if not isinstance(source_quote, str) or not source_quote.strip():
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "missing_source_quote",
                }
            )
            continue

        if normalize_claim_text(text) != normalize_claim_text(source_quote):
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "claim_not_equal_to_quote",
                }
            )
            continue

        count = raw_evidence.count(source_quote)

        if count == 0:
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "quote_not_in_source",
                }
            )
            continue

        if count > 1:
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "quote_ambiguous_in_source",
                }
            )
            continue

        start = raw_evidence.find(source_quote)
        end = start + len(source_quote)
        span_key = (start, end)

        if span_key in admitted_spans:
            rejected.append(
                {
                    "index": index,
                    "item": item,
                    "reason": "duplicate_span",
                }
            )
            continue

        atom_id = f"E{len(admitted) + 1}"
        sha256 = hashlib.sha256(source_quote.encode("utf-8")).hexdigest()

        admitted.append(
            {
                "id": atom_id,
                "text": source_quote.strip(),
                "source_quote": source_quote,
                "start": start,
                "end": end,
                "sha256": sha256,
            }
        )
        admitted_spans.add(span_key)

    return {
        "admitted": admitted,
        "rejected": rejected,
        "ungrounded_atoms_admitted": 0,
    }


def build_atom_discovery_prompt(evidence: str) -> str:
    return f"""
{RAW_ATOMIZATION_INSTRUCTION}

--- RAW HISTORICAL EVIDENCE START ---
{evidence}
--- RAW HISTORICAL EVIDENCE END ---

Return JSON only.
""".strip()


def _source_evidence_text(
    candidate_decision: str,
    outcome_text: str,
) -> str:
    return (
        "DECISION: "
        + candidate_decision
        + "\n"
        + "OUTCOME: "
        + outcome_text
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _controlled_candidate_reasoner(candidate_decision: str):
    def reasoner(task: str, context: str) -> str:
        return candidate_decision

    return reasoner


def _score_text(text: str, family):
    correct_complete = grade_text(text, family["correct_grader"])
    correct_transfer = grade_text(
        text, family.get("transfer_grader", family["correct_grader"])
    )
    contaminated = contains_any_regex(text, family["contamination_regex"])

    return {
        "complete_knowledge": correct_complete,
        "transfer_knowledge": correct_transfer,
        "designated_contamination": contaminated,
        "task_success": correct_transfer and not contaminated,
    }


def _run_memory_condition_007(
    *,
    condition_name,
    family,
    family_dir,
    model,
    embedder,
    meter,
    consolidator_factory,
):
    db_path = family_dir / f"{condition_name}.sqlite3"

    if db_path.exists():
        db_path.unlink()

    mnexa = MnexaSeed(
        db_path,
        embedder=embedder,
        meter=meter,
    )

    audit = {}

    candidate_reasoner = _controlled_candidate_reasoner(
        family["candidate_decision"]
    )

    transfer_reasoner = make_fidelity_reasoner(model)

    try:
        experience_decision = mnexa.decide(
            family["experience"]["prompt"],
            tuple(family["entities"]),
            candidate_reasoner,
        )

        if experience_decision.text != family["candidate_decision"]:
            raise RuntimeError("Controlled candidate decision changed.")

        outcome_text = (
            "EVALUATION: FAIL.\n"
            "AUTHORITATIVE CORRECTION:\n"
            + family["correction"]
        )

        outcome = mnexa.observe_outcome(
            experience_decision.record_id,
            outcome_text,
            success=False,
        )

        source_evidence = _source_evidence_text(
            experience_decision.text,
            outcome_text,
        )

        source_evidence_sha256 = _sha256_text(source_evidence)

        consolidator = consolidator_factory(audit, outcome_text)

        lesson = mnexa.consolidate(
            experience_decision.record_id,
            consolidator,
        )

        lesson_score = _score_text(lesson.text, family)

        transfer = mnexa.decide(
            family["transfer"]["prompt"],
            tuple(family["entities"]),
            transfer_reasoner,
        )

        transfer_score = _score_text(transfer.text, family)

        result = {
            "candidate_decision": experience_decision.text,
            "outcome": outcome_text,
            "outcome_id": outcome.object_id,
            "source_evidence_sha256": source_evidence_sha256,
            "lesson": lesson.text,
            "lesson_id": lesson.object_id,
            "lesson_complete_knowledge": lesson_score["complete_knowledge"],
            "lesson_contaminated": lesson_score["designated_contamination"],
            "transfer_decision": transfer.text,
            "transfer_correct_knowledge": transfer_score["transfer_knowledge"],
            "transfer_contaminated": transfer_score["designated_contamination"],
            "task_success": transfer_score["task_success"],
            "memory_segments": list(transfer.memory_segments),
        }

        result.update(audit)
        return result

    finally:
        mnexa.close()


def run_family_007(
    *,
    family,
    work_dir: Path,
    model,
    embedder,
    meter,
):
    family_dir = Path(work_dir) / family["id"]
    family_dir.mkdir(parents=True, exist_ok=True)

    # ================================================================
    # A — NO MEMORY
    # ================================================================
    baseline_db = family_dir / "baseline.sqlite3"
    if baseline_db.exists():
        baseline_db.unlink()

    baseline = MnexaSeed(
        baseline_db,
        embedder=embedder,
        meter=meter,
    )

    transfer_reasoner = make_fidelity_reasoner(model)

    try:
        baseline_decision = baseline.decide(
            family["transfer"]["prompt"],
            tuple(family["entities"]),
            transfer_reasoner,
        )

        baseline_score = _score_text(baseline_decision.text, family)

        baseline_result = {
            "decision": baseline_decision.text,
            "correct_knowledge": baseline_score["transfer_knowledge"],
            "designated_contamination": baseline_score["designated_contamination"],
            "task_success": baseline_score["task_success"],
        }
    finally:
        baseline.close()

    # ================================================================
    # B — ORACLE GROUNDED CLAIMS (Seed Growth 006 style upper bound)
    # ================================================================
    oracle = _run_memory_condition_007(
        condition_name="oracle_grounded",
        family=family,
        family_dir=family_dir,
        model=model,
        embedder=embedder,
        meter=meter,
        consolidator_factory=lambda audit, outcome_text: make_claim_ancestry_consolidator(
            model,
            family={"evidence_atoms": family["oracle_evidence_atoms"]},
            audit=audit,
        ),
    )

    # ================================================================
    # C — RAW EVIDENCE ATOMIZATION + DETERMINISTIC SPAN GROUNDING
    # ================================================================
    def make_raw_span_consolidator(audit, outcome_text):
        def consolidator(evidence: str) -> str:
            atom_prompt = build_atom_discovery_prompt(outcome_text)
            raw_atom_resp = model.generate(atom_prompt).text.strip()

            audit["raw_atom_model_response"] = raw_atom_resp

            try:
                proposed_atoms_payload = parse_atom_proposal(raw_atom_resp)
            except Exception as exc:
                proposed_atoms_payload = {"atoms": []}
                audit["atom_parse_error"] = f"{type(exc).__name__}: {exc}"

            raw_proposed_items = list(proposed_atoms_payload.get("atoms", []))
            audit["raw_model_atom_proposals_count"] = len(raw_proposed_items)

            # Append adversarial atom challenges to test runtime gate rejections
            challenges = family.get("adversarial_atom_challenges", [])
            combined_items = raw_proposed_items + challenges

            grounding_res = admit_grounded_atoms(
                {"atoms": combined_items},
                outcome_text,
            )

            admitted_atoms = grounding_res["admitted"]
            rejected_atoms = grounding_res["rejected"]

            # Calculate adversarial rejections specifically
            adv_rejections = sum(
                1
                for r in rejected_atoms
                if any(
                    r.get("item", {}).get("text") == c["text"]
                    and r.get("item", {}).get("source_quote") == c["source_quote"]
                    for c in challenges
                )
            )

            audit["model_atom_proposals"] = len(raw_proposed_items)
            audit["adversarial_atom_challenges"] = len(challenges)
            audit["adversarial_atom_rejections"] = adv_rejections
            audit["grounded_atoms_count"] = len(admitted_atoms)
            audit["rejected_atoms_count"] = len(rejected_atoms)
            audit["ungrounded_atoms_admitted"] = grounding_res[
                "ungrounded_atoms_admitted"
            ]

            oracle_count = len(family["oracle_evidence_atoms"])
            audit["source_span_coverage"] = (
                len(admitted_atoms) / oracle_count if oracle_count else 1.0
            )

            # Now pass admitted grounded atoms into claim ancestry consolidator
            claim_consolidator = make_claim_ancestry_consolidator(
                model,
                family={"evidence_atoms": admitted_atoms},
                audit=audit,
            )

            return claim_consolidator(evidence)

        return consolidator

    raw_span = _run_memory_condition_007(
        condition_name="raw_span_grounded",
        family=family,
        family_dir=family_dir,
        model=model,
        embedder=embedder,
        meter=meter,
        consolidator_factory=make_raw_span_consolidator,
    )

    same_source_evidence = (
        oracle["source_evidence_sha256"] == raw_span["source_evidence_sha256"]
    )

    if not same_source_evidence:
        raise RuntimeError("007 ablation invalid: B and C received different historical source evidence.")

    return {
        "family_id": family["id"],
        "baseline": baseline_result,
        "mnexa_oracle": oracle,
        "mnexa_raw_span": raw_span,
        "same_source_evidence": same_source_evidence,
    }


def _count(results, condition, metric):
    return sum(
        int(family[condition].get(metric, False))
        for family in results
    )


def _sum_metric(results, condition, metric):
    return sum(
        int(family[condition].get(metric, 0))
        for family in results
    )


def run_experiment_007(
    *,
    tasks_path: Path,
    results_dir: Path,
    model,
    embedder,
    meter,
):
    tasks_path = Path(tasks_path)
    payload = json.loads(tasks_path.read_text())
    taskset_sha256 = hashlib.sha256(tasks_path.read_bytes()).hexdigest()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(results_dir) / run_id
    state_dir = run_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    results = [
        run_family_007(
            family=family,
            work_dir=state_dir,
            model=model,
            embedder=embedder,
            meter=meter,
        )
        for family in payload["families"]
    ]

    span_coverages = [
        family["mnexa_raw_span"].get("source_span_coverage", 0.0)
        for family in results
    ]

    report = {
        "experiment": "seed-growth-007",
        "classification": "exploratory-fresh-raw-evidence-atomization-ablation",
        "run_id": run_id,
        "taskset_sha256": taskset_sha256,
        "model": getattr(model, "name", type(model).__name__),
        "embedder": getattr(embedder, "name", type(embedder).__name__),
        "meter": getattr(meter, "name", type(meter).__name__),
        "task_count": len(results),
        "conditions": {
            "A": "baseline_no_memory",
            "B": "mnexa_oracle_grounded_claims",
            "C": "mnexa_raw_span_grounded_claims",
        },
        "baseline_task_passes": _count(results, "baseline", "task_success"),
        "oracle_task_passes": _count(results, "mnexa_oracle", "task_success"),
        "raw_span_task_passes": _count(results, "mnexa_raw_span", "task_success"),
        "oracle_complete_lessons": _count(
            results, "mnexa_oracle", "lesson_complete_knowledge"
        ),
        "raw_span_complete_lessons": _count(
            results, "mnexa_raw_span", "lesson_complete_knowledge"
        ),
        "oracle_contaminated_lessons": _count(
            results, "mnexa_oracle", "lesson_contaminated"
        ),
        "raw_span_contaminated_lessons": _count(
            results, "mnexa_raw_span", "lesson_contaminated"
        ),
        "raw_span_model_atom_proposals": _sum_metric(
            results, "mnexa_raw_span", "model_atom_proposals"
        ),
        "raw_span_grounded_atoms": _sum_metric(
            results, "mnexa_raw_span", "grounded_atoms_count"
        ),
        "raw_span_rejected_atoms": _sum_metric(
            results, "mnexa_raw_span", "rejected_atoms_count"
        ),
        "adversarial_atom_challenges": _sum_metric(
            results, "mnexa_raw_span", "adversarial_atom_challenges"
        ),
        "adversarial_atom_rejections": _sum_metric(
            results, "mnexa_raw_span", "adversarial_atom_rejections"
        ),
        "ungrounded_atoms_admitted": _sum_metric(
            results, "mnexa_raw_span", "ungrounded_atoms_admitted"
        ),
        "mean_source_span_coverage": (
            sum(span_coverages) / len(span_coverages) if span_coverages else 0.0
        ),
        "full_source_span_coverage_families": sum(
            int(coverage == 1.0) for coverage in span_coverages
        ),
        "unsupported_claims_admitted": _sum_metric(
            results, "mnexa_raw_span", "unsupported_claims_admitted"
        ),
        "all_source_evidence_equal": all(
            family["same_source_evidence"] for family in results
        ),
        "raw_atomization_instruction": RAW_ATOMIZATION_INSTRUCTION,
        "families": results,
    }

    output = run_dir / "result.json"
    output.write_text(json.dumps(report, indent=2) + "\n")

    return report, output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="experiments/tasks_007.json")
    parser.add_argument("--results", default="experiments/results")

    args = parser.parse_args()

    model_name = os.environ.get("MNEXA_MODEL")
    if not model_name:
        raise SystemExit("Set MNEXA_MODEL.")

    model = OpenAIResponsesModel(model_name)
    embedder = SentenceTransformerEmbedder(
        os.environ.get(
            "MNEXA_EMBED_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    report, output = run_experiment_007(
        tasks_path=Path(args.tasks),
        results_dir=Path(args.results),
        model=model,
        embedder=embedder,
        meter=WordMeter(),
    )

    keys = (
        "experiment",
        "taskset_sha256",
        "baseline_task_passes",
        "oracle_task_passes",
        "raw_span_task_passes",
        "oracle_complete_lessons",
        "raw_span_complete_lessons",
        "oracle_contaminated_lessons",
        "raw_span_contaminated_lessons",
        "raw_span_model_atom_proposals",
        "raw_span_grounded_atoms",
        "raw_span_rejected_atoms",
        "adversarial_atom_challenges",
        "adversarial_atom_rejections",
        "ungrounded_atoms_admitted",
        "mean_source_span_coverage",
        "full_source_span_coverage_families",
        "unsupported_claims_admitted",
        "all_source_evidence_equal",
    )

    summary = {key: report[key] for key in keys}
    summary["result"] = str(output)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
