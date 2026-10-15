from datetime import date, timedelta

import pytest

from app.services.market_data import MarketDataError, compute_metrics


def _make_series(days=3 * 365, daily_growth=0.0003, start_price=100.0):
    series = []
    price = start_price
    d = date(2022, 1, 1)
    for i in range(days):
        series.append((d + timedelta(days=i), price))
        price *= 1 + daily_growth
    return series


def test_compute_metrics_returns_expected_keys():
    metrics = compute_metrics(_make_series())
    assert set(metrics) == {
        "one_year_return_pct",
        "three_year_cagr_pct",
        "annualized_volatility_pct",
        "max_drawdown_pct",
    }
    assert metrics["one_year_return_pct"] > 0  # series grows steadily
    assert metrics["max_drawdown_pct"] <= 0    # drawdown is always <= 0


def test_compute_metrics_too_short_raises():
    with pytest.raises(MarketDataError):
        compute_metrics([(date(2024, 1, 1), 100.0)])