from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.orchestrator import ClinicalBridge
from clinicalbridge.rendering import brief_to_markdown, result_summary
from clinicalbridge.schemas import RPMAlert

app = typer.Typer(help="ClinicalBridge: simulated multi-agent clinical context synthesis.")
console = Console()


@app.command("scenarios")
def list_scenarios() -> None:
    """List the eight included clinical scenarios."""

    repository = DataRepository()
    table = Table("Scenario", "Title", "Patient", "Expected urgency")
    for item in repository.list_scenarios():
        table.add_row(
            item["scenario_id"],
            item["title"],
            item["patient_id"],
            item["expected_urgency"],
        )
    console.print(table)


@app.command("run")
def run_scenario(
    scenario: Annotated[str, typer.Option("--scenario", "-s")] = "scenario_01",
    output_json: Annotated[bool, typer.Option("--json")] = False,
    save: Annotated[Path | None, typer.Option("--save")] = None,
) -> None:
    """Run one packaged scenario through the full workflow."""

    result = ClinicalBridge().run_scenario(scenario)
    rendered = (
        json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)
        if output_json
        else brief_to_markdown(result.brief)
    )
    if save:
        save.parent.mkdir(parents=True, exist_ok=True)
        save.write_text(rendered + "\n", encoding="utf-8")
        console.print(f"Saved to {save}")
    console.print(result_summary(result))
    console.print(Markdown(rendered) if not output_json else rendered)
    if result.warnings:
        console.print(f"[yellow]Quality warnings:[/yellow] {result.warnings}")


@app.command("run-alert")
def run_alert(
    alert_file: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run a custom simulated RPM alert JSON file."""

    alert = RPMAlert.model_validate_json(alert_file.read_text(encoding="utf-8"))
    result = ClinicalBridge().run_alert(alert)
    if output_json:
        console.print_json(data=result.model_dump(mode="json"))
    else:
        console.print(Markdown(brief_to_markdown(result.brief)))


@app.command("doctor")
def doctor() -> None:
    """Check configuration and dataset readiness without making an API call."""

    settings = Settings()
    repository = DataRepository(settings)
    repository.validate_simulated_only()
    console.print("[green]Dataset manifest passed simulated-data validation.[/green]")
    console.print(f"Patients: {repository.patient_count()}")
    console.print(f"Scenarios: {len(repository.scenarios)}")
    console.print(f"Configured model: {settings.model}")
    console.print(f"Runtime mode: {'live' if settings.use_llm else 'offline'}")
    console.print(
        "API key: "
        + (
            "present (not displayed)"
            if settings.openai_api_key
            else "not set; offline fallback active"
        )
    )


if __name__ == "__main__":
    app()
