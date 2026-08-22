from nazrah_utils.text_utils import word_count, is_palindrome, reverse_words


def test_word_count():
    assert word_count("hello world") == 2
    assert word_count("") == 0
    assert word_count("one") == 1


def test_is_palindrome():
    assert is_palindrome("A man a plan a canal Panama") is True
    assert is_palindrome("racecar") is True
    assert is_palindrome("hello") is False


def test_reverse_words():
    assert reverse_words("hello world") == "world hello"
    assert reverse_words("one two three") == "three two one"
    assert reverse_words("solo") == "solo"
    assert reverse_words("") == ""
