import asyncio
from pathlib import Path

import cv2
from sender import compress_send
from trackhuman import track_human


async def capture(q, stop):
    cap = cv2.VideoCapture(0)
    try:
        while not stop.is_set():
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                print("Failed to grab frame")
                break
            if q.full():
                q.get_nowait()
            q.put_nowait(frame)
    finally:
        cap.release()
        if q.full():
            q.get_nowait()
        q.put_nowait(None)

async def main():
    q = asyncio.Queue(maxsize=1)
    dets_q = asyncio.Queue(maxsize=1)
    stop = asyncio.Event()
    project_root = Path(__file__).resolve().parent.parent
    ai_enabled = not (project_root / "noai").is_file()
    print("AI tracking enabled" if ai_enabled else "AI tracking disabled (noai file present)")
    tasks = [capture(q, stop), compress_send(q, dets_q, stop, ai_enabled=ai_enabled)]
    if ai_enabled:
        tasks.append(track_human(dets_q, stop))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
