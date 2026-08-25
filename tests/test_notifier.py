from nazrah.notifier import CaregiverNotifier
from nazrah.phrases import by_id


def test_notify_posts_to_topic_url():
    calls = []

    def fake_post(url, message, headers):
        calls.append((url, message, headers))

    notifier = CaregiverNotifier("test-topic", post_fn=fake_post)
    result = notifier.notify(by_id("pain"))

    assert result is True
    assert len(calls) == 1
    url, message, headers = calls[0]
    assert url == "https://ntfy.sh/test-topic"
    assert "ألم" in message
    assert headers["Priority"] == "urgent"


def test_notify_returns_false_on_failure_without_raising():
    def failing_post(url, message, headers):
        raise OSError("network down")

    notifier = CaregiverNotifier("test-topic", post_fn=failing_post)
    result = notifier.notify(by_id("help"))

    assert result is False


def test_custom_base_url_strips_trailing_slash():
    calls = []

    def fake_post(url, message, headers):
        calls.append(url)

    notifier = CaregiverNotifier("t", base_url="https://example.com/", post_fn=fake_post)
    notifier.notify(by_id("pain"))

    assert calls[0] == "https://example.com/t"
