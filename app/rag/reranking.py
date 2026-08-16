"""Azure chat-model relevance reranking reused from the previous project."""
from __future__ import annotations
import os
import re
from collections.abc import Callable
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import AzureChatOpenAI

class AzureRelevanceReranker:
    def __init__(self, scorer: Callable[[str, Document], float] | None = None) -> None:
        self.scorer = scorer
        self.llm = None
        if scorer is None:
            load_dotenv()
            self.llm = AzureChatOpenAI(azure_endpoint=os.environ["AZURE_ENDPOINT"], api_key=os.environ["AZURE_API_KEY"], api_version=os.environ["CHAT_API_VERSION"], azure_deployment=os.environ["CHAT_DEPLOYMENT"], temperature=0)
    def score(self, query: str, document: Document) -> float:
        if self.scorer:
            return self.scorer(query, document)
        response = str(self.llm.invoke(f"Give a relevance score from 0 to 1 only.\nQuestion: {query}\nPassage: {document.page_content}").content)
        match = re.search(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", response)
        return float(match.group()) if match else 0.0
    def rerank(self, query: str, documents: list[Document], k: int) -> list[Document]:
        scored = sorted(((d, self.score(query, d)) for d in documents), key=lambda item: item[1], reverse=True)[:k]
        return [Document(page_content=d.page_content, metadata={**d.metadata, "rerank_score": score}) for d, score in scored]
