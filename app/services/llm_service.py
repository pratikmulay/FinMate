import asyncio
from pathlib import Path

import instructor
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.llm import LLMPortfolio
from app.services.guardrails import effective_bands

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "portfolio_system.txt"
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = instructor.from_openai(
            AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url),
            mode=instructor.Mode.MD_JSON,
        )
    return _client


def build_context(profile: str, horizon: str, monthly_savings: float,
                  shortlist: list[dict], bands: dict) -> dict:
    """Only validated enums and numbers go into the prompt, never free text."""
    eff = effective_bands(bands, shortlist)
    return {
        "risk_profile": profile,
        "horizon_years": horizon,
        "monthly_savings": monthly_savings,
        "assets": [
            {k: a[k] for k in ("id", "name", "asset_class", "risk_level",
                               "expected_return_pct", "volatility_pct", "max_weight_pct")}
            for a in shortlist
        ],
        "class_bands": {c: {"min": round(lo, 1), "max": round(hi, 1)} for c, (lo, hi) in eff.items()},
    }


async def get_llm_portfolio(context: dict) -> LLMPortfolio:
    import json
    try:
        coro = _get_client().chat.completions.create(
            model=settings.llm_model,
            response_model=LLMPortfolio,
            max_retries=3,
            temperature=0.1,
            messages=[
                {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
                {"role": "user", "content": json.dumps(context)},
            ],
        )
        return await asyncio.wait_for(coro, timeout=settings.llm_timeout)
    except Exception as exc:
        print(f"\n[LLM ERROR]: {type(exc).__name__} -> {exc}\n")
        raise exc