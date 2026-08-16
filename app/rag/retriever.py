"""Hybrid financial-document retrieval: dense + BM25 + RRF + Azure reranking."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from langchain_core.documents import Document
from app.rag.bm25 import BM25Retriever
from app.rag.chunking import chunk_documents
from app.rag.embeddings import get_embeddings
from app.rag.loaders import load_company_documents
from app.rag.reranking import AzureRelevanceReranker
from app.rag.vectorstore import DenseRetriever, persistent_index_exists, rebuild_persistent_index


DOCUMENTS_DIRECTORY = Path("data/documents/rag")
INDEX_DIRECTORY = Path("data/chroma")

def reciprocal_rank_fusion(result_sets: list[list[Document]], rrf_k: int = 60) -> list[Document]:
    scores: dict[str, float] = {}; documents: dict[str, Document] = {}
    for result_set in result_sets:
        for rank, document in enumerate(result_set, 1):
            key = document.metadata["chunk_id"]; documents[key] = document
            scores[key] = scores.get(key, 0.0) + 1 / (rrf_k + rank)
    return [documents[key] for key in sorted(scores, key=scores.get, reverse=True)]

class FinancialDocumentRetriever:
    def __init__(self, chunks: list[Document], embeddings: object, reranker: AzureRelevanceReranker, dense: DenseRetriever | None = None) -> None:
        self.chunks = chunks; self.dense = dense or DenseRetriever(chunks, embeddings)
        self.sparse = BM25Retriever(chunks); self.reranker = reranker
    def search(self, ticker: str, query: str, k: int = 5) -> list[Document]:
        ticker = ticker.upper().strip()
        if not any(chunk.metadata["ticker"] == ticker for chunk in self.chunks): return []
        candidates = reciprocal_rank_fusion([self.dense.search(query, ticker, k * 2), self.sparse.search(query, ticker, k * 2)])
        return self.reranker.rerank(query, candidates, k)

@lru_cache(maxsize=1)
def _default_retriever() -> FinancialDocumentRetriever:
    chunks = chunk_documents(load_company_documents(DOCUMENTS_DIRECTORY))
    if not chunks: raise RuntimeError("No RAG documents found in data/documents/rag.")
    if not persistent_index_exists(INDEX_DIRECTORY):
        raise RuntimeError("RAG index has not been built. Run: uv run python scripts/build_rag_index.py")
    embeddings = get_embeddings()
    return FinancialDocumentRetriever(chunks, embeddings, AzureRelevanceReranker(), DenseRetriever.open_existing(embeddings, INDEX_DIRECTORY))


def build_rag_index() -> int:
    """Chunk the local corpus and save its dense index for fast later searches."""
    chunks = chunk_documents(load_company_documents(DOCUMENTS_DIRECTORY))
    if not chunks:
        raise RuntimeError("No RAG documents found in data/documents/rag.")
    rebuild_persistent_index(chunks, get_embeddings(), INDEX_DIRECTORY)
    _default_retriever.cache_clear()
    return len(chunks)

def search_company_documents(ticker: str, query: str, k: int = 5) -> list[Document]:
    return _default_retriever().search(ticker, query, k)
