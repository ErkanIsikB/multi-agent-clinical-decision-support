from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.tools import classify_alert_rules


def repository() -> DataRepository:
    base = Settings()
    settings = Settings(
        project_root=base.project_root,
        openai_api_key="",
        model=base.model,
        embedding_model=base.embedding_model,
        mode="offline",
        rag_backend=base.rag_backend,
        reasoning_effort=base.reasoning_effort,
        retrieval_k=base.retrieval_k,
        max_retries=base.max_retries,
    )
    return DataRepository(settings)


def test_critical_hypoxemia_rule_is_fail_safe():
    urgency, factors = classify_alert_rules(repository().get_alert("A006"))
    assert urgency.value == "Critical"
    assert any("SpO2" in factor for factor in factors)


def test_noncritical_scenarios_match_gold_urgency():
    repo = repository()
    for scenario in repo.scenarios:
        urgency, _ = classify_alert_rules(repo.get_alert(scenario["alert_id"]))
        assert urgency.value == scenario["expected_urgency"]
