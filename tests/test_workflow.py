from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.orchestrator import ClinicalBridge


def offline_system() -> ClinicalBridge:
    base = Settings()
    settings = Settings(
        project_root=base.project_root,
        openai_api_key="",
        model=base.model,
        embedding_model=base.embedding_model,
        mode="offline",
        rag_backend=base.rag_backend,
        reasoning_effort=base.reasoning_effort,
        retrieval_k=8,
        max_retries=base.max_retries,
    )
    return ClinicalBridge(settings=settings, repository=DataRepository(settings))


def test_all_scenarios_generate_traceable_safe_briefs():
    system = offline_system()
    for scenario in system.repository.scenarios:
        result = system.run_scenario(scenario["scenario_id"])
        assert result.brief.urgency.value == scenario["expected_urgency"]
        assert result.brief.human_review_required is True
        assert "not a diagnosis" in result.brief.disclaimer.lower()
        citation_ids = {item.source_id for item in result.brief.citations}
        referenced_ids = {
            source_id
            for item in [
                *result.brief.contextual_analysis,
                *result.brief.risk_assessment,
                *result.brief.recommended_actions,
            ]
            for source_id in item.source_ids
        }
        assert referenced_ids <= citation_ids
        assert not result.warnings


def test_critical_scenario_bypasses_context_agents():
    result = offline_system().run_scenario("scenario_06")
    assert result.brief.immediate_escalation is True
    assert result.ehr_context is None
    assert result.anamnesis_summary is None


def test_noncritical_scenario_uses_both_context_agents():
    result = offline_system().run_scenario("scenario_03")
    assert result.ehr_context is not None
    assert result.anamnesis_summary is not None
    assert result.brief.immediate_escalation is False
