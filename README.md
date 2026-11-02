# Car Framework
Unified framework for all RPI and UNO based cars that require CV

## main.py
Captures the frame, puts it in a async q to allow other functions from other files to use it

Also calls the functions from other files and puts them in a async loop

## sender.py
Compresses the file into AVIF format, encrypt it using encryption.py and sends it and also runs the detection loop

## encryption.py
Generates keys using ML-KEM and signs the keys with ML-DSA to verrify source and authenticity, then uses AES256-GMCSIV to encrypt the image. Same stac, but in reverse for decryption

## trackhuman.py
uses the tracked location values to send controlls. This can be completely swapped out for other projects with other needs

# Models:
yolov8n-pose and yolov26n converted to NCNN from pytorch for speed reasons
Project of distilling v26l into v8n has been canceled due to the vastly superior performance of v26n compared to tuned v8n

# License:
GNU LGPL-3.0

## First-time key setup

Each device needs its own ML-DSA identity. Install a Python `cryptography` version that supports ML-DSA and ML-KEM (47.0.0 or newer) on both devices. From the CarFramework folder, run the appropriate command **once on each device**:

```bash
# On the camera/sender device:
python3 keygen.py sender

# On the CarView/receiver device:
python3 keygen.py receiver
```

The script writes raw key files in the CarFramework folder, refuses to overwrite existing files, and keeps private files accessible only to the current user on systems that support Unix file permissions. An existing directory can be selected with `--output-dir PATH`.

Exchange **only the public keys**, using a trusted method and verifying their authenticity:

- Copy `sender_mldsa_pk.bin` to the receiver device, and select it as the sender public key in CarView.
- Copy `receiver_mldsa_pk.bin` to the sender's CarFramework folder (or the directory from which `main.py` runs).
- Keep `sender_mldsa_sk.bin` on the sender and `receiver_mldsa_sk.bin` on the receiver. Select the latter as the receiver private key in CarView. Never share or commit private keys.

ML-KEM session keys are created during the connection; they do not need a separate setup command. The existing 192-byte nonce setting must be corrected consistently on both devices before encrypted video can work; see `Reciever/README.md`.

### Exchange the public keys over UDP

After generating each device's own key pair as above, you can exchange the two public keys without `scp`. Both devices need `exchange_keys.py` and must be able to communicate over UDP port 5007 (or the same port selected with `--port`). Run the receiver first.

1. Generate a fresh pairing code on either device with `python3 -c 'import secrets; print(secrets.token_hex(32))'`. Share the code with the person at the other device through a trusted private channel. Use a new code for each pairing.
2. On the CarView device, from the CarFramework folder, run `python3 exchange_keys.py receiver` and enter the code when prompted.
3. Within two minutes, on the sender Pi run `python3 exchange_keys.py sender --peer CARVIEW_IP`, replacing `CARVIEW_IP` with the CarView device's IP address. Enter the same code.
4. Select `sender_mldsa_pk.bin` and `receiver_mldsa_sk.bin` in CarView. The Pi automatically receives `receiver_mldsa_pk.bin` in its CarFramework folder.

Only public keys are sent. The code authenticates the exchange; it does not encrypt the public keys. Existing different public keys are never overwritten. If a transfer is interrupted, rerun both commands using a fresh code; a matching already-saved public key is accepted. Both devices must have their own key pair first. On systems with a firewall, permit UDP 5007 on the receiver.
