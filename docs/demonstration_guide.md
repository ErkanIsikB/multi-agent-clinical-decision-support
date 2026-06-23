# Demonstration Guide

The required demonstration is supplied as `notebooks/clinicalbridge_demo.ipynb`. It is designed to show two contrasting workflows:

1. `scenario_03`, where non-critical triage triggers parallel EHR and anamnesis retrieval before synthesis;
2. `scenario_06`, where critical hypoxemia bypasses routine synthesis and immediately escalates.

## Suggested recording script

1. Open the repository and show `.env.example`, emphasizing that the real `.env` is ignored.
2. Run `clinicalbridge doctor` and identify whether the demonstration is using live or offline mode.
3. Show the scenario list and the fictional-data manifest.
4. Run the silent-deterioration scenario.
5. Point out the weight trend, ankle swelling, EHR dry weight, source IDs, uncertainty, and mandatory human review.
6. Open the session log and show triage, parallel dispatch, retrieval, anamnesis, synthesis, and quality-gate events.
7. Run the critical-hypoxemia scenario.
8. Show that EHR and anamnesis outputs are absent because the safety pathway bypassed them.
9. Close with the evaluation report, limitations, and the statement that the system is not clinically validated.

The notebook can be used directly as the annotated demonstration deliverable or screen-recorded for a video submission.

