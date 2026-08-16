"""Build the saved local Chroma index after RAG source documents change."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.retriever import build_rag_index


chunk_count = build_rag_index()
print(f"Saved RAG index with {chunk_count} chunks in data/chroma.")
