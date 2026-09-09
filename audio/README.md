# Phrase audio bank

Drop a `.wav` recording for each phrase in this folder, named exactly as below
(matches each `Phrase.id` in [`nazrah/phrases.py`](../nazrah/phrases.py)).
`nazrah/tts.py` checks here first and only falls back to robotic system TTS
for whichever files are missing — so this can be filled in gradually, and
nothing breaks if some are still missing.

A real Saudi/Gulf speaker recording these naturally will sound far better
than any TTS voice, especially for the colloquial ones — that's the whole
point of this folder existing.

| filename | say this | (transliteration) |
|---|---|---|
| `water.wav` | مويه | moyah |
| `hungry.wav` | جوعان | jaw'an |
| `bathroom.wav` | حمام | hammam |
| `pain.wav` | وجع | waja' |
| `prayer.wav` | الصلاة | as-salah |
| `wudu.wav` | وضوء | wudu' |
| `mother.wav` | يمّه | yumma |
| `father.wav` | يبى | yaba |
| `yes.wav` | إي | ee |
| `no.wav` | لا | la |
| `help.wav` | لحقوني | la7gooni |
| `sleep.wav` | ودّي أنام | widdi anam |

## Recording tips

- Quiet room, phone voice-recorder or laptop mic is fine — this doesn't need
  studio quality, just clear and natural.
- Say each phrase the way you'd actually say it to family, not overly
  formal/enunciated — that's the whole reason these are pre-recorded instead
  of using a generic TTS voice.
- Trim dead air from the start/end of each clip so playback doesn't have an
  awkward pause before/after — most phones' built-in voice memo apps, or
  any free audio editor (e.g. Audacity), can export as `.wav`.
- If your recorder only exports `.m4a`/`.mp3`, convert to `.wav` before
  dropping it here (`ffmpeg -i in.m4a water.wav`, or an online converter) —
  `winsound`/`aplay` (see tts.py) only play `.wav`.
