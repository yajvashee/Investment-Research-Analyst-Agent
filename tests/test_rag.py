from pathlib import Path

from langchain_core.documents import Document

from app.rag.bm25 import BM25Retriever
from app.rag.chunking import chunk_documents
from app.rag.loaders import load_document
from app.rag.news import save_news_articles
from app.rag.reranking import AzureRelevanceReranker
from app.rag.retriever import FinancialDocumentRetriever, reciprocal_rank_fusion
from app.rag.vectorstore import DenseRetriever


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[float(text.lower().count("risk")), float(text.lower().count("cloud"))] for text in texts]
    def embed_query(self, text):
        return [float(text.lower().count("risk")), float(text.lower().count("cloud"))]


def documents():
    return chunk_documents([
        Document(page_content="RISK FACTORS\nCloud security risk is important.", metadata={"ticker": "MSFT", "company_name": "Microsoft", "document_name": "MSFT report", "document_type": "annual_report", "fiscal_year": 2024, "page_number": 1, "source": "test"}),
        Document(page_content="RISK FACTORS\nSupply constraints affect chips.", metadata={"ticker": "NVDA", "company_name": "NVIDIA", "document_name": "NVDA report", "document_type": "annual_report", "fiscal_year": 2024, "page_number": 1, "source": "test"}),
    ])


def test_loading_and_metadata(tmp_path: Path):
    path = tmp_path / "MSFT" / "MSFT_2024_annual_report.txt"; path.parent.mkdir(); path.write_text("Report text")
    document = load_document(path)[0]
    assert document.metadata["ticker"] == "MSFT" and document.metadata["fiscal_year"] == 2024


def test_news_metadata_preserves_original_url(tmp_path: Path):
    path = save_news_articles([{"company_name": "NVIDIA", "ticker": "NVDA", "document_name": "News", "document_type": "official_news", "fiscal_year": 2026, "source": "https://example.com/news", "content": "News text"}], tmp_path)[0]
    document = load_document(path)[0]
    assert document.metadata["ticker"] == "NVDA" and document.metadata["source"] == "https://example.com/news"


def test_structure_aware_chunking_preserves_metadata():
    chunks = documents()
    assert chunks[0].metadata["section"] == "Risk Factors" and chunks[0].metadata["chunk_id"] == "0"


def test_dense_and_bm25_retrieval_filter_by_ticker():
    chunks = documents()
    assert DenseRetriever(chunks, FakeEmbeddings()).search("cloud risk", "MSFT", 2)[0].metadata["ticker"] == "MSFT"
    assert BM25Retriever(chunks).search("cloud risk", "MSFT", 2)[0].metadata["ticker"] == "MSFT"


def test_rrf_and_reranking():
    chunks = documents()
    fused = reciprocal_rank_fusion([[chunks[0], chunks[1]], [chunks[0]]])
    assert fused[0].metadata["chunk_id"] == chunks[0].metadata["chunk_id"]
    reranked = AzureRelevanceReranker(lambda _query, doc: 1.0 if doc.metadata["ticker"] == "NVDA" else 0.0).rerank("risk", chunks, 2)
    assert reranked[0].metadata["ticker"] == "NVDA"


def test_final_retrieval_output_and_ticker_filtering():
    chunks = documents()
    retriever = FinancialDocumentRetriever(chunks, FakeEmbeddings(), AzureRelevanceReranker(lambda _q, _d: 1.0))
    results = retriever.search("MSFT", "cloud security risk")
    assert results and all(result.metadata["ticker"] == "MSFT" for result in results)
    assert retriever.search("BAD", "risk") == []
