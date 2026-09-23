from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

from wir import __version__, languages, periods, series, trust
from wir.collect import analysis_window, collect, significant_titles
from wir.languages import Edition
from wir.metrics import analyze, yoy
from wir.periods import last_complete_month_end
from wir.rank import parse_weights, rank
from wir.resolve import Candidate, load_entities, proxy_search, resolve_topic
from wir.wikimedia import WikimediaClient

STUDIES_DIR = Path("wiki-studies")
QID = re.compile(r"^[Qq]\d+$")
TOP_COUNTRIES = 3
MAX_REASONS = 2
REPORT_LANGUAGES = ("uk", "en")
RAW_GAP_PP = 10


class NeedsChoice(Exception):
    def __init__(self, payload: dict):
        super().__init__("topic needs a choice")
        self.payload = payload


@dataclass
class Topic:
    input: str
    qids: list[str]
    label: str = ""
    labels: dict = field(default_factory=dict)


@dataclass
class Spec:
    topics: list[Topic]
    langs: list[str]
    period: str = "24m"
    weights: dict = field(default_factory=lambda: parse_weights(None))
    proxies: list[dict] = field(default_factory=list)
    question: str = ""
    topic_lang: str = "en"


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:60] or "study"


def study_dir(study_id: str) -> Path:
    return STUDIES_DIR / study_id


def parse_topic_inputs(values: list[str]) -> list[str]:
    topics = [v.strip() for v in values if v and v.strip()]
    if not topics:
        raise ValueError("Give at least one --topic, e.g. --topic 'astronomy'.")
    return topics


def parse_proxy(value: str, topic_count: int) -> dict:
    """'pl:Title' or '<topic number>:pl:Title' -> {"topic": index, "lang", "title"}."""
    parts = value.split(":", 2)
    if len(parts) == 3 and parts[0].isdigit():
        index, lang, title = int(parts[0]) - 1, parts[1], parts[2]
    elif len(parts) >= 2:
        if topic_count > 1:
            raise ValueError(
                "Several topics: say which one the article is for, e.g. --article '2:pl:Title' "
                "(topic number as listed in the study)."
            )
        index, lang, title = 0, parts[0], ":".join(parts[1:])
    else:
        raise ValueError(f"--article must look like pl:'Title', got '{value}'.")
    if not 0 <= index < topic_count:
        raise ValueError(f"Topic number {index + 1} does not exist (1..{topic_count}).")
    return {"topic": index, "lang": languages.get(lang).code, "title": title.strip().strip("'\"")}


def resolve_topics(
    client: WikimediaClient, inputs: list[str], topic_lang: str, editions: list[Edition]
) -> list[Topic]:
    topics, problems = [], []
    for text in inputs:
        qids, labels = [], []
        for part in (p.strip() for p in text.split("+")):
            if not part:
                continue
            if QID.match(part):
                qids.append(part.upper())
                continue
            result = resolve_topic(client, part, topic_lang, editions)
            if result.status == "ok":
                qids.append(result.concept.qid)
                labels.append(result.concept.label)
            else:
                problems.append({"topic": part, **result.to_dict()})
        topics.append(Topic(input=text, qids=qids, label=" + ".join(labels)))
    if problems:
        raise NeedsChoice(
            {
                "status": "needs_choice",
                "problems": problems,
                "next_step": (
                    "Some topics are ambiguous or were not found. Ask the user which meaning they "
                    "want, then re-run with Wikidata ids, e.g. --topic Q308 (combine concepts with "
                    "'+', e.g. --topic 'Q1860+Q130192')."
                ),
            }
        )
    return topics


def load_concepts(
    client: WikimediaClient, topic: Topic, editions: list[Edition]
) -> list[Candidate]:
    concepts = [Candidate(qid=q) for q in topic.qids]
    load_entities(client, concepts, editions, REPORT_LANGUAGES[0])
    for concept in concepts:
        if not concept.sitelinks:
            raise ValueError(f"{concept.qid} has no Wikipedia articles; check the id.")
    if not topic.label:
        topic.label = " + ".join(c.labels.get("en") or c.label or c.qid for c in concepts)
    codes = {*REPORT_LANGUAGES, *(e.code for e in editions)}
    topic.labels = {
        code: " + ".join(c.labels.get(code) or c.labels.get("en") or c.qid for c in concepts)
        for code in sorted(codes)
    }
    return concepts


def edition_context(client: WikimediaClient, edition: Edition) -> dict:
    last = last_complete_month_end()
    countries = client.top_by_country(edition.project, last.year, last.month)
    total = sum(c.get("views_ceil", 0) for c in countries) or 1
    top = [
        {"country": c["country"], "share": round(c.get("views_ceil", 0) / total, 2)}
        for c in countries[:TOP_COUNTRIES]
    ]
    devices = client.unique_devices(edition.project, dt.date(last.year, last.month, 1), last)
    return {
        "language": edition.name,
        "top_reader_countries": top,
        "hidden_countries": languages.hidden_reader_countries(edition.code),
        "hidden_country_codes": languages.hidden_country_codes(edition.code),
        "monthly_unique_devices": devices[0][1] if devices else None,
        "month": f"{last:%Y-%m}",
    }


def readers_text(context: dict) -> str:
    shares = ", ".join(f"{c['country']} {c['share']:.0%}" for c in context["top_reader_countries"])
    hidden = context.get("hidden_countries") or []
    if not hidden:
        return shares
    return (
        f"MISLEADING WITHOUT CAVEAT: Wikimedia hides readers from {', '.join(hidden)} "
        f"(country protection list), so the visible split ({shares}) leaves out the main audience."
    )


def _breadth(per_article: list[pd.Series], total: pd.Series) -> dict:
    if len(per_article) <= 1:
        return {"articles": len(per_article), "breadth": 1.0, "top_share": 1.0}
    total_sign = (yoy(total)["robust_yoy_pct"] or 0) >= 0
    same = sum(((yoy(s)["robust_yoy_pct"] or 0) >= 0) == total_sign for s in per_article)
    sums = [float(s.sum()) for s in per_article]
    return {
        "articles": len(per_article),
        "breadth": round(same / len(per_article), 2),
        "top_share": round(max(sums) / max(sum(sums), 1), 2),
    }


def compute_cell(
    client: WikimediaClient,
    edition: Edition,
    concepts: list[Candidate],
    proxies: list[dict],
    window: periods.Period,
) -> tuple[dict, pd.DataFrame | None]:
    articles = [
        {"title": c.sitelinks[edition.dbname], "qid": c.qid, "proxy": False}
        for c in concepts
        if edition.dbname in c.sitelinks
    ]
    articles += [{"title": p["title"], "qid": None, "proxy": True} for p in proxies]
    missing = [c.qid for c in concepts if edition.dbname not in c.sitelinks]
    if not articles:
        return {
            "status": "missing",
            "language": edition.name,
            "missing_concepts": missing,
            "proxy_candidates": proxy_search(client, edition, concepts[0]),
        }, None

    all_titles, per_article = [], []
    for article in articles:
        titles = significant_titles(client, edition, article["title"], window)
        article["titles_included"] = [t["title"] for t in titles]
        all_titles += article["titles_included"]
        per_article.append(
            series.monthly(collect(client, edition, article["titles_included"], window).user)
        )
    data = collect(client, edition, all_titles, window)
    metrics = analyze(data)
    total = series.monthly(data.user)
    cluster = {**_breadth(per_article, total), "proxy": any(a["proxy"] for a in articles)}
    for article, monthly in zip(articles, per_article, strict=True):
        article["views"] = int(monthly.sum())
    cell = {
        "status": "ok",
        "language": edition.name,
        "articles": articles,
        "missing_concepts": missing,
        "metrics": metrics,
        "cluster": cluster,
        "trust": trust.assess(metrics, cluster),
    }
    frame = pd.DataFrame(
        {
            "month": [f"{m:%Y-%m}" for m in total.index],
            "views": total.to_numpy(),
            "edition_views": series.monthly(data.project).to_numpy(),
        }
    )
    frame["per_million"] = (frame["views"] / frame["edition_views"].replace(0, pd.NA) * 1e6).round(
        2
    )
    return cell, frame


def cell_key(topic: Topic, lang: str, topics: int, langs: int) -> str:
    if topics == 1:
        return lang
    if langs == 1:
        return topic.label or topic.input
    return f"{topic.label or topic.input} @ {lang}"


def compute(client: WikimediaClient, spec: Spec) -> tuple[dict, pd.DataFrame]:
    period = periods.parse(spec.period)
    window = analysis_window(period)
    editions = [languages.get(code) for code in spec.langs]
    cells, frames = [], []
    for index, topic in enumerate(spec.topics):
        concepts = load_concepts(client, topic, editions)
        for edition in editions:
            proxies = [p for p in spec.proxies if p["topic"] == index and p["lang"] == edition.code]
            cell, frame = compute_cell(client, edition, concepts, proxies, window)
            key = cell_key(topic, edition.code, len(spec.topics), len(editions))
            cells.append({"key": key, "topic": topic.label, "lang": edition.code, **cell})
            if frame is not None:
                frame.insert(0, "lang", edition.code)
                frame.insert(0, "topic", topic.label)
                frames.append(frame)
    ranking = rank(
        [
            {"key": c["key"], "metrics": c["metrics"], "trust": c["trust"]}
            for c in cells
            if c["status"] == "ok"
        ],
        spec.weights,
    )
    context = {e.code: edition_context(client, e) for e in editions}
    results = {
        "period": period.label(),
        "window": window.label(),
        "cells": cells,
        "ranking": ranking,
        "editions": context,
    }
    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return results, data


def assumptions(spec: Spec, results: dict) -> list[str]:
    notes = [
        f"Period {results['period']} = whole months up to the last complete month; statistics "
        f"use {results['window']} so every month has a year-earlier comparison.",
        "Views are agent=user (declared bots and crawlers excluded), all devices, redirects "
        "carrying ≥1% of an article's views included.",
        "Weights: " + ", ".join(f"{k}={v:g}" for k, v in spec.weights.items() if v) + ".",
    ]
    for topic in spec.topics:
        notes.append(f"Topic '{topic.input}' = Wikidata {'+'.join(topic.qids)} ({topic.label}).")
    for proxy in spec.proxies:
        topic = spec.topics[proxy["topic"]].label
        notes.append(
            f"PROXY: {proxy['lang']} has no article on '{topic}'; '{proxy['title']}' is used "
            "instead and is not the same concept."
        )
    return notes


def write(study_id: str, spec: Spec, results: dict, data: pd.DataFrame, history: list) -> Path:
    folder = study_dir(study_id)
    (folder / "data").mkdir(parents=True, exist_ok=True)
    if not data.empty:
        data.to_csv(folder / "data" / "monthly.csv", index=False)
    document = {
        "id": study_id,
        "wir_version": __version__,
        "updated": dt.datetime.now().isoformat(timespec="seconds"),
        "spec": {**asdict(spec), "topics": [asdict(t) for t in spec.topics]},
        "assumptions": assumptions(spec, results),
        "history": history,
        "results": results,
    }
    (folder / "study.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return folder


def load(study_id: str) -> dict:
    path = study_dir(study_id) / "study.json"
    if not path.exists():
        known = [p.name for p in STUDIES_DIR.glob("*") if (p / "study.json").exists()]
        raise ValueError(
            f"No study '{study_id}' in {STUDIES_DIR}/ (current directory). "
            f"Known studies: {', '.join(known) or 'none'}. Run `scripts/wir study list`."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def spec_from(document: dict) -> Spec:
    raw = document["spec"]
    return Spec(**{**raw, "topics": [Topic(**t) for t in raw["topics"]]})


def list_studies() -> list[dict]:
    rows = []
    for path in sorted(STUDIES_DIR.glob("*/study.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "id": doc["id"],
                "question": doc["spec"].get("question", ""),
                "topics": [t["label"] or t["input"] for t in doc["spec"]["topics"]],
                "langs": doc["spec"]["langs"],
                "period": doc["results"]["period"],
                "updated": doc["updated"],
            }
        )
    return rows


def summarize(document: dict) -> dict:
    """Compact view for the agent: every number it may quote, nothing it does not need."""
    results = document["results"]
    rows = []
    for cell in results["cells"]:
        if cell["status"] != "ok":
            rows.append(
                {
                    "key": cell["key"],
                    "status": "missing",
                    "note": f"No {cell['language']} article on this topic.",
                    "proxy_candidates": [p["title"] for p in cell["proxy_candidates"]],
                }
            )
            continue
        m, t = cell["metrics"], cell["trust"]
        clean, season = m["growth_without_one_offs"], m.get("seasonality") or {}
        negatives = sorted((r for r in t["reasons"] if r["effect"] < 0), key=lambda r: r["effect"])
        reasons = negatives[:MAX_REASONS] or [r for r in t["reasons"] if r["code"] == "consistent"]
        row = {
            "key": cell["key"],
            "articles": [a["title"] + (" (PROXY)" if a["proxy"] else "") for a in cell["articles"]],
            "verdict": m["verdict"],
            "yoy_pct": clean["robust_yoy_pct"],
            "months_up_of_12": clean["months_up"],
            "avg_monthly_views": m["volume"]["avg_monthly_last12"],
            "per_million_views": m["relative"]["per_million_last12"],
            "relative_yoy_pct": m["relative"]["yoy_pct"],
            "edition_yoy_pct": m["relative"]["edition_views_yoy_pct"],
            "trust": f"{t['level']} ({t['score']})",
            "trust_reasons": [r["text"] for r in reasons],
        }
        raw = m["growth"]["yoy_pct"]
        robust = clean["robust_yoy_pct"]
        if raw is not None and robust is not None and abs(raw - robust) >= RAW_GAP_PP:
            row["raw_yoy_pct"] = raw
        if season.get("strong"):
            row["seasonality"] = f"{season['peak_month']} peak ≈{season['peak_factor']}× every year"
        if clean["one_off_months"]:
            row["one_off_months"] = [o["month"] for o in clean["one_off_months"]]
        rows.append(row)
    return {
        "study": document["id"],
        "folder": str(study_dir(document["id"])),
        "question": document["spec"].get("question", ""),
        "period": results["period"],
        "stats_window": results["window"],
        "results": rows,
        "ranking": [
            {"rank": r["rank"], "key": r["key"], "score": r["score"], "strongest": r["strongest"]}
            for r in results["ranking"]
        ],
        "readers_by_country": {
            code: readers_text(ctx) for code, ctx in results["editions"].items()
        },
        "assumptions": document["assumptions"],
        "next_steps": [
            "Answer using only numbers from this output; name the trust level and its reasons.",
            "Say plainly when a language has no article (missing) instead of guessing.",
            f"For a shareable one-page PDF: scripts/wir report {document['id']}",
        ],
    }
