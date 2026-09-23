from __future__ import annotations

import pandas as pd

from wir import series
from wir.languages import Edition
from wir.metrics import MIN_MONTHS_FOR_YOY, ArticleData
from wir.periods import AUTOMATED_AGENT_START, DATA_START, Period, add_months
from wir.resolve import redirects
from wir.wikimedia import WikimediaClient

MAX_REDIRECTS_CHECKED = 20
REDIRECT_MIN_SHARE = 0.01


def analysis_window(period: Period) -> Period:
    """At least two full years, so every month can be compared with the year before."""
    if period.months >= MIN_MONTHS_FOR_YOY:
        return period
    start = add_months(period.start, -(MIN_MONTHS_FOR_YOY - period.months))
    return Period(max(start, DATA_START), period.end)


def significant_titles(
    client: WikimediaClient, edition: Edition, title: str, window: Period
) -> list[dict]:
    """The article plus redirects carrying ≥1% of its views (e.g. its title before a rename)."""
    main = client.per_article(
        edition.project, title, window.start, window.end, granularity="monthly"
    )
    main_total = sum(v for _, v in main)
    titles = [{"title": title, "views": main_total, "redirect": False}]
    for alias in redirects(client, edition, title)[:MAX_REDIRECTS_CHECKED]:
        rows = client.per_article(
            edition.project, alias, window.start, window.end, granularity="monthly"
        )
        total = sum(v for _, v in rows)
        if total > 0 and total >= REDIRECT_MIN_SHARE * max(main_total, 1):
            titles.append({"title": alias, "views": total, "redirect": True})
    return titles


def _sum_daily(client, edition, titles, window, **kwargs) -> pd.Series:
    total = series.daily([], window.start, window.end)
    for title in titles:
        rows = client.per_article(edition.project, title, window.start, window.end, **kwargs)
        total = total + series.daily(rows, window.start, window.end)
    return total


def collect(
    client: WikimediaClient, edition: Edition, titles: list[str], window: Period
) -> ArticleData:
    user = _sum_daily(client, edition, titles, window)
    desktop = _sum_daily(client, edition, titles, window, access="desktop")
    automated = series.daily([], window.start, window.end)
    if window.end >= AUTOMATED_AGENT_START:
        bots_window = Period(max(window.start, AUTOMATED_AGENT_START), window.end)
        automated = automated.add(
            _sum_daily(client, edition, titles, bots_window, agent="automated"), fill_value=0
        ).astype("int64")
    project = series.daily(
        client.aggregate(edition.project, window.start, window.end), window.start, window.end
    )
    nonzero = user[user > 0]
    first = nonzero.index[0].date() if len(nonzero) else None
    return ArticleData(user, desktop, automated, project, first)
