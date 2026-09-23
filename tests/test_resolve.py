from wir import languages
from wir.resolve import Candidate, check_title, is_ambiguous, rank, redirects, resolve_topic


def langs(codes: str):
    return languages.parse_list(codes)


def by_lang(resolution):
    return {a.edition.code: a for a in resolution.articles}


def test_polish_has_no_intermittent_fasting_article(cassette_client):
    client = cassette_client("resolve_fasting")
    result = resolve_topic(client, "intermittent fasting", "en", langs("pl,cs"))
    assert result.status == "ok"
    assert result.concept.qid == "Q1666254"
    articles = by_lang(result)
    assert articles["cs"].status == "found"
    assert articles["cs"].title == "Přerušovaný půst"
    assert articles["pl"].status == "missing"
    assert articles["pl"].title is None
    assert "Głodówka lecznicza" in [p["title"] for p in articles["pl"].proxy_candidates]
    assert "No article in: pl" in result.next_step()


def test_mercury_is_ambiguous(cassette_client):
    client = cassette_client("resolve_mercury")
    result = resolve_topic(client, "Меркурій", "uk", langs("uk"))
    assert result.status == "ambiguous"
    meanings = {result.concept.qid, *(c.qid for c in result.alternatives)}
    assert {"Q308", "Q1150", "Q925"} <= meanings
    assert "--qid" in result.next_step()


def test_pinned_qid_skips_search_and_ambiguity(cassette_client):
    client = cassette_client("resolve_mercury_qid")
    result = resolve_topic(client, "", "uk", langs("uk"), qid="q308")
    assert result.status == "ok"
    assert by_lang(result)["uk"].title == "Меркурій (планета)"


def test_astronomy_found_everywhere(cassette_client):
    client = cassette_client("resolve_astronomy")
    result = resolve_topic(client, "astronomy", "en", langs("uk,pl,cs,sk"))
    assert result.status == "ok"
    assert {a.edition.code: a.title for a in result.articles} == {
        "uk": "Астрономія",
        "pl": "Astronomia",
        "cs": "Astronomie",
        "sk": "Astronómia",
    }


def test_nonsense_topic_is_not_found(cassette_client):
    client = cassette_client("resolve_nonsense")
    result = resolve_topic(client, "qwzxkjv plorf", "en", langs("uk"))
    assert result.status == "not_found"
    assert "Rephrase" in result.to_dict()["next_step"]


def test_check_title_follows_redirects(cassette_client):
    client = cassette_client("check_title")
    page = check_title(client, languages.get("en"), "Einstein")
    assert page == {
        "lang": "en",
        "title": "Albert Einstein",
        "exists": True,
        "qid": "Q937",
        "disambiguation": False,
    }
    assert check_title(client, languages.get("en"), "Qwzxkjv plorf")["exists"] is False


def test_redirects_are_listed(cassette_client):
    client = cassette_client("redirects")
    assert "Einstein" in redirects(client, languages.get("en"), "Albert Einstein")


def candidate(qid, match, editions, rank_=0, description="topic"):
    c = Candidate(qid=qid, match=match, search_rank=rank_, english_description=description)
    c.sitelinks = {f"w{i}": "t" for i in range(editions)}
    return c


def test_rank_prefers_exact_label_then_notability():
    ranked = rank(
        [
            candidate("Q1", match=0, editions=300),
            candidate("Q2", match=1, editions=250),
            candidate("Q3", match=2, editions=80),
            candidate("Q4", match=2, editions=200),
        ]
    )
    assert [c.qid for c in ranked] == ["Q4", "Q3", "Q2", "Q1"]


def test_rank_drops_non_articles():
    ranked = rank(
        [
            candidate("Q1", 2, 0),
            candidate("Q2", 2, 50, description="Wikimedia disambiguation page"),
            candidate("Q3", 2, 5, description="scholarly article published in 2019"),
            candidate("Q4", 0, 10),
        ]
    )
    assert [c.qid for c in ranked] == ["Q4"]


def test_obscure_namesakes_are_not_ambiguity():
    ranked = rank([candidate("Q333", 2, 252), candidate("Q9", 2, 3)])
    assert is_ambiguous(ranked) == []


def test_comparable_namesakes_are_ambiguity():
    ranked = rank([candidate("Q308", 2, 250), candidate("Q1150", 2, 84)])
    assert [c.qid for c in is_ambiguous(ranked)] == ["Q1150"]
