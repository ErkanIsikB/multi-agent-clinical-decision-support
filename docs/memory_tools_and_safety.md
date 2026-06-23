# Memory, Tools, and Safety Architecture

## Memory design

ClinicalBridge implements memory at the workflow-session level rather than creating an unbounded cross-patient chat history.

### Event memory

Every agent records a timestamped event with its structured output. This provides an auditable inter-agent transcript without relying on hidden model reasoning.

### Summary memory

Each agent appends a concise summary such as the triage classification, number of retrieved sources, and synthesis confidence. These summaries support debugging and demonstration.

### Entity memory

Stable session facts such as patient ID, urgency, and patient concerns are stored separately. Entity memory is scoped to one run and never crosses patient boundaries.

## Tools

### Alert classification tool

A deterministic threshold function checks critical and urgent rules. It is used as a safety backstop and as the offline triage implementation.

### EHR search tool

The live path uses OpenAI embeddings and Chroma with a mandatory patient-ID metadata filter. The offline path uses TF-IDF and the same patient filter.

### Data parsing tool

Pydantic models validate alerts, agent messages, and final briefs. Invalid urgency enums, confidence values, or uncited contextual findings are rejected.

## Safety layers

1. dataset manifest rejects any package that does not explicitly declare `contains_real_patient_data: false`;
2. deterministic critical thresholds override a lower LLM classification;
3. critical alerts bypass context retrieval and routine synthesis;
4. prompts prohibit diagnosis, prescription, unsupported facts, and accusatory adherence language;
5. structured outputs carry source IDs at claim level;
6. synthesis receives an exact upstream source allow-list and reconstructs citations from genuine source objects;
7. the quality gate detects unresolved unknown references;
8. human review and a non-diagnostic disclaimer are mandatory;
9. the final v4 triage design gives the deterministic tool authority over the urgency enum;
10. tests cover all eight scenarios and the critical bypass.

## Why raw chain-of-thought is not stored

The course brief asks for explicit reasoning design. ClinicalBridge implements that requirement as auditable decision factors, structured evidence links, and documented synthesis stages rather than requesting or persisting private hidden chain-of-thought. This makes the reasoning contract inspectable while avoiding verbose, unverified rationales that could be mistaken for clinical evidence.
