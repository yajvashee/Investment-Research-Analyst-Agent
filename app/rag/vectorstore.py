"""Chroma dense vector search, matching the previous RAG project."""
from __future__ import annotations
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document


COLLECTION_NAME = "investment_research"


class DenseRetriever:
    def __init__(self, documents: list[Document], embeddings: object, persist_directory: Path | None = None) -> None:
        options = {"collection_name": COLLECTION_NAME}
        if persist_directory is not None:
            persist_directory.mkdir(parents=True, exist_ok=True)
            options["persist_directory"] = str(persist_directory)
        self.store = Chroma.from_documents(documents=documents, embedding=embeddings, **options)

    @classmethod
    def open_existing(cls, embeddings: object, persist_directory: Path) -> "DenseRetriever":
        """Open a previously built Chroma collection without embedding documents again."""
        instance = cls.__new__(cls)
        instance.store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(persist_directory),
        )
        return instance

    def search(self, query: str, ticker: str, k: int) -> list[Document]:
        return self.store.similarity_search(query, k=k, filter={"ticker": ticker.upper()})


def persistent_index_exists(persist_directory: Path) -> bool:
    """Chroma stores its persistent catalogue in this SQLite file."""
    return (persist_directory / "chroma.sqlite3").exists()


def rebuild_persistent_index(documents: list[Document], embeddings: object, persist_directory: Path) -> DenseRetriever:
    """Replace the saved dense index after RAG source documents change."""
    persist_directory.mkdir(parents=True, exist_ok=True)
    existing = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )
    existing.delete_collection()
    return DenseRetriever(documents, embeddings, persist_directory)
