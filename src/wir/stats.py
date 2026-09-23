from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

NORMAL = NormalDist()


@dataclass(frozen=True)
class KendallResult:
    s: float
    variance: float
    z: float
    p_value: float


def _kendall_s(values: np.ndarray) -> tuple[float, float]:
    n = len(values)
    if n < 2:
        return 0.0, 0.0
    diffs = np.sign(values[None, :] - values[:, None])
    s = float(np.triu(diffs, k=1).sum())
    _, counts = np.unique(values, return_counts=True)
    ties = sum(t * (t - 1) * (2 * t + 5) for t in counts if t > 1)
    variance = (n * (n - 1) * (2 * n + 5) - ties) / 18
    return s, float(variance)


def _z_and_p(s: float, variance: float) -> tuple[float, float]:
    if variance <= 0:
        return 0.0, 1.0
    z = (s - math.copysign(1, s)) / math.sqrt(variance) if s else 0.0
    return z, 2 * (1 - NORMAL.cdf(abs(z)))


def mann_kendall(values) -> KendallResult:
    s, variance = _kendall_s(np.asarray(values, dtype=float))
    return KendallResult(s, variance, *_z_and_p(s, variance))


def seasonal_kendall(values, period: int = 12) -> KendallResult:
    """Hirsch's seasonal Mann-Kendall: compares each calendar month only with itself."""
    values = np.asarray(values, dtype=float)
    s_total = var_total = 0.0
    for season in range(period):
        s, variance = _kendall_s(values[season::period])
        s_total += s
        var_total += variance
    return KendallResult(s_total, var_total, *_z_and_p(s_total, var_total))


@dataclass(frozen=True)
class SenSlope:
    slope: float
    low: float
    high: float


def theil_sen(values, confidence: float = 0.95) -> SenSlope:
    """Median pairwise slope with Sen's (1968) rank-based confidence interval."""
    y = np.asarray(values, dtype=float)
    i, j = np.triu_indices(len(y), k=1)
    slopes = np.sort((y[j] - y[i]) / (j - i))
    if len(slopes) == 0:
        return SenSlope(0.0, 0.0, 0.0)
    _, variance = _kendall_s(y)
    c = NORMAL.inv_cdf(0.5 + confidence / 2) * math.sqrt(variance)
    lower = max(round((len(slopes) - c) / 2) - 1, 0)
    upper = min(round((len(slopes) + c) / 2), len(slopes) - 1)
    return SenSlope(float(np.median(slopes)), float(slopes[lower]), float(slopes[upper]))


def seasonal_sen(values, period: int = 12) -> float:
    """Median of within-season slopes per period step (per year for monthly data)."""
    values = np.asarray(values, dtype=float)
    slopes = []
    for season in range(period):
        y = values[season::period]
        for a in range(len(y)):
            for b in range(a + 1, len(y)):
                slopes.append((y[b] - y[a]) / (b - a))
    return float(np.median(slopes)) if slopes else 0.0
