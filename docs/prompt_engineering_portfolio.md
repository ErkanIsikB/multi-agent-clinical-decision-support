# ClinicalBridge Prompt Engineering Portfolio

## Purpose

This portfolio documents the prompt system used by the four ClinicalBridge agents. Complete prompt text is versioned under `prompts/<agent>/v1.md`, `v2.md`, and `v3.md`; each agent also has three few-shot examples, including one edge case. A triage-only v4 prompt records the final architecture correction discovered through live evaluation.

The portfolio distinguishes three kinds of evidence:

- static prompt analysis, which can be reproduced without an API key;
- deterministic integration tests, which validate schemas, routing, citations, and safety behavior;
- live model evaluation using the configured OpenAI API.

## Shared design principles

All final prompts use a consistent contract:

1. a narrow role and explicit non-diagnostic boundary;
2. delimited, untrusted data sections;
3. a named procedure rather than a vague request;
4. OpenAI structured output with Pydantic validation;
5. exact preservation of source IDs;
6. explicit unknown and missing-data behavior;
7. confidence calibration;
8. positive and negative constraints;
9. concise auditable factors instead of stored hidden chain-of-thought;
10. mandatory human review.

## Prompt versioning method

### Version 1: baseline

Version 1 establishes the role and primary task. It is intentionally short and serves as the baseline for static comparison. Its main weaknesses are underspecified evidence handling, incomplete output rules, and limited safety detail.

### Version 2: structured workflow

Version 2 adds task decomposition, urgency or evidence definitions, source preservation, and explicit output expectations. It reduces ambiguous behavior but still leaves some edge cases implicit.

### Version 3: safety and traceability

Version 3 adds claim-level source requirements, contradiction handling, uncertainty behavior, negative constraints, confidence calibration, critical routing requirements, and neutral language for sensitive conflicts.

### Version 4: tool-authority boundary

Live v1-v3 results showed that urgency classification remained unstable even when the prompt was more explicit. The final v4 changes only triage: the deterministic classification tool owns the urgency enum, while the LLM validates input, explains the result, and formulates retrieval queries. EHR, anamnesis, and synthesis remain on v3.

## Alert Triage Agent

### Objective

Classify the RPM alert, record concise decision factors, and formulate focused retrieval queries.

### Structured output

`TriageDecision` includes patient ID, urgency, clinical question, decision factors, EHR and anamnesis topics, lookback period, immediate-escalation flag, and confidence.

### Iteration log

| Version | Change | Rationale | Expected effect |
|---|---|---|---|
| v1 | Added basic four-level classification and no-diagnosis rule | Establish a measurable baseline | Produces a usable label but may vary in threshold interpretation |
| v2 | Defined each urgency level and a five-step review process | Reduce label drift and improve retrieval questions | More consistent classification and query relevance |
| v3 | Added supplied-threshold priority, device quality, safer-tie behavior, critical bypass, explicit unknown handling, and no-lowering rule | Address high-stakes false reassurance and ambiguous sensor data | Better safety compliance and edge-case behavior |
| v4 | Made the deterministic triage tool authoritative for urgency; retained the LLM for explanation and query generation | Resolve live label drift that prompts alone did not fix | Stable, auditable urgency with flexible language tasks |

### Failure case targeted

**Input:** heart rate 142 bpm during vigorous movement with poor contact, returning to 78 bpm ten minutes later.

**Baseline risk:** v1 can overconfidently call the reading a device error or dismiss the threshold breach.

**Revision:** v3 requires the agent to preserve the alert, acknowledge artifact evidence, and choose the safer class when evidence conflicts. Live evaluation still showed inconsistent labels. v4 moves the enum decision to the deterministic tool and retains the model's useful explanation and retrieval work.

### Few-shot strategy

The examples cover critical hypoxemia, gradual weight gain, and a possible device artifact. They demonstrate the urgency boundary and the difference between explaining uncertainty and dismissing an alert.

## EHR Retrieval Agent

### Objective

Convert patient-scoped RAG results into a concise structured context object without adding clinical facts.

### Structured output

`EHRContext` contains demographics, conditions, medications, labs, notes, allergies, contradictions, missing data, citations, and retrieval confidence.

### Iteration log

| Version | Change | Rationale | Expected effect |
|---|---|---|---|
| v1 | Requested relevant EHR categories | Establish extraction baseline | Can retrieve facts but may omit dates or mix inference with evidence |
| v2 | Added source preservation, contradiction separation, and confidence | Improve traceability and uncertainty | More auditable retrieval output |
| v3 | Added direct-support rule, active-medication caveat, exact dates/units, absent-category handling, relevance filtering, and prohibition on causal inference | Address hallucinated fills and copied-forward status ambiguity | Higher precision and safer missing-data behavior |

### Failure case targeted

**Input:** a sparse transfer record containing only “external records requested but unavailable.”

**Baseline risk:** v1 may infer a typical medication for hypertension or produce an empty result without explaining why.

**Revision:** v3 requires an empty medication list, explicit missing-data entries, lower confidence, and citation of the transfer note. The schema prevents free-form filler.

### RAG configuration

- source-level chunks rather than large patient documents;
- OpenAI `text-embedding-3-small`;
- persistent Chroma collection;
- mandatory patient-ID metadata filtering;
- top-k configured through `.env`;
- TF-IDF fallback for deterministic tests;
- retrieval evaluation against scenario-required source IDs.

## Anamnesis Agent

### Objective

Interpret self-reported symptoms, adherence, lifestyle, family history, and concerns in neutral clinical language.

### Structured output

`AnamnesisSummary` contains symptoms and timeline, reported adherence, lifestyle, family history, patient concerns, sensitive disclosures, missing data, citations, and confidence.

### Iteration log

| Version | Change | Rationale | Expected effect |
|---|---|---|---|
| v1 | Requested relevant patient-reported categories | Establish baseline extraction | May lose timing and over-normalize patient language |
| v2 | Added timing, relevant negatives, neutral adherence language, and citation | Improve completeness and respect | Better structured intake summary |
| v3 | Distinguished prescribed status from reported behavior, limited sensitive disclosure, prohibited intent inference, preserved source IDs, and added missing-data rules | Address stigma, accusation, and unsupported translation | Safer handling of adherence and sensitive information |

### Failure case targeted

**Input:** “I have taken every dose. I do not know why the level is low.”

**Baseline risk:** v1 may convert the low level into “nonadherent” and contradict the patient's account.

**Revision:** v3 reports full claimed adherence, preserves the low result for synthesis, and explicitly prohibits accusing or inferring intent. The final discrepancy is framed as something to clarify.

### Conversational design

The capstone's stored anamnesis records simulate the output of an intake conversation. The prompt supports multi-turn use by preserving timing, concerns, and missing categories in structured fields. Session memory records extracted concerns and summary facts without sharing memory between patients.

## Synthesis Agent

### Objective

Produce a concise Clinical Context Brief from the three upstream outputs and the original alert.

### Structured output

The final schema includes claim-level citations for contextual findings, risk considerations, and recommended actions. Recommendations are clinician-review actions rather than treatment instructions.

### Iteration log

| Version | Change | Rationale | Expected effect |
|---|---|---|---|
| v1 | Defined six brief sections and basic citations | Establish readable output | Can produce polished but weakly grounded prose |
| v2 | Added explicit multi-source correlation, cautious risk language, action confidence, and missing-data section | Improve clinical usefulness and uncertainty | More complete, less diagnostic briefs |
| v3 | Added claim-level traceability contract, valid-ID rule, weakest-source confidence, mandatory human review, concise audience target, no-overrule rule, and explicit unsupported-claim omission | Address hallucination and automation bias | Higher traceability and safety compliance |

### Failure case targeted

**Input:** elevated blood pressure, an EHR medication marked active, and anamnesis reporting that the patient stopped it because of cough.

**Baseline risk:** v1 may state that the patient is taking lisinopril or conclude that the medication caused the alert.

**Revision:** v3 preserves the contradiction, uses cautious temporal-association language, cites both sources, and recommends clinician review of adherence, side effects, and treatment plan without changing medication.

### Brief-length discipline

The intended reader has less than 60 seconds. The prompt tells the model to include only alert-relevant patient details and to avoid repeating raw records. The dashboard keeps the agent audit trail available under an expandable section rather than placing it in the primary brief.

## Output schemas and validation

All confidence values are constrained to 0–1. Urgency and priority are enums. Contextual findings cannot have an empty source list. The synthesis agent receives the exact upstream source-ID allow-list, retries once when invalid IDs appear, removes any remaining invalid references, and rebuilds citations from upstream source objects. The quality gate checks the final inventory and restores mandatory safety text if needed.

This validation addresses format compliance; it does not prove clinical truth. The evaluation report therefore labels unsupported-source detection as a hallucination proxy.

## Reasoning design

The prompts use explicit task decomposition:

- triage checks metadata, thresholds, baseline, trend, and quality;
- EHR retrieval links the question to evidence categories;
- anamnesis separates symptoms, adherence, lifestyle, and concerns;
- synthesis correlates sources, assesses uncertainty, and prioritizes actions.

The system stores concise decision factors and source-linked outputs. It does not request or persist hidden chain-of-thought. This choice provides auditable reasoning artifacts without presenting verbose model rationales as evidence.

## Parameter rationale

- Model: `gpt-5.4-mini` by default, configurable.
- Reasoning effort: low, because tasks are bounded extraction and synthesis.
- Temperature: not forced for current reasoning-model compatibility.
- Retries: two bounded provider retries.
- Timeout: 60 seconds per call.
- Retrieval top-k: six by default.
- Embedding model: `text-embedding-3-small`.

## Static prompt-quality evaluation

`evaluation/prompt_quality.py` checks each version for eight visible properties: role definition, structured output, safety boundary, uncertainty, traceability, negative constraints, confidence calibration, and explicit procedure. This is a reproducible prompt-documentation metric, not a model-performance score.

## Live iteration results

| Version | Pass rate | Triage accuracy | Mean latency | Main finding |
|---|---:|---:|---:|---|
| v1 | 87.5% | 87.5% | 14.17s | Over-classified the benign glucose alert |
| v2 | 62.5% | 62.5% | 15.31s | Definitions alone introduced under- and over-classification |
| v3 | 75.0% | 75.0% | 14.54s | Fixed discrepancy and artifact cases; two urgency errors remained |
| v4 | 100% | 100% | 15.65s | Tool-owned urgency eliminated label drift |

All versions achieved 100% required-source recall, source traceability, and safety compliance after system guardrails. Raw structured outputs are stored per scenario under `evaluation/results/runs/`.

### Live integration failure: strict EHR schema

The first live smoke test returned HTTP 400 because OpenAI strict JSON Schema requires `additionalProperties: false`, while `EHRContext` intentionally contains heterogeneous clinical dictionaries. The EHR agent was switched to OpenAI function calling and continues to validate with Pydantic.

### Live integration failure: invented source IDs

The next smoke test generated internally plausible identifiers such as `triage_decision` and an invented missing-data source. Prompt instructions alone were insufficient. The final system supplies an explicit allow-list, performs one corrective retry, and reconstructs the citation inventory from genuine upstream evidence.
