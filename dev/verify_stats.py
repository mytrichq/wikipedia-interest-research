"""Cross-checks wir.stats against SciPy: uv run --with scipy python dev/verify_stats.py"""

import numpy as np
from scipy import stats as sp

from wir import stats as ours


def main(trials: int = 500) -> None:
    rng = np.random.default_rng(42)
    worst_slope = worst_p = 0.0
    for _ in range(trials):
        n = int(rng.integers(8, 60))
        y = np.round(rng.normal(0, 10, n) + rng.normal(0, 0.5) * np.arange(n))
        reference = sp.theilslopes(y, np.arange(n), alpha=0.95)
        fit = ours.theil_sen(y)
        worst_slope = max(
            worst_slope,
            abs(fit.slope - reference.slope),
            abs(fit.low - reference.low_slope),
            abs(fit.high - reference.high_slope),
        )
        mk = ours.mann_kendall(y)
        p_uncorrected = 2 * (1 - sp.norm.cdf(abs(mk.s / np.sqrt(mk.variance))))
        tau = sp.kendalltau(np.arange(n), y, method="asymptotic")
        worst_p = max(worst_p, abs(p_uncorrected - tau.pvalue))
    print(f"{trials} random series with ties")
    print(f"  Theil-Sen slope and 95% CI, max abs difference: {worst_slope:.2e}")
    print(f"  Mann-Kendall p-value, max abs difference:       {worst_p:.2e}")
    assert worst_slope < 1e-9 and worst_p < 1e-9


if __name__ == "__main__":
    main()
