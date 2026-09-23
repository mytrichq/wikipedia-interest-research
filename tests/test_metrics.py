import datetime as dt

import numpy as np
import pandas as pd
import pytest

from wir import trust
from wir.metrics import ArticleData, analyze, one_off_months

START = dt.date(2024, 9, 1)
END = dt.date(2026, 8, 31)
DAYS = pd.date_range(START, END, freq="D")
EDITION_DAILY = 1_500_000


def make(
    monthly_level,
    *,
    noise=0.05,
    desktop_share=0.35,
    edition=None,
    seed=1,
    edits=None,
) -> ArticleData:
    """Daily series from a function of the month index (0..23) with multiplicative noise."""
    rng = np.random.default_rng(seed)
    month_index = (DAYS.year - START.year) * 12 + DAYS.month - START.month
    level = np.array([monthly_level(m, d) for m, d in zip(month_index, DAYS, strict=True)])
    user = pd.Series(np.round(level * rng.normal(1, noise, len(DAYS))).clip(0), index=DAYS)
    desktop = (user * desktop_share).round()
    if edits:
        user, desktop = edits(user.copy(), desktop.copy())
    edition_level = edition or (lambda m: EDITION_DAILY)
    project = pd.Series([edition_level(m) for m in month_index], index=DAYS, dtype=float)
    return ArticleData(
        user=user.astype("int64"),
        desktop=desktop.astype("int64"),
        automated=(user * 0.05).round().astype("int64"),
        project=project.round().astype("int64"),
        first_day_with_views=START,
    )


def run(data: ArticleData):
    metrics = analyze(data)
    return metrics, trust.assess(metrics)


def codes(assessment) -> set[str]:
    return {r["code"] for r in assessment["reasons"]}


def test_steady_growth_is_growing_with_high_trust():
    metrics, assessment = run(make(lambda m, d: 60 * 1.03**m))
    assert metrics["verdict"] == "growing"
    assert metrics["growth"]["yoy_pct"] == pytest.approx(42.6, abs=5)
    assert metrics["growth"]["months_up"] == 12
    assert assessment["level"] == "High"


def test_september_peak_is_seasonality_not_growth():
    metrics, assessment = run(make(lambda m, d: 200 if d.month == 9 else 60))
    assert metrics["verdict"] == "stable"
    assert metrics["seasonality"]["peak_month"] == "September"
    assert metrics["seasonality"]["strong"] is True
    assert "seasonality_handled" in codes(assessment)
    assert assessment["level"] == "High"


def test_one_off_month_in_base_year_is_flagged():
    def level(m, d):
        return 900 if (d.year, d.month) == (2025, 5) else 60

    metrics, assessment = run(make(level))
    months = [o["month"] for o in metrics["growth_without_one_offs"]["one_off_months"]]
    assert months == ["2025-05"]
    assert metrics["seasonality"]["strong"] is False
    assert metrics["verdict"] == "stable"
    assert "one_off_months" in codes(assessment) or "spike_driven" in codes(assessment)


def test_short_spike_does_not_count_as_growth():
    def spike(user, desktop):
        user.loc["2026-03-10":"2026-03-12"] = 4000
        desktop.loc["2026-03-10":"2026-03-12"] = 1400
        return user, desktop

    metrics, assessment = run(make(lambda m, d: 60, edits=spike))
    assert metrics["growth"]["yoy_pct"] > 10
    assert metrics["verdict"] == "stable"
    assert metrics["spikes"]["event_count"] >= 1
    assert "spike_driven" in codes(assessment)
    assert assessment["level"] != "High"


def test_desktop_only_spike_looks_like_bots():
    def bots(user, desktop):
        user.loc["2025-11-01":"2025-11-04"] = 3000
        desktop.loc["2025-11-01":"2025-11-04"] = 2950
        return user, desktop

    metrics, assessment = run(make(lambda m, d: 80, edits=bots))
    assert metrics["spikes"]["events"][0]["bot_like"] is True
    assert "bot_like_spikes" in codes(assessment)


def test_growth_that_only_mirrors_the_edition_is_not_attributed_to_the_topic():
    metrics, assessment = run(
        make(lambda m, d: 60 * 1.03**m, edition=lambda m: EDITION_DAILY * 1.03**m)
    )
    assert metrics["verdict"] == "growing"
    assert metrics["relative"]["verdict"] == "stable"
    assert "edition_effect" in codes(assessment)
    assert assessment["level"] != "High"


def test_low_volume_gives_low_trust():
    metrics, assessment = run(make(lambda m, d: 1.5 * 1.03**m, noise=0.3))
    assert metrics["volume"]["avg_monthly_last12"] < 100
    assert assessment["level"] == "Low"


def test_article_created_inside_the_window():
    data = make(lambda m, d: 0 if m < 8 else 80)
    data.first_day_with_views = dt.date(2025, 5, 1)
    _, assessment = run(data)
    assert "new_article" in codes(assessment)


def test_short_history_is_unclear():
    data = make(lambda m, d: 60)
    cut = data.user.index >= pd.Timestamp("2025-11-01")
    data = ArticleData(*(s[cut] for s in (data.user, data.desktop, data.automated, data.project)))
    metrics, assessment = run(data)
    assert metrics["months"] == 10
    assert metrics["verdict"] == "unclear"
    assert "short_history" in codes(assessment)


def test_every_reason_explains_itself():
    _, assessment = run(make(lambda m, d: 60 * 1.03**m))
    assert all(r["text"] and r["code"] for r in assessment["reasons"])
    assert assessment["score"] == 100 + sum(r["effect"] for r in assessment["reasons"])


def test_one_off_detection_leaves_recurring_peaks_alone():
    index = pd.date_range("2024-09-01", periods=24, freq="MS")
    values = [300 if stamp.month == 9 else 100 for stamp in index]
    values[8] = 900
    found = one_off_months(pd.Series(values, index=index))
    assert [f["month"] for f in found] == ["2025-05"]
