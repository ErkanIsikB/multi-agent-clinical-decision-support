from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage

from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.llm import build_structured_llm
from clinicalbridge.memory import SessionMemory
from clinicalbridge.prompt_loader import PromptLibrary
from clinicalbridge.retrieval import BaseEHRRetriever
from clinicalbridge.schemas import (
    AnamnesisSummary,
    ClinicalContextBrief,
    ContextFinding,
    EHRContext,
    Priority,
    RecommendedAction,
    RetrievalQuery,
    RiskConsideration,
    RPMAlert,
    SourceCitation,
    TriageDecision,
    Urgency,
)
from clinicalbridge.tools import classify_alert_rules


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


class AlertTriageAgent:
    def __init__(self, settings: Settings, prompts: PromptLibrary):
        self.settings = settings
        self.prompts = prompts
        self.structured_llm = (
            build_structured_llm(TriageDecision, settings) if settings.use_llm else None
        )

    def run(self, alert: RPMAlert, memory: SessionMemory) -> TriageDecision:
        rule_urgency, rule_factors = classify_alert_rules(alert)
        if self.structured_llm:
            examples = self.prompts.few_shot_examples("triage")
            decision = self.structured_llm.invoke(
                [
                    SystemMessage(content=self.prompts.system_prompt("triage")),
                    HumanMessage(
                        content=(
                            "Classify this simulated RPM alert.\n\n"
                            f"<alert>\n{_json(alert)}\n</alert>\n\n"
                            "<deterministic_triage_tool>\n"
                            f"{_json({'urgency': rule_urgency, 'factors': rule_factors})}\n"
                            "</deterministic_triage_tool>\n\n"
                            f"<few_shot_examples>\n{_json(examples)}\n</few_shot_examples>\n\n"
                            "Return only the schema-constrained decision."
                        )
                    ),
                ]
            )
            if self.prompts.version == "v4":
                model_urgency = decision.urgency
                decision.urgency = rule_urgency
                decision.immediate_escalation = rule_urgency == Urgency.CRITICAL
                reconciliation_factor = (
                    [
                        "The deterministic triage tool is authoritative for the "
                        f"urgency label; model draft was {model_urgency}."
                    ]
                    if model_urgency != rule_urgency
                    else []
                )
                decision.decision_factors = list(
                    dict.fromkeys(
                        [
                            *rule_factors,
                            *decision.decision_factors,
                            *reconciliation_factor,
                        ]
                    )
                )
            # Critical deterministic guardrail also protects older prompt versions.
            elif rule_urgency == Urgency.CRITICAL and decision.urgency != Urgency.CRITICAL:
                decision.urgency = Urgency.CRITICAL
                decision.immediate_escalation = True
                decision.decision_factors = rule_factors + decision.decision_factors
        else:
            decision = self._offline_decision(alert, rule_urgency, rule_factors)

        memory.record("Alert Triage Agent", "triage_completed", decision.model_dump(mode="json"))
        memory.remember_entity("urgency", decision.urgency)
        memory.add_summary(
            f"Alert {alert.alert_id} classified {decision.urgency} with "
            f"{decision.confidence:.0%} confidence."
        )
        return decision

    @staticmethod
    def _offline_decision(alert: RPMAlert, urgency: Urgency, factors: list[str]) -> TriageDecision:
        category_topics = {
            "blood_pressure": ["hypertension", "blood pressure", "antihypertensive", "renal"],
            "high_glucose": ["diabetes", "glucose", "HbA1c", "insulin", "diet"],
            "weight_gain_trend": ["heart failure", "weight", "edema", "diuretic", "dyspnea"],
            "medication_discrepancy": ["medication", "drug level", "adherence", "pharmacy"],
            "device_artifact": ["cardiac", "heart rate", "device", "activity"],
            "nocturnal_hypertension": ["blood pressure", "sleep", "NSAID", "pain"],
            "hypoxemia": ["oxygen", "SpO2", "pulmonary", "respiratory"],
        }
        combined = f"{alert.alert_category} {alert.device_type}".lower()
        matched_key = next((key for key in category_topics if key in combined), None)
        topics = category_topics.get(
            matched_key or "", ["recent visits", "medications", "symptoms"]
        )
        question = (
            f"What EHR and patient-reported factors could contextualize the "
            f"{alert.alert_category.replace('_', ' ')} alert for {alert.patient_id}?"
        )
        return TriageDecision(
            patient_id=alert.patient_id,
            urgency=urgency,
            clinical_question=question,
            decision_factors=factors,
            retrieval_query=RetrievalQuery(
                patient_id=alert.patient_id,
                clinical_question=question,
                ehr_topics=topics,
                anamnesis_topics=topics + ["medication adherence", "recent symptoms"],
                lookback_days=180,
            ),
            immediate_escalation=urgency == Urgency.CRITICAL,
            confidence=0.96 if urgency == Urgency.CRITICAL else 0.88,
        )


class EHRRetrievalAgent:
    def __init__(
        self,
        settings: Settings,
        prompts: PromptLibrary,
        repository: DataRepository,
        retriever: BaseEHRRetriever,
    ):
        self.settings = settings
        self.prompts = prompts
        self.repository = repository
        self.retriever = retriever
        self.structured_llm = (
            build_structured_llm(EHRContext, settings, method="function_calling")
            if settings.use_llm
            else None
        )

    def run(self, triage: TriageDecision, memory: SessionMemory) -> EHRContext:
        query = " ".join([triage.clinical_question, *triage.retrieval_query.ehr_topics])
        chunks = self.retriever.search(
            triage.patient_id,
            query,
            self.settings.retrieval_k,
        )
        if self.structured_llm:
            context = self.structured_llm.invoke(
                [
                    SystemMessage(content=self.prompts.system_prompt("ehr")),
                    HumanMessage(
                        content=(
                            f"<clinical_question>{triage.clinical_question}</clinical_question>\n"
                            f"<retrieved_ehr_chunks>\n{_json(chunks)}\n</retrieved_ehr_chunks>\n"
                            "Use only these chunks. Preserve source_id values exactly."
                        )
                    ),
                ]
            )
        else:
            context = self._offline_context(triage.patient_id, chunks)
        memory.record("EHR Retrieval Agent", "retrieval_completed", context.model_dump(mode="json"))
        memory.add_summary(
            f"EHR retrieval returned {len(context.citations)} traceable sources at "
            f"{context.retrieval_confidence:.0%} confidence."
        )
        return context

    def _offline_context(self, patient_id: str, chunks: list[dict[str, Any]]) -> EHRContext:
        record = self.repository.get_ehr(patient_id)
        selected_ids = {chunk["source_id"] for chunk in chunks}

        def selected(section: str) -> list[dict[str, Any]]:
            items = record.get(section, [])
            relevant = [item for item in items if item["source_id"] in selected_ids]
            if section in {"problems", "medications"}:
                active = [item for item in items if item.get("status") == "active"]
                merged = {item["source_id"]: item for item in [*relevant, *active]}
                return list(merged.values())
            return relevant

        sections = {
            "problems": selected("problems"),
            "medications": selected("medications"),
            "labs": selected("labs"),
            "visit_notes": selected("visit_notes"),
            "allergies": selected("allergies"),
        }
        citations = [
            SourceCitation(
                source_id=item["source_id"],
                source_type=f"ehr_{section}",
                timestamp=item.get("date") or item.get("timestamp"),
                label=item.get("name")
                or item.get("test")
                or item.get("title")
                or item.get("substance", section),
            )
            for section, items in sections.items()
            for item in items
        ]
        missing = record.get("known_gaps", [])
        contradictions = record.get("contradictions", [])
        return EHRContext(
            patient_id=patient_id,
            demographics=record["demographics"],
            active_conditions=sections["problems"],
            active_medications=sections["medications"],
            relevant_labs=sections["labs"],
            relevant_notes=sections["visit_notes"],
            allergies=sections["allergies"],
            contradictions=contradictions,
            missing_data=missing,
            citations=citations,
            retrieval_confidence=0.9 if chunks else 0.55,
        )


class AnamnesisAgent:
    def __init__(self, settings: Settings, prompts: PromptLibrary, repository: DataRepository):
        self.settings = settings
        self.prompts = prompts
        self.repository = repository
        self.structured_llm = (
            build_structured_llm(AnamnesisSummary, settings) if settings.use_llm else None
        )

    def run(self, triage: TriageDecision, memory: SessionMemory) -> AnamnesisSummary:
        record = self.repository.get_anamnesis(triage.patient_id)
        if self.structured_llm:
            summary = self.structured_llm.invoke(
                [
                    SystemMessage(content=self.prompts.system_prompt("anamnesis")),
                    HumanMessage(
                        content=(
                            f"<clinical_question>{triage.clinical_question}</clinical_question>\n"
                            f"<anamnesis_record>\n{_json(record)}\n</anamnesis_record>\n"
                            "Use only the record. Preserve source_id values exactly."
                        )
                    ),
                ]
            )
        else:
            summary = self._offline_summary(record)
        memory.record(
            "Anamnesis Agent", "interpretation_completed", summary.model_dump(mode="json")
        )
        memory.remember_entity("patient_concerns", summary.patient_concerns)
        memory.add_summary(
            f"Anamnesis extraction found {len(summary.symptoms_and_timeline)} symptom entries "
            f"and {len(summary.medication_adherence)} adherence entries."
        )
        return summary

    @staticmethod
    def _offline_summary(record: dict[str, Any]) -> AnamnesisSummary:
        citations: list[SourceCitation] = []
        for section in (
            "symptoms",
            "medication_adherence",
            "lifestyle",
            "family_history",
            "patient_concerns",
            "sensitive_disclosures",
        ):
            for item in record.get(section, []):
                citations.append(
                    SourceCitation(
                        source_id=item["source_id"],
                        source_type=f"anamnesis_{section}",
                        timestamp=item.get("date"),
                        label=item.get("label", section.replace("_", " ")),
                    )
                )

        def texts(section: str) -> list[str]:
            return [item["text"] for item in record.get(section, [])]

        return AnamnesisSummary(
            patient_id=record["patient_id"],
            symptoms_and_timeline=texts("symptoms"),
            medication_adherence=texts("medication_adherence"),
            lifestyle_factors=texts("lifestyle"),
            family_history=texts("family_history"),
            patient_concerns=texts("patient_concerns"),
            sensitive_disclosures=texts("sensitive_disclosures"),
            missing_data=record.get("missing_data", []),
            citations=citations,
            confidence=0.92 if not record.get("missing_data") else 0.76,
        )


class SynthesisAgent:
    def __init__(self, settings: Settings, prompts: PromptLibrary):
        self.settings = settings
        self.prompts = prompts
        self.structured_llm = (
            build_structured_llm(ClinicalContextBrief, settings) if settings.use_llm else None
        )

    def run(
        self,
        alert: RPMAlert,
        triage: TriageDecision,
        ehr: EHRContext,
        anamnesis: AnamnesisSummary,
        memory: SessionMemory,
    ) -> ClinicalContextBrief:
        if self.structured_llm:
            brief = self._live_brief(alert, triage, ehr, anamnesis, memory)
        else:
            brief = self._offline_brief(alert, triage, ehr, anamnesis)
        memory.record("Synthesis Agent", "brief_generated", brief.model_dump(mode="json"))
        memory.add_summary(
            f"Clinical Context Brief generated with {brief.confidence:.0%} confidence."
        )
        return brief

    def _live_brief(
        self,
        alert: RPMAlert,
        triage: TriageDecision,
        ehr: EHRContext,
        anamnesis: AnamnesisSummary,
        memory: SessionMemory,
    ) -> ClinicalContextBrief:
        source_map = self._upstream_source_map(alert, ehr, anamnesis)
        allowed_source_ids = sorted(source_map)
        base_input = (
            f"<original_alert>\n{_json(alert)}\n</original_alert>\n"
            f"<triage_decision>\n{_json(triage)}\n</triage_decision>\n"
            f"<ehr_context>\n{_json(ehr)}\n</ehr_context>\n"
            f"<anamnesis_summary>\n{_json(anamnesis)}\n</anamnesis_summary>\n"
            f"<allowed_source_ids>\n{_json(allowed_source_ids)}\n</allowed_source_ids>\n"
            "Every finding, risk, and action must use only IDs in allowed_source_ids. "
            "Do not create identifiers for triage, missing-data lists, sections, or inferred facts. "
            "Do not make a diagnosis."
        )
        messages = [
            SystemMessage(content=self.prompts.system_prompt("synthesis")),
            HumanMessage(content=base_input),
        ]
        brief = self.structured_llm.invoke(messages)
        invalid = self._invalid_source_ids(brief, set(allowed_source_ids))
        if invalid:
            memory.record(
                "Synthesis Agent",
                "citation_retry_requested",
                {"invalid_source_ids": sorted(invalid)},
            )
            brief = self.structured_llm.invoke(
                [
                    *messages,
                    HumanMessage(
                        content=(
                            "The prior draft used invalid source identifiers: "
                            f"{', '.join(sorted(invalid))}. Regenerate the complete brief. "
                            "Use only the exact IDs in allowed_source_ids, and omit any claim "
                            "that cannot be supported by one of them."
                        )
                    ),
                ]
            )
        return self._enforce_source_allowlist(brief, source_map, memory)

    @staticmethod
    def _upstream_source_map(
        alert: RPMAlert,
        ehr: EHRContext,
        anamnesis: AnamnesisSummary,
    ) -> dict[str, SourceCitation]:
        alert_citation = SourceCitation(
            source_id=alert.source_id,
            source_type="rpm_alert",
            timestamp=alert.timestamp.isoformat(),
            label=alert.alert_category.replace("_", " "),
        )
        return {
            citation.source_id: citation
            for citation in [alert_citation, *ehr.citations, *anamnesis.citations]
        }

    @staticmethod
    def _invalid_source_ids(
        brief: ClinicalContextBrief,
        allowed_source_ids: set[str],
    ) -> set[str]:
        used_ids = {
            source_id
            for item in [
                *brief.contextual_analysis,
                *brief.risk_assessment,
                *brief.recommended_actions,
            ]
            for source_id in item.source_ids
        }
        cited_ids = {citation.source_id for citation in brief.citations}
        return (used_ids | cited_ids) - allowed_source_ids

    @staticmethod
    def _enforce_source_allowlist(
        brief: ClinicalContextBrief,
        source_map: dict[str, SourceCitation],
        memory: SessionMemory,
    ) -> ClinicalContextBrief:
        allowed = set(source_map)
        removed: set[str] = set()

        def filter_items(items):
            valid_items = []
            for item in items:
                original = set(item.source_ids)
                item.source_ids = [
                    source_id for source_id in item.source_ids if source_id in allowed
                ]
                removed.update(original - set(item.source_ids))
                if item.source_ids:
                    valid_items.append(item)
            return valid_items

        brief.contextual_analysis = filter_items(brief.contextual_analysis)
        brief.risk_assessment = filter_items(brief.risk_assessment)
        brief.recommended_actions = filter_items(brief.recommended_actions)
        referenced_ids = {
            source_id
            for item in [
                *brief.contextual_analysis,
                *brief.risk_assessment,
                *brief.recommended_actions,
            ]
            for source_id in item.source_ids
        }
        brief.citations = [source_map[source_id] for source_id in sorted(referenced_ids)]
        if removed:
            memory.record(
                "Synthesis Agent",
                "citation_allowlist_enforced",
                {"removed_source_ids": sorted(removed)},
            )
        return brief

    @staticmethod
    def critical_brief(
        alert: RPMAlert, triage: TriageDecision, memory: SessionMemory
    ) -> ClinicalContextBrief:
        citation = SourceCitation(
            source_id=alert.source_id,
            source_type="rpm_alert",
            timestamp=alert.timestamp.isoformat(),
            label=alert.alert_category.replace("_", " "),
        )
        factor_text = " ".join(triage.decision_factors)
        brief = ClinicalContextBrief(
            brief_id=f"ccb-{uuid4().hex[:10]}",
            patient_id=alert.patient_id,
            generated_at=datetime.now(UTC),
            urgency=Urgency.CRITICAL,
            alert_summary=(f"Critical simulated RPM alert from {alert.device_type}: {factor_text}"),
            patient_snapshot=(
                "Full contextual retrieval was intentionally bypassed because the critical "
                "safety rule requires immediate human escalation."
            ),
            contextual_analysis=[
                ContextFinding(
                    text="The deterministic critical threshold was crossed.",
                    source_ids=[alert.source_id],
                    confidence=0.99,
                )
            ],
            risk_assessment=[
                RiskConsideration(
                    text=(
                        "Delay while awaiting automated synthesis could be unsafe; the measurement "
                        "requires immediate verification and clinician review."
                    ),
                    source_ids=[alert.source_id],
                    confidence=0.99,
                )
            ],
            recommended_actions=[
                RecommendedAction(
                    action=(
                        "Immediately notify the responsible clinician or emergency escalation "
                        "pathway and verify the reading using the approved clinical protocol."
                    ),
                    rationale="Critical alerts fail safe and bypass nonessential automation.",
                    priority=Priority.IMMEDIATE,
                    confidence=0.99,
                    source_ids=[alert.source_id],
                )
            ],
            uncertainties_and_gaps=[
                "EHR and anamnesis context were not retrieved before escalation.",
                "Device accuracy and the patient's current symptoms require human verification.",
            ],
            confidence=0.99,
            citations=[citation],
            immediate_escalation=True,
        )
        memory.record("Orchestrator", "critical_escalation", brief.model_dump(mode="json"))
        return brief

    @staticmethod
    def _offline_brief(
        alert: RPMAlert,
        triage: TriageDecision,
        ehr: EHRContext,
        anamnesis: AnamnesisSummary,
    ) -> ClinicalContextBrief:
        all_citations = [
            SourceCitation(
                source_id=alert.source_id,
                source_type="rpm_alert",
                timestamp=alert.timestamp.isoformat(),
                label=alert.alert_category.replace("_", " "),
            ),
            *ehr.citations,
            *anamnesis.citations,
        ]
        citation_ids = {citation.source_id for citation in all_citations}

        def ids_containing(*needles: str) -> list[str]:
            lowered = [needle.lower() for needle in needles]
            matches = [
                citation.source_id
                for citation in all_citations
                if any(
                    needle in f"{citation.source_id} {citation.label}".lower() for needle in lowered
                )
            ]
            return matches or [alert.source_id]

        findings: list[ContextFinding] = [
            ContextFinding(
                text=f"The RPM alert was classified {triage.urgency}.",
                source_ids=[alert.source_id],
                confidence=triage.confidence,
            )
        ]
        for text, source in zip(
            [
                *anamnesis.symptoms_and_timeline[:2],
                *anamnesis.medication_adherence[:2],
                *anamnesis.lifestyle_factors[:1],
            ],
            [
                *[c.source_id for c in anamnesis.citations if "symptoms" in c.source_type][:2],
                *[
                    c.source_id
                    for c in anamnesis.citations
                    if "medication_adherence" in c.source_type
                ][:2],
                *[c.source_id for c in anamnesis.citations if "lifestyle" in c.source_type][:1],
            ],
            strict=False,
        ):
            findings.append(
                ContextFinding(text=text, source_ids=[source], confidence=anamnesis.confidence)
            )

        combined_text = " ".join(
            [
                triage.clinical_question,
                *anamnesis.symptoms_and_timeline,
                *anamnesis.medication_adherence,
                *anamnesis.lifestyle_factors,
                *ehr.contradictions,
                *[str(item) for item in ehr.relevant_labs],
                *[str(item) for item in ehr.relevant_notes],
            ]
        ).lower()
        risks: list[RiskConsideration] = []
        actions: list[RecommendedAction] = [
            RecommendedAction(
                action="Review the alert and cited context using the appropriate clinical protocol.",
                rationale="The system provides context only; a clinician must determine next steps.",
                priority=Priority.HIGH if triage.urgency == Urgency.URGENT else Priority.STANDARD,
                confidence=0.95,
                source_ids=[alert.source_id],
            )
        ]

        if "cough" in combined_text and ("stopped" in combined_text or "missed" in combined_text):
            sources = ids_containing("adherence", "medication", "cough")
            risks.append(
                RiskConsideration(
                    text=(
                        "The elevated blood pressure is temporally associated with a reported "
                        "medication interruption after cough; this warrants medication review "
                        "without assuming causality."
                    ),
                    source_ids=sources,
                    confidence=0.9,
                )
            )
            actions.append(
                RecommendedAction(
                    action="Confirm adherence, side effects, and the current antihypertensive plan.",
                    rationale="The patient reports stopping medication because of persistent cough.",
                    priority=Priority.HIGH,
                    confidence=0.9,
                    source_ids=sources,
                )
            )
        if "planned dietary" in combined_text or "medication adjustment" in combined_text:
            sources = ids_containing("diet", "glucose", "visit", "medication")
            risks.append(
                RiskConsideration(
                    text=(
                        "The glucose alert may reflect a documented short-term dietary change and "
                        "recent treatment adjustment, but persistence still requires review."
                    ),
                    source_ids=sources,
                    confidence=0.84,
                )
            )
        if "ankle swelling" in combined_text or "fluid" in combined_text:
            sources = ids_containing("weight", "symptom", "heart failure", "note")
            risks.append(
                RiskConsideration(
                    text=(
                        "Gradual weight increase together with reported ankle swelling may indicate "
                        "worsening fluid status and deserves prompt clinician assessment."
                    ),
                    source_ids=sources,
                    confidence=0.91,
                )
            )
        if ehr.missing_data:
            sources = [alert.source_id]
            risks.append(
                RiskConsideration(
                    text="Sparse longitudinal EHR data materially limits contextual confidence.",
                    source_ids=sources,
                    confidence=0.95,
                )
            )
        if "sub-therapeutic" in combined_text or "subtherapeutic" in combined_text:
            sources = ids_containing("drug level", "adherence", "lab")
            risks.append(
                RiskConsideration(
                    text=(
                        "Patient-reported adherence and the measured drug level conflict; the "
                        "discrepancy should be explored neutrally rather than interpreted as blame."
                    ),
                    source_ids=sources,
                    confidence=0.89,
                )
            )
        if "poor skin contact" in combined_text or "vigorous activity" in combined_text:
            sources = ids_containing("device", "activity", "heart rate")
            risks.append(
                RiskConsideration(
                    text=(
                        "The isolated heart-rate alert may be affected by activity or device contact, "
                        "so measurement verification is important before escalation."
                    ),
                    source_ids=sources,
                    confidence=0.88,
                )
            )
        if "ibuprofen" in combined_text or "nsaid" in combined_text:
            sources = ids_containing("ibuprofen", "nsaid", "blood pressure")
            risks.append(
                RiskConsideration(
                    text=(
                        "Repeated overnight blood pressure elevation follows recent ibuprofen use "
                        "despite previously controlled daytime readings; NSAID exposure is a "
                        "relevant contextual factor for clinician review."
                    ),
                    source_ids=sources,
                    confidence=0.86,
                )
            )
        if not risks:
            risks.append(
                RiskConsideration(
                    text=(
                        "The alert requires clinical interpretation in context; available simulated "
                        "data do not support an automated diagnostic conclusion."
                    ),
                    source_ids=[alert.source_id],
                    confidence=0.82,
                )
            )

        valid_risks = [
            risk
            for risk in risks
            if all(source_id in citation_ids for source_id in risk.source_ids)
        ]
        conditions = (
            ", ".join(
                item.get("name", "unspecified condition") for item in ehr.active_conditions[:3]
            )
            or "no active condition retrieved"
        )
        medications = (
            ", ".join(
                item.get("name", "unspecified medication") for item in ehr.active_medications[:3]
            )
            or "no active medication retrieved"
        )
        measurement_text = ", ".join(
            f"{key.replace('_', ' ')} {value:g} {alert.units.get(key, '')}".strip()
            for key, value in alert.measurements.items()
        )
        uncertainties = [*ehr.missing_data, *anamnesis.missing_data, *ehr.contradictions]
        if not uncertainties:
            uncertainties = [
                "The prototype cannot independently verify device accuracy or symptoms."
            ]

        return ClinicalContextBrief(
            brief_id=f"ccb-{uuid4().hex[:10]}",
            patient_id=alert.patient_id,
            generated_at=datetime.now(UTC),
            urgency=triage.urgency,
            alert_summary=(
                f"{alert.alert_category.replace('_', ' ').title()} alert: {measurement_text}."
            ),
            patient_snapshot=f"Active conditions: {conditions}. Current treatment: {medications}.",
            contextual_analysis=findings,
            risk_assessment=valid_risks,
            recommended_actions=actions,
            uncertainties_and_gaps=uncertainties,
            confidence=min(triage.confidence, ehr.retrieval_confidence, anamnesis.confidence),
            citations=all_citations,
            immediate_escalation=False,
        )
