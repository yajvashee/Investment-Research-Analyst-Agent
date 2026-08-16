"""Print normalized market data for one ticker."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.market_data.client import MarketDataError
from app.market_data.service import get_market_data


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "MSFT"
    try:
        print(json.dumps(asdict(get_market_data(ticker)), indent=2, default=str))
    except MarketDataError as error:
        print(f"Market-data request failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
