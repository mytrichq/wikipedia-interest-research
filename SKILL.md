---
name: wikipedia-interest-research
description: Measures and compares audience interest in topics across Wikipedia language editions from Wikimedia pageview data, judges how trustworthy each trend is (seasonality, one-off news spikes, bots, edition-wide traffic changes), ranks languages or topics, and produces a one-page PDF report with charts. Use when a user asks whether interest in a topic is growing, wants to compare interest between languages, markets or topics, is choosing a course topic, content niche or localization language for a product, or mentions Wikipedia pageviews — even if they do not say "Wikipedia".
license: MIT
compatibility: Requires uv (https://docs.astral.sh/uv/) and internet access to wikimedia.org, wikipedia.org and wikidata.org.
metadata:
  version: "0.1.0"
---

# Wikipedia Interest Research

This skill answers questions like "is interest in X growing in Polish vs Czech Wikipedia, and can we trust it?" with real pageview data. All data work is done by the bundled CLI `scripts/wir`; your job is to pick the right inputs, run it, and explain its output honestly.

**Never** fetch pageviews yourself (WebFetch, curl, your own Python). The CLI handles the API, caching, bot filtering, statistics and fact-checking; hand-made numbers will be wrong or unverifiable.

## How to run commands

Commands are relative to this skill's directory. Call them by full path, e.g. `<skill-dir>/scripts/wir study new ...`. Run them from the user's working directory: studies are saved there in `./wiki-studies/<id>/`. Output is JSON on stdout. Request statistics and errors go to stderr.

First use on a machine, or when something fails: `scripts/wir doctor`.

## Workflow (copy this checklist)

```
- [ ] 1. Extract: topic(s), languages, period, what matters to the user, report wanted?
- [ ] 2. Run `study new` (or `study show` / `study update` for follow-ups)
- [ ] 3. Handle the status: needs_choice / missing articles / concept check
- [ ] 4. Answer in chat with the template below, using only numbers from the output
- [ ] 5. If a report is wanted: write the narrative file, run `report`, give the PDF path
```

### 1. Extract the inputs

- **Topic**: pass the English name of the encyclopedia concept ("intermittent fasting", "astronomy"). The user may write in any language; translate the concept, not the sentence. For "interest in learning <language>", use that language's article, e.g. English = `Q1860`.
- **Languages**: Wikipedia language codes, comma-separated: `uk,pl,cs`. Map names yourself: польська→pl, чеська→cs, українська→uk, португальська→pt, турецька→tr, в'єтнамська→vi. If the user named no languages, ask one short question before running.
- **Period**: default `24m` (last 24 complete months). "Останні три роки" → `36m`. Explicit ranges look like `2024-01..2026-06`.
- **What matters**: if the user cares more about growth than size (or the reverse), pass weights: `--weights growth=0.5,size=0.3,trust=0.2`. Otherwise keep the defaults.

### 2. Run the study

```bash
scripts/wir study new --topic "intermittent fasting" --langs pl,cs --question "<the user's question, verbatim>"
```

- **Compare topics** in one language: repeat `--topic` (`--topic photography --topic "computer programming" --langs uk`).
- **Several concepts as one topic**: join them with `+` (`--topic "Q1860+Q130192"`).
- **Follow-ups on the same study** (they reuse cached data, so they are fast):
  - `scripts/wir study update <id> --add-lang sk` (also `--remove-lang`, `--period 36m`, `--weights ...`, `--add-topic ...`, `--question ...`)
- **A new session or "continue our study"**: run `scripts/wir study list`, then `scripts/wir study show <id>`. Do not recreate an existing study.

### 3. Handle the status

- **`"status": "needs_choice"`**: the topic is ambiguous or not found. Show the user the options (QID + description) and ask which one they mean. Then re-run with `--topic Q308`. Do not guess silently.
- **A result with `"status": "missing"`**: that language has **no article** on the concept. Tell the user plainly; it is a content gap, not zero interest.
  - `proxy_candidates` are raw search hits. Add one only if it is clearly about the same topic and the user agrees: `study update <id> --article "pl:Głodówka lecznicza"`. It will be labelled PROXY everywhere.
- **Check the concept.** The assumptions name the Wikidata concept (e.g. `Q333 (astronomy)`). If it is not what the user means, find the right QID with `scripts/wir resolve --topic "..." --langs ...` and re-run with it.

### 4. Answer in chat

Reply in the user's language. Use language names, not codes (польська, not pl). Quote **only** numbers that appear in the command output; rounding is fine. Template:

```
**<Direct answer in one sentence>**: <verdict>, <yoy_pct>% year over year, trust <level>.

- <Language/topic>: <verdict>, <yoy_pct>% (<months_up_of_12> of 12 months above last year), trust <level> — <main trust reason>.
- (one line per result; say "no article" for missing ones)
- Seasonality / one-off events, if reported.
- The whole edition changed <edition_yoy_pct>%; relative to it the topic moved <relative_yoy_pct>%.

**Limitations:** interest in an article ≠ willingness to pay; a language ≠ a country (<readers_by_country>); <any proxy, missing article, low volume or hidden-country caveat>.

**Next:** <1–2 concrete things to validate>. I can prepare a one-page PDF report.
```

To double-check a draft answer, save it to a file and run `scripts/wir check <id> --file answer.md`. It lists any number that is not in the study.

### 5. Build the report

1. Copy `assets/narrative_template.md` to a new file and fill it in the user's language. It has three sections:
   - `# Headline`: one sentence;
   - `## Findings`: 1–4 bullets;
   - `## Next steps`: up to 3 bullets.
2. Run `scripts/wir report <id> --narrative narrative.md`.
3. Exit code 6 means the fact-check failed. The error lists the wrong numbers and the closest correct ones: fix the file and re-run. Never drop `--narrative` just to get past it.
4. Give the user the `pdf` path from the output. `summary.md` (for chat or Slack), the PNG charts and `data/monthly.csv` sit next to it.

## Reading the output

| Field | Meaning |
|---|---|
| `verdict` | `growing` / `declining` / `stable` / `unclear`, computed after removing one-off spikes |
| `yoy_pct` | Robust year-over-year change, in %: the main number to quote |
| `months_up_of_12` | How many of the last 12 months beat the same month a year earlier |
| `relative_yoy_pct`, `edition_yoy_pct` | The change relative to the whole language edition, and the edition's own change. Whole editions are shrinking, so relative figures show topic-specific interest |
| `trust` + `trust_reasons` | High / Medium / Low with the reasons. Always pass the reasons on |
| `seasonality`, `one_off_months` | Recurring peaks, e.g. September for school topics, and news events that were neutralised |
| `ranking` | Order by combined score; `strongest` names the criteria that drove it |
| `readers_by_country` | Where an edition's readers are. When it starts with `MISLEADING WITHOUT CAVEAT`, Wikimedia hides the main country: say so instead of quoting shares |

## Gotchas

- **A missing article is a finding.** For example, Polish Wikipedia has no article on intermittent fasting. Never invent a title or compare against a guess.
- **Exact names can hit the wrong concept.** "Learning English" matches a VOA program. Read the concept's description in the assumptions.
- **Low volume.** Under ~100 views/month the trust is Low. Say the data is too thin rather than calling a trend.
- **Growth driven by one event** (a conclave, a death, a film) is flagged `spike_driven` / `one_off_months`. Do not present it as rising interest.
- **A language is not a market.** Portuguese = Brazil + Portugal; English = the world. Some editions (tr, vi, ru, fa, ar, kk…) hide their main country's readers.
- **Do not add languages, topics or numbers** the user did not ask for and the tool did not return.
- **Exit codes**: 2 = bad input (the message says how to fix it), 3 = not found, 4 = API or network error, 5 = offline cache miss, 6 = fact-check failed.

## References (read only when needed)

- `references/METHODOLOGY.md`: read when the user asks how growth or trust is calculated, or challenges a verdict.
- `references/INTERPRETATION.md`: read before writing recommendations, a ranking of audiences, or a report narrative.
- `references/API_NOTES.md`: read when numbers look surprising, e.g. partial months, redirects, bots or hidden countries.
- `references/TROUBLESHOOTING.md`: read when a command exits non-zero and the message is not enough.

## Commands

| Command | Purpose |
|---|---|
| `scripts/wir study new --topic T --langs L [--period 24m] [--weights ...] [--question Q]` | Create a study: resolve, fetch, analyse, rank |
| `scripts/wir study update <id> --add-lang/--remove-lang/--period/--weights/--add-topic/--article/--question` | Change a study; only new data is downloaded |
| `scripts/wir study show <id>` / `scripts/wir study list` | Restore context without network |
| `scripts/wir report <id> --narrative FILE [--lang uk\|en]` | One-page PDF + summary.md + charts (fact-checked) |
| `scripts/wir check <id> --file FILE` | Fact-check a draft answer |
| `scripts/wir resolve --topic T --langs L` | Only map a topic to article titles and QIDs |
| `scripts/wir analyze --lang L --article A` / `scripts/wir views ...` | One-article checks |
| `scripts/wir doctor` | Environment, cache and API check |
