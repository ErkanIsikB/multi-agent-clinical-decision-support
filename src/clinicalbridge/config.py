from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    project_root: Path = PROJECT_ROOT
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip())
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-5.4-mini"))
    embedding_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    mode: str = field(default_factory=lambda: os.getenv("CLINICALBRIDGE_MODE", "auto").lower())
    rag_backend: str = field(
        default_factory=lambda: os.getenv("CLINICALBRIDGE_RAG_BACKEND", "chroma").lower()
    )
    reasoning_effort: str = field(
        default_factory=lambda: os.getenv("CLINICALBRIDGE_REASONING_EFFORT", "low")
    )
    retrieval_k: int = field(
        default_factory=lambda: int(os.getenv("CLINICALBRIDGE_RETRIEVAL_K", "6"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("CLINICALBRIDGE_MAX_RETRIES", "2"))
    )

    @property
    def use_llm(self) -> bool:
        if self.mode == "offline":
            return False
        if self.mode == "live":
            if not self.openai_api_key:
                raise RuntimeError(
                    "CLINICALBRIDGE_MODE=live requires OPENAI_API_KEY in the .env file."
                )
            return True
        return bool(self.openai_api_key)

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data" / "simulated"

    @property
    def prompt_dir(self) -> Path:
        return self.project_root / "prompts"

    @property
    def vector_store_dir(self) -> Path:
        return self.project_root / "data" / "vector_store"

    @property
    def session_log_dir(self) -> Path:
        return self.project_root / "data" / "session_logs"
