import numpy as np


class Calibrator:
    """Fits a mapping from normalized eye position (as returned by
    GazeTracker) to screen pixel coordinates, using least-squares regression
    over a handful of (eye_pos, screen_pos) calibration samples — e.g. the
    standard 5-point calibration (four corners + center).
    """

    def __init__(self):
        self._eye_points = []
        self._screen_points = []
        self._transform = None  # 3x2 matrix: [x, y, 1] @ transform = [screen_x, screen_y]

    def add_sample(self, eye_pos, screen_pos):
        self._eye_points.append(eye_pos)
        self._screen_points.append(screen_pos)

    @property
    def num_samples(self):
        return len(self._eye_points)

    @property
    def is_fitted(self):
        return self._transform is not None

    def fit(self):
        if len(self._eye_points) < 3:
            raise ValueError("Need at least 3 calibration samples to fit a mapping")
        eye = np.array(self._eye_points, dtype=float)
        screen = np.array(self._screen_points, dtype=float)
        design = np.hstack([eye, np.ones((eye.shape[0], 1))])  # N x 3
        transform, *_ = np.linalg.lstsq(design, screen, rcond=None)
        self._transform = transform
        return self

    def predict(self, eye_pos):
        if self._transform is None:
            raise RuntimeError("Calibrator.fit() must be called before predict()")
        x, y = eye_pos
        vec = np.array([x, y, 1.0])
        screen_x, screen_y = vec @ self._transform
        return float(screen_x), float(screen_y)
