"""Manually query the Phase 4 financial-document RAG pipeline."""
from __future__ import annotations
import sys
from pathlib import Path

# A script is executed from its own folder, so add the project root for app imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag import search_company_documents

if len(sys.argv) < 3:
    raise SystemExit('Usage: uv run python scripts/test_rag.py MSFT "Your question"')

results = search_company_documents(sys.argv[1], " ".join(sys.argv[2:]))
if not results:
    print(f"No indexed documents found for {sys.argv[1].upper()}.")
for number, result in enumerate(results, 1):
    metadata = result.metadata
    print(f"\n[{number}] {metadata['company_name']} | {metadata['document_name']}")
    print(f"Source: {metadata['source']} | page {metadata['page_number']} | {metadata['section']}")
    print(result.page_content)
