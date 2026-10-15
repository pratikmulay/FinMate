"""Market data fetching and metrics computation.

Two sources: MFAPI.in (mutual funds) and yfinance (ETFs/stocks/crypto).
Both normalize into a (date, price) series, then one shared function
computes metrics for either. Only scripts/refresh_market_data.py calls
the fetch_* functions — request-time code only reads the cache.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
import yfinance as yf

APP_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = APP_DIR / "data" / "cache" / "metrics.json"
CACHE_MAX_AGE_HOURS = 24 * 7  # refresh weekly


class MarketDataError(Exception):
    """Raised when a source can't be fetched or parsed."""


def fetch_mfapi_series(scheme_code: str) -> list[tuple[date, float]]:
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    raw = resp.json().get("data", [])
    if not raw:
        raise MarketDataError(f"No NAV data for scheme {scheme_code}")
    series = [
        (datetime.strptime(row["date"], "%d-%m-%Y").date(), float(row["nav"]))
        for row in raw
    ]
    series.sort(key=lambda x: x[0])  # MFAPI returns newest-first
    return series


def fetch_yfinance_series(ticker: str) -> list[tuple[date, float]]:
    hist = yf.Ticker(ticker).history(period="3y", interval="1d")
    # Drop rows where Close is missing/NaN
    hist = hist.dropna(subset=["Close"])
    if hist.empty:
        raise MarketDataError(f"No price data for ticker {ticker}")
    series = [(idx.date(), float(row["Close"])) for idx, row in hist.iterrows()]
    series.sort(key=lambda x: x[0])
    return series


def _price_on_or_before(series: list[tuple[date, float]], target: date) -> Optional[float]:
    candidates = [p for d, p in series if d <= target]
    return candidates[-1] if candidates else None

def _clean_float(val: Optional[float]) -> Optional[float]:
    if val is None or math.isnan(val):
        return None
    return round(val, 2)

def compute_metrics(series: list[tuple[date, float]]) -> dict:
    # Filter out invalid, zero, or negative prices
    series = [(d, p) for d, p in series if p is not None and not math.isnan(p) and p > 0]

    if len(series) < 30:
        raise MarketDataError("Series too short to compute reliable metrics")

    latest_date, latest_price = series[-1]
    one_y_price = _price_on_or_before(series, latest_date - timedelta(days=365))
    three_y_price = _price_on_or_before(series, latest_date - timedelta(days=365 * 3))

    one_y_return = (
        (latest_price / one_y_price - 1) * 100
        if one_y_price and one_y_price > 0
        else None
    )
    three_y_cagr = (
        ((latest_price / three_y_price) ** (1 / 3) - 1) * 100
        if three_y_price and three_y_price > 0
        else None
    )

    daily_returns = [
        series[i][1] / series[i - 1][1] - 1
        for i in range(1, len(series))
        if series[i - 1][1] > 0
    ]

    if daily_returns:
        mean = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean) ** 2 for r in daily_returns) / len(daily_returns)
        volatility = math.sqrt(variance) * math.sqrt(252) * 100
    else:
        volatility = None

    peak = series[0][1]
    max_dd = 0.0
    for _, price in series:
        if price > peak:
            peak = price
        if peak > 0:
            max_dd = min(max_dd, (price / peak - 1) * 100)

    return {
        "one_year_return_pct": _clean_float(one_y_return),
        "three_year_cagr_pct": _clean_float(three_y_cagr),
        "annualized_volatility_pct": _clean_float(volatility),
        "max_drawdown_pct": _clean_float(max_dd),
    }


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text())


def save_cache(metrics_by_asset: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "assets": metrics_by_asset,
    }
    CACHE_PATH.write_text(json.dumps(payload, indent=2))


def is_cache_stale(cache: dict, max_age_hours: int = CACHE_MAX_AGE_HOURS) -> bool:
    fetched_at = cache.get("fetched_at")
    if not fetched_at:
        return True
    age = datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)
    return age > timedelta(hours=max_age_hours)


def get_cached_metrics(asset_id: str) -> Optional[dict]:
    """Request-time entry point — cache only, never hits the network."""
    cache = load_cache()
    if is_cache_stale(cache):
        return None
    return cache.get("assets", {}).get(asset_id)