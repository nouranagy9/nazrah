import urllib.request


class CaregiverNotifier:
    """Sends a push notification to the caregiver's phone via ntfy.sh
    (https://ntfy.sh) when an urgent phrase is selected — for when they
    might not be in the room to hear the local speaker.

    Uses ntfy's free public service: no account or API key, just an HTTP
    POST to a topic URL. The topic name IS the access control — anyone who
    knows it can read everything sent to it — so treat it like a shared
    password (a long, random string), not something guessable like
    "nazrah-alerts". See the setup note in README.md.
    """

    def __init__(self, topic, base_url="https://ntfy.sh", post_fn=None):
        self.topic = topic
        self.base_url = base_url.rstrip("/")
        self._post_fn = post_fn or self._default_post

    def notify(self, phrase):
        """Sends an alert for the given phrase. Returns True on success,
        False on failure (network issues, ntfy unreachable, etc.) — never
        raises, since a failed remote alert shouldn't crash the local
        device or block the local speaker from still working."""
        url = f"{self.base_url}/{self.topic}"
        message = f"{phrase.text_ar} ({phrase.transliteration})"
        headers = {
            "Title": "Nazrah: urgent need",
            "Priority": "urgent",
            "Tags": "warning",
        }
        try:
            self._post_fn(url, message, headers)
            return True
        except Exception as exc:
            print(f"[Notifier] Failed to send caregiver alert: {exc}")
            return False

    @staticmethod
    def _default_post(url, message, headers):
        request = urllib.request.Request(
            url, data=message.encode("utf-8"), headers=headers, method="POST"
        )
        urllib.request.urlopen(request, timeout=5)
