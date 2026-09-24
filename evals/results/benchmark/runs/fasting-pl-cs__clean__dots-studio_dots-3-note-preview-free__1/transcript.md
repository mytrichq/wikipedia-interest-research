# OpenRouter run — `dots-studio/dots-3-note-preview:free`

- Tool calls: **3**, tokens in/out: 13562/1943, cost $0.0, 34.7 s, retries 0

## Turn 1

> **User:** Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.

**Assistant:** 




**Tool call — Read**
```json
{
  "path": "<tmp>/wir-eval-i_lan4j8/workspace/.claude/skills/wikipedia-interest-research/SKILL.md"
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
  "command": "cd <tmp>/wir-eval-i_lan4j8/workspace && <tmp>/wir-eval-i_lan4j8/workspace/.claude/skills/wikipedia-interest-research/scripts/wir doctor",
  "timeout": 60
}
```
<details><summary>Tool result</summary>

```
exit code 0
stdout:
{
  "ok": true,
  "version": "0.1.0",
  "today": "2026-09-24",
  "checks": [
    {
      "check": "python",
      "ok": true,
      "detail": "3.12.14",
      "ms": 0
    },
    {
      "check": "cache",
      "ok": true,
      "detail": {
        "path": "~/.cache/wikipedia-interest-research/cache.sqlite",
        "entries": 192,
        "megabytes": 6.97
      }
    },
    {
      "check": "user_agent",
      "ok": true,
      "detail": "wikipedia-interest-research/0.1.0 (https://github.com/mytrichq/wikipedia-interest-research) httpx/0.28.1",
      "ms": 0
    },
    {
      "check": "analytics_api",
      "ok": true,
      "detail": "HTTP 200",
      "ms": 97
    },
    {
      "check": "action_api",
      "ok": true,
      "detail": "HTTP 200",
      "ms": 310
    },
    {
      "check": "wikidata_api",
      "ok": true,
      "detail": "HTTP 200",
      "ms": 274
    }
  ]
}

stderr:
wir: requests — 0 network, 0 from cache, 0 retries

```
</details>

**Assistant:** 




**Tool call — Bash**
```json
{
  "command": "cd <tmp>/wir-eval-i_lan4j8/workspace && .claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"intermittent fasting\" --langs pl,cs --question \"Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки\"",
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
  "folder": "<tmp>/wir-eval-i_lan4j8/workspace/wiki-studies/intermittent-fasting-pl-cs",
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

**Прямая відповідь**: в чеськомовній Вікіпедії інтерес до інтервального голодування сутто падає (‑48,7% рік до року, висока довіра), тоді як у польськомовній немає статті з цієї теми — це прогалина в контенті, а не нульевий інтерес.

- **cs (чеськомовна)**: зниження, ‑48,7% рік до року, 0 з 12 місяців вищі за минулий рік, довіра High (80) — ~183 перегляди/місяць: малі обсяги роблять зміни виглядають великими; 16% переглядів приходяться на короткі новинні сплески. Сезонність: січневий пік ≈2,17× щорічно. Відносно всієї чеської Вікіпедії (‑12,6%) тема рухалася ‑30,5%.
- **pl (польськомовна)**: немає статті. Кандидати на проксі-статтю: «Stres oksydacyjny», «Głodówka lecznicza», «Paleolityczny styl życia» — додати можна лише за згодою користувача, і вони будуть позначені PROXY.
- Сезонність / одноразові події: у cs — січневий пік ≈2,17× щорічно; 16% сплесків нейтралізовано як одноразові.
- Читачі за країнами: pl — PL 87%, US 4%, DE 2%; cs — CZ 80%, US 5%, SK 5%.

**Обмеження:** інтерес до статті ≠ бажання платити; мова ≠ ринок (pl = Польща + діаспора, cs = Чехія + діаспора); у pl — відсутність статті робить порівняння неможливим; у cs — малі обсяги (~183/місяць) і новинні сплески можуть вводити в оману.

**Наступні кроки:** 1) вирішити, чи додавати проксі-статтю «Głodówka lecznicza» для pl; 2) перевірити, чи є різні назви теми (наприклад, «dieta intermittentna») у польській Вікіпедії; 3) розглянути збільшений період (36 місяців), щоб побачити, чи є спад новим трендом.

Бажаєте звіт (PDF)? Тоді одразу зроблю: `scripts/wir report intermittent-fasting-pl-cs --narrative narrative.md`.
