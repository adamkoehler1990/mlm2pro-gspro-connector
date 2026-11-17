#!/usr/bin/env python3
"""
gspro_test_shot.py - Send a synthetic shot to GSPro OpenConnect (no monitor).

Use this to confirm GSPro accepts the shot format and that the "not ready" box
clears, without needing to swing. STOP the main bridge first (Ctrl+C) - GSPro
only accepts one connector connection at a time.

    python gspro_test_shot.py
"""

import asyncio
import json

HOST, PORT = "127.0.0.1", 921
DEVICE_ID = "MLM2PRO-Bridge"
UNITS = "Yards"
APIV = "1"

# A plausible 7-iron strike.
SHOT = {
    "speed": 115.0, "spin_axis": -3.0, "total_spin": 6200,
    "hla": 1.0, "vla": 18.0, "back_spin": 6190, "side_spin": -324,
    "club_speed": 83.0,
}

def heartbeat():
    return {
        "DeviceID": DEVICE_ID, "Units": UNITS, "ShotNumber": 0, "APIversion": APIV,
        "ShotDataOptions": {
            "ContainsBallData": False, "ContainsClubData": False,
            "LaunchMonitorIsReady": True, "LaunchMonitorBallDetected": False,
            "IsHeartBeat": True,
        },
    }

def shot(n):
    return {
        "DeviceID": DEVICE_ID, "Units": UNITS, "ShotNumber": n, "APIversion": APIV,
        "BallData": {
            "Speed": SHOT["speed"], "SpinAxis": SHOT["spin_axis"],
            "TotalSpin": SHOT["total_spin"], "HLA": SHOT["hla"], "VLA": SHOT["vla"],
            "Backspin": SHOT["back_spin"], "SideSpin": SHOT["side_spin"],
            "CarryDistance": 0,
        },
        "ClubData": {
            "Speed": SHOT["club_speed"], "AngleOfAttack": 0, "FaceToTarget": 0,
            "Lie": 0, "Loft": 0, "Path": 0, "SpeedAtImpact": SHOT["club_speed"],
            "VerticalFaceImpact": 0, "HorizontalFaceImpact": 0, "ClosureRate": 0,
        },
        "ShotDataOptions": {
            "ContainsBallData": True, "ContainsClubData": True,
            "LaunchMonitorIsReady": True, "LaunchMonitorBallDetected": True,
            "IsHeartBeat": False,
        },
    }


async def send(writer, reader, payload, label):
    writer.write(json.dumps(payload).encode("utf-8"))
    await writer.drain()
    try:
        resp = await asyncio.wait_for(reader.read(2048), timeout=3)
        print(f"[{label}] <- {resp.decode('utf-8', 'replace').strip()}")
    except asyncio.TimeoutError:
        print(f"[{label}] (no response within 3s)")


async def main():
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except Exception as ex:
        print(f"connect failed: {ex}  (is GSPro running and the bridge stopped?)")
        return
    print(f"connected to {HOST}:{PORT}")

    # warm up with heartbeats so GSPro marks us ready
    for _ in range(3):
        await send(writer, reader, heartbeat(), "hb")
        await asyncio.sleep(1)

    print(">>> sending synthetic shot")
    await send(writer, reader, shot(1), "shot")

    # keep heartbeating a few more seconds so GSPro stays happy / ball plays out
    for _ in range(5):
        await send(writer, reader, heartbeat(), "hb")
        await asyncio.sleep(1)

    writer.close()
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
