#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
VENV="$ROOT/.venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3 was not found. Set PYTHON to its executable and rerun." >&2
  exit 1
fi

"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
# Use the CPU wheels for the Raspberry Pi/Linux sender environment.
if [[ "$(uname -s)" == "Linux" ]]; then
  "$VENV/bin/python" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
else
  "$VENV/bin/python" -m pip install torch torchvision
fi
"$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"

if command -v bun >/dev/null 2>&1; then
  (cd "$ROOT/Reciever" && bun install)
else
  echo "Bun not found; skipping CarView JavaScript dependencies. Install Bun, then run: cd Reciever && bun install"
fi

cat <<EOF

Python setup complete. Activate the environment with:
  source "$VENV/bin/activate"

Start the sender from the repository root with:
  python main.py

Start CarView from the repository root with:
  (cd Reciever && bun run start)
EOF
