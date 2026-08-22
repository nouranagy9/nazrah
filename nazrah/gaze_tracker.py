import os
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)
_DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "face_landmarker.task")

# The FaceLandmarker task outputs 478 landmarks (the standard 468-point face
# mesh plus 10 iris points); 468 and 473 are the right and left iris centers.
_RIGHT_IRIS_CENTER = 468
_LEFT_IRIS_CENTER = 473


def ensure_model(model_path=_DEFAULT_MODEL_PATH):
    """Downloads the face landmark model on first use and caches it locally.
    Needs a one-time internet connection; the model then works fully
    offline, which matters for a device that may not always have wifi."""
    if os.path.isfile(model_path):
        return model_path
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    print(f"Downloading face landmark model to {model_path}...")
    urllib.request.urlretrieve(_MODEL_URL, model_path)
    return model_path


class GazeTracker:
    """Wraps MediaPipe's Face Landmarker task to extract a single normalized
    (x, y) gaze position per frame, averaged across both iris centers. Runs
    in real time on a Raspberry Pi 4 without any dedicated eye-tracking
    hardware.
    """

    def __init__(self, model_path=None):
        model_path = ensure_model(model_path or _DEFAULT_MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=mp_vision.RunningMode.IMAGE,
            num_faces=1,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)

    def get_eye_position(self, frame_bgr):
        """Returns the normalized (x, y) iris position in [0, 1] x [0, 1]
        image space, or None if no face was detected in this frame."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)
        if not result.face_landmarks:
            return None

        landmarks = result.face_landmarks[0]
        right = landmarks[_RIGHT_IRIS_CENTER]
        left = landmarks[_LEFT_IRIS_CENTER]
        return ((right.x + left.x) / 2, (right.y + left.y) / 2)

    def close(self):
        self._landmarker.close()
