import logging
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.portfolio import PortfolioRequest, PortfolioResponse
from app.services.risk_engine import compute_risk
from app.services.asset_selector import select_assets
from app.services.allocation_engine import get_bands, baseline, build_allocations
from app.services.projection import build_projections
from app.services.llm_service import build_context, get_llm_portfolio
from app.services.guardrails import validate_and_fix

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("/recommend", response_model=PortfolioResponse)
async def recommend(req: PortfolioRequest):
    risk = compute_risk(req.quiz)
    shortlist = select_assets(risk.profile, req.quiz.horizon)
    bands = get_bands(risk.profile, req.quiz.emergency_months)
    lookup = {a["id"]: a for a in shortlist}

    allocations, summary, source = None, "", "baseline"

    if settings.llm_api_key:
        try:
            ctx = build_context(risk.profile, req.quiz.horizon, req.monthly_savings, shortlist, bands)
            llm_out = await get_llm_portfolio(ctx)
            weights = validate_and_fix(llm_out.allocations, shortlist, bands)
            rationales = {a.asset_id: a.rationale for a in llm_out.allocations}
            allocations = build_allocations(weights, lookup, rationales, risk.profile, req.monthly_savings)
            summary, source = llm_out.summary, "llm"
        except Exception as e:                      # timeout, bad JSON, guardrail rejection, network
            logger.warning("LLM path failed (%s): %s", type(e).__name__, e)
            source = "fallback"

    if allocations is None:
        allocations = baseline(shortlist, risk.profile, bands, req.monthly_savings)

    return PortfolioResponse(
        risk=risk,
        savings_rate_pct=round(req.monthly_savings / req.monthly_income * 100, 1),
        allocations=allocations,
        projections=build_projections(allocations, lookup, req.monthly_savings),
        summary=summary,
        source=source,
    )