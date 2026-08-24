# Final Project Checklist

| Area | Status | Evidence / note |
|---|---|---|
| PostgreSQL historical database | Verified | 36 records for 9 companies, 2021-2024; Docker health check passes. |
| Finance API | Implemented and tested | Mocked tests pass; live requests can be rate-limited by the free Alpha Vantage tier. |
| RAG document loading | Verified | Active corpus contains selected annual-report/risk extracts and official news for all 9 companies. |
| Dense retrieval | Verified | Chroma persistent index and Azure embeddings are used. |
| Amazon OpenSearch mode | Unit verified; live deployment pending | Optional IAM-authenticated k-NN backend preserves ticker filtering; a VPC domain has not yet been connected or indexed. |
| BM25 | Verified | Sparse keyword retrieval is part of the hybrid retriever. |
| Reciprocal Rank Fusion | Verified | Dense and BM25 results are combined before reranking. |
| Azure reranking | Verified | GPT-4.1-mini scores candidate chunks. |
| Agent tools | Verified | PostgreSQL, market-data, and RAG wrappers have automated tests. |
| LangGraph agent | Verified | 10/10 routing evaluation cases pass. |
| FastAPI | Verified | `/health` and `/research` are tested. |
| Streamlit | Verified | Browser UI calls FastAPI rather than LangGraph directly. |
| Docker Compose | Verified | Frontend, backend, and PostgreSQL containers run together. |
| Automated tests | Verified | `uv run pytest`: 50 passed in a clean verification environment. |
| Evaluation | Verified | `uv run python scripts/evaluate_agent.py`: 10/10 routing cases passed. |
| AWS deployment | Blocked, documented | AWS CLI is installed but no profile, credentials, or region is configured on this machine. See `docs/aws-deployment.md`. |
| Documentation | Verified | README, architecture diagram, deployment guide, and checklist are included. |
