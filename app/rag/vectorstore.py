"""Dense vector search backed by local Chroma or Amazon OpenSearch."""
from __future__ import annotations
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import boto3
from langchain_chroma import Chroma
from langchain_core.documents import Document
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection


COLLECTION_NAME = "investment_research"
DEFAULT_OPENSEARCH_INDEX = "investment-research"


class DenseRetriever:
    def __init__(self, documents: list[Document], embeddings: object, persist_directory: Path | None = None) -> None:
        options = {"collection_name": COLLECTION_NAME}
        if persist_directory is not None:
            persist_directory.mkdir(parents=True, exist_ok=True)
            options["persist_directory"] = str(persist_directory)
        self.store = Chroma.from_documents(documents=documents, embedding=embeddings, **options)

    @classmethod
    def open_existing(cls, embeddings: object, persist_directory: Path) -> "DenseRetriever":
        """Open a previously built Chroma collection without embedding documents again."""
        instance = cls.__new__(cls)
        instance.store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(persist_directory),
        )
        return instance

    def search(self, query: str, ticker: str, k: int) -> list[Document]:
        return self.store.similarity_search(query, k=k, filter={"ticker": ticker.upper()})


class OpenSearchDenseRetriever:
    """Amazon OpenSearch k-NN adapter with the same search interface as Chroma."""

    def __init__(self, client: OpenSearch, embeddings: object, index_name: str) -> None:
        self.client = client
        self.embeddings = embeddings
        self.index_name = index_name

    @classmethod
    def open_existing(
        cls,
        embeddings: object,
        endpoint: str | None = None,
        index_name: str | None = None,
        client: OpenSearch | None = None,
    ) -> "OpenSearchDenseRetriever":
        selected_index = index_name or os.getenv("OPENSEARCH_INDEX", DEFAULT_OPENSEARCH_INDEX)
        selected_client = client or create_opensearch_client(endpoint)
        if not selected_client.indices.exists(index=selected_index):
            raise RuntimeError(
                f"OpenSearch index '{selected_index}' does not exist. "
                "Run: uv run python scripts/build_rag_index.py"
            )
        return cls(selected_client, embeddings, selected_index)

    def search(self, query: str, ticker: str, k: int) -> list[Document]:
        vector = self.embeddings.embed_query(query)
        response = self.client.search(
            index=self.index_name,
            body={
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": vector,
                            "k": k,
                            "filter": {"term": {"ticker": ticker.upper()}},
                        }
                    }
                },
            },
        )
        return [
            Document(
                page_content=hit["_source"]["text"],
                metadata=hit["_source"].get("metadata", {}),
            )
            for hit in response.get("hits", {}).get("hits", [])
        ]


def create_opensearch_client(endpoint: str | None = None) -> OpenSearch:
    """Create an IAM-authenticated client for a managed OpenSearch domain."""
    raw_endpoint = (endpoint or os.getenv("OPENSEARCH_ENDPOINT", "")).strip()
    if not raw_endpoint:
        raise RuntimeError("OPENSEARCH_ENDPOINT is required when VECTOR_STORE=opensearch.")
    parsed = urlparse(raw_endpoint if "://" in raw_endpoint else f"https://{raw_endpoint}")
    if not parsed.hostname:
        raise RuntimeError("OPENSEARCH_ENDPOINT must be a valid domain endpoint.")
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if not region:
        raise RuntimeError("AWS_REGION is required when VECTOR_STORE=opensearch.")
    credentials = boto3.Session().get_credentials()
    if credentials is None:
        raise RuntimeError("AWS credentials are required to access OpenSearch.")
    service = os.getenv("OPENSEARCH_SERVICE", "es")
    timeout_seconds = float(os.getenv("OPENSEARCH_TIMEOUT_SECONDS", "60"))
    return OpenSearch(
        hosts=[{"host": parsed.hostname, "port": parsed.port or 443}],
        http_auth=AWSV4SignerAuth(credentials, region, service),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        http_compress=True,
        pool_maxsize=20,
        timeout=timeout_seconds,
        max_retries=6,
        retry_on_timeout=True,
        retry_on_status=(429, 502, 503, 504),
    )


def rebuild_opensearch_index(
    documents: list[Document],
    embeddings: object,
    endpoint: str | None = None,
    index_name: str | None = None,
    client: OpenSearch | None = None,
) -> OpenSearchDenseRetriever:
    """Replace the configured OpenSearch k-NN index with freshly embedded chunks."""
    if not documents:
        raise RuntimeError("Cannot build an OpenSearch index without documents.")
    selected_index = index_name or os.getenv("OPENSEARCH_INDEX", DEFAULT_OPENSEARCH_INDEX)
    selected_client = client or create_opensearch_client(endpoint)
    vectors = embeddings.embed_documents([document.page_content for document in documents])
    if not vectors or not vectors[0]:
        raise RuntimeError("The embedding model returned no vectors.")
    if selected_client.indices.exists(index=selected_index):
        selected_client.indices.delete(index=selected_index)
    selected_client.indices.create(
        index=selected_index,
        body={
            "settings": {"index.knn": True},
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "ticker": {"type": "keyword"},
                    "metadata": {"type": "object", "enabled": False},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": len(vectors[0]),
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        },
    )
    operations: list[dict] = []
    for document, vector in zip(documents, vectors, strict=True):
        operations.extend(
            [
                {"index": {"_index": selected_index, "_id": document.metadata["chunk_id"]}},
                {
                    "text": document.page_content,
                    "ticker": str(document.metadata.get("ticker", "")).upper(),
                    "metadata": document.metadata,
                    "embedding": vector,
                },
            ]
        )
    failures = []
    batch_documents = int(os.getenv("OPENSEARCH_BULK_DOCUMENTS", "20"))
    operation_batch_size = batch_documents * 2  # One action and one source per document.
    for start in range(0, len(operations), operation_batch_size):
        response = selected_client.bulk(body=operations[start:start + operation_batch_size], refresh=False)
        if response.get("errors"):
            failures.extend(item for item in response.get("items", []) if item.get("index", {}).get("error"))
        if start + operation_batch_size < len(operations):
            time.sleep(0.5)
    if failures:
        raise RuntimeError(f"OpenSearch rejected {len(failures)} document chunks.")
    selected_client.indices.refresh(index=selected_index)
    return OpenSearchDenseRetriever(selected_client, embeddings, selected_index)


def persistent_index_exists(persist_directory: Path) -> bool:
    """Chroma stores its persistent catalogue in this SQLite file."""
    return (persist_directory / "chroma.sqlite3").exists()


def rebuild_persistent_index(documents: list[Document], embeddings: object, persist_directory: Path) -> DenseRetriever:
    """Replace the saved dense index after RAG source documents change."""
    persist_directory.mkdir(parents=True, exist_ok=True)
    existing = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )
    existing.delete_collection()
    return DenseRetriever(documents, embeddings, persist_directory)
