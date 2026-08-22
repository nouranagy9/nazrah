import time

from . import phrases as phrase_data
from .calibration import Calibrator
from .camera import WebcamSource
from .config import CALIBRATION_POINTS_RATIO, DWELL_SECONDS, GRID_COLUMNS
from .dwell import DwellSelector
from .gaze_tracker import GazeTracker
from .logger import UsageLogger
from .tts import TTSEngine
from .ui import PhraseGridUI


def run_calibration(ui, tracker, camera):
    """Standard 5-point calibration: look at each highlighted corner/center
    in turn and hold still while samples are collected."""
    calibrator = Calibrator()
    screen_w = ui.root.winfo_screenwidth()
    screen_h = ui.root.winfo_screenheight()

    for rx, ry in CALIBRATION_POINTS_RATIO:
        target = (int(rx * screen_w), int(ry * screen_h))
        print(f"Look at point {target} and hold still...")
        time.sleep(1.0)  # give the user time to move their gaze

        samples = []
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            frame = camera.read()
            if frame is None:
                continue
            eye_pos = tracker.get_eye_position(frame)
            if eye_pos is not None:
                samples.append(eye_pos)

        if not samples:
            print("No face detected during this calibration point — skipping it.")
            continue

        avg_eye = (
            sum(p[0] for p in samples) / len(samples),
            sum(p[1] for p in samples) / len(samples),
        )
        calibrator.add_sample(avg_eye, target)

    calibrator.fit()
    return calibrator


def main():
    camera = WebcamSource()
    tracker = GazeTracker()
    logger = UsageLogger()
    tts = TTSEngine()
    dwell = DwellSelector(dwell_seconds=DWELL_SECONDS)

    def on_select(phrase_id):
        phrase = phrase_data.by_id(phrase_id)
        tts.speak(phrase)
        logger.log_selection(phrase)
        ui.flash_selection(phrase_id)

    ui = PhraseGridUI(on_select=on_select, columns=GRID_COLUMNS)
    ui.update()

    calibrator = run_calibration(ui, tracker, camera)

    try:
        while True:
            frame = camera.read()
            if frame is None:
                ui.update()
                continue

            eye_pos = tracker.get_eye_position(frame)
            target_id = None
            if eye_pos is not None and calibrator.is_fitted:
                screen_x, screen_y = calibrator.predict(eye_pos)
                target_id = ui.hit_test(screen_x, screen_y)

            fired = dwell.update(target_id)
            ui.set_active_cell(target_id, dwell.progress)
            if fired:
                on_select(fired)

            ui.update()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.close()
        camera.release()


if __name__ == "__main__":
    main()
