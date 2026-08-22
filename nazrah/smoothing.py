class TargetSmoother:
    """Debounces per-frame target classification: a new target only
    replaces the current one once it's been seen `confirm_frames` times in
    a row, so a single noisy/misclassified frame can't flip the active
    target on its own.

    This is deliberately NOT majority-vote over a sliding window of recent
    frames — that approach was tried first and turned out to feel
    unresponsive: right after a real gaze shift, the window is still
    mostly full of the *previous* target, so several frames of the new one
    are needed just to outnumber the stale history before anything
    updates. Requiring consecutive agreement instead reacts as soon as the
    new target has repeated a couple of times, with no bias toward
    whatever came before — while a single stray noisy frame still can't
    win, because reverting to the old target immediately resets the count.
    """

    def __init__(self, confirm_frames=2):
        self.confirm_frames = confirm_frames
        self._current = None
        self._candidate = None
        self._candidate_count = 0

    def update(self, target_id):
        if target_id == self._current:
            self._candidate = None
            self._candidate_count = 0
            return self._current

        if target_id == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate = target_id
            self._candidate_count = 1

        if self._candidate_count >= self.confirm_frames:
            self._current = self._candidate
            self._candidate = None
            self._candidate_count = 0

        return self._current
