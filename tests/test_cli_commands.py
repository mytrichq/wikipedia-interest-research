import json

import pytest

from wir import cli


@pytest.fixture
def run(cassette_client, monkeypatch, capsys):
    def invoke(cassette: str, *argv: str):
        monkeypatch.setattr(cli, "open_client", lambda: cassette_client(cassette))
        code = cli.main(list(argv))
        out, err = capsys.readouterr()
        return code, (json.loads(out) if out.strip() else None), err

    return invoke


def test_resolve_prints_json_and_request_stats(run):
    code, out, err = run(
        "cli_resolve", "resolve", "--topic", "intermittent fasting", "--langs", "pl,cs"
    )
    assert code == cli.EXIT_OK
    assert out["concept"]["qid"] == "Q1666254"
    assert [a["status"] for a in out["articles"]] == ["missing", "found"]
    assert "wir: requests" in err


def test_resolve_needs_topic_or_qid(run):
    code, out, err = run("unused", "resolve", "--langs", "uk")
    assert code == cli.EXIT_BAD_INPUT
    assert "--topic" in err


def test_unknown_language_is_bad_input_with_hint(run):
    code, _, err = run("unused", "resolve", "--topic", "astronomy", "--langs", "uk,polsh")
    assert code == cli.EXIT_BAD_INPUT
    assert "Did you mean" in err


def test_views_monthly(run):
    code, out, _ = run(
        "cli_views", "views", "--lang", "uk", "--article", "Астрономія",
        "--period", "2024-01..2026-08",
    )  # fmt: skip
    assert code == cli.EXIT_OK
    assert out["monthly"][0] == ["2024-01", 3700]
    assert out["monthly"][-1] == ["2026-08", 360]
    assert len(out["monthly"]) == 32
    assert out["total_views"] == sum(v for _, v in out["monthly"])


def test_views_unknown_article(run):
    code, out, _ = run("cli_views_missing", "views", "--lang", "uk", "--article", "Qwzxkjv plorf")
    assert code == cli.EXIT_NOT_FOUND
    assert out["status"] == "not_found"


def test_views_daily_refuses_to_flood_the_terminal(run):
    code, _, err = run(
        "cli_views", "views", "--lang", "uk", "--article", "Астрономія",
        "--period", "2024-01..2026-08", "--granularity", "daily",
    )  # fmt: skip
    assert code == cli.EXIT_BAD_INPUT
    assert "--csv" in err


def test_views_daily_csv(run, tmp_path):
    target = tmp_path / "daily.csv"
    code, out, _ = run(
        "cli_views", "views", "--lang", "uk", "--article", "Астрономія",
        "--period", "2024-01..2026-08", "--granularity", "daily", "--csv", str(target),
    )  # fmt: skip
    assert code == cli.EXIT_OK
    lines = target.read_text().splitlines()
    assert lines[0] == "date,views"
    assert len(lines) == 1 + 974
    assert "daily" not in out


def test_analyze_uk_astronomy_is_a_trusted_seasonal_decline(run):
    code, out, _ = run(
        "cli_analyze", "analyze", "--lang", "uk", "--article", "Астрономія",
        "--period", "2024-09..2026-08",
    )  # fmt: skip
    assert code == cli.EXIT_OK
    assert out["verdict"] == "declining"
    assert out["seasonality"]["peak_month"] == "September"
    assert out["seasonality"]["strong"] is True
    assert out["growth"]["months_up"] <= 1
    assert out["trust"]["level"] == "High"
    assert len(out["monthly"]) == 24
