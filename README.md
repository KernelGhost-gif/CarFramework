# CarFramework

Use a Raspberry Pi as the camera sender and CarView on another computer to view its video stream.

## 1. Prepare both computers

Clone or update this repository on both devices, then open a terminal in the `CarFramework` folder on each. Use the same version of the repository on both devices.

Both devices need Python 3.11 or newer and the project's cryptography dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'cryptography>=47'
```

Activate `.venv` again in each new terminal before running the Python commands below. On the CarView computer, you will also need [Bun](https://bun.sh/docs/installation) and [Rust and Cargo](https://www.rust-lang.org/tools/install).

On the sender Pi, install the video and inference dependencies in the same environment (for camera-only mode, see below):

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install ncnn opencv-python ultralytics
```

With AI tracking enabled, the sender needs both `yolov26n_ncnn_model` and `yolov8n-pose_ncnn_model`, each with `model.ncnn.param` and `model.ncnn.bin`. The YOLOv8 pose weights may be absent after cloning; see [model setup and troubleshooting](docs/troubleshooting.md#model-files).

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

On the CarView computer:

```bash
cd Reciever
bun install
bun run start
```

You only need `bun install` on first setup or after dependencies change. Open the **Connection** tab; CarView looks for the keys automatically. If needed, browse to `sender_mldsa_pk.bin` and `receiver_mldsa_sk.bin`. Set **Python executable** to the full path to the Python in your `.venv` if `python3` does not have `cryptography` installed.

Click **Start receiver**. The receiver waits up to 30 seconds for the sender.

## 4. Start the sender

On the Pi, from the repository folder with `.venv` active:

```bash
python main.py
```

When prompted for the Mac IP, enter the CarView computer's reachable IP address. The application captures from camera index 0. To stop, press **Ctrl+C** on the Pi and use **Stop** in CarView's Connection tab.

### Camera-only mode

To stream without AI detection, pose estimation or tracking commands, create an empty file named `noai` in the sender's CarFramework folder before starting the sender:

```bash
touch noai
python main.py
```

This mode sends the unannotated camera feed and does not send vehicle-control commands. It does not load the AI models, so the AI-specific dependencies and model files are not needed. To re-enable AI tracking, remove the file and restart the sender:

```bash
rm noai
python main.py
```

The file is ignored by Git. Changes take effect when the sender starts.

See [troubleshooting](docs/troubleshooting.md) if the stream does not appear. For implementation details, see [architecture](docs/architecture.md).
