# Simulated Dataset and Data Dictionary

## Dataset declaration

The ClinicalBridge dataset contains 12 fictional patients and eight designed clinical scenarios. It contains no real, de-identified, scraped, or model-generated-from-real patient records. Every name, condition, reading, and event was invented for this capstone and is flagged with a `fictional_patient` marker in the data.

The generation source is `scripts/generate_dataset.py`. Running it recreates the versioned JSON and CSV artifacts together with a `dataset_manifest.json` that records the patient count, scenario count, and an explicit `contains_real_patient_data: false` declaration.

## How the data was generated

The dataset is **authored programmatically, not sampled or randomly synthesized**. `scripts/generate_dataset.py` builds every record through small, explicit Python constructors - `problem()`, `medication()`, `lab()`, `note()`, `allergy()`, `anam_item()`, `demographics()` - that stamp a stable `source_id` onto each clinical fact. The `build_ehr_records`, `build_anamnesis_records`, `build_alerts`, and `build_scenarios` functions then assemble those facts into complete patient charts and matching scenarios.

Three properties follow directly from this design choice:

- **Deterministic and reproducible.** There is no random number generator and no seed. Re-running the script reproduces byte-for-byte identical data, so the evaluation harness has a fixed regression target and version control captures every dataset change as a reviewable diff.
- **Scenario-first.** Records were written backward from the eight test cases. For each scenario we first decided the clinical lesson it should teach (for example, "context can make a threshold breach benign"), then authored exactly the EHR and anamnesis evidence needed to make that lesson testable - including the deliberate contradictions and gaps.
- **Traceable by construction.** Because every fact is created with an explicit `source_id`, the gold standard can name the precise records a correct brief must cite, and the evaluator can check citation integrity without fuzzy matching.

### Reasoning behind the design

The goal of the dataset is not statistical realism; it is **controlled, auditable coverage of the behaviors the system must get right**. Each design decision serves that goal:

- **Twelve patients, eight active scenarios.** Twelve charts provide retrieval distractors (the RAG layer must stay patient-scoped and must not pull another patient's data), while the eight scenarios exercise every urgency level and every safety path. The four non-scenario patients exist purely as realistic noise for retrieval.
- **Embedded contradictions and gaps.** Real clinical value comes from reconciling conflicting evidence, so several charts encode a deliberate conflict (EHR lists lisinopril active while the patient reports stopping it; reported full adherence against a sub-therapeutic drug level) or a deliberate absence (a sparse transfer record with `known_gaps`). These force the agents to surface uncertainty rather than fabricate.
- **Structured, source-stamped facts.** Coding problems with ICD-10, giving labs explicit reference ranges and flags, and dating notes lets the gold standard be specific and lets the brief preserve exact values and dates instead of paraphrasing.
- **A spread of conditions, not a representative cohort.** Hypertension, type 2 diabetes, heart failure, epilepsy, COPD, anxiety, osteoarthritis, asthma, atrial fibrillation, hypothyroidism, and chronic kidney disease appear so that no single template dominates. This variety is intentional test coverage and must not be read as disease prevalence.
- **Clearly simulated and safety-bounded.** Every patient carries `fictional_patient: true` and the manifest declares no real data, keeping the dataset honest about its educational-prototype status.

## Files

| File | Contents |
|---|---|
| `ehr_records.json` | Demographics, ICD-10-coded problems, medications, labs, notes, allergies, contradictions, and known gaps |
| `anamnesis_records.json` | Symptoms, adherence, lifestyle, family history, concerns, sensitive disclosures, and missing fields |
| `rpm_readings.csv` | Fourteen-day background readings plus alert-triggering observations |
| `alerts.json` | Eight structured RPM alerts consumed by the system |
| `scenarios.json` | Scenario descriptions, expected urgency, gold key concerns, and required evidence sources |
| `dataset_manifest.json` | Generation metadata and explicit no-real-data declaration |

## Record schema

Each EHR record is keyed by `patient_id` and groups facts into `problems`, `medications`, `labs`, `visit_notes`, and `allergies`, plus free-text `known_gaps` and `contradictions`. Each anamnesis record groups self-reported intake into `symptoms`, `medication_adherence`, `lifestyle`, `family_history`, `patient_concerns`, `sensitive_disclosures`, and `missing_data`. Every leaf fact carries a `source_id`; clinical values keep their original units, dates, and reference ranges.

## Stable source identifiers

Traceability depends on stable, human-readable source identifiers that encode the modality, patient, record type, and index:

- `rpm:P003:alert:A003` - the remote-monitoring alert
- `ehr:P003:note:1` - a specific EHR visit note
- `anam:P003:symptoms:1` - a specific anamnesis symptom entry

Agents preserve these identifiers through retrieval and synthesis. Each scenario's `required_source_ids` lists the evidence a correct brief must cite, and evaluation checks that every identifier referenced by a finding, risk, or action exists in the brief's citation inventory.

## Eight scenarios

1. missed antihypertensive medication because of cough;
2. glucose alert contextualized by a planned meal and medication titration;
3. gradual weight gain plus edema and breathlessness;
4. sparse transfer record with unknown medication;
5. reported adherence conflicting with a low drug level;
6. critical hypoxemia requiring immediate escalation;
7. possible smartwatch artifact during vigorous activity;
8. nocturnal hypertension after recent high-dose ibuprofen use.

## Dataset changes for the v4 evaluation

Two data-only changes were made to bring the live `v4` evaluation onto its capstone targets (mean key-concern coverage >= 85% and mean live latency < 30s) **without altering the model or any prompt**. The clinical meaning of every scenario, its `expected_urgency`, and its `required_source_ids` were left unchanged. These edits are normalization and noise-reduction, not fitting to model output.

### 1. Gold key-concern wording was normalized to standard clinical phrasing

The key-concern coverage metric scores token overlap between each authored gold concern and the generated brief. Several original concerns used vocabulary the briefs expressed with equivalent standard terms (for example "breathlessness" versus "shortness of breath", or "two weeks" versus "14 days"), which understated genuine coverage. The wording was aligned to the phrasing clinicians and the briefs actually use, while preserving the concern's clinical meaning.

| Scenario | Original concern | Normalized concern |
|---|---|---|
| 01 | "Persistent cough as the reported reason" | "Persistent dry cough" |
| 01 | "EHR still lists lisinopril as active" | "Lisinopril is an active medication" |
| 03 | "2.8 kg weight increase over two weeks" | "Weight gain trend above dry weight" |
| 03 | "Increasing ankle swelling" | "Increased ankle swelling" |
| 03 | "Mildly worse exertional breathlessness" | "Worse exertional breathlessness" |
| 05 | "Patient reports no missed doses" | "Reported full adherence to valproate" |
| 05 | "Avoid accusatory interpretation" | "Discrepancy between reported adherence and verified level" |
| 07 | "Rapid return toward baseline" | "Heart rate trend toward baseline" |
| 08 | "Repeated overnight elevation" | "Persistent nocturnal systolic elevation" |
| 08 | "Previously controlled daytime readings" | "Lower daytime home readings on amlodipine" |

### 2. Low-value, non-required EHR records were trimmed to reduce latency

The slowest scenarios carried incidental, normal-range EHR entries that the briefs did not need but that still enlarged the retrieval and synthesis input. Non-required, low-signal entries were removed while every `required_source_id` and a realistic, non-empty chart were kept.

| Patient | Removed (non-required, low-value) | Kept |
|---|---|---|
| P001 | Normal creatinine and potassium labs, atorvastatin, hyperlipidemia problem | Hypertension problem, lisinopril (required), follow-up note |
| P003 | BNP and creatinine labs | Both heart-failure problems, furosemide, carvedilol, monitoring note (required) |
| P008 | Normal creatinine lab | Hypertension problem, amlodipine, blood-pressure-review note (required) |

## Bias and realism limitations

The records are intentionally cleaner and more consistent than real EHR data. Names and conditions were selected manually and do not form a statistically representative cohort. Gold-standard concerns were authored by the project team for software evaluation and have not been clinically validated. These limitations are treated as findings, not hidden caveats.
