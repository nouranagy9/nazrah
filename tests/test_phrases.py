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


def test_pain_and_help_are_marked_urgent():
    # These trigger a remote caregiver alert (see notifier.py) — the most
    # time-sensitive phrases in the set.
    assert by_id("pain").urgent is True
    assert by_id("help").urgent is True


def test_most_phrases_are_not_urgent():
    # Guards against accidentally marking everything urgent, which would
    # spam the caregiver's phone for routine selections.
    urgent_count = sum(1 for p in PHRASES if p.urgent)
    assert urgent_count < len(PHRASES) / 2
