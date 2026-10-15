import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1 import routes_portfolio
from app.schemas.llm import LLMPortfolio, LLMAllocation

client = TestClient(app)
BODY = {"monthly_income": 80000, "monthly_savings": 15000,
        "quiz": {"age": 32, "horizon": "3-7", "drop_reaction": "hold",
                 "income_stability": "stable", "experience": "some", "emergency_months": 3}}

def _enable_llm(monkeypatch):
    monkeypatch.setattr(routes_portfolio.settings, "llm_api_key", "test-key")

def test_timeout_falls_back(monkeypatch):
    _enable_llm(monkeypatch)
    async def boom(ctx): raise asyncio.TimeoutError()
    monkeypatch.setattr(routes_portfolio, "get_llm_portfolio", boom)
    data = client.post("/api/v1/portfolio/recommend", json=BODY).json()
    assert data["source"] == "fallback"
    assert round(sum(a["weight_pct"] for a in data["allocations"]), 1) == 100.0

def test_invented_asset_falls_back(monkeypatch):
    _enable_llm(monkeypatch)
    async def fake(ctx):
        return LLMPortfolio(allocations=[LLMAllocation(asset_id="tesla_stock", weight_pct=100, rationale="x")])
    monkeypatch.setattr(routes_portfolio, "get_llm_portfolio", fake)
    data = client.post("/api/v1/portfolio/recommend", json=BODY).json()
    assert data["source"] == "fallback"
    assert all(a["asset_id"] != "tesla_stock" for a in data["allocations"])