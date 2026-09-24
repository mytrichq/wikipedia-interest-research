import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dev" / "harness"))
agent = importlib.import_module("agent")
SKILL_DIR = Path(__file__).resolve().parents[1]


def reply(content="", calls=()):
    tool_calls = [
        {"id": f"c{i}", "type": "function", "function": {"name": name, "arguments": args}}
        for i, (name, args) in enumerate(calls)
    ]
    message = {"role": "assistant", "content": content, "tool_calls": tool_calls or None}
    return {
        "choices": [{"message": message}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    return agent.Session("test/model", tmp_path, None)


def test_skills_are_advertised_by_name_description_and_location(tmp_path):
    (tmp_path / "wikipedia-interest-research").symlink_to(SKILL_DIR)
    block = agent.skills_block(tmp_path)
    assert "<name>wikipedia-interest-research</name>" in block
    assert "Measures and compares audience interest" in block
    assert "SKILL.md</location>" in block
    assert "## Workflow" not in block


def test_tool_loop_runs_commands_and_returns_the_final_answer(session, monkeypatch):
    replies = [reply(calls=[("bash", '{"command": "echo hello"}')]), reply("Done: hello")]
    monkeypatch.setattr(session, "_complete", lambda: replies.pop(0))
    assert session.ask("say hello", 1) == "Done: hello"
    tool = next(e for e in session.events if e["type"] == "tool")
    assert tool["tool"] == "Bash" and "hello" in tool["result"]
    assert session.usage == {"input_tokens": 20, "output_tokens": 10}


def test_silent_model_is_nudged_to_continue(session, monkeypatch):
    replies = [reply(""), reply("Finished.")]
    monkeypatch.setattr(session, "_complete", lambda: replies.pop(0))
    assert session.ask("do it", 1) == "Finished."
    assert [e["type"] for e in session.events].count("nudge") == 1


def test_secrets_are_not_visible_to_model_commands(session, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-value")
    out = session._tool("bash", {"command": "env"})
    assert "secret-value" not in out


@pytest.mark.parametrize("command", ["sudo ls", "rm -rf /", "rm -rf ~/x", "mkfs.ext4 /dev/x"])
def test_destructive_commands_are_refused(session, command):
    assert session._tool("bash", {"command": command}).startswith("Refused")


def test_long_output_is_truncated(session):
    out = session._tool("bash", {"command": "python3 -c 'print(\"x\" * 20000)'"})
    assert "characters cut" in out and len(out) < agent.OUTPUT_LIMIT + 100
