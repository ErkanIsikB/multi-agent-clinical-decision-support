from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ("triage", "ehr", "anamnesis", "synthesis")
VERSIONS = ("v1", "v2", "v3")
CHECKS = {
    "role_definition": ["role", "identity"],
    "structured_output": ["schema", "structured"],
    "safety_boundary": ["do not diagnose", "not a diagnostician", "not medical"],
    "uncertainty": ["missing", "unknown", "uncertainty"],
    "source_traceability": ["source_id", "cite", "citation"],
    "negative_constraints": ["never", "do not"],
    "confidence_calibration": ["confidence", "calibrat"],
    "explicit_procedure": ["procedure", "method", "1."],
}


def score_prompt(text: str) -> dict:
    lowered = text.lower()
    checks = {
        name: any(marker in lowered for marker in markers) for name, markers in CHECKS.items()
    }
    return {
        "score": sum(checks.values()),
        "maximum": len(checks),
        "checks": checks,
        "word_count": len(text.split()),
    }


def main() -> None:
    results = {}
    for agent in AGENTS:
        results[agent] = {}
        for version in VERSIONS:
            text = (ROOT / "prompts" / agent / f"{version}.md").read_text(encoding="utf-8")
            results[agent][version] = score_prompt(text)
    output = ROOT / "evaluation" / "results" / "prompt_quality.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
