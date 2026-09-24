# OpenRouter run — `dots-studio/dots-3-note-preview:free`

- Tool calls: **2**, tokens in/out: 8985/1505, cost $0.0, 25.5 s, retries 0

## Turn 1

> **User:** Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.

**Assistant:** 




**Tool call — Read**
```json
{
  "path": "<tmp>/wir-eval-c89dn2ym/workspace/.claude/skills/wikipedia-interest-research/SKILL.md"
}
```
<details><summary>Tool result</summary>

```
---
name: wikipedia-interest-research
description: Measures and compares audience interest in topics across Wikipedia language editions from Wikimedia pageview data, judges how trustworthy each trend is (seasonality, one-off news spikes, bots, edition-wide traffic changes), ranks languages or topics, and produces a one-page PDF report with charts. Use when a user asks whether interest in a topic is growing, wants to compare interest between languages, markets or topics, is choosing a course topic, content niche or localization language for a product, or mentions Wikipedia pageviews — even if they do not say "Wikipedia".
license: MIT
compatibility: Requires uv (https://docs.astral.sh/uv/) and internet access to wikimedia.org, wikipedia.org and wikidata.org.
metadata:
  version: "0.1.0"
---

# Wikipedia Interest Research

This skill answers questions like "is interest in X growing in Polish vs Czech Wikipedia, and can we trust it?" with real pageview data. All data work is done by the bundled CLI `scripts/wir`; your job is to pick the right inputs, run it, and explain its output honestly.

**Never** fetch pageviews yourself (WebFetch, curl, your own Python). The CLI handles the API, caching, bot filtering, statistics and fact-checking; hand-made numbers will be wrong or unverifiable.

## How to run commands

Commands are relative to this skill's directory. Call them by full path, e.g. `<skill-dir>/scripts/wir study new ...`. Run them from the user's working direc
```
</details>

**Assistant:** 




**Tool call — Bash**
```json
{
  "command": "cd <tmp>/wir-eval-c89dn2ym/workspace && <tmp>/wir-eval-c89dn2ym/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"intermittent fasting\" --langs pl,cs --period 24m --question \"Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки\"",
  "timeout": 120
}
```
<details><summary>Tool result</summary>

```
exit code 0
stdout:
{
  "status": "ok",
  "study": "intermittent-fasting-pl-cs",
  "folder": "<tmp>/wir-eval-c89dn2ym/workspace/wiki-studies/intermittent-fasting-pl-cs",
  "question": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки",
  "period": "2024-09..2026-08",
  "stats_window": "2024-09..2026-08",
  "results": [
    {
      "key": "pl",
      "status": "missing",
      "note": "No Polish article on this topic.",
      "proxy_candidates": ["Stres oksydacyjny", "Głodówka lecznicza", "Paleolityczny styl życia"]
    },
    {
      "key": "cs",
      "articles": ["Přerušovaný půst"],
      "verdict": "declining",
      "yoy_pct": -48.7,
      "months_up_of_12": 0,
      "avg_monthly_views": 183,
      "per_million_views": 3.04,
      "relative_yoy_pct": -30.5,
      "relative_verdict": "declining",
      "edition_yoy_pct": -12.6,
      "trust": "High (80)",
      "trust_reasons": ["~183 views/month: small changes look large.", "16% of views came from short news-like spikes."],
      "seasonality": "January peak ≈2.17× every year"
    }
  ],
  "ranking": [
    {
      "rank": 1,
      "key": "cs",
      "score": 28.4,
      "strongest": ["trust", "size"]
    }
  ],
  "readers_by_country": {
    "pl": "PL 87%, US 4%, DE 2%",
    "cs": "CZ 80%, US 5%, SK 5%"
  },
  "assumptions": ["Period 2024-09..2026-08 = whole months up to the last complete month; statis
```
</details>

**Assistant:** 

**Прямая відповідь**: в чеськомовній Вікіпедії інтерес до інтервального голодування суточно падає (−48,7% рік до року), тоді як у польськомовній статті на цю тему взагалі немає — це прогалина в контенті, а не нуль інтересу.

- **pl (польськомовна)**: немає статті (status: missing). Існують кандидати-проксі: «Stres oksydacyjny», «Głodówka lecznicza», «Paleolityczny styl życia» — але жоден з них не є прямим синонімом, тому порівнювати не на що.
- **cs (чеськомовна)**: verdict `declining`, yoy −48,7%, 0 з 12 місяців вищі за минулий рік, середня місячна кількість переглядів ≈183, trust **висока (80)** — через те, що малий обсяг робить зміни виглядають великими, і через те, що 16% переглядів припадають на короткі новинні спайки. Сезонність: січневий пік ≈2,17× щорічно. Відносно всієї чеськомовної Вікіпедії, яка сама зменшилася на −12,6%, тема рухалася −30,5% (теж `declining`).

**Обмеження**: інтерес до статті ≠ бажання платити; мова ≠ ринок (читачі чеськомовної Вікіпедії — 80% CZ, 5% US, 5% SK); відсутня стаття в польськомовній версії робить порівняння неможливим; низький обсяг переглядів (~183/місяць) робить тренд менш надійним, незважаючи на високий рівень довіри.

**Наступні кроки**: перевірити, чи є в польськомовній Вікіпедії стаття з іншим назвою (наприклад, за QID), або додати проксі-статтю за згодою користувача; також варто перевірити, чи були спайки викликані одноразовими новинами.

Хочете односторінковий PDF-звіт з цим аналізом?
