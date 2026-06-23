from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Urgency(StrEnum):
    CRITICAL = "Critical"
    URGENT = "Urgent"
    ROUTINE = "Routine"
    INFORMATIONAL = "Informational"


class Priority(StrEnum):
    IMMEDIATE = "Immediate"
    HIGH = "High"
    STANDARD = "Standard"
    LOW = "Low"


class RPMAlert(BaseModel):
    alert_id: str
    patient_id: str
    timestamp: datetime
    device_type: str
    alert_category: str
    measurements: dict[str, float]
    units: dict[str, str]
    baseline: dict[str, float] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict)
    trend: list[dict[str, Any]] = Field(default_factory=list)
    device_metadata: dict[str, Any] = Field(default_factory=dict)
    source_id: str


class RetrievalQuery(BaseModel):
    patient_id: str
    clinical_question: str
    ehr_topics: list[str]
    anamnesis_topics: list[str]
    lookback_days: int = Field(ge=1, le=3650)


class TriageDecision(BaseModel):
    patient_id: str
    urgency: Urgency
    clinical_question: str
    decision_factors: list[str]
    retrieval_query: RetrievalQuery
    immediate_escalation: bool
    confidence: float = Field(ge=0, le=1)


class SourceCitation(BaseModel):
    source_id: str
    source_type: str
    timestamp: str | None = None
    label: str


class EHRContext(BaseModel):
    patient_id: str
    demographics: dict[str, Any]
    active_conditions: list[dict[str, Any]]
    active_medications: list[dict[str, Any]]
    relevant_labs: list[dict[str, Any]]
    relevant_notes: list[dict[str, Any]]
    allergies: list[dict[str, Any]]
    contradictions: list[str]
    missing_data: list[str]
    citations: list[SourceCitation]
    retrieval_confidence: float = Field(ge=0, le=1)


class AnamnesisSummary(BaseModel):
    patient_id: str
    symptoms_and_timeline: list[str]
    medication_adherence: list[str]
    lifestyle_factors: list[str]
    family_history: list[str]
    patient_concerns: list[str]
    sensitive_disclosures: list[str]
    missing_data: list[str]
    citations: list[SourceCitation]
    confidence: float = Field(ge=0, le=1)


class ContextFinding(BaseModel):
    text: str
    source_ids: list[str]
    confidence: float = Field(ge=0, le=1)

    @field_validator("source_ids")
    @classmethod
    def source_ids_must_not_be_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Every contextual finding must cite at least one source.")
        return value


class RiskConsideration(BaseModel):
    text: str
    source_ids: list[str]
    confidence: float = Field(ge=0, le=1)


class RecommendedAction(BaseModel):
    action: str
    rationale: str
    priority: Priority
    confidence: float = Field(ge=0, le=1)
    source_ids: list[str]


class ClinicalContextBrief(BaseModel):
    brief_id: str
    patient_id: str
    generated_at: datetime
    urgency: Urgency
    alert_summary: str
    patient_snapshot: str
    contextual_analysis: list[ContextFinding]
    risk_assessment: list[RiskConsideration]
    recommended_actions: list[RecommendedAction]
    uncertainties_and_gaps: list[str]
    confidence: float = Field(ge=0, le=1)
    citations: list[SourceCitation]
    immediate_escalation: bool = False
    human_review_required: bool = True
    disclaimer: str = (
        "Educational prototype using simulated data. This output is not a diagnosis or "
        "medical advice and must be reviewed by a qualified clinician."
    )


class WorkflowResult(BaseModel):
    alert: RPMAlert
    triage: TriageDecision
    ehr_context: EHRContext | None = None
    anamnesis_summary: AnamnesisSummary | None = None
    brief: ClinicalContextBrief
    session_id: str
    elapsed_seconds: float
    mode: str
    warnings: list[str] = Field(default_factory=list)
