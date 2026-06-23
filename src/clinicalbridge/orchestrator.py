from __future__ import annotations

from time import perf_counter
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from clinicalbridge.agents import (
    AlertTriageAgent,
    AnamnesisAgent,
    EHRRetrievalAgent,
    SynthesisAgent,
)
from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.memory import SessionMemory
from clinicalbridge.prompt_loader import PromptLibrary
from clinicalbridge.retrieval import build_retriever
from clinicalbridge.schemas import (
    AnamnesisSummary,
    ClinicalContextBrief,
    EHRContext,
    RPMAlert,
    TriageDecision,
    WorkflowResult,
)


class WorkflowState(TypedDict, total=False):
    alert: RPMAlert
    memory: SessionMemory
    triage: TriageDecision
    ehr_context: EHRContext
    anamnesis_summary: AnamnesisSummary
    brief: ClinicalContextBrief
    warnings: list[str]


class ClinicalBridge:
    """Coordinate specialized agents into one auditable Clinical Context Brief."""

    def __init__(
        self,
        settings: Settings | None = None,
        repository: DataRepository | None = None,
        prompt_version: str = "v4",
    ):
        self.settings = settings or Settings()
        self.repository = repository or DataRepository(self.settings)
        self.repository.validate_simulated_only()
        prompts = PromptLibrary(self.settings, version=prompt_version)
        retriever = build_retriever(self.repository, self.settings)
        self.triage_agent = AlertTriageAgent(self.settings, prompts)
        self.ehr_agent = EHRRetrievalAgent(self.settings, prompts, self.repository, retriever)
        self.anamnesis_agent = AnamnesisAgent(self.settings, prompts, self.repository)
        self.synthesis_agent = SynthesisAgent(self.settings, prompts)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(WorkflowState)
        builder.add_node("triage", self._triage)
        builder.add_node("dispatch_context", self._dispatch_context)
        builder.add_node("ehr_retrieval", self._ehr_retrieval)
        builder.add_node("anamnesis", self._anamnesis)
        builder.add_node("synthesis", self._synthesis)
        builder.add_node("critical_escalation", self._critical_escalation)
        builder.add_node("quality_gate", self._quality_gate)

        builder.add_edge(START, "triage")
        builder.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {
                "critical_escalation": "critical_escalation",
                "dispatch_context": "dispatch_context",
            },
        )
        builder.add_edge("critical_escalation", "quality_gate")
        builder.add_edge("dispatch_context", "ehr_retrieval")
        builder.add_edge("dispatch_context", "anamnesis")
        builder.add_edge("ehr_retrieval", "synthesis")
        builder.add_edge("anamnesis", "synthesis")
        builder.add_edge("synthesis", "quality_gate")
        builder.add_edge("quality_gate", END)
        return builder.compile()

    def _triage(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "triage": self.triage_agent.run(state["alert"], state["memory"]),
            "warnings": [],
        }

    @staticmethod
    def _route_after_triage(state: WorkflowState) -> str:
        return "critical_escalation" if state["triage"].immediate_escalation else "dispatch_context"

    @staticmethod
    def _dispatch_context(state: WorkflowState) -> dict[str, Any]:
        state["memory"].record(
            "Orchestrator",
            "parallel_dispatch",
            {"targets": ["EHR Retrieval Agent", "Anamnesis Agent"]},
        )
        return {}

    def _ehr_retrieval(self, state: WorkflowState) -> dict[str, Any]:
        return {"ehr_context": self.ehr_agent.run(state["triage"], state["memory"])}

    def _anamnesis(self, state: WorkflowState) -> dict[str, Any]:
        return {"anamnesis_summary": self.anamnesis_agent.run(state["triage"], state["memory"])}

    def _synthesis(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "brief": self.synthesis_agent.run(
                state["alert"],
                state["triage"],
                state["ehr_context"],
                state["anamnesis_summary"],
                state["memory"],
            )
        }

    def _critical_escalation(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "brief": self.synthesis_agent.critical_brief(
                state["alert"], state["triage"], state["memory"]
            )
        }

    @staticmethod
    def _quality_gate(state: WorkflowState) -> dict[str, Any]:
        brief = state["brief"]
        citation_ids = {citation.source_id for citation in brief.citations}
        referenced_ids = {
            source_id
            for item in [
                *brief.contextual_analysis,
                *brief.risk_assessment,
                *brief.recommended_actions,
            ]
            for source_id in item.source_ids
        }
        warnings = list(state.get("warnings", []))
        unknown = sorted(referenced_ids - citation_ids)
        if unknown:
            warnings.append(f"Unknown citation IDs referenced: {', '.join(unknown)}")
        if not brief.human_review_required:
            state["memory"].record(
                "Orchestrator",
                "safety_field_restored",
                {"field": "human_review_required"},
            )
            brief.human_review_required = True
        if "not a diagnosis" not in brief.disclaimer.lower():
            state["memory"].record(
                "Orchestrator",
                "safety_field_restored",
                {"field": "disclaimer"},
            )
            brief.disclaimer = (
                "Educational prototype using simulated data. This output is not a diagnosis or "
                "medical advice and must be reviewed by a qualified clinician."
            )
        state["memory"].record(
            "Orchestrator",
            "quality_gate_completed",
            {"warnings": warnings, "referenced_source_count": len(referenced_ids)},
        )
        return {"brief": brief, "warnings": warnings}

    def run_alert(self, alert: RPMAlert) -> WorkflowResult:
        started = perf_counter()
        memory = SessionMemory(alert.patient_id, self.settings)
        memory.record("Orchestrator", "alert_received", alert.model_dump(mode="json"))
        final_state = self.graph.invoke({"alert": alert, "memory": memory})
        memory.persist()
        elapsed = perf_counter() - started
        return WorkflowResult(
            alert=alert,
            triage=final_state["triage"],
            ehr_context=final_state.get("ehr_context"),
            anamnesis_summary=final_state.get("anamnesis_summary"),
            brief=final_state["brief"],
            session_id=memory.session_id,
            elapsed_seconds=elapsed,
            mode="live" if self.settings.use_llm else "offline",
            warnings=final_state.get("warnings", []),
        )

    def run_scenario(self, scenario_id: str) -> WorkflowResult:
        return self.run_alert(self.repository.scenario_alert(scenario_id))
