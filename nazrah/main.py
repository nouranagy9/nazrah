import threading
import time

from . import phrases as phrase_data
from .calibration import Calibrator, median_point
from .camera import WebcamSource
from .config import (
    CALIBRATION_POINTS_RATIO,
    DWELL_SECONDS,
    GRID_COLUMNS,
    NTFY_TOPIC,
    TARGET_CONFIRM_FRAMES,
)
from .dwell import DwellSelector
from .gaze_tracker import GazeTracker
from .logger import UsageLogger
from .notifier import CaregiverNotifier
from .smoothing import TargetSmoother
from .tts import TTSEngine
from .ui import PhraseGridUI


def run_calibration(ui, tracker, camera):
    """Grid calibration (size set by config.CALIBRATION_POINTS_RATIO): look
    at each highlighted point in turn and hold still while samples are
    collected. Naturally turning your head toward each point (not just
    moving your eyes) is expected and fine — see the note in
    gaze_tracker.GazeTracker."""
    calibrator = Calibrator()
    screen_w = ui.root.winfo_screenwidth()
    screen_h = ui.root.winfo_screenheight()

    for rx, ry in CALIBRATION_POINTS_RATIO:
        target = (int(rx * screen_w), int(ry * screen_h))
        ui.show_calibration_target(*target)
        print("Look at the red dot and hold still...")
        time.sleep(1.2)  # give the user time to move their gaze to the dot

        samples = []
        deadline = time.monotonic() + 2.0
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

        median_eye = median_point(samples)
        calibrator.add_sample(median_eye, target)
        print(f"  target={target} median_eye_pos={median_eye} samples={len(samples)}", flush=True)

    ui.hide_calibration_target()
    return calibrator


def main():
    camera = WebcamSource()
    tracker = GazeTracker()
    logger = UsageLogger()
    tts = TTSEngine()
    dwell = DwellSelector(dwell_seconds=DWELL_SECONDS)
    smoother = TargetSmoother(confirm_frames=TARGET_CONFIRM_FRAMES)

    notifier = CaregiverNotifier(NTFY_TOPIC) if NTFY_TOPIC else None
    if notifier is None:
        print(
            "[Notifier] NAZRAH_NTFY_TOPIC not set — urgent phrases won't send "
            "a remote caregiver alert, only the local speaker.",
            flush=True,
        )

    def on_select(phrase_id):
        phrase = phrase_data.by_id(phrase_id)
        tts.speak(phrase)
        logger.log_selection(phrase)
        ui.flash_selection(phrase_id)
        if phrase.urgent and notifier is not None:
            # Runs on a background thread so a slow/unreachable network
            # can't stall gaze tracking while an urgent alert is in flight.
            threading.Thread(target=notifier.notify, args=(phrase,), daemon=True).start()

    ui = PhraseGridUI(on_select=on_select, columns=GRID_COLUMNS)
    ui.update()

    calibrator = run_calibration(ui, tracker, camera)
    print(f"Calibration done with {calibrator.num_samples} samples", flush=True)

    try:
        frame_count = 0
        while not ui.closed:
            frame = camera.read()
            if frame is None:
                ui.update()
                continue

            eye_pos = tracker.get_eye_position(frame)
            raw_target_id = None
            screen_x = screen_y = None
            if eye_pos is not None and calibrator.num_samples > 0:
                screen_x, screen_y = calibrator.nearest_target(eye_pos)
                raw_target_id = ui.hit_test(screen_x, screen_y)

            # Smooth before feeding into dwell: a single frame misclassified
            # to a neighboring calibration point (easy when points are
            # packed close together — see calibration.py) shouldn't be able
            # to flip the target dwell is timing.
            target_id = smoother.update(raw_target_id)

            frame_count += 1
            if frame_count % 15 == 0:
                print(
                    f"eye_pos={eye_pos} screen=({screen_x}, {screen_y}) "
                    f"raw={raw_target_id} smoothed={target_id} progress={dwell.progress:.2f}",
                    flush=True,
                )

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
