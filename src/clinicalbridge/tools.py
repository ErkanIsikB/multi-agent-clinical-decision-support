from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from clinicalbridge.schemas import RPMAlert, Urgency


def classify_alert_rules(alert: RPMAlert) -> tuple[Urgency, list[str]]:
    """Deterministic safety net used for validation and offline demonstrations."""

    m = alert.measurements
    factors: list[str] = []

    systolic = m.get("systolic_bp")
    diastolic = m.get("diastolic_bp")
    spo2 = m.get("spo2")
    glucose = m.get("glucose")
    heart_rate = m.get("heart_rate")

    if spo2 is not None and spo2 < 88:
        factors.append(f"SpO2 {spo2:g}% is below the critical safety threshold of 88%.")
    if systolic is not None and systolic >= 180:
        factors.append(f"Systolic blood pressure {systolic:g} mmHg is critically elevated.")
    if diastolic is not None and diastolic >= 120:
        factors.append(f"Diastolic blood pressure {diastolic:g} mmHg is critically elevated.")
    if glucose is not None and (glucose < 54 or glucose > 400):
        factors.append(f"Glucose {glucose:g} mg/dL crosses a critical safety threshold.")
    if heart_rate is not None and (heart_rate < 40 or heart_rate > 160):
        factors.append(f"Heart rate {heart_rate:g} bpm crosses a critical safety threshold.")
    if factors:
        return Urgency.CRITICAL, factors

    if systolic is not None and systolic >= 160:
        factors.append(f"Systolic blood pressure {systolic:g} mmHg is above the urgent threshold.")
    if diastolic is not None and diastolic >= 100:
        factors.append(
            f"Diastolic blood pressure {diastolic:g} mmHg is above the urgent threshold."
        )
    if glucose is not None and (glucose < 70 or glucose > 250):
        factors.append(f"Glucose {glucose:g} mg/dL warrants prompt contextual review.")
    if heart_rate is not None and (heart_rate < 50 or heart_rate > 130):
        factors.append(f"Heart rate {heart_rate:g} bpm warrants prompt contextual review.")
    if alert.alert_category in {"weight_gain_trend", "medication_discrepancy"}:
        factors.append(
            f"Alert category '{alert.alert_category}' can indicate gradual deterioration."
        )
    if factors:
        return Urgency.URGENT, factors

    if alert.alert_category in {
        "threshold_breach",
        "high_glucose",
        "device_artifact",
        "nocturnal_hypertension",
    }:
        return Urgency.ROUTINE, [
            "Threshold breach requires context but no critical feature is present."
        ]
    return Urgency.INFORMATIONAL, ["No acute or urgent rule-based threshold was crossed."]


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from", "this"}
    }


def flatten_record(record: dict[str, Any]) -> Iterable[tuple[str, str, dict[str, Any]]]:
    """Yield source-id, searchable text, and metadata chunks from an EHR record."""

    patient_id = record["patient_id"]
    demographics = record["demographics"]
    yield (
        f"ehr:{patient_id}:demographics",
        " ".join(f"{key}: {value}" for key, value in demographics.items()),
        {"patient_id": patient_id, "section": "demographics", "payload": demographics},
    )
    for section in ("problems", "medications", "labs", "visit_notes", "allergies"):
        for item in record.get(section, []):
            source_id = item["source_id"]
            text = " ".join(f"{key}: {value}" for key, value in item.items())
            yield (
                source_id,
                text,
                {"patient_id": patient_id, "section": section, "payload": item},
            )
