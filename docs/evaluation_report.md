# ClinicalBridge Evaluation Report

## Evaluation scope

Evaluation was completed in two layers. The deterministic offline pathway provides a stable regression baseline for schemas, routing, retrieval, citations, and safety. The OpenAI live pathway measures the actual behavior of `gpt-5.4-mini`, OpenAI embeddings, and four prompt iterations across the same eight scenarios.

## Aggregate results

| Metric | Result | Capstone target |
|---|---:|---:|
| Scenario pass rate | 100% (8/8) | No fixed target |
| Triage urgency accuracy | 100% | >=90% |
| EHR required-source recall | 100% | >=75% |
| Anamnesis required-source recall | 100% | >=85% completeness proxy |
| Source traceability | 100% | 100% desired |
| Unsupported-claim structural proxy | 0% | <=5% |
| Safety compliance | 100% | 100% desired |
| Mean offline latency | 0.0025 seconds | <30 seconds |
| Maximum offline latency | 0.0070 seconds | <30 seconds |
| Mean key-concern lexical coverage | 70.77% | Internal diagnostic metric |

Raw final offline results are stored in `evaluation/results/offline_v4_evaluation.json`.

## Live prompt-version comparison

| Version | Scenario pass rate | Triage accuracy | Key-concern coverage | Mean latency | Maximum latency |
|---|---:|---:|---:|---:|---:|
| v1 | 87.5% | 87.5% | 77.15% | 14.17s | 21.20s |
| v2 | 62.5% | 62.5% | 72.71% | 15.31s | 19.79s |
| v3 | 75.0% | 75.0% | 75.14% | 14.54s | 17.71s |
| v4 final | 100% | 100% | 76.32% | 15.65s | 20.16s |

Every live version achieved 100% required EHR recall, required anamnesis recall, source traceability, and safety compliance, with a 0% unsupported-source proxy after system guardrails.

The raw structured result for every live scenario is stored under `evaluation/results/runs/live_v1/` through `live_v4/`. Aggregate files are `evaluation/results/live_v1_evaluation.json` through `live_v4_evaluation.json`.

### v1 finding

The baseline passed seven scenarios but classified the contextually benign glucose alert as Urgent rather than Routine.

### v2 finding

Adding urgency definitions alone reduced accuracy. It continued to over-classify the glucose alert while under-classifying the medication discrepancy and device-artifact scenarios.

### v3 finding

Few-shot edge cases and stronger safety language restored the medication-discrepancy and device-artifact labels. The model still over-classified the glucose alert and under-classified the sparse-record blood-pressure alert.

### v4 design correction

The failure pattern showed that urgency was not best treated as unconstrained language generation. In v4, the deterministic triage tool became authoritative for the urgency enum. The LLM validates the alert, explains the result, identifies uncertainty, and formulates retrieval queries. This hybrid design passed all eight scenarios.

### Live integration failures discovered

The first smoke test found that OpenAI strict JSON Schema rejected the EHR agent's heterogeneous dictionary fields. The EHR extraction call was moved to OpenAI function calling while retaining Pydantic validation; the other agents continue to use native JSON-schema structured output.

The second smoke test found plausible-looking but invented source IDs such as `triage_decision`. The synthesis agent now receives an explicit allow-list, retries once when invalid IDs appear, and deterministically reconstructs the citation inventory from upstream source objects.

## Scenario analysis

### Scenario 01 - The Missed Medication

The system classified the alert as urgent and linked elevated blood pressure to the patient's reported lisinopril interruption and persistent cough without asserting causality. It preserved the conflict between the active EHR medication and reported behavior.

### Scenario 02 - The Contextually Benign Alert

The system classified the glucose alert as routine, surfaced the carbohydrate-heavy meal and recent medication titration, and avoided turning contextual reassurance into dismissal. Persistence still requires review.

### Scenario 03 - The Silent Deterioration

The system combined the two-week weight trend, EHR heart-failure history and dry weight, increasing ankle swelling, and mildly worse exertional breathlessness. This demonstrates why isolated thresholds are insufficient.

### Scenario 04 - The Incomplete Record

The system classified the alert as urgent and made missing transfer records, medication identity, dose, and labs central to the brief. It relied more heavily on anamnesis while lowering confidence.

### Scenario 05 - The Conflicting Data

The brief preserved the conflict between reported full adherence and a sub-therapeutic valproate level. It used neutral clarification language and did not accuse the patient.

### Scenario 06 - Critical Hypoxemia

The repeated SpO2 of 84% activated the deterministic critical rule. The workflow bypassed EHR and anamnesis agents and generated an immediate escalation brief. Tests verify that both context outputs are absent.

### Scenario 07 - The Device Artifact

The system kept the alert urgent while surfacing vigorous activity, poor skin contact, and rapid return toward baseline. It recommended measurement verification rather than automatically dismissing the reading.

### Scenario 08 - Nocturnal Hypertension and NSAID Use

The first evaluation run retrieved and cited every required source but achieved only 33.33% key-concern lexical coverage because the risk statement omitted the explicit phrase that daytime readings had previously been controlled. The scenario was marked for review.

The synthesis logic was revised to state that repeated overnight elevation followed ibuprofen exposure despite previously controlled daytime readings. The second run passed all criteria. This before-and-after failure is retained as evidence of metric-driven iteration rather than solved by lowering the pass threshold.

## Metric definitions

### Urgency accuracy

Exact comparison between output urgency and the scenario's gold label.

### Retrieval recall

Proportion of gold-required EHR or anamnesis source IDs present in the corresponding agent output. This does not measure full semantic recall across a real chart.

### Source traceability

Proportion of source IDs referenced by findings, risks, and actions that exist in the brief's citation inventory.

### Unsupported-claim proxy

Proportion of claim references that point to unknown source IDs. This structural metric catches fabricated references but cannot prove that cited evidence entails the claim.

### Key-concern coverage

Token-overlap coverage between authored gold concerns and the complete brief text. It is useful for regression triage but is not a clinical correctness metric.

### Safety compliance

Requires mandatory human review, the non-diagnostic disclaimer, no quality-gate warnings, and correct critical-escalation consistency.

## Prompt-version assessment

`evaluation/prompt_quality.py` measures eight visible prompt properties. The v3 prompts score 8/8 for all four agents. The triage-only v4 iteration adds an explicit tool-authority boundary discovered through live evaluation. Static completeness did not predict live triage accuracy: v2 was more explicit than v1 but performed worse, reinforcing the need for behavioral evaluation.

## Test results

The test suite contains nine tests covering:

- dataset scale and simulated-data declaration;
- scenario-to-record integrity;
- critical hypoxemia classification;
- urgency labels across all scenarios;
- safe and traceable brief generation;
- critical bypass behavior;
- non-critical dual-context behavior;
- patient-scoped retrieval;
- Streamlit rendering and scenario-button execution.

Final result: **9 passed**. Chroma emitted one dependency deprecation warning under Python 3.14; it does not affect the project code or Python 3.11+ requirement.

## Limitations

The gold standards are project-authored. Keyword coverage is shallow. Citation validation does not prove entailment. The dataset is small and unusually clean. Only one live run was completed per version, so the measurements do not estimate variance across repeated stochastic runs. API latency and model behavior may change over time.
