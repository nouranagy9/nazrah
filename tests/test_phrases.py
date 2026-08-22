import pytest

from nazrah.phrases import CATEGORIES, PHRASES, by_category, by_id


def test_phrase_ids_are_unique():
    ids = [p.id for p in PHRASES]
    assert len(ids) == len(set(ids))


def test_every_phrase_has_arabic_text():
    for phrase in PHRASES:
        assert phrase.text_ar.strip() != ""


def test_all_categories_represented():
    represented = {p.category for p in PHRASES}
    assert represented == set(CATEGORIES)


def test_by_category_filters_correctly():
    prayer_phrases = by_category("prayer")
    assert len(prayer_phrases) > 0
    assert all(p.category == "prayer" for p in prayer_phrases)


def test_by_id_returns_matching_phrase():
    assert by_id("water").text_ar == "ماء"


def test_by_id_raises_for_unknown_id():
    with pytest.raises(KeyError):
        by_id("does-not-exist")
