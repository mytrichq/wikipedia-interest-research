# astronomy-uk-trust — env `realistic`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0595, duration: 34.2 s, tokens in/out: 28/1928 (cache read 78280)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "astronomy ukraine ukrainian wikipedia pageviews"
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
  "command": "<tmp>/wir-eval-jg0rpy84/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk --question \"Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?\""
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "<tmp>/wir-eval-jg0rpy84/workspace/wiki-studies/astronomy-uk",
  "question": "Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?",
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
  "assumptions": ["Period 2024-09..2026-08 = whole months up to the last complete month; statistics use 2024-09..2026-08 so every month has a year-earlier comparison.", "Views are agent=user (declared bots and crawlers excluded), all devices, redirects carrying ≥1% of an article's views included.", "Weights: momentum=0.35, relative=0.25, size=0.25, trust=0.15.", "Topic 'astron
… [399 chars cut]
```
</details>

**Assistant:** **Інтерес до астрономії в україномовній Вікіпедії різко падає**: вердикт — на спаді 61,7% у річному порівнянні, довіра висока.

- **Українська Вікіпедія**: на спаді, −61,7% рік до року (0 з 12 місяців перевищили показники року раніше), довіра висока — консистентне падіння протягом усього періоду (p=0,002). Улітку та восени чи більші піки відвідувань (вересень ≈ 2,3× від середнього), але це не зупиняє загального тренду.

Сама українська Вікіпедія теж скоротилася на 24,6%, проте астрономія падає швидше — на 42,4% відносно до змін у редакції в цілому. Це означає, що тема втрачає інтерес навіть у контексті загального скорочення трафіку.

**Обмеження:** інтерес до статті на Вікіпедії не дорівнює готовності до навчання; більшість читачів приходить з України (65%), але 11% — з США і 4% — з Польщі — це не вказує на географічну фокусність інтересу.

**Наступні кроки:** перевірте, чи падіння відбилося на інших мовних версіях (польській, англійській), або це локальне явище; розгляньте, чи впав інтерес до STEM-тематики в цілому на українській Вікіпедії.

---

Хочете за звіт для презентації? Можу підготувати односторінковий PDF з графіками.

### Final answer

**Інтерес до астрономії в україномовній Вікіпедії різко падає**: вердикт — на спаді 61,7% у річному порівнянні, довіра висока.

- **Українська Вікіпедія**: на спаді, −61,7% рік до року (0 з 12 місяців перевищили показники року раніше), довіра висока — консистентне падіння протягом усього періоду (p=0,002). Улітку та восени чи більші піки відвідувань (вересень ≈ 2,3× від середнього), але це не зупиняє загального тренду.

Сама українська Вікіпедія теж скоротилася на 24,6%, проте астрономія падає швидше — на 42,4% відносно до змін у редакції в цілому. Це означає, що тема втрачає інтерес навіть у контексті загального скорочення трафіку.

**Обмеження:** інтерес до статті на Вікіпедії не дорівнює готовності до навчання; більшість читачів приходить з України (65%), але 11% — з США і 4% — з Польщі — це не вказує на географічну фокусність інтересу.

**Наступні кроки:** перевірте, чи падіння відбилося на інших мовних версіях (польській, англійській), або це локальне явище; розгляньте, чи впав інтерес до STEM-тематики в цілому на українській Вікіпедії.

---

Хочете за звіт для презентації? Можу підготувати односторінковий PDF з графіками.
