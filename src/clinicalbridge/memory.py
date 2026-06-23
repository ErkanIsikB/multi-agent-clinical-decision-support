from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from clinicalbridge.config import Settings


class SessionMemory:
    """Auditable session, summary, and patient-entity memory for one workflow run."""

    def __init__(self, patient_id: str, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.session_id = f"session-{uuid4().hex[:12]}"
        self.patient_id = patient_id
        self.events: list[dict[str, Any]] = []
        self.entity_memory: dict[str, Any] = {"patient_id": patient_id}
        self.summary_memory: list[str] = []
        self._lock = Lock()

    def record(self, agent: str, event: str, payload: Any) -> None:
        with self._lock:
            self.events.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "agent": agent,
                    "event": event,
                    "payload": payload,
                }
            )

    def remember_entity(self, key: str, value: Any) -> None:
        self.entity_memory[key] = value

    def add_summary(self, text: str) -> None:
        self.summary_memory.append(text)

    def persist(self) -> Path:
        directory = self.settings.session_log_dir
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.session_id}.json"
        path.write_text(
            json.dumps(
                {
                    "session_id": self.session_id,
                    "patient_id": self.patient_id,
                    "entity_memory": self.entity_memory,
                    "summary_memory": self.summary_memory,
                    "events": self.events,
                },
                indent=2,
                ensure_ascii=False,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        return path
