from __future__ import annotations

import re

ISO_DATE = re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?(?:\.\.\d{4}-\d{2})?\b")
NUMBER = re.compile(
    r"(?<![\w.,])([-−–+]?)"
    r"(\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d{1,3}(?:,\d{3})+(?![\d,])|\d+)"
    r"(?:([.,])(\d+))?"
    r"\s*(%|×|x\b|[kKкК]\b|тис\.?|тисяч\w*)?"
)
YEARS = range(2001, 2036)
FREE_INTEGERS = {*range(0, 13), 24, 36, 48, 60}
MIN_ABS_TOLERANCE = 0.6
REL_TOLERANCE_PERCENT = 0.03
REL_TOLERANCE_COUNT = 0.01
CONTEXT_CHARS = 40


def extract(text: str) -> list[dict]:
    cleaned = ISO_DATE.sub(" ", text)
    found = []
    for match in NUMBER.finditer(cleaned):
        sign, whole, _, fraction, unit = match.groups()
        digits = re.sub(r"[ \u00a0\u202f,]", "", whole)
        value = float(f"{digits}.{fraction}") if fraction else float(digits)
        if unit and unit[0] in "kKкКт":
            value *= 1000
        start, end = match.span()
        found.append(
            {
                "text": match.group(0).strip(),
                "value": value,
                "percent": unit == "%",
                "multiple": unit in ("×", "x"),
                "context": cleaned[max(0, start - CONTEXT_CHARS) : end + CONTEXT_CHARS].strip(),
            }
        )
    return found


def _walk(node, key: str, numbers: set[float], percents: set[float]) -> None:
    if isinstance(node, bool) or node is None:
        return
    if isinstance(node, str):
        for item in extract(node):
            (percents if item["percent"] else numbers).add(item["value"])
        return
    if isinstance(node, (int, float)):
        (percents if key.endswith("_pct") else numbers).add(abs(float(node)))
        return
    if isinstance(node, dict):
        for k, v in node.items():
            _walk(v, str(k), numbers, percents)
    elif isinstance(node, (list, tuple)):
        for item in node:
            _walk(item, key, numbers, percents)


def known_numbers(document: dict) -> tuple[set[float], set[float]]:
    """Only numbers the agent was shown: the study summary, including numbers inside its texts."""
    from wir.study import summarize

    numbers: set[float] = set()
    percents: set[float] = set()
    _walk(summarize(document), "", numbers, percents)
    return numbers, percents


def _rounding_step(value: float) -> float:
    """Precision implied by trailing zeros: 180 -> 10, 12500 -> 100, 183 -> 1."""
    if not value.is_integer() or value == 0:
        return 0.0
    digits = str(int(value))
    zeros = len(digits) - len(digits.rstrip("0"))
    return 10.0 ** min(zeros, len(digits) - 1) / 2 if zeros else 0.0


def _close(value: float, candidates: set[float], relative: float, rounded: bool) -> bool:
    step = _rounding_step(value) if rounded else 0.0
    return any(abs(value - c) <= max(MIN_ABS_TOLERANCE, relative * c, step) for c in candidates)


def _nearest(value: float, candidates: set[float], count: int = 3) -> list[float]:
    return sorted(candidates, key=lambda c: abs(c - value))[:count]


def check(text: str, document: dict) -> dict:
    """Every number in the text must come from the study (sign-insensitive, small tolerance)."""
    numbers, percents = known_numbers(document)
    unmatched, checked = [], 0
    for item in extract(text):
        value = item["value"]
        if (
            not item["percent"]
            and not item["multiple"]
            and (value in FREE_INTEGERS or (value.is_integer() and int(value) in YEARS))
        ):
            continue
        checked += 1
        pool = percents if item["percent"] else numbers
        tolerance = REL_TOLERANCE_PERCENT if item["percent"] else REL_TOLERANCE_COUNT
        if _close(value, pool, tolerance, rounded=not item["percent"]):
            continue
        unmatched.append(
            {
                "number": item["text"],
                "context": item["context"],
                "closest_study_values": [round(v, 2) for v in _nearest(value, pool)],
            }
        )
    return {"ok": not unmatched, "numbers_checked": checked, "unmatched": unmatched}


def explain(result: dict) -> str:
    lines = [
        f"Fact-check failed: {len(result['unmatched'])} number(s) are not in the study data. "
        "Use only numbers from `scripts/wir study show <id>` (rounding is fine):"
    ]
    for item in result["unmatched"]:
        closest = ", ".join(str(v) for v in item["closest_study_values"])
        lines.append(
            f"  - '{item['number']}' in \"…{item['context']}…\" — closest study values: {closest}"
        )
    return "\n".join(lines)
