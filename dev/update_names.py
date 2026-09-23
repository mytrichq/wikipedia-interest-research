"""Regenerates src/wir/data/names.json from Unicode CLDR.

Run: uv run --with babel python dev/update_names.py
"""

import json
from pathlib import Path

from babel import Locale

from wir.config import DATA_DIR

UI_LANGUAGES = ("uk", "en")
SPECIAL = {
    "zh-yue": "yue",
    "zh-min-nan": "nan",
    "zh-classical": "lzh",
    "simple": "en",
    "als": "gsw",
    "bat-smg": "sgs",
    "fiu-vro": "vro",
    "roa-rup": "rup",
    "nds-nl": "nds",
    "map-bms": "jv",
    "roa-tara": "it",
    "cbk-zam": "cbk",
}


def main() -> None:
    editions = json.loads((DATA_DIR / "wikipedias.json").read_text(encoding="utf-8"))
    out: dict = {"source": "Unicode CLDR via Babel", "languages": {}, "countries": {}}
    for ui in UI_LANGUAGES:
        locale = Locale.parse(ui)
        names = {}
        for edition in editions:
            code = edition["code"]
            cldr = SPECIAL.get(code, code).replace("-", "_")
            name = locale.languages.get(cldr) or locale.languages.get(cldr.split("_")[0])
            if code == "simple":
                name = "Simple English" if ui == "en" else "спрощена англійська"
            names[code] = name or edition["name"]
        out["languages"][ui] = names
        out["countries"][ui] = {k: v for k, v in locale.territories.items() if len(k) == 2}
    path = Path(DATA_DIR) / "names.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    missing = [c for c, n in out["languages"]["uk"].items() if n == out["languages"]["en"][c]]
    print(f"Wrote {path}; uk names equal to en for {len(missing)} codes: {missing[:15]}")


if __name__ == "__main__":
    main()
