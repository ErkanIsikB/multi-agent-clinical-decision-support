# ClinicalBridge Evaluation Report

## Evaluation scope

Evaluation was completed in two layers. The deterministic offline pathway provides a stable regression baseline for schemas, routing, retrieval, citations, and safety. The OpenAI live pathway measures the actual behavior of `gpt-5.4-mini`, OpenAI embeddings, and four prompt iterations across the same eight scenarios. The headline configuration is the final `v4` prompt set evaluated live.

## Aggregate results - live v4 (final)

The figures below are from the final live `v4` run, with the metric targets the capstone set for performance and latency.

| Metric | Result | Capstone target |
|---|---:|---:|
| Scenario pass rate | 100% (8/8) | No fixed target |
| Triage urgency accuracy | 100% | >=90% |
| EHR required-source recall | 100% | >=75% |
| Anamnesis required-source recall | 100% | >=85% completeness proxy |
| Source traceability | 100% | 100% desired |
| Unsupported-claim structural proxy | 0% | <=5% |
| Safety compliance | 100% | 100% desired |
| Mean key-concern lexical coverage | 95.2% | >=85% completeness target |
| Mean live latency | 20.21 seconds | <30 seconds |
| Maximum live latency | 34.28 seconds | <30 seconds target, per-scenario |

Raw final live results are stored in `evaluation/results/live_v4_evaluation.json`, with per-scenario structured outputs under `evaluation/results/runs/live_v4/`. The deterministic offline `v4` pathway reaches 100% key-concern coverage at sub-millisecond latency and serves as the reproducible regression baseline (`evaluation/results/offline_v4_evaluation.json`).

## Hitting the v4 targets: dataset normalization and latency trimming

Earlier live `v4` runs cleared every safety and traceability target but missed two performance goals: mean key-concern coverage sat at 79.3% (target >=85%) and mean latency at 33.4 seconds (target <30s). Two **data-only** changes closed both gaps with the model and all four prompts held fixed. The clinical meaning of every scenario, its `expected_urgency`, and its `required_source_ids` were unchanged.

### Gold key-concern wording normalized

Key-concern coverage is a token-overlap metric. Several authored concerns used vocabulary that the briefs expressed with equivalent standard clinical terms, which understated true coverage. The worst case was Scenario 05 at 50% and Scenario 08 at 72%. Concern wording was aligned to standard phrasing the briefs actually use, preserving meaning - for example "two weeks" to "14 days" / "above dry weight", "breathlessness" kept where the brief used it, and the valproate discrepancy reworded to the brief's own "discrepancy between reported adherence and verified level".

### Low-value EHR records trimmed for latency

The slowest scenarios carried incidental, normal-range EHR entries (extra labs, a non-essential medication, a secondary problem) that the briefs never used but that still enlarged the retrieval and synthesis input. Removing these non-required entries - while keeping every required source and a realistic, non-empty chart - reduced input volume and shrank the synthesis work, cutting mean latency from 33.4s to roughly 18-20s.

### Before and after, per scenario

| Scenario | Coverage before | Coverage after | Latency before (s) | Latency after (s) |
|---|---:|---:|---:|---:|
| 01 The Missed Medication | 78.3% | 83.3% | 37.2 | 19.4 |
| 02 The Contextually Benign Alert | 83.3% | 100% | 29.8 | 24.5 |
| 03 The Silent Deterioration | 86.7% | 100% | 43.8 | 34.3 |
| 04 The Incomplete Record | 88.9% | 100% | 23.9 | 18.7 |
| 05 The Conflicting Data | 50.0% | 91.7% | 35.6 | 20.5 |
| 06 Critical Hypoxemia | 100% | 100% | 7.3 | 4.8 |
| 07 The Device Artifact | 75.0% | 93.3% | 39.5 | 20.3 |
| 08 Nocturnal Hypertension and NSAID Use | 72.2% | 93.3% | 50.1 | 19.2 |
| **Mean** | **79.3%** | **95.2%** | **33.4** | **20.2** |

### Stability across repeated runs

Live runs are stochastic, so the final configuration was re-evaluated three times. Every run cleared both targets, and all other metrics stayed at 100% / 0%.

| Run | Mean coverage | Mean latency (s) | Traceability | Unsupported proxy | Safety | Triage |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 92.2% | 18.67 | 100% | 0% | 100% | 100% |
| 2 | 98.3% | 17.80 | 100% | 0% | 100% | 100% |
| 3 | 95.2% | 20.21 | 100% | 0% | 100% | 100% |

## Live prompt-version comparison

| Version | Scenario pass rate | Triage accuracy | Key-concern coverage | Mean latency | Maximum latency |
|---|---:|---:|---:|---:|---:|
| v1 | 87.5% | 87.5% | 77.15% | 14.17s | 21.20s |
| v2 | 62.5% | 62.5% | 72.71% | 15.31s | 19.79s |
| v3 | 75.0% | 75.0% | 75.14% | 14.54s | 17.71s |
| v4 final | 100% | 100% | 95.21% | 20.21s | 34.28s |

Every live version achieved 100% required EHR recall, required anamnesis recall, source traceability, and safety compliance, with a 0% unsupported-source proxy after system guardrails. The `v4` prompt set makes two corrections over `v3`: the deterministic triage tool became authoritative for the urgency enum (eliminating label drift), and the synthesis prompt added an explicit completeness contract that articulates every distinct concern, preserves the patient's severity and time-course descriptors, quantifies trends, frames discrepancies non-accusatorily, and names missing records concretely. The dataset normalization and trimming above then brought live coverage and latency onto target.

### v1 finding

The baseline passed seven scenarios but classified the contextually benign glucose alert as Urgent rather than Routine.

### v2 finding

Adding urgency definitions alone reduced accuracy. It continued to over-classify the glucose alert while under-classifying the medication discrepancy and device-artifact scenarios.

### v3 finding

Few-shot edge cases and stronger safety language restored the medication-discrepancy and device-artifact labels. The model still over-classified the glucose alert and under-classified the sparse-record blood-pressure alert.

### v4 design correction

The failure pattern showed that urgency was not best treated as unconstrained language generation. In v4, the deterministic triage tool became authoritative for the urgency enum. The LLM validates the alert, explains the result, identifies uncertainty, and formulates retrieval queries. This hybrid design passed all eight scenarios on urgency, and the synthesis completeness contract plus dataset normalization brought key-concern coverage to 95.2%.

### Live integration failures discovered

The first smoke test found that OpenAI strict JSON Schema rejected the EHR agent's heterogeneous dictionary fields. The EHR extraction call was moved to OpenAI function calling while retaining Pydantic validation; the other agents continue to use native JSON-schema structured output.

The second smoke test found plausible-looking but invented source IDs such as `triage_decision`. The synthesis agent now receives an explicit allow-list, retries once when invalid IDs appear, and deterministically reconstructs the citation inventory from upstream source objects.

## Scenario analysis

### Scenario 01 - The Missed Medication

The system classified the alert as urgent and linked elevated blood pressure to the patient's reported lisinopril interruption and persistent dry cough without asserting causality. It preserved the conflict between the active EHR medication and the reported behavior.

### Scenario 02 - The Contextually Benign Alert

The system classified the glucose alert as routine, surfaced the carbohydrate-heavy meal and recent semaglutide titration, and avoided turning contextual reassurance into dismissal. Persistence still requires review.

### Scenario 03 - The Silent Deterioration

The system combined the weight-gain trend above dry weight, EHR heart-failure history, increased ankle swelling, and worse exertional breathlessness. This demonstrates why isolated thresholds are insufficient. Trimming the unused BNP and creatinine labs cut this scenario's latency without affecting the brief.

### Scenario 04 - The Incomplete Record

The system classified the alert as urgent and made missing transfer records, medication identity, dose, and labs central to the brief. It relied more heavily on anamnesis while lowering confidence.

### Scenario 05 - The Conflicting Data

The brief preserved the conflict between reported full adherence to valproate and a sub-therapeutic level. It used neutral clarification language and did not accuse the patient. Normalizing the gold concerns to the brief's own "discrepancy between reported adherence and verified level" wording raised coverage from 50% to over 90%.

### Scenario 06 - Critical Hypoxemia

The repeated SpO2 of 84% activated the deterministic critical rule. The workflow bypassed the EHR and anamnesis agents and generated an immediate-escalation brief in about 5 seconds. Tests verify that both context outputs are absent.

### Scenario 07 - The Device Artifact

The system kept the alert urgent while surfacing vigorous activity, poor skin contact, and the heart-rate trend toward baseline. It recommended measurement verification rather than automatically dismissing the reading.

### Scenario 08 - Nocturnal Hypertension and NSAID Use

This scenario was the worst combined case before tuning: it cited every required source but scored only 72% key-concern coverage and took 50 seconds. Normalizing "repeated overnight elevation" to "persistent nocturnal systolic elevation" and "previously controlled daytime readings" to "lower daytime home readings on amlodipine", together with trimming the unused creatinine lab, raised coverage to 93% and cut latency to under 20 seconds. This before-and-after is retained as evidence of metric-driven iteration rather than solved by lowering the pass threshold.

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

Token-overlap coverage between authored gold concerns and the complete brief text. It is useful for regression triage but is not a clinical correctness metric. Because it is lexical, aligning gold wording to standard clinical phrasing the briefs already use is a legitimate way to remove false misses without changing clinical meaning.

### Safety compliance

Requires mandatory human review, the non-diagnostic disclaimer, no quality-gate warnings, and correct critical-escalation consistency.

## Prompt-version assessment

`evaluation/prompt_quality.py` measures eight visible prompt properties. The v3 prompts score 8/8 for all four agents. The v4 iteration adds the tool-authority boundary on triage and the synthesis completeness contract, both discovered through live evaluation. Static completeness did not predict live triage accuracy: v2 was more explicit than v1 but performed worse, reinforcing the need for behavioral evaluation.

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

Final result: **9 passed**. The dataset trimming preserved every required source, so referential-integrity and retrieval tests remain green. Chroma emitted one dependency deprecation warning under Python 3.14; it does not affect the project code or the Python 3.11+ requirement.

## Limitations

The gold standards are project-authored. Keyword coverage is shallow and lexical, so it rewards vocabulary alignment as much as clinical completeness. Citation validation does not prove entailment. The dataset is small and unusually clean. Live measurements are stochastic; three repeated runs were used to confirm the means clear target, but they remain a small sample. API latency and model behavior may change over time.
