"""Place sources: the cache, and building counts."""

from busyness.places import CachedSource, Place, count_buildings

from .helpers import ll


class FakeSource:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def places(self, boxes):
        self.calls.append(sorted(boxes))
        return {k: self.answers.get(k) for k in boxes}


BOX_A, BOX_B = (6.0, 45.0, 6.1, 45.1), (7.0, 46.0, 7.1, 46.1)
VILLAGE = Place("Village", "village", 6.05, 45.05, 120)


def test_cache_fetches_missing_domains_once_and_reuses_them(tmp_path):
    inner = FakeSource({"a": [VILLAGE], "b": None})
    cache = CachedSource(tmp_path / "places.json", inner, release="r1")
    assert cache.places({"a": BOX_A, "b": BOX_B}) == {"a": [VILLAGE], "b": None}
    assert inner.calls == [["a", "b"]]
    # A new run reads the file: "a" comes from the cache; "b" failed before, so it's asked for again.
    again = CachedSource(tmp_path / "places.json", inner, release="r1")
    assert again.places({"a": BOX_A, "b": BOX_B})["a"] == [VILLAGE]
    assert inner.calls[-1] == ["b"]


def test_cache_refetches_when_the_box_or_release_changes(tmp_path):
    inner = FakeSource({"a": [VILLAGE]})
    CachedSource(tmp_path / "places.json", inner, release="r1").places({"a": BOX_A})
    CachedSource(tmp_path / "places.json", inner, release="r1").places({"a": (6.0, 45.0, 6.2, 45.1)})
    CachedSource(tmp_path / "places.json", inner, release="r2").places({"a": (6.0, 45.0, 6.2, 45.1)})
    assert inner.calls == [["a"], ["a"], ["a"]]


def test_cache_without_a_source_answers_none_for_unknown_domains(tmp_path):
    assert CachedSource(tmp_path / "none.json", None).places({"a": BOX_A}) == {"a": None}


def test_buildings_counted_within_500_m():
    (lon, lat, _), = ll((0, 0, 0))
    near = [(x, y) for x, y, _ in ll((100, 0, 0), (0, 490, 0), (-350, -350, 0))]
    far = [(x, y) for x, y, _ in ll((0, 520, 0), (600, 0, 0))]
    (p,) = count_buildings([("Here", "village", lon, lat)], near + far)
    assert p.buildings == 3
