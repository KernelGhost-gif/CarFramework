# Repository notes for coding agents

- Treat the repository root as the working directory for setup and Python commands.
- Run `./setup.sh` to create the root `.venv` and install the Python dependencies. The script installs CarView's Bun packages when Bun is available.
- Launch the camera sender with `python "Pi5/main.py"`, CarView with `(cd Reciever && bun run start)`, and the optional Python controller bridge with `python controller/mac_dualsense_servo.py`. The native Swift bridge is `./controller/run_swift_bridge.sh`.
- Keep sender modules in `Pi5/` and model bundles in `models/`; sender and model paths resolve from the repository root.
- Keep generated caches, logs, training runs, build output, local virtual environments, and private device keys out of version control. The root `.gitignore` documents these exclusions.
- Update the root README and relevant component documentation when setup or launch commands change.
