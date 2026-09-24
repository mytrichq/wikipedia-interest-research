"""Benchmark orchestrator: runs eval cases and trigger queries, checks, judges, aggregates.

Examples:
    uv run python evals/run.py cases --envs clean --runs 3 --workers 4
    uv run python evals/run.py cases --envs baseline --cases fasting-pl-cs,astronomy-uk-trust
    uv run python evals/run.py triggers --envs clean --runs 3
    uv run python evals/run.py openrouter --model dots-studio/dots-3-note-preview:free --cases ...
    uv run python evals/run.py judge
    uv run python evals/run.py report

Finished runs are skipped, so an interrupted benchmark can be resumed with the same command.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml
from checks import evaluate_dir, skill_triggered
from claude_code import SKILL_DIR, run_case
from judge import judge

EVALS = SKILL_DIR / "evals"
OUT = EVALS / "results" / "benchmark"
TRIGGER_MAX_TURNS = 2


def load_cases() -> dict[str, dict]:
    data = yaml.safe_load((EVALS / "cases.yaml").read_text(encoding="utf-8"))
    return {c["id"]: {**data["defaults"], **c} for c in data["cases"]}


def load_triggers() -> list[dict]:
    data = yaml.safe_load((EVALS / "trigger_queries.yaml").read_text(encoding="utf-8"))
    return [
        {"id": f"{kind}-{i:02d}", "turns": [query], "expect": kind == "should_trigger"}
        for kind in ("should_trigger", "should_not_trigger")
        for i, query in enumerate(data[kind], 1)
    ]


def _run_jobs(jobs: list, workers: int) -> None:
    todo = [j for j in jobs if not (j["dir"] / "run.json").exists()]
    print(f"{len(jobs)} jobs, {len(jobs) - len(todo)} already done, {len(todo)} to run")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(j["fn"]): j for j in todo}
        for number, future in enumerate(as_completed(futures), 1):
            job = futures[future]
            try:
                future.result()
                status = "ok"
            except Exception as exc:
                status = f"FAILED {type(exc).__name__}: {exc}"
            print(f"[{number}/{len(todo)}] {job['dir'].name}: {status}", flush=True)


def cmd_cases(args) -> None:
    cases = load_cases()
    wanted = args.cases.split(",") if args.cases else list(cases)
    jobs = []
    for case_id in wanted:
        case = cases[case_id]
        for env in args.envs.split(","):
            if env not in case["envs"]:
                continue
            runs = args.runs or (1 if env == "realistic" else case["runs"])
            for run in range(1, runs + 1):
                out = OUT / "runs"
                jobs.append(
                    {
                        "dir": out / f"{case_id}__{env}__{args.model}__{run}",
                        "fn": lambda c=case, e=env, r=run, o=out: run_case(c, e, args.model, r, o),
                    }
                )
    _run_jobs(jobs, args.workers)


def cmd_triggers(args) -> None:
    jobs = []
    for query in load_triggers():
        for env in args.envs.split(","):
            for run in range(1, args.runs + 1):
                out = OUT / "triggers"
                jobs.append(
                    {
                        "dir": out / f"{query['id']}__{env}__{args.model}__{run}",
                        "fn": lambda q=query, e=env, r=run, o=out: run_case(
                            q, e, args.model, r, o, timeout=300, max_turns=TRIGGER_MAX_TURNS
                        ),
                    }
                )
    _run_jobs(jobs, args.workers)


def cmd_openrouter(args) -> None:
    for case_id in args.cases.split(","):
        for run in range(1, args.runs + 1):
            subprocess.run(
                [
                    sys.executable,
                    str(EVALS / "openrouter.py"),
                    "--case",
                    case_id,
                    "--model",
                    args.model,
                    "--run",
                    str(run),
                    "--out",
                    str(OUT / "runs"),
                ],
                check=False,
            )


def cmd_judge(args) -> None:
    cases = load_cases()
    jobs = []
    for run_dir in sorted((OUT / "runs").glob("*__*__*__*")):
        case = cases.get(run_dir.name.split("__")[0])
        env = run_dir.name.split("__")[1]
        if not case or not case.get("rubric") or env not in args.envs.split(","):
            continue
        target = run_dir / "judge.json"
        if target.exists() or not (run_dir / "run.json").exists():
            continue

        def task(c=case, d=run_dir, t=target):
            run = json.loads((d / "run.json").read_text(encoding="utf-8"))
            t.write_text(
                json.dumps(judge(c, run, d / "workspace"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        jobs.append({"dir": run_dir, "fn": task})
    todo = [j for j in jobs if not (j["dir"] / "judge.json").exists()]
    print(f"judging {len(todo)} runs")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(j["fn"]) for j in todo]):
            future.result()


def _stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 3),
        "std": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
        "median": round(statistics.median(values), 3),
    }


def aggregate() -> dict:
    cases = load_cases()
    groups: dict[tuple, list] = {}
    for run_dir in sorted((OUT / "runs").glob("*__*__*__*")):
        if not (run_dir / "run.json").exists():
            continue
        case_id, env, model, _ = run_dir.name.split("__")
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        checks = evaluate_dir(run_dir, cases[case_id])
        (run_dir / "checks.json").write_text(
            json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        judged = run_dir / "judge.json"
        groups.setdefault((case_id, env, model), []).append(
            {
                "pass_rate": sum(c["pass"] for c in checks.values()) / max(len(checks), 1),
                "checks": checks,
                "tool_calls": run["n_tool_calls"],
                "tokens": run["usage"].get("input_tokens", 0)
                + run["usage"].get("output_tokens", 0)
                + run["usage"].get("cache_read_input_tokens", 0),
                "seconds": run["duration_s"],
                "cost": run["cost_usd"],
                "errors": len(run.get("errors", [])),
                "judge": json.loads(judged.read_text()) if judged.exists() else None,
            }
        )
    rows = []
    for (case_id, env, model), runs in sorted(groups.items()):
        per_check: dict[str, list] = {}
        for r in runs:
            for name, result in r["checks"].items():
                per_check.setdefault(name, []).append(result["pass"])
        judged = [r["judge"]["mean"] for r in runs if r["judge"] and r["judge"].get("mean")]
        rows.append(
            {
                "case": case_id,
                "env": env,
                "model": model,
                "pass_rate": _stats([r["pass_rate"] for r in runs]),
                "checks": {k: round(sum(v) / len(v), 2) for k, v in per_check.items()},
                "tool_calls": _stats([r["tool_calls"] for r in runs]),
                "tokens": _stats([r["tokens"] for r in runs]),
                "seconds": _stats([r["seconds"] for r in runs]),
                "cost_usd": _stats([r["cost"] for r in runs]),
                "judge_mean": _stats(judged),
            }
        )

    triggers = {}
    for run_dir in sorted((OUT / "triggers").glob("*__*__*__*")):
        if not (run_dir / "run.json").exists():
            continue
        query_id, env, model, _ = run_dir.name.split("__")
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        triggers.setdefault((query_id, env, model), []).append(skill_triggered(run))
    queries = {q["id"]: q for q in load_triggers()}
    trigger_rows = [
        {
            "query": qid,
            "env": env,
            "model": model,
            "expect": queries[qid]["expect"],
            "text": queries[qid]["turns"][0],
            "rate": round(sum(v) / len(v), 2),
            "n": len(v),
            "pass": (sum(v) / len(v) > 0.5) == queries[qid]["expect"],
        }
        for (qid, env, model), v in sorted(triggers.items())
    ]
    return {"cases": rows, "triggers": trigger_rows}


def _fmt(stat: dict, pct: bool = False, digits: int = 0) -> str:
    if not stat.get("n"):
        return "—"
    mean, std = stat["mean"], stat["std"]
    if pct:
        return f"{mean:.0%} ± {std:.0%}" if stat["n"] > 1 else f"{mean:.0%}"
    return f"{mean:.{digits}f} ± {std:.{digits}f}" if stat["n"] > 1 else f"{mean:.{digits}f}"


def render(result: dict) -> str:
    lines = [
        "# Benchmark",
        "",
        "Generated by `uv run python evals/run.py report`. "
        "Pass rate = share of deterministic checks passed per run (mean ± std over runs).",
        "",
        "## Scenarios",
        "",
        "| Case | Env | Model | Runs | Pass rate | Judge (1-5) | Tool calls | Tokens | Time, s "
        "| Cost, $ |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in result["cases"]:
        lines.append(
            f"| {r['case']} | {r['env']} | {r['model']} | {r['pass_rate']['n']} | "
            f"{_fmt(r['pass_rate'], pct=True)} | {_fmt(r['judge_mean'], digits=1)} | "
            f"{_fmt(r['tool_calls'], digits=1)} | {_fmt(r['tokens'])} | "
            f"{_fmt(r['seconds'])} | {_fmt(r['cost_usd'], digits=3)} |"
        )
    by_env: dict[tuple, dict[str, list]] = {}
    for r in result["cases"]:
        bucket = by_env.setdefault((r["env"], r["model"]), {})
        for check, rate in r["checks"].items():
            bucket.setdefault(check, []).append(rate)
    lines += [
        "",
        "## Checks by environment",
        "",
        "| Env | Model | Check | Pass rate |",
        "|---|---|---|---|",
    ]
    for (env, model), checks in sorted(by_env.items()):
        for check, rates in sorted(checks.items()):
            lines.append(f"| {env} | {model} | {check} | {statistics.mean(rates):.0%} |")
    if result["triggers"]:
        lines += ["", "## Triggering", ""]
        summary: dict[tuple, list] = {}
        for t in result["triggers"]:
            summary.setdefault((t["env"], t["model"], t["expect"]), []).append(t)
        lines += [
            "| Env | Model | Queries | Correct | Mean trigger rate |",
            "|---|---|---|---|---|",
        ]
        for (env, model, expect), items in sorted(summary.items()):
            kind = "should trigger" if expect else "should NOT trigger"
            correct = sum(i["pass"] for i in items)
            rate = statistics.mean(i["rate"] for i in items)
            lines.append(
                f"| {env} | {model} | {kind} ({len(items)}) | {correct}/{len(items)} | {rate:.0%} |"
            )
        misses = [t for t in result["triggers"] if not t["pass"]]
        if misses:
            lines += ["", "Misclassified queries:", ""]
            lines += [
                f"- `{t['env']}` rate {t['rate']:.0%}, expected "
                f"{'trigger' if t['expect'] else 'no trigger'}: {t['text']}"
                for t in misses
            ]
    return "\n".join(lines) + "\n"


def cmd_report(args) -> None:
    result = aggregate()
    (OUT / "benchmark.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "benchmark.md").write_text(render(result), encoding="utf-8")
    print(render(result))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("cases", cmd_cases), ("triggers", cmd_triggers)):
        p = sub.add_parser(name)
        p.add_argument("--envs", default="clean")
        p.add_argument("--runs", type=int, default=None if name == "cases" else 3)
        p.add_argument("--cases", default="")
        p.add_argument("--model", default="haiku")
        p.add_argument("--workers", type=int, default=4)
        p.set_defaults(fn=fn)
    p = sub.add_parser("openrouter")
    p.add_argument("--model", required=True)
    p.add_argument("--cases", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.set_defaults(fn=cmd_openrouter)
    p = sub.add_parser("judge")
    p.add_argument("--envs", default="clean,baseline")
    p.add_argument("--workers", type=int, default=3)
    p.set_defaults(fn=cmd_judge)
    p = sub.add_parser("report")
    p.set_defaults(fn=cmd_report)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
