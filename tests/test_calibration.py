import pytest

from nazrah.calibration import Calibrator


def test_predict_before_fit_raises():
    calibrator = Calibrator()
    with pytest.raises(RuntimeError):
        calibrator.predict((0.5, 0.5))


def test_fit_with_too_few_samples_raises():
    calibrator = Calibrator()
    calibrator.add_sample((0.1, 0.1), (0, 0))
    with pytest.raises(ValueError):
        calibrator.fit()


def test_fit_recovers_known_linear_mapping():
    scale = (1920, 1080)
    offset = (-100, -50)

    calibrator = Calibrator()
    for ex, ey in [(0.0, 0.0), (1.0, 0.0), (0.5, 0.5), (0.0, 1.0), (1.0, 1.0)]:
        sx = ex * scale[0] + offset[0]
        sy = ey * scale[1] + offset[1]
        calibrator.add_sample((ex, ey), (sx, sy))

    calibrator.fit()

    px, py = calibrator.predict((0.5, 0.5))
    assert px == pytest.approx(0.5 * scale[0] + offset[0], abs=1.0)
    assert py == pytest.approx(0.5 * scale[1] + offset[1], abs=1.0)
