"""Runs one eval case in headless Claude Code, isolated from the repo (see docs/TEST_PLAN.md).

Usage: uv run python evals/claude_code.py --case astronomy-uk-trust --env baseline --model haiku
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_NAME = SKILL_DIR.name
CASES_FILE = SKILL_DIR / "evals" / "cases.yaml"
ALLOWED_TOOLS = "Bash Read Write Edit Glob Grep WebFetch WebSearch Skill"
RESULT_PREVIEW = 1500
SHIPPED = [
    "SKILL.md",
    "LICENSE",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "scripts",
    "src",
    "references",
    "assets",
]


def load_case(case_id: str) -> dict:
    data = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))
    for case in data["cases"]:
        if case["id"] == case_id:
            return {**data["defaults"], **case}
    known = ", ".join(c["id"] for c in data["cases"])
    sys.exit(f"Error: unknown case '{case_id}'. Known cases: {known}")


def package_skill(dest: Path) -> None:
    ignore = shutil.ignore_patterns("__pycache__", ".venv", "*.pyc")
    dest.mkdir(parents=True)
    for item in SHIPPED:
        src = SKILL_DIR / item
        if src.is_dir():
            shutil.copytree(src, dest / item, ignore=ignore)
        elif src.exists():
            shutil.copy2(src, dest / item)


def prepare_workspace(workspace: Path, env: str) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    if env in ("clean", "realistic"):
        package_skill(workspace / ".claude" / "skills" / SKILL_NAME)


def collect_artifacts(workspace: Path, dest: Path) -> None:
    shutil.copytree(workspace, dest, ignore=shutil.ignore_patterns(".claude"))


def claude_command(
    env: str, model: str, prompt: str, resume: str | None, persist: bool
) -> list[str]:
    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "stream-json",
        "--verbose",
        "--allowedTools",
        ALLOWED_TOOLS,
        "--max-turns",
        "40",
    ]
    if env in ("baseline", "clean"):
        cmd += ["--setting-sources", "project", "--strict-mcp-config"]
    if resume:
        cmd += ["--resume", resume]
    if not persist:
        cmd += ["--no-session-persistence"]
    return cmd


def run_turns(case: dict, env: str, model: str, workspace: Path, timeout: int) -> list[dict]:
    prepare_workspace(workspace, env)
    events: list[dict] = []
    session_id = None
    multi_turn = len(case["turns"]) > 1
    for turn, prompt in enumerate(case["turns"], start=1):
        started = time.monotonic()
        proc = subprocess.run(
            claude_command(env, model, prompt, session_id, persist=multi_turn),
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            event["_turn"] = turn
            events.append(event)
            if event.get("type") == "system" and event.get("session_id"):
                session_id = event["session_id"]
        if proc.returncode != 0 and not any(e.get("type") == "result" for e in events):
            events.append({"type": "error", "_turn": turn, "stderr": proc.stderr[-2000:]})
        elapsed = time.monotonic() - started
        events.append({"type": "_turn_timing", "_turn": turn, "seconds": elapsed})
    return events


def summarize(events: list[dict]) -> dict:
    tool_calls, skills_used, answers = [], [], []
    cost = duration = 0.0
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
    for event in events:
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "turn": event["_turn"],
                            "tool": block["name"],
                            "input": block.get("input", {}),
                        }
                    )
                    if block["name"] == "Skill":
                        skills_used.append(block.get("input", {}).get("skill"))
        elif event.get("type") == "result":
            answers.append(event.get("result", ""))
            cost += event.get("total_cost_usd") or 0
            duration += (event.get("duration_ms") or 0) / 1000
            for key in usage:
                usage[key] += (event.get("usage") or {}).get(key, 0)
    return {
        "tool_calls": tool_calls,
        "n_tool_calls": len(tool_calls),
        "skills_used": skills_used,
        "final_answers": answers,
        "cost_usd": round(cost, 4),
        "duration_s": round(duration, 1),
        "usage": usage,
        "errors": [e for e in events if e.get("type") == "error"],
    }


def render_markdown(case: dict, env: str, model: str, events: list[dict], summary: dict) -> str:
    out = [
        f"# {case['id']} — env `{env}`, model `{model}`",
        "",
        f"- Tool calls: **{summary['n_tool_calls']}**, "
        f"skills used: {summary['skills_used'] or 'none'}",
        f"- Cost: ${summary['cost_usd']}, duration: {summary['duration_s']} s, "
        f"tokens in/out: {summary['usage']['input_tokens']}/{summary['usage']['output_tokens']} "
        f"(cache read {summary['usage']['cache_read_input_tokens']})",
        "",
    ]
    turn = 0
    for event in events:
        if event.get("_turn") != turn:
            turn = event["_turn"]
            out += [f"## Turn {turn}", "", f"> **User:** {case['turns'][turn - 1]}", ""]
        kind = event.get("type")
        if kind == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "text" and block["text"].strip():
                    out += [f"**Assistant:** {block['text'].strip()}", ""]
                elif block.get("type") == "tool_use":
                    payload = json.dumps(block.get("input", {}), ensure_ascii=False, indent=2)
                    out += [f"**Tool call — {block['name']}**", "```json", payload, "```", ""]
        elif kind == "user":
            for block in event["message"].get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    content = block.get("content")
                    if isinstance(content, list):
                        parts = [c.get("text", "") for c in content if isinstance(c, dict)]
                        content = "\n".join(parts)
                    text = str(content or "")
                    if len(text) > RESULT_PREVIEW:
                        cut = len(text) - RESULT_PREVIEW
                        text = text[:RESULT_PREVIEW] + f"\n… [{cut} chars cut]"
                    out += [
                        "<details><summary>Tool result</summary>",
                        "",
                        "```",
                        text,
                        "```",
                        "</details>",
                        "",
                    ]
        elif kind == "result":
            out += ["### Final answer", "", event.get("result", ""), ""]
        elif kind == "error":
            out += ["### Error", "```", event["stderr"], "```", ""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", required=True)
    parser.add_argument("--env", choices=["baseline", "clean", "realistic"], required=True)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--run", type=int, default=1, help="repetition index")
    parser.add_argument("--out", type=Path, default=SKILL_DIR / "evals" / "results" / "runs")
    parser.add_argument("--timeout", type=int, default=900, help="seconds per turn")
    args = parser.parse_args()

    case = load_case(args.case)
    run_dir = args.out / f"{args.case}__{args.env}__{args.model}__{args.run}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    sandbox = Path(tempfile.mkdtemp(prefix="wir-eval-"))
    try:
        events = run_turns(case, args.env, args.model, sandbox / "workspace", args.timeout)
        collect_artifacts(sandbox / "workspace", run_dir / "workspace")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
    summary = summarize(events)
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in events), encoding="utf-8"
    )
    (run_dir / "run.json").write_text(
        json.dumps(
            {"case": args.case, "env": args.env, "model": args.model, "run": args.run, **summary},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "transcript.md").write_text(
        render_markdown(case, args.env, args.model, events, summary), encoding="utf-8"
    )
    print(
        f"{run_dir}: {summary['n_tool_calls']} tool calls, ${summary['cost_usd']}, "
        f"{summary['duration_s']} s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
