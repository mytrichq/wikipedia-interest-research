"""Minimal tool-calling agent for OpenRouter models that loads Agent Skills per the spec.

The model sees only each skill's name, description and SKILL.md location (progressive
disclosure); it reads SKILL.md itself with read_file and runs the skill's scripts with bash.

Usage:
    uv run python dev/harness/agent.py --model google/gemma-4-31b-it:free \\
        --skills path/to/skills --workspace /tmp/ws "Чи росте інтерес до астрономії в uk?"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "HTTP-Referer": "https://github.com/mytrichq/wikipedia-interest-research",
    "X-Title": "wikipedia-interest-research eval harness",
}
REPO = Path(__file__).resolve().parents[2]
OUTPUT_LIMIT = 12_000
MAX_STEPS = 25
MAX_NUDGES = 2
NUDGE = "Continue the task. If you have finished, write your final answer to the user now."
RETRY_DELAYS = (5, 15, 30, 60, 90)
SECRET_ENV = re.compile(r"KEY|TOKEN|SECRET|PASSWORD", re.I)
FORBIDDEN = re.compile(r"\bsudo\b|rm\s+-rf\s+(/|~)|\bmkfs\b|:\(\)\s*\{|\bshutdown\b|>\s*/dev/sd")

SYSTEM_PROMPT = """You are a capable assistant working in a terminal. The working directory \
is {workspace}. Use the tools to act; do not describe commands without running them.

Skills extend what you can do. When the user's request matches a skill's description, \
first read that skill's SKILL.md with read_file and follow its instructions exactly. \
Paths inside a skill are relative to the skill's directory (the folder containing SKILL.md).

{skills}"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "integer", "description": "seconds, default 300"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file (absolute path or relative to the working directory).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
]
CLAUDE_NAMES = {"bash": "Bash", "read_file": "Read", "write_file": "Write"}


def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    env_file = REPO / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("Error: OPENROUTER_API_KEY is not set (put it in .env, see .env.example).")
    return key


def skills_block(skills_dir: Path) -> str:
    """<available_skills> in the format of `skills-ref to-prompt`."""
    entries = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        front = re.match(r"^---\n(.*?)\n---", text, re.S).group(1)
        fields = dict(re.findall(r"^(name|description):\s*(.+)$", front, re.M))
        entries.append(
            f"<skill>\n<name>{fields['name']}</name>\n<description>{fields['description']}"
            f"</description>\n<location>{skill_md}</location>\n</skill>"
        )
    return "<available_skills>\n" + "\n".join(entries) + "\n</available_skills>" if entries else ""


def scrubbed_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not SECRET_ENV.search(k)}


@dataclass
class Session:
    model: str
    workspace: Path
    skills_dir: Path | None
    events: list[dict] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    cost: float = 0.0

    def __post_init__(self) -> None:
        skills = skills_block(self.skills_dir) if self.skills_dir else ""
        prompt = SYSTEM_PROMPT.format(workspace=self.workspace, skills=skills)
        self.messages.append({"role": "system", "content": prompt})
        self._http = httpx.Client(timeout=httpx.Timeout(180.0, connect=15.0))
        self._key = api_key()

    def _complete(self) -> dict:
        body = {
            "model": self.model,
            "messages": self.messages,
            "tools": TOOLS,
            "usage": {"include": True},
        }
        for attempt, delay in enumerate((0, *RETRY_DELAYS)):
            time.sleep(delay)
            try:
                response = self._http.post(
                    API_URL, json=body, headers=HEADERS | {"Authorization": f"Bearer {self._key}"}
                )
                data = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                self.events.append({"type": "retry", "attempt": attempt, "error": str(exc)})
                continue
            error = data.get("error")
            if error and int(error.get("code") or 0) in (408, 429, 500, 502, 503, 504):
                self.events.append({"type": "retry", "attempt": attempt, "error": error})
                continue
            if error or not data.get("choices"):
                raise RuntimeError(f"OpenRouter error: {error or data}")
            return data
        raise RuntimeError(f"OpenRouter kept failing for {self.model}; see events.")

    def _tool(self, name: str, args: dict) -> str:
        try:
            if name == "bash":
                command = args["command"]
                if FORBIDDEN.search(command):
                    return "Refused: this command is not allowed in the harness."
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=int(args.get("timeout") or 300),
                    env=scrubbed_env(),
                )
                out = f"exit code {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            elif name == "read_file":
                path = Path(args["path"])
                out = (path if path.is_absolute() else self.workspace / path).read_text(
                    encoding="utf-8"
                )
            elif name == "write_file":
                path = Path(args["path"])
                target = path if path.is_absolute() else self.workspace / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(args["content"], encoding="utf-8")
                out = f"Wrote {len(args['content'])} characters to {target}"
            else:
                out = f"Unknown tool {name}"
        except Exception as exc:
            out = f"Tool error: {type(exc).__name__}: {exc}"
        if len(out) > OUTPUT_LIMIT:
            out = out[:OUTPUT_LIMIT] + f"\n… [{len(out) - OUTPUT_LIMIT} characters cut]"
        return out

    def ask(self, prompt: str, turn: int) -> str:
        self.messages.append({"role": "user", "content": prompt})
        self.events.append({"type": "user", "turn": turn, "content": prompt})
        nudges = 0
        for _ in range(MAX_STEPS):
            data = self._complete()
            usage = data.get("usage") or {}
            self.usage["input_tokens"] += usage.get("prompt_tokens", 0)
            self.usage["output_tokens"] += usage.get("completion_tokens", 0)
            self.cost += float(usage.get("cost") or 0)
            message = data["choices"][0]["message"]
            calls = message.get("tool_calls") or []
            self.messages.append(
                {k: v for k, v in message.items() if k in ("role", "content", "tool_calls")}
            )
            if message.get("content"):
                self.events.append(
                    {"type": "assistant", "turn": turn, "content": message["content"]}
                )
            if not calls:
                content = (message.get("content") or "").strip()
                if content or nudges >= MAX_NUDGES:
                    return content
                nudges += 1
                self.messages.append({"role": "user", "content": NUDGE})
                self.events.append({"type": "nudge", "turn": turn})
                continue
            for call in calls:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._tool(name, args)
                self.events.append(
                    {
                        "type": "tool",
                        "turn": turn,
                        "tool": CLAUDE_NAMES.get(name, name),
                        "input": args,
                        "result": result,
                    }
                )
                self.messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        return "(stopped: step limit reached)"


def summarize(session: Session, answers: list[str], seconds: float) -> dict:
    calls = [
        {"turn": e["turn"], "tool": e["tool"], "input": e["input"]}
        for e in session.events
        if e["type"] == "tool"
    ]
    return {
        "tool_calls": calls,
        "n_tool_calls": len(calls),
        "skills_used": sorted(
            {
                Path(c["input"].get("path", "")).parent.name
                for c in calls
                if c["tool"] == "Read" and c["input"].get("path", "").endswith("SKILL.md")
            }
        ),
        "final_answers": answers,
        "cost_usd": round(session.cost, 4),
        "duration_s": round(seconds, 1),
        "usage": session.usage,
        "errors": [e for e in session.events if e["type"] == "retry"],
    }


def render(model: str, turns: list[str], events: list[dict], summary: dict) -> str:
    out = [
        f"# OpenRouter run — `{model}`",
        "",
        f"- Tool calls: **{summary['n_tool_calls']}**, tokens in/out: "
        f"{summary['usage']['input_tokens']}/{summary['usage']['output_tokens']}, "
        f"cost ${summary['cost_usd']}, {summary['duration_s']} s, retries {len(summary['errors'])}",
        "",
    ]
    for event in events:
        if event["type"] == "user":
            out += [f"## Turn {event['turn']}", "", f"> **User:** {event['content']}", ""]
        elif event["type"] == "assistant":
            out += [f"**Assistant:** {event['content']}", ""]
        elif event["type"] == "tool":
            result = event["result"][:1500]
            out += [
                f"**Tool call — {event['tool']}**",
                "```json",
                json.dumps(event["input"], ensure_ascii=False, indent=2)[:3000],
                "```",
                "<details><summary>Tool result</summary>",
                "",
                "```",
                result,
                "```",
                "</details>",
                "",
            ]
    return "\n".join(out)


def run(
    model: str, turns: list[str], workspace: Path, skills_dir: Path | None
) -> tuple[list, dict]:
    session = Session(model, workspace, skills_dir)
    started, answers = time.monotonic(), []
    for turn, prompt in enumerate(turns, start=1):
        try:
            answers.append(session.ask(prompt, turn))
        except RuntimeError as exc:
            session.events.append({"type": "retry", "turn": turn, "error": str(exc)})
            answers.append(f"(harness error: {exc})")
            break
    return session.events, summarize(session, answers, time.monotonic() - started)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prompt", nargs="+", help="one or more user turns")
    parser.add_argument("--model", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--skills", type=Path, help="directory that contains skill folders")
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=True)
    events, summary = run(args.model, args.prompt, args.workspace.resolve(), args.skills)
    print(render(args.model, args.prompt, events, summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
