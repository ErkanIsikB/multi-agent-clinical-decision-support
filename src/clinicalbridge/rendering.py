from __future__ import annotations

from clinicalbridge.schemas import ClinicalContextBrief, WorkflowResult


def brief_to_markdown(brief: ClinicalContextBrief) -> str:
    findings = "\n".join(
        f"- {item.text} _Sources: {', '.join(item.source_ids)}_"
        for item in brief.contextual_analysis
    )
    risks = "\n".join(
        f"- {item.text} _Sources: {', '.join(item.source_ids)}_" for item in brief.risk_assessment
    )
    actions = "\n".join(
        f"- **{item.priority}:** {item.action} — {item.rationale} "
        f"_(confidence {item.confidence:.0%}; sources: {', '.join(item.source_ids)})_"
        for item in brief.recommended_actions
    )
    gaps = "\n".join(f"- {gap}" for gap in brief.uncertainties_and_gaps)
    citations = "\n".join(
        f"- `{item.source_id}` — {item.label} ({item.source_type})" for item in brief.citations
    )
    return f"""# Clinical Context Brief

**Patient:** {brief.patient_id}  
**Urgency:** {brief.urgency}  
**Confidence:** {brief.confidence:.0%}  
**Immediate escalation:** {"Yes" if brief.immediate_escalation else "No"}

## Alert Summary

{brief.alert_summary}

## Patient Snapshot

{brief.patient_snapshot}

## Contextual Analysis

{findings}

## Risk Assessment

{risks}

## Recommended Actions

{actions}

## Uncertainties and Gaps

{gaps}

## Sources

{citations}

> {brief.disclaimer}
"""


def result_summary(result: WorkflowResult) -> str:
    return (
        f"{result.brief.urgency} brief for {result.brief.patient_id} "
        f"generated in {result.elapsed_seconds:.2f}s ({result.mode} mode)."
    )
