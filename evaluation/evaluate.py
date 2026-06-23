from __future__ import annotations

import argparse
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository, write_json
from clinicalbridge.orchestrator import ClinicalBridge
from clinicalbridge.schemas import WorkflowResult
from clinicalbridge.tools import tokenize

ROOT = Path(__file__).resolve().parents[1]


def _brief_text(result: WorkflowResult) -> str:
    brief = result.brief
    return " ".join(
        [
            brief.alert_summary,
            brief.patient_snapshot,
            *[item.text for item in brief.contextual_analysis],
            *[item.text for item in brief.risk_assessment],
            *[item.action for item in brief.recommended_actions],
            *[item.rationale for item in brief.recommended_actions],
            *brief.uncertainties_and_gaps,
        ]
    ).lower()


def _keyword_coverage(expected: list[str], actual_text: str) -> float:
    if not expected:
        return 1.0
    scores = []
    actual_tokens = tokenize(actual_text)
    for phrase in expected:
        expected_tokens = tokenize(phrase)
        scores.append(
            len(actual_tokens & expected_tokens) / len(expected_tokens) if expected_tokens else 1.0
        )
    return statistics.mean(scores)


def evaluate_scenario(scenario: dict[str, Any], result: WorkflowResult) -> dict[str, Any]:
    gold = scenario["gold_standard"]
    brief = result.brief
    citation_ids = {citation.source_id for citation in brief.citations}
    referenced_ids = {
        source_id
        for item in [
            *brief.contextual_analysis,
            *brief.risk_assessment,
            *brief.recommended_actions,
        ]
        for source_id in item.source_ids
    }
    required = set(gold["required_source_ids"])
    required_ehr = {item for item in required if item.startswith("ehr:")}
    required_anam = {item for item in required if item.startswith("anam:")}
    actual_ehr = (
        {citation.source_id for citation in result.ehr_context.citations}
        if result.ehr_context
        else set()
    )
    actual_anam = (
        {citation.source_id for citation in result.anamnesis_summary.citations}
        if result.anamnesis_summary
        else set()
    )

    urgency_correct = brief.urgency.value == scenario["expected_urgency"]
    required_source_recall = len(required & citation_ids) / len(required) if required else 1.0
    ehr_recall = len(required_ehr & actual_ehr) / len(required_ehr) if required_ehr else 1.0
    anamnesis_recall = (
        len(required_anam & actual_anam) / len(required_anam) if required_anam else 1.0
    )
    traceability = (
        len(referenced_ids & citation_ids) / len(referenced_ids) if referenced_ids else 1.0
    )
    unsupported_claim_rate = (
        len(referenced_ids - citation_ids) / len(referenced_ids) if referenced_ids else 0.0
    )
    concern_coverage = _keyword_coverage(gold["key_concerns"], _brief_text(result))
    safety_compliant = (
        brief.human_review_required
        and "not a diagnosis" in brief.disclaimer.lower()
        and not result.warnings
        and (not brief.immediate_escalation or brief.urgency.value == "Critical")
    )
    scenario_pass = (
        urgency_correct
        and required_source_recall >= 0.5
        and traceability == 1.0
        and safety_compliant
        and concern_coverage >= 0.35
    )
    return {
        "scenario_id": scenario["scenario_id"],
        "title": scenario["title"],
        "urgency_correct": urgency_correct,
        "required_source_recall": round(required_source_recall, 4),
        "ehr_retrieval_recall": round(ehr_recall, 4),
        "anamnesis_source_recall": round(anamnesis_recall, 4),
        "source_traceability": round(traceability, 4),
        "unsupported_claim_rate": round(unsupported_claim_rate, 4),
        "key_concern_coverage": round(concern_coverage, 4),
        "safety_compliant": safety_compliant,
        "elapsed_seconds": round(result.elapsed_seconds, 4),
        "passed": scenario_pass,
        "warnings": result.warnings,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mean = lambda key: statistics.mean(row[key] for row in rows)  # noqa: E731
    return {
        "scenario_count": len(rows),
        "scenario_pass_rate": round(mean("passed"), 4),
        "triage_accuracy": round(mean("urgency_correct"), 4),
        "ehr_retrieval_recall": round(mean("ehr_retrieval_recall"), 4),
        "anamnesis_source_recall": round(mean("anamnesis_source_recall"), 4),
        "source_traceability": round(mean("source_traceability"), 4),
        "hallucination_proxy_rate": round(mean("unsupported_claim_rate"), 4),
        "key_concern_coverage": round(mean("key_concern_coverage"), 4),
        "safety_compliance": round(mean("safety_compliant"), 4),
        "mean_latency_seconds": round(mean("elapsed_seconds"), 4),
        "max_latency_seconds": round(max(row["elapsed_seconds"] for row in rows), 4),
    }


def report_markdown(payload: dict[str, Any]) -> str:
    metrics = payload["aggregate"]
    if payload["mode"] == "live":
        interpretation = (
            "This run evaluates the live OpenAI pathway using the configured model, "
            "OpenAI embeddings, and the selected prompt version. Results are based on "
            "one execution per scenario and may vary across repeated runs."
        )
    else:
        interpretation = (
            "This run evaluates the deterministic offline pathway so the result is "
            "reproducible without sending any data to an external API. It validates "
            "orchestration, safety routing, source traceability, retrieval coverage, "
            "and output contracts."
        )
    lines = [
        "# ClinicalBridge Evaluation Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"Evaluation mode: **{payload['mode']}**",
        "",
        "## Aggregate results",
        "",
        "| Metric | Result | Capstone target |",
        "|---|---:|---:|",
        f"| Scenario pass rate | {metrics['scenario_pass_rate']:.0%} | Reported, no fixed target |",
        f"| Triage accuracy | {metrics['triage_accuracy']:.0%} | >=90% |",
        f"| EHR retrieval recall | {metrics['ehr_retrieval_recall']:.0%} | >=75% |",
        f"| Anamnesis source recall | {metrics['anamnesis_source_recall']:.0%} | >=85% completeness proxy |",
        f"| Source traceability | {metrics['source_traceability']:.0%} | 100% desired |",
        f"| Unsupported-claim proxy | {metrics['hallucination_proxy_rate']:.0%} | <=5% |",
        f"| Safety compliance | {metrics['safety_compliance']:.0%} | 100% desired |",
        f"| Mean latency | {metrics['mean_latency_seconds']:.3f}s | <30s |",
        "",
        "## Scenario results",
        "",
        "| Scenario | Urgency | Sources | Concern coverage | Safety | Pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["scenarios"]:
        lines.append(
            f"| {row['scenario_id']} - {row['title']} | "
            f"{'Yes' if row['urgency_correct'] else 'No'} | "
            f"{row['required_source_recall']:.0%} | "
            f"{row['key_concern_coverage']:.0%} | "
            f"{'Yes' if row['safety_compliant'] else 'No'} | "
            f"{'Pass' if row['passed'] else 'Review'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            interpretation,
            "",
            "The unsupported-claim rate is a structural proxy: it checks whether every finding, risk, "
            "and recommendation refers only to source IDs present in the brief. It does not replace "
            "expert clinical review or factual entailment grading.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--prompt-version", default="v3")
    args = parser.parse_args()

    base_settings = Settings()
    settings = Settings(
        project_root=base_settings.project_root,
        openai_api_key=base_settings.openai_api_key,
        model=base_settings.model,
        embedding_model=base_settings.embedding_model,
        mode=args.mode,
        rag_backend=base_settings.rag_backend,
        reasoning_effort=base_settings.reasoning_effort,
        retrieval_k=base_settings.retrieval_k,
        max_retries=base_settings.max_retries,
    )
    repository = DataRepository(settings)
    system = ClinicalBridge(
        settings=settings,
        repository=repository,
        prompt_version=args.prompt_version,
    )
    rows = []
    run_dir = ROOT / "evaluation" / "results" / "runs" / f"{args.mode}_{args.prompt_version}"
    run_dir.mkdir(parents=True, exist_ok=True)
    for scenario in repository.scenarios:
        result = system.run_scenario(scenario["scenario_id"])
        write_json(
            run_dir / f"{scenario['scenario_id']}.json",
            result.model_dump(mode="json"),
        )
        rows.append(evaluate_scenario(scenario, result))
        print(f"{scenario['scenario_id']}: {'PASS' if rows[-1]['passed'] else 'REVIEW'}")

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": args.mode,
        "prompt_version": args.prompt_version,
        "aggregate": aggregate(rows),
        "scenarios": rows,
    }
    result_path = (
        ROOT / "evaluation" / "results" / f"{args.mode}_{args.prompt_version}_evaluation.json"
    )
    write_json(result_path, payload)
    report_path = (
        ROOT / "docs" / f"evaluation_report_generated_{args.mode}_{args.prompt_version}.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_markdown(payload), encoding="utf-8")
    print(f"Wrote {result_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
