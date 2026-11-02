# CarView

An Electron desktop interface backed by a Rust UDP receiver for the CarFramework video stream. The Rust process binds UDP 5005 and passes encrypted datagrams to a small Python worker. The worker calls the existing `../encryption.py` for the authenticated key exchange on UDP 5006 and for decryption. Electron displays the resulting AVIF frames. This is a desktop app; Electron and the crypto worker are separate from the Rust executable.

## Requirements

- Rust and Cargo.
- Bun; Electron is installed locally by Bun.
- Python 3 with a version of `cryptography` that provides `MLKEM768`, `MLDSA44`, and `AESGCMSIV` (the same requirements as the existing framework).
- The sender's trusted ML-DSA public key and the receiver's ML-DSA private key, in the existing raw formats.

From this directory, run `bun install` and `bun run start`. The latter builds the Rust process in release mode and launches Electron. Bun runs the Electron launcher without relying on the system Node installation; Electron itself uses its bundled runtime. Select the key files and, if necessary, enter the full path to the Python executable for the environment containing the dependency. Start the receiver before starting the sender; they must have network access to UDP ports 5005 and 5006. Update the sender's hard-coded destination IP to this computer's reachable address.

For first-time key creation and public-key exchange, see the [key setup instructions](../README.md#first-time-key-setup).

## Connection notes

Both devices must use the current `encryption.py`, which uses the 12-byte nonce required by AES-GCM-SIV. Older versions with a 192-byte nonce are incompatible. Large frames may exceed UDP's maximum datagram size because the sender does not fragment them. Do not run this app and `reciever.py` on the same ports simultaneously.

The receiver has not been tested against live hardware. It does not connect to robot controls or the WebSocket dashboard from the pull request.
