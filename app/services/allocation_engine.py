from app.schemas.portfolio import Allocation
from app.services.weights import normalize

BANDS = {
    "Conservative": {"Liquid": (10, 20), "Debt": (55, 70), "Equity": (10, 20), "Gold": (5, 10), "Satellite": (0, 0)},
    "Moderate":     {"Liquid": (5, 10),  "Debt": (25, 40), "Equity": (35, 50), "Gold": (5, 10), "Satellite": (0, 2)},
    "Aggressive":   {"Liquid": (0, 5),   "Debt": (10, 20), "Equity": (60, 75), "Gold": (0, 10), "Satellite": (0, 5)},
}

def get_bands(profile: str, emergency_months: int) -> dict[str, tuple[int, int]]:
    bands = dict(BANDS[profile])
    if emergency_months < 3:
        bands["Liquid"] = (15, 20)      # build a buffer first
    return bands

def baseline(shortlist: list[dict], profile: str, bands: dict, monthly_savings: float) -> list[Allocation]:
    by_class: dict[str, list[dict]] = {}
    for a in shortlist:
        by_class.setdefault(a["asset_class"], []).append(a)

    raw: dict[str, float] = {}
    for cls, assets in by_class.items():
        lo, hi = bands.get(cls, (0, 0))
        target = (lo + hi) / 2
        if target <= 0:
            continue
        share = target / len(assets)
        for a in assets:
            raw[a["id"]] = min(share, a["max_weight_pct"])

    weights = normalize(raw)
    lookup = {a["id"]: a for a in shortlist}
    return [
        Allocation(
            asset_id=aid,
            name=lookup[aid]["name"],
            asset_class=lookup[aid]["asset_class"],
            weight_pct=w,
            monthly_amount=round(monthly_savings * w / 100),
            rationale=f"{lookup[aid]['sub_class']} exposure suited to a {profile} profile.",
        )
        for aid, w in weights.items()
    ]

def build_allocations(weights: dict[str, float], lookup: dict[str, dict],
                      rationales: dict[str, str], profile: str,
                      monthly_savings: float) -> list[Allocation]:
    return [
        Allocation(
            asset_id=aid,
            name=lookup[aid]["name"],
            asset_class=lookup[aid]["asset_class"],
            weight_pct=w,
            monthly_amount=round(monthly_savings * w / 100),
            rationale=rationales.get(aid)
                      or f"{lookup[aid]['sub_class']} exposure suited to a {profile} profile.",
        )
        for aid, w in weights.items()
    ]