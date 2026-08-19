"""Ten fast unit tests for small, deterministic project components.

These tests use no database, Docker container, Azure model, or finance API.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from langchain_core.documents import Document

from app.agent.tools import _citation, _json_value, _normalise_tickers
from app.rag.bm25 import BM25Retriever
from app.rag.chunking import _is_heading, chunk_documents, split_into_sections
from app.rag.loaders import _HtmlTextExtractor, metadata_from_path


def test_item_heading_is_recognised() -> None:
    assert _is_heading("ITEM 1A RISK FACTORS")


def test_normal_sentence_is_not_a_heading() -> None:
    assert not _is_heading("Revenue increased during the year.")


def test_section_splitting_preserves_document_metadata() -> None:
    document = Document(
        page_content="Opening text\nITEM 1A RISK FACTORS\nRisk text",
        metadata={"ticker": "MSFT", "source": "test"},
    )

    sections = split_into_sections(document)

    assert len(sections) == 2
    assert sections[1].metadata["ticker"] == "MSFT"
    assert sections[1].metadata["section"] == "Item 1A Risk Factors"


def test_chunking_adds_a_unique_chunk_id() -> None:
    chunks = chunk_documents(
        [Document(page_content="ITEM 1 BUSINESS\n" + "Microsoft cloud. " * 20, metadata={"ticker": "MSFT"})],
        chunk_size=80,
        chunk_overlap=10,
    )

    assert chunks
    assert [chunk.metadata["chunk_id"] for chunk in chunks] == [str(index) for index in range(len(chunks))]


def test_bm25_returns_only_the_requested_ticker() -> None:
    documents = [
        Document(page_content="Microsoft cloud security risks", metadata={"ticker": "MSFT"}),
        Document(page_content="Apple product design risks", metadata={"ticker": "AAPL"}),
    ]

    results = BM25Retriever(documents).search("cloud risks", "MSFT", k=5)

    assert len(results) == 1
    assert results[0].metadata["ticker"] == "MSFT"


def test_metadata_from_path_identifies_company_year_and_document_type() -> None:
    metadata = metadata_from_path(Path("data/documents/rag/MSFT/MSFT_2024_annual_risk_report.txt"))

    assert metadata["company_name"] == "Microsoft"
    assert metadata["ticker"] == "MSFT"
    assert metadata["fiscal_year"] == 2024
    assert metadata["document_type"] == "risk_disclosure"


def test_html_text_extractor_ignores_script_content() -> None:
    parser = _HtmlTextExtractor()
    parser.feed("<p>Useful report text</p><script>secret()</script>")

    assert parser.text() == "Useful report text"


def test_ticker_normalisation_accepts_a_single_lowercase_ticker() -> None:
    assert _normalise_tickers("msft") == ["MSFT"]


def test_json_value_converts_decimal_and_date() -> None:
    value = _json_value({"price": Decimal("12.50"), "as_of": date(2024, 1, 1)})

    assert value == {"price": "12.50", "as_of": "2024-01-01"}


def test_citation_retains_known_metadata_fields() -> None:
    citation = _citation(Document(page_content="text", metadata={"ticker": "MSFT", "source": "annual report"}))

    assert citation["ticker"] == "MSFT"
    assert citation["source"] == "annual report"
    assert citation["page_number"] is None
