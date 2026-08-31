import os
import platform


class TTSEngine:
    """Speaks a selected phrase aloud to alert the caregiver. Prefers a
    pre-recorded Arabic audio bank (better pronunciation than any system TTS
    voice, and works even where no Arabic voice is installed); falls back to
    pyttsx3's system TTS; falls back to printing if neither is available
    (e.g. no audio output during development).

    Call speak() from a background thread, not the main loop — see the note
    in main.py's speak_phrase(). It can genuinely take a while, and on this
    Windows setup pyttsx3 was observed to hang outright when a call ran on
    the same thread driving gaze tracking, freezing the whole app.
    """

    def __init__(self, audio_bank_dir=None):
        self.audio_bank_dir = audio_bank_dir

    def speak(self, phrase):
        audio_path = self._find_audio_file(phrase)
        if audio_path:
            self._play_audio_file(audio_path)
            return

        try:
            import pyttsx3

            # A fresh engine per call, not a cached/reused one: pyttsx3's
            # Windows SAPI5 driver is known to hang on a second
            # runAndWait() call against the same engine instance — reusing
            # one is exactly what caused the freeze mentioned above. This
            # still isn't enough on its own if two calls can overlap
            # (SAPI5's run loop state isn't fully isolated per engine) —
            # see main.py's single-worker TTS queue, which guarantees only
            # one call is ever in flight.
            engine = pyttsx3.init()
            engine.say(phrase.text_ar)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            try:
                print(f"[TTS unavailable, would speak]: {phrase.text_ar} ({exc})")
            except UnicodeEncodeError:
                # This console can't render the Arabic text itself (seen
                # on this Windows setup) — fall back to the ASCII-safe id
                # rather than let the fallback print crash too.
                print(f"[TTS unavailable, would speak]: phrase id '{phrase.id}' ({exc})")

    def _find_audio_file(self, phrase):
        if not self.audio_bank_dir:
            return None
        path = os.path.join(self.audio_bank_dir, f"{phrase.id}.wav")
        return path if os.path.isfile(path) else None

    def _play_audio_file(self, path):
        if platform.system() == "Windows":
            import winsound

            winsound.PlaySound(path, winsound.SND_FILENAME)
        else:
            os.system(f"aplay '{path}'")
