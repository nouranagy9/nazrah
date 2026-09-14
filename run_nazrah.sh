#!/bin/bash
# Launches Nazrah with this device's settings. Double-click the "Nazrah"
# desktop icon instead of running this directly — see docs/raspberry_pi_setup.md
# for how that's wired up. Safe to re-run any time; it doesn't need a
# fresh calibration unless the screen or camera changed (see
# NAZRAH_RECALIBRATE in nazrah/config.py).

cd "$(dirname "$0")" || exit 1
source .venv311/bin/activate

export DISPLAY=:0
# Camera index isn't stable across reboots/replugs (see
# docs/raspberry_pi_setup.md) -- re-check with `v4l2-ctl --list-devices`
# if the app can't open the camera, and update the line below.
export NAZRAH_CAMERA_INDEX=0

# Uncomment and set this to enable caregiver push alerts for urgent
# phrases (see README.md's "Caregiver alerts" section):
# export NAZRAH_NTFY_TOPIC="your-caregiver-alert-topic-here"

python3 -m nazrah.main
