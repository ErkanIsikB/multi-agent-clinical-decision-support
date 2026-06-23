# Clinical Context Brief

**Patient:** P006  
**Urgency:** Critical  
**Confidence:** 99%  
**Immediate escalation:** Yes

## Alert Summary

Critical simulated RPM alert from Pulse oximeter: SpO2 84% is below the critical safety threshold of 88%.

## Patient Snapshot

Full contextual retrieval was intentionally bypassed because the critical safety rule requires immediate human escalation.

## Contextual Analysis

- The deterministic critical threshold was crossed. _Sources: rpm:P006:alert:A006_

## Risk Assessment

- Delay while awaiting automated synthesis could be unsafe; the measurement requires immediate verification and clinician review. _Sources: rpm:P006:alert:A006_

## Recommended Actions

- **Immediate:** Immediately notify the responsible clinician or emergency escalation pathway and verify the reading using the approved clinical protocol. — Critical alerts fail safe and bypass nonessential automation. _(confidence 99%; sources: rpm:P006:alert:A006)_

## Uncertainties and Gaps

- EHR and anamnesis context were not retrieved before escalation.
- Device accuracy and the patient's current symptoms require human verification.

## Sources

- `rpm:P006:alert:A006` — hypoxemia (rpm_alert)

> Educational prototype using simulated data. This output is not a diagnosis or medical advice and must be reviewed by a qualified clinician.

