from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from functools import cache

from wir.config import DATA_DIR


@dataclass(frozen=True)
class Edition:
    code: str
    name: str
    native_name: str
    dbname: str

    @property
    def project(self) -> str:
        return f"{self.code}.wikipedia"

    def article_url(self, title: str) -> str:
        return f"https://{self.code}.wikipedia.org/wiki/{title.replace(' ', '_')}"


class UnknownLanguage(ValueError):
    pass


@cache
def _editions() -> dict[str, Edition]:
    rows = json.loads((DATA_DIR / "wikipedias.json").read_text(encoding="utf-8"))
    return {row["code"]: Edition(**row) for row in rows}


@cache
def dbnames() -> frozenset[str]:
    return frozenset(e.dbname for e in _editions().values())


def get(value: str) -> Edition:
    """Accepts a code ('pl'), an English name ('Polish') or a native name ('polski')."""
    editions = _editions()
    key = value.strip().lower()
    if key in editions:
        return editions[key]
    for edition in editions.values():
        if key in (edition.name.lower(), edition.native_name.lower()):
            return edition
    choices = list(editions) + [e.name.lower() for e in editions.values()]
    close = difflib.get_close_matches(key, choices, n=3, cutoff=0.6)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    raise UnknownLanguage(
        f"Unknown Wikipedia language '{value}'.{hint} Use a language code such as uk, pl, cs, "
        "pt, tr, vi (the subdomain of <code>.wikipedia.org)."
    )


def parse_list(value: str) -> list[Edition]:
    seen: dict[str, Edition] = {}
    for part in value.replace(";", ",").split(","):
        if part.strip():
            edition = get(part)
            seen.setdefault(edition.code, edition)
    if not seen:
        raise UnknownLanguage("No languages given. Example: --langs uk,pl,cs")
    return list(seen.values())
