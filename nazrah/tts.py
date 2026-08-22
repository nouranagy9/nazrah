import os
import platform


class TTSEngine:
    """Speaks a selected phrase aloud to alert the caregiver. Prefers a
    pre-recorded Arabic audio bank (better pronunciation than any system TTS
    voice, and works even where no Arabic voice is installed); falls back to
    pyttsx3's system TTS; falls back to printing if neither is available
    (e.g. no audio output during development).
    """

    def __init__(self, audio_bank_dir=None):
        self.audio_bank_dir = audio_bank_dir
        self._engine = None

    def speak(self, phrase):
        audio_path = self._find_audio_file(phrase)
        if audio_path:
            self._play_audio_file(audio_path)
            return

        try:
            engine = self._get_engine()
            engine.say(phrase.text_ar)
            engine.runAndWait()
        except Exception as exc:
            print(f"[TTS unavailable, would speak]: {phrase.text_ar} ({exc})")

    def _get_engine(self):
        if self._engine is None:
            import pyttsx3

            self._engine = pyttsx3.init()
        return self._engine

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
