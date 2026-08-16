"""Azure OpenAI embedding client reused from the previous RAG project."""
from __future__ import annotations
import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

def get_embeddings() -> AzureOpenAIEmbeddings:
    load_dotenv()
    required = ["AZURE_ENDPOINT", "AZURE_API_KEY", "EMBED_API_VERSION", "EMBED_DEPLOYMENT"]
    missing = [name for name in required if not os.getenv(name)]
    if missing: raise RuntimeError("Missing Azure RAG settings: " + ", ".join(missing))
    return AzureOpenAIEmbeddings(azure_endpoint=os.environ["AZURE_ENDPOINT"], api_key=os.environ["AZURE_API_KEY"],
                                 api_version=os.environ["EMBED_API_VERSION"], azure_deployment=os.environ["EMBED_DEPLOYMENT"])
