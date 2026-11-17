# MLM2PRO → GSPro Connector

Connect a **Rapsodo MLM2PRO** launch monitor directly to your PC over Bluetooth
LE and feed shots straight into **GSPro** via its OpenConnect API — **no Rapsodo
phone app in the loop during play, and no manual daily re-authentication.**

It runs as a lightweight background service: it waits for GSPro, finds your
monitor, fetches a fresh session token automatically each time, arms the device,
and forwards every shot to GSPro. Auto-reconnects if the monitor sleeps.

> **Interoperability tool for people who own the hardware and the software.**
> Not affiliated with, endorsed by, or supported by Rapsodo or GSPro. See
> [CREDITS.md](CREDITS.md) for trademarks and attribution.

---

## Features

- **Direct BLE → GSPro** — talks to the MLM2PRO over Bluetooth, decodes shots,
  sends them to GSPro OpenConnect (`127.0.0.1:921`).
- **Automatic token refresh** — no more daily reauth dance; it gets a session
  token the same way the official app does, every run.
- **Resilient service mode** — one persistent GSPro connection, auto-reconnect to
  the monitor, rotating log file. Designed to run hidden at logon and just work.
- **One-file executable** — build a single `.exe`; end users don't need Python.
- **Windows auto-start** — per-user, no admin required.

## Requirements

- Windows 10/11 with Bluetooth.
- A Rapsodo MLM2PRO.
- GSPro with the OpenConnect API enabled.
- A Rapsodo **third-party** subscription, authorized once (see below).

## One-time setup (required)

In the **Rapsodo phone app**: `Play → Third Party → authorize a third-party slot`
(e.g. "Awesome Golf"). This binds your account to the device so it will issue
session tokens. You only redo this if that authorization lapses. After this, you
don't need the phone app day to day.

> **Why one cloud call remains:** the MLM2PRO firmware requires a valid
> Rapsodo-issued session token to arm. This tool fetches that token for you
> automatically instead of making you re-auth by hand — it can't be removed
> without new device firmware.

## Quick start (one-click setup)

1. Pair the MLM2PRO in Windows Bluetooth settings (pick the `MLM2-<serial>` entry).
2. Double-click **`Configure.bat`**. A small window opens — pick your club, optionally
   **Scan** for your monitor, and click **Save & Start now**. You can also tick
   "Start automatically at Windows login".
3. Start GSPro and open its OpenConnect API. Done.

The setup window writes a `config.json` next to the program; the connector reads it
on every launch, so you never touch the command line. Re-run `Configure.bat` any time
to change your club or device.

## Install & run (manual)

### Option A — one-file executable (easiest)

1. Download `mlm2pro-gspro-connector.exe` from the
   [Releases](https://github.com/adamkoehler1990/mlm2pro-gspro-connector/releases)
   page (or build it: `powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1`).
2. Pair the MLM2PRO in Windows Bluetooth settings (pick the `MLM2-<serial>` entry).
3. Start GSPro and open its OpenConnect API.
4. Run it:

```bash
mlm2pro-gspro-connector.exe --service --club 7i
```

### Option B — from source

```bash
pip install -r requirements.txt
python mlm2pro_bridge.py --service --club 7i
```

(Requires Python 3.10+.)

### Options

```bash
--service                 resilient background mode (recommended)
--address AA:BB:...       connect to a specific monitor, skip the scan
--club 7i                 set the reported club (PT = putter, shots ignored)
--gspro-port 921          GSPro OpenConnect port
--log PATH                log file location (service mode)
--retry 8                 seconds between reconnect attempts
```

### config.json

Instead of flags you can drop a `config.json` next to the program (this is what
`Configure.bat` writes). See [`config.example.json`](config.example.json):

```json
{
  "club": "7i",
  "address": null,
  "gspro_host": "127.0.0.1",
  "gspro_port": 921,
  "retry": 8
}
```

Command-line flags override `config.json` when both are present.

## Run automatically at Windows logon (hidden)

```bash
powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1
```

Drops a hidden-launch shortcut in your per-user **Startup folder** (no admin). It
prefers the built `.exe` if present, otherwise uses Python. Edit `$Club` in the
script to change your default club. Remove with `scripts\uninstall_autostart.ps1`.

**Check it's alive:** open `mlm2pro_bridge.log`.

## How it works

1. Connects to the MLM2PRO over BLE.
2. Runs the auth handshake → the device returns a user id.
3. Fetches a session token from Rapsodo's web API for that id.
4. Writes the encrypted initial parameters (incl. the token) and arms the device.
5. Decodes each shot (AES-256-CBC) and sends it to GSPro OpenConnect.

## Troubleshooting

- **GSPro shows "not ready" but the connector is running** — GSPro's indicator
  typically clears when it receives the first real shot. If the log shows
  `202 GSPro ready`, the pipeline is connected; just hit a ball.
- **Connector connects but no ball flies / no response on 921** — GSPro Connect is
  single-connection and doesn't clean up old sockets. Quit and relaunch GSPro to
  clear port 921, then start the connector **once** and leave it running. Don't
  run two clients against 921 at the same time.
- **Shot misreads** — 20 zero bytes from the device = a misread; it's ignored.

## Contributing

Issues and PRs welcome. Because this builds on GPL-3.0 upstream work, the project
is GPL-3.0; contributions are accepted under the same license.

## License

**GPL-3.0** — see [LICENSE](LICENSE). Portions derived from
[springbok/MLM2PRO-GSPro-Connector](https://github.com/springbok/MLM2PRO-GSPro-Connector)
(GPL-3.0) and [Duwaynef/MLM2PRO-BT-APP](https://github.com/Duwaynef/MLM2PRO-BT-APP)
(MIT). Full attribution in [CREDITS.md](CREDITS.md).
