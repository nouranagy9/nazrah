import re


def word_count(text):
    return len(text.split())


def is_palindrome(text):
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return cleaned == cleaned[::-1]


def reverse_words(text):
    return " ".join(reversed(text.split()))
