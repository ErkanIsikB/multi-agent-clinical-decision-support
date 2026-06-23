# Ethical Considerations and Limitations

ClinicalBridge is an educational prototype. It is not a medical device, has not undergone clinical validation, and must not influence care for a real person.

## Non-negotiable safeguards

All records are fictional. Every output requires human review, avoids diagnostic claims, cites source records, states uncertainty, and includes a visible disclaimer. Critical alerts take a fail-safe path that prioritizes immediate human escalation over automated completeness.

## Hallucination risk

Schema validation prevents malformed output but cannot prove factual correctness. Source IDs improve traceability but do not guarantee that the cited text entails the generated statement. Real deployment would require deterministic evidence verification, clinical knowledge checks, red-team testing, and independent validation.

## Simulated-data limitations

The dataset is too small, clean, and purpose-built to represent real EHR complexity. It lacks copied-forward notes, ambiguous abbreviations, delayed updates, duplicate medication records, sensor outages, multilingual intake, and many social determinants. Performance on these scenarios cannot be generalized to clinical settings.

## Evaluation limitations

The gold standards were written for the project and may contain author bias. Automated keyword coverage is only a rough completeness proxy. The offline pathway is deterministic and useful for regression testing, but it does not measure the same behavior as the live LLM pathway. Live results should be reviewed and reported separately.

## Bias

The fictional cohort does not represent disease prevalence, demographic distributions, disability, gender identity, socioeconomic variation, or health-system inequities. Prompt language can also encode assumptions about adherence and credibility. The project counters one common failure mode by requiring neutral language for contradictory adherence evidence, but that does not eliminate bias.

## Privacy and security

The repository must never ingest real patient records. API keys remain in a Git-ignored `.env`. Runtime session logs are excluded from version control. A production system would additionally require access control, encryption, retention policy, audit governance, vendor review, and regulatory approval.

## Multi-agent failure modes

Specialized agents improve testability but introduce cascading errors, stale context, inter-agent disagreement, and orchestration failures. A confident synthesis can still be wrong if retrieval missed a crucial source. The final confidence score therefore cannot be treated as a calibrated probability of clinical correctness.

## Human factors

A concise brief may reduce cognitive load, but poor prioritization can also create automation bias. The prototype should be evaluated not only for accuracy but for whether users over-trust it, overlook uncertainty, or misunderstand recommendations as orders.

