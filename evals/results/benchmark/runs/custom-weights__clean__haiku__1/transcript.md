# custom-weights — env `clean`, model `haiku`

- Tool calls: **3**, skills used: ['wikipedia-interest-research']
- Cost: $0.0999, duration: 61.6 s, tokens in/out: 46/3224 (cache read 119685)

## Turn 1

> **User:** Порівняй інтерес до астрономії в українській, польській і чеській Wikipedia.

**Assistant:** I'll compare the audience interest in astronomy across Ukrainian, Polish, and Czech Wikipedia using pageview data.

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "astronomy Ukrainian Polish Czech Wikipedia"
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
  "command": "<tmp>/wir-eval-yxnv7or0/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"astronomy\" --langs uk,pl,cs --question \"Порівняй інтерес до астрономії в українській, польській і чеській Wikipedia.\"",
  "description": "Run Wikipedia interest research for astronomy across three languages"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 13 network, 83 from cache, 0 retries
{
  "status": "ok",
  "study": "astronomy-uk-pl-cs",
  "folder": "<tmp>/wir-eval-yxnv7or0/workspace/wiki-studies/astronomy-uk-pl-cs",
  "question": "Порівняй інтерес до астрономії в українській, польській і чеській Wikipedia.",
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
    },
    {
      "key": "pl",
      "articles": ["Astronomia"],
      "verdict": "declining",
      "yoy_pct": -30.5,
      "months_up_of_12": 0,
      "avg_monthly_views": 1431,
      "per_million_views": 7.41,
      "relative_yoy_pct": -21.8,
      "relative_verdict": "declining",
      "edition_yoy_pct": -8.8,
      "trust": "High (70)",
      "trust_reasons": ["One-off months (2025-11 ×3.2) were set to a typical level, but they show the comparison year was unusual, so part of the change is a return to normal.", "32% of requests were flagged as automated (excluded; a warning sign)."
… [1898 chars cut]
```
</details>

**Assistant:** **Інтерес до астрономії скорочується на всіх трьох мовах, найбільше на українській**: падіння, –61,7% рік до року, висока довіра.

- **Українська Вікіпедія**: падіння, –61,7% (0 з 12 місяців вище за минулий рік), висока довіра (100) — жоден місяць не перевищив показник року раніше; порівняння статистично значиме.
- **Польська Вікіпедія**: падіння, –30,5% (0 з 12 місяців вище), висока довіра (70) — листопад 2025 показав одноразовий сплеск (×3,2), але це скоріше означає, що період порівняння був нетиповим; також 32% запитів — це автоматизовані запити.
- **Чеська Вікіпедія**: падіння, –33,2% (1 з 12 місяців вище), висока довіра (90) — 34% запитів автоматизовані.

Відносно до траєкторії кожної мовної Вікіпедії:
- Українська: скоротилась на –24,6%, астрономія падає ще швидше (–42,4% відносно видання).
- Польська: скоротилась на –8,8%, астрономія падає швидше (–21,8% відносно видання).
- Чеська: скоротилась на –12,6%, астрономія падає швидше (–16,9% відносно видання).

**Характеристики:**
- Найбільше читачів на польській (1 431 переглядів на місяць), потім українська (559) і чеська (516).
- На українській щороку — піки у вересні (близько ×2,3 вище).
- Польська і чеська мають попередження про ботів: відповідно 32% і 34% запитів помічені як автоматизовані.

**Обмеження:** інтерес до статті ≠ реальний інтерес до науки (мож­ливо, змінились навички пошуку або джерела); мовна Вікіпедія ≠ країна (українська: 65% з України, 11% з США; польська: 87% з Польщі; чеська: 80% з Чехії).

**Далі:** варто перевірити, чи пов'язане падіння з: навчальним циклом (коли учні кидають гуглити астрономію), зміною медіаспоживання (Youtube, TikTok про космос), чи справді загальним відтоком від енциклопедій.

Хочете мати це у вигляді звіту?

### Final answer

**Інтерес до астрономії скорочується на всіх трьох мовах, найбільше на українській**: падіння, –61,7% рік до року, висока довіра.

- **Українська Вікіпедія**: падіння, –61,7% (0 з 12 місяців вище за минулий рік), висока довіра (100) — жоден місяць не перевищив показник року раніше; порівняння статистично значиме.
- **Польська Вікіпедія**: падіння, –30,5% (0 з 12 місяців вище), висока довіра (70) — листопад 2025 показав одноразовий сплеск (×3,2), але це скоріше означає, що період порівняння був нетиповим; також 32% запитів — це автоматизовані запити.
- **Чеська Вікіпедія**: падіння, –33,2% (1 з 12 місяців вище), висока довіра (90) — 34% запитів автоматизовані.

Відносно до траєкторії кожної мовної Вікіпедії:
- Українська: скоротилась на –24,6%, астрономія падає ще швидше (–42,4% відносно видання).
- Польська: скоротилась на –8,8%, астрономія падає швидше (–21,8% відносно видання).
- Чеська: скоротилась на –12,6%, астрономія падає швидше (–16,9% відносно видання).

**Характеристики:**
- Найбільше читачів на польській (1 431 переглядів на місяць), потім українська (559) і чеська (516).
- На українській щороку — піки у вересні (близько ×2,3 вище).
- Польська і чеська мають попередження про ботів: відповідно 32% і 34% запитів помічені як автоматизовані.

**Обмеження:** інтерес до статті ≠ реальний інтерес до науки (мож­ливо, змінились навички пошуку або джерела); мовна Вікіпедія ≠ країна (українська: 65% з України, 11% з США; польська: 87% з Польщі; чеська: 80% з Чехії).

**Далі:** варто перевірити, чи пов'язане падіння з: навчальним циклом (коли учні кидають гуглити астрономію), зміною медіаспоживання (Youtube, TikTok про космос), чи справді загальним відтоком від енциклопедій.

Хочете мати це у вигляді звіту?

## Turn 2

> **User:** Для нас темп росту важливіший за розмір аудиторії. Перерахуй рейтинг.

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-yxnv7or0/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study update astronomy-uk-pl-cs --weights momentum=0.5,relative=0.25,size=0.1,trust=0.15",
  "description": "Recalculate ranking prioritizing growth over audience size"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 93 from cache, 0 retries
{
  "status": "ok",
  "changes": ["weights -> momentum=0.5,relative=0.25,size=0.1,trust=0.15"],
  "study": "astronomy-uk-pl-cs",
  "folder": "<tmp>/wir-eval-yxnv7or0/workspace/wiki-studies/astronomy-uk-pl-cs",
  "question": "Порівняй інтерес до астрономії в українській, польській і чеській Wikipedia.",
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
    },
    {
      "key": "pl",
      "articles": ["Astronomia"],
      "verdict": "declining",
      "yoy_pct": -30.5,
      "months_up_of_12": 0,
      "avg_monthly_views": 1431,
      "per_million_views": 7.41,
      "relative_yoy_pct": -21.8,
      "relative_verdict": "declining",
      "edition_yoy_pct": -8.8,
      "trust": "High (70)",
      "trust_reasons": ["One-off months (2025-11 ×3.2) were set to a typical level, but they show the comparison year was unusual, so part of the change is a return to normal
… [1982 chars cut]
```
</details>

**Assistant:** **З пріоритетом на темп росту:**

1. **Польська Вікіпедія** (1-е місце): score 34.9 — найменший спад (–30,5%) і висока довіра.
2. **Чеська Вікіпедія** (2-е місце): score 32.7 — спад –33,2%, але вищий за розмір видання (–16,9% відносно).
3. **Українська Вікіпедія** (3-е місце): score 29.1 — найбільший спад (–61,7%), вдвічі гірший за польську.

Польська залишилась першою, оскільки уникає найгіршої динаміки. Українська впала на останнє місце — темп падіння там критичний.

### Final answer

**З пріоритетом на темп росту:**

1. **Польська Вікіпедія** (1-е місце): score 34.9 — найменший спад (–30,5%) і висока довіра.
2. **Чеська Вікіпедія** (2-е місце): score 32.7 — спад –33,2%, але вищий за розмір видання (–16,9% відносно).
3. **Українська Вікіпедія** (3-е місце): score 29.1 — найбільший спад (–61,7%), вдвічі гірший за польську.

Польська залишилась першою, оскільки уникає найгіршої динаміки. Українська впала на останнє місце — темп падіння там критичний.
