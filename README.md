# نظرة — Nazrah

An Arabic-first eye-gaze communication board for non-verbal or paralyzed
patients, built around how care actually happens in Saudi/Gulf homes:
multigenerational, mostly home-based, organized around prayer routines and
family roles rather than institutional care.

## Problem

Commercial eye-tracking AAC (Augmentative and Alternative Communication)
tools — Tobii Dynavox and similar — are built in English for Western care
settings and cost thousands of dollars. Families in Saudi Arabia caring for
a non-verbal relative (stroke, ALS, cerebral palsy, elderly) often have
neither the budget nor a tool whose vocabulary reflects how they actually
speak and care for each other at home.

## Cultural framing

This isn't a generic yes/no/hungry board translated into Arabic. The phrase
set in [`nazrah/phrases.py`](nazrah/phrases.py) is organized around:

- **Prayer** (الصلاة, وضوء) — needs tied to prayer times, which structure
  the day in a way most AAC tools never account for.
- **Family, by the terms actually used** (يمّه، بابا، جدّي، جدتي) —
  colloquial Gulf terms of address, not formal dictionary Arabic.
- **Basic needs and responses** phrased the way they're actually said, not
  literal translations of an English AAC vocabulary list.

That framing is only as credible as the research behind it. See
[`docs/research.md`](docs/research.md) — it's a template, not finished
findings; the interviews and sources need to be done and filled in for the
cultural claim to hold up in front of judges.

## Hardware

- Raspberry Pi 4 (or 3B+)
- Pi Camera Module, or a USB webcam (with IR for low light)
- 7" touchscreen or small monitor for the phrase grid
- Optional: IR LEDs for pupil detection in dim rooms
- Speaker for audio output

## How it works

1. **Gaze tracking** — [`nazrah/gaze_tracker.py`](nazrah/gaze_tracker.py)
   uses MediaPipe's Face Landmarker task (iris landmarks) to get a
   normalized eye position per frame. No dedicated eye-tracker hardware
   needed.
2. **Calibration** — [`nazrah/calibration.py`](nazrah/calibration.py) walks
   through a grid of points (4x4 = 16 by default, see
   `config.CALIBRATION_POINTS_RATIO`) and, for live tracking, classifies
   the current eye position as whichever calibration point it's closest to
   (nearest-neighbor), rather than fitting a continuous regression. A
   plain webcam's gaze signal is too weak/noisy relative to full-screen
   pixel coordinates for a continuous fit to extrapolate reliably — see the
   docstring in `calibration.py` for what was tried first and why it
   didn't hold up. Practically, this means the number of reliably
   distinguishable targets is bounded by how many points you calibrate;
   `nazrah/ui.py`'s `hit_test` maps each calibration point to whichever
   phrase cell's center is nearest it. Pushing the grid size higher has a
   ceiling — see the note in `config.py`.
3. **Dwell-time selection** — [`nazrah/dwell.py`](nazrah/dwell.py) selects
   a phrase after the gaze holds on it for ~1.5s. Chosen over
   blink-detection: more reliable for users with limited or unpredictable
   eyelid control.
4. **Phrase grid UI** — [`nazrah/ui.py`](nazrah/ui.py), a Tkinter grid of
   Arabic phrases with icons, showing dwell progress as the gaze lingers.
5. **Speech output** — [`nazrah/tts.py`](nazrah/tts.py) speaks the selected
   phrase aloud (pre-recorded Arabic audio bank preferred, falls back to
   system TTS) so a caregiver in another room hears it.
6. **Usage logging** — [`nazrah/logger.py`](nazrah/logger.py) logs every
   selection, which is the raw data for the evaluation/iteration step
   (Criterion D).

`nazrah/camera.py` abstracts the camera behind one interface with two
implementations: `WebcamSource` for development on a laptop, and
`PiCameraSource` for the deployed device. The rest of the pipeline doesn't
care which one it's talking to.

## MYP criteria alignment

- **A — Inquiry & Analysis**: [`docs/research.md`](docs/research.md) —
  interviews and sources on the AAC gap for Arabic speakers and how Saudi
  caregiving is structured.
- **B — Developing Ideas**: design decisions captured above and in code
  comments — dwell-time threshold, calibration approach, phrase set
  structure.
- **C — Creating the Solution**: this repository — Pi + camera + gaze
  tracking + TTS pipeline.
- **D — Evaluating**: `usage_log.csv` (generated at runtime, via
  `UsageLogger.most_used()`) plus real-user testing notes — calibration
  accuracy, dwell-time false positives, iteration based on what's
  actually selected.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
```

The first run downloads MediaPipe's face landmark model (~4MB, cached in
`nazrah/models/` — gitignored) — needs an internet connection once, then
works fully offline.

## Running

```bash
python -m nazrah.main
```

This opens the phrase grid fullscreen, walks through grid calibration
(look at each highlighted point and hold still — press Escape anytime to
exit fullscreen), then starts tracking gaze against the grid.

Wired to `WebcamSource`, which works identically on a laptop webcam and on
a USB camera plugged into the Pi — no code change needed to move from dev
to deployment with a USB camera. `PiCameraSource` in
[`nazrah/camera.py`](nazrah/camera.py) is only needed if you switch to the
Pi's CSI ribbon camera instead (requires `picamera2`, which only installs
on Pi OS). See [`docs/raspberry_pi_setup.md`](docs/raspberry_pi_setup.md)
for the full Raspberry Pi 5 + CrowPi deployment walkthrough.

## Testing

```bash
pytest
```

Covers the pieces that don't need a camera or display: dwell-timing state
machine, calibration math, and phrase data integrity. The gaze tracker, UI,
and camera modules are exercised manually against real hardware — see
Criterion D notes for that testing process.

## Adding phrases

Add entries to `PHRASES` in [`nazrah/phrases.py`](nazrah/phrases.py) —
`id`, `category`, Arabic text, transliteration, and an icon (emoji
placeholder until real icon assets are added). To use recorded audio
instead of system TTS for a phrase, drop a `<phrase_id>.wav` file into the
audio bank directory passed to `TTSEngine(audio_bank_dir=...)`.
