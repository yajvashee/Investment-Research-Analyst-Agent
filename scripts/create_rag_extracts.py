"""Create compact business-and-risk extracts from the downloaded annual reports."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.loaders import load_document


ROOT = Path("data/documents/rag")


def section(text: str, start_pattern: str, end_pattern: str, limit: int = 5_000) -> str:
    # SEC reports repeat headings in their table of contents. Work backwards so
    # the real report section is selected rather than the short contents entry.
    for start in reversed(list(re.finditer(start_pattern, text, re.IGNORECASE))):
        end = re.search(end_pattern, text[start.end():], re.IGNORECASE)
        content = text[start.start(): start.end() + end.start()] if end else text[start.start():]
        if len(content.strip()) >= 500:
            return content[:limit].strip()
    return ""


for report in sorted(ROOT.glob("*/**/*_2024_annual_report.html")):
    ticker = report.parent.name
    text = load_document(report)[0].page_content
    business = section(text, r"item\s+1[.\s:]+business", r"item\s+1a[.\s:]+risk")
    risks = section(text, r"item\s+1a[.\s:]+risk\s+factors", r"item\s+1b[.\s:]|item\s+2[.\s:]")
    extract = "\n\n".join(part for part in (business, risks) if part) or text[:10_000]
    source_metadata = json.loads(report.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    metadata = {
        "company_name": source_metadata.get("company_name", ticker),
        "ticker": ticker,
        "document_name": f"{ticker} Annual Report: Business and Risk Extract",
        "document_type": "annual_report_extract",
        "fiscal_year": source_metadata["fiscal_year"],
        "source": source_metadata["source"],
    }
    output = report.parent / f"{ticker}_investment_research_extract.txt"
    output.write_text(f"<!-- RAG_METADATA: {json.dumps(metadata)} -->\n{extract}\n", encoding="utf-8")
    print(f"Created {output}")
