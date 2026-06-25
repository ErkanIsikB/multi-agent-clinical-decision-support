# Agent-Level Test Results

Source: final live OpenAI evaluation, prompt version v4, eight simulated scenarios.

| Component | Test criterion | Result | Evidence used |
|---|---:|---:|---|
| Triage | Query relevance / expert review | 100% pass, 8/8 scenarios | The triage route selected the expected urgency class for every authored scenario. This is reported as `triage_accuracy = 1.0` in `evaluation/results/live_v4_evaluation.json`. |
| EHR Retrieval | Retrieval precision | 100% pass, 8/8 scenarios | The final briefs used only scenario-relevant EHR context and preserved all required EHR gold-standard sources where EHR context was expected. This is supported by `ehr_retrieval_recall = 1.0` and `source_traceability = 1.0`. |
| Anamnesis | Interpretation accuracy | 100% pass, 8/8 scenarios | All required anamnesis facts were carried into the brief without unsupported-source warnings. This is reported as `anamnesis_source_recall = 1.0` with `hallucination_proxy_rate = 0.0`. |
| Synthesis | Clinical accuracy vs. source | 100% pass, 8/8 scenarios | Every finding, risk statement, and recommendation cited an available source, and all scenarios passed the final quality gate. This is reported as `scenario_pass_rate = 1.0`, `source_traceability = 1.0`, and `safety_compliance = 1.0`. |

Important interpretation note: these results show consistency against the project-authored simulated gold standards. They do not establish real-world clinical validity.
