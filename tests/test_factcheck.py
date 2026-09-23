import pytest

from wir import factcheck

DOCUMENT_ROWS = {
    "yoy_pct": -61.7,
    "months_up_of_12": 0,
    "avg_monthly_views": 1431,
    "relative_yoy_pct": -42.4,
    "trust": "High (100)",
    "trust_reasons": ["~559 views/month is enough.", "32% of requests were automated."],
    "seasonality": "September peak ≈2.35× every year",
}


@pytest.fixture
def document(monkeypatch):
    monkeypatch.setattr(
        "wir.study.summarize",
        lambda doc: {"results": [DOCUMENT_ROWS], "ranking": [{"score": 42.8}]},
    )
    return {"results": {}}


@pytest.mark.parametrize(
    ("text", "value", "percent"),
    [
        ("впав на −62%", 62.0, True),
        ("1 431 перегляд", 1431.0, False),
        ("1,431 views", 1431.0, False),
        ("61,7 відсотка", 61.7, False),
        ("пік ≈2.35×", 2.35, False),
        ("score 42.8", 42.8, False),
    ],
)
def test_extract_understands_local_number_formats(text, value, percent):
    [item] = factcheck.extract(text)
    assert item["value"] == value
    assert item["percent"] is percent


def test_dates_ids_and_codes_are_not_numbers():
    assert factcheck.extract("period 2024-09..2026-08, on 2025-05-07, concept Q333") == []


def test_rounded_numbers_from_the_study_pass(document):
    text = "Спад на 62% (0 з 12 місяців вище); ~1 431 перегляд/міс, відносно −42%; пік ≈2.35×."
    result = factcheck.check(text, document)
    assert result["ok"], result
    assert result["numbers_checked"] == 4


def test_numbers_inside_reason_texts_count_as_shown(document):
    assert factcheck.check("559 переглядів на місяць, 32% автоматичних", document)["ok"]


def test_invented_numbers_are_reported_with_closest_values(document):
    result = factcheck.check("Інтерес впав на 47%, а в середньому 1 900 переглядів.", document)
    assert not result["ok"]
    assert [u["number"] for u in result["unmatched"]] == ["47%", "1 900"]
    assert 42.4 in result["unmatched"][0]["closest_study_values"]
    assert "closest study values" in factcheck.explain(result)


def test_percent_must_match_a_percentage_not_a_count(document):
    assert not factcheck.check("зросло на 1431%", document)["ok"]


def test_years_and_small_counts_are_free(document):
    assert factcheck.check("У 2025 році 3 мови з 5 показали спад за 12 місяців.", document)["ok"]
