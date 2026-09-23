from __future__ import annotations

import datetime as dt

import pandas as pd


def daily(rows: list[tuple[dt.date, int]], start: dt.date, end: dt.date) -> pd.Series:
    """Zero-filled daily views: the API omits days without views instead of returning 0."""
    index = pd.date_range(start, end, freq="D")
    if not rows:
        return pd.Series(0, index=index, dtype="int64")
    values = pd.Series({pd.Timestamp(day): views for day, views in rows}, dtype="int64")
    return values.reindex(index, fill_value=0)


def monthly(daily_views: pd.Series) -> pd.Series:
    return daily_views.resample("MS").sum()


def month_rows(series: pd.Series) -> list[list]:
    return [[stamp.strftime("%Y-%m"), int(value)] for stamp, value in series.items()]
