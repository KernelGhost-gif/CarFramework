import asyncio
import socket
import time

COMMANDS = {"left": "l", "center": "f", "right": "r"}
IDLE_CMD = "s"
NAMES = {"l": "turn left", "f": "forward", "r": "turn right", "s": "stop"}

CAR_ADDR = ("192.168.68.50", 4210)   # the Uno's IP and port
LOST_TIMEOUT = 0.5
HEARTBEAT = 0.5


def _area(box):
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def largest_person(dets):
    people = [d for d in dets if d.get("label") == "person"]
    return max(people, key=lambda d: _area(d["box"])) if people else None


async def track_human(dets_q, stop, addr=CAR_ADDR):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)

    def _send(cmd: str):
        try:
            sock.sendto(cmd.encode(), addr)
        except OSError as e:
            print(f"send failed: {e}", flush=True)

    last, last_sent = None, 0.0
    last_seen = time.monotonic()

    try:
        while not stop.is_set():
            dets = None
            try:
                dets = await asyncio.wait_for(dets_q.get(), timeout=0.2)
                while not dets_q.empty():
                    dets = dets_q.get_nowait()
            except asyncio.TimeoutError:
                pass

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
                    continue

            changed = command != last
            if changed or (now - last_sent) > HEARTBEAT:
                _send(command)
                last_sent = now
            if changed:
                print(NAMES.get(command, command), flush=True)
                last = command
    finally:
        _send(IDLE_CMD)
        sock.close()
