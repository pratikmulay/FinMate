from app.services.weights import normalize

TOL = 0.5   # allowed rounding slack, in percentage points


class GuardrailError(Exception):
    """LLM output can't be fixed. The route should use the fallback."""


def _class_totals(weights: dict[str, float], lookup: dict[str, dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for k, v in weights.items():
        c = lookup[k]["asset_class"]
        totals[c] = totals.get(c, 0) + v
    return totals


def effective_bands(bands: dict, shortlist: list[dict]) -> dict:
    """Keep only classes that exist in the shortlist. If their max bands
    can't reach 100%, scale them up so a valid portfolio is possible."""
    present = {a["asset_class"] for a in shortlist}
    eff = {c: bands.get(c, (0, 100)) for c in present}
    hi_sum = sum(hi for _, hi in eff.values())
    if 0 < hi_sum < 100:
        f = 100 / hi_sum
        eff = {c: (lo * f, hi * f) for c, (lo, hi) in eff.items()}
    return eff


def _violations(weights, lookup, eff, enforce_caps) -> list[str]:
    issues = []
    if abs(sum(weights.values()) - 100) > 0.05:
        issues.append("weights do not sum to 100")
    if enforce_caps:
        for k, v in weights.items():
            if v > lookup[k]["max_weight_pct"] + TOL:
                issues.append(f"{k} exceeds its max weight")
    totals = _class_totals(weights, lookup)
    for cls, (lo, hi) in eff.items():
        t = totals.get(cls, 0)
        if t < lo - TOL or t > hi + TOL:
            issues.append(f"{cls} outside its band")
    return issues


def validate_and_fix(items, shortlist: list[dict], bands: dict) -> dict[str, float]:
    """items: list of LLMAllocation. Returns {asset_id: weight} summing to 100,
    or raises GuardrailError."""
    lookup = {a["id"]: a for a in shortlist}

    # 1. ids must exist in the approved shortlist (no invented assets, ever)
    weights: dict[str, float] = {}
    for it in items:
        if it.asset_id not in lookup:
            raise GuardrailError(f"Unknown asset_id from LLM: {it.asset_id}")
        weights[it.asset_id] = weights.get(it.asset_id, 0) + it.weight_pct   # merge duplicates

    weights = {k: v for k, v in weights.items() if v > 0}
    if not weights:
        raise GuardrailError("LLM returned no usable allocations")

    eff = effective_bands(bands, shortlist)
    # if the per-asset caps can't add up to 100 (few assets), skip cap enforcement
    enforce_caps = sum(a["max_weight_pct"] for a in shortlist) >= 100

    # 2. clamp and renormalize until stable (normalizing can push things back over a limit)
    try:
        weights = normalize(weights)
        for _ in range(10):
            if enforce_caps:
                weights = {k: min(v, lookup[k]["max_weight_pct"]) for k, v in weights.items()}

            for cls, (lo, hi) in eff.items():
                members = [k for k in lookup if lookup[k]["asset_class"] == cls]
                tot = sum(weights.get(k, 0) for k in members)
                target = min(max(tot, lo), hi)
                if tot == 0 and target > 0:                # class missing: add it
                    for k in members:
                        weights[k] = target / len(members)
                elif tot > 0 and target != tot:            # class outside band: rescale it
                    f = target / tot
                    for k in members:
                        if k in weights:
                            weights[k] *= f

            weights = normalize({k: v for k, v in weights.items() if v > 0})
            if not _violations(weights, lookup, eff, enforce_caps):
                return weights
    except ValueError as e:
        raise GuardrailError(str(e))

    raise GuardrailError("Could not satisfy portfolio constraints")