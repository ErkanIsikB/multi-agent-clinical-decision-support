from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any

import pandas as pd

from clinicalbridge.config import Settings
from clinicalbridge.schemas import RPMAlert


class DataRepository:
    """Read-only access to the fully simulated capstone dataset."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.base = self.settings.data_dir

    def _load_json(self, name: str) -> Any:
        path = self.base / name
        if not path.exists():
            raise FileNotFoundError(
                f"Missing simulated dataset file: {path}. Run scripts/generate_dataset.py."
            )
        return json.loads(path.read_text(encoding="utf-8"))

    @cached_property
    def ehr_records(self) -> list[dict[str, Any]]:
        return self._load_json("ehr_records.json")

    @cached_property
    def anamnesis_records(self) -> list[dict[str, Any]]:
        return self._load_json("anamnesis_records.json")

    @cached_property
    def alerts(self) -> list[dict[str, Any]]:
        return self._load_json("alerts.json")

    @cached_property
    def scenarios(self) -> list[dict[str, Any]]:
        return self._load_json("scenarios.json")

    @cached_property
    def rpm_readings(self) -> pd.DataFrame:
        return pd.read_csv(self.base / "rpm_readings.csv")

    def get_ehr(self, patient_id: str) -> dict[str, Any]:
        return next(record for record in self.ehr_records if record["patient_id"] == patient_id)

    def get_anamnesis(self, patient_id: str) -> dict[str, Any]:
        return next(
            record for record in self.anamnesis_records if record["patient_id"] == patient_id
        )

    def get_alert(self, alert_id: str) -> RPMAlert:
        raw = next(alert for alert in self.alerts if alert["alert_id"] == alert_id)
        return RPMAlert.model_validate(raw)

    def get_scenario(self, scenario_id: str) -> dict[str, Any]:
        return next(
            scenario for scenario in self.scenarios if scenario["scenario_id"] == scenario_id
        )

    def scenario_alert(self, scenario_id: str) -> RPMAlert:
        return self.get_alert(self.get_scenario(scenario_id)["alert_id"])

    def list_scenarios(self) -> list[dict[str, Any]]:
        return [
            {
                "scenario_id": item["scenario_id"],
                "title": item["title"],
                "patient_id": item["patient_id"],
                "expected_urgency": item["expected_urgency"],
            }
            for item in self.scenarios
        ]

    def patient_count(self) -> int:
        return len(self.ehr_records)

    def validate_simulated_only(self) -> None:
        marker = self._load_json("dataset_manifest.json")
        if marker.get("contains_real_patient_data") is not False:
            raise ValueError(
                "Dataset manifest must explicitly state that no real patient data is used."
            )


def write_json(path: Path, payload: Any) -> None:
    """Utility used by project scripts, kept here for consistent UTF-8 output."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
