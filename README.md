# CarFramework

Use a Raspberry Pi as the camera sender and CarView on another computer to view its video stream.

## 1. Prepare both computers

Clone or update this repository on both devices, then open a terminal in the `CarFramework` folder on each. Use the same version of the repository on both devices.

Both devices need Python 3.11 or newer. From the repository root on each device, run the setup script to create `.venv` and install the Python dependencies used by the sender, receiver, and Arduino controller bridge:

```bash
./setup.sh
source .venv/bin/activate
```

Activate `.venv` again in each new terminal before running Python commands. The setup script installs CarView's Bun packages when Bun is available. On the CarView computer, also install [Bun](https://bun.sh/docs/installation) and [Rust and Cargo](https://www.rust-lang.org/tools/install); if Bun was not available during setup, run `cd Reciever && bun install` once from the repository root.

The Raspberry Pi sender code is grouped in `Pi 5/`. With AI tracking enabled, it needs both `models/yolov26n_ncnn_model` and `models/yolov8n-pose_ncnn_model`, each with `model.ncnn.param` and `model.ncnn.bin`. The YOLOv8 pose weights may be absent after cloning; see [model setup and troubleshooting](docs/troubleshooting.md#model-files).

## 2. Generate and exchange keys

Run these **once**, from the repository folder on the corresponding device:

```bash
# On the sender Pi
python keygen.py sender

# On the CarView computer
python keygen.py receiver
```

To exchange the public keys over UDP, generate a fresh pairing code on either device:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Share the code privately with the other device. On the CarView computer, run this first and enter the code when prompted:

```bash
python exchange_keys.py receiver
```

On the Pi, run the following within two minutes, replacing `CARVIEW_IP` with the CarView computer's IP address, and enter the same code:

```bash
python exchange_keys.py sender --peer CARVIEW_IP
```

Only public keys are exchanged. Keep each `*_sk.bin` private key on the device that created it. See [key exchange troubleshooting](docs/troubleshooting.md#key-exchange) for firewall and retry instructions.

## 3. Start CarView

On a macOS CarView computer, you can start CarView and the native Swift controller bridge together from the repository root (requires Java 11 or newer):

```bash
java launcher/ClientLauncher.java
```

See the [client launcher guide](launcher/README.md) for prerequisites and controller setup. To start CarView alone, run:

```bash
(cd Reciever && bun run start)
```

You only need `bun install` on first setup or after dependencies change. Open the **Connection** tab; CarView looks for the keys automatically. If needed, browse to `sender_mldsa_pk.bin` and `receiver_mldsa_sk.bin`. Set **Python executable** to the full path to the Python in your `.venv` if `python3` does not have `cryptography` installed.

Click **Start receiver**. The receiver waits up to 30 seconds for the sender.

## 4. Start the sender

On the Pi, from the repository root with `.venv` active:

```bash
python "Pi 5/main.py"
```

When prompted for the Mac IP, enter the CarView computer's reachable IP address. The application captures from camera index 0. To stop, press **Ctrl+C** on the Pi and use **Stop** in CarView's Connection tab.

### Camera-only mode

To stream without AI detection, pose estimation or tracking commands, create an empty file named `noai` in the sender's CarFramework folder before starting the sender:

```bash
touch noai
python "Pi 5/main.py"
```

This mode sends the unannotated camera feed and does not send vehicle-control commands. It does not load the AI models, so the AI-specific dependencies and model files are not needed. To re-enable AI tracking, remove the file and restart the sender:

```bash
rm noai
python "Pi 5/main.py"
```

The file is ignored by Git. Changes take effect when the sender starts.

### Arduino controller bridge

The setup script also installs the Python packages for the optional DualSense-to-UNO BLE bridge. With the UNO sketch uploaded and the controller paired, launch the bridge from the repository root:

```bash
python controller/mac_dualsense_servo.py
```

To send servo angles manually without a controller, use the [Kotlin Arduino debugger](launcher/README.md#arduino-command-debugger).

See [troubleshooting](docs/troubleshooting.md) if the stream does not appear. For implementation details, see [architecture](docs/architecture.md).
