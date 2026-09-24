from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

from wir import __version__, config, factcheck, languages, periods, report, series, study, trust
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
EXIT_FACTCHECK = 6
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
        edition.project,
        page["title"],
        period.start,
        period.end,
        access=args.access,
        agent=args.agent,
    )
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


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _emit_study(document: dict, client: WikimediaClient, extra: dict | None = None) -> None:
    summary = study.summarize(document)
    emit({"status": "ok", **(extra or {}), **summary, "requests": client.stats.summary()})


def cmd_study_new(args: argparse.Namespace, client: WikimediaClient) -> int:
    editions = languages.parse_list(args.langs)
    topic_lang = languages.get(args.topic_lang).code
    periods.parse(args.period)
    inputs = study.parse_topic_inputs(args.topic)
    try:
        topics = study.resolve_topics(client, inputs, topic_lang, editions)
    except study.NeedsChoice as choice:
        emit(choice.payload)
        return EXIT_OK
    spec = study.Spec(
        topics=topics,
        langs=[e.code for e in editions],
        period=args.period,
        weights=study.parse_weights(args.weights),
        proxies=[study.parse_proxy(a, len(topics)) for a in args.article or []],
        question=args.question or "",
        topic_lang=topic_lang,
    )
    study_id = args.id or study.slugify("-".join([t.label or t.input for t in topics] + spec.langs))
    if study.study_dir(study_id).exists() and not args.replace:
        raise ValueError(
            f"Study '{study_id}' already exists. Change it with `scripts/wir study update "
            f"{study_id} ...`, pick another --id, or pass --replace to start over."
        )
    results, data = study.compute(client, spec)
    history = [{"at": _now(), "action": "new", "change": "created"}]
    study.write(study_id, spec, results, data, history)
    _emit_study(study.load(study_id), client)
    return EXIT_OK


def cmd_study_update(args: argparse.Namespace, client: WikimediaClient) -> int:
    document = study.load(args.id)
    spec = study.spec_from(document)
    changes = []
    if args.add_lang:
        added = [e.code for e in languages.parse_list(args.add_lang) if e.code not in spec.langs]
        spec.langs += added
        changes += [f"added language {code}" for code in added]
    if args.remove_lang:
        removed = [e.code for e in languages.parse_list(args.remove_lang)]
        spec.langs = [code for code in spec.langs if code not in removed]
        spec.proxies = [p for p in spec.proxies if p["lang"] not in removed]
        changes += [f"removed language {code}" for code in removed]
    if args.add_topic:
        editions = [languages.get(code) for code in spec.langs]
        try:
            new = study.resolve_topics(client, args.add_topic, spec.topic_lang, editions)
        except study.NeedsChoice as choice:
            emit(choice.payload)
            return EXIT_OK
        spec.topics += new
        changes += [f"added topic {t.input} ({'+'.join(t.qids)})" for t in new]
    if args.remove_topic:
        index = int(args.remove_topic) - 1
        if not 0 <= index < len(spec.topics):
            raise ValueError(f"Topic number must be 1..{len(spec.topics)}.")
        changes.append(f"removed topic {spec.topics.pop(index).input}")
        spec.proxies = [
            {**p, "topic": p["topic"] - (p["topic"] > index)}
            for p in spec.proxies
            if p["topic"] != index
        ]
    if args.period:
        periods.parse(args.period)
        changes.append(f"period {spec.period} -> {args.period}")
        spec.period = args.period
    if args.weights:
        spec.weights = study.parse_weights(args.weights)
        changes.append(f"weights -> {args.weights}")
    for value in args.article or []:
        proxy = study.parse_proxy(value, len(spec.topics))
        spec.proxies.append(proxy)
        changes.append(f"proxy article {proxy['lang']}:{proxy['title']}")
    for value in args.drop_article or []:
        target = study.parse_proxy(value, len(spec.topics))
        spec.proxies = [p for p in spec.proxies if p != target]
        changes.append(f"dropped proxy {target['lang']}:{target['title']}")
    if args.question:
        spec.question = args.question
        changes.append("question updated")
    if not spec.langs or not spec.topics:
        raise ValueError("A study needs at least one language and one topic.")
    if not changes:
        raise ValueError(
            "Nothing to change. Use --add-lang, --remove-lang, --add-topic, --remove-topic, "
            "--period, --weights, --article or --question."
        )
    results, data = study.compute(client, spec)
    entries = [{"at": _now(), "action": "update", "change": c} for c in changes]
    entries[0]["before"] = study.snapshot(document)
    history = document["history"] + entries
    study.write(args.id, spec, results, data, history)
    _emit_study(study.load(args.id), client, {"changes": changes})
    return EXIT_OK


def cmd_study_show(args: argparse.Namespace, client: WikimediaClient) -> int:
    document = study.load(args.id)
    if args.full:
        emit(document)
    else:
        _emit_study(document, client, {"history": [h["change"] for h in document["history"]]})
    return EXIT_OK


def cmd_study_list(args: argparse.Namespace, client: WikimediaClient) -> int:
    root = str(config.studies_root().resolve())
    emit({"status": "ok", "folder": root, "studies": study.list_studies()})
    return EXIT_OK


def cmd_report(args: argparse.Namespace, client: WikimediaClient) -> int:
    emit(report.build(args.id, Path(args.narrative) if args.narrative else None, args.lang))
    return EXIT_OK


def cmd_check(args: argparse.Namespace, client: WikimediaClient) -> int:
    document = study.load(args.id)
    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    result = factcheck.check(text, document)
    emit({"status": "ok" if result["ok"] else "failed", **result})
    return EXIT_OK if result["ok"] else EXIT_FACTCHECK


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

    p = sub.add_parser(
        "study",
        help="create, update and inspect studies (the main workflow)",
        description=(
            "A study compares interest in one or more topics across languages. It is saved in "
            "./wiki-studies/<id>/ (study.json + data/monthly.csv) so follow-up questions reuse it."
        ),
    )
    study_sub = p.add_subparsers(dest="study_command", metavar="<action>", required=True)

    q = study_sub.add_parser(
        "new",
        help="resolve topics, fetch data, analyze and rank",
        description=(
            "Create a study. Topics are best given in English; several concepts can form one "
            "topic with '+', and Wikidata ids (Q333) pin exact concepts."
        ),
    )
    q.add_argument(
        "--topic",
        action="append",
        required=True,
        help="topic; repeat to compare topics; 'A + B' or 'Q1860+Q130192' for a cluster",
    )
    q.add_argument("--langs", required=True, help="comma-separated language codes, e.g. uk,pl,cs")
    q.add_argument("--period", default="24m", help="'24m', '3y' or 'YYYY-MM..YYYY-MM'")
    q.add_argument("--topic-lang", default="en", help="language of the topic text (default: en)")
    q.add_argument("--weights", help="ranking weights, e.g. growth=0.5,size=0.3,trust=0.2")
    q.add_argument(
        "--article",
        action="append",
        help="clearly labelled proxy for a language without an article: pl:'Title'",
    )
    q.add_argument("--question", help="the user's question, stored with the study")
    q.add_argument("--id", help="study id (default: derived from topics and languages)")
    q.add_argument(
        "--replace", action="store_true", help="overwrite an existing study with this id"
    )
    q.set_defaults(handler=cmd_study_new)

    q = study_sub.add_parser("update", help="change a study; only new data is downloaded")
    q.add_argument("id")
    q.add_argument("--add-lang", help="e.g. sk or sk,hu")
    q.add_argument("--remove-lang")
    q.add_argument("--add-topic", action="append")
    q.add_argument("--remove-topic", help="topic number (1-based, as listed)")
    q.add_argument("--period")
    q.add_argument("--weights")
    q.add_argument("--article", action="append", help="add a proxy article: pl:'Title'")
    q.add_argument("--drop-article", action="append", help="remove a proxy article: pl:'Title'")
    q.add_argument("--question")
    q.set_defaults(handler=cmd_study_update)

    q = study_sub.add_parser("show", help="print a saved study (no network)")
    q.add_argument("id")
    q.add_argument("--full", action="store_true", help="print the whole study.json")
    q.set_defaults(handler=cmd_study_show)

    q = study_sub.add_parser("list", help="list studies in ./wiki-studies")
    q.set_defaults(handler=cmd_study_list)

    p = sub.add_parser(
        "report",
        help="one-page PDF + summary.md + charts for a study",
        description=(
            "Build wiki-studies/<id>/report.pdf (one A4 page), summary.md and charts/*.png. "
            "With --narrative, your text (see assets/narrative_template.md) is fact-checked "
            "against the study first; without it, a neutral summary is generated from the data."
        ),
    )
    p.add_argument("id")
    p.add_argument("--narrative", help="markdown file with # Headline, ## Findings, ## Next steps")
    p.add_argument("--lang", choices=["uk", "en"], help="report language (default: detected)")
    p.set_defaults(handler=cmd_report)

    p = sub.add_parser(
        "check",
        help="fact-check a draft answer against a study",
        description="Every number in the text must match the study (rounding allowed).",
    )
    p.add_argument("id")
    p.add_argument("--file", help="text file to check (default: stdin)")
    p.set_defaults(handler=cmd_check)

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
    except report.FactCheckError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_FACTCHECK
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
