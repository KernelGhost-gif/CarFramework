#!/usr/bin/env python3
"""Send the DualSense left-stick X position to the UNO R4 WiFi servo."""

import asyncio
import sys

import pygame
from bleak import BleakClient, BleakScanner

DEVICE_NAME = "UNO-R4-Servo"
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
ANGLE_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
DEAD_ZONE = 0.08
SEND_INTERVAL = 0.04
ANGLE_STEP = 2


def find_controller():
    pygame.init()
    pygame.joystick.init()
    while pygame.joystick.get_count() == 0:
        pygame.event.pump()
        print("Waiting for a controller. Pair/connect the DualSense to this Mac...")
        pygame.time.wait(1000)

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    if joystick.get_numaxes() < 1:
        raise RuntimeError("The controller does not expose joystick axis 0.")
    print(f"Controller: {joystick.get_name()} (using left-stick horizontal axis 0)")
    return joystick


async def find_board():
    print(f"Scanning for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, advertisement: (
            d.name == DEVICE_NAME or DEVICE_NAME in (advertisement.local_name or "")
        ),
        timeout=15.0,
        service_uuids=[SERVICE_UUID],
    )
    if device is None:
        raise RuntimeError("UNO-R4-Servo not found. Check power and the uploaded sketch.")
    return device


async def main() -> None:
    joystick = find_controller()
    device = await find_board()
    print("Connecting to the UNO. Move the left stick horizontally; Ctrl+C quits.")

    async with BleakClient(device) as client:
        last_sent = -ANGLE_STEP
        loop = asyncio.get_running_loop()
        try:
            while True:
                pygame.event.pump()
                if not joystick.get_init():
                    raise RuntimeError("Controller disconnected.")

                x = max(-1.0, min(1.0, joystick.get_axis(0)))
                if abs(x) < DEAD_ZONE:
                    x = 0.0
                angle = round((x + 1.0) * 90.0)
                if abs(angle - last_sent) >= ANGLE_STEP:
                    await client.write_gatt_char(
                        ANGLE_UUID, str(angle).encode("ascii"), response=True
                    )
                    last_sent = angle
                    print(f"\rstick {x:+.2f} -> servo {angle:3d}°", end="", flush=True)
                await asyncio.sleep(SEND_INTERVAL)
        finally:
            pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as exc:
        print(f"Controller/BLE error: {exc}", file=sys.stderr)
        raise
