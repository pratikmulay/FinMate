import pytest
from app.schemas.llm import LLMAllocation
from app.services.asset_selector import select_assets
from app.services.allocation_engine import get_bands
from app.services.guardrails import validate_and_fix, GuardrailError

def alloc(**weights):
    return [LLMAllocation(asset_id=k, weight_pct=v, rationale="test") for k, v in weights.items()]

def test_unknown_asset_is_rejected():
    shortlist = select_assets("Moderate", "3-7")
    with pytest.raises(GuardrailError):
        validate_and_fix(alloc(fake_coin=100), shortlist, get_bands("Moderate", 3))

def test_weights_over_100_are_normalized():
    shortlist = select_assets("Conservative", "<1")          # liquid_fund + bank_fd only
    out = validate_and_fix(alloc(liquid_fund=70, bank_fd=60), shortlist, get_bands("Conservative", 3))
    assert round(sum(out.values()), 1) == 100.0

def test_crypto_is_clamped_to_its_cap():
    shortlist = select_assets("Aggressive", "7+")
    bands = get_bands("Aggressive", 6)
    llm = alloc(nifty50_index=30, flexi_cap=25, nifty_next50_index=15,
                gilt_fund=8, short_duration_debt=7, gold_etf=5, bitcoin=10)
    out = validate_and_fix(llm, shortlist, bands)
    assert round(sum(out.values()), 1) == 100.0
    assert out["bitcoin"] <= 5.5