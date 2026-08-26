# Deploying to Raspberry Pi 5 + CrowPi + USB camera

This covers getting this repo running on the actual device: a Raspberry Pi
5 in a CrowPi case, with a USB camera (not the CSI ribbon camera). Because
[`nazrah/camera.py`](../nazrah/camera.py)'s `WebcamSource` uses OpenCV's
`VideoCapture`, which talks to any USB UVC webcam on Linux the same way it
talks to a laptop webcam on Windows — **no code changes are needed** to
move from your Windows dev machine to the Pi. You only need
`PiCameraSource` if you later swap to the CSI camera module instead of the
USB one.

## 1. Flash the SD card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your
Windows machine:

1. Choose **Raspberry Pi 5** as the device.
2. Choose **Raspberry Pi OS (64-bit)** — the full **Desktop** version, not
   Lite. Tkinter needs a GUI/display server to draw the phrase grid, so
   Lite won't work here.
3. Click the gear icon (advanced options) before writing:
   - Set a hostname (e.g. `nazrah-pi`)
   - Enable SSH if you want to set things up remotely
   - Set your Wi-Fi SSID/password so it's online on first boot
4. Write it to the SD card and boot the Pi.

## 2. Physical setup

- Assemble the CrowPi per its manual (screen + speaker connections into
  the Pi 5's ports).
- Plug the **USB camera** into any USB port on the Pi 5.
- Power the Pi via USB-C.

## 3. Get the code onto the Pi

Simplest path, since the repo is already on GitHub — open a terminal on
the Pi (or SSH in) and clone it directly:

```bash
git clone https://github.com/nouranagy9/nazrah.git
cd nazrah
```

## 4. System dependencies

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-tk espeak libatlas-base-dev
```

- `python3-tk` — Tkinter isn't always in the base image
- `espeak` — the offline TTS engine `pyttsx3` uses on Linux (its Arabic
  pronunciation is rough; see the note on a recorded audio bank below)
- `libatlas-base-dev` — a common OpenCV runtime dependency on Pi OS

## 5. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Raspberry Pi OS's pip is pre-configured to also pull from
[piwheels.org](https://www.piwheels.org/), which has prebuilt ARM wheels
for opencv-python and mediapipe — without that, some of these packages
would need to compile from source, which is slow (mediapipe especially).
If `pip install mediapipe` fails to find a wheel for your exact Python
version, check
[piwheels.org/project/mediapipe](https://www.piwheels.org/project/mediapipe)
for which versions are available and pin to one of those in
`requirements.txt`.

If you're wiring up the home screen's light/relay control (see step 7a),
also install gpiozero — deliberately not in `requirements.txt` since it's
Pi-only and would be dead weight on a dev machine:

```bash
pip install gpiozero
```

Without it, [`nazrah/light.py`](../nazrah/light.py)'s `GpioLightController`
just fails to import and `main.py` falls back to `NoOpLightController`
automatically (logs what it would have done instead of controlling real
hardware) — so this step is optional if you don't have a relay wired up
yet.

## 6. Check the camera

```bash
ls /dev/video*
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read()[0])"
```

Should print `True`. If you get a permissions error, add your user to the
`video` group and log back in:

```bash
sudo usermod -aG video $USER
```

## 7. Wire up the light (optional)

The home screen's "turn off light" button drives a relay via
[`nazrah/light.py`](../nazrah/light.py) — a relay module or relay-driven
light wired to GPIO pin 17 by default (`config.LIGHT_GPIO_PIN`). CrowPi
kits typically include a relay module on the breadboard for exactly this
kind of experiment.

Check it's actually controllable before trusting the app with it:

```bash
python3 -c "
from gpiozero import OutputDevice
relay = OutputDevice(17, active_high=True, initial_value=True)
relay.off()
"
```

If the wired light/relay turns off, you're set. Skip this step entirely
if you don't have hardware wired up yet — the app runs fine without it
(see the gpiozero note in step 5).

## 8. Check audio output

CrowPi's speaker routing depends on how it's wired (3.5mm jack, HDMI, or
USB, depending on your CrowPi version) — set the right output device:

```bash
sudo raspi-config
# System Options → Audio → pick the correct output
```

Test it:

```bash
espeak "hello"
```

## 9. Run it

Make sure you're running on the Pi's actual desktop (not a headless SSH
session with no display attached) — Tkinter needs `$DISPLAY` set to a real
screen. If you're SSH'd in but the Pi is also connected to the CrowPi
screen, run:

```bash
export DISPLAY=:0
```

If you set up [caregiver alerts](../README.md#caregiver-alerts-optional),
set the topic too (same value the caregiver's ntfy app is subscribed to):

```bash
export NAZRAH_NTFY_TOPIC="your-long-random-topic-name"
```

Then:

```bash
python3 -m nazrah.main
```

First run downloads the face landmark model (~4MB) — needs internet once,
then it's cached in `nazrah/models/` and works offline after that.
Calibration runs once at startup, then lands on the home screen (light
off / needs) — see "How it works" in the main [README](../README.md) for
the full session flow.

## Troubleshooting

- **`mediapipe` won't install** — check piwheels for a matching wheel (see
  step 5); as a last resort it can build from source but expect it to take
  a long time on a Pi.
- **Camera opens but frames are `None`** — try a different USB port, or
  lower the requested resolution in `WebcamSource.__init__` (some USB
  webcams don't support 640x480 in every mode).
- **Everything works but feels laggy** — MediaPipe's face detection is the
  expensive step per frame; on a Pi 5 it should still run at an
  interactive frame rate, but if it doesn't, that's worth measuring and
  writing up for Criterion D (evaluation) rather than just tolerating it.
- **TTS sounds bad / not real Arabic** — expected with `espeak`. Record
  real audio clips for each phrase (a family member reading them aloud is
  more authentic anyway) and drop them into an audio bank directory, then
  pass `audio_bank_dir=` to `TTSEngine` in `nazrah/main.py` — see
  "Adding phrases" in the main [README](../README.md).
- **"إطفاء الضوء" doesn't actually turn anything off** — check the console
  output right after startup for `[Light] (no hardware configured)...`,
  which means `GpioLightController` failed to initialize (gpiozero not
  installed, or `OutputDevice(17, ...)` couldn't claim the pin) and it
  silently fell back to the no-op controller. Re-run the check command
  from step 7 directly to isolate whether it's a wiring issue or a
  software one.

## Optional: launch on boot

Once it's working reliably, you can make it start automatically so the
device just works when powered on — happy to set that up (a systemd
service or a desktop autostart entry) once you've tested it manually a
few times first.
