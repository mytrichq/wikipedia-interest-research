# offline-cache — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0375, duration: 23.8 s, tokens in/out: 28/1566 (cache read 63475)

## Turn 1

> **User:** Чи зростає інтерес до астрономії в українській Wikipedia?

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "astronomy Ukrainian"
}
```

<details><summary>Tool result</summary>

```
Launching skill: wikipedia-interest-research
```
</details>

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-iscgy9of/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk --question \"Чи зростає інтерес до астрономії в українській Wikipedia?\"",
  "description": "Run Wikipedia interest research for astronomy on Ukrainian Wikipedia"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "<tmp>/wir-eval-iscgy9of/workspace/wiki-studies/astronomy-uk",
  "question": "Чи зростає інтерес до астрономії в українській Wikipedia?",
  "period": "2024-09..2026-08",
  "stats_window": "2024-09..2026-08",
  "results": [
    {
      "key": "uk",
      "articles": ["Астрономія"],
      "verdict": "declining",
      "yoy_pct": -61.7,
      "months_up_of_12": 0,
      "avg_monthly_views": 559,
      "per_million_views": 9.69,
      "relative_yoy_pct": -42.4,
      "relative_verdict": "declining",
      "edition_yoy_pct": -24.6,
      "trust": "High (100)",
      "trust_reasons": ["0 of 12 months were above the same month a year earlier (p=0.002)."],
      "seasonality": "September peak ≈2.3× every year"
    }
  ],
  "ranking": [
    {
      "rank": 1,
      "key": "uk",
      "score": 37.3,
      "strongest": ["trust", "size"]
    }
  ],
  "readers_by_country": {
    "uk": "UA 65%, US 11%, PL 4%"
  },
  "assumptions": ["Period 2024-09..2026-08 = whole months up to the last complete month; statistics use 2024-09..2026-08 so every month has a year-earlier comparison.", "Views are agent=user (declared bots and crawlers excluded), all devices, redirects carrying ≥1% of an article's views included.", "Weights: momentum=0.35, relative=0.25, size=0.25, trust=0.15.", "Topic 'astronomy' = Wikidata Q333 (astronomy)."],
  "next_
… [354 chars cut]
```
</details>

**Assistant:** **Ні, інтерес до астрономії в українській Wikipedia різко знижується**: падіння на 61,7% рік до року, довіра висока.

- **Українська Wikipedia**: інтерес **знижується** на 61,7% рік до року (0 з 12 останніх місяців перевищили показники року тому), довіра **висока** — статистична значущість (p=0,002) не залишає місця для випадковості. Середньомісячно стаття про астрономію збирає 559 переглядів. Є стійкий піковий сезон в вересні (приблизно 2,3× вище кожного року), але навіть він не врятував тренд.

- **Контекст**: вся українськомовна Wikipedia впала на 24,6% рік до року; астрономія впала на 42,4% більше ніж видання в цілому, отже інтерес до теми знижується швидше, ніж загальне зменшення трафіку.

**Обмеження:** інтерес до статті ≠ інтерес до теми (люди можуть вчитися в інших джерелах); більшість читачів з України (65%), але також 11% з США й 4% з Польщі — це вже не міцно прив'язано до українського ринку. Дані охоплюють вересень 2024 — серпень 2026, щомісячні показники порівнюються з тим же місяцем року раніше.

**Наступне:** перевірити, чи пов'язане падіння з видаленням вмісту або змінами в освітніх програмах; подивитися на відповідні статті (космос, планети, астрофізика), щоб побачити, чи це падіння глобальне або специфічне для астрономії.

Хочете односторінковий звіт (PDF) з графіками?

### Final answer

**Ні, інтерес до астрономії в українській Wikipedia різко знижується**: падіння на 61,7% рік до року, довіра висока.

- **Українська Wikipedia**: інтерес **знижується** на 61,7% рік до року (0 з 12 останніх місяців перевищили показники року тому), довіра **висока** — статистична значущість (p=0,002) не залишає місця для випадковості. Середньомісячно стаття про астрономію збирає 559 переглядів. Є стійкий піковий сезон в вересні (приблизно 2,3× вище кожного року), але навіть він не врятував тренд.

- **Контекст**: вся українськомовна Wikipedia впала на 24,6% рік до року; астрономія впала на 42,4% більше ніж видання в цілому, отже інтерес до теми знижується швидше, ніж загальне зменшення трафіку.

**Обмеження:** інтерес до статті ≠ інтерес до теми (люди можуть вчитися в інших джерелах); більшість читачів з України (65%), але також 11% з США й 4% з Польщі — це вже не міцно прив'язано до українського ринку. Дані охоплюють вересень 2024 — серпень 2026, щомісячні показники порівнюються з тим же місяцем року раніше.

**Наступне:** перевірити, чи пов'язане падіння з видаленням вмісту або змінами в освітніх програмах; подивитися на відповідні статті (космос, планети, астрофізика), щоб побачити, чи це падіння глобальне або специфічне для астрономії.

Хочете односторінковий звіт (PDF) з графіками?
