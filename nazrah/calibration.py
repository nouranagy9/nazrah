import json
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
    screen position, using inverse-distance-weighted k-nearest-neighbors
    over the (eye_pos, screen_pos) samples collected during calibration.

    This started out as least-squares regression to a continuous screen
    coordinate, which is the "textbook" approach — but a plain webcam's
    gaze signal turned out to be weak and noisy relative to the screen
    range it's mapped to, so a small amount of live drift from the
    calibration pose got amplified into wildly out-of-bounds predictions.
    Plain (k=1) nearest-neighbor classification fixed that — it can't
    extrapolate, since it only ever returns one of the known calibration
    targets exactly — but trades away smoothness for it: gaze readings
    that land right at the boundary between two calibration points'
    "territory" can flip the result between them on essentially no
    change in input, which reads as jittery/inaccurate selection.

    Weighted k-NN (this version) blends the K closest calibration
    samples' screen positions by inverse squared distance instead of
    picking only the single closest one — still bounded to the convex
    hull of the actual calibration points (so it still can't extrapolate
    into wild out-of-bounds territory the way regression did), but the
    output moves continuously as gaze drifts near a boundary instead of
    snapping discretely between two fixed points. An eye_pos that
    exactly matches a calibration sample still returns that sample's
    screen_pos exactly (no blending needed, and avoids dividing by a
    zero distance). See config.TARGET_K_NEIGHBORS.
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

    @property
    def samples(self):
        """List of (eye_pos, screen_pos) pairs collected so far."""
        return list(zip(self._eye_points, self._screen_points))

    def nearest_target(self, eye_pos, k=3):
        """Returns a screen position blending the k calibration samples
        whose eye_pos is closest (Euclidean distance) to the given
        eye_pos, weighted by inverse squared distance — closer samples
        pull the result more. Falls back to fewer than k if there aren't
        that many samples yet."""
        if not self._eye_points:
            raise RuntimeError("No calibration samples added yet")

        k = min(k, len(self._eye_points))
        by_distance = sorted(
            range(len(self._eye_points)),
            key=lambda i: (self._eye_points[i][0] - eye_pos[0]) ** 2
            + (self._eye_points[i][1] - eye_pos[1]) ** 2,
        )[:k]

        nearest_index = by_distance[0]
        nearest_dist_sq = (self._eye_points[nearest_index][0] - eye_pos[0]) ** 2 + (
            self._eye_points[nearest_index][1] - eye_pos[1]
        ) ** 2
        if nearest_dist_sq == 0:
            return self._screen_points[nearest_index]

        weights = []
        for i in by_distance:
            dist_sq = (self._eye_points[i][0] - eye_pos[0]) ** 2 + (
                self._eye_points[i][1] - eye_pos[1]
            ) ** 2
            weights.append(1.0 / dist_sq)

        total_weight = sum(weights)
        x = sum(w * self._screen_points[i][0] for w, i in zip(weights, by_distance)) / total_weight
        y = sum(w * self._screen_points[i][1] for w, i in zip(weights, by_distance)) / total_weight
        return (x, y)


def save_calibration(calibrator, path, screen_w, screen_h):
    """Saves calibration samples to a JSON file so a session doesn't have
    to redo the full calibration flow every time the app starts — see
    load_calibration and main.py. Records the screen size the calibration
    was done against, since the saved screen-pixel coordinates only mean
    anything for that exact resolution."""
    data = {
        "screen_w": screen_w,
        "screen_h": screen_h,
        "samples": [
            {"eye": list(eye), "screen": list(screen)} for eye, screen in calibrator.samples
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_calibration(path, screen_w, screen_h):
    """Loads a previously saved calibration. Raises FileNotFoundError if no
    file exists there, or ValueError if it was saved for a different
    screen resolution than the one given (its screen-pixel coordinates
    wouldn't line up with the current grid)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("screen_w") != screen_w or data.get("screen_h") != screen_h:
        raise ValueError(
            f"Saved calibration was for {data.get('screen_w')}x{data.get('screen_h')}, "
            f"but the current screen is {screen_w}x{screen_h}"
        )

    calibrator = Calibrator()
    for entry in data["samples"]:
        calibrator.add_sample(tuple(entry["eye"]), tuple(entry["screen"]))
    return calibrator
