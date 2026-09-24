# Troubleshooting

Read this when a `scripts/wir` command exits with a non-zero code and its message is not enough.

| Exit | Situation | What to do |
|---|---|---|
| 127 | `uv` is not installed | Ask the user to install it: `curl -LsSf https://astral.sh/uv/install.sh \| sh` (macOS: `brew install uv`). Then retry. |
| 2 | Bad input: unknown language, bad period, bad weights, a study that already exists, a narrative in the wrong format | The message says what is wrong and suggests the fix, e.g. "Did you mean: polish?". Correct the argument; don't retry unchanged. |
| 2 | "Study 'x' already exists" | Use `study update x ...`, or `study show x` to reuse it. Pass `--replace` only if the user wants to start over. |
| 3 | Topic or article not found | Rephrase the topic with the English encyclopedia name, or run `scripts/wir resolve --topic ... --langs ...` to see candidates. |
| 4 | Wikimedia API or network error | Run `scripts/wir doctor`. If the network is down but the study was run before, `WIR_OFFLINE=1 scripts/wir study show <id>` still works. HTTP 429 is retried automatically; if it persists, wait a minute. |
| 5 | Offline mode and the data is not cached | Unset `WIR_OFFLINE`, or narrow the request to what was already fetched. |
| 6 | Fact-check failed (`report --narrative` or `check`) | The message lists each wrong number and the closest study values. Fix the text to use the study's numbers and re-run. |

## Other situations

- **`needs_choice` status (exit 0).** The topic is ambiguous. Ask the user and re-run with `--topic Q<id>`.
- **Very slow first run.** A cold 5-language study makes about 140 requests (~10 s). Later runs hit the cache in `~/.cache/wikipedia-interest-research/` (override with `WIR_HOME`).
- **Numbers differ slightly from the Pageviews Analysis website.** `wir` counts humans only (`agent=user`), adds redirects with ≥1% of views, and uses whole months. Use `scripts/wir views --lang uk --article "…"` to see the raw monthly series for one title.
- **A PDF title shows boxes.** The script isn't covered by Inter or DejaVu (e.g. CJK). The data is correct; use `summary.md`.
