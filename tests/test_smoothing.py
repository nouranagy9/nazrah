from nazrah.smoothing import TargetSmoother


def test_first_frame_does_not_immediately_become_current():
    smoother = TargetSmoother(confirm_frames=2)
    assert smoother.update("water") is None


def test_target_confirmed_after_consecutive_frames():
    smoother = TargetSmoother(confirm_frames=2)
    smoother.update("water")
    assert smoother.update("water") == "water"


def test_single_noisy_frame_does_not_flip_current_target():
    smoother = TargetSmoother(confirm_frames=2)
    smoother.update("water")
    smoother.update("water")  # water is now current
    assert smoother.update("hungry") == "water"  # one noisy frame: ignored
    assert smoother.update("water") == "water"  # reverted, count reset


def test_sustained_shift_switches_after_confirm_frames():
    smoother = TargetSmoother(confirm_frames=2)
    smoother.update("water")
    smoother.update("water")  # water is now current
    smoother.update("hungry")  # candidate, count=1
    assert smoother.update("hungry") == "hungry"  # confirmed, count=2


def test_interrupted_candidate_streak_resets_count():
    smoother = TargetSmoother(confirm_frames=3)
    smoother.update("water")
    smoother.update("water")
    smoother.update("water")  # water is now current (3 in a row)
    smoother.update("hungry")  # candidate hungry, count=1
    smoother.update("bathroom")  # different candidate, resets to count=1
    smoother.update("hungry")  # candidate hungry again, count=1
    assert smoother.update("hungry") == "water"  # only count=2, not confirmed yet


def test_none_is_treated_like_any_other_target():
    smoother = TargetSmoother(confirm_frames=2)
    smoother.update("water")
    smoother.update("water")
    smoother.update(None)
    assert smoother.update(None) is None
