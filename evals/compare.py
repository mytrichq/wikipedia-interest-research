"""Compares two benchmark.json files per case/env/model: uv run python evals/compare.py OLD NEW"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def index(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(r["case"], r["env"], r["model"]): r for r in data["cases"]}


def value(row: dict | None, key: str) -> float | None:
    if not row or not row[key].get("n"):
        return None
    return row[key]["mean"]


def main() -> int:
    old, new = index(Path(sys.argv[1])), index(Path(sys.argv[2]))
    print("| Case | Env | Model | Pass rate v1 → v2 | Judge v1 → v2 |")
    print("|---|---|---|---|---|")
    for key in sorted(set(old) | set(new)):
        before, after = old.get(key), new.get(key)
        p0, p1 = value(before, "pass_rate"), value(after, "pass_rate")
        j0, j1 = value(before, "judge_mean"), value(after, "judge_mean")
        if p0 == p1 and j0 == j1:
            continue
        pass_text = f"{p0:.0%} → {p1:.0%}" if p0 is not None and p1 is not None else "—"
        judge_text = f"{j0:.1f} → {j1:.1f}" if j0 is not None and j1 is not None else "—"
        print(f"| {key[0]} | {key[1]} | {key[2]} | {pass_text} | {judge_text} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
