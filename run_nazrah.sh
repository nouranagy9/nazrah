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

# Enables caregiver push alerts for urgent phrases (see README.md's
# "Caregiver alerts" section). This is a smoke-test topic used during
# development -- swap it for a real, private, long-random topic name
# before actually relying on this for a real caregiver (the topic name
# IS the access control, so a guessable one isn't private).
export NAZRAH_NTFY_TOPIC="nazrah-smoketest-8f3k2x9p7q"

python3 -m nazrah.main
