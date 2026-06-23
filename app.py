from __future__ import annotations

import streamlit as st

from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.orchestrator import ClinicalBridge
from clinicalbridge.rendering import brief_to_markdown

st.set_page_config(
    page_title="ClinicalBridge",
    page_icon="🩺",
    layout="wide",
)

st.title("ClinicalBridge")
st.caption(
    "Educational prototype using entirely simulated patient data. "
    "Not a diagnostic or clinical decision-making tool."
)

settings = Settings()
repository = DataRepository(settings)
scenarios = repository.list_scenarios()
labels = {f"{item['scenario_id']} — {item['title']}": item["scenario_id"] for item in scenarios}

with st.sidebar:
    st.header("Run configuration")
    selected_label = st.selectbox("Clinical scenario", list(labels))
    st.metric("Patients", repository.patient_count())
    st.metric("Scenarios", len(scenarios))
    st.write(f"Mode: **{'OpenAI live' if settings.use_llm else 'Offline deterministic'}**")
    st.write(f"Model: `{settings.model}`")
    st.info(
        "Add OPENAI_API_KEY to .env and restart Streamlit to activate the live multi-agent path."
    )

scenario_id = labels[selected_label]
scenario = repository.get_scenario(scenario_id)

left, right = st.columns([1, 1])
with left:
    st.subheader("Scenario")
    st.write(scenario["description"])
    st.json(repository.scenario_alert(scenario_id).model_dump(mode="json"))
with right:
    st.subheader("Evaluation target")
    st.write(f"Expected urgency: **{scenario['expected_urgency']}**")
    st.write("Expected key concerns:")
    for concern in scenario["gold_standard"]["key_concerns"]:
        st.write(f"- {concern}")

if st.button("Generate Clinical Context Brief", type="primary", use_container_width=True):
    with st.spinner("Coordinating triage, retrieval, anamnesis, and synthesis agents..."):
        result = ClinicalBridge(settings=settings, repository=repository).run_scenario(scenario_id)
    st.success(
        f"Generated in {result.elapsed_seconds:.2f}s using {result.mode} mode. "
        f"Session: {result.session_id}"
    )
    if result.brief.immediate_escalation:
        st.error("Critical safety pathway activated: immediate human escalation required.")
    st.markdown(brief_to_markdown(result.brief))
    with st.expander("Agent outputs and audit details"):
        st.json(result.model_dump(mode="json"))
