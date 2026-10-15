from app.schemas.risk import QuizAnswers
from app.services.risk_engine import compute_risk

def make(**over):
    base = dict(age=32, horizon="3-7", drop_reaction="hold",
                income_stability="stable", experience="some", emergency_months=3)
    return QuizAnswers(**{**base, **over})

def test_mid_career_is_moderate():
    assert compute_risk(make()).profile == "Moderate"

def test_short_horizon_caps_to_conservative():
    assert compute_risk(make(age=25, horizon="<1", drop_reaction="buy_more")).profile == "Conservative"

def test_no_emergency_fund_caps_at_moderate():
    r = compute_risk(make(age=21, horizon="7+", drop_reaction="buy_more",
                          income_stability="very_stable", experience="experienced", emergency_months=0))
    assert r.profile == "Moderate"