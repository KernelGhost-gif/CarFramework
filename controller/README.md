# DualSense to UNO R4 WiFi servo

The Mac reads the DualSense left stick and sends its horizontal position over
BLE. The UNO R4 WiFi moves a positional servo connected to digital pin 6.

## Wiring

- Servo signal (usually yellow/orange/white) → UNO pin **6**
- Servo power (usually red) → a suitable **external 5 V supply**
- Servo ground (usually brown/black) → supply ground
- UNO GND → the same supply ground

Do not power the servo from the UNO's 5 V pin. Use an external supply rated for
the servo and join its ground to UNO GND. With power off, connect the servo
horn so its center position (90°) is mechanically safe.

## Upload the sketch

In Arduino IDE, install **ArduinoBLE** and **Servo** from Library Manager,
select **Arduino UNO R4 WiFi**, then upload
`../Arduino/UnoR4BleEcho/UnoR4BleEcho.ino`. The board advertises as `UNO-R4-Servo`.

## Connect the DualSense and run the Mac bridge

Pair the DualSense to macOS in **System Settings → Bluetooth**. From the
CarFramework repository root, run `./setup.sh` once, activate the root
environment, then start the bridge:

```sh
source .venv/bin/activate
python controller/mac_dualsense_servo.py
```

The client uses the DualSense **left stick's horizontal axis**: left moves the
servo toward 0°, center holds 90°, and right moves toward 180°. It discovers the
first controller and the UNO automatically. Press Ctrl+C to stop; the servo
holds its last position. If you want to limit travel for your linkage, adjust
the angle mapping in `controller/mac_dualsense_servo.py` before running it.

## Native Swift option

The Swift bridge uses Apple's **Game Controller** framework to read the
DualSense and **Core Bluetooth** to send angles directly to the UNO. It uses
the same stick mapping and BLE service, so run either Mac bridge at a time.
Pair the controller and run this from the repository root:

```sh
./controller/run_swift_bridge.sh
```

The script builds a small app bundle in the system temporary folder, with the
Bluetooth usage description required by macOS, then launches it in Terminal.
Approve the Bluetooth access prompt if macOS shows one. Apple's framework
provides the controller's extended gamepad profile and thumbstick input.
