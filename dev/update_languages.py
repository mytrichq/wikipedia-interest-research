"""Regenerates src/wir/data/wikipedias.json: uv run python dev/update_languages.py"""

import json
from pathlib import Path

import httpx

from wir.config import DATA_DIR, user_agent

SITEMATRIX = (
    "https://meta.wikimedia.org/w/api.php?action=sitematrix&smtype=language"
    "&smlangprop=code|name|localname|site&smsiteprop=code|dbname|url|closed"
    "&format=json&formatversion=2"
)


def main() -> None:
    data = httpx.get(SITEMATRIX, headers={"User-Agent": user_agent()}, timeout=60).json()
    editions = []
    for key, lang in data["sitematrix"].items():
        if key == "count":
            continue
        for site in lang.get("site", []):
            if site.get("code") == "wiki" and not site.get("closed"):
                editions.append({
                    "code": site["url"].removeprefix("https://").split(".")[0],
                    "name": lang.get("localname") or lang["code"],
                    "native_name": lang.get("name") or lang["code"],
                    "dbname": site["dbname"],
                })  # fmt: skip
    editions.sort(key=lambda e: e["code"])
    out = Path(DATA_DIR) / "wikipedias.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(editions, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {len(editions)} Wikipedia editions to {out}")


if __name__ == "__main__":
    main()
