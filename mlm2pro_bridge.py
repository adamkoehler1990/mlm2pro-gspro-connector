#!/usr/bin/env python3
#
# MLM2PRO -> GSPro Connector
# Copyright (C) 2026 Adam Koehler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Portions of the MLM2PRO BLE protocol and the GSPro OpenConnect message
# handling in this file are derived from springbok/MLM2PRO-GSPro-Connector
# (GPL-3.0) and Duwaynef/MLM2PRO-BT-APP (MIT). See CREDITS.md.
"""
mlm2pro_bridge.py  -  Standalone Rapsodo MLM2PRO -> GSPro OpenConnect bridge.

Connects to an MLM2PRO over Bluetooth LE directly from this PC, performs the
auth handshake, fetches the per-session token from Rapsodo's web API, arms the
device, decodes shots, and forwards them to GSPro's OpenConnect API (TCP/JSON,
port 921). No Rapsodo phone app needed during play.

Protocol ported from the open-source springbok/MLM2PRO-GSPro-Connector and
Duwaynef/MLM2PRO-BT-APP projects, verified against the Rapsodo MLM2PRO APK.

ONE-TIME PREREQUISITE (unavoidable):
  In the Rapsodo phone app: Play -> Third Party -> authorize a third-party slot
  (e.g. "Awesome Golf"). Requires a Rapsodo third-party subscription. This binds
  your account to the device so it will issue session tokens. Re-authorize only
  if that slot lapses. After this, you do not need the phone app day to day.

DEPENDENCIES:
  pip install bleak cryptography

USAGE:
  1) Start GSPro and open its OpenConnect API (it listens on 127.0.0.1:921).
  2) Power on the MLM2PRO, wait for solid red.
  3) python mlm2pro_bridge.py            (scans for a device named MLM2-...)
     or: python mlm2pro_bridge.py --address AA:BB:CC:DD:EE:FF
     set club with --club 7i  (use PT for putter -> shots ignored)

NOTE: BLE auth/arm/token fetch and the GSPro OpenConnect path are verified
working against real hardware. If a step misbehaves on your setup, the per-step
hex logging below is designed to let you compare against the reference projects.
See README.md.
"""

import argparse
import asyncio
import json
import math
import os
import struct
import sys
import urllib.request
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("Missing dependency. Run:  pip install bleak cryptography")
    sys.exit(1)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Rapsodo web API (recovered from the app / connectors). The device returns a
# userId during auth; we GET {WEB_API_URL}{userId} with the Secret header and
# receive {success, user:{id, token, expireDate}}.
WEB_API_URL = "https://mlm.rapsodo.com/api/simulator/user/"
WEB_API_SECRET = "d3d4baff-02c7-4c91-8100-2e362936e06e"   # Rapsodo app "Secret" header

GSPRO_HOST = "127.0.0.1"
GSPRO_PORT = 921
GSPRO_DEVICE_ID = "MLM2PRO-Bridge"
GSPRO_UNITS = "Yards"
GSPRO_API_VERSION = "1"

TEMPERATURE_CELSIUS = 15.0      # sent in the initial-parameters write
ALTITUDE_METRES = 0.0           # reference connector always sends 0.0 here

DEVICE_NAME_PREFIX = "MLM2-"    # Windows pairs the monitor as "MLM2-<serial>"

HEARTBEAT_SECONDS = 2.0         # keepalive written to the heartbeat char while armed

# BLE GATT (service DAF9B2A4-... with 7 characteristics)
SERVICE_UUID       = "daf9b2a4-e4db-4be4-816d-298a050f25cd"
AUTH_UUID          = "b1e9ce5b-48c8-4a28-89dd-12ffd779f5e1"
COMMAND_UUID       = "1ea0fa51-1649-4603-9c5f-59c940323471"
CONFIGURE_UUID     = "df5990cf-47fb-4115-8fdd-40061d40af84"
EVENTS_UUID        = "02e525fd-7960-4ef0-bfb7-de0f514518ff"
HEARTBEAT_UUID     = "ef6a028e-f78b-47a4-b56c-dda6dae85cbf"
MEASUREMENT_UUID   = "76830bce-b9a7-4f69-aeaa-fd5b9f6b0965"
WRITE_RESPONSE_UUID= "cfbbcb0d-7121-4bc2-bf54-8284166d61f0"

# AES-256-CBC key + IV used for ALL encrypted BLE payloads (command/configure/
# events/measurement). The key is also sent to the device in the auth write.
AES_KEY = bytes([26, 24, 1, 38, 249, 154, 60, 63, 149, 185, 205, 150, 126, 160,
                 38, 61, 89, 199, 68, 140, 255, 21, 250, 131, 55, 165, 121, 250,
                 49, 121, 233, 21])
AES_IV = bytes([109, 46, 82, 19, 33, 50, 4, 69, 111, 44, 121, 72, 16, 101, 109, 66])

# Launch-monitor event codes (first byte of a decrypted EVENTS payload)
EVT_SHOT, EVT_PROCESSING, EVT_READY, EVT_BATTERY, EVT_MISREAD_OR_DISARMED = 0, 1, 2, 3, 5

MISREAD_SHOT = bytes(20)  # 20 zero bytes = misread marker


# --------------------------------------------------------------------------- #
# Crypto helpers
# --------------------------------------------------------------------------- #

def aes_encrypt(data: bytes) -> bytes:
    padder = PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    enc = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV)).encryptor()
    return enc.update(padded) + enc.finalize()


def aes_decrypt(data: bytes) -> bytes | None:
    try:
        dec = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV)).decryptor()
        padded = dec.update(data) + dec.finalize()
        unpadder = PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()
    except Exception as ex:
        print(f"[crypto] decrypt error: {ex}")
        return None


# --------------------------------------------------------------------------- #
# Byte builders (ported from BluetoothUtils)
# --------------------------------------------------------------------------- #

def air_pressure_bytes(d: float) -> bytes:
    d2 = d * 0.0065
    value = int(((math.pow(1.0 - (d2 / ((15.0 + d2) + 273.15)), 5.257) * 1013.25)
                 * 0.1 - 50.0) * 1000.0)
    return struct.pack("<H", value & 0xFFFF)


def temperature_bytes(d: float) -> bytes:
    return struct.pack("<H", int(d * 100.0) & 0xFFFF)


def build_auth_payload() -> bytes:
    prefix = struct.pack("<I", 1)        # int 1, little-endian -> 01 00 00 00
    enc_type = bytes([0, 1])             # encryption type
    return prefix + enc_type + AES_KEY   # 4 + 2 + 32 = 38 bytes


def build_initial_params(token: int) -> bytes:
    return (bytes([1, 2, 0, 0])
            + air_pressure_bytes(ALTITUDE_METRES)
            + temperature_bytes(TEMPERATURE_CELSIUS)
            + struct.pack("<Q", int(token))     # token as uint64 LE
            + bytes([0, 0]))


def hx(b: bytes) -> str:
    return b.hex().upper()


# --------------------------------------------------------------------------- #
# Config file (config.json next to the program) - edited by configure.py
# --------------------------------------------------------------------------- #

def _program_dir() -> str:
    # Works for both the .py and the PyInstaller one-file .exe.
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def load_config() -> dict:
    """Read config.json (club, address, gspro_host, gspro_port, retry) if present.
    Returns {} when missing or unreadable. CLI flags always override these."""
    path = os.path.join(_program_dir(), "config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as ex:
        print(f"[config] could not read config.json: {ex}")
        return {}


# --------------------------------------------------------------------------- #
# Rapsodo web API
# --------------------------------------------------------------------------- #

def fetch_token(user_id: int) -> dict | None:
    url = WEB_API_URL + str(user_id)
    req = urllib.request.Request(url, headers={"Secret": WEB_API_SECRET})
    print(f"[api] GET {url}  (Secret header set)")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
    except Exception as ex:
        print(f"[api] request failed: {ex}")
        return None
    try:
        data = json.loads(body)
    except Exception as ex:
        print(f"[api] bad JSON: {ex}  raw={body!r}")
        return None
    user = data.get("user") or data.get("User") or {}
    out = {
        "token": user.get("token", user.get("Token")),
        "expireDate": user.get("expireDate", user.get("ExpireDate")),
        "id": user.get("id", user.get("Id")),
    }
    if out["token"] is None:
        print(f"[api] no token in response: {body!r}")
        return None
    return out


# --------------------------------------------------------------------------- #
# GSPro OpenConnect client
# --------------------------------------------------------------------------- #

class GSProClient:
    def __init__(self, host: str, port: int):
        self.host, self.port = host, port
        self.reader = self.writer = None
        self.shot_number = 1
        self._lock = asyncio.Lock()
        self._hb_task = None
        self._reader_task = None
        self.alive = False

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.alive = True
        print(f"[gspro] connected to {self.host}:{self.port}")
        # One background reader drains ALL responses (GSPro glues them together
        # and sends unsolicited 201/202 messages). Writes never block on reads.
        self._reader_task = asyncio.create_task(self._reader_loop())
        # Heartbeats are optional (GSPro ignores them / does not reply) but keep
        # traffic flowing; they are fire-and-forget so a shot is never delayed.
        self._hb_task = asyncio.create_task(self._heartbeat_loop())

    async def _reader_loop(self):
        buf = ""
        decoder = json.JSONDecoder()
        while True:
            try:
                chunk = await self.reader.read(4096)
            except Exception:
                self.alive = False
                return
            if not chunk:
                print("[gspro] connection closed by GSPro")
                self.alive = False
                return
            buf += chunk.decode("utf-8", "replace").strip()
            # GSPro may concatenate several JSON objects with no separator.
            while buf:
                buf = buf.lstrip()
                try:
                    obj, idx = decoder.raw_decode(buf)
                except ValueError:
                    break  # incomplete; wait for more bytes
                buf = buf[idx:]
                code = obj.get("Code")
                msg = obj.get("Message", "")
                player = obj.get("Player")
                if code == 201 and player:
                    print(f"[gspro] <- 201 player: club={player.get('Club')} "
                          f"hand={player.get('Handed')} dist={player.get('DistanceToTarget')}")
                else:
                    print(f"[gspro] <- {code} {msg}")

    async def _send(self, payload: dict):
        raw = json.dumps(payload).encode("utf-8")
        async with self._lock:
            self.writer.write(raw)
            await self.writer.drain()

    async def _heartbeat_loop(self):
        payload = {
            "DeviceID": GSPRO_DEVICE_ID,
            "Units": GSPRO_UNITS,
            "ShotNumber": 0,
            "APIversion": GSPRO_API_VERSION,
            "ShotDataOptions": {
                "ContainsBallData": False,
                "ContainsClubData": False,
                "LaunchMonitorIsReady": True,
                "LaunchMonitorBallDetected": False,
                "IsHeartBeat": True,
            },
        }
        while True:
            try:
                await self._send(payload)
            except Exception as ex:
                print(f"[gspro] heartbeat failed: {ex}")
                return
            await asyncio.sleep(1.0)

    async def send_shot(self, ball: dict):
        payload = {
            "DeviceID": GSPRO_DEVICE_ID,
            "Units": GSPRO_UNITS,
            "ShotNumber": self.shot_number,
            "APIversion": GSPRO_API_VERSION,
            "BallData": {
                "Speed": ball["speed"],
                "SpinAxis": ball["spin_axis"],
                "TotalSpin": ball["total_spin"],
                "HLA": ball["hla"],
                "VLA": ball["vla"],
                "Backspin": ball["back_spin"],
                "SideSpin": ball["side_spin"],
                "CarryDistance": 0,
            },
            "ClubData": {
                "Speed": ball["club_speed"],
                "AngleOfAttack": 0,
                "FaceToTarget": 0,
                "Lie": 0, "Loft": 0, "Path": 0,
                "SpeedAtImpact": ball["club_speed"],
                "VerticalFaceImpact": 0, "HorizontalFaceImpact": 0, "ClosureRate": 0,
            },
            "ShotDataOptions": {
                "ContainsBallData": True,
                "ContainsClubData": True,
                "LaunchMonitorIsReady": True,
                "LaunchMonitorBallDetected": True,
                "IsHeartBeat": False,
            },
        }
        print(f"[gspro] -> shot #{self.shot_number}: {payload['BallData']}")
        await self._send(payload)
        self.shot_number += 1

    async def close(self):
        for t in (self._hb_task, self._reader_task):
            if t:
                t.cancel()
        if self.writer:
            self.writer.close()


# --------------------------------------------------------------------------- #
# Shot decoding (ported from BallData.from_mlm2pro_bt)
# --------------------------------------------------------------------------- #

def decode_shot(data: bytes) -> dict | None:
    if data[:20] == MISREAD_SHOT:
        print("[shot] misread (all zero), ignoring")
        return None
    mult = 2.2375  # device units -> mph
    club_speed = round(int.from_bytes(data[0:2], "little") / 10.0 * mult, 2)
    speed = round(int.from_bytes(data[2:4], "little") / 10.0 * mult, 2)
    hla = struct.unpack("<h", data[4:6])[0] / 10.0
    vla = struct.unpack("<h", data[6:8])[0] / 10.0
    spin_axis = struct.unpack("<h", data[8:10])[0] / 10.0
    total_spin = int.from_bytes(data[10:12], "little")
    back_spin = round(total_spin * math.cos(math.radians(spin_axis)))
    side_spin = round(total_spin * math.sin(math.radians(spin_axis)))
    return {
        "club_speed": club_speed, "speed": speed, "hla": hla, "vla": vla,
        "spin_axis": spin_axis, "total_spin": total_spin,
        "back_spin": back_spin, "side_spin": side_spin,
    }


# --------------------------------------------------------------------------- #
# Main device driver
# --------------------------------------------------------------------------- #

class MLM2PROBridge:
    def __init__(self, client: BleakClient, gspro: GSProClient, club: str):
        self.client = client
        self.gspro = gspro
        self.club = club.upper()
        self.armed = False
        self.connected_evt = asyncio.Event()
        self.loop = asyncio.get_event_loop()
        self._hb_task = None

    async def write(self, uuid: str, data: bytes, label: str, response: bool = True):
        print(f"[ble] -> {label}: {hx(data)}")
        await self.client.write_gatt_char(uuid, data, response=response)

    async def start(self):
        # Subscribe to the four notification characteristics.
        await self.client.start_notify(WRITE_RESPONSE_UUID, self._on_write_response)
        await self.client.start_notify(EVENTS_UUID, self._on_events)
        await self.client.start_notify(MEASUREMENT_UUID, self._on_measurement)
        await self.client.start_notify(HEARTBEAT_UUID, self._on_heartbeat)
        print("[ble] notifications subscribed")
        await asyncio.sleep(1.0)          # reference waits ~1s before auth
        await self.write(AUTH_UUID, build_auth_payload(), "AUTH")

    # --- notification handlers (sync; schedule async work on the loop) ------- #
    def _on_write_response(self, _char, data: bytearray):
        data = bytes(data)
        print(f"[ble] <- WRITE_RESPONSE: {hx(data)}  ints={list(data)}")
        asyncio.run_coroutine_threadsafe(self._handle_write_response(data), self.loop)

    def _on_heartbeat(self, _char, _data):
        pass  # device heartbeat notification; nothing to do

    def _on_events(self, _char, data: bytearray):
        dec = aes_decrypt(bytes(data))
        if not dec:
            return
        code = dec[0]
        names = {EVT_SHOT: "SHOT READ", EVT_PROCESSING: "PROCESSING SHOT",
                 EVT_READY: "READY", EVT_BATTERY: "BATTERY",
                 EVT_MISREAD_OR_DISARMED: "MISREAD/DISARMED"}
        if code == EVT_BATTERY:
            print(f"[evt] battery: {dec[1]}%")
        elif code == EVT_MISREAD_OR_DISARMED:
            print("[evt] misread" if dec[1] == 0 else "[evt] DISARMED")
            if dec[1] == 1:
                self.armed = False
        else:
            print(f"[evt] {names.get(code, f'unknown({code})')}")

    def _on_measurement(self, _char, data: bytearray):
        if not self.armed:
            return
        if self.club == "PT":
            print("[shot] putter selected, ignoring")
            return
        dec = aes_decrypt(bytes(data))
        if not dec:
            return
        print(f"[shot] measurement decrypted: {hx(dec)}")
        ball = decode_shot(dec)
        if ball:
            asyncio.run_coroutine_threadsafe(self.gspro.send_shot(ball), self.loop)

    # --- write-response state machine ---------------------------------------- #
    async def _handle_write_response(self, data: bytes):
        if len(data) < 2:
            return
        if len(data) > 2:
            if data[0] == 2:  # needs initial params
                if data[1] != 0 or len(data) < 4:
                    if data[1] == 1:
                        print("[auth] FAILED: third-party authorization expired. "
                              "Re-authorize in the Rapsodo app.")
                    else:
                        print(f"[auth] FAILED: code {data[1]}")
                    return
                print("[auth] success, sending initial params")
                await self._send_initial_params(data)
            elif data[0] == 0:
                print("[auth] connected")
                await self._on_connected()
            elif data[0] == 1:
                print("[ble] write acknowledged (arm/command OK)")
            else:
                print(f"[auth] unexpected write response: {list(data)}")
        else:
            print("[auth] connected (no initial params required)")
            await self._on_connected()

    async def _send_initial_params(self, data: bytes):
        user_id = int.from_bytes(data[2:6], "little")
        print(f"[auth] device userId = {user_id}")
        tok = await asyncio.get_event_loop().run_in_executor(None, fetch_token, user_id)
        if not tok:
            print("[auth] could not obtain token; aborting")
            return
        exp = tok["expireDate"]
        try:
            when = datetime.fromtimestamp(float(exp), tz=timezone.utc).astimezone()
            print(f"[auth] token acquired, expires {when:%Y-%m-%d %H:%M:%S}")
        except Exception:
            print(f"[auth] token acquired, expireDate={exp}")
        params = build_initial_params(tok["token"])
        print(f"[auth] initial params (plain): {hx(params)}")
        await self.write(CONFIGURE_UUID, aes_encrypt(params), "CONFIGURE")
        await self._on_connected()

    async def _on_connected(self):
        if self.connected_evt.is_set():
            return
        self.connected_evt.set()
        await asyncio.sleep(0.5)
        await self._arm()
        self._hb_task = asyncio.create_task(self._heartbeat_loop())

    async def _arm(self):
        await self.write(COMMAND_UUID, aes_encrypt(bytes.fromhex("010D0001000000")), "ARM")
        self.armed = True
        print("[ble] device ARMED - ready to read shots")

    async def _heartbeat_loop(self):
        while self.client.is_connected:
            if self.armed:
                try:
                    await self.client.write_gatt_char(HEARTBEAT_UUID, bytes([0x01]),
                                                       response=False)
                except Exception as ex:
                    print(f"[hb] write failed: {ex}")
            await asyncio.sleep(HEARTBEAT_SECONDS)


# --------------------------------------------------------------------------- #

async def find_device(address: str | None):
    if address:
        print(f"[ble] connecting to {address}")
        return address
    print(f"[ble] scanning for a device named '{DEVICE_NAME_PREFIX}...' (10s)")
    devices = await BleakScanner.discover(timeout=10.0)
    for d in devices:
        if d.name and d.name.startswith(DEVICE_NAME_PREFIX):
            print(f"[ble] found {d.name}  [{d.address}]")
            return d.address
    print("[ble] no MLM2PRO found. Pair it in Windows first, or pass --address.")
    for d in devices:
        if d.name:
            print(f"        seen: {d.name}  [{d.address}]")
    return None


async def run_session(args):
    """One full attempt: connect GSPro, connect the monitor, run until a drop.
    Raises on any failure so the service loop can retry."""
    gspro = GSProClient(args.gspro_host, args.gspro_port)
    await gspro.connect()                       # raises if GSPro/OpenConnect is down
    try:
        address = await find_device(args.address)
        if not address:
            raise RuntimeError("MLM2PRO not found on this scan")
        print("[ble] connecting...")
        async with BleakClient(address) as client:
            if not client.is_connected:
                raise RuntimeError("BLE connect failed")
            print("[ble] connected")
            bridge = MLM2PROBridge(client, gspro, args.club)
            await bridge.start()
            print("\nBridge running.\n")
            while client.is_connected and gspro.alive:
                await asyncio.sleep(1)
            print("[ble] link lost (monitor slept/out of range, or GSPro closed)")
    finally:
        await gspro.close()


async def service_loop(args):
    """Resilient forever-loop for unattended / auto-start operation.

    Holds a SINGLE GSPro connection across many BLE reconnects. GSPro Connect
    does not clean up disconnects, so we must not repeatedly connect/disconnect
    it (that jams port 921). We only (re)connect GSPro when it is actually down,
    and otherwise just re-scan/reconnect the monitor underneath it.
    """
    print(f"[service] resilient bridge started (retry every {args.retry}s)")
    gspro = GSProClient(args.gspro_host, args.gspro_port)
    try:
        while True:
            # 1) Ensure GSPro is connected (cheap socket; no BLE scan if it's down).
            if not gspro.alive:
                try:
                    await gspro.connect()
                except Exception:
                    await asyncio.sleep(args.retry)   # GSPro not up yet; wait
                    continue

            # 2) GSPro up: find and run the monitor until it (or GSPro) drops.
            try:
                address = await find_device(args.address)
                if not address:
                    await asyncio.sleep(args.retry)
                    continue
                print("[ble] connecting...")
                async with BleakClient(address) as client:
                    if not client.is_connected:
                        raise RuntimeError("BLE connect failed")
                    print("[ble] connected")
                    bridge = MLM2PROBridge(client, gspro, args.club)
                    await bridge.start()
                    print("\nBridge running.\n")
                    while client.is_connected and gspro.alive:
                        await asyncio.sleep(1)
                    print("[ble] link lost (monitor slept/out of range, or GSPro closed)")
            except asyncio.CancelledError:
                raise
            except Exception as ex:
                print(f"[service] monitor session ended: {ex}")
            await asyncio.sleep(args.retry)
    finally:
        await gspro.close()


class _LogStream:
    """Minimal rotating, timestamped log stream used in --service mode so the
    hidden process leaves a readable trail without extra dependencies."""
    def __init__(self, path: str, max_bytes: int = 1_000_000):
        self.path, self.max = path, max_bytes
        self._at_line_start = True
        self.f = open(path, "a", encoding="utf-8", buffering=1)

    def write(self, s: str):
        if not s:
            return 0
        for part in s.splitlines(keepends=True):
            if self._at_line_start and part.strip():
                self.f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {part}")
            else:
                self.f.write(part)
            self._at_line_start = part.endswith("\n")
        try:
            if self.f.tell() > self.max:
                self.f.close()
                bak = self.path + ".1"
                try:
                    if os.path.exists(bak):
                        os.remove(bak)
                    os.replace(self.path, bak)
                except OSError:
                    pass
                self.f = open(self.path, "a", encoding="utf-8", buffering=1)
        except Exception:
            pass
        return len(s)

    def flush(self):
        try:
            self.f.flush()
        except Exception:
            pass


async def main():
    cfg = load_config()
    ap = argparse.ArgumentParser(description="MLM2PRO -> GSPro bridge")
    ap.add_argument("--address", default=cfg.get("address"),
                    help="BLE MAC address of the MLM2PRO")
    ap.add_argument("--club", default=cfg.get("club", "7i"),
                    help="current club (PT=putter, ignored)")
    ap.add_argument("--gspro-host", default=cfg.get("gspro_host", GSPRO_HOST))
    ap.add_argument("--gspro-port", type=int, default=cfg.get("gspro_port", GSPRO_PORT))
    ap.add_argument("--service", action="store_true",
                    help="resilient unattended mode (retry/reconnect forever)")
    ap.add_argument("--retry", type=int, default=cfg.get("retry", 8),
                    help="seconds between retries in --service mode")
    ap.add_argument("--log", default=None, help="log file path (--service mode)")
    args = ap.parse_args()

    if args.service:
        log_path = args.log or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "mlm2pro_bridge.log")
        stream = _LogStream(log_path)
        sys.stdout = sys.stderr = stream
        print("=" * 60)
        print("[service] launched")
        await service_loop(args)
    else:
        try:
            await run_session(args)
        except Exception as ex:
            print(f"[error] {ex}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[exit] stopped")
