import time


class DwellSelector:
    """Fires a selection when the same target has been gazed at continuously
    for `dwell_seconds`. Simpler and more reliable than blink-detection for
    users with limited or unreliable eyelid control.
    """

    def __init__(self, dwell_seconds=1.5, clock=time.monotonic):
        self.dwell_seconds = dwell_seconds
        self._clock = clock
        self._current_target = None
        self._target_since = None

    def update(self, target_id):
        """Call once per frame with the currently gazed-at target id (or None
        if nothing is being looked at). Returns the target_id once the dwell
        threshold is reached, otherwise None. Firing resets the dwell timer
        so the same target must be re-acquired to select again.
        """
        now = self._clock()

        if target_id is None:
            self._current_target = None
            self._target_since = None
            return None

        if target_id != self._current_target:
            self._current_target = target_id
            self._target_since = now
            return None

        elapsed = now - self._target_since
        if elapsed >= self.dwell_seconds:
            self._current_target = None
            self._target_since = None
            return target_id

        return None

    @property
    def progress(self):
        """Fraction of the dwell time elapsed for the current target, in
        [0, 1]. Used to drive a fill/progress indicator in the UI."""
        if self._current_target is None:
            return 0.0
        elapsed = self._clock() - self._target_since
        return min(elapsed / self.dwell_seconds, 1.0)
