import pytest

from nazrah.calibration import Calibrator, median_point


def test_nearest_target_before_any_samples_raises():
    calibrator = Calibrator()
    with pytest.raises(RuntimeError):
        calibrator.nearest_target((0.5, 0.5))


def test_nearest_target_picks_closest_sample():
    calibrator = Calibrator()
    calibrator.add_sample((0.1, 0.1), "top-left")
    calibrator.add_sample((0.9, 0.1), "top-right")
    calibrator.add_sample((0.5, 0.9), "bottom-center")

    assert calibrator.nearest_target((0.12, 0.08)) == "top-left"
    assert calibrator.nearest_target((0.85, 0.15)) == "top-right"
    assert calibrator.nearest_target((0.5, 1.0)) == "bottom-center"


def test_nearest_target_never_extrapolates_beyond_known_targets():
    calibrator = Calibrator()
    calibrator.add_sample((0.4, 0.4), (100, 100))
    calibrator.add_sample((0.6, 0.4), (200, 100))

    # A wild, noisy eye position still resolves to one of the two known
    # targets rather than some out-of-range extrapolated point.
    result = calibrator.nearest_target((5.0, -3.0))
    assert result in ((100, 100), (200, 100))


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
