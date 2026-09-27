from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from wir import config

DATA_START = dt.date(2015, 7, 1)
# The "automated" agent class starts on 2020-04-29; earlier bots are counted as "user".
AUTOMATED_AGENT_START = dt.date(2020, 5, 1)


@dataclass(frozen=True)
class Period:
    start: dt.date
    end: dt.date

    @property
    def months(self) -> int:
        return (self.end.year - self.start.year) * 12 + self.end.month - self.start.month + 1

    def label(self) -> str:
        return f"{self.start:%Y-%m}..{self.end:%Y-%m}"


def add_months(day: dt.date, months: int) -> dt.date:
    index = day.year * 12 + day.month - 1 + months
    return dt.date(index // 12, index % 12 + 1, 1)


def month_end(day: dt.date) -> dt.date:
    return add_months(dt.date(day.year, day.month, 1), 1) - dt.timedelta(days=1)


def last_complete_month_end(today: dt.date | None = None) -> dt.date:
    today = today or config.today()
    return dt.date(today.year, today.month, 1) - dt.timedelta(days=1)


def parse(value: str, today: dt.date | None = None) -> Period:
    """'24m', '2y' or 'YYYY-MM..YYYY-MM'; always whole months ending at a complete month."""
    value = value.strip().lower()
    latest_end = last_complete_month_end(today)
    if match := re.fullmatch(r"(\d+)\s*([my])", value):
        count = int(match.group(1)) * (12 if match.group(2) == "y" else 1)
        if count < 1:
            raise ValueError("Period must be at least 1 month.")
        start = add_months(dt.date(latest_end.year, latest_end.month, 1), -(count - 1))
        period = Period(start, latest_end)
    elif match := re.fullmatch(r"(\d{4})-(\d{2})\.\.(\d{4})-(\d{2})", value):
        start = dt.date(int(match.group(1)), int(match.group(2)), 1)
        end = month_end(dt.date(int(match.group(3)), int(match.group(4)), 1))
        if end > latest_end:
            raise ValueError(
                f"Period ends in {end:%Y-%m}, but the last complete month is {latest_end:%Y-%m}. "
                "Partial months distort trends; end the period at a complete month."
            )
        if start > end:
            raise ValueError("Period start is after its end.")
        period = Period(start, end)
    else:
        raise ValueError(
            f"Cannot parse period '{value}'. Use '24m', '2y' or 'YYYY-MM..YYYY-MM' "
            "(e.g. 2024-09..2026-08)."
        )
    if period.start < DATA_START:
        raise ValueError(
            f"Pageview data starts in {DATA_START:%Y-%m}; the period starts in "
            f"{period.start:%Y-%m}. Shorten the period."
        )
    return period
