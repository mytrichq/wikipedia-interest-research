from __future__ import annotations

import calendar
import datetime as dt
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from wir import series, stats
from wir.periods import AUTOMATED_AGENT_START

MIN_MONTHS_FOR_YOY = 24
MEANINGFUL_CHANGE_PCT = 10.0
SIGNIFICANCE = 0.05
SPIKE_WINDOW_DAYS = 29
SPIKE_Z = 6.0
SPIKE_MULTIPLE = 3.0
SPIKE_MIN_EXCESS = 20
BOT_DESKTOP_SHARE = 0.8
BOT_DESKTOP_JUMP = 0.3
STRONG_PEAK_FACTOR = 1.5
MAX_SPIKE_EVENTS = 3
ONE_OFF_MONTH_MULTIPLE = 2.5
RECURRING_MONTH_MULTIPLE = 1.5


@dataclass
class ArticleData:
    user: pd.Series
    desktop: pd.Series
    automated: pd.Series
    project: pd.Series
    first_day_with_views: dt.date | None = None


def pct(ratio: float | None) -> float | None:
    return None if ratio is None or not math.isfinite(ratio) else round((ratio - 1) * 100, 1)


def yoy(monthly: pd.Series) -> dict:
    if len(monthly) < MIN_MONTHS_FOR_YOY:
        return {"yoy_pct": None, "robust_yoy_pct": None, "months_up": None, "months_compared": 0}
    last, prev = monthly.iloc[-12:].to_numpy(float), monthly.iloc[-24:-12].to_numpy(float)
    ratios = (last + 1) / (prev + 1)
    return {
        "yoy_pct": pct(last.sum() / prev.sum()) if prev.sum() > 0 else None,
        "robust_yoy_pct": pct(float(np.median(ratios))),
        "months_up": int((last > prev).sum()),
        "months_compared": 12,
    }


def trend(monthly: pd.Series) -> dict:
    logged = np.log1p(monthly.to_numpy(float))
    if len(monthly) >= MIN_MONTHS_FOR_YOY:
        test = stats.seasonal_kendall(logged)
        annual = stats.seasonal_sen(logged)
        method = "seasonal Mann-Kendall (each month vs the same month in other years)"
    else:
        test = stats.mann_kendall(logged)
        annual = stats.theil_sen(logged).slope * 12
        method = "Mann-Kendall (history too short to separate seasonality)"
    return {
        "p_value": round(test.p_value, 4),
        "direction": "up" if test.s > 0 else "down" if test.s < 0 else "flat",
        "annual_trend_pct": pct(math.exp(annual)),
        "method": method,
    }


def verdict(growth: dict, trend_: dict, months: int) -> str:
    if months < MIN_MONTHS_FOR_YOY or growth["robust_yoy_pct"] is None:
        return "unclear"
    change = growth["robust_yoy_pct"]
    significant = trend_["p_value"] < SIGNIFICANCE
    if abs(change) < MEANINGFUL_CHANGE_PCT:
        return "stable"
    if significant and change > 0 and trend_["direction"] == "up":
        return "growing"
    if significant and change < 0 and trend_["direction"] == "down":
        return "declining"
    return "unclear"


def _year_blocks(n: int) -> list[slice]:
    return [slice(end - 12, end) for end in range(n, 11, -12)]


def one_off_months(monthly: pd.Series) -> list[dict]:
    """Months far above their year's typical month whose calendar month is normal in other years."""
    values = monthly.to_numpy(float)
    blocks = _year_blocks(len(values))
    elevated: dict[int, float] = {}
    for block in blocks:
        typical = max(float(np.median(values[block])), 1.0)
        for index in range(block.start, block.stop):
            elevated[index] = values[index] / typical
    found = []
    for index, multiple in elevated.items():
        if multiple < ONE_OFF_MONTH_MULTIPLE:
            continue
        twins = [i for i in elevated if i != index and (i - index) % 12 == 0]
        if twins and any(elevated[i] >= RECURRING_MONTH_MULTIPLE for i in twins):
            continue
        label = f"{monthly.index[index]:%Y-%m}"
        found.append({"month": label, "times_typical": round(multiple, 1)})
    return sorted(found, key=lambda f: f["month"])


def without_one_offs(monthly: pd.Series, one_offs: list[dict]) -> pd.Series:
    cleaned = monthly.astype(float).copy()
    labels = [f"{stamp:%Y-%m}" for stamp in monthly.index]
    for block in _year_blocks(len(monthly)):
        typical = float(np.median(monthly.iloc[block]))
        for one_off in one_offs:
            if one_off["month"] in labels[block]:
                cleaned.iloc[labels.index(one_off["month"])] = typical
    return cleaned.round().astype("int64")


def seasonality(monthly: pd.Series) -> dict | None:
    """A calendar-month pattern that repeats every year (not a one-off event)."""
    n = len(monthly)
    if n < MIN_MONTHS_FOR_YOY:
        return None
    y = np.log1p(monthly.to_numpy(float))
    t = np.arange(n)
    slope = stats.theil_sen(y).slope
    detrended = y - (np.median(y - slope * t) + slope * t)
    months = monthly.index.month.to_numpy()
    means = pd.Series(detrended).groupby(months).mean()
    component = means - means.mean()
    residual = detrended - component.reindex(months).to_numpy()
    total = float(np.var(detrended))
    if total == 0:
        return {
            "strength": 0.0,
            "peak_month": None,
            "peak_factor": 1.0,
            "peak_every_year": False,
            "strong": False,
        }
    r2 = 1 - float(np.var(residual)) / total
    adjusted = max(0.0, 1 - (1 - r2) * (n - 1) / (n - 12))
    peak = int(component.idxmax())
    factor = math.exp(float(component.max() - component.median()))
    peak_every_year = all(
        peak in months[block][np.argsort(detrended[block])[-2:]] for block in _year_blocks(n)
    )
    return {
        "strength": round(adjusted, 2),
        "peak_month": calendar.month_name[peak],
        "peak_factor": round(factor, 2),
        "peak_every_year": bool(peak_every_year),
        "strong": bool(factor >= STRONG_PEAK_FACTOR and peak_every_year),
    }


def detect_spikes(user: pd.Series, desktop: pd.Series) -> tuple[dict, pd.Series]:
    """Robust z-score against a rolling median; returns events and a spike-free series."""
    baseline = user.rolling(SPIKE_WINDOW_DAYS, center=True, min_periods=7).median()
    mad = (user - baseline).abs().rolling(SPIKE_WINDOW_DAYS, center=True, min_periods=7).median()
    scale = np.maximum(mad * 1.4826, np.sqrt(baseline) + 1)
    z = (user - baseline) / scale
    is_spike = (
        (z > SPIKE_Z) & (user > SPIKE_MULTIPLE * baseline) & (user - baseline >= SPIKE_MIN_EXCESS)
    )
    cleaned = user.where(~is_spike, baseline.round()).astype("int64")

    normal_days = ~is_spike
    normal_desktop = desktop[normal_days].sum() / max(user[normal_days].sum(), 1)
    events = []
    for _, days in user[is_spike].groupby((~is_spike).cumsum()[is_spike]):
        excess = float((days - baseline[days.index]).sum())
        desktop_share = float(desktop[days.index].sum() / max(days.sum(), 1))
        events.append({
            "start": days.index[0].strftime("%Y-%m-%d"),
            "days": len(days),
            "peak_views": int(days.max()),
            "times_baseline": round(float(days.max() / max(baseline[days.idxmax()], 1)), 1),
            "excess_views": int(excess),
            "desktop_share": round(desktop_share, 2),
            "bot_like": bool(
                desktop_share >= BOT_DESKTOP_SHARE
                and desktop_share - normal_desktop >= BOT_DESKTOP_JUMP
            ),
        })  # fmt: skip
    total = max(int(user.sum()), 1)
    excess_total = sum(e["excess_views"] for e in events)
    bot_excess = sum(e["excess_views"] for e in events if e["bot_like"])
    events.sort(key=lambda e: e["excess_views"], reverse=True)
    return {
        "events": events[:MAX_SPIKE_EVENTS],
        "event_count": len(events),
        "excess_share": round(excess_total / total, 3),
        "bot_like_excess_share": round(bot_excess / total, 3),
        "normal_desktop_share": round(float(normal_desktop), 2),
    }, cleaned


def automated_share(user: pd.Series, automated: pd.Series) -> float | None:
    since = pd.Timestamp(AUTOMATED_AGENT_START)
    auto, human = automated[automated.index >= since].sum(), user[user.index >= since].sum()
    return None if auto + human == 0 else round(float(auto / (auto + human)), 3)


def analyze(data: ArticleData) -> dict:
    monthly = series.monthly(data.user)
    project_monthly = series.monthly(data.project)
    per_million = monthly / project_monthly.replace(0, np.nan) * 1e6
    months = len(monthly)

    spikes, despiked = detect_spikes(data.user, data.desktop)
    despiked_monthly = series.monthly(despiked)
    one_offs = one_off_months(despiked_monthly)
    clean_monthly = without_one_offs(despiked_monthly, one_offs)

    growth = {**yoy(monthly), **trend(monthly)}
    clean = {**yoy(clean_monthly), **trend(clean_monthly)}
    clean_per_million = clean_monthly / project_monthly.replace(0, np.nan) * 1e6
    relative = {**yoy(clean_per_million.fillna(0)), **trend(clean_per_million.fillna(0))}

    window_start = monthly.index[0].date()
    first = data.first_day_with_views
    return {
        "window": f"{monthly.index[0]:%Y-%m}..{monthly.index[-1]:%Y-%m}",
        "months": months,
        "verdict": verdict(clean, clean, months),
        "volume": {
            "total_views": int(monthly.sum()),
            "avg_monthly_last12": round(float(monthly.iloc[-12:].mean())),
            "avg_monthly_first12": round(float(monthly.iloc[:12].mean())),
        },
        "growth": growth,
        "growth_without_one_offs": {
            "yoy_pct": clean["yoy_pct"],
            "robust_yoy_pct": clean["robust_yoy_pct"],
            "months_up": clean["months_up"],
            "p_value": clean["p_value"],
            "one_off_months": one_offs,
        },
        "relative": {
            "per_million_last12": round(float(per_million.iloc[-12:].mean()), 2),
            "yoy_pct": relative["robust_yoy_pct"],
            "verdict": verdict(relative, relative, months),
            "edition_views_yoy_pct": yoy(project_monthly)["yoy_pct"],
        },
        "seasonality": seasonality(clean_monthly),
        "spikes": spikes,
        "automated_share": automated_share(data.user, data.automated),
        "data": {
            "first_day_with_views": first.isoformat() if first else None,
            "new_in_window": bool(first and first > window_start + dt.timedelta(days=45)),
            "zero_day_share": round(float((data.user == 0).mean()), 3),
            "window_before_bot_filtering": window_start < AUTOMATED_AGENT_START,
        },
        "monthly": series.month_rows(monthly),
    }
