# Nazrah Utils

A tiny collection of Python text-processing helpers.

## Functions

- `word_count(text)` — counts the words in a string.
- `is_palindrome(text)` — checks whether a string reads the same forwards and backwards (ignoring case, spaces, and punctuation).
- `reverse_words(text)` — reverses the order of words in a string.

## Usage

```python
from nazrah_utils.text_utils import word_count, is_palindrome, reverse_words

word_count("hello world")        # 2
is_palindrome("A man a plan a canal Panama")  # True
reverse_words("hello world")     # "world hello"
```

## Running tests

```bash
pytest
```
