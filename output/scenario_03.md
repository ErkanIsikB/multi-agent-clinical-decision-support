# Clinical Context Brief

**Patient:** P003  
**Urgency:** Urgent  
**Confidence:** 88%  
**Immediate escalation:** No

## Alert Summary

Weight Gain Trend alert: weight 74.8 kg.

## Patient Snapshot

Active conditions: Heart failure with reduced ejection fraction, Essential hypertension. Current treatment: Furosemide, Carvedilol.

## Contextual Analysis

- The RPM alert was classified Urgent. _Sources: rpm:P003:alert:A003_
- Ankle swelling has gradually increased over six days. _Sources: anam:P003:symptoms:1_
- Mild breathlessness when climbing stairs is slightly worse than usual. _Sources: anam:P003:symptoms:2_
- Reports taking furosemide every morning. _Sources: anam:P003:adherence:1_
- Ate several salty prepared meals this week. _Sources: anam:P003:lifestyle:1_

## Risk Assessment

- Gradual weight increase together with reported ankle swelling may indicate worsening fluid status and deserves prompt clinician assessment. _Sources: rpm:P003:alert:A003, ehr:P003:problem:1, ehr:P003:note:1, anam:P003:symptoms:1, anam:P003:symptoms:2_

## Recommended Actions

- **High:** Review the alert and cited context using the appropriate clinical protocol. — The system provides context only; a clinician must determine next steps. _(confidence 95%; sources: rpm:P003:alert:A003)_

## Uncertainties and Gaps

- The prototype cannot independently verify device accuracy or symptoms.

## Sources

- `rpm:P003:alert:A003` — weight gain trend (rpm_alert)
- `ehr:P003:problem:1` — Heart failure with reduced ejection fraction (ehr_problems)
- `ehr:P003:problem:2` — Essential hypertension (ehr_problems)
- `ehr:P003:med:1` — Furosemide (ehr_medications)
- `ehr:P003:med:2` — Carvedilol (ehr_medications)
- `ehr:P003:lab:2` — Creatinine (ehr_labs)
- `ehr:P003:note:1` — Heart failure monitoring plan (ehr_visit_notes)
- `anam:P003:symptoms:1` — symptoms (anamnesis_symptoms)
- `anam:P003:symptoms:2` — symptoms (anamnesis_symptoms)
- `anam:P003:adherence:1` — adherence (anamnesis_medication_adherence)
- `anam:P003:lifestyle:1` — lifestyle (anamnesis_lifestyle)
- `anam:P003:concern:1` — concern (anamnesis_patient_concerns)

> Educational prototype using simulated data. This output is not a diagnosis or medical advice and must be reviewed by a qualified clinician.

