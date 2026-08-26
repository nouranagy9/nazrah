"""Light control. Same split as camera.py: a real implementation for the
deployed Pi (a relay/light wired to a GPIO pin) and a no-op stand-in for
development on a machine with no such hardware attached.
"""

from abc import ABC, abstractmethod


class LightController(ABC):
    @abstractmethod
    def turn_off(self):
        """Turns the light off. Returns True on success."""


class NoOpLightController(LightController):
    """No light hardware wired up — just logs what would have happened.
    Used for development/testing away from the actual device."""

    def turn_off(self):
        print("[Light] (no hardware configured) Would turn the light off.", flush=True)
        return True


class GpioLightController(LightController):
    """Controls a relay/light wired to a Raspberry Pi GPIO pin via
    gpiozero. Only usable on a Pi with gpiozero installed and the
    hardware actually wired up."""

    def __init__(self, pin=17):
        try:
            from gpiozero import OutputDevice
        except ImportError as exc:
            raise RuntimeError(
                "gpiozero is not installed. GpioLightController only runs on "
                "a Raspberry Pi with a relay/light wired to a GPIO pin."
            ) from exc
        self._relay = OutputDevice(pin, active_high=True, initial_value=True)

    def turn_off(self):
        self._relay.off()
        return True
