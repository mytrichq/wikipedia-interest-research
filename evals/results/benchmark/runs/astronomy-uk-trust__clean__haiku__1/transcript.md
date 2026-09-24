# astronomy-uk-trust — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0375, duration: 28.4 s, tokens in/out: 28/1547 (cache read 63485)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "astronomy Ukrainian Wikipedia interest trend trustworthiness"
}
```

<details><summary>Tool result</summary>

```
Launching skill: wikipedia-interest-research
```
</details>

**Assistant:** Розпочинаю дослідження тренду інтересу до астрономії на українськомовній Wikipedia.

**Tool call — Bash**
```json
{
  "command": "cd <tmp>/wir-eval-hz2pt0o8/workspace/.claude/skills/wikipedia-interest-research && ./scripts/wir study new --topic \"astronomy\" --langs uk --question \"Чи зростає інтерес до астрономії на українськомовній Wikipedia?\""
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "<tmp>/wir-eval-hz2pt0o8/workspace/wiki-studies/astronomy-uk",
  "question": "Чи зростає інтерес до астрономії на українськомовній Wikipedia?",
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
  
… [360 chars cut]
```
</details>

**Assistant:** **Результат: інтерес до астрономії на українськомовній Wikipedia падає, не зростає. Відповідь на вашу думку додати курс — обережна: тренд йде проти очікування.**

- **Українськомовна Wikipedia**: падіння на 61,7% у річному порівнянні, довіра **висока** — жоден з останніх 12 місяців не перевищив аналогічний місяць минулого року (p=0,002). Відносно всієї видання української Wikipedia (яка сама впала на 24,6%) астрономія впала ще швидше — на 42,4% більше, ніж редакція в цілому. Середньомісячний трафік: 559 переглядів. Чіткий сезонний пік у вересні (≈2,3×).

**Обмеження:** інтерес до статті ≠ готовність користувачів платити за курс; читачами статті є 65% з України, 11% з США, 4% з Польщі. Українськомовна аудиторія на Wikipedia скорочується в цілому.

**Подальші кроки:**
1. Перевірте, чому саме астрономія падає швидше, ніж редакція в цілому — це можуть пояснити технічні зміни, конкуренція з іншими джерелами або реальна втрата інтересу?
2. Дослідіть інші мовні видання Wikipedia (англійська, польська) — чи там астрономія стабільнша чи зростає?

Я можу підготувати односторінковий PDF-звіт з графіками — розкажіть, якщо це допоможе обґрунтувати рішення перед командою.

### Final answer

**Результат: інтерес до астрономії на українськомовній Wikipedia падає, не зростає. Відповідь на вашу думку додати курс — обережна: тренд йде проти очікування.**

- **Українськомовна Wikipedia**: падіння на 61,7% у річному порівнянні, довіра **висока** — жоден з останніх 12 місяців не перевищив аналогічний місяць минулого року (p=0,002). Відносно всієї видання української Wikipedia (яка сама впала на 24,6%) астрономія впала ще швидше — на 42,4% більше, ніж редакція в цілому. Середньомісячний трафік: 559 переглядів. Чіткий сезонний пік у вересні (≈2,3×).

**Обмеження:** інтерес до статті ≠ готовність користувачів платити за курс; читачами статті є 65% з України, 11% з США, 4% з Польщі. Українськомовна аудиторія на Wikipedia скорочується в цілому.

**Подальші кроки:**
1. Перевірте, чому саме астрономія падає швидше, ніж редакція в цілому — це можуть пояснити технічні зміни, конкуренція з іншими джерелами або реальна втрата інтересу?
2. Дослідіть інші мовні видання Wikipedia (англійська, польська) — чи там астрономія стабільнша чи зростає?

Я можу підготувати односторінковий PDF-звіт з графіками — розкажіть, якщо це допоможе обґрунтувати рішення перед командою.
