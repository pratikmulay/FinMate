"""Refresh market data cache from MFAPI.in and yfinance.

Run manually or on a schedule. Never called from the request path.

Usage:
    python -m app.services.refresh_market_data
"""
import json
import sys
from pathlib import Path

# __file__ is app/services/refresh_market_data.py
# .parent is app/services/
# .parent.parent is app/
APP_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = APP_DIR.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.market_data import (
    MarketDataError,
    compute_metrics,
    fetch_mfapi_series,
    fetch_yfinance_series,
    save_cache,
)

APL_PATH = APP_DIR / "data" / "apl.json"


def main() -> None:
    if not APL_PATH.exists():
        print(f"[error] Cannot find asset list at: {APL_PATH}")
        return

    assets = json.loads(APL_PATH.read_text(encoding="utf-8"))
    metrics_by_asset: dict[str, dict] = {}

    for asset in assets:
        source = asset.get("source")
        if not source:
            continue  # stays on static apl.json values

        asset_id = asset["id"]
        try:
            if source["type"] == "mfapi":
                series = fetch_mfapi_series(str(source["scheme_code"]))
            elif source["type"] == "yfinance":
                series = fetch_yfinance_series(source["ticker"])
            else:
                print(f"[skip] {asset_id}: unknown source type {source['type']}")
                continue

            metrics_by_asset[asset_id] = compute_metrics(series)
            print(f"[ok]   {asset_id}: {metrics_by_asset[asset_id]}")
        except (MarketDataError, KeyError) as e:
            print(f"[fail] {asset_id}: {e}")

    save_cache(metrics_by_asset)
    print(f"\nSaved metrics for {len(metrics_by_asset)}/{len(assets)} assets.")


if __name__ == "__main__":
    main()