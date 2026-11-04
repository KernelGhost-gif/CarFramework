#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ROOT
export PYTHON="${PYTHON:-python3}"
export VENV="$ROOT/.venv"

if ! command -v clang >/dev/null 2>&1; then
  echo "Clang was not found. Install Clang and rerun setup." >&2
  exit 1
fi

BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/carframework-setup.XXXXXXXX")"
trap 'rm -rf "$BUILD_DIR"' EXIT
printf '%s\n' 'Compiling the BrainSh setup interpreter...'
clang -std=c99 -Wall -Wextra -pedantic "$ROOT/Setup/brainsh.c" -o "$BUILD_DIR/brainsh"
export BRAINSH="$BUILD_DIR/brainsh"
"$BRAINSH" --allow-shell "$ROOT/Setup/setup.bsh"
