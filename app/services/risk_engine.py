from app.schemas.risk import QuizAnswers, RiskResult

WEIGHTS = {"age": 10, "horizon": 25, "drop_reaction": 25,
           "income_stability": 15, "experience": 10, "emergency_months": 15}
ORDER = ["Conservative", "Moderate", "Aggressive"]

def _points(q: QuizAnswers) -> dict[str, int]:
    return {
        "age": 4 if q.age < 30 else 3 if q.age < 40 else 2 if q.age < 55 else 1,
        "horizon": {"<1": 1, "1-3": 2, "3-7": 3, "7+": 4}[q.horizon],
        "drop_reaction": {"sell_all": 1, "sell_some": 2, "hold": 3, "buy_more": 4}[q.drop_reaction],
        "income_stability": {"unstable": 1, "somewhat": 2, "stable": 3, "very_stable": 4}[q.income_stability],
        "experience": {"none": 1, "beginner": 2, "some": 3, "experienced": 4}[q.experience],
        "emergency_months": 1 if q.emergency_months == 0 else 2 if q.emergency_months < 3
                            else 3 if q.emergency_months < 6 else 4,
    }
def _cap(profile: str, max_profile: str, reason: str, reasons: list[str]) -> str:
    if ORDER.index(profile) > ORDER.index(max_profile):
        reasons.append(reason)
        return max_profile
    return profile

def compute_risk(q: QuizAnswers) -> RiskResult:
    pts = _points(q)
    total = sum(pts[k] * w for k, w in WEIGHTS.items())

    # this is the score line (replace the old one with these two lines)
    weight_sum = sum(WEIGHTS.values())
    score = round((total - weight_sum) / (3 * weight_sum) * 100)

    profile = "Conservative" if score < 40 else "Moderate" if score <= 70 else "Aggressive"
    reasons = [f"Weighted quiz score is {score}/100."]

    if q.horizon == "<1":
        profile = _cap(profile, "Conservative", "Horizon under 1 year caps risk at Conservative.", reasons)
    if q.horizon == "1-3":
        profile = _cap(profile, "Moderate", "Horizon of 1-3 years caps risk at Moderate.", reasons)
    if q.drop_reaction == "sell_all":
        profile = _cap(profile, "Moderate", "Selling in a 20% drop caps risk at Moderate.", reasons)
    if q.emergency_months == 0:
        profile = _cap(profile, "Moderate", "No emergency fund caps risk at Moderate.", reasons)

    return RiskResult(score=score, profile=profile, reasons=reasons)