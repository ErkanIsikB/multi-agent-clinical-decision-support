from __future__ import annotations

import json
from pathlib import Path

from clinicalbridge.config import Settings


class PromptLibrary:
    def __init__(self, settings: Settings | None = None, version: str = "v4"):
        self.settings = settings or Settings()
        self.version = version

    def system_prompt(self, agent_name: str) -> str:
        path = self.settings.prompt_dir / agent_name / f"{self.version}.md"
        if not path.exists() and self.version == "v4":
            path = self.settings.prompt_dir / agent_name / "v3.md"
        return path.read_text(encoding="utf-8")

    def few_shot_examples(self, agent_name: str) -> list[dict]:
        path = self.settings.prompt_dir / agent_name / "few_shot_examples.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def available_versions(self, agent_name: str) -> list[str]:
        folder: Path = self.settings.prompt_dir / agent_name
        return sorted(path.stem for path in folder.glob("v*.md"))
