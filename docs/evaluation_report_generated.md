# ClinicalBridge Evaluation Report

Generated: 2026-06-20T19:31:55.462259+00:00

Evaluation mode: **offline**

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
| Mean latency | 0.003s | <30s |

## Scenario results

| Scenario | Urgency | Sources | Concern coverage | Safety | Pass |
|---|---:|---:|---:|---:|---:|
| scenario_01 - The Missed Medication | Yes | 100% | 85% | Yes | Pass |
| scenario_02 - The Contextually Benign Alert | Yes | 100% | 72% | Yes | Pass |
| scenario_03 - The Silent Deterioration | Yes | 100% | 59% | Yes | Pass |
| scenario_04 - The Incomplete Record | Yes | 100% | 61% | Yes | Pass |
| scenario_05 - The Conflicting Data | Yes | 100% | 67% | Yes | Pass |
| scenario_06 - Critical Hypoxemia | Yes | 100% | 56% | Yes | Pass |
| scenario_07 - The Device Artifact | Yes | 100% | 67% | Yes | Pass |
| scenario_08 - Nocturnal Hypertension and NSAID Use | Yes | 100% | 100% | Yes | Pass |

## Interpretation

This automated run evaluates the deterministic offline pathway so the result is reproducible without sending any data to an external API. It validates orchestration, safety routing, source traceability, retrieval coverage, and output contracts. A live OpenAI run should be recorded separately after the API key is added; model outputs are non-deterministic and may produce different scores.

The unsupported-claim rate is a structural proxy: it checks whether every finding, risk, and recommendation refers only to source IDs present in the brief. It does not replace expert clinical review or factual entailment grading.
