import json
from functools import lru_cache
from pathlib import Path

APL_PATH = Path(__file__).resolve().parent.parent / "data" / "apl.json"
HORIZON_YEARS = {"<1": 0, "1-3": 1, "3-7": 3, "7+": 7}   # lower bound of each range
TARGET_RISK = {"Conservative": 2, "Moderate": 3, "Aggressive": 4.5}
MAX_PER_CLASS = {"Equity": 5}

@lru_cache
def load_apl() -> list[dict]:
    with open(APL_PATH, encoding="utf-8") as f:
        return json.load(f)

def select_assets(profile: str, horizon: str) -> list[dict]:
    years = HORIZON_YEARS[horizon]
    eligible = [
        a for a in load_apl()
        if profile in a["eligible_profiles"] and a["min_horizon_years"] <= years
    ]
    # closest to the profile's target risk first; sorted() is stable, so file order breaks ties
    ranked = sorted(eligible, key=lambda a: abs(a["risk_level"] - TARGET_RISK[profile]))
    by_class: dict[str, list[dict]] = {}
    for a in ranked:
        bucket = by_class.setdefault(a["asset_class"], [])
        if len(bucket) < MAX_PER_CLASS.get(a["asset_class"], 3):
            bucket.append(a)
    return [a for bucket in by_class.values() for a in bucket]
