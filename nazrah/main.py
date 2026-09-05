import os
import queue
import threading
import time

from . import phrases as phrase_data
from .calibration import Calibrator, load_calibration, median_point, save_calibration
from .camera import WebcamSource
from .config import (
    CALIBRATION_FILE,
    CALIBRATION_POINTS_RATIO,
    CAMERA_INDEX,
    DWELL_SECONDS,
    FORCE_RECALIBRATE,
    GRID_COLUMNS,
    LIGHT_GPIO_PIN,
    NTFY_TOPIC,
    TARGET_CONFIRM_FRAMES,
)
from .dwell import DwellSelector
from .gaze_tracker import GazeTracker
from .light import GpioLightController, NoOpLightController
from .logger import UsageLogger
from .notifier import CaregiverNotifier
from .smoothing import TargetSmoother
from .tts import TTSEngine
from .ui import GridItem, GridUI

SCREEN_HOME = "home"
SCREEN_NEEDS = "needs"

HOME_ITEMS = [
    GridItem("light_off", "\U0001F4A1", "إطفاء الضوء"),
    GridItem("needs", "\U0001F4AC", "الاحتياجات"),
]

# The needs screen drops "wudu" and adds a way back to the home screen —
# prayer already covers that moment, and without a way back the light
# button would be unreachable for the rest of the session. Keeping this a
# clean 12 cells (matching len(phrases.PHRASES)) preserves the calibration
# grid's tuning; see the note in config.py about why that count matters.
NEEDS_ITEMS = [
    GridItem(p.id, p.icon, p.text_ar) for p in phrase_data.PHRASES if p.id != "wudu"
] + [GridItem("home", "\U0001F3E0", "الرئيسية")]


def run_calibration(ui, tracker, camera, screen_w, screen_h):
    """Grid calibration (size set by config.CALIBRATION_POINTS_RATIO): look
    at each highlighted point in turn and hold still while samples are
    collected. Naturally turning your head toward each point (not just
    moving your eyes) is expected and fine — see the note in
    gaze_tracker.GazeTracker. Only depends on screen dimensions, not on
    which screen (home/needs) is currently shown, so it only needs to run
    once per session even though the UI switches screens afterward."""
    calibrator = Calibrator()

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
    camera = WebcamSource(index=CAMERA_INDEX)
    tracker = GazeTracker()
    logger = UsageLogger()
    tts = TTSEngine()
    dwell = DwellSelector(dwell_seconds=DWELL_SECONDS)
    smoother = TargetSmoother(confirm_frames=TARGET_CONFIRM_FRAMES)

    try:
        light = GpioLightController(LIGHT_GPIO_PIN)
    except RuntimeError:
        light = NoOpLightController()

    notifier = CaregiverNotifier(NTFY_TOPIC) if NTFY_TOPIC else None
    if notifier is None:
        print(
            "[Notifier] NAZRAH_NTFY_TOPIC not set — urgent phrases won't send "
            "a remote caregiver alert, only the local speaker.",
            flush=True,
        )

    screen = SCREEN_HOME

    # A single persistent worker, not one thread per phrase: pyttsx3 can be
    # slow (or hang outright, as observed on this Windows setup), and
    # calling it on the same thread driving gaze tracking froze the whole
    # app right after a phrase was selected. A thread per call fixed that
    # but let two overlapping calls collide in pyttsx3's shared run-loop
    # state ("run loop already started") if a phrase was selected again
    # before the first finished speaking — this worker guarantees only one
    # speak() is ever in flight, queuing the rest instead. See tts.py.
    tts_queue = queue.Queue()

    def tts_worker():
        while True:
            phrase = tts_queue.get()
            tts.speak(phrase)

    threading.Thread(target=tts_worker, daemon=True).start()

    def speak_phrase(phrase_id):
        phrase = phrase_data.by_id(phrase_id)
        tts_queue.put(phrase)
        logger.log_selection(phrase)
        if phrase.urgent and notifier is not None:
            # Runs on a background thread so a slow/unreachable network
            # can't stall gaze tracking while an urgent alert is in flight.
            threading.Thread(target=notifier.notify, args=(phrase,), daemon=True).start()

    def on_select(cell_id):
        nonlocal screen

        # Cells that switch screens skip the flash: the frame that flash
        # would revert gets destroyed by show() well before its 400ms
        # timer runs out, and the screen change itself is enough visual
        # feedback that the selection registered.
        if screen == SCREEN_HOME:
            if cell_id == "needs":
                screen = SCREEN_NEEDS
                ui.show(NEEDS_ITEMS, columns=GRID_COLUMNS)
                # The smoother's memory of "what was being looked at" can
                # otherwise keep returning a home-screen id (e.g. "needs")
                # that no longer exists among the new screen's cells,
                # crashing set_active_cell on the very next frame.
                smoother.reset()
            elif cell_id == "light_off":
                ui.flash_selection(cell_id)
                light.turn_off()
        elif screen == SCREEN_NEEDS:
            if cell_id == "home":
                screen = SCREEN_HOME
                ui.show(HOME_ITEMS, columns=2)
                smoother.reset()
            else:
                ui.flash_selection(cell_id)
                speak_phrase(cell_id)

    ui = GridUI(on_select=on_select, items=HOME_ITEMS, columns=2)
    ui.update()
    screen_w = ui.root.winfo_screenwidth()
    screen_h = ui.root.winfo_screenheight()

    calibrator = None
    if not FORCE_RECALIBRATE and os.path.isfile(CALIBRATION_FILE):
        try:
            calibrator = load_calibration(CALIBRATION_FILE, screen_w, screen_h)
            print(
                f"Loaded saved calibration ({calibrator.num_samples} samples) from "
                f"{CALIBRATION_FILE} — skipping calibration. Set NAZRAH_RECALIBRATE=1 "
                "to force a fresh one.",
                flush=True,
            )
        except (OSError, ValueError, KeyError) as exc:
            print(f"Could not use saved calibration ({exc}) — running a fresh one.", flush=True)
            calibrator = None

    if calibrator is None:
        calibrator = run_calibration(ui, tracker, camera, screen_w, screen_h)
        print(f"Calibration done with {calibrator.num_samples} samples", flush=True)
        save_calibration(calibrator, CALIBRATION_FILE, screen_w, screen_h)
        print(f"Saved calibration to {CALIBRATION_FILE}", flush=True)

    # Threshold for the [SLOW] warnings below: a single loop iteration
    # (camera read, gaze inference, or a Tkinter update) taking longer than
    # this is the kind of thing that reads as the whole app "freezing" or
    # "lagging" to someone using it, even though the process is still
    # alive — worth flagging loudly rather than silently absorbing.
    _SLOW_STEP_SECONDS = 0.5

    try:
        frame_count = 0
        fps_window_start = time.monotonic()
        while not ui.closed:
            step_start = time.monotonic()
            frame = camera.read()
            step_end = time.monotonic()
            if step_end - step_start > _SLOW_STEP_SECONDS:
                print(f"[SLOW] camera.read() took {step_end - step_start:.2f}s", flush=True)
            if frame is None:
                ui.update()
                continue

            step_start = step_end
            eye_pos = tracker.get_eye_position(frame)
            step_end = time.monotonic()
            if step_end - step_start > _SLOW_STEP_SECONDS:
                print(
                    f"[SLOW] tracker.get_eye_position() took {step_end - step_start:.2f}s",
                    flush=True,
                )
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
                now = time.monotonic()
                fps = 15 / (now - fps_window_start) if now > fps_window_start else 0
                fps_window_start = now
                print(
                    f"fps={fps:.1f} eye_pos={eye_pos} screen=({screen_x}, {screen_y}) "
                    f"raw={raw_target_id} smoothed={target_id} progress={dwell.progress:.2f}",
                    flush=True,
                )

            fired = dwell.update(target_id)
            ui.set_active_cell(target_id, dwell.progress)
            if fired:
                on_select(fired)

            step_start = time.monotonic()
            ui.update()
            step_end = time.monotonic()
            if step_end - step_start > _SLOW_STEP_SECONDS:
                print(f"[SLOW] ui.update() took {step_end - step_start:.2f}s", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.close()
        camera.release()


if __name__ == "__main__":
    main()
