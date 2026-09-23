from __future__ import annotations

import datetime as dt

import pandas as pd

from wir import series
from wir.languages import Edition
from wir.metrics import MIN_MONTHS_FOR_YOY, ArticleData
from wir.periods import AUTOMATED_AGENT_START, DATA_START, Period, add_months
from wir.resolve import recent_views, redirects
from wir.wikimedia import WikimediaClient

MAX_REDIRECTS_CHECKED = 50
REDIRECT_MIN_SHARE = 0.01
RENAME_GRACE = dt.timedelta(days=45)


def analysis_window(period: Period) -> Period:
    """At least two full years, so every month can be compared with the year before."""
    if period.months >= MIN_MONTHS_FOR_YOY:
        return period
    start = add_months(period.start, -(MIN_MONTHS_FOR_YOY - period.months))
    return Period(max(start, DATA_START), period.end)


def significant_titles(
    client: WikimediaClient, edition: Edition, title: str, window: Period
) -> list[dict]:
    """The article plus redirects carrying ≥1% of its views (e.g. its title before a rename).

    Redirects are screened with one batched request for recent views. Only when the article
    itself is new in the window (a likely rename) is each redirect's full history checked.
    """
    main = series.daily(
        client.per_article(edition.project, title, window.start, window.end),
        window.start,
        window.end,
    )
    titles = [{"title": title, "views": int(main.sum()), "redirect": False}]
    aliases = redirects(client, edition, title)[:MAX_REDIRECTS_CHECKED]
    if not aliases:
        return titles
    nonzero = main[main > 0]
    renamed = nonzero.empty or nonzero.index[0].date() > window.start + RENAME_GRACE
    if renamed:
        for alias in aliases:
            rows = client.per_article(
                edition.project, alias, window.start, window.end, granularity="monthly"
            )
            total = sum(v for _, v in rows)
            if total > 0 and total >= REDIRECT_MIN_SHARE * max(int(main.sum()), 1):
                titles.append({"title": alias, "views": total, "redirect": True})
        return titles
    recent = recent_views(client, edition, [title, *aliases])
    base = max(recent.get(title, 0), 1)
    for alias in aliases:
        views = recent.get(alias, 0)
        if views > 0 and views >= REDIRECT_MIN_SHARE * base:
            titles.append({"title": alias, "views": views, "redirect": True})
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
