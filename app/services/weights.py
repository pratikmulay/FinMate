def normalize(weights: dict[str, float]) -> dict[str, float]:
    """Scale weights so they sum to exactly 100.0 (1 decimal place)."""
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Weights must have a positive total")
    scaled = {k: round(v / total * 100, 1) for k, v in weights.items()}
    diff = round(100.0 - sum(scaled.values()), 1)
    biggest = max(scaled, key=scaled.get)
    scaled[biggest] = round(scaled[biggest] + diff, 1)
    return scaled