"""Sparse BM25 retrieval for exact financial terms."""
from __future__ import annotations
import re
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

class BM25Retriever:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        self.index = BM25Okapi([_tokens(d.page_content) for d in documents])
    def search(self, query: str, ticker: str, k: int) -> list[Document]:
        scores = self.index.get_scores(_tokens(query))
        ranked = sorted(((d, score) for d, score in zip(self.documents, scores) if d.metadata["ticker"] == ticker.upper()), key=lambda item: item[1], reverse=True)
        return [d for d, _ in ranked[:k]]
