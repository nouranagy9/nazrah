import math

from .phrases import PHRASES

DWELL_SECONDS = 2.5

# How many consecutive frames a new target classification must repeat
# before a gaze shift is treated as real (see nazrah/smoothing.py). Higher
# = more resistant to single-frame noise, but slower to respond to an
# intentional shift. Keep this low — unlike a majority-vote window, this
# doesn't carry a bias toward the previous target, so it doesn't need to
# be large to filter noise.
TARGET_CONFIRM_FRAMES = 2

CAMERA_INDEX = 0
GRID_COLUMNS = 4

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
