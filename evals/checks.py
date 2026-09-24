"""Deterministic checks from docs/TEST_PLAN.md, section 6, evaluated on one recorded run."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

SKILL_NAME = "wikipedia-interest-research"
CYRILLIC = range(0x0400, 0x0500)
TRUST_WORDS = re.compile(r"\b(high|medium|low|висок|середн|низьк)\w*", re.IGNORECASE)
LIMITATION_WORDS = re.compile(
    r"обмежен|limitation|caveat|застереж|≠|не означає|not the same|is not a country|не країна",
    re.IGNORECASE,
)
CLARIFY_WORDS = re.compile(
    r"\?|уточн|clarif|which (one|languages)|які мови|яких мов|припуска|assum"
)
STUDY_COMMAND = re.compile(r"scripts/wir\s+study\s+(new|update|show)")


def _bash_commands(run: dict) -> list[str]:
    return [c["input"].get("command", "") for c in run["tool_calls"] if c["tool"] == "Bash"]


def _studies(workspace: Path) -> list[dict]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(workspace.glob("wiki-studies/*/study.json"))
    ]


def _language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    cyrillic = sum(ord(c) in CYRILLIC for c in letters)
    return "uk" if letters and cyrillic / len(letters) > 0.3 else "en"


def skill_triggered(run: dict) -> bool:
    for call in run["tool_calls"]:
        text = json.dumps(call["input"], ensure_ascii=False)
        if call["tool"] == "Skill" and SKILL_NAME in text:
            return True
        if call["tool"] == "Read" and "SKILL.md" in text and SKILL_NAME in text:
            return True
    return any("scripts/wir" in c for c in _bash_commands(run))


def used_cli(run: dict) -> bool:
    fetched_alone = any(c["tool"] == "WebFetch" for c in run["tool_calls"])
    ran_study = any(STUDY_COMMAND.search(c) for c in _bash_commands(run))
    return ran_study and not fetched_alone


def evaluate(case: dict, run: dict, workspace: Path) -> dict[str, dict]:
    """Returns {check: {"pass": bool, "detail": str}} for the checks the case asks for."""
    from wir import factcheck

    wanted = case.get("checks", {})
    answer = "\n\n".join(run["final_answers"])
    last_answer = run["final_answers"][-1] if run["final_answers"] else ""
    studies = _studies(workspace)
    results: dict[str, dict] = {}

    def record(name: str, passed: bool, detail: str = "") -> None:
        results[name] = {"pass": bool(passed), "detail": detail}

    if "skill_triggered" in wanted:
        record("skill_triggered", skill_triggered(run))
    if "skill_not_triggered" in wanted:
        record("skill_not_triggered", not skill_triggered(run))
    if "used_cli" in wanted:
        record("used_cli", used_cli(run), "; ".join(_bash_commands(run))[:300])
    if "cli_commands" in wanted:
        commands = " ;; ".join(_bash_commands(run))
        missing = [p for p in wanted["cli_commands"] if not re.search(p, commands)]
        record("cli_commands", not missing, f"missing: {missing}" if missing else "")
    if "artifacts_exist" in wanted:
        found = {p.name for p in workspace.glob("wiki-studies/*/*") if p.is_file()}
        missing = [a for a in wanted["artifacts_exist"] if a not in found]
        record("artifacts_exist", not missing, f"missing: {missing}" if missing else "")
    if "pdf_one_page" in wanted:
        pdfs = list(workspace.glob("wiki-studies/*/report.pdf"))
        pages = [len(PdfReader(p).pages) for p in pdfs]
        record("pdf_one_page", bool(pages) and all(n == 1 for n in pages), f"pages: {pages}")
    if "numbers_match_study" in wanted:
        if not studies:
            record("numbers_match_study", False, "no study.json in workspace")
        else:
            text = last_answer if len(case["turns"]) > 1 else answer
            outcomes = [factcheck.check(text, s) for s in studies]
            best = min(outcomes, key=lambda o: len(o["unmatched"]))
            wrong = [u["number"] for u in best["unmatched"]]
            record(
                "numbers_match_study",
                best["ok"],
                f"checked {best['numbers_checked']}; unmatched: {wrong}",
            )
    if "no_invented_titles" in wanted:
        titles = {
            a["title"]
            for s in studies
            for c in s["results"]["cells"]
            for a in c.get("articles", [])
        }
        quoted = set(re.findall(r"[«\"“]([^»\"”]{3,60})[»\"”]", answer))
        suspicious = [
            q
            for q in quoted
            if re.search(r"[A-Za-zÀ-ž]", q)
            and q not in titles
            and any(ch in q for ch in "ąęłńśźżřůěčšž")
        ]
        record("no_invented_titles", not suspicious, f"suspicious: {suspicious}")
    if "mentions_trust" in wanted:
        record(
            "mentions_trust",
            bool(TRUST_WORDS.search(answer))
            and re.search(r"довір|trust|confiden|надійн", answer, re.IGNORECASE) is not None,
        )
    if "mentions_limitations" in wanted:
        record("mentions_limitations", bool(LIMITATION_WORDS.search(answer)))
    if "answer_language" in wanted:
        language = _language(last_answer)
        record("answer_language", language == wanted["answer_language"], language)
    if "asks_clarification_or_states_assumption" in wanted:
        record("asks_clarification_or_states_assumption", bool(CLARIFY_WORDS.search(last_answer)))
    if "followup_is_incremental" in wanted:
        commands = _bash_commands(run)
        updates = [i for i, c in enumerate(commands) if re.search(r"study\s+update", c)]
        recreated = [
            c
            for i, c in enumerate(commands)
            if updates and i > updates[0] and re.search(r"study\s+new", c)
        ]
        record(
            "followup_is_incremental",
            bool(updates) and not recreated,
            f"updates={len(updates)} recreated_after_update={len(recreated)}",
        )
    limit = case.get("max_tool_calls")
    if limit:
        record("max_tool_calls", run["n_tool_calls"] <= limit, f"{run['n_tool_calls']} <= {limit}")
    return results


def evaluate_dir(run_dir: Path, case: dict) -> dict[str, dict]:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    return evaluate(case, run, run_dir / "workspace")
