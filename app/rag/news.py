"""Import a small number of official newsroom RSS articles into the RAG corpus."""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx


OFFICIAL_NEWS_FEEDS = {
    "MSFT": ("Microsoft", "https://news.microsoft.com/feed/"),
    "AAPL": ("Apple", "https://www.apple.com/newsroom/rss-feed.rss"),
    "KO": ("Coca-Cola", "https://investors.coca-colacompany.com/news-events/press-releases/rss"),
    "GOOGL": ("Alphabet", "https://blog.google/rss/"),
    "AMZN": ("Amazon", "https://www.aboutamazon.com/news/rss"),
    "META": ("Meta", "https://about.fb.com/news/category/utility/recent-news/feed/"),
    "NVDA": ("NVIDIA", "https://nvidianews.nvidia.com/rss.xml"),
    "TSLA": ("Tesla", "https://ir.tesla.com/press/rss"),
    "AMD": ("AMD", "https://ir.amd.com/news-events/press-releases/rss"),
}


def _text(element: ET.Element | None, tag: str) -> str:
    if element is None:
        return ""
    for child in element:
        if child.tag.rsplit("}", 1)[-1] == tag:
            return (child.text or "").strip()
    return ""


def _clean_html(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def fetch_official_news(ticker: str, limit: int = 3, client: httpx.Client | None = None) -> list[dict[str, str | int]]:
    """Fetch recent items from a configured official company RSS feed."""
    ticker = ticker.upper()
    if ticker not in OFFICIAL_NEWS_FEEDS:
        raise ValueError(f"No official news feed is configured for {ticker}.")
    company_name, feed_url = OFFICIAL_NEWS_FEEDS[ticker]
    owns_client = client is None
    client = client or httpx.Client(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "InvestmentResearchAnalyst/0.1 (educational project)"},
    )
    try:
        response = client.get(feed_url)
        response.raise_for_status()
    finally:
        if owns_client:
            client.close()
    # A few otherwise-valid publisher feeds contain an unescaped ampersand.
    xml_content = re.sub(rb"&(?!#?[A-Za-z0-9]+;)", b"&amp;", response.content)
    root = ET.fromstring(xml_content)
    articles = []
    items = root.findall("./channel/item") or root.findall("{*}entry")
    for item in items[:limit]:
        published = _text(item, "pubDate") or _text(item, "published") or _text(item, "updated")
        try:
            year = parsedate_to_datetime(published).year
        except (TypeError, ValueError):
            year = datetime.now().year
        link = _text(item, "link")
        if not link:
            link_element = next((child for child in item if child.tag.rsplit("}", 1)[-1] == "link"), None)
            link = link_element.get("href", "") if link_element is not None else ""
        articles.append({
            "company_name": company_name, "ticker": ticker,
            "document_name": _text(item, "title"), "document_type": "official_news",
            "fiscal_year": year, "published_date": published,
            "source": link,
            "content": _clean_html(_text(item, "description") or _text(item, "summary") or _text(item, "content")),
        })
    return articles


def save_news_articles(articles: list[dict[str, str | int]], output_directory: Path) -> list[Path]:
    """Save RSS items as Markdown with a metadata header the RAG loader understands."""
    saved: list[Path] = []
    for number, article in enumerate(articles, start=1):
        ticker = str(article["ticker"])
        directory = output_directory / ticker / "news"
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{ticker}_{article['fiscal_year']}_official_news_{number}.md"
        path = directory / filename
        metadata = {key: value for key, value in article.items() if key != "content"}
        path.write_text(f"<!-- RAG_METADATA: {json.dumps(metadata)} -->\n{article['content']}\n", encoding="utf-8")
        saved.append(path)
    return saved
