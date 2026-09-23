# Wikimedia API notes

Facts the skill's code relies on. Every item was checked against the live API on 2026-09-23. Read this file only when a result looks surprising or a command fails.

## Pageviews (Analytics API)

- **Coverage.** Per-article and aggregate data start on **2015-07-01**. Older requests silently return data from July 2015.
- **Bot data.** `agent=automated` exists since **2020-04-29**, so May 2020 is the first full month. Before that, undeclared bots are counted as `user`, which makes spikes before 2020 less trustworthy.
- **Missing days.** Days with zero views are **absent** from responses. `wir` fills them with 0.
- **Partial months.** A monthly query stops at its end date, so the current month is partial. `wir` periods always end at the last complete month.
- **Unknown titles.** An unknown title returns HTTP 404, not an empty list. `wir` reports it as `not_found`.
- **Redirects.** Redirects are counted **separately**: views of `Einstein` are not included in `Albert_Einstein`. A renamed article keeps its old history under the old title, which is now a redirect.
- **Title format.** Spaces and underscores are equivalent. `/` must be URL-encoded (`AC%2FDC`). Titles are case-sensitive after the first letter.
- **Verification.** `wir views` sums daily data. It matched the monthly endpoint exactly for all 32 months checked (`tests/test_live.py`).

## Readers by country

- **Source.** `top-by-country` gives each edition's reader countries, bucketed for privacy (`views_ceil`).
- **Hidden countries.** Wikimedia **omits 38 countries** on its [Country and Territory Protection List](https://foundation.wikimedia.org/wiki/Legal:Wikimedia_Foundation_Country_and_Territory_Protection_List). This covers all three categories: not published, higher risk and medium risk. They include Russia, Belarus, Vietnam, China, Iran, Türkiye, Kazakhstan, Egypt, Pakistan and Bangladesh. Checked live: tr.wikipedia shows "US 31%" because Türkiye is missing.
- **What `wir` does.** It flags these editions: `readers_by_country` starts with `MISLEADING WITHOUT CAVEAT`. The list is bundled in `src/wir/data/hidden_countries.json`.

## Mapping a topic across languages

- **Concept ID.** A concept is a Wikidata item (QID), and its `sitelinks` give the article title in each language (`ukwiki`, `plwiki`, …).
- **No article.** A language without a sitelink has **no article** on that concept. Example: Q1666254 "intermittent fasting" has no Polish article. Say so; never invent a title.
- **Ambiguous names.** Some names match several concepts; «Меркурій» is the planet Q308, the god Q1150 and mercury (the element) Q925. `wir resolve` returns `status: ambiguous`. Ask the user, then pin the concept with `--qid`.
- **Exact names can mislead.** "Learning English" matches the VOA program Q2731224, not language learning. Always compare `concept.description` with the user's intent. For "interest in learning English", use `English` (Q1860), which exists in almost every edition.

## Limits and etiquette

- **User-Agent.** Every request sends a descriptive User-Agent with a contact.
- **Rate limits.** Requests run one after another, and HTTP 429/503 responses are retried after `Retry-After`.
- **Caching.** Pageview requests are split into calendar years, and finished years are cached forever in `~/.cache/wikipedia-interest-research/cache.sqlite` (override with `WIR_HOME`). A longer or shifted period only downloads the missing years.
- **Redirects.** They are screened with one batched request for recent views (`prop=pageviews`, 50 titles per request).
- **Request counts.** A cold study of 5 languages takes about 140 requests and 10 seconds; follow-ups are mostly served from the cache.
- **Offline mode.** `WIR_OFFLINE=1` serves only from the cache and names the missing request.
