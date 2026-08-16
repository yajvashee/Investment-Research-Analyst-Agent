"""Download a few recent official-company newsroom items into the RAG folder."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.rag.news import fetch_official_news, save_news_articles

ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "NVDA"
articles = fetch_official_news(ticker, limit=3)
paths = save_news_articles(articles, Path("data/documents/rag"))
print(f"Saved {len(paths)} official {ticker} newsroom articles.")
for path in paths:
    print(path)
