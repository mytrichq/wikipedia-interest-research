import json

import pytest
from pypdf import PdfReader

from wir import cli, report

GOOD = """# Headline
Інтерес до інтервального голодування спадає в cs (−49%), а в pl статті немає.

## Findings
- cs: 0 з 12 місяців вище, ніж рік тому; довіра висока (80).
- pl: окремої статті немає, «Głodówka lecznicza» — лише проксі.

## Next steps
- Перевірити пошукові запити в Польщі та Чехії.
"""


@pytest.fixture
def run(cassette_client, monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    client = cassette_client("report_fasting")
    monkeypatch.setattr(cli, "open_client", lambda: client)

    def invoke(*argv: str):
        code = cli.main(list(argv))
        out, err = capsys.readouterr()
        return code, (json.loads(out) if out.strip() else None), err

    invoke(
        "study",
        "new",
        "--topic",
        "intermittent fasting",
        "--langs",
        "pl,cs",
        "--article",
        "pl:Głodówka lecznicza",
        "--question",
        "Порівняй PL і CS",
    )
    return invoke


def pdf_text(path) -> tuple[int, str]:
    reader = PdfReader(path)
    return len(reader.pages), "\n".join(page.extract_text() for page in reader.pages)


def test_report_with_narrative_is_one_page_with_all_sections(run, tmp_path):
    (tmp_path / "n.md").write_text(GOOD, encoding="utf-8")
    code, out, _ = run("report", "intermittent-fasting-pl-cs", "--narrative", "n.md")
    assert code == cli.EXIT_OK
    assert out["report_language"] == "uk"
    assert out["factcheck"]["ok"] and out["factcheck"]["numbers_checked"] >= 2
    pages, text = pdf_text(out["pdf"])
    assert pages == 1
    for needle in [
        "Ключові спостереження",
        "Що дослідити далі",
        "Припущення та обмеження",
        "Přerušovaný půst",
        "Głodówka",
        "проксі",
        "Wikimedia",
    ]:
        assert needle in text, needle
    summary = (tmp_path / "wiki-studies" / "intermittent-fasting-pl-cs" / "summary.md").read_text()
    assert "Přerušovaný půst" in summary and "PROXY" in summary


def test_invented_number_blocks_the_report(run, tmp_path):
    (tmp_path / "n.md").write_text(GOOD.replace("−49%", "−71%"), encoding="utf-8")
    code, _, err = run("report", "intermittent-fasting-pl-cs", "--narrative", "n.md")
    assert code == cli.EXIT_FACTCHECK
    assert "71%" in err and "closest study values" in err
    assert not (tmp_path / "wiki-studies" / "intermittent-fasting-pl-cs" / "report.pdf").exists()


def test_report_without_narrative_is_generated_from_data_in_english(run):
    code, out, _ = run("report", "intermittent-fasting-pl-cs", "--lang", "en")
    assert out["narrative"].startswith("automatic")
    pages, text = pdf_text(out["pdf"])
    assert pages == 1
    assert "Key findings" in text and "generated automatically" in text


def test_check_command_flags_wrong_numbers(run, tmp_path):
    (tmp_path / "a.md").write_text("У cs інтерес впав на 49%, у pl на 90%.", encoding="utf-8")
    code, out, _ = run("check", "intermittent-fasting-pl-cs", "--file", "a.md")
    assert code == cli.EXIT_FACTCHECK
    assert [u["number"] for u in out["unmatched"]] == ["90%"]


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("## Findings\n- x", "Headline"),
        ("# Headline\n" + "a" * 300 + "\n## Findings\n- x", "under 220"),
        ("# Headline\nok\n## Findings\n" + "- x\n" * 5, "1-4 bullets"),
    ],
)
def test_narrative_format_errors_explain_the_fix(text, problem):
    with pytest.raises(report.NarrativeError, match=problem):
        report.parse_narrative(text)


def test_ukrainian_headings_are_accepted():
    narrative = report.parse_narrative("# Висновок\nТак.\n## Спостереження\n1. a\n## Що далі\n* b")
    assert (narrative.headline, narrative.findings, narrative.next_steps) == ("Так.", ["a"], ["b"])


def test_language_detection():
    assert report.detect_language("Інтерес спадає") == "uk"
    assert report.detect_language("Interest is falling") == "en"
