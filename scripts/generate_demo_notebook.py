from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "clinicalbridge_demo.ipynb"


def main() -> None:
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11+"},
    }
    notebook["cells"] = [
        nbf.v4.new_markdown_cell(
            """# ClinicalBridge End-to-End Demonstration

**Team:** Erkan Işık Bacak (2200914), Raymond Lasses (2200274), Ata Uzun (2103247), Kutlay Başar Aklan (2202139)

This annotated notebook demonstrates the two most important orchestration paths:

1. a non-critical alert that triggers parallel EHR and anamnesis processing;
2. a critical alert that bypasses routine synthesis and immediately escalates.

> ClinicalBridge uses entirely simulated data. It is not a diagnostic or clinical decision-making tool."""
        ),
        nbf.v4.new_markdown_cell(
            """## 1. Load the reproducible offline system

The repository automatically uses OpenAI when a key is present. For a stable graded demonstration, this notebook explicitly selects offline mode. The same `ClinicalBridge` interface is used in both modes."""
        ),
        nbf.v4.new_code_cell(
            """import json
from pathlib import Path

from IPython.display import Markdown, display

from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.orchestrator import ClinicalBridge
from clinicalbridge.rendering import brief_to_markdown

base = Settings()
settings = Settings(
    project_root=base.project_root,
    openai_api_key="",
    model=base.model,
    embedding_model=base.embedding_model,
    mode="offline",
    rag_backend=base.rag_backend,
    reasoning_effort=base.reasoning_effort,
    retrieval_k=8,
    max_retries=base.max_retries,
)
repository = DataRepository(settings)
system = ClinicalBridge(settings=settings, repository=repository)
print(f"Patients: {repository.patient_count()} | Scenarios: {len(repository.scenarios)} | Mode: offline")"""
        ),
        nbf.v4.new_markdown_cell(
            """## 2. Inspect the scenario catalog

The eight scenarios deliberately test different failure modes rather than repeating the same threshold alert."""
        ),
        nbf.v4.new_code_cell(
            """for scenario in repository.list_scenarios():
    print(
        f"{scenario['scenario_id']}: {scenario['title']} "
        f"({scenario['patient_id']}, expected {scenario['expected_urgency']})"
    )"""
        ),
        nbf.v4.new_markdown_cell(
            """## 3. Scenario 03 - Silent deterioration

This scenario tests trend reasoning. No single weight value tells the whole story. The brief must combine a two-week increase with EHR dry weight, heart-failure history, ankle swelling, and mildly worse breathlessness."""
        ),
        nbf.v4.new_code_cell(
            """scenario_03 = repository.get_scenario("scenario_03")
alert_03 = repository.scenario_alert("scenario_03")
display(Markdown(f"**Scenario:** {scenario_03['description']}"))
print(alert_03.model_dump_json(indent=2))"""
        ),
        nbf.v4.new_code_cell(
            """result_03 = system.run_scenario("scenario_03")
display(Markdown(brief_to_markdown(result_03.brief)))"""
        ),
        nbf.v4.new_markdown_cell(
            """### Inspect the specialized agent outputs

For a non-critical alert, both context agents are present. Their source IDs flow into the final brief."""
        ),
        nbf.v4.new_code_cell(
            """print("Triage:", result_03.triage.urgency)
print("EHR sources:", len(result_03.ehr_context.citations))
print("Anamnesis sources:", len(result_03.anamnesis_summary.citations))
print("Warnings:", result_03.warnings)
print("Session:", result_03.session_id)"""
        ),
        nbf.v4.new_markdown_cell(
            """## 4. Scenario 06 - Critical hypoxemia

This scenario demonstrates the safety exception. Repeated SpO2 of 84% crosses the supplied critical threshold. The orchestrator must not wait for EHR or anamnesis retrieval."""
        ),
        nbf.v4.new_code_cell(
            """result_06 = system.run_scenario("scenario_06")
display(Markdown(brief_to_markdown(result_06.brief)))
print("EHR agent output:", result_06.ehr_context)
print("Anamnesis agent output:", result_06.anamnesis_summary)
assert result_06.brief.immediate_escalation
assert result_06.ehr_context is None
assert result_06.anamnesis_summary is None"""
        ),
        nbf.v4.new_markdown_cell(
            """## 5. Review the reproducible evaluation

The automated evaluation checks urgency, retrieval recall, source traceability, safety, latency, key-concern coverage, and a structural unsupported-claim proxy."""
        ),
        nbf.v4.new_code_cell(
            """evaluation_path = Path("../evaluation/results/offline_v4_evaluation.json")
if not evaluation_path.exists():
    evaluation_path = Path("evaluation/results/offline_v4_evaluation.json")
evaluation = json.loads(evaluation_path.read_text())
evaluation["aggregate"]"""
        ),
        nbf.v4.new_markdown_cell(
            """## 6. Review the completed OpenAI prompt comparison

The same eight scenarios were run live with four prompt iterations. v4 assigns the urgency enum to the deterministic triage tool while retaining the LLM for explanation and retrieval-query generation."""
        ),
        nbf.v4.new_code_cell(
            """live_results = {}
for version in ("v1", "v2", "v3", "v4"):
    path = Path(f"../evaluation/results/live_{version}_evaluation.json")
    if not path.exists():
        path = Path(f"evaluation/results/live_{version}_evaluation.json")
    live_results[version] = json.loads(path.read_text())["aggregate"]

{
    version: {
        "scenario_pass_rate": metrics["scenario_pass_rate"],
        "triage_accuracy": metrics["triage_accuracy"],
        "mean_latency_seconds": metrics["mean_latency_seconds"],
        "source_traceability": metrics["source_traceability"],
        "safety_compliance": metrics["safety_compliance"],
    }
    for version, metrics in live_results.items()
}"""
        ),
        nbf.v4.new_markdown_cell(
            """## 7. Rerun the OpenAI path

Add `OPENAI_API_KEY` to `.env`, leave `CLINICALBRIDGE_MODE=auto`, restart the kernel, and construct `ClinicalBridge()` without overriding settings. The live path uses `gpt-5.4-mini`, OpenAI structured outputs, `text-embedding-3-small`, and persistent Chroma.

Rerun the final live evaluator with:

```bash
python evaluation/evaluate.py --mode live --prompt-version v4
```

The command makes API calls and may incur cost."""
        ),
        nbf.v4.new_markdown_cell(
            """## Conclusion

The demonstration shows that ClinicalBridge can coordinate specialized agents, preserve evidence provenance, fail safely on a critical alert, and produce a brief that leaves the final judgment with a clinician. The evaluation does not establish clinical validity; it establishes that the educational prototype behaves according to its implemented contracts on its fictional scenarios."""
        ),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, OUT)
    print(OUT)


if __name__ == "__main__":
    main()
