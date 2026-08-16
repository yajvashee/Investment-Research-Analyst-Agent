"""Load company documents and attach consistent citation metadata."""
from __future__ import annotations
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from langchain_core.documents import Document
from pypdf import PdfReader

COMPANY_NAMES = {
    "MSFT": "Microsoft", "AAPL": "Apple", "KO": "Coca-Cola",
    "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta",
    "NVDA": "NVIDIA", "TSLA": "Tesla", "AMD": "AMD",
}


class _HtmlTextExtractor(HTMLParser):
    """Small dependency-free HTML-to-text extractor for SEC filing pages."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skip_depth += 1
        elif tag in {"p", "div", "br", "tr", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", "".join(self.parts))).strip()

def metadata_from_path(path: Path) -> dict[str, str | int]:
    ticker = next((parent.name.upper() for parent in (path.parent, *path.parents)
                   if re.fullmatch(r"[A-Za-z]{2,5}", parent.name)), path.parent.name.upper())
    year = re.search(r"(20\d{2})", path.stem)
    lower = path.stem.lower()
    return {"company_name": COMPANY_NAMES.get(ticker, ticker), "ticker": ticker,
            "document_name": path.stem.replace("_", " ").title(),
            "document_type": "risk_disclosure" if "risk" in lower else "annual_report" if "annual" in lower else "company_document",
            "fiscal_year": int(year.group(1)) if year else 0, "source": str(path)}

def load_document(path: Path) -> list[Document]:
    metadata = metadata_from_path(path)
    sidecar = path.with_suffix(".metadata.json")
    if sidecar.exists():
        metadata.update(json.loads(sidecar.read_text(encoding="utf-8")))
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        documents = []
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip(): documents.append(Document(page_content=text, metadata={**metadata, "page_number": number}))
        return documents
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".html":
        parser = _HtmlTextExtractor()
        parser.feed(text)
        text = parser.text()
    if text.startswith("<!-- RAG_METADATA:"):
        header, text = text.split("-->\n", maxsplit=1)
        metadata.update(json.loads(header.removeprefix("<!-- RAG_METADATA:").strip()))
    return [Document(page_content=text, metadata={**metadata, "page_number": 1})]

def load_company_documents(documents_directory: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(documents_directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf", ".html"}:
            documents.extend(load_document(path))
    return documents
