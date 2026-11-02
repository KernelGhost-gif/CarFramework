#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR="${TMPDIR:-/tmp}/DualSenseServoBridge.app"
CONTENTS="$APP_DIR/Contents"

mkdir -p "$CONTENTS/MacOS"
swiftc "$SCRIPT_DIR/mac_dualsense_servo.swift" \
  -o "$CONTENTS/MacOS/DualSenseServoBridge" \
  -framework GameController \
  -framework CoreBluetooth
cp "$SCRIPT_DIR/macOSInfo.plist" "$CONTENTS/Info.plist"
codesign --force --deep --sign - "$APP_DIR"
exec "$CONTENTS/MacOS/DualSenseServoBridge"
