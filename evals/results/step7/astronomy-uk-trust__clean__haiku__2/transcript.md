# astronomy-uk-trust — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.0362, duration: 25.8 s, tokens in/out: 28/1413 (cache read 63260)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "astronomy uk.wikipedia"
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
  "command": "cd <tmp>/wir-eval-dlqbsszf/workspace/.claude/skills/wikipedia-interest-research && ./scripts/wir study new --topic \"astronomy\" --langs uk --question \"Is interest in astronomy growing on Ukrainian Wikipedia, and how trustworthy is this trend?\""
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "wiki-studies/astronomy-uk",
  "question": "Is interest in astronomy growing on Ukrainian Wikipedia, and how trustworthy is this trend?",
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
  "next_steps": ["Answer using only numbers from this outpu
… [239 chars cut]
```
</details>

**Assistant:** **Ні, інтерес до астрономії на україномовній Вікіпедії знижується**: спад на 61,7% рік до року, довіра висока.

- **Українська Вікіпедія**: вердикт — спад, −61,7% зміни рік до року (0 з 12 місяців перевищили показники року назад), довіра висока — всі останні 12 місяців були нижче за відповідні місяці минулого року (p=0,002).
- **Сезонність**: виражена — піки в вересні (приблизно 2,3× за кожен рік).
- Цілком видання українськомовної Вікіпедії впало на 24,6%; відносно цього падіння астрономія впала ще на 42,4% — це падіння, специфічне для теми, не загальнов Вікіпедії.

**Обмеження:** читання Вікіпедії — не показник готовності платити за курс; в основному українські читачі (65%), але є й читачі з США (11%), Польщі (4%). Дані за період вересень 2024 р. — серпень 2026 р.

**Висновок для вашого рішення:** за даними Вікіпедії явно ніяких позитивних сигналів для курсу з астрономії. Варто перевірити інші показники: запити в пошукових системах, активність у соціальних мережах, оцінки попиту в цільовій аудиторії вашого застосунку. Можу підготувати односторінковий PDF-звіт з графіками.

### Final answer

**Ні, інтерес до астрономії на україномовній Вікіпедії знижується**: спад на 61,7% рік до року, довіра висока.

- **Українська Вікіпедія**: вердикт — спад, −61,7% зміни рік до року (0 з 12 місяців перевищили показники року назад), довіра висока — всі останні 12 місяців були нижче за відповідні місяці минулого року (p=0,002).
- **Сезонність**: виражена — піки в вересні (приблизно 2,3× за кожен рік).
- Цілком видання українськомовної Вікіпедії впало на 24,6%; відносно цього падіння астрономія впала ще на 42,4% — це падіння, специфічне для теми, не загальнов Вікіпедії.

**Обмеження:** читання Вікіпедії — не показник готовності платити за курс; в основному українські читачі (65%), але є й читачі з США (11%), Польщі (4%). Дані за період вересень 2024 р. — серпень 2026 р.

**Висновок для вашого рішення:** за даними Вікіпедії явно ніяких позитивних сигналів для курсу з астрономії. Варто перевірити інші показники: запити в пошукових системах, активність у соціальних мережах, оцінки попиту в цільовій аудиторії вашого застосунку. Можу підготувати односторінковий PDF-звіт з графіками.
