"""Download three recent items from every configured official company news feed."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.news import OFFICIAL_NEWS_FEEDS, fetch_official_news, save_news_articles


failures: list[str] = []
for ticker in OFFICIAL_NEWS_FEEDS:
    try:
        articles = fetch_official_news(ticker, limit=3)
        paths = save_news_articles(articles, Path("data/documents/rag"))
        print(f"Saved {len(paths)} official {ticker} newsroom articles.")
    except Exception as error:
        failures.append(ticker)
        print(f"Could not ingest {ticker}: {error}")

if failures:
    raise SystemExit(f"News ingestion incomplete. Failed tickers: {', '.join(failures)}")
