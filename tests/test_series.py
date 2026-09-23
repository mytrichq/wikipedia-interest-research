import datetime as dt

from wir import series


def test_missing_days_become_zero_not_interpolated():
    rows = [(dt.date(2026, 1, 1), 10), (dt.date(2026, 1, 3), 30)]
    daily = series.daily(rows, dt.date(2026, 1, 1), dt.date(2026, 1, 4))
    assert daily.tolist() == [10, 0, 30, 0]


def test_no_rows_means_all_zero():
    daily = series.daily([], dt.date(2026, 2, 1), dt.date(2026, 2, 28))
    assert len(daily) == 28 and daily.sum() == 0


def test_monthly_sums_whole_months():
    rows = [(dt.date(2026, 1, 31), 5), (dt.date(2026, 2, 1), 7), (dt.date(2026, 2, 28), 1)]
    monthly = series.monthly(series.daily(rows, dt.date(2026, 1, 1), dt.date(2026, 2, 28)))
    assert series.month_rows(monthly) == [["2026-01", 5], ["2026-02", 8]]
