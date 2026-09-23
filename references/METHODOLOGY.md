# Methodology: how `wir` measures interest and trust

Read this file when you need to explain *why* a verdict or a trust level came out the way it did, or when the user questions the method. All thresholds live in `src/wir/metrics.py`, `trust.py` and `rank.py`.

## Contents

1. Data
2. Growth
3. Verdict
4. One-off events and spikes
5. Seasonality
6. Relative interest (adjusting for the edition)
7. Trust level
8. Ranking audiences
9. What this does not measure

## 1. Data

- **Views.** Daily pageviews with `agent=user` (humans; declared bots and crawlers excluded) across all devices. Missing days are filled with 0.
- **Window.** Whole calendar months, ending with the last complete month. It always covers at least 24 months, so every month can be compared with the same month a year earlier. If the user asks for a shorter period, the window reaches further back.
- **Titles.** The main article plus redirects that carry ≥1% of its views. A renamed article keeps its old history under the redirect.
- **Extra series.** Desktop views (used to spot bot-like spikes), `automated` views (a warning sign only; never counted), and the total views of the whole edition (used for normalisation).

## 2. Growth

| Metric | Definition |
|---|---|
| `yoy_pct` | Views in the last 12 months vs the previous 12, in %. Seasonality cancels out because both sides are full years. |
| `robust_yoy_pct` | Median over the last 12 months of (month ÷ same month a year earlier) − 1. A single abnormal month cannot move it much. |
| `months_up` | How many of the last 12 months were above the same month a year earlier. Easy to explain: "11 of 12 months were lower". |
| `p_value` | Seasonal Mann–Kendall test (Hirsch 1982) on log views. Each calendar month is compared only with itself, so school-year or holiday peaks do not create a trend. |
| `annual_trend_pct` | Seasonal Sen slope: the median yearly change of log views, converted to %. |

The code was cross-checked against SciPy on 500 random series: `uv run --with scipy python dev/verify_stats.py`.

## 3. Verdict

The verdict is computed on the series **after one-off events are removed** (section 4):

| Verdict | Condition |
|---|---|
| `growing` | robust change ≥ +10% **and** p < 0.05 **and** the test direction is up |
| `declining` | robust change ≤ −10% **and** p < 0.05 **and** the test direction is down |
| `stable` | \|robust change\| < 10% |
| `unclear` | anything else, or less than 24 months of data |

With 24 months, p < 0.05 needs roughly 10 of 12 months moving the same way. That is deliberately strict.

## 4. One-off events and spikes

- **Daily spikes.** A day is a spike if views are more than 6 robust z-scores above the 29-day rolling median, more than 3× that median, and at least 20 views above it. Consecutive spike days form one event. Each event reports its desktop share; ≥80% desktop, while normal days are far lower, looks like undeclared bots.
- **One-off months.** A month is one-off if it is ≥2.5× the median month of its year **and** the same calendar month in other years is not elevated (<1.5×). This catches multi-week news events that a rolling median absorbs, such as the papal conclave in April–May 2025. It leaves recurring peaks alone, such as September for astronomy.
- **Clean series.** Spike days are replaced with the rolling median, and one-off months with the median month of their year. `growth_without_one_offs` is computed on this clean series.

## 5. Seasonality

- **Method.** Log views are detrended, and each calendar month's average deviation is measured.
- **Strong seasonality** requires both conditions:
  - the peak month is ≥1.5× a typical month;
  - the peak month is among the top 2 months **in every year** of the window.

  One huge event therefore cannot pass as seasonality.
- **Effect on the verdict.** Seasonality never changes the verdict directly, because the growth metrics already compare like with like. It is reported so the user understands the peaks on the chart.

## 6. Relative interest (adjusting for the edition)

- **Metric.** `per_million` is article views per million views of the whole language edition.
- **Why it matters.** Whole editions rise and fall. On 2026-09-23, for example, uk.wikipedia was −25% year over year, likely because of AI answers and search changes.
- **Check.** If the absolute and relative directions disagree, the topic did not really change; the edition did. This is the `edition_effect` rule in section 7.

## 7. Trust level

Trust means how much the user can rely on the verdict. It starts at 100, and each rule below subtracts points. Every applied rule comes with a sentence of explanation in `trust.reasons`.

| Code | Effect | Rule |
|---|---|---|
| `very_low_volume` | −80 | < 30 views/month (last 12 months) |
| `low_volume` | −65 | < 100 views/month |
| `modest_volume` | −10 | < 300 views/month |
| `short_history` | −30 | < 24 months of data |
| `not_significant` | −35 | verdict is `unclear` (no consistent direction) |
| `spike_driven` | −30 | raw vs clean year-over-year differ in sign or by ≥25 points |
| `one_off_months` | −20 | one-off months present: the comparison year was unusual |
| `news_driven` | −20 | ≥30% of views came from spikes |
| `spiky` | −10 | ≥15% of views came from spikes |
| `bot_like_spikes` | −25 | bot-like spike events carry ≥5% of views |
| `automated_heavy` | −10 | ≥30% of requests were flagged `automated` |
| `edition_effect` | −35 | absolute and relative directions disagree |
| `new_article` | −30 | article created or renamed inside the window |
| `pre_2020_bots` | −5 | window starts before May 2020 (no bot separation) |
| `narrow_breadth` | −15 | multi-article topic: < 50% of articles move the same way |
| `dominant_article` | −5 | multi-article topic: one article has ≥ 90% of views |

The score maps to a level: **High** is ≥ 70, **Medium** is 40–69, **Low** is < 40. Rules with effect 0 (`volume_ok`, `consistent`, `seasonality_handled`, `edition_consistent`) are included as positive evidence.

## 8. Ranking audiences

Each candidate (a language, or a topic) gets four components on **fixed** scales. Adding a candidate never changes another candidate's score.

| Component | Scale |
|---|---|
| `momentum` | robust year-over-year change: −50% → 0, 0% → 0.33, +100% → 1 |
| `relative` | log10(views per million + 1) / 3, so 1000 per million → 1 |
| `size` | log10(avg monthly views + 1) / 5, so 100k/month → 1 |
| `trust` | trust score / 100 |

- **Score.** The score is 100 × the weighted mean. Default weights are momentum 0.35, relative 0.25, size 0.25, trust 0.15.
- **Custom weights.** Users can override them, e.g. `--weights growth=0.5,size=0.3,trust=0.2`. Weights left out become 0.

## 9. What this does not measure

Say these limits in every report:

- Interest in an encyclopedia article ≠ willingness to pay for a product.
- A language edition ≠ a country. Portuguese covers Brazil and Portugal; English covers the world. Use the edition's reader countries if available.
- Wikipedia traffic is shrinking overall, so the relative metrics matter more than the absolute ones.
- One article is a proxy for a topic. A missing article in a language is itself a finding, and an opportunity to test, not a zero.
