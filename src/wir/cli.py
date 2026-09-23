from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

from wir import __version__, config, languages, periods, series, trust
from wir.cache import Cache
from wir.collect import analysis_window, collect, significant_titles
from wir.metrics import analyze
from wir.resolve import check_title, resolve_topic
from wir.wikimedia import OfflineCacheMiss, WikimediaClient, WikimediaError

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_NOT_FOUND = 3
EXIT_API_ERROR = 4
EXIT_OFFLINE_MISS = 5
DAILY_ROWS_LIMIT = 62
ACTION_PROBE = "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&format=json"
WIKIDATA_PROBE = (
    "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q333&props=info&format=json"
)


def open_client() -> WikimediaClient:
    return WikimediaClient(Cache(config.home_dir() / "cache.sqlite"))


INNER_ARRAY = re.compile(r"\[\s+([^\[\]{}]*?)\s+\]")


def emit(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(INNER_ARRAY.sub(lambda m: "[" + re.sub(r",\s+", ", ", m.group(1)) + "]", text))


def cmd_resolve(args: argparse.Namespace, client: WikimediaClient) -> int:
    editions = languages.parse_list(args.langs)
    if not args.topic and not args.qid:
        raise ValueError("Give --topic (e.g. --topic 'astronomy') or --qid (e.g. --qid Q333).")
    topic_lang = languages.get(args.topic_lang).code
    resolution = resolve_topic(client, args.topic or "", topic_lang, editions, qid=args.qid)
    emit(resolution.to_dict())
    return EXIT_NOT_FOUND if resolution.status == "not_found" else EXIT_OK


def cmd_views(args: argparse.Namespace, client: WikimediaClient) -> int:
    edition = languages.get(args.lang)
    period = periods.parse(args.period)
    page = check_title(client, edition, args.article)
    if not page["exists"]:
        emit(
            {
                "status": "not_found",
                "lang": edition.code,
                "article": args.article,
                "next_step": "Check the title with: scripts/wir resolve --topic ... --langs ...",
            }
        )
        return EXIT_NOT_FOUND
    rows = client.per_article(
        edition.project, page["title"], period.start, period.end,
        access=args.access, agent=args.agent,
    )  # fmt: skip
    daily_views = series.daily(rows, period.start, period.end)
    monthly_views = series.monthly(daily_views)
    payload = {
        "status": "ok",
        "lang": edition.code,
        "article": page["title"],
        "url": edition.article_url(page["title"]),
        "period": period.label(),
        "agent": args.agent,
        "access": args.access,
        "total_views": int(daily_views.sum()),
        "monthly": series.month_rows(monthly_views),
    }
    if args.granularity == "daily":
        if len(daily_views) > DAILY_ROWS_LIMIT and not args.csv:
            raise ValueError(
                f"{len(daily_views)} daily rows are too many for the terminal; "
                "add --csv <path> to save them, or use --granularity monthly."
            )
        payload["daily"] = [[d.strftime("%Y-%m-%d"), int(v)] for d, v in daily_views.items()]
    if args.csv:
        frame = daily_views if args.granularity == "daily" else monthly_views
        frame.rename("views").to_csv(Path(args.csv), index_label="date")
        payload["csv"] = str(Path(args.csv).resolve())
        payload.pop("daily", None)
    emit(payload)
    return EXIT_OK


def cmd_analyze(args: argparse.Namespace, client: WikimediaClient) -> int:
    edition = languages.get(args.lang)
    period = periods.parse(args.period)
    page = check_title(client, edition, args.article)
    if not page["exists"]:
        emit({"status": "not_found", "lang": edition.code, "article": args.article})
        return EXIT_NOT_FOUND
    window = analysis_window(period)
    if args.no_redirects:
        titles = [{"title": page["title"], "redirect": False}]
    else:
        titles = significant_titles(client, edition, page["title"], window)
    metrics = analyze(collect(client, edition, [t["title"] for t in titles], window))
    emit(
        {
            "status": "ok",
            "lang": edition.code,
            "article": page["title"],
            "titles_included": [t["title"] for t in titles],
            "period_requested": period.label(),
            **metrics,
            "trust": trust.assess(metrics),
        }
    )
    return EXIT_OK


def cmd_doctor(args: argparse.Namespace, client: WikimediaClient) -> int:
    checks = []

    def check(name: str, fn: Callable[[], str]) -> None:
        started = time.monotonic()
        try:
            detail = fn()
            checks.append({"check": name, "ok": True, "detail": detail})
        except Exception as exc:
            checks.append({"check": name, "ok": False, "detail": f"{type(exc).__name__}: {exc}"})
        checks[-1]["ms"] = round((time.monotonic() - started) * 1000)

    check("python", lambda: platform.python_version())
    checks.append({"check": "cache", "ok": True, "detail": client.cache.stats()})
    check("user_agent", config.user_agent)
    last = periods.last_complete_month_end()
    if client.offline:
        checks.append({"check": "network", "ok": True, "detail": "skipped: WIR_OFFLINE is on"})
    else:
        check("analytics_api", lambda: _probe(client, _rest_probe_url(last)))
        check("action_api", lambda: _probe(client, ACTION_PROBE))
        check("wikidata_api", lambda: _probe(client, WIKIDATA_PROBE))
    ok = all(c["ok"] for c in checks)
    emit({"ok": ok, "version": __version__, "today": str(config.today()), "checks": checks})
    return EXIT_OK if ok else EXIT_API_ERROR


def _rest_probe_url(last) -> str:
    stamp = last.strftime("%Y%m%d")
    return (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/"
        f"en.wikipedia/all-access/user/daily/{stamp}/{stamp}"
    )


def _probe(client: WikimediaClient, url: str) -> str:
    return f"HTTP {client.ping(url)}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wir",
        description=(
            "Wikipedia Interest Research: measure how interest in a topic changes "
            "across Wikipedia language editions, judge how trustworthy the trend is, "
            "and produce a one-page PDF report. Output is JSON on stdout; request "
            "statistics go to stderr."
        ),
    )
    parser.add_argument("--version", action="version", version=f"wir {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p = sub.add_parser(
        "resolve",
        help="map a topic to its Wikipedia article in each language",
        description=(
            "Find the Wikipedia concept (Wikidata QID) for a topic and its article title in "
            "each language. Reports ambiguous topics and languages without an article."
        ),
    )
    p.add_argument("--topic", help="topic name, best in English, e.g. 'intermittent fasting'")
    p.add_argument("--langs", required=True, help="comma-separated language codes, e.g. uk,pl,cs")
    p.add_argument("--topic-lang", default="en", help="language of the topic text (default: en)")
    p.add_argument("--qid", help="pin an exact concept, e.g. Q333 (skips the search)")
    p.set_defaults(handler=cmd_resolve)

    p = sub.add_parser(
        "views",
        help="pageviews of one article (quick check / verification)",
        description="Pageviews of one article over whole months, zero-filled.",
    )
    p.add_argument("--lang", required=True, help="language code, e.g. uk")
    p.add_argument("--article", required=True, help="article title, e.g. 'Астрономія'")
    p.add_argument("--period", default="24m", help="'24m', '2y' or 'YYYY-MM..YYYY-MM'")
    p.add_argument("--granularity", choices=["monthly", "daily"], default="monthly")
    p.add_argument("--agent", choices=["user", "automated", "spider", "all-agents"], default="user")
    p.add_argument(
        "--access",
        choices=["all-access", "desktop", "mobile-web", "mobile-app"],
        default="all-access",
    )
    p.add_argument("--csv", help="also write the series to this CSV file")
    p.set_defaults(handler=cmd_views)

    p = sub.add_parser(
        "analyze",
        help="trend, seasonality, spikes and trust for one article",
        description=(
            "Analyze one article: year-over-year change, significance, seasonality, spikes, "
            "bot-like traffic, change relative to the whole edition, and a trust level."
        ),
    )
    p.add_argument("--lang", required=True, help="language code, e.g. uk")
    p.add_argument("--article", required=True, help="article title, e.g. 'Астрономія'")
    p.add_argument("--period", default="24m", help="'24m', '2y' or 'YYYY-MM..YYYY-MM'")
    p.add_argument("--no-redirects", action="store_true", help="ignore views of redirect titles")
    p.set_defaults(handler=cmd_analyze)

    p = sub.add_parser("doctor", help="check the environment, cache and API access")
    p.set_defaults(handler=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_OK
    client = open_client()
    try:
        return args.handler(args, client)
    except (ValueError, languages.UnknownLanguage) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT
    except OfflineCacheMiss as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_OFFLINE_MISS
    except WikimediaError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_API_ERROR
    finally:
        print(f"wir: requests — {client.stats.summary()}", file=sys.stderr)
        client.close()


if __name__ == "__main__":
    sys.exit(main())
