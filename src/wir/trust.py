from __future__ import annotations

from wir.metrics import MEANINGFUL_CHANGE_PCT, MIN_MONTHS_FOR_YOY

HIGH = 70
MEDIUM = 40
VERY_LOW_VOLUME = 30
LOW_VOLUME = 100
MODEST_VOLUME = 300
SPIKE_DRIVEN_GAP_PP = 25
SPIKY_SHARE = 0.15
NEWS_DRIVEN_SHARE = 0.3
BOT_LIKE_SHARE = 0.05
AUTOMATED_HEAVY = 0.3
NARROW_BREADTH = 0.5
DOMINANT_ARTICLE = 0.9


def _sign(value: float | None) -> int:
    if value is None or abs(value) < MEANINGFUL_CHANGE_PCT:
        return 0
    return 1 if value > 0 else -1


def _volume(reasons: list, avg: int) -> None:
    if avg < VERY_LOW_VOLUME:
        reasons.append(("very_low_volume", -80, f"Only ~{avg} views/month: a few readers move it."))
    elif avg < LOW_VOLUME:
        reasons.append(("low_volume", -65, f"Only ~{avg} views/month: too little data to trust."))
    elif avg < MODEST_VOLUME:
        reasons.append(("modest_volume", -10, f"~{avg} views/month: small changes look large."))
    else:
        reasons.append(("volume_ok", 0, f"~{avg} views/month is enough for a stable estimate."))


def _consistency(reasons: list, m: dict) -> None:
    growth = m["growth_without_one_offs"]
    if m["months"] < MIN_MONTHS_FOR_YOY:
        text = f"{m['months']} months of data: no full year-over-year comparison."
        reasons.append(("short_history", -30, text))
        return
    detail = (
        f"{growth['months_up']} of 12 months were above the same month a year earlier "
        f"(p={growth['p_value']})"
    )
    if m["verdict"] == "unclear":
        reasons.append(("not_significant", -35, f"No consistent direction: {detail}."))
    else:
        reasons.append(("consistent", 0, f"{detail}."))
    season = m.get("seasonality")
    if season and season["strong"]:
        text = (
            f"Strong seasonality ({season['peak_month']} ≈ {season['peak_factor']}× a typical "
            "month) is handled by comparing each month with the same month a year earlier."
        )
        reasons.append(("seasonality_handled", 0, text))


def _spikes_and_bots(reasons: list, m: dict) -> None:
    cleaned, spikes = m["growth_without_one_offs"], m["spikes"]
    yoy, clean = m["growth"]["yoy_pct"], cleaned["yoy_pct"]
    one_offs = ", ".join(f"{o['month']} (×{o['times_typical']})" for o in cleaned["one_off_months"])
    if (
        yoy is not None
        and clean is not None
        and (_sign(yoy) != _sign(clean) or abs(yoy - clean) >= SPIKE_DRIVEN_GAP_PP)
    ):
        text = f"One-off events drive the raw change: {yoy:+.0f}% with them, {clean:+.0f}% without"
        text += f" (one-off months: {one_offs})." if one_offs else "."
        reasons.append(("spike_driven", -30, text))
    elif one_offs:
        text = (
            f"One-off months ({one_offs}) were set to a typical level, but they show the "
            "comparison year was unusual, so part of the change is a return to normal."
        )
        reasons.append(("one_off_months", -20, text))
    share = spikes["excess_share"]
    if share >= NEWS_DRIVEN_SHARE:
        text = f"{share:.0%} of views came from short spikes: a news-driven topic."
        reasons.append(("news_driven", -20, text))
    elif share >= SPIKY_SHARE:
        text = f"{share:.0%} of views came from short news-like spikes."
        reasons.append(("spiky", -10, text))
    if spikes["bot_like_excess_share"] >= BOT_LIKE_SHARE:
        text = "Some spikes are almost all desktop traffic, a typical sign of undeclared bots."
        reasons.append(("bot_like_spikes", -25, text))
    automated = m.get("automated_share")
    if automated is not None and automated >= AUTOMATED_HEAVY:
        text = f"{automated:.0%} of requests were flagged as automated (excluded; a warning sign)."
        reasons.append(("automated_heavy", -10, text))


def _edition(reasons: list, m: dict) -> None:
    absolute = m["growth_without_one_offs"]["robust_yoy_pct"]
    relative = m["relative"]["yoy_pct"]
    if absolute is None or relative is None:
        return
    if _sign(absolute) != _sign(relative):
        edition = m["relative"]["edition_views_yoy_pct"] or 0
        text = (
            f"The whole edition's traffic changed {edition:+.0f}%; relative to it the topic "
            f"moved {relative:+.0f}% (absolute: {absolute:+.0f}%)."
        )
        reasons.append(("edition_effect", -35, text))
    else:
        text = "The trend holds after adjusting for the edition's total traffic."
        reasons.append(("edition_consistent", 0, text))


def _data(reasons: list, m: dict) -> None:
    if m["data"]["new_in_window"]:
        text = (
            f"The article only has views since {m['data']['first_day_with_views']} "
            "(created or renamed in the window), so early growth is mechanical."
        )
        reasons.append(("new_article", -30, text))
    if m["data"]["window_before_bot_filtering"]:
        text = "Part of the window is before May 2020, when bots were not yet separated out."
        reasons.append(("pre_2020_bots", -5, text))


def _cluster(reasons: list, cluster: dict | None) -> None:
    if not cluster or cluster.get("articles", 1) <= 1:
        return
    if cluster.get("breadth", 1) < NARROW_BREADTH:
        text = f"Only {cluster['breadth']:.0%} of the topic's articles move in the same direction."
        reasons.append(("narrow_breadth", -15, text))
    if cluster.get("top_share", 0) >= DOMINANT_ARTICLE:
        text = f"One article provides {cluster['top_share']:.0%} of the topic's views."
        reasons.append(("dominant_article", -5, text))


def assess(m: dict, cluster: dict | None = None) -> dict:
    """Rule-based confidence in the trend verdict; every deduction carries its reason."""
    reasons: list[tuple[str, int, str]] = []
    _volume(reasons, m["volume"]["avg_monthly_last12"])
    _consistency(reasons, m)
    _spikes_and_bots(reasons, m)
    _edition(reasons, m)
    _data(reasons, m)
    _cluster(reasons, cluster)
    score = max(0, 100 + sum(effect for _, effect, _ in reasons))
    level = "High" if score >= HIGH else "Medium" if score >= MEDIUM else "Low"
    return {
        "level": level,
        "score": score,
        "reasons": [{"code": c, "effect": e, "text": t} for c, e, t in reasons],
    }
