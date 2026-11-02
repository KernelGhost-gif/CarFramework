# Repository notes for coding agents

- Treat the repository root as the working directory for setup and Python commands.
- Run `./setup.sh` to create the root `.venv` and install the Python dependencies. The script installs CarView's Bun packages when Bun is available.
- Launch the camera sender with `python main.py`, CarView with `(cd Reciever && bun run start)`, and the optional Arduino BLE bridge with `python Arduino/mac_dualsense_servo.py`.
- Keep model bundles in `models/`; `mpipe.py` resolves their paths relative to itself.
- Keep generated caches, logs, training runs, build output, local virtual environments, and private device keys out of version control. The root `.gitignore` documents these exclusions.
- Update the root README and relevant component documentation when setup or launch commands change.
