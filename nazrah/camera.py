"""Camera sources. Development happens against a regular USB/laptop webcam;
deployment on the actual device uses the Pi Camera Module. Both implement the
same tiny interface so the rest of the pipeline (gaze_tracker, main) never
needs to know which one it's talking to.
"""

from abc import ABC, abstractmethod

import cv2


class CameraSource(ABC):
    @abstractmethod
    def read(self):
        """Returns the latest frame as a BGR numpy array, or None if a frame
        isn't available yet."""

    @abstractmethod
    def release(self):
        """Releases the underlying hardware/device handle."""


class WebcamSource(CameraSource):
    """Any USB/built-in webcam via OpenCV. Used for development and testing
    on a regular laptop/desktop."""

    def __init__(self, index=0, width=1280, height=720):
        # Higher resolution than the old 640x480 default gives MediaPipe
        # more pixels across the eye region, which directly improves how
        # precisely it can localize the iris landmark — the gaze signal is
        # already weak (see gaze_tracker.py), so every bit of localization
        # precision matters for whether nearby calibration points are
        # actually distinguishable.
        self._cap = cv2.VideoCapture(index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {index}")

    def read(self):
        ok, frame = self._cap.read()
        return frame if ok else None

    def release(self):
        self._cap.release()


class PiCameraSource(CameraSource):
    """Raspberry Pi Camera Module via picamera2. Only usable on a Raspberry
    Pi with picamera2 installed — this is what the deployed device uses."""

    def __init__(self, width=640, height=480):
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError(
                "picamera2 is not installed. PiCameraSource only runs on a "
                "Raspberry Pi with the Pi Camera Module set up."
            ) from exc

        self._picam2 = Picamera2()
        config = self._picam2.create_preview_configuration(
            main={"size": (width, height), "format": "BGR888"}
        )
        self._picam2.configure(config)
        self._picam2.start()

    def read(self):
        return self._picam2.capture_array()

    def release(self):
        self._picam2.stop()
