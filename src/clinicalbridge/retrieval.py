from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.tools import flatten_record


class BaseEHRRetriever(ABC):
    @abstractmethod
    def search(self, patient_id: str, query: str, k: int) -> list[dict[str, Any]]:
        raise NotImplementedError


class LexicalEHRRetriever(BaseEHRRetriever):
    """Local TF-IDF retriever used for tests and key-free demonstrations."""

    def __init__(self, repository: DataRepository):
        self.chunks = [
            {"source_id": source_id, "text": text, "metadata": metadata}
            for record in repository.ehr_records
            for source_id, text, metadata in flatten_record(record)
        ]

    def search(self, patient_id: str, query: str, k: int) -> list[dict[str, Any]]:
        candidates = [c for c in self.chunks if c["metadata"]["patient_id"] == patient_id]
        corpus = [c["text"] for c in candidates] + [query]
        matrix = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(corpus)
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        ranked = scores.argsort()[::-1][:k]
        return [
            {**candidates[index], "score": float(scores[index])}
            for index in ranked
            if scores[index] > 0
        ]


class ChromaEHRRetriever(BaseEHRRetriever):
    """Persistent OpenAI-embedding vector store for the live RAG path."""

    def __init__(self, repository: DataRepository, settings: Settings):
        settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        self.store = Chroma(
            collection_name="clinicalbridge_ehr",
            embedding_function=embeddings,
            persist_directory=str(settings.vector_store_dir),
        )
        if self.store._collection.count() == 0:
            documents: list[Document] = []
            ids: list[str] = []
            for record in repository.ehr_records:
                for source_id, text, metadata in flatten_record(record):
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "patient_id": metadata["patient_id"],
                                "section": metadata["section"],
                                "payload_json": json.dumps(
                                    metadata["payload"], ensure_ascii=False, default=str
                                ),
                                "source_id": source_id,
                            },
                        )
                    )
                    ids.append(source_id.replace(":", "_"))
            self.store.add_documents(documents=documents, ids=ids)

    def search(self, patient_id: str, query: str, k: int) -> list[dict[str, Any]]:
        results = self.store.similarity_search_with_relevance_scores(
            query,
            k=k,
            filter={"patient_id": patient_id},
        )
        return [
            {
                "source_id": document.metadata["source_id"],
                "text": document.page_content,
                "metadata": {
                    "patient_id": document.metadata["patient_id"],
                    "section": document.metadata["section"],
                    "payload": json.loads(document.metadata["payload_json"]),
                },
                "score": float(score),
            }
            for document, score in results
        ]


def build_retriever(
    repository: DataRepository, settings: Settings | None = None
) -> BaseEHRRetriever:
    settings = settings or Settings()
    if settings.use_llm and settings.rag_backend == "chroma":
        return ChromaEHRRetriever(repository, settings)
    return LexicalEHRRetriever(repository)
