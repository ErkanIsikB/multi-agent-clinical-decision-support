"""Generate the entirely fictional ClinicalBridge capstone dataset."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "simulated"


def write_json(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def source(patient_id: str, kind: str, number: int) -> str:
    return f"ehr:{patient_id}:{kind}:{number}"


def anam_source(patient_id: str, kind: str, number: int) -> str:
    return f"anam:{patient_id}:{kind}:{number}"


def problem(patient_id: str, number: int, name: str, code: str) -> dict[str, Any]:
    return {
        "source_id": source(patient_id, "problem", number),
        "name": name,
        "icd10": code,
        "status": "active",
    }


def medication(
    patient_id: str,
    number: int,
    name: str,
    dose: str,
    started: str,
    status: str = "active",
) -> dict[str, Any]:
    return {
        "source_id": source(patient_id, "med", number),
        "name": name,
        "dose": dose,
        "started": started,
        "status": status,
    }


def lab(
    patient_id: str,
    number: int,
    test: str,
    value: float,
    unit: str,
    date: str,
    reference_range: str,
    flag: str = "normal",
) -> dict[str, Any]:
    return {
        "source_id": source(patient_id, "lab", number),
        "test": test,
        "value": value,
        "unit": unit,
        "date": date,
        "reference_range": reference_range,
        "flag": flag,
    }


def note(patient_id: str, number: int, title: str, date: str, text: str) -> dict[str, Any]:
    return {
        "source_id": source(patient_id, "note", number),
        "title": title,
        "date": date,
        "text": text,
    }


def allergy(patient_id: str, number: int, substance: str, reaction: str) -> dict[str, Any]:
    return {
        "source_id": source(patient_id, "allergy", number),
        "substance": substance,
        "reaction": reaction,
        "status": "active",
    }


def anam_item(
    patient_id: str, kind: str, number: int, text: str, date: str = "2026-05-12"
) -> dict[str, Any]:
    return {
        "source_id": anam_source(patient_id, kind, number),
        "label": kind.replace("_", " "),
        "date": date,
        "text": text,
    }


def demographics(name: str, age: int, sex: str, language: str = "English") -> dict[str, Any]:
    return {
        "name": name,
        "age": age,
        "sex": sex,
        "preferred_language": language,
        "fictional_patient": True,
    }


def build_ehr_records() -> list[dict[str, Any]]:
    return [
        {
            "patient_id": "P001",
            "demographics": demographics("Maria Demir", 61, "female"),
            "problems": [
                problem("P001", 1, "Essential hypertension", "I10"),
                problem("P001", 2, "Hyperlipidemia", "E78.5"),
            ],
            "medications": [
                medication("P001", 1, "Lisinopril", "20 mg once daily", "2025-11-02"),
                medication("P001", 2, "Atorvastatin", "20 mg nightly", "2025-07-18"),
            ],
            "labs": [
                lab("P001", 1, "Creatinine", 0.9, "mg/dL", "2026-03-14", "0.6-1.2"),
                lab("P001", 2, "Potassium", 4.3, "mmol/L", "2026-03-14", "3.5-5.1"),
            ],
            "visit_notes": [
                note(
                    "P001",
                    1,
                    "Hypertension follow-up",
                    "2026-03-14",
                    "Clinic blood pressure 132/82. Lisinopril continued. No side effects documented.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [
                "The EHR lists lisinopril as active, while the patient reports stopping it."
            ],
        },
        {
            "patient_id": "P002",
            "demographics": demographics("James Kaya", 54, "male"),
            "problems": [
                problem("P002", 1, "Type 2 diabetes mellitus", "E11.9"),
                problem("P002", 2, "Obesity", "E66.9"),
            ],
            "medications": [
                medication("P002", 1, "Metformin XR", "1000 mg twice daily", "2024-09-11"),
                medication("P002", 2, "Semaglutide", "0.5 mg weekly", "2026-05-05"),
            ],
            "labs": [
                lab("P002", 1, "HbA1c", 7.8, "%", "2026-04-28", "4.0-5.6", "high"),
                lab("P002", 2, "Fasting glucose", 151, "mg/dL", "2026-04-28", "70-99", "high"),
            ],
            "visit_notes": [
                note(
                    "P002",
                    1,
                    "Diabetes medication adjustment",
                    "2026-05-05",
                    "Semaglutide initiated. Short-term glucose variability discussed during titration.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P003",
            "demographics": demographics("Aylin Foster", 69, "female"),
            "problems": [
                problem("P003", 1, "Heart failure with reduced ejection fraction", "I50.2"),
                problem("P003", 2, "Essential hypertension", "I10"),
            ],
            "medications": [
                medication("P003", 1, "Furosemide", "40 mg each morning", "2025-10-21"),
                medication("P003", 2, "Carvedilol", "12.5 mg twice daily", "2025-10-21"),
            ],
            "labs": [
                lab("P003", 1, "BNP", 280, "pg/mL", "2026-04-20", "<100", "high"),
                lab("P003", 2, "Creatinine", 1.1, "mg/dL", "2026-04-20", "0.6-1.2"),
            ],
            "visit_notes": [
                note(
                    "P003",
                    1,
                    "Heart failure monitoring plan",
                    "2026-04-20",
                    "Dry weight approximately 72.0 kg. Call care team for rapid weight gain, edema, or dyspnea.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P004",
            "demographics": demographics("Omar Reed", 58, "male"),
            "problems": [problem("P004", 1, "Essential hypertension", "I10")],
            "medications": [],
            "labs": [],
            "visit_notes": [
                note(
                    "P004",
                    1,
                    "Transfer intake",
                    "2026-05-02",
                    "Patient transferred from an external health system. Prior records requested but not received.",
                )
            ],
            "allergies": [],
            "known_gaps": [
                "External medication list is unavailable.",
                "No prior laboratory history is available.",
                "Problem list may be incomplete after transfer.",
            ],
            "contradictions": [],
        },
        {
            "patient_id": "P005",
            "demographics": demographics("Leyla Stone", 42, "female"),
            "problems": [problem("P005", 1, "Epilepsy", "G40.909")],
            "medications": [medication("P005", 1, "Valproate", "500 mg twice daily", "2023-06-12")],
            "labs": [
                lab(
                    "P005",
                    1,
                    "Valproate level",
                    34,
                    "mcg/mL",
                    "2026-05-10",
                    "50-100",
                    "sub-therapeutic",
                )
            ],
            "visit_notes": [
                note(
                    "P005",
                    1,
                    "Neurology follow-up",
                    "2026-02-19",
                    "No reported seizure activity. Continue current valproate dose and monitor levels.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [
                "Measured valproate level is sub-therapeutic despite reported full adherence."
            ],
        },
        {
            "patient_id": "P006",
            "demographics": demographics("Thomas Çelik", 67, "male"),
            "problems": [problem("P006", 1, "Chronic obstructive pulmonary disease", "J44.9")],
            "medications": [
                medication("P006", 1, "Tiotropium", "18 mcg inhaled daily", "2025-02-03"),
                medication("P006", 2, "Albuterol", "2 puffs as needed", "2025-02-03"),
            ],
            "labs": [],
            "visit_notes": [
                note(
                    "P006",
                    1,
                    "Pulmonary follow-up",
                    "2026-03-01",
                    "Usual home SpO2 reported as 93-95% on room air.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P007",
            "demographics": demographics("Zeynep Hart", 36, "female"),
            "problems": [problem("P007", 1, "Generalized anxiety disorder", "F41.1")],
            "medications": [medication("P007", 1, "Sertraline", "50 mg once daily", "2025-08-09")],
            "labs": [],
            "visit_notes": [
                note(
                    "P007",
                    1,
                    "Palpitations review",
                    "2026-01-17",
                    "Prior ECG showed sinus rhythm. Patient advised to document activity and device fit during alerts.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P008",
            "demographics": demographics("Daniel Arslan", 63, "male"),
            "problems": [
                problem("P008", 1, "Essential hypertension", "I10"),
                problem("P008", 2, "Knee osteoarthritis", "M17.9"),
            ],
            "medications": [medication("P008", 1, "Amlodipine", "10 mg once daily", "2024-04-22")],
            "labs": [lab("P008", 1, "Creatinine", 1.0, "mg/dL", "2026-03-29", "0.6-1.2")],
            "visit_notes": [
                note(
                    "P008",
                    1,
                    "Blood pressure review",
                    "2026-03-29",
                    "Daytime home readings generally 128-138/76-86 on amlodipine.",
                )
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P009",
            "demographics": demographics("Nora Wells", 47, "female"),
            "problems": [problem("P009", 1, "Asthma", "J45.909")],
            "medications": [
                medication("P009", 1, "Budesonide-formoterol", "2 puffs twice daily", "2025-06-01")
            ],
            "labs": [],
            "visit_notes": [
                note("P009", 1, "Asthma review", "2026-03-12", "Symptoms well controlled.")
            ],
            "allergies": [allergy("P009", 1, "Penicillin", "rash")],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P010",
            "demographics": demographics("Kemal Price", 72, "male"),
            "problems": [problem("P010", 1, "Atrial fibrillation", "I48.91")],
            "medications": [
                medication("P010", 1, "Apixaban", "5 mg twice daily", "2024-12-10"),
                medication("P010", 2, "Metoprolol", "50 mg once daily", "2024-12-10"),
            ],
            "labs": [],
            "visit_notes": [
                note("P010", 1, "Cardiology follow-up", "2026-02-25", "Rate controlled.")
            ],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P011",
            "demographics": demographics("Selin Moore", 51, "female"),
            "problems": [problem("P011", 1, "Hypothyroidism", "E03.9")],
            "medications": [
                medication("P011", 1, "Levothyroxine", "75 mcg once daily", "2022-10-04")
            ],
            "labs": [lab("P011", 1, "TSH", 2.1, "mIU/L", "2026-03-03", "0.4-4.0")],
            "visit_notes": [],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
        {
            "patient_id": "P012",
            "demographics": demographics("Victor Aksoy", 59, "male"),
            "problems": [problem("P012", 1, "Chronic kidney disease stage 3a", "N18.31")],
            "medications": [medication("P012", 1, "Losartan", "50 mg once daily", "2025-05-13")],
            "labs": [lab("P012", 1, "eGFR", 52, "mL/min/1.73m2", "2026-04-01", ">60", "low")],
            "visit_notes": [],
            "allergies": [],
            "known_gaps": [],
            "contradictions": [],
        },
    ]


def build_anamnesis_records() -> list[dict[str, Any]]:
    specifics = {
        "P001": {
            "symptoms": [
                anam_item(
                    "P001",
                    "symptoms",
                    1,
                    "Persistent dry cough began about three weeks ago; no chest pain or shortness of breath.",
                )
            ],
            "medication_adherence": [
                anam_item(
                    "P001",
                    "adherence",
                    1,
                    "Patient stopped lisinopril five days ago because the cough was disruptive.",
                )
            ],
            "lifestyle": [
                anam_item("P001", "lifestyle", 1, "No major dietary or activity change reported.")
            ],
            "patient_concerns": [
                anam_item(
                    "P001",
                    "concern",
                    1,
                    "Asks whether another blood pressure medicine is possible.",
                )
            ],
        },
        "P002": {
            "symptoms": [
                anam_item(
                    "P002",
                    "symptoms",
                    1,
                    "Feels well and reports no polyuria, vomiting, or confusion.",
                )
            ],
            "medication_adherence": [
                anam_item(
                    "P002",
                    "adherence",
                    1,
                    "Reports taking metformin and the new weekly injection as directed.",
                )
            ],
            "lifestyle": [
                anam_item(
                    "P002",
                    "lifestyle",
                    1,
                    "Planned dietary change for a family celebration included a carbohydrate-heavy meal before the reading.",
                )
            ],
            "patient_concerns": [
                anam_item(
                    "P002", "concern", 1, "Wants to know whether one high reading is dangerous."
                )
            ],
        },
        "P003": {
            "symptoms": [
                anam_item(
                    "P003",
                    "symptoms",
                    1,
                    "Ankle swelling has gradually increased over six days.",
                ),
                anam_item(
                    "P003",
                    "symptoms",
                    2,
                    "Mild breathlessness when climbing stairs is slightly worse than usual.",
                ),
            ],
            "medication_adherence": [
                anam_item("P003", "adherence", 1, "Reports taking furosemide every morning.")
            ],
            "lifestyle": [
                anam_item("P003", "lifestyle", 1, "Ate several salty prepared meals this week.")
            ],
            "patient_concerns": [
                anam_item("P003", "concern", 1, "Concerned that shoes feel tighter by evening.")
            ],
        },
        "P004": {
            "symptoms": [
                anam_item(
                    "P004", "symptoms", 1, "Intermittent morning headaches over the past week."
                )
            ],
            "medication_adherence": [
                anam_item(
                    "P004",
                    "adherence",
                    1,
                    "Reports taking a small white blood pressure tablet but cannot recall its name or dose.",
                )
            ],
            "lifestyle": [
                anam_item(
                    "P004",
                    "lifestyle",
                    1,
                    "Recently moved and has not established local primary care.",
                )
            ],
            "patient_concerns": [
                anam_item("P004", "concern", 1, "Worries that transfer records have not arrived.")
            ],
            "missing_data": ["Home medication name and dose remain unverified."],
        },
        "P005": {
            "symptoms": [
                anam_item(
                    "P005",
                    "symptoms",
                    1,
                    "No seizure symptoms or new neurologic complaints reported.",
                )
            ],
            "medication_adherence": [
                anam_item(
                    "P005",
                    "adherence",
                    1,
                    "Reports taking every valproate dose and denies intentional or accidental missed doses.",
                )
            ],
            "lifestyle": [
                anam_item(
                    "P005", "lifestyle", 1, "No new supplements or major diet changes reported."
                )
            ],
            "patient_concerns": [
                anam_item("P005", "concern", 1, "Surprised that the medication level was low.")
            ],
        },
        "P006": {
            "symptoms": [
                anam_item(
                    "P006", "symptoms", 1, "Reports new shortness of breath at rest this morning."
                )
            ],
            "medication_adherence": [
                anam_item("P006", "adherence", 1, "Used rescue inhaler twice with limited relief.")
            ],
            "lifestyle": [],
            "patient_concerns": [
                anam_item(
                    "P006", "concern", 1, "Says breathing feels substantially worse than baseline."
                )
            ],
        },
        "P007": {
            "symptoms": [
                anam_item(
                    "P007",
                    "symptoms",
                    1,
                    "Felt briefly winded after climbing stairs but denies chest pain, fainting, or persistent palpitations.",
                )
            ],
            "medication_adherence": [
                anam_item("P007", "adherence", 1, "Reports taking sertraline consistently.")
            ],
            "lifestyle": [
                anam_item(
                    "P007",
                    "lifestyle",
                    1,
                    "The alert occurred during vigorous activity; the watch strap was loose and showed poor skin contact.",
                )
            ],
            "patient_concerns": [
                anam_item(
                    "P007", "concern", 1, "Asks whether the watch reading could be inaccurate."
                )
            ],
        },
        "P008": {
            "symptoms": [
                anam_item("P008", "symptoms", 1, "Knee pain has disrupted sleep for four nights.")
            ],
            "medication_adherence": [
                anam_item("P008", "adherence", 1, "Reports taking amlodipine every morning.")
            ],
            "lifestyle": [
                anam_item(
                    "P008",
                    "lifestyle",
                    1,
                    "Started over-the-counter ibuprofen 600 mg three times daily five days ago for knee pain.",
                )
            ],
            "patient_concerns": [
                anam_item("P008", "concern", 1, "Noticed blood pressure is mainly high overnight.")
            ],
        },
    }
    records = []
    for index in range(1, 13):
        patient_id = f"P{index:03d}"
        entry = specifics.get(
            patient_id,
            {
                "symptoms": [anam_item(patient_id, "symptoms", 1, "No new symptoms reported.")],
                "medication_adherence": [
                    anam_item(patient_id, "adherence", 1, "Reports taking medication as directed.")
                ],
                "lifestyle": [
                    anam_item(patient_id, "lifestyle", 1, "No recent lifestyle change reported.")
                ],
                "patient_concerns": [],
            },
        )
        records.append(
            {
                "patient_id": patient_id,
                "intake_date": "2026-05-12",
                "symptoms": entry.get("symptoms", []),
                "medication_adherence": entry.get("medication_adherence", []),
                "lifestyle": entry.get("lifestyle", []),
                "family_history": entry.get("family_history", []),
                "patient_concerns": entry.get("patient_concerns", []),
                "sensitive_disclosures": entry.get("sensitive_disclosures", []),
                "missing_data": entry.get("missing_data", []),
            }
        )
    return records


def build_alerts() -> list[dict[str, Any]]:
    return [
        {
            "alert_id": "A001",
            "patient_id": "P001",
            "timestamp": "2026-05-13T08:10:00Z",
            "device_type": "Bluetooth blood pressure cuff",
            "alert_category": "blood_pressure",
            "measurements": {"systolic_bp": 172, "diastolic_bp": 106, "heart_rate": 82},
            "units": {"systolic_bp": "mmHg", "diastolic_bp": "mmHg", "heart_rate": "bpm"},
            "baseline": {"systolic_bp": 134, "diastolic_bp": 82},
            "thresholds": {"systolic_bp_high": 160, "diastolic_bp_high": 100},
            "trend": [],
            "device_metadata": {"validated_cuff": True, "repeat_reading": "170/104"},
            "source_id": "rpm:P001:alert:A001",
        },
        {
            "alert_id": "A002",
            "patient_id": "P002",
            "timestamp": "2026-05-13T19:30:00Z",
            "device_type": "Continuous glucose monitor",
            "alert_category": "high_glucose",
            "measurements": {"glucose": 238},
            "units": {"glucose": "mg/dL"},
            "baseline": {"glucose": 142},
            "thresholds": {"glucose_high": 220},
            "trend": [{"minutes": -60, "glucose": 176}, {"minutes": -30, "glucose": 214}],
            "device_metadata": {"sensor_age_days": 5, "signal_quality": "good"},
            "source_id": "rpm:P002:alert:A002",
        },
        {
            "alert_id": "A003",
            "patient_id": "P003",
            "timestamp": "2026-05-13T07:05:00Z",
            "device_type": "Connected scale",
            "alert_category": "weight_gain_trend",
            "measurements": {"weight": 74.8},
            "units": {"weight": "kg"},
            "baseline": {"weight": 72.0},
            "thresholds": {"fourteen_day_gain": 2.0},
            "trend": [
                {"days_ago": 14, "weight": 72.1},
                {"days_ago": 7, "weight": 73.2},
                {"days_ago": 3, "weight": 74.1},
            ],
            "device_metadata": {"surface": "hard floor", "signal_quality": "good"},
            "source_id": "rpm:P003:alert:A003",
        },
        {
            "alert_id": "A004",
            "patient_id": "P004",
            "timestamp": "2026-05-13T09:40:00Z",
            "device_type": "Bluetooth blood pressure cuff",
            "alert_category": "blood_pressure",
            "measurements": {"systolic_bp": 166, "diastolic_bp": 101, "heart_rate": 78},
            "units": {"systolic_bp": "mmHg", "diastolic_bp": "mmHg", "heart_rate": "bpm"},
            "baseline": {},
            "thresholds": {"systolic_bp_high": 160, "diastolic_bp_high": 100},
            "trend": [],
            "device_metadata": {"validated_cuff": True},
            "source_id": "rpm:P004:alert:A004",
        },
        {
            "alert_id": "A005",
            "patient_id": "P005",
            "timestamp": "2026-05-13T10:15:00Z",
            "device_type": "Medication monitoring portal",
            "alert_category": "medication_discrepancy",
            "measurements": {"valproate_level": 34},
            "units": {"valproate_level": "mcg/mL"},
            "baseline": {"valproate_level": 68},
            "thresholds": {"valproate_level_low": 50},
            "trend": [],
            "device_metadata": {"laboratory_verified": True},
            "source_id": "rpm:P005:alert:A005",
        },
        {
            "alert_id": "A006",
            "patient_id": "P006",
            "timestamp": "2026-05-13T06:50:00Z",
            "device_type": "Pulse oximeter",
            "alert_category": "hypoxemia",
            "measurements": {"spo2": 84, "heart_rate": 118},
            "units": {"spo2": "%", "heart_rate": "bpm"},
            "baseline": {"spo2": 94},
            "thresholds": {"spo2_critical": 88},
            "trend": [{"minutes": -10, "spo2": 86}, {"minutes": -5, "spo2": 85}],
            "device_metadata": {"signal_quality": "good", "repeat_reading": 84},
            "source_id": "rpm:P006:alert:A006",
        },
        {
            "alert_id": "A007",
            "patient_id": "P007",
            "timestamp": "2026-05-13T17:20:00Z",
            "device_type": "Smartwatch",
            "alert_category": "device_artifact",
            "measurements": {"heart_rate": 148},
            "units": {"heart_rate": "bpm"},
            "baseline": {"heart_rate": 72},
            "thresholds": {"heart_rate_high": 130},
            "trend": [{"minutes": 5, "heart_rate": 94}, {"minutes": 10, "heart_rate": 78}],
            "device_metadata": {"motion": "high", "skin_contact": "poor"},
            "source_id": "rpm:P007:alert:A007",
        },
        {
            "alert_id": "A008",
            "patient_id": "P008",
            "timestamp": "2026-05-13T02:15:00Z",
            "device_type": "Ambulatory blood pressure monitor",
            "alert_category": "nocturnal_hypertension",
            "measurements": {"systolic_bp": 164, "diastolic_bp": 98, "heart_rate": 76},
            "units": {"systolic_bp": "mmHg", "diastolic_bp": "mmHg", "heart_rate": "bpm"},
            "baseline": {"systolic_bp": 134, "diastolic_bp": 81},
            "thresholds": {"night_systolic_high": 150},
            "trend": [
                {"hours_ago": 24, "systolic_bp": 158},
                {"hours_ago": 48, "systolic_bp": 160},
            ],
            "device_metadata": {"signal_quality": "good"},
            "source_id": "rpm:P008:alert:A008",
        },
    ]


def build_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "scenario_01",
            "title": "The Missed Medication",
            "patient_id": "P001",
            "alert_id": "A001",
            "description": "Blood pressure rises after the patient stops lisinopril because of cough.",
            "expected_urgency": "Urgent",
            "gold_standard": {
                "primary_concern": "Elevated blood pressure in the setting of self-discontinued lisinopril.",
                "key_concerns": [
                    "Medication interruption",
                    "Persistent cough as the reported reason",
                    "EHR still lists lisinopril as active",
                ],
                "required_source_ids": [
                    "rpm:P001:alert:A001",
                    "ehr:P001:med:1",
                    "anam:P001:adherence:1",
                    "anam:P001:symptoms:1",
                ],
            },
        },
        {
            "scenario_id": "scenario_02",
            "title": "The Contextually Benign Alert",
            "patient_id": "P002",
            "alert_id": "A002",
            "description": "A high glucose reading follows a planned meal during recent medication titration.",
            "expected_urgency": "Routine",
            "gold_standard": {
                "primary_concern": "Transient glucose elevation requiring trend review rather than automatic escalation.",
                "key_concerns": [
                    "Carbohydrate-heavy meal before reading",
                    "Recent semaglutide initiation",
                    "No acute symptoms",
                ],
                "required_source_ids": [
                    "rpm:P002:alert:A002",
                    "ehr:P002:note:1",
                    "anam:P002:lifestyle:1",
                ],
            },
        },
        {
            "scenario_id": "scenario_03",
            "title": "The Silent Deterioration",
            "patient_id": "P003",
            "alert_id": "A003",
            "description": "Gradual weight gain combines with edema and mild worsening breathlessness.",
            "expected_urgency": "Urgent",
            "gold_standard": {
                "primary_concern": "Possible worsening fluid status requiring prompt clinical review.",
                "key_concerns": [
                    "2.8 kg weight increase over two weeks",
                    "Increasing ankle swelling",
                    "Mildly worse exertional breathlessness",
                ],
                "required_source_ids": [
                    "rpm:P003:alert:A003",
                    "ehr:P003:note:1",
                    "anam:P003:symptoms:1",
                    "anam:P003:symptoms:2",
                ],
            },
        },
        {
            "scenario_id": "scenario_04",
            "title": "The Incomplete Record",
            "patient_id": "P004",
            "alert_id": "A004",
            "description": "A recent transfer has a sparse EHR, making anamnesis and explicit uncertainty central.",
            "expected_urgency": "Urgent",
            "gold_standard": {
                "primary_concern": "Elevated blood pressure with an unverified medication regimen and sparse history.",
                "key_concerns": [
                    "Unknown antihypertensive name and dose",
                    "Missing external records",
                    "Morning headaches",
                ],
                "required_source_ids": [
                    "rpm:P004:alert:A004",
                    "ehr:P004:note:1",
                    "anam:P004:adherence:1",
                ],
            },
        },
        {
            "scenario_id": "scenario_05",
            "title": "The Conflicting Data",
            "patient_id": "P005",
            "alert_id": "A005",
            "description": "Reported full adherence conflicts with a sub-therapeutic valproate level.",
            "expected_urgency": "Urgent",
            "gold_standard": {
                "primary_concern": "Neutral investigation of discordant adherence and drug-level evidence.",
                "key_concerns": [
                    "Sub-therapeutic valproate level",
                    "Patient reports no missed doses",
                    "Avoid accusatory interpretation",
                ],
                "required_source_ids": [
                    "rpm:P005:alert:A005",
                    "ehr:P005:lab:1",
                    "anam:P005:adherence:1",
                ],
            },
        },
        {
            "scenario_id": "scenario_06",
            "title": "Critical Hypoxemia",
            "patient_id": "P006",
            "alert_id": "A006",
            "description": "Repeated SpO2 of 84% activates the fail-safe immediate escalation pathway.",
            "expected_urgency": "Critical",
            "gold_standard": {
                "primary_concern": "Immediate human escalation for critically low oxygen saturation.",
                "key_concerns": [
                    "SpO2 below critical threshold",
                    "Worsening breathlessness",
                    "Bypass routine synthesis",
                ],
                "required_source_ids": ["rpm:P006:alert:A006"],
            },
        },
        {
            "scenario_id": "scenario_07",
            "title": "The Device Artifact",
            "patient_id": "P007",
            "alert_id": "A007",
            "description": "An isolated tachycardia reading occurs during activity with poor watch contact.",
            "expected_urgency": "Urgent",
            "gold_standard": {
                "primary_concern": "Verify a potentially artifactual high heart-rate reading.",
                "key_concerns": [
                    "Vigorous activity",
                    "Poor skin contact",
                    "Rapid return toward baseline",
                ],
                "required_source_ids": [
                    "rpm:P007:alert:A007",
                    "anam:P007:lifestyle:1",
                ],
            },
        },
        {
            "scenario_id": "scenario_08",
            "title": "Nocturnal Hypertension and NSAID Use",
            "patient_id": "P008",
            "alert_id": "A008",
            "description": "New nocturnal hypertension appears after several days of high-dose ibuprofen use.",
            "expected_urgency": "Urgent",
            "gold_standard": {
                "primary_concern": "Nocturnal blood pressure elevation with recent NSAID exposure.",
                "key_concerns": [
                    "Repeated overnight elevation",
                    "Recent ibuprofen use",
                    "Previously controlled daytime readings",
                ],
                "required_source_ids": [
                    "rpm:P008:alert:A008",
                    "ehr:P008:note:1",
                    "anam:P008:lifestyle:1",
                ],
            },
        },
    ]


def write_rpm_csv(alerts: list[dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "rpm_readings.csv"
    fieldnames = [
        "patient_id",
        "timestamp",
        "metric",
        "value",
        "unit",
        "device_type",
        "quality",
    ]
    rows: list[dict[str, Any]] = []
    start = datetime(2026, 4, 30, 8, tzinfo=UTC)
    for patient_index in range(1, 13):
        patient_id = f"P{patient_index:03d}"
        for day in range(14):
            metric = "heart_rate"
            value = 68 + patient_index % 7 + day % 4
            unit = "bpm"
            if patient_id in {"P001", "P004", "P008", "P012"}:
                metric, value, unit = "systolic_bp", 126 + patient_index + day % 5, "mmHg"
            elif patient_id == "P002":
                metric, value, unit = "glucose", 128 + day % 18, "mg/dL"
            elif patient_id == "P003":
                metric, value, unit = "weight", round(72.0 + day * 0.18, 1), "kg"
            elif patient_id == "P006":
                metric, value, unit = "spo2", 94 - (1 if day % 6 == 0 else 0), "%"
            rows.append(
                {
                    "patient_id": patient_id,
                    "timestamp": (start + timedelta(days=day)).isoformat(),
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "device_type": "simulated RPM device",
                    "quality": "good",
                }
            )
    for alert in alerts:
        for metric, value in alert["measurements"].items():
            rows.append(
                {
                    "patient_id": alert["patient_id"],
                    "timestamp": alert["timestamp"],
                    "metric": metric,
                    "value": value,
                    "unit": alert["units"].get(metric, ""),
                    "device_type": alert["device_type"],
                    "quality": alert["device_metadata"].get("signal_quality", "good"),
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    alerts = build_alerts()
    write_json("ehr_records.json", build_ehr_records())
    write_json("anamnesis_records.json", build_anamnesis_records())
    write_json("alerts.json", alerts)
    write_json("scenarios.json", build_scenarios())
    write_json(
        "dataset_manifest.json",
        {
            "dataset_name": "ClinicalBridge Simulated Cohort",
            "version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "patient_count": 12,
            "scenario_count": 8,
            "contains_real_patient_data": False,
            "generation_method": (
                "Programmatically generated fictional records designed around capstone test cases."
            ),
            "warning": "For education and software testing only. Not clinically validated.",
        },
    )
    write_rpm_csv(alerts)
    print(f"Generated simulated dataset in {OUT}")


if __name__ == "__main__":
    main()
