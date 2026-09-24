# astronomy-uk-trust — env `clean`, model `haiku`

- Tool calls: **2**, skills used: ['wikipedia-interest-research']
- Cost: $0.038, duration: 27.1 s, tokens in/out: 28/1646 (cache read 63578)

## Turn 1

> **User:** Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

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

**Assistant:** Беру дані про інтерес до астрономії в україномовній Вікіпедії.

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-kqs83akp/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk --question \"Чи зростає інтерес до астрономії в україномовній Вікіпедії?\"",
  "description": "Run Wikipedia interest research for astronomy in Ukrainian"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 35 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk",
  "folder": "<tmp>/wir-eval-kqs83akp/workspace/wiki-studies/astronomy-uk",
  "question": "Чи зростає інтерес до астрономії в україномовній Вікіпедії?",
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
… [356 chars cut]
```
</details>

**Assistant:** **Інтерес до астрономії в україномовній Вікіпедії падає, не зростає**: уник -61,7% у річному порівнянні, довіра висока.

- **Українська мова**: падіння -61,7% (у п'яти останніх місяців жодного місяця не перевищив показник року раніше), довіра висока — статистично значущо (p=0,002), 0 із 12 місяців показали зростання. У той час як вся український видання впала на 24,6%, астрономія впала навіть більше: відносне падіння -42,4%. Сезонність: у вересні щороку пік ≈2,3× від середнього.

**Обмеження**: інтерес до статті ≠ готовність вчитися; більшість читачів з України (65%), але видання має аудиторію по світу (США 11%, Польща 4%).

**Висновок для вашого застосунку**: дані не підтримують висновок про растучий інтерес до астрономії. Падіння на 61,7% є значущим сигналом, хоча може відбиватися специфіка когорти читачів Вікіпедії. Варто перевірити:
1. чи рівень інтересу падає й в інших мовах чи це українська специфіка;
2. чи астрономія як освітня тема привабить іншу аудиторію, ніж читачі енциклопедій.

Хочете звіт PDF чи порівняння з іншими мовами?

### Final answer

**Інтерес до астрономії в україномовній Вікіпедії падає, не зростає**: уник -61,7% у річному порівнянні, довіра висока.

- **Українська мова**: падіння -61,7% (у п'яти останніх місяців жодного місяця не перевищив показник року раніше), довіра висока — статистично значущо (p=0,002), 0 із 12 місяців показали зростання. У той час як вся український видання впала на 24,6%, астрономія впала навіть більше: відносне падіння -42,4%. Сезонність: у вересні щороку пік ≈2,3× від середнього.

**Обмеження**: інтерес до статті ≠ готовність вчитися; більшість читачів з України (65%), але видання має аудиторію по світу (США 11%, Польща 4%).

**Висновок для вашого застосунку**: дані не підтримують висновок про растучий інтерес до астрономії. Падіння на 61,7% є значущим сигналом, хоча може відбиватися специфіка когорти читачів Вікіпедії. Варто перевірити:
1. чи рівень інтересу падає й в інших мовах чи це українська специфіка;
2. чи астрономія як освітня тема привабить іншу аудиторію, ніж читачі енциклопедій.

Хочете звіт PDF чи порівняння з іншими мовами?
