import pytest

from wir.rank import DEFAULT_WEIGHTS, parse_weights, rank


def entry(key, yoy, per_million, avg, score):
    return {
        "key": key,
        "metrics": {
            "growth": {"robust_yoy_pct": yoy},
            "relative": {"per_million_last12": per_million},
            "volume": {"avg_monthly_last12": avg},
        },
        "trust": {"score": score},
    }


BIG_FLAT = entry("big", yoy=0, per_million=50, avg=20000, score=100)
SMALL_GROWING = entry("small", yoy=80, per_million=20, avg=500, score=80)


def test_default_weights():
    assert parse_weights(None) == DEFAULT_WEIGHTS
    assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1)


def test_aliases_and_unmentioned_weights_are_zero():
    weights = parse_weights("growth=0.6, volume=0.4")
    assert weights == {"momentum": 0.6, "relative": 0.0, "size": 0.4, "trust": 0.0}


@pytest.mark.parametrize("text", ["speed=1", "growth=high", "growth=0,size=0"])
def test_bad_weights_explain_the_format(text):
    with pytest.raises(ValueError):
        parse_weights(text)


def test_weights_change_the_winner():
    by_size = rank([BIG_FLAT, SMALL_GROWING], parse_weights("size=1"))
    by_growth = rank([BIG_FLAT, SMALL_GROWING], parse_weights("growth=1"))
    assert by_size[0]["key"] == "big"
    assert by_growth[0]["key"] == "small"
    assert by_growth[0]["strongest"] == ["momentum"]


def test_scores_do_not_depend_on_other_candidates():
    alone = rank([BIG_FLAT], DEFAULT_WEIGHTS)[0]["score"]
    together = {r["key"]: r["score"] for r in rank([BIG_FLAT, SMALL_GROWING], DEFAULT_WEIGHTS)}
    assert together["big"] == alone


def test_ranks_are_consecutive():
    rows = rank([SMALL_GROWING, BIG_FLAT], DEFAULT_WEIGHTS)
    assert [r["rank"] for r in rows] == [1, 2]
    assert all(0 <= r["score"] <= 100 for r in rows)
