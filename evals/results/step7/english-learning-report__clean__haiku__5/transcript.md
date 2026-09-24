# english-learning-report — env `clean`, model `haiku`

- Tool calls: **6**, skills used: ['wikipedia-interest-research']
- Cost: $0.0743, duration: 66.8 s, tokens in/out: 60/4377 (cache read 184124)

## Turn 1

> **User:** Ми створюємо застосунок для вивчення мов. Порівняй інтерес до вивчення англійської в польському, турецькому, в'єтнамському, португальському та українському розділах Wikipedia і підготуй короткий звіт: які аудиторії варто дослідити наступними й чому?

**Assistant:** Я використаю навичку дослідження інтересу на Wikipedia для порівняння інтересу до вивчення англійської в цих мовних розділах.

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "{\"topic\": \"English language learning\", \"languages\": [\"pl\", \"tr\", \"vi\", \"pt\", \"uk\"], \"focus\": \"audience_interest_comparison\", \"output\": \"report_with_recommendations\"}"
}
```

<details><summary>Tool result</summary>

```
Launching skill: wikipedia-interest-research
```
</details>

**Assistant:** Розумію. Я порівняю інтерес до вивчення англійської мови в цих п'яти мовних розділах Wikipedia. Спочатку запущу дослідження.

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-fsbxjsa5/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"Q1860\" --langs pl,tr,vi,pt,uk --question \"Який інтерес до вивчення англійської мови в цих аудиторіях, які з них варто дослідити наступними?\" 2>&1"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 181 from cache, 0 retries
{
  "status": "ok",
  "study": "q1860-pl-tr-vi-pt-uk",
  "folder": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk",
  "question": "Який інтерес до вивчення англійської мови в цих аудиторіях, які з них варто дослідити наступними?",
  "period": "2024-09..2026-08",
  "stats_window": "2024-09..2026-08",
  "results": [
    {
      "key": "pl",
      "articles": ["Język angielski"],
      "verdict": "declining",
      "yoy_pct": -19.4,
      "months_up_of_12": 2,
      "avg_monthly_views": 8087,
      "per_million_views": 43.04,
      "relative_yoy_pct": -9.9,
      "relative_verdict": "stable",
      "relative_note": "-9.9% relative to the edition is within ±10%: call it stable relative to the edition, not growth or decline.",
      "edition_yoy_pct": -8.8,
      "trust": "Medium (65)",
      "trust_reasons": ["The whole edition's traffic changed -9%; relative to it the topic moved -10% (absolute: -19%)."]
    },
    {
      "key": "tr",
      "articles": ["İngilizce"],
      "verdict": "declining",
      "yoy_pct": -13.5,
      "months_up_of_12": 1,
      "avg_monthly_views": 7080,
      "per_million_views": 65.27,
      "relative_yoy_pct": 5.3,
      "relative_verdict": "stable",
      "relative_note": "+5.3% relative to the edition is within ±10%: call it stable relative to the edition, not growth or decline.",
      "edition_yoy_pct": -16.3,
      "trus
… [3611 chars cut]
```
</details>

**Assistant:** Отримав результати. Всі п'ять аудиторій показують спад інтересу до англійської мови, але з різною динамікою. Тепер підготую короткий звіт.

**Основні знахідки**: інтерес до статей про англійську мову падає на всіх п'яти мовних розділах за останні 24 місяці, проте найбільший спад в українській (−37,3%) та португальській (−33,7%) аудиторіях, де довіра до цих даних висока.

- **В'єтнамська Вікіпедія**: спад 24,0% рік на рік, але належить до топ-3 найцікавіших аудиторій за потенціалом (255 переглядів на мільйон). Однак Wikimedia приховує основну аудиторію з В'єтнаму, тому справжній розмір невідомий — середня довіра.
- **Українська Вікіпедія**: найглибший спад (−37,3%) із високою довірою. Жоден місяць за останній рік не виконав план попереднього року. Показує 119 переглядів на мільйон — друга за розміром.
- **Португальська Вікіпедія**: −33,7% за останній рік, висока довіра. Читачі переважно з Бразилії (74%). Лише 2 місяці з 12 перевищили минулорічні показники.
- **Турецька Вікіпедія**: −13,5%, але розмір аудиторії помітно більший у відносному вимірі. Wikimedia приховує читачів з Туреччини — справжня величина невідома. Середня довіра.
- **Польська Вікіпедія**: −19,4%, найменший спад у групі. Найстабільніша на тлі повільного падіння власного розділу (−8,8%). Середня довіра.

**Обмеження:** данні відображають інтерес до статей про мову, а не готовність вчити її; турецька та в'єтнамська аудиторії непрозорі з причин захисту даних — реальні цифри можуть бути набагато більшими.

**Рекомендація для подальшого дослідження:**
1. **В'єтнамська** — попри спад, найбільший потенціал за розміром (якщо основна аудиторія приховується). Варто дослідити мотиви вивчення англійської в цій аудиторії безпосередньо.
2. **Українська** — висока довіра до спаду, можливо через зниження мотивації учнів. Варто розібратися, чи це технічне падіння переглядів, чи справді вибір інших ресурсів.
3. **Португальська** — найсильніший спад із високою довіою, переважно бразильська аудиторія. Бразилія — велика англомовна спільнота, це різкий спад варто перевірити.

Тепер побудую PDF звіт.

**Tool call — Bash**
```json
{
  "command": "cp <tmp>/wir-eval-fsbxjsa5/workspace/.claude/skills/wikipedia-interest-research/assets/narrative_template.md <tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/narrative.md"
}
```

<details><summary>Tool result</summary>

```
Claude requested permissions to write to <tmp>/wir-eval-fsbxjsa5/workspace/.claude/skills/wikipedia-interest-research/assets/narrative_template.md, but you haven't granted it yet.
```
</details>

**Tool call — Read**
```json
{
  "file_path": "<tmp>/wir-eval-fsbxjsa5/workspace/.claude/skills/wikipedia-interest-research/assets/narrative_template.md"
}
```

<details><summary>Tool result</summary>

```
1	# Headline
2	One sentence that answers the user's question, with the main number and the trust level.
3	
4	## Findings
5	- Up to 4 short bullets. Use only numbers printed by `scripts/wir study show <id>`.
6	- Mention seasonality, one-off events or missing articles when the study reports them.
7	
8	## Next steps
9	- Up to 3 concrete things to research or validate next, and why.
10	
```
</details>

**Tool call — Write**
```json
{
  "file_path": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/narrative.md",
  "content": "# Інтерес до англійської мови падає у всіх п'яти аудиторіях, але в'єтнамська залишається найбільшою за потенціалом\n\nІнтерес до статей про англійську мову спадає на польській (−19,4%), турецькій (−13,5%), в'єтнамській (−24,0%), португальській (−33,7%) та українській (−37,3%) Вікіпедіях рік на рік. В'єтнамська та українська аудиторії варто дослідити наступними.\n\n## Findings\n- **В'єтнамська Вікіпедія** лідирує за розміром (255 переглядів на мільйон) попри спад на 24,0%, але Wikimedia приховує основну аудиторію з В'єтнаму — справжній розмір невідомий, довіра середня.\n- **Українська Вікіпедія** показує найглибший спад (−37,3% з високою довірою), жоден месяць не перевищив минулорічні показники, при цьому аудиторія друга за розміром (119 переглядів на мільйон, 65% від України).\n- **Португальська Вікіпедія** демонструє −33,7% падіння з високою довірою, аудиторія переважно з Бразилії (74%), лише 2 місяці з 12 виконали річні плани.\n- **Турецька та польська** показують менший спад (−13,5% та −19,4%), але в турецькій основна аудиторія прихована від Wikimedia — реальний розмір невідомий.\n\n## Next steps\n- Досліджувати в'єтнамську аудиторію напряму: незважаючи на прихованість даних, вона залишається найбільшою за потенціалом та варто розібратися з причинами спаду в контексті зростання інтернету у В'єтнамі.\n- Проаналізувати українську аудиторію: висока довіра до негативного тренду з 2024 року вказує на справжню втрату інтересу, варто перевірити, чи читачі перейшли на інші ресурси.\n- Валідувати португальське падіння в Бразилії через пряме опитування або фокус-групи, оскільки спад −33,7% з високою довірою може вказати на зміну навчальних стратегій або конкуренцію платформ.\n"
}
```

<details><summary>Tool result</summary>

```
File created successfully at: <tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/narrative.md (file state is current in your context — no need to Read it back)
```
</details>

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-fsbxjsa5/workspace/.claude/skills/wikipedia-interest-research/scripts/wir report q1860-pl-tr-vi-pt-uk --narrative wiki-studies/q1860-pl-tr-vi-pt-uk/narrative.md --lang uk 2>&1"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 0 from cache, 0 retries
{
  "status": "ok",
  "study": "q1860-pl-tr-vi-pt-uk",
  "report_language": "uk",
  "pdf": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/report.pdf",
  "pages": 1,
  "summary_md": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/summary.md",
  "charts": {
    "dynamics": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/charts/dynamics.png",
    "change": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/charts/change.png"
  },
  "data_csv": "<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/data/monthly.csv",
  "narrative": "from file",
  "factcheck": {
    "ok": true,
    "numbers_checked": 10
  },
  "generated": "2026-09-24T10:25:08"
}
```
</details>

**Assistant:** Звіт готов!

**PDF звіт:** `<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/report.pdf`

## Рекомендація для наступних кроків:

1. **В'єтнамська аудиторія** — попри спад на 24%, залишається найбільшою за потенціалом з 255 переглядами на мільйон. Основні читачі прихованої, але це важлива ринок для вивчення англійської. Варто дослідити, чи читачи переходять на інші платформи.

2. **Українська аудиторія** — найглибший спад (−37,3%) з **високою довірою** до цифри. Жоден місяць за останній рік не перевищив показники попередніх років — це справжня втрата інтересу. Варто перевірити, чи причина в освітній політиці, змінах навчальних ресурсів чи пріоритетів користувачів.

3. **Португальська аудиторія** — спад на 33,7% із **високою довірою**, переважно з Бразилії (74%). Це значна англомовна спільнота, тому такий спад може вказати на конкуренцію платформ або зміну освітніх тенденцій на латиноамериканському ринку.

Турецька та польська показують стабільність відносно до власних мовних розділів, тому може йти мова про загальне падіння трафіку, а не втрату інтересу саме до англійської.

### Final answer

Звіт готов!

**PDF звіт:** `<tmp>/wir-eval-fsbxjsa5/workspace/wiki-studies/q1860-pl-tr-vi-pt-uk/report.pdf`

## Рекомендація для наступних кроків:

1. **В'єтнамська аудиторія** — попри спад на 24%, залишається найбільшою за потенціалом з 255 переглядами на мільйон. Основні читачі прихованої, але це важлива ринок для вивчення англійської. Варто дослідити, чи читачи переходять на інші платформи.

2. **Українська аудиторія** — найглибший спад (−37,3%) з **високою довірою** до цифри. Жоден місяць за останній рік не перевищив показники попередніх років — це справжня втрата інтересу. Варто перевірити, чи причина в освітній політиці, змінах навчальних ресурсів чи пріоритетів користувачів.

3. **Португальська аудиторія** — спад на 33,7% із **високою довірою**, переважно з Бразилії (74%). Це значна англомовна спільнота, тому такий спад може вказати на конкуренцію платформ або зміну освітніх тенденцій на латиноамериканському ринку.

Турецька та польська показують стабільність відносно до власних мовних розділів, тому може йти мова про загальне падіння трафіку, а не втрату інтересу саме до англійської.
