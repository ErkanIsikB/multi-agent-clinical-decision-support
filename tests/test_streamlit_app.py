from streamlit.testing.v1 import AppTest


def test_streamlit_dashboard_renders_and_runs_scenario(monkeypatch):
    monkeypatch.setenv("CLINICALBRIDGE_MODE", "offline")
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "ClinicalBridge"
    assert len(app.selectbox) == 1
    assert len(app.button) == 1

    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert any("Generated in" in message.value for message in app.success)
