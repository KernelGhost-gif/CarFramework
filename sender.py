import asyncio
import socket
import cv2
from mpipe import Analyser

DEST = ("192.168.68.57", 5005)
PARAMS = [cv2.IMWRITE_AVIF_QUALITY, 50]

analyser = Analyser()

def encode(frame):
    ok, buf = cv2.imencode('.avif', frame, PARAMS)
    return buf.tobytes() if ok else None

async def compress_send(q, stop):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        while not stop.is_set():
            frame = await q.get()
            result = await analyser(frame)
            if result is None:
                break
            data = await asyncio.to_thread(encode, result)
            if data is None:
                print("Encode failed")
                continue
            sock.sendto(data, DEST)
    finally:
        sock.close()
