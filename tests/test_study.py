import json

import pytest

from wir import cli, languages, study


@pytest.fixture
def run(cassette_client, monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)

    def invoke(cassette: str, *argv: str):
        client = cassette_client(cassette)
        monkeypatch.setattr(cli, "open_client", lambda: client)
        code = cli.main(list(argv))
        out, err = capsys.readouterr()
        return code, (json.loads(out) if out.strip() else None), err, client

    return invoke


def by_key(summary):
    return {row["key"]: row for row in summary["results"]}


def test_new_update_show_list_keeps_memory(run, tmp_path):
    code, out, _, _ = run(
        "study_astronomy",
        "study",
        "new",
        "--topic",
        "astronomy",
        "--langs",
        "uk",
        "--question",
        "Is interest in astronomy growing?",
    )
    assert code == cli.EXIT_OK
    assert out["study"] == "astronomy-uk"
    assert by_key(out)["uk"]["verdict"] == "declining"
    assert (tmp_path / "wiki-studies" / "astronomy-uk" / "data" / "monthly.csv").exists()

    code, out, _, client = run(
        "study_astronomy_add_pl", "study", "update", "astronomy-uk", "--add-lang", "pl"
    )
    assert out["changes"] == ["added language pl"]
    assert set(by_key(out)) == {"uk", "pl"}
    assert [r["rank"] for r in out["ranking"]] == [1, 2]
    assert client.stats.cached > client.stats.network

    code, out, _, client = run("unused", "study", "show", "astronomy-uk")
    assert client.stats.network == 0
    assert out["history"] == ["created", "added language pl"]
    assert out["question"] == "Is interest in astronomy growing?"
    assert any("Q333" in a for a in out["assumptions"])

    code, out, _, _ = run("unused", "study", "list")
    assert [s["id"] for s in out["studies"]] == ["astronomy-uk"]


def test_missing_article_then_labelled_proxy(run):
    code, out, _, _ = run(
        "study_fasting", "study", "new", "--topic", "intermittent fasting", "--langs", "pl,cs"
    )
    rows = by_key(out)
    assert rows["pl"]["status"] == "missing"
    assert "Głodówka lecznicza" in rows["pl"]["proxy_candidates"]
    assert rows["cs"]["articles"] == ["Přerušovaný půst"]
    assert [r["key"] for r in out["ranking"]] == ["cs"]

    code, out, _, _ = run(
        "study_fasting_proxy",
        "study",
        "update",
        "intermittent-fasting-pl-cs",
        "--article",
        "pl:Głodówka lecznicza",
    )
    assert by_key(out)["pl"]["articles"] == ["Głodówka lecznicza (PROXY)"]
    assert any(a.startswith("PROXY: pl") for a in out["assumptions"])


def test_ambiguous_topic_does_not_create_a_study(run, tmp_path):
    code, out, _, _ = run(
        "study_mercury",
        "study",
        "new",
        "--topic",
        "Меркурій",
        "--topic-lang",
        "uk",
        "--langs",
        "uk",
    )
    assert code == cli.EXIT_OK
    assert out["status"] == "needs_choice"
    assert "--topic Q308" in out["next_step"]
    assert not (tmp_path / "wiki-studies").exists()


def test_existing_study_is_not_overwritten(run):
    run("study_astronomy", "study", "new", "--topic", "astronomy", "--langs", "uk")
    code, _, err, _ = run(
        "study_astronomy", "study", "new", "--topic", "astronomy", "--langs", "uk"
    )
    assert code == cli.EXIT_BAD_INPUT
    assert "study update" in err


def test_unknown_study_lists_known_ones(run):
    code, _, err, _ = run("unused", "study", "show", "nope")
    assert code == cli.EXIT_BAD_INPUT
    assert "study list" in err


def test_update_without_changes_is_rejected(run):
    run("study_astronomy", "study", "new", "--topic", "astronomy", "--langs", "uk")
    code, _, err, _ = run("unused", "study", "update", "astronomy-uk")
    assert code == cli.EXIT_BAD_INPUT
    assert "--add-lang" in err


@pytest.mark.parametrize(
    ("value", "topics", "expected"),
    [
        ("pl:Głodówka lecznicza", 1, {"topic": 0, "lang": "pl", "title": "Głodówka lecznicza"}),
        ("2:pl:'Foo: bar'", 2, {"topic": 1, "lang": "pl", "title": "Foo: bar"}),
    ],
)
def test_parse_proxy(value, topics, expected):
    assert study.parse_proxy(value, topics) == expected


def test_parse_proxy_needs_topic_number_when_ambiguous():
    with pytest.raises(ValueError, match="2:pl:Title"):
        study.parse_proxy("pl:Title", 2)


def test_slugify_is_ascii():
    assert study.slugify("Přerušovaný půst-uk-pl") == "prerusovany-pust-uk-pl"
    assert study.slugify("Астрономія") == "study"


def test_hidden_countries_turn_the_readers_split_into_a_warning():
    assert languages.hidden_reader_countries("tr") == ["Türkiye (TR)"]
    assert languages.hidden_reader_countries("pl") == []
    context = {
        "top_reader_countries": [{"country": "US", "share": 0.31}],
        "hidden_countries": ["Türkiye (TR)"],
    }
    assert study.readers_text(context).startswith("MISLEADING WITHOUT CAVEAT")


def test_update_reports_what_changed(run):
    run("study_astronomy", "study", "new", "--topic", "astronomy", "--langs", "uk")
    code, out, _, _ = run(
        "study_astronomy_add_pl", "study", "update", "astronomy-uk", "--add-lang", "pl"
    )
    assert out["changes_since_previous_state"] == ["pl: new in this update"]
