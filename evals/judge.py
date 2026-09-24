"""LLM judge (docs/TEST_PLAN.md, section 6): scores an answer 1-5 per rubric criterion."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

GENERAL_RUBRIC = [
    "Answers the user's actual question directly.",
    "Recommendations and claims rest on the provided data, not on the model's general knowledge.",
    "Limitations are named concretely (e.g. a language edition is not a country, article "
    "interest is not willingness to pay, seasonality, missing articles).",
    "Clear for a founder without an analytics background, in natural wording in the user's "
    "language (no words from other languages, no invented words).",
]

PROMPT = """You are grading an AI assistant's answer in an evaluation. Be strict and fair.

USER TURNS:
{turns}

FACTS THE ASSISTANT HAD (tool output; the only legitimate source of numbers):
{facts}

GROUND TRUTH NOTES FOR THE GRADER:
{notes}

ASSISTANT'S FINAL ANSWER:
{answer}

Score each criterion from 1 (fails) to 5 (fully meets), with a one-sentence reason:
{criteria}

Reply with JSON only, no prose, in exactly this shape:
{{"scores": [{{"criterion": "<text>", "score": <1-5>, "reason": "<one sentence>"}}]}}"""


def facts_for(workspace: Path) -> str:
    from wir.study import summarize

    studies = sorted(workspace.glob("wiki-studies/*/study.json"))
    if not studies:
        return "(no study was created, so the assistant had no tool data)"
    summaries = [summarize(json.loads(p.read_text(encoding="utf-8"))) for p in studies]
    for summary in summaries:
        summary.pop("next_steps", None)
    return json.dumps(summaries, ensure_ascii=False)[:12000]


def judge(case: dict, run: dict, workspace: Path, model: str = "sonnet") -> dict:
    criteria = case.get("rubric", []) + GENERAL_RUBRIC
    prompt = PROMPT.format(
        turns="\n".join(f"{i}. {t}" for i, t in enumerate(case["turns"], 1)),
        facts=facts_for(workspace),
        notes=case.get("notes", "(none)"),
        answer=(run["final_answers"] or ["(no answer)"])[-1][:8000],
        criteria="\n".join(f"- {c}" for c in criteria),
    )
    with tempfile.TemporaryDirectory(prefix="wir-judge-") as folder:
        proc = subprocess.run(
            [
                "claude",
                "-p",
                prompt,
                "--model",
                model,
                "--output-format",
                "json",
                "--max-turns",
                "1",
                "--setting-sources",
                "project",
                "--strict-mcp-config",
                "--disable-slash-commands",
                "--no-session-persistence",
            ],
            cwd=folder,
            capture_output=True,
            text=True,
            timeout=600,
        )
    try:
        text = json.loads(proc.stdout)["result"]
        scores = json.loads(re.search(r"\{.*\}", text, re.S).group(0))["scores"]
    except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
        return {"error": (proc.stdout or proc.stderr)[-1000:], "scores": []}
    rubric_count = len(case.get("rubric", []))
    for index, score in enumerate(scores):
        score["kind"] = "case" if index < rubric_count else "general"
    return {
        "model": model,
        "scores": scores,
        "mean": round(sum(s["score"] for s in scores) / max(len(scores), 1), 2),
    }
