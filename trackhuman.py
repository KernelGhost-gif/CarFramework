import asyncio
import time
import serial
import serial.tools.list_ports

COMMANDS = {
    "left": ["turn left", "lt"],
    "center": ["forward", "fd"],
    "right": ["turn right", "rt"],
}

IDLE_CMD = "STOP"        # must be a command your firmware understands
LOST_TIMEOUT = 0.5       # seconds with no person before sending IDLE_CMD
HEARTBEAT = 0.5          # resend same command at least this often (0 to disable)
BAUD = 115200

# USB vendor IDs commonly seen on Arduino-style boards and USB-serial chips
KNOWN_VIDS = {
    0x2341,  # Arduino
    0x2A03,  # Arduino (dog hunter)
    0x1B4F,  # SparkFun
    0x16C0,  # PJRC (Teensy)
    0x1A86,  # WCH CH340/CH341 (clone Nanos, many ESP32 boards)
    0x10C4,  # Silicon Labs CP210x (many ESP32 boards)
    0x0403,  # FTDI
    0x303A,  # Espressif native USB
}


def find_arduino_port():
    candidates = []
    for p in serial.tools.list_ports.comports():
        desc = f"{p.description} {p.manufacturer or ''} {p.product or ''}".lower()
        score = 0
        if p.vid in KNOWN_VIDS:
            score += 2
        if "arduino" in desc:
            score += 3
        if p.device.startswith(("/dev/ttyACM", "/dev/ttyUSB")):
            score += 1
        if score >= 2:
            candidates.append((score, p.device))
    if not candidates:
        raise RuntimeError("No Arduino-like serial device found")
    candidates.sort(reverse=True)
    return candidates[0][1]


def _area(box):
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def largest_person(dets):
    people = [d for d in dets if d.get("label") == "person"]
    if not people:
        return None
    return max(people, key=lambda d: _area(d["box"]))


async def track_human(dets_q, stop, port=None):
    port = port or find_arduino_port()
    print(f"using serial port {port}", flush=True)

    ser = serial.Serial(
        port=port,
        baudrate=BAUD,
        timeout=1,
        write_timeout=1,
    )
    await asyncio.sleep(2)  # board may reset when the port opens

    def _send(cmd: str):
        ser.write(cmd.encode() + b"\n")
        ser.flush()

    last = None
    last_sent = 0.0
    last_seen = time.monotonic()

    try:
        while not stop.is_set():
            dets = None
            try:
                dets = await asyncio.wait_for(dets_q.get(), timeout=0.2)
                while not dets_q.empty():      # drain to newest frame
                    dets = dets_q.get_nowait()
            except asyncio.TimeoutError:
                pass

            command = None
            if dets is not None:
                person = largest_person(dets)
                if person is not None:
                    command = COMMANDS.get(person["zone"])
                    if command is not None:
                        last_seen = time.monotonic()

            now = time.monotonic()
            if command is None:
                if now - last_seen > LOST_TIMEOUT:
                    command = IDLE_CMD
                else:
                    continue

            changed = command != last
            stale = HEARTBEAT and (now - last_sent) > HEARTBEAT
            if changed or stale:
                try:
                    await asyncio.to_thread(_send, command[1])
                except serial.SerialException as e:
                    print(f"serial error: {e}", flush=True)
                    break
                last_sent = now

            if changed:
                print(command, flush=True)
                last = command
    finally:
        try:
            await asyncio.to_thread(_send, IDLE_CMD)
        except Exception:
            pass
        ser.close()
