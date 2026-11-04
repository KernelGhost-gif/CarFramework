# Architecture

CarFramework is a camera, inference and vehicle-control framework for Raspberry Pi and compatible vehicles. It includes CarView, an Electron desktop viewer backed by a Rust receiver process and the existing Python cryptography implementation.

## Video and control

- `Pi5/main.py` captures frames with OpenCV, starts the sender and runs the control loop.
- `Pi5/mpipe.py` loads the YOLOv26 nano detection and YOLOv8 nano pose NCNN models from root `models/`, performs inference and identifies a person's position.
- `Pi5/sender.py` encodes frames as AVIF, encrypts them using `Pi5/encryption.py`, and sends them as UDP datagrams. It prompts for the receiver's IP address at startup.
- `Pi5/trackhuman.py` translates tracked positions into UDP commands for the configured UNO address. This path is separate from CarView and can be replaced for other vehicles. A root `noai` file disables model loading, inference and this control loop at startup; the sender streams the original frames instead.
- `Reciever/src/main.rs` receives video datagrams, while `Reciever/worker/crypto_worker.py` uses `Pi5/encryption.py`. Electron displays the decoded AVIF images and connection controls.

The model files are exported from PyTorch to NCNN for deployment. An earlier YOLOv26-large-to-YOLOv8-nano distillation experiment was discontinued after comparison with YOLOv26 nano.

## Keys and transport

`keygen.py` creates ML-DSA-44 identity keys. `exchange_keys.py` transfers public keys over UDP using an authenticated one-time pairing code; the public keys themselves are not encrypted. The stream handshake uses ML-KEM-768 and ML-DSA-44, then AES-GCM-SIV with a 12-byte nonce for frame encryption. The session key is created during the handshake. Both ends must run compatible protocol versions.

The default ports are UDP 5005 for video, 5006 for key exchange, and 5007 for first-time public-key exchange. The sender transmits each frame as one datagram and does not implement application-level fragmentation.

This repository is licensed under LGPL-3.0; see [LICENSE](../LICENSE).
