import pytest

from wir import languages


@pytest.mark.parametrize("value", ["pl", "PL", "Polish", "polski", " pl "])
def test_codes_and_names_are_accepted(value):
    assert languages.get(value).code == "pl"


def test_identifiers_for_each_api():
    edition = languages.get("uk")
    assert edition.project == "uk.wikipedia"
    assert edition.dbname == "ukwiki"
    assert edition.article_url("Меркурій (планета)").endswith("/wiki/Меркурій_(планета)")


def test_irregular_dbname():
    assert languages.get("be-tarask").dbname == "be_x_oldwiki"


def test_unknown_language_suggests_close_matches():
    with pytest.raises(languages.UnknownLanguage, match="Did you mean: .*polish"):
        languages.get("polsh")


def test_parse_list_dedupes_and_keeps_order():
    assert [e.code for e in languages.parse_list("uk, pl,Polish;cs")] == ["uk", "pl", "cs"]


def test_parse_list_requires_something():
    with pytest.raises(languages.UnknownLanguage):
        languages.parse_list(" , ")
