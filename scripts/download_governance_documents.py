"""Download the latest official proxy statement for each project company from SEC EDGAR."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv


COMPANIES = {
    "MSFT": "0000789019", "AAPL": "0000320193", "KO": "0000021344",
    "GOOGL": "0001652044", "AMZN": "0001018724", "META": "0001326801",
    "NVDA": "0001045810", "TSLA": "0001318605", "AMD": "0000002488",
}

load_dotenv()
user_agent = os.getenv("SEC_USER_AGENT", "").strip()
if not user_agent:
    raise RuntimeError("SEC_USER_AGENT is missing. Add a project name and contact email to .env.")

root = Path("data/documents/rag")
failures: list[str] = []
headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}

with httpx.Client(timeout=90, headers=headers) as client:
    for ticker, cik in COMPANIES.items():
        output = root / ticker / f"{ticker}_corporate_governance_proxy.html"
        sidecar = output.with_suffix(".metadata.json")
        if output.exists() and sidecar.exists():
            print(f"Already downloaded {ticker}")
            continue
        try:
            submissions = client.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
            submissions.raise_for_status()
            recent = submissions.json()["filings"]["recent"]
            index = next(i for i, form in enumerate(recent["form"]) if form == "DEF 14A")
            accession = recent["accessionNumber"][index]
            primary_document = recent["primaryDocument"][index]
            filing_date = recent["filingDate"][index]
            archive_cik = str(int(cik))
            source = f"https://www.sec.gov/Archives/edgar/data/{archive_cik}/{accession.replace('-', '')}/{primary_document}"
            response = client.get(source)
            response.raise_for_status()

            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(response.text, encoding="utf-8")
            sidecar.write_text(json.dumps({
                "document_name": f"{ticker} Proxy Statement (DEF 14A)",
                "document_type": "corporate_governance",
                "fiscal_year": int(filing_date[:4]),
                "filing_date": filing_date,
                "source": source,
            }, indent=2), encoding="utf-8")
            print(f"Downloaded {ticker}: {filing_date}, {len(response.content):,} bytes")
        except (httpx.HTTPError, KeyError, StopIteration, ValueError) as error:
            failures.append(ticker)
            print(f"Could not download {ticker}: {error}")
        time.sleep(0.25)

if failures:
    raise SystemExit(f"Download incomplete. Failed tickers: {', '.join(failures)}")
