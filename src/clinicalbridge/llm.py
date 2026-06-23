from __future__ import annotations

from typing import TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from clinicalbridge.config import Settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def build_structured_llm(
    schema: type[SchemaT],
    settings: Settings,
    method: str = "json_schema",
) -> object:
    """Build a Responses-API-backed LangChain model constrained by a Pydantic schema."""

    llm = ChatOpenAI(
        model=settings.model,
        api_key=settings.openai_api_key,
        use_responses_api=True,
        reasoning_effort=settings.reasoning_effort,
        max_retries=settings.max_retries,
        timeout=60,
    )
    return llm.with_structured_output(schema, method=method)
