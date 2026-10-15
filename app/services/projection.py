from app.schemas.portfolio import Allocation, ProjectionPoint

def sip_future_value(monthly: float, annual_pct: float, years: int) -> float:
    r = (1 + annual_pct / 100) ** (1 / 12) - 1     # monthly rate
    n = years * 12
    if r == 0:
        return monthly * n
    return monthly * (((1 + r) ** n - 1) / r) * (1 + r)

def build_projections(allocations: list[Allocation], assets: dict[str, dict],
                      monthly: float, horizons=(1, 3, 5, 10)) -> list[ProjectionPoint]:
    ret = sum(a.weight_pct / 100 * assets[a.asset_id]["expected_return_pct"] for a in allocations)
    vol = sum(a.weight_pct / 100 * assets[a.asset_id]["volatility_pct"] for a in allocations)
    # simplification: weighted-average volatility overstates real portfolio risk (no correlation modelling)
    low, high = max(ret - 0.5 * vol, 0), ret + 0.5 * vol
    return [
        ProjectionPoint(
            years=y,
            invested=round(monthly * 12 * y),
            pessimistic=round(sip_future_value(monthly, low, y)),
            expected=round(sip_future_value(monthly, ret, y)),
            optimistic=round(sip_future_value(monthly, high, y)),
        )
        for y in horizons
    ]