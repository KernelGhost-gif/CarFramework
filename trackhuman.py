import asyncio
import time
import serial
import serial.tools.list_ports

# zone -> single-char command understood by the Arduino sketch
COMMANDS = {
    "left": "l",
    "center": "f",
    "right": "r",
}
IDLE_CMD = "s"
NAMES = {"l": "turn left", "f": "forward", "r": "turn right", "s": "stop"}

BAUD = 9600
LOST_TIMEOUT = 0.5      # seconds without a person before sending IDLE_CMD
HEARTBEAT = 0.5         # resend same command at least this often (0 to disable)
RECONNECT_DELAY = 2.0   # seconds between reconnect attempts
BOOT_DELAY = 2.0        # Arduino resets when the port opens

# USB vendor IDs commonly seen on Arduino-style boards and USB-serial chips
KNOWN_VIDS = {
    0x2341,  # Arduino
    0x2A03,  # Arduino (dog hunter)
    0x1B4F,  # SparkFun
    0x16C0,  # PJRC (Teensy)
    0x1A86,  # WCH CH340/CH341
    0x10C4,  # Silicon Labs CP210x
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


async def _run(dets_q, stop, port):
    """One connected session. Raises on serial failure so the caller can reconnect."""
    port = port or find_arduino_port()
    print(f"using serial port {port}", flush=True)

    ser = serial.Serial(port=port, baudrate=BAUD, timeout=1, write_timeout=1)

    def _send(cmd: str):
        ser.reset_input_buffer()          # discard Arduino's unread "-> Moving..." replies
        ser.write(cmd.encode() + b"\n")
        ser.flush()

    last = None
    last_sent = 0.0
    last_seen = time.monotonic()

    try:
        await asyncio.sleep(BOOT_DELAY)

        while not stop.is_set():
            # Get newest detections (drop stale frames)
            dets = None
            try:
                dets = await asyncio.wait_for(dets_q.get(), timeout=0.2)
                while not dets_q.empty():
                    dets = dets_q.get_nowait()
            except asyncio.TimeoutError:
                pass

            # Decide command
            command = None
            if dets is not None:
                person = largest_person(dets)
                if person is not None:
                    command = COMMANDS.get(person.get("zone"))
                    if command is not None:
                        last_seen = time.monotonic()

            now = time.monotonic()
            if command is None:
                if now - last_seen > LOST_TIMEOUT:
                    command = IDLE_CMD
                else:
                    continue  # brief dropout: keep current command running

            # Send on change, or as a heartbeat
            changed = command != last
            stale = HEARTBEAT and (now - last_sent) > HEARTBEAT
            if changed or stale:
                await asyncio.to_thread(_send, command)
                last_sent = now

            if changed:
                print(NAMES.get(command, command), flush=True)
                last = command
    finally:
        try:
            _send(IDLE_CMD)  # leave the car stopped (best effort)
        except Exception:
            pass
        try:
            ser.close()
        except Exception:
            pass


async def track_human(dets_q, stop, port=None):
    while not stop.is_set():
        try:
            await _run(dets_q, stop, port)
        except (serial.SerialException, OSError, RuntimeError) as e:
            print(f"serial problem: {e}; retrying in {RECONNECT_DELAY}s", flush=True)
            try:
                await asyncio.wait_for(stop.wait(), timeout=RECONNECT_DELAY)
            except asyncio.TimeoutError:
                pass
