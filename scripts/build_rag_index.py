"""Build the configured Chroma or OpenSearch index after source changes."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.retriever import build_rag_index


chunk_count = build_rag_index()
backend = os.getenv("VECTOR_STORE", "chroma").strip().lower()
destination = "Amazon OpenSearch" if backend == "opensearch" else "data/chroma"
print(f"Saved RAG index with {chunk_count} chunks in {destination}.")
