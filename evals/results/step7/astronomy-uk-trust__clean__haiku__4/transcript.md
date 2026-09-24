# astronomy-uk-trust — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0384, duration: 29.9 s, tokens in/out: 28/1737 (cache read 63463)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

**Assistant:** Я допоможу вам дослідити інтерес до астрономії в україномовній Wikipedia. Це саме той вид аналізу, для якого призначена спеціалізована дослідницька навичка.

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

**Assistant:** Дослідимо дані про інтерес до астрономії в україномовній Wikipedia за останні 24 місяці.

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-9ndorvo8/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk --question \"Чи зростає інтерес до астрономії в україномовній Wikipedia?\"",
  "description": "Research astronomy interest trend in Ukrainian Wikipedia"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "<tmp>/wir-eval-9ndorvo8/workspace/wiki-studies/astronomy-uk",
  "question": "Чи зростає інтерес до астрономії в україномовній Wikipedia?",
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
  "nex
… [292 chars cut]
```
</details>

**Assistant:** **Інтерес до астрономії в україномовній Wikipedia **падає**, не зростає**: -61,7% в порівнянні з роком раніше, довіра **висока**.

- **Українська Wikipedia**: інтерес **падає на 61,7%** в порівнянні рік до року (0 з 12 місяців випередили аналогічний місяць минулого року), довіра **висока** — статистично значущо (p=0,002). Відносно до всієї українськомовної Wikipedia (яка сама впала на 24,6%), астрономія падає ще крутіше: на 42,4%.

- **Сезонність**: у вересні щороку спостерігається піку приблизно в 2,3 рази вищий, ніж у інші місяці (можливо, це пов'язано з початком навчального року).

- Середня кількість переглядів на місяць: 559; читачі переважно з України (65%), також зі США (11%) та Польщі (4%).

**Обмеження:** погляди на статтю ≠ готовність платити за курс; мова ≠ ринок (але українськомовна аудиторія в даному випадку переважно з України). Дані охоплюють лише 24 місяці, але тренд стійкий.

**Рекомендація:** перед розробкою курсу перевірте:
1. Чи цей спад відбувається й на інших мовах Wikipedia (порівняти з англійською, російською)?
2. Чи зацікавлені користувачі *вашого* застосунку в астрономії (директна опитування переважає мережеві тренди)?

Якщо потрібен звіт у форматі PDF для зацікавлених сторін, можу його підготувати.

### Final answer

**Інтерес до астрономії в україномовній Wikipedia **падає**, не зростає**: -61,7% в порівнянні з роком раніше, довіра **висока**.

- **Українська Wikipedia**: інтерес **падає на 61,7%** в порівнянні рік до року (0 з 12 місяців випередили аналогічний місяць минулого року), довіра **висока** — статистично значущо (p=0,002). Відносно до всієї українськомовної Wikipedia (яка сама впала на 24,6%), астрономія падає ще крутіше: на 42,4%.

- **Сезонність**: у вересні щороку спостерігається піку приблизно в 2,3 рази вищий, ніж у інші місяці (можливо, це пов'язано з початком навчального року).

- Середня кількість переглядів на місяць: 559; читачі переважно з України (65%), також зі США (11%) та Польщі (4%).

**Обмеження:** погляди на статтю ≠ готовність платити за курс; мова ≠ ринок (але українськомовна аудиторія в даному випадку переважно з України). Дані охоплюють лише 24 місяці, але тренд стійкий.

**Рекомендація:** перед розробкою курсу перевірте:
1. Чи цей спад відбувається й на інших мовах Wikipedia (порівняти з англійською, російською)?
2. Чи зацікавлені користувачі *вашого* застосунку в астрономії (директна опитування переважає мережеві тренди)?

Якщо потрібен звіт у форматі PDF для зацікавлених сторін, можу його підготувати.
