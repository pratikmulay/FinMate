import pytest
from app.schemas.risk import QuizAnswers
from app.services.risk_engine import compute_risk
from app.services.asset_selector import select_assets
from app.services.allocation_engine import get_bands, baseline

def run(**over):
    base = dict(age=32, horizon="3-7", drop_reaction="hold",
                income_stability="stable", experience="some", emergency_months=3)
    q = QuizAnswers(**{**base, **over})
    risk = compute_risk(q)
    shortlist = select_assets(risk.profile, q.horizon)
    bands = get_bands(risk.profile, q.emergency_months)
    return risk, baseline(shortlist, risk.profile, bands, 10000)

@pytest.mark.parametrize("over", [
    {}, {"age": 58, "horizon": "1-3", "drop_reaction": "sell_some"},
    {"age": 22, "horizon": "7+", "drop_reaction": "buy_more", "income_stability": "very_stable",
     "experience": "experienced", "emergency_months": 8},
])
def test_weights_sum_to_100(over):
    _, allocs = run(**over)
    assert round(sum(a.weight_pct for a in allocs), 1) == 100.0

def test_no_crypto_unless_aggressive():
    risk, allocs = run()
    assert risk.profile != "Aggressive"
    assert all(a.asset_class != "Satellite" for a in allocs)

def test_low_emergency_fund_boosts_liquid():
    _, allocs = run(emergency_months=0)
    liquid = sum(a.weight_pct for a in allocs if a.asset_class == "Liquid")
    assert liquid >= 14