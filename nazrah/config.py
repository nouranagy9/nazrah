import math
import os
import platform

from .phrases import PHRASES

DWELL_SECONDS = 2.5

# ntfy.sh topic for remote caregiver alerts on urgent phrases (see
# notifier.py). Deliberately NOT hardcoded here: the topic name is the
# only thing standing between a stranger and reading the patient's urgent
# alerts, so it shouldn't live in a public repo. Set it as an environment
# variable instead:
#   export NAZRAH_NTFY_TOPIC="some-long-random-string"
# and have the caregiver subscribe to the same topic in the ntfy app.
# Alerts are silently skipped if this isn't set.
NTFY_TOPIC = os.environ.get("NAZRAH_NTFY_TOPIC")

# How many consecutive frames a new target classification must repeat
# before a gaze shift is treated as real (see nazrah/smoothing.py). Higher
# = more resistant to single-frame noise, but slower to respond to an
# intentional shift. Keep this low — unlike a majority-vote window, this
# doesn't carry a bias toward the previous target, so it doesn't need to
# be large to filter noise.
TARGET_CONFIRM_FRAMES = 2

# Which /dev/videoN (or Windows camera index) WebcamSource opens. A device
# with multiple cameras attached — e.g. CrowPi's built-in low-res camera
# plus a separate external USB webcam — won't necessarily put the one you
# actually want at index 0; check with `v4l2-ctl --list-devices` on Linux
# and override via NAZRAH_CAMERA_INDEX if needed rather than guessing.
CAMERA_INDEX = int(os.environ.get("NAZRAH_CAMERA_INDEX", "0"))
GRID_COLUMNS = 4

# Where a successful calibration gets saved, so the app can skip
# calibration on the next launch instead of redoing it every time — a real
# problem for a patient with limited mobility turning the device on daily.
# Gitignored: it's specific to one camera's position/angle and one
# screen's resolution, not something to commit.
CALIBRATION_FILE = os.environ.get("NAZRAH_CALIBRATION_FILE", "calibration_data.json")

# Set NAZRAH_RECALIBRATE=1 to ignore any saved calibration and force a
# fresh one — e.g. after moving the camera or screen, or a different
# person is using the device now.
FORCE_RECALIBRATE = os.environ.get("NAZRAH_RECALIBRATE") == "1"

# GPIO pin the light/relay is wired to on the deployed Pi (see light.py).
# CrowPi's built-in relay module is wired to pin 40 / GPIO21 (per Elecrow's
# CrowPi manual's sensor control table) — not the arbitrary default we'd
# picked before actually checking. Irrelevant on a dev machine with no
# such hardware — GpioLightController just fails to import gpiozero there
# and main.py falls back to NoOpLightController automatically.
LIGHT_GPIO_PIN = 21

# Font family for the grid labels (see ui.py). Tk has no font-fallback
# chain — an unavailable family silently substitutes some default, which
# on Windows still renders Arabic fine (the OS does its own glyph
# substitution), but on a fresh Raspberry Pi OS install there's no
# Arabic-capable font installed by default, so phrase text on the grid
# rendered as blank space (found via real hardware testing on the CrowPi).
# Fixed by installing `fonts-noto-core` (apt) on the Pi and pointing this
# at "Noto Sans Arabic" there specifically, rather than hoping whatever Tk
# substitutes happens to cover Arabic. Override with NAZRAH_GRID_FONT if a
# different font is preferred.
GRID_FONT_FAMILY = os.environ.get(
    "NAZRAH_GRID_FONT",
    "Segoe UI" if platform.system() == "Windows" else "Noto Sans Arabic",
)

# A real TrueType font FILE, used only as a fallback path for when Tk's own
# font engine can't render Arabic at all (see ui.py's GridUI.__init__ for
# why — the Pi's Python 3.11 interpreter's bundled Tk has no TrueType
# support whatsoever, so GRID_FONT_FAMILY above never actually reaches a
# real Arabic font there no matter what's installed). Left unset on
# Windows, where Tk's native rendering already works fine.
GRID_FONT_FILE = os.environ.get(
    "NAZRAH_GRID_FONT_FILE",
    None
    if platform.system() == "Windows"
    else "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
)

# Calibration grid targets as (x_ratio, y_ratio) of the screen, sized to
# exactly match the phrase grid's own columns x rows — a calibration grid
# that doesn't line up with the actual grid was a real, hard-to-spot bug
# here before (calibration points landing between phrase cells instead of
# on them), so the two are now derived from the same numbers instead of
# kept in sync by hand.
#
# More points than the classic 5-point layout: the mapping from webcam
# gaze signal to screen position is only reliable near the calibrated
# points (see nazrah/calibration.py's nearest-neighbor classification), so
# denser coverage matters more here than it would for a dedicated
# eye-tracker. There's a ceiling on this, though: the raw gaze signal only
# spans a small range (roughly 0.05-0.1 in practice), so packing in too
# many points eventually puts them closer together than ordinary
# frame-to-frame noise, and nearest-neighbor starts misclassifying between
# adjacent points. If the phrase grid grows and selection accuracy gets
# worse instead of better, that's the ceiling — worth measuring and
# writing up for Criterion D rather than just adding more phrases.
_CALIBRATION_ROWS = math.ceil(len(PHRASES) / GRID_COLUMNS)


def _steps(count):
    if count == 1:
        return [0.5]
    return [0.05 + i * (0.9 / (count - 1)) for i in range(count)]


CALIBRATION_POINTS_RATIO = [
    (x, y) for y in _steps(_CALIBRATION_ROWS) for x in _steps(GRID_COLUMNS)
]
