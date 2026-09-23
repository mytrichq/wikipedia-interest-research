import datetime as dt

import pytest

from wir import periods

TODAY = dt.date(2026, 9, 23)


@pytest.mark.parametrize("value", ["24m", "2y", "2024-09..2026-08"])
def test_two_years_end_at_last_complete_month(value):
    period = periods.parse(value, TODAY)
    assert (period.start, period.end) == (dt.date(2024, 9, 1), dt.date(2026, 8, 31))
    assert period.months == 24


def test_first_day_of_month_still_excludes_current_month():
    period = periods.parse("1m", dt.date(2026, 9, 1))
    assert (period.start, period.end) == (dt.date(2026, 8, 1), dt.date(2026, 8, 31))


def test_partial_month_is_rejected():
    with pytest.raises(ValueError, match="last complete month is 2026-08"):
        periods.parse("2025-01..2026-09", TODAY)


def test_period_before_data_start_is_rejected():
    with pytest.raises(ValueError, match="starts in 2015-07"):
        periods.parse("2015-01..2016-01", TODAY)


@pytest.mark.parametrize("value", ["two years", "24", "0m", "2026-08..2025-01"])
def test_invalid_periods_explain_the_format(value):
    with pytest.raises(ValueError):
        periods.parse(value, TODAY)


def test_add_months_crosses_years():
    assert periods.add_months(dt.date(2026, 1, 1), -1) == dt.date(2025, 12, 1)
    assert periods.add_months(dt.date(2025, 12, 1), 13) == dt.date(2027, 1, 1)
