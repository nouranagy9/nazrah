from nazrah.light import NoOpLightController


def test_noop_light_turn_off_succeeds_without_hardware():
    light = NoOpLightController()
    assert light.turn_off() is True
