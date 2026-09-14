import pytest

from nazrah.calibration import Calibrator, load_calibration, median_point, save_calibration


def test_nearest_target_before_any_samples_raises():
    calibrator = Calibrator()
    with pytest.raises(RuntimeError):
        calibrator.nearest_target((0.5, 0.5))


def test_nearest_target_exact_match_returns_that_target_exactly():
    # An eye_pos exactly matching a calibration sample shouldn't get
    # blended with its neighbors — the zero-distance shortcut in
    # nearest_target returns it untouched.
    calibrator = Calibrator()
    calibrator.add_sample((0.1, 0.1), (10, 10))
    calibrator.add_sample((0.9, 0.1), (90, 10))
    calibrator.add_sample((0.5, 0.9), (50, 90))

    assert calibrator.nearest_target((0.1, 0.1)) == (10, 10)
    assert calibrator.nearest_target((0.9, 0.1)) == (90, 10)


def test_nearest_target_weights_toward_the_closer_sample():
    # Not an exact match to either sample, but much closer to the first —
    # weighted k-NN should pull the blended result well past the halfway
    # point between them, toward the closer one.
    calibrator = Calibrator()
    calibrator.add_sample((0.0, 0.0), (0, 0))
    calibrator.add_sample((1.0, 0.0), (100, 0))

    x, y = calibrator.nearest_target((0.1, 0.0), k=2)
    assert x < 50  # pulled toward (0, 0), not sitting at the midpoint (50, 0)


def test_nearest_target_stays_within_bounds_of_known_targets():
    calibrator = Calibrator()
    calibrator.add_sample((0.4, 0.4), (100, 100))
    calibrator.add_sample((0.6, 0.4), (200, 100))

    # A wild, noisy eye position still resolves within the range of the
    # known targets rather than some wildly out-of-range extrapolation —
    # the failure mode that sank the least-squares-regression approach
    # this replaced (see the Calibrator docstring).
    x, y = calibrator.nearest_target((5.0, -3.0))
    assert 100 <= x <= 200
    assert y == pytest.approx(100)


def test_num_samples_tracks_added_samples():
    calibrator = Calibrator()
    assert calibrator.num_samples == 0
    calibrator.add_sample((0.1, 0.1), (0, 0))
    calibrator.add_sample((0.2, 0.2), (100, 100))
    assert calibrator.num_samples == 2


def test_median_point_of_empty_list_raises():
    with pytest.raises(ValueError):
        median_point([])


def test_median_point_ignores_a_single_outlier():
    points = [(0.5, 0.5)] * 9 + [(5.0, -3.0)]  # one wild outlier frame
    assert median_point(points) == (0.5, 0.5)


def test_median_point_averages_odd_count_per_axis():
    points = [(0.1, 0.9), (0.2, 0.8), (0.3, 0.7)]
    assert median_point(points) == (0.2, 0.8)


def test_save_and_load_calibration_round_trip(tmp_path):
    path = tmp_path / "calibration.json"
    original = Calibrator()
    original.add_sample((0.1, 0.2), (100, 200))
    original.add_sample((0.3, 0.4), (300, 400))

    save_calibration(original, path, screen_w=1920, screen_h=1080)
    loaded = load_calibration(path, screen_w=1920, screen_h=1080)

    assert loaded.num_samples == 2
    assert loaded.nearest_target((0.1, 0.2)) == (100, 200)
    assert loaded.nearest_target((0.3, 0.4)) == (300, 400)


def test_load_calibration_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_calibration(tmp_path / "does-not-exist.json", screen_w=1920, screen_h=1080)


def test_load_calibration_rejects_mismatched_screen_size(tmp_path):
    path = tmp_path / "calibration.json"
    calibrator = Calibrator()
    calibrator.add_sample((0.1, 0.2), (100, 200))
    save_calibration(calibrator, path, screen_w=1920, screen_h=1080)

    with pytest.raises(ValueError):
        load_calibration(path, screen_w=1280, screen_h=720)
