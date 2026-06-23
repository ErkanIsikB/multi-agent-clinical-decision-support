# Simulated Dataset and Data Dictionary

## Dataset declaration

The ClinicalBridge dataset contains 12 fictional patients and eight designed clinical scenarios. It contains no real, de-identified, scraped, or synthetic-from-real patient records. Every name and event was invented for this capstone.

The generation source is `scripts/generate_dataset.py`. Running it recreates the versioned JSON and CSV artifacts.

## Files

| File | Contents |
|---|---|
| `ehr_records.json` | Demographics, ICD-10-coded problems, medications, labs, notes, allergies, contradictions, and known gaps |
| `anamnesis_records.json` | Symptoms, adherence, lifestyle, family history, concerns, sensitive disclosures, and missing fields |
| `rpm_readings.csv` | Fourteen-day background readings plus alert-triggering observations |
| `alerts.json` | Eight structured RPM alerts consumed by the system |
| `scenarios.json` | Scenario descriptions, expected urgency, gold concerns, and required evidence sources |
| `dataset_manifest.json` | Generation metadata and explicit no-real-data declaration |

## Stable source identifiers

Traceability depends on stable source identifiers:

- `rpm:P003:alert:A003`
- `ehr:P003:note:1`
- `anam:P003:symptoms:1`

Agents preserve these identifiers through retrieval and synthesis. Evaluation checks that every cited identifier exists in the brief's source inventory.

## Patient cohort

The cohort includes hypertension, type 2 diabetes, heart failure, epilepsy, COPD, anxiety, osteoarthritis, asthma, atrial fibrillation, hypothyroidism, and chronic kidney disease. Demographic variety is included to prevent a single stereotyped patient template, but no inference about disease prevalence or real populations should be drawn from the cohort.

## Eight scenarios

1. missed antihypertensive medication because of cough;
2. glucose alert contextualized by a planned meal and medication titration;
3. gradual weight gain plus edema and breathlessness;
4. sparse transfer record with unknown medication;
5. reported adherence conflicting with a low drug level;
6. critical hypoxemia requiring immediate escalation;
7. possible smartwatch artifact during vigorous activity;
8. nocturnal hypertension after recent high-dose ibuprofen use.

## Bias and realism limitations

The records are intentionally cleaner and more consistent than real EHR data. Names and conditions were selected manually and do not form a statistically representative cohort. Gold-standard briefs were authored by the project team for software evaluation and have not been clinically validated. These limitations are treated as findings, not hidden caveats.

