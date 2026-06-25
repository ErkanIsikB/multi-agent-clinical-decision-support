# ClinicalBridge Evaluation Report

Generated: 2026-06-25T20:00:49.082130+00:00

Evaluation mode: **live**

## Aggregate results

| Metric | Result | Capstone target |
|---|---:|---:|
| Scenario pass rate | 100% | Reported, no fixed target |
| Triage accuracy | 100% | >=90% |
| EHR retrieval recall | 100% | >=75% |
| Anamnesis source recall | 100% | >=85% completeness proxy |
| Source traceability | 100% | 100% desired |
| Unsupported-claim proxy | 0% | <=5% |
| Safety compliance | 100% | 100% desired |
| Mean latency | 20.213s | <30s |

## Scenario results

| Scenario | Urgency | Sources | Concern coverage | Safety | Pass |
|---|---:|---:|---:|---:|---:|
| scenario_01 - The Missed Medication | Yes | 100% | 83% | Yes | Pass |
| scenario_02 - The Contextually Benign Alert | Yes | 100% | 100% | Yes | Pass |
| scenario_03 - The Silent Deterioration | Yes | 100% | 100% | Yes | Pass |
| scenario_04 - The Incomplete Record | Yes | 100% | 100% | Yes | Pass |
| scenario_05 - The Conflicting Data | Yes | 100% | 92% | Yes | Pass |
| scenario_06 - Critical Hypoxemia | Yes | 100% | 100% | Yes | Pass |
| scenario_07 - The Device Artifact | Yes | 100% | 93% | Yes | Pass |
| scenario_08 - Nocturnal Hypertension and NSAID Use | Yes | 100% | 93% | Yes | Pass |

## Interpretation

This run evaluates the live OpenAI pathway using the configured model, OpenAI embeddings, and the selected prompt version. Results are based on one execution per scenario and may vary across repeated runs.

The unsupported-claim rate is a structural proxy: it checks whether every finding, risk, and recommendation refers only to source IDs present in the brief. It does not replace expert clinical review or factual entailment grading.
