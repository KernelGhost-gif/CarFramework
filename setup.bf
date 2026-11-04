++++++++[>++++++++++<-]
>+++.
++++++++++++++++++.
+++++++++++++++.
+.
-----.
------------------------------------------------------------------------------------------------------.
!{printf '%s\n' 'Checking Python...'}
!{if ! command -v "$PYTHON" >/dev/null 2>&1; then printf '%s\n' 'Python 3 was not found. Set PYTHON to its executable and rerun.' >&2; exit 1; fi}
!{printf '%s\n' 'Creating the Python virtual environment...'}
!{"$PYTHON" -m venv "$VENV"}
!{printf '%s\n' 'Upgrading pip...'}
!{"$VENV/bin/python" -m pip install --upgrade pip}
!{printf '%s\n' 'Installing PyTorch and torchvision...'}
!{if [ "$(uname -s)" = Linux ]; then "$VENV/bin/python" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu; else "$VENV/bin/python" -m pip install torch torchvision; fi}
!{printf '%s\n' 'Installing Python requirements...'}
!{"$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"}
!{if command -v bun >/dev/null 2>&1; then printf '%s\n' 'Installing CarView JavaScript dependencies...'; cd "$ROOT/Reciever" && bun install; else printf '%s\n' 'Bun not found; skipping CarView JavaScript dependencies. Install Bun, then run: cd Reciever && bun install'; fi}
!{printf '\nPython setup complete. Activate the environment with:\n  source "%s/bin/activate"\n\nStart the sender from the repository root with:\n  python "Pi5/main.py"\n\nStart CarView from the repository root with:\n  (cd Reciever && bun run start)\n' "$VENV"}
