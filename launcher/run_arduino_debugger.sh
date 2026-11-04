#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
if ! command -v kotlinc >/dev/null 2>&1; then
  echo "Install the Kotlin command-line compiler (kotlinc) first." >&2
  exit 1
fi
BUILD_DIR=$(mktemp -d "${TMPDIR:-/tmp}/arduino-debugger.XXXXXX")
trap 'rm -rf "$BUILD_DIR"' EXIT HUP INT TERM
kotlinc launcher/ArduinoDebugger.kt -include-runtime -d "$BUILD_DIR/debugger.jar"
java -jar "$BUILD_DIR/debugger.jar"
