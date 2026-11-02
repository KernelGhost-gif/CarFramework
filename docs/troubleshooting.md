# Troubleshooting

## Key exchange

- Run `python keygen.py sender` on the sender and `python keygen.py receiver` on the CarView computer before exchanging keys. The generator refuses to overwrite existing files.
- For the first-time UDP public-key exchange, start the receiver command first, then the sender command, and enter the same freshly generated 64-character code on both devices. Code entry is hidden. Allow UDP port 5007 through the receiver's firewall. Use a new code for each pairing and share it through a trusted private channel.
- A different existing public key is never overwritten. An identical existing key is accepted, so an interrupted exchange can be retried with a fresh code. If replacing a key is intentional, verify the new identity and handle the old key manually.
- You can instead copy `sender_mldsa_pk.bin` to the receiver and `receiver_mldsa_pk.bin` to the sender through a trusted method. Never copy or share either private key. Both ends generate ML-KEM session keys during connection.

## No video

1. Open CarView's Connection tab and check the detected public and private key paths. The app searches the launch directory and project folders and prefers a complete pair from the same folder. You can select different files.
2. If CarView cannot import `cryptography`, set its Python executable to the Python from the environment where the dependency is installed. For the example in the operating guide, that is the repository's `.venv/bin/python` on macOS or Linux.
3. Start CarView's receiver first, then start the Pi sender within 30 seconds. Both devices need network access to the CarView computer on UDP ports 5005 and 5006. Enter the CarView computer's reachable IP address when the sender prompts for it.
4. Both devices need the current `encryption.py`. Older versions with a 192-byte nonce are incompatible with AES-GCM-SIV and with the current 12-byte protocol.
5. Check the Pi's terminal for camera, dependency or model errors. The sender opens camera index 0. A Raspberry Pi camera module may need a different capture setup from a USB camera.
6. Verify AVIF encoding with `python -c "import cv2; print(cv2.haveImageWriter('.avif'))"`. The sender requires an OpenCV build with AVIF support.
7. An encrypted frame larger than the UDP datagram limit cannot be sent by the current sender. Reduce the capture resolution or encoding quality if the sender reports a message-size error.

Do not run the original `reciever.py` and CarView receiver simultaneously on the same machine: both bind the same ports. CarView's receiver has not been verified against live hardware and does not operate the vehicle controls.

## Model files

The sender expects `model.ncnn.param` and `model.ncnn.bin` in `models/yolov26n_ncnn_model` and `models/yolov8n-pose_ncnn_model`. The root ignore rules exclude ordinary `.bin` files while explicitly allowing files under `models/`; if the YOLOv8 pose weights are missing from a fresh clone, obtain matching weights from a trusted copy or re-export the model. For example, with the sender's Ultralytics environment active:

```bash
yolo export model=yolov8n-pose.pt format=ncnn imgsz=320
```

Check that the resulting `yolov8n-pose_ncnn_model` directory contains both files, then place it under `models/`. Keep model parameters and weights from the same export together. The PyTorch `.pt` file used for export is not needed for NCNN inference.

## CarView and Bun

From the repository root, run `(cd Reciever && bun run start)`. The start command builds the Rust receiver and opens Electron. CarView uses Bun for setup and its launcher; Electron uses its own bundled runtime. Run `(cd Reciever && bun install)` once or after dependency changes. If a build fails, check that Bun, Rust and Cargo are available in the terminal's PATH.
