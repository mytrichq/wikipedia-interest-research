# astronomy-uk-trust — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0356, duration: 31.4 s, tokens in/out: 28/1441 (cache read 63104)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "topic=astronomy language=Ukrainian"
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
  "command": "<tmp>/wir-eval-jlb9pd4m/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk --question \"Чи зростає інтерес до астрономії в україномовній Wikipedia?\""
}
```

<details><summary>Tool result</summary>

```
wir: requests — 20 network, 15 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "wiki-studies/astronomy-uk",
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
  "next_steps": ["Answer using only numbers from this output; name the trust level and its reasons.", "Say plainly when a languag
… [170 chars cut]
```
</details>

**Assistant:** **Вибачте, але інтерес до астрономії в україномовній Wikipedia **не зростає** — скоріше падає**: -61,7% за рік, trust **High**.

**Детально:**

- **Українська Wikipedia**: різко падає на -61,7% за рік (-42,4% відносно до загального зменшення користування виданням), довіра **High** — жоден із 12 останніх місяців не перевищив відповідний місяць минулого року (p=0.002, вельми значущо).
  - Щоправда, є стійкий сезонний піки в вересні (≈2,3× вище за звичайне).
  - Середньомісячне значення: 559 переглядів; 65% читачів з України, 11% з США, 4% з Польщі.

**Чому це не надійна база для курсу:**

1. **Дуже крутий спад** — читачі англійської-мовної Wikipedia менше цікавляться астрономією, а тут падіння в 2,5 рази більше, ніж у самому виданні.
2. **Вересневий пік** — це не зростання інтересу, а сезонність, пов'язана зі школою. На осіб, які шукають освітній контент, це вказує, але не на стійкий попит.
3. **Малий обсяг** — 559 переглядів/місяць — невелика аудиторія для висновків про жанр.

**Далі:** Перш ніж додавати курс, перевірте: (1) чи є попит на українськомовні освітні ресурси з астрономії поза Wikipedia (пошук, соцмережі, локальні опитування); (2) чи є в вас контент-лідер, який міг би утримати аудиторію. Гугл Тренди або пряме опитування користувачів дали б більш надійну картину.

Якщо потрібен детальний звіт (PDF з графіками), можу його підготувати.

### Final answer

**Вибачте, але інтерес до астрономії в україномовній Wikipedia **не зростає** — скоріше падає**: -61,7% за рік, trust **High**.

**Детально:**

- **Українська Wikipedia**: різко падає на -61,7% за рік (-42,4% відносно до загального зменшення користування виданням), довіра **High** — жоден із 12 останніх місяців не перевищив відповідний місяць минулого року (p=0.002, вельми значущо).
  - Щоправда, є стійкий сезонний піки в вересні (≈2,3× вище за звичайне).
  - Середньомісячне значення: 559 переглядів; 65% читачів з України, 11% з США, 4% з Польщі.

**Чому це не надійна база для курсу:**

1. **Дуже крутий спад** — читачі англійської-мовної Wikipedia менше цікавляться астрономією, а тут падіння в 2,5 рази більше, ніж у самому виданні.
2. **Вересневий пік** — це не зростання інтересу, а сезонність, пов'язана зі школою. На осіб, які шукають освітній контент, це вказує, але не на стійкий попит.
3. **Малий обсяг** — 559 переглядів/місяць — невелика аудиторія для висновків про жанр.

**Далі:** Перш ніж додавати курс, перевірте: (1) чи є попит на українськомовні освітні ресурси з астрономії поза Wikipedia (пошук, соцмережі, локальні опитування); (2) чи є в вас контент-лідер, який міг би утримати аудиторію. Гугл Тренди або пряме опитування користувачів дали б більш надійну картину.

Якщо потрібен детальний звіт (PDF з графіками), можу його підготувати.
