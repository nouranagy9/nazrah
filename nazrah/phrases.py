"""The phrase set spoken by the board.

Deliberately not generic AAC vocabulary ("yes/no/hungry" in isolation) — the
categories and specific words reflect home-based, multigenerational Gulf
caregiving: prayer routines, family terms as they're actually used in
everyday Saudi speech, and the needs a bedridden or non-verbal relative most
often has to signal. See docs/research.md for the cultural research this is
meant to be grounded in and expanded from.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Phrase:
    id: str
    category: str
    text_ar: str
    transliteration: str
    icon: str  # emoji placeholder for the grid; swap for real icon assets later


PHRASES = [
    # الاحتياجات الأساسية — Basic needs
    Phrase("water", "basic_needs", "ماء", "maa'", "\U0001F4A7"),
    Phrase("hungry", "basic_needs", "جوعان", "jaw'an", "\U0001F37D"),
    Phrase("bathroom", "basic_needs", "حمام", "hammam", "\U0001F6BB"),
    Phrase("pain", "basic_needs", "ألم", "alam", "⚠"),
    Phrase("tired", "basic_needs", "تعبان", "ta'ban", "\U0001F634"),
    Phrase("cold", "basic_needs", "بردان", "bardan", "\U0001F976"),
    Phrase("hot", "basic_needs", "حرّان", "harran", "\U0001F975"),

    # الصلاة والعبادة — Prayer & worship
    Phrase("prayer", "prayer", "الصلاة", "as-salah", "\U0001F54C"),
    Phrase("wudu", "prayer", "وضوء", "wudu'", "\U0001F4A6"),
    Phrase("quran", "prayer", "القرآن", "al-Qur'an", "\U0001F4D6"),

    # أفراد العائلة — Family members
    Phrase("mother", "family", "يمّه", "yumma", "\U0001F469"),
    Phrase("father", "family", "بابا", "baba", "\U0001F468"),
    Phrase("grandfather", "family", "جدّي", "jiddi", "\U0001F474"),
    Phrase("grandmother", "family", "جدتي", "jiddati", "\U0001F475"),
    Phrase("brother", "family", "أخوي", "akhoy", "\U0001F466"),
    Phrase("sister", "family", "أختي", "ukhti", "\U0001F467"),
    Phrase("caregiver", "family", "الممرضة", "al-mumarrida", "\U0001F9D1‍⚕️"),

    # طلبات ومشاعر — Requests & feelings
    Phrase("yes", "responses", "نعم", "na'am", "✅"),
    Phrase("no", "responses", "لا", "la", "❌"),
    Phrase("help", "responses", "ساعدني", "sa'idni", "\U0001F198"),
    Phrase("sleep", "responses", "أريد أن أنام", "ureedu an anam", "\U0001F6CC"),
]

CATEGORIES = ["basic_needs", "prayer", "family", "responses"]


def by_category(category):
    return [p for p in PHRASES if p.category == category]


def by_id(phrase_id):
    for phrase in PHRASES:
        if phrase.id == phrase_id:
            return phrase
    raise KeyError(f"Unknown phrase id: {phrase_id}")
