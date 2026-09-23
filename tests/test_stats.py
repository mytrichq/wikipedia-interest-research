import math

import numpy as np
import pytest

from wir import stats


def test_mann_kendall_textbook_example():
    result = stats.mann_kendall([1, 2, 3, 4])
    assert result.s == 6
    assert result.variance == pytest.approx(4 * 3 * 13 / 18)
    assert result.z == pytest.approx(5 / math.sqrt(4 * 3 * 13 / 18))
    assert result.p_value == pytest.approx(0.0895, abs=1e-3)


def test_mann_kendall_handles_ties():
    result = stats.mann_kendall([1, 1, 2, 2])
    assert result.s == 4
    assert result.variance == pytest.approx((4 * 3 * 13 - 2 * (2 * 1 * 9)) / 18)


def test_mann_kendall_flat_series_is_not_significant():
    assert stats.mann_kendall([5] * 20).p_value == 1.0


def test_seasonal_kendall_ignores_a_repeating_seasonal_peak():
    seasonal = np.tile([100] * 8 + [400] + [100] * 3, 3)
    assert stats.mann_kendall(seasonal[:20]).p_value < 1.0
    assert stats.seasonal_kendall(seasonal).s == 0
    assert stats.seasonal_kendall(seasonal).p_value == 1.0


def test_seasonal_kendall_detects_every_month_falling():
    two_years = np.concatenate([np.full(12, 200.0), np.full(12, 100.0)])
    result = stats.seasonal_kendall(two_years)
    assert result.s == -12
    assert result.p_value < 0.01


def test_theil_sen_recovers_a_linear_slope_despite_an_outlier():
    y = 3.0 * np.arange(30) + 10
    y[7] = 1000
    fit = stats.theil_sen(y)
    assert fit.slope == pytest.approx(3.0)
    assert fit.low <= 3.0 <= fit.high


def test_seasonal_sen_is_the_median_yearly_change():
    y = np.concatenate([np.full(12, 10.0), np.full(12, 12.0)])
    y[20] = 100
    assert stats.seasonal_sen(y) == pytest.approx(2.0)
