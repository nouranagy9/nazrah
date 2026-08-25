from nazrah.config import CALIBRATION_POINTS_RATIO, GRID_COLUMNS
from nazrah.phrases import PHRASES


def test_calibration_grid_size_matches_phrase_grid():
    """The calibration grid and the phrase grid must have the same number
    of points/cells, and the same column count, or calibration points end
    up landing between phrase cells instead of on them (a real bug this
    project hit more than once)."""
    assert len(CALIBRATION_POINTS_RATIO) == len(PHRASES)
    assert len(PHRASES) % GRID_COLUMNS == 0


def test_calibration_points_are_within_screen_bounds():
    for x_ratio, y_ratio in CALIBRATION_POINTS_RATIO:
        assert 0.0 <= x_ratio <= 1.0
        assert 0.0 <= y_ratio <= 1.0
