import asyncio


COMMANDS = {
    "left": "turn left",
    "center": "forward",
    "right": "turn right",
}


def _area(box):
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def largest_person(dets):
    people = [d for d in dets if d.get("label") == "person"]
    if not people:
        return None
    return max(people, key=lambda d: _area(d["box"]))


async def track_human(dets_q, stop):
    last = None
    while not stop.is_set():
        try:
            dets = await asyncio.wait_for(dets_q.get(), timeout=0.2)
        except asyncio.TimeoutError:
            continue

        person = largest_person(dets)
        if person is None:
            continue

        command = COMMANDS.get(person["zone"])
        if command is None:
            continue
        if command != last:
            print(command, flush=True)
            last = command
