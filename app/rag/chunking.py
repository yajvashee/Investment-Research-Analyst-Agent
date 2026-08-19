"""Structure-aware chunking for financial documents."""
from __future__ import annotations
import re
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def _is_heading(line: str) -> bool:
    """Recognise SEC-style ITEM headings as well as ordinary all-caps headings."""
    return bool(
        re.match(
            r"^(ITEM\s+\d+[A-Z]?(?:\s+[A-Z][A-Z &,-]*)?|[A-Z][A-Z &,-]{4,})$",
            line.strip(),
        )
    )

def split_into_sections(document: Document) -> list[Document]:
    section, lines, sections = "Introduction", [], []
    def save() -> None:
        text = "\n".join(lines).strip()
        if text: sections.append(Document(page_content=text, metadata={**document.metadata, "section": section}))
    for line in document.page_content.splitlines():
        if _is_heading(line):
            save(); lines = []; section = line.strip().title()
        else: lines.append(line)
    save()
    return sections

def chunk_documents(documents: list[Document], chunk_size: int = 800, chunk_overlap: int = 120) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                              separators=["\n\n", "\n", ". ", " ", ""])
    chunks: list[Document] = []
    for document in documents:
        for section in split_into_sections(document):
            for chunk in splitter.split_documents([section]):
                chunk.metadata = {**chunk.metadata, "chunk_id": str(len(chunks))}
                chunks.append(chunk)
    return chunks
