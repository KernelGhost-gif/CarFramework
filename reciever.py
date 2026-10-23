import cv2
import socket
import numpy as np

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)  # bigger buffer for bursts
sock.bind(("0.0.0.0", 5005))

try:
    while True:
        data, addr = sock.recvfrom(65535)
        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            print("Decode failed")
            continue

        cv2.imshow("UDP video", frame) # remove this if you want to use it as an api, will rewuire heavy mods
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    sock.close()
    cv2.destroyAllWindows()
