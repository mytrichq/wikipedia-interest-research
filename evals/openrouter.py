"""Runs one eval case with an OpenRouter model through dev/harness/agent.py, isolated like
evals/claude_code.py, and writes the same run.json / transcript.md / events.jsonl.

Usage:
    uv run python evals/openrouter.py --case astronomy-uk-trust --model google/gemma-4-31b-it:free
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from claude_code import SKILL_DIR, collect_artifacts, load_case, prepare_workspace

sys.path.insert(0, str(SKILL_DIR / "dev" / "harness"))
agent = importlib.import_module("agent")


def slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one eval case on an OpenRouter model.")
    parser.add_argument("--case", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--env", choices=["baseline", "clean"], default="clean")
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--out", type=Path, default=SKILL_DIR / "evals" / "results" / "runs")
    args = parser.parse_args()

    case = load_case(args.case)
    run_dir = args.out / f"{args.case}__{args.env}__{slug(args.model)}__{args.run}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    sandbox = Path(tempfile.mkdtemp(prefix="wir-eval-"))
    try:
        workspace = sandbox / "workspace"
        prepare_workspace(workspace, args.env)
        skills = workspace / ".claude" / "skills" if args.env == "clean" else None
        events, summary = agent.run(args.model, case["turns"], workspace, skills)
        collect_artifacts(workspace, run_dir / "workspace")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)

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
        agent.render(args.model, case["turns"], events, summary), encoding="utf-8"
    )
    print(
        f"{run_dir}: {summary['n_tool_calls']} tool calls, {summary['usage']}, "
        f"{summary['duration_s']} s, retries {len(summary['errors'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
