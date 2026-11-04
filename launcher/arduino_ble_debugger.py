#!/usr/bin/env python3
"""BLE transport for the Kotlin Arduino debugger; reads angles from stdin."""
import asyncio
import sys

from bleak import BleakClient, BleakScanner

NAME = "UNO-R4-Servo"
SERVICE = "19B10000-E8F2-537E-4F6C-D104768A1214"
ANGLE = "19B10001-E8F2-537E-4F6C-D104768A1214"


async def main():
    print(f"Scanning for {NAME} (up to 15 seconds)...", flush=True)
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name == NAME or ad.local_name == NAME,
        timeout=15.0, service_uuids=[SERVICE],
    )
    if device is None:
        raise RuntimeError(f"{NAME} not found; check board power and the uploaded sketch")
    async with BleakClient(device) as client:
        print("Connected. Enter a command to move the servo.", flush=True)
        while client.is_connected:
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                break
            angle = int(line.strip())
            if not 0 <= angle <= 180:
                raise ValueError("Angle must be between 0 and 180")
            await client.write_gatt_char(ANGLE, str(angle).encode("ascii"), response=True)
            print(f"Sent {angle} degrees.", flush=True)
        if not client.is_connected:
            raise RuntimeError("Arduino disconnected")
    print("Disconnected; the servo holds its last position.", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"BLE error: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
