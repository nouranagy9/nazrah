DWELL_SECONDS = 2.5

# How many consecutive frames a new target classification must repeat
# before a gaze shift is treated as real (see nazrah/smoothing.py). Higher
# = more resistant to single-frame noise, but slower to respond to an
# intentional shift. Keep this low — unlike a majority-vote window, this
# doesn't carry a bias toward the previous target, so it doesn't need to
# be large to filter noise.
TARGET_CONFIRM_FRAMES = 2

# 4x4 grid calibration targets as (x_ratio, y_ratio) of the screen. More
# points than the classic 5-point layout: the mapping from webcam gaze
# signal to screen position is only reliable near the calibrated points
# (see nazrah/calibration.py's nearest-neighbor classification), so denser
# coverage matters more here than it would for a dedicated eye-tracker.
# There's a ceiling on this, though: the raw gaze signal only spans a
# small range (roughly 0.05-0.1 in practice), so packing in too many
# points eventually puts them closer together than ordinary frame-to-frame
# noise, and nearest-neighbor starts misclassifying between adjacent
# points. If you raise _GRID_SIZE and selection accuracy gets worse
# instead of better, that's the ceiling — worth measuring and writing up
# for Criterion D rather than just cranking the number higher.
_GRID_SIZE = 4
_STEPS = [0.05 + i * (0.9 / (_GRID_SIZE - 1)) for i in range(_GRID_SIZE)]
CALIBRATION_POINTS_RATIO = [(x, y) for y in _STEPS for x in _STEPS]

CAMERA_INDEX = 0
GRID_COLUMNS = 4
