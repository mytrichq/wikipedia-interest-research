from __future__ import annotations

import math

DEFAULT_WEIGHTS = {"momentum": 0.35, "relative": 0.25, "size": 0.25, "trust": 0.15}
ALIASES = {"growth": "momentum", "volume": "size", "audience": "size", "share": "relative"}
DESCRIPTIONS = {
    "momentum": "year-over-year change (-50% → 0, +100% → 1)",
    "relative": "views per million edition views (log scale, 1000 → 1)",
    "size": "average monthly views (log scale, 100k → 1)",
    "trust": "trust score / 100",
}


def parse_weights(text: str | None) -> dict[str, float]:
    if not text:
        return dict(DEFAULT_WEIGHTS)
    weights = dict.fromkeys(DEFAULT_WEIGHTS, 0.0)
    for part in text.split(","):
        name, _, value = part.partition("=")
        name = ALIASES.get(name.strip().lower(), name.strip().lower())
        if name not in weights:
            raise ValueError(
                f"Unknown weight '{name}'. Use: {', '.join(DEFAULT_WEIGHTS)} "
                "(aliases: growth, volume, share). Example: --weights growth=0.5,size=0.3,trust=0.2"
            )
        try:
            weights[name] = float(value)
        except ValueError:
            raise ValueError(f"Weight for '{name}' must be a number, got '{value}'.") from None
    if sum(weights.values()) <= 0:
        raise ValueError("At least one weight must be positive.")
    return weights


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def components(metrics: dict, trust: dict) -> dict[str, float]:
    yoy = metrics["growth"]["robust_yoy_pct"]
    return {
        "momentum": _clip(((yoy or 0) + 50) / 150),
        "relative": _clip(math.log10(metrics["relative"]["per_million_last12"] + 1) / 3),
        "size": _clip(math.log10(metrics["volume"]["avg_monthly_last12"] + 1) / 5),
        "trust": trust["score"] / 100,
    }


def rank(entries: list[dict], weights: dict[str, float]) -> list[dict]:
    """entries: [{"key", "metrics", "trust"}] -> sorted rows with a 0-100 score."""
    total_weight = sum(weights.values())
    rows = []
    for entry in entries:
        parts = components(entry["metrics"], entry["trust"])
        contributions = {k: weights[k] * v for k, v in parts.items()}
        score = 100 * sum(contributions.values()) / total_weight
        strongest = sorted(
            (k for k in contributions if weights[k] > 0), key=contributions.get, reverse=True
        )
        rows.append(
            {
                "key": entry["key"],
                "score": round(score, 1),
                "components": {k: round(v, 2) for k, v in parts.items()},
                "strongest": strongest[:2],
            }
        )
    rows.sort(key=lambda r: r["score"], reverse=True)
    for position, row in enumerate(rows, start=1):
        row["rank"] = position
    return rows
