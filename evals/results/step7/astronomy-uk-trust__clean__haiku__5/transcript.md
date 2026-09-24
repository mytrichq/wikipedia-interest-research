# astronomy-uk-trust — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0387, duration: 26.7 s, tokens in/out: 28/1741 (cache read 63443)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

**Assistant:** Це чудове питання для прийняття рішення про вміст. Я використаю навик дослідження интереса до астрономії на украйнській Wikipedia.

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
  "command": "<tmp>/wir-eval-xkg5q_8d/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk --question \"Is interest in astronomy growing in Ukrainian Wikipedia, and how trustworthy is this growth?\"",
  "description": "Run Wikipedia interest research for astronomy in Ukrainian"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "<tmp>/wir-eval-xkg5q_8d/workspace/wiki-studies/astronomy-uk",
  "question": "Is interest in astronomy growing in Ukrainian Wikipedia, and how trustworthy is this growth?",
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
  "assumptions": ["Period 2024-09..2026-08 = whole months up to the last complete month; statistics use 2024-09..2026-08 so every month has a year-earlier comparison.", "Views are agent=user (declared bots and crawlers excluded), all devices, redirects carrying ≥1% of an article's views included.", "Weights: momentum=0.35, relative=0.25, size=0.25, trust=0.15.", "Topic 'astronomy' = Wik
… [389 chars cut]
```
</details>

**Assistant:** **На жаль, інтерес до астрономії на україномовній Вікіпедії **падає**, а не зростає**: -61,7% рік-до-року, довіра **висока**.

- **Українська мова**: падіння, -61,7% (0 з 12 місяців перевищило рівень минулого року), довіра висока — жоден місяць останнього року не перевищив відповідний місяць минулого року (статистично значуще, p=0,002).
- **Сезонність**: стійкий сплеск у вересні (~2,3× раза на рік), що логічно для навчальної тематики.
- Уся украйнськомовна Вікіпедія також падає на -24,6%, але астрономія падає **швидше** — на -42,4% відносно тренду всієї платформи.

**Обмеження:** інтерес до статті ≠ бажання платити за курс; украйнськомовна аудиторія — це переважно читачі з України (65%), США (11%), Польщі (4%). Дані якісні, але обсяг переглядів невеликий (559/місяць у середньому).   

**Наступні кроки:** 
1. Перевірте, чи падіння — це глобальний тренд (чи астрономія падає на **всіх** Вікіпедіях).
2. Розглядайте інші показники попиту (соціальні мережі, пошукові запити, опитування користувачів), а не тільки перегляди на Вікіпедії.

Якщо вам потрібен письмовий звіт з графіками, я можу його створити.

### Final answer

**На жаль, інтерес до астрономії на україномовній Вікіпедії **падає**, а не зростає**: -61,7% рік-до-року, довіра **висока**.

- **Українська мова**: падіння, -61,7% (0 з 12 місяців перевищило рівень минулого року), довіра висока — жоден місяць останнього року не перевищив відповідний місяць минулого року (статистично значуще, p=0,002).
- **Сезонність**: стійкий сплеск у вересні (~2,3× раза на рік), що логічно для навчальної тематики.
- Уся украйнськомовна Вікіпедія також падає на -24,6%, але астрономія падає **швидше** — на -42,4% відносно тренду всієї платформи.

**Обмеження:** інтерес до статті ≠ бажання платити за курс; украйнськомовна аудиторія — це переважно читачі з України (65%), США (11%), Польщі (4%). Дані якісні, але обсяг переглядів невеликий (559/місяць у середньому).   

**Наступні кроки:** 
1. Перевірте, чи падіння — це глобальний тренд (чи астрономія падає на **всіх** Вікіпедіях).
2. Розглядайте інші показники попиту (соціальні мережі, пошукові запити, опитування користувачів), а не тільки перегляди на Вікіпедії.

Якщо вам потрібен письмовий звіт з графіками, я можу його створити.
