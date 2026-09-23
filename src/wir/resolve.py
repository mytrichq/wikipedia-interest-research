from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from wir import languages
from wir.languages import Edition
from wir.wikimedia import WikimediaClient

NON_ARTICLE_DESCRIPTIONS = (
    "wikimedia disambiguation page",
    "wikimedia list article",
    "wikimedia category",
    "wikimedia template",
    "scientific article",
    "scholarly article",
)
MATCH_KINDS = {2: "exact_title_or_label", 1: "alias", 0: "search_only"}
AMBIGUITY_RATIO = 0.3
MAX_CANDIDATES = 12
MAX_REDIRECTS = 50


@dataclass
class Candidate:
    qid: str
    label: str = ""
    description: str = ""
    english_description: str = ""
    match: int = 0
    search_rank: int = 99
    sitelinks: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)

    @property
    def editions(self) -> int:
        return len(self.sitelinks)

    def brief(self) -> dict:
        return {
            "qid": self.qid,
            "label": self.label,
            "description": self.description,
            "matched_by": MATCH_KINDS[self.match],
            "wikipedia_editions": self.editions,
        }


@dataclass
class ArticleMatch:
    edition: Edition
    status: str
    title: str | None = None
    proxy_candidates: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        out = {"lang": self.edition.code, "language": self.edition.name, "status": self.status}
        if self.title:
            out["title"] = self.title
            out["url"] = self.edition.article_url(self.title)
        if self.status == "missing":
            out["proxy_candidates"] = self.proxy_candidates
        return out


@dataclass
class Resolution:
    status: str
    topic: str
    topic_lang: str
    concept: Candidate | None
    articles: list[ArticleMatch]
    alternatives: list[Candidate]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "topic": self.topic,
            "topic_lang": self.topic_lang,
            "concept": self.concept.brief() if self.concept else None,
            "articles": [a.to_dict() for a in self.articles],
            "alternatives": [c.brief() for c in self.alternatives],
            "next_step": self.next_step(),
        }

    def next_step(self) -> str:
        if self.status == "not_found":
            return (
                "No Wikipedia concept matched. Rephrase the topic (the English name of the "
                "encyclopedia article works best) or pass --topic-lang for the language it is in."
            )
        if self.status == "ambiguous":
            options = "; ".join(
                f"{c.qid} = {c.label} ({c.description})"
                for c in [self.concept, *self.alternatives]
                if c
            )
            return (
                f"The topic is ambiguous. Ask the user which meaning they want ({options}), "
                "then re-run with --qid <QID>."
            )
        missing = [a.edition.code for a in self.articles if a.status == "missing"]
        step = (
            f"Check that the concept description matches what the user means; if an alternative "
            f"fits better, re-run with its --qid. Otherwise re-use --qid {self.concept.qid}."
        )
        if missing:
            step += (
                f" No article in: {', '.join(missing)} — tell the user. proxy_candidates are raw "
                "search hits, not verified: use one only if it is clearly about the same topic, "
                "and label it as a proxy."
            )
        return step


def search_candidates(client: WikimediaClient, topic: str, topic_lang: str) -> list[Candidate]:
    """Concept candidates from Wikidata entity search and Wikipedia full-text search."""
    found: dict[str, Candidate] = {}
    folded = topic.casefold()

    hits = client.wikidata(
        action="wbsearchentities",
        search=topic,
        language=topic_lang,
        uselang=topic_lang,
        type="item",
        limit=10,
    ).get("search", [])
    for position, hit in enumerate(hits):
        match = hit.get("match", {})
        exact = match.get("text", "").casefold() == folded
        score = (2 if match.get("type") == "label" else 1) if exact else 0
        found[hit["id"]] = Candidate(qid=hit["id"], match=score, search_rank=position)

    pages = (
        client.action(
            topic_lang,
            action="query",
            generator="search",
            gsrsearch=topic,
            gsrlimit=5,
            gsrnamespace=0,
            prop="pageprops",
            ppprop="wikibase_item|disambiguation",
            redirects=1,
        )
        .get("query", {})
        .get("pages", [])
    )
    for page in pages:
        props = page.get("pageprops", {})
        qid = props.get("wikibase_item")
        if not qid or "disambiguation" in props:
            continue
        position = page.get("index", 99) - 1
        exact = page["title"].casefold() == folded
        candidate = found.setdefault(qid, Candidate(qid=qid, search_rank=position))
        candidate.search_rank = min(candidate.search_rank, position)
        candidate.match = max(candidate.match, 2 if exact else 0)

    return list(found.values())[:MAX_CANDIDATES]


def load_entities(
    client: WikimediaClient, candidates: list[Candidate], editions: list[Edition], topic_lang: str
) -> None:
    if not candidates:
        return
    wikipedia_dbnames = languages.dbnames()
    label_langs = sorted({topic_lang, "en", "uk", *(e.code for e in editions)})
    entities = client.wikidata(
        action="wbgetentities",
        ids="|".join(c.qid for c in candidates),
        props="sitelinks|labels|descriptions",
        languages="|".join(label_langs),
    ).get("entities", {})
    for candidate in candidates:
        entity = entities.get(candidate.qid, {})
        candidate.sitelinks = {
            site: link["title"]
            for site, link in entity.get("sitelinks", {}).items()
            if site in wikipedia_dbnames
        }
        candidate.labels = {k: v["value"] for k, v in entity.get("labels", {}).items()}
        descriptions = {k: v["value"] for k, v in entity.get("descriptions", {}).items()}
        candidate.label = candidate.labels.get(topic_lang) or candidate.labels.get("en", "")
        candidate.description = descriptions.get(topic_lang) or descriptions.get("en", "")
        candidate.english_description = descriptions.get("en", "")


def is_article_concept(candidate: Candidate) -> bool:
    english = candidate.english_description.casefold()
    return candidate.editions > 0 and not english.startswith(NON_ARTICLE_DESCRIPTIONS)


def rank(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(
        (c for c in candidates if is_article_concept(c)),
        key=lambda c: (-c.match, -c.editions, c.search_rank),
    )


def is_ambiguous(ranked: list[Candidate]) -> list[Candidate]:
    """Other exact-name matches that are about as notable as the top one."""
    if not ranked or ranked[0].match == 0:
        return []
    top = ranked[0]
    return [c for c in ranked[1:] if c.match > 0 and c.editions >= AMBIGUITY_RATIO * top.editions]


def proxy_search(client: WikimediaClient, edition: Edition, concept: Candidate) -> list[dict]:
    """Search a language edition that has no article, so a human can judge possible proxies."""
    term = concept.labels.get(edition.code) or concept.labels.get("en") or concept.label
    if not term:
        return []
    results = (
        client.action(
            edition.code,
            action="query",
            list="search",
            srsearch=term,
            srlimit=3,
            srnamespace=0,
            srprop="snippet",
        )
        .get("query", {})
        .get("search", [])
    )
    return [
        {"title": r["title"], "snippet": _clean_snippet(r.get("snippet", "")), "searched_for": term}
        for r in results
    ]


def resolve_topic(
    client: WikimediaClient,
    topic: str,
    topic_lang: str,
    editions: list[Edition],
    qid: str | None = None,
) -> Resolution:
    if qid:
        candidates = [Candidate(qid=qid.upper(), match=2)]
        load_entities(client, candidates, editions, topic_lang)
        ranked = [c for c in candidates if c.editions > 0]
        ambiguous: list[Candidate] = []
    else:
        candidates = search_candidates(client, topic, topic_lang)
        load_entities(client, candidates, editions, topic_lang)
        ranked = rank(candidates)
        ambiguous = is_ambiguous(ranked)

    if not ranked:
        return Resolution("not_found", topic, topic_lang, None, [], [])

    concept = ranked[0]
    articles = []
    for edition in editions:
        title = concept.sitelinks.get(edition.dbname)
        if title:
            articles.append(ArticleMatch(edition, "found", title))
        else:
            proxies = proxy_search(client, edition, concept)
            articles.append(ArticleMatch(edition, "missing", proxy_candidates=proxies))
    alternatives = ambiguous if ambiguous else ranked[1:4]
    status = "ambiguous" if ambiguous else "ok"
    return Resolution(status, topic, topic_lang, concept, articles, alternatives)


def check_title(client: WikimediaClient, edition: Edition, title: str) -> dict:
    """Canonical title of a user-supplied article, following redirects."""
    body = client.action(
        edition.code,
        action="query",
        titles=title,
        redirects=1,
        prop="pageprops",
        ppprop="wikibase_item|disambiguation",
    )
    page = body.get("query", {}).get("pages", [{}])[0]
    if page.get("missing") or page.get("invalid"):
        return {"lang": edition.code, "title": title, "exists": False}
    props = page.get("pageprops", {})
    return {
        "lang": edition.code,
        "title": page["title"],
        "exists": True,
        "qid": props.get("wikibase_item"),
        "disambiguation": "disambiguation" in props,
    }


def redirects(client: WikimediaClient, edition: Edition, title: str) -> list[str]:
    """Titles that redirect to an article; their pageviews are counted separately by the API."""
    body = client.action(
        edition.code,
        action="query",
        titles=title,
        prop="redirects",
        rdnamespace=0,
        rdlimit=MAX_REDIRECTS,
        rdprop="title",
    )
    page = body.get("query", {}).get("pages", [{}])[0]
    return [r["title"] for r in page.get("redirects", [])]


def recent_views(client: WikimediaClient, edition: Edition, titles: list[str]) -> dict[str, int]:
    """Views over the last ~60 days for many titles at once (one request per 50 titles)."""
    totals: dict[str, int] = {}
    for start in range(0, len(titles), 50):
        batch = "|".join(titles[start : start + 50])
        extra: dict = {}
        while True:
            body = client.action(
                edition.code, action="query", titles=batch, prop="pageviews", pvipdays=60, **extra
            )
            for page in body.get("query", {}).get("pages", []):
                views = page.get("pageviews") or {}
                totals[page["title"]] = totals.get(page["title"], 0) + sum(
                    v or 0 for v in views.values()
                )
            if "continue" not in body:
                break
            extra = {k: v for k, v in body["continue"].items() if k != "continue"}
    return totals


def _clean_snippet(snippet: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", snippet)).strip()
