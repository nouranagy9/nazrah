import statistics


def median_point(points):
    """Per-axis median of a list of (x, y) points. Used to collapse the
    many frames sampled at one calibration point down to a single
    representative eye position.

    Plain mean was tried first: a single frame with a momentary landmark
    misdetection can pull the average noticeably off, since nothing
    dampens an outlier's contribution. The median is robust to that — a
    handful of bad frames among dozens of good ones barely moves it —
    which matters here because a calibration point that's even slightly
    off degrades nearest-neighbor targeting for every live frame that
    should have matched it.
    """
    if not points:
        raise ValueError("Cannot compute median of an empty list of points")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return statistics.median(xs), statistics.median(ys)


class Calibrator:
    """Maps a normalized eye position (as returned by GazeTracker) to a
    screen target, using nearest-neighbor classification over the
    (eye_pos, screen_pos) samples collected during calibration.

    This started out as least-squares regression to a continuous screen
    coordinate, which is the "textbook" approach — but a plain webcam's
    gaze signal turned out to be weak and noisy relative to the screen
    range it's mapped to, so a small amount of live drift from the
    calibration pose got amplified into wildly out-of-bounds predictions.
    Nearest-neighbor classification can't extrapolate — it only ever
    returns one of the known calibration targets — trading continuous
    positioning for robustness. In practice this means the number of
    reliably distinguishable targets is bounded by how many calibration
    points were collected (see CALIBRATION_POINTS_RATIO in config.py).
    """

    def __init__(self):
        self._eye_points = []
        self._screen_points = []

    def add_sample(self, eye_pos, screen_pos):
        self._eye_points.append(eye_pos)
        self._screen_points.append(screen_pos)

    @property
    def num_samples(self):
        return len(self._eye_points)

    def nearest_target(self, eye_pos):
        """Returns the screen_pos of whichever calibration sample's eye_pos
        is closest (Euclidean distance) to the given eye_pos."""
        if not self._eye_points:
            raise RuntimeError("No calibration samples added yet")
        best_index = min(
            range(len(self._eye_points)),
            key=lambda i: (self._eye_points[i][0] - eye_pos[0]) ** 2
            + (self._eye_points[i][1] - eye_pos[1]) ** 2,
        )
        return self._screen_points[best_index]
