from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository


def offline_settings() -> Settings:
    base = Settings()
    return Settings(
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


def test_dataset_has_required_scale_and_is_simulated():
    repository = DataRepository(offline_settings())
    repository.validate_simulated_only()
    assert repository.patient_count() == 12
    assert len(repository.scenarios) == 8
    assert len(repository.alerts) == 8


def test_every_scenario_references_existing_patient_and_alert():
    repository = DataRepository(offline_settings())
    patient_ids = {record["patient_id"] for record in repository.ehr_records}
    alert_ids = {alert["alert_id"] for alert in repository.alerts}
    for scenario in repository.scenarios:
        assert scenario["patient_id"] in patient_ids
        assert scenario["alert_id"] in alert_ids
