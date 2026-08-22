from nazrah.dwell import DwellSelector


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def advance(self, seconds):
        self.t += seconds

    def __call__(self):
        return self.t


def test_selection_fires_after_dwell_threshold():
    clock = FakeClock()
    selector = DwellSelector(dwell_seconds=1.5, clock=clock)

    assert selector.update("water") is None
    clock.advance(1.0)
    assert selector.update("water") is None
    clock.advance(0.6)
    assert selector.update("water") == "water"


def test_looking_away_resets_dwell():
    clock = FakeClock()
    selector = DwellSelector(dwell_seconds=1.5, clock=clock)

    selector.update("water")
    clock.advance(1.0)
    selector.update(None)  # looked away
    clock.advance(1.0)
    assert selector.update("water") is None  # dwell restarted, not yet 1.5s


def test_switching_target_resets_dwell():
    clock = FakeClock()
    selector = DwellSelector(dwell_seconds=1.5, clock=clock)

    selector.update("water")
    clock.advance(1.4)
    assert selector.update("bathroom") is None
    clock.advance(1.4)
    assert selector.update("bathroom") is None
    clock.advance(0.2)
    assert selector.update("bathroom") == "bathroom"


def test_progress_reports_fraction_of_dwell_time():
    clock = FakeClock()
    selector = DwellSelector(dwell_seconds=2.0, clock=clock)
    selector.update("water")
    clock.advance(1.0)
    assert selector.progress == 0.5
