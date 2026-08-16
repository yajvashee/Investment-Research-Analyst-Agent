"""Download one official 2024 annual 10-K filing for each project company."""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

FILINGS = {
 "MSFT": "https://www.sec.gov/Archives/edgar/data/789019/000095017024087843/msft-20240630.htm",
 "AAPL": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
 "KO": "https://www.sec.gov/Archives/edgar/data/21344/000002134425000011/ko-20241231.htm",
 "GOOGL": "https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm",
 "AMZN": "https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/amzn-20241231.htm",
 "META": "https://www.sec.gov/Archives/edgar/data/1326801/000132680125000017/meta-20241231.htm",
 "NVDA": "https://www.sec.gov/Archives/edgar/data/1045810/000104581025000023/nvda-20250126.htm",
 "TSLA": "https://www.sec.gov/Archives/edgar/data/1318605/000162828025003063/tsla-20241231.htm",
 "AMD": "https://ir.amd.com/financial-information/sec-filings/content/0000002488-25-000012/amd-20241228.htm",
}
load_dotenv()
user_agent = os.getenv("SEC_USER_AGENT", "").strip()
if not user_agent:
    raise RuntimeError("SEC_USER_AGENT is missing. Add a project name and contact email to .env.")

root = Path("data/documents/rag")
failures: list[str] = []
with httpx.Client(timeout=90, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}) as client:
    for ticker, url in FILINGS.items():
        try:
            folder = root / ticker
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{ticker}_2024_annual_report.html"
            if path.exists() and path.with_suffix(".metadata.json").exists():
                print(f"Already downloaded {ticker}")
                continue
            response = client.get(url)
            response.raise_for_status()
            path.write_text(response.text, encoding="utf-8")
            path.with_suffix(".metadata.json").write_text(
                json.dumps(
                    {
                        "document_name": f"{ticker} 2024 Annual Report (Form 10-K)",
                        "document_type": "annual_report",
                        "fiscal_year": 2024,
                        "source": url,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"Downloaded {ticker}: {len(response.content):,} bytes")
        except httpx.HTTPError as error:
            failures.append(ticker)
            print(f"Could not download {ticker}: {error}")

if failures:
    raise SystemExit(f"Download incomplete. Failed tickers: {', '.join(failures)}")
