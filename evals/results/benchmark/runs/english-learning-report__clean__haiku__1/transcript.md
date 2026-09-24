# english-learning-report — env `clean`, model `haiku`

- Tool calls: **5**, skills used: ['wikipedia-interest-research']
- Cost: $0.0688, duration: 58.4 s, tokens in/out: 51/4059 (cache read 152593)

## Turn 1

> **User:** Ми створюємо застосунок для вивчення мов. Порівняй інтерес до вивчення англійської в польському, турецькому, в'єтнамському, португальському та українському розділах Wikipedia і підготуй короткий звіт: які аудиторії варто дослідити наступними й чому?

**Assistant:** Це цікава задача для мові-навчального застосунку. Я використаю навичку аналізу Вікіпедії, щоб порівняти інтерес до вивчення англійської мови в цих п'яти мовних розділах.

**Tool call — Skill**
```json
{
  "skill": "wikipedia-interest-research",
  "args": "\nTopics: \"English language learning\", \"English as a foreign language\", \"Learning English\"\nLanguages: Polish, Turkish, Vietnamese, Portuguese, Ukrainian\nOutput: one-page PDF report\nFocus: audience interest trends, seasonal patterns, regional opportunities for language learning app\n"
}
```

<details><summary>Tool result</summary>

```
Launching skill: wikipedia-interest-research
```
</details>

**Assistant:** Розумію, прошу хвилину. Я запущу дослідження порівняння інтересу до вивчення англійської мови в цих п'яти розділах Вікіпедії.

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-_q3e97xp/workspace/.claude/skills/wikipedia-interest-research/scripts/wir study new --topic \"English\" --langs uk,pl,tr,vi,pt --question \"Які аудиторії варто дослідити наступними для застосунку вивчення мов?\"",
  "description": "Run Wikipedia interest research study on English language learning across five language editions"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 184 from cache, 0 retries
{
  "status": "ok",
  "study": "english-uk-pl-tr-vi-pt",
  "folder": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/english-uk-pl-tr-vi-pt",
  "question": "Які аудиторії варто дослідити наступними для застосунку вивчення мов?",
  "period": "2024-09..2026-08",
  "stats_window": "2024-09..2026-08",
  "results": [
    {
      "key": "uk",
      "articles": ["Англійська мова"],
      "verdict": "declining",
      "yoy_pct": -37.3,
      "months_up_of_12": 0,
      "avg_monthly_views": 6730,
      "per_million_views": 118.8,
      "relative_yoy_pct": -10.5,
      "relative_verdict": "declining",
      "edition_yoy_pct": -24.6,
      "trust": "High (100)",
      "trust_reasons": ["0 of 12 months were above the same month a year earlier (p=0.002)."]
    },
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
    
… [3591 chars cut]
```
</details>

**Assistant:** Дані розрахунку готові. Аналізую результати та готую звіт.

**Tool call — Read**
```json
{
  "file_path": "<tmp>/wir-eval-_q3e97xp/workspace/.claude/skills/wikipedia-interest-research/assets/narrative_template.md"
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
  "file_path": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/narrative_english_market.md",
  "content": "# В'єтнамська аудиторія — найсильніша для запуску, турецька та українська потребують окремого дослідження\n\nВ'єтнамська Вікіпедія є найперспективнішим ринком з найвищою абсолютною кількістю переглядів (12,478 на місяць) і стабільним інтересом відносно свого розділу (+2,9%), тоді як турецька та польська аудиторії також показують стабільність, але турецька відповідає прихованій аудиторії з Туреччини.\n\n## Findings\n\n- **В'єтнамська (першість за рейтингом)**: найбільше переглядів (12,478/місяць), стабільна відносно видання (+2,9%), но абсолютно знижується на 24,0%. Реальна аудиторія з В'єтнаму прихована Wikimedia, тому її розмір невідомий.\n- **Турецька (стабільна, прихована аудиторія)**: незважаючи на 13,5% абсолютне зниження, відносно видання стабільна (+5,3%), з 7,080 переглядами на місяць. Турецька аудиторія з Туреччини невідома через захист країни.\n- **Українська (різкий спад)**: найгіршпий результат з падінням на 37,3% — більше, ніж середнє падіння розділу (24,6%). Висока довіра, але тренд критичний для розробки продукту на українському ринку.\n- **Португальська та польська**: португальська стабільна лише статистично (2 місяці з 12 вище), польська стабільна відносно видання. Польська — найменший потенціал (50,1 рейтингу).\n\n## Next steps\n\n- **Запустити в В'єтнамі**: перевірити завдання користувачів через фокус-групи й скопіювати тренування контенту з англійської Вікіпедії, щоб підтвердити, що спад є глобальним.\n- **Проаналізувати Туреччину окремо**: скористатися локальними источниками даних (Google Trends, мобільні аналітики) для з'ясування справжнього інтересу до вивчення англійської в Туреччині (Wikimedia приховує основну аудиторію).\n- **Дослідити падіння на українському ринку**: визначити, чи це глобальне зниження інтересу до вивчення мов чи вибуття користувачів через政策/конфлікти.\n"
}
```

<details><summary>Tool result</summary>

```
File created successfully at: <tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/narrative_english_market.md (file state is current in your context — no need to Read it back)
```
</details>

**Tool call — Bash**
```json
{
  "command": "<tmp>/wir-eval-_q3e97xp/workspace/.claude/skills/wikipedia-interest-research/scripts/wir report english-uk-pl-tr-vi-pt --narrative wiki-studies/narrative_english_market.md --lang uk",
  "description": "Generate PDF report from the narrative"
}
```

<details><summary>Tool result</summary>

```
wir: requests — 0 network, 0 from cache, 0 retries
{
  "status": "ok",
  "study": "english-uk-pl-tr-vi-pt",
  "report_language": "uk",
  "pdf": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/english-uk-pl-tr-vi-pt/report.pdf",
  "pages": 1,
  "summary_md": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/english-uk-pl-tr-vi-pt/summary.md",
  "charts": {
    "dynamics": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/english-uk-pl-tr-vi-pt/charts/dynamics.png",
    "change": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/english-uk-pl-tr-vi-pt/charts/change.png"
  },
  "data_csv": "<tmp>/wir-eval-_q3e97xp/workspace/wiki-studies/english-uk-pl-tr-vi-pt/data/monthly.csv",
  "narrative": "from file",
  "factcheck": {
    "ok": true,
    "numbers_checked": 9
  },
  "limitations_for_chat": ["Інтерес до статті в енциклопедії ≠ готовність платити: це підказка, що перевіряти, а не доказ попиту.", "Мовний розділ ≠ країна. Читачі за країнами: Українська: Україна 65%, Сполучені Штати 11%, Польща 4%; Польська: Польща 87%, Сполучені Штати 4%, Німеччина 2%; Португальська: Бразилія 74%, Португалія 9%, Сполучені Штати 9%.", "Турецька: Wikimedia приховує читачів з Туреччина (список захисту приватності), тож розподіл за країнами неповний.", "Вʼ
… [511 chars cut]
```
</details>

**Assistant:** ## Результати дослідження

**В'єтнамська аудиторія — найперспективніша для запуску**: стабільний інтерес відносно видання (+2,9%), найвищий трафік (12,478 переглядів/місяць), висока довіра. Турецька варто дослідити окремо — приховані дані про аудиторію з Туреччини. Українській знадобиться особливий аналіз через різкий спад (-37,3%).

### За мовними розділами:

- **В'єтнамська** (1-й за рейтингом): стабільна відносно видання (+2,9% z 12 міс.), найбільше переглядів (12,478/міс.), довіра висока — найсильніша для першого запуску.
- **Турецька** (стабільна з прихованою аудиторією): стабільна відносно видання (+5,3%), 7,080 переглядів/місяць, довіра середня — Wikimedia приховує читачів з Туреччини через захист приватності, реальний попит невідомий.
- **Польська**: стабільна відносно видання (-9,9% ≈ ±10%), 8,087 переглядів/місяць, довіра середня — найменший потенціал (50,1 балу рейтингу).
- **Португальська**: неясна динаміка (лише 2 з 12 місяців позитивні), 9,178 переглядів/місяць, довіра висока — потребує подальшої валідації.
- **Українська**: різко падає на 37,3% (більше, ніж видання на -24,6%), 6,730 переглядів/місяць, довіра висока — критичний сигнал для українського ринку.

### Сезонність / события
Специфічних піків або новинних подій не виявлено.

**Обмеження:** Інтерес до статті ≠ готовність платити — це підказка для перевірки, а не доказ попиту. Мовний розділ ≠ країна: українська читачі 65% з України; португальська — 74% з Бразилії. Турецька та в'єтнамська аудиторії з їхніх країн приховані Wikimedia, тому справжні розміри невідомі.

### Рекомендації для наступного кроку:
1. **В'єтнамський ринок** — запустити бета-версію, перевірити завдання користувачів через фокус-групи
2. **Туреччина** — скопіювати тренування контенту, перевірити інтерес через Google Trends або мобільні аналітики
3. **Україна** — розібратися, чи це глобальний тренд зниження інтересу до вивчення мов чи локальні фактори

---

📄 **PDF-звіт готов:** `wiki-studies/english-uk-pl-tr-vi-pt/report.pdf`  
Також доступні: графіки динаміки, дані за місяцями у CSV для вашого аналізу.

### Final answer

## Результати дослідження

**В'єтнамська аудиторія — найперспективніша для запуску**: стабільний інтерес відносно видання (+2,9%), найвищий трафік (12,478 переглядів/місяць), висока довіра. Турецька варто дослідити окремо — приховані дані про аудиторію з Туреччини. Українській знадобиться особливий аналіз через різкий спад (-37,3%).

### За мовними розділами:

- **В'єтнамська** (1-й за рейтингом): стабільна відносно видання (+2,9% z 12 міс.), найбільше переглядів (12,478/міс.), довіра висока — найсильніша для першого запуску.
- **Турецька** (стабільна з прихованою аудиторією): стабільна відносно видання (+5,3%), 7,080 переглядів/місяць, довіра середня — Wikimedia приховує читачів з Туреччини через захист приватності, реальний попит невідомий.
- **Польська**: стабільна відносно видання (-9,9% ≈ ±10%), 8,087 переглядів/місяць, довіра середня — найменший потенціал (50,1 балу рейтингу).
- **Португальська**: неясна динаміка (лише 2 з 12 місяців позитивні), 9,178 переглядів/місяць, довіра висока — потребує подальшої валідації.
- **Українська**: різко падає на 37,3% (більше, ніж видання на -24,6%), 6,730 переглядів/місяць, довіра висока — критичний сигнал для українського ринку.

### Сезонність / события
Специфічних піків або новинних подій не виявлено.

**Обмеження:** Інтерес до статті ≠ готовність платити — це підказка для перевірки, а не доказ попиту. Мовний розділ ≠ країна: українська читачі 65% з України; португальська — 74% з Бразилії. Турецька та в'єтнамська аудиторії з їхніх країн приховані Wikimedia, тому справжні розміри невідомі.

### Рекомендації для наступного кроку:
1. **В'єтнамський ринок** — запустити бета-версію, перевірити завдання користувачів через фокус-групи
2. **Туреччина** — скопіювати тренування контенту, перевірити інтерес через Google Trends або мобільні аналітики
3. **Україна** — розібратися, чи це глобальний тренд зниження інтересу до вивчення мов чи локальні фактори

---

📄 **PDF-звіт готов:** `wiki-studies/english-uk-pl-tr-vi-pt/report.pdf`  
Також доступні: графіки динаміки, дані за місяцями у CSV для вашого аналізу.
