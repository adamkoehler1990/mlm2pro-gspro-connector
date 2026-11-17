# MLM2PRO â†’ GSPro Connector

Connect a **Rapsodo MLM2PRO** launch monitor directly to your PC over Bluetooth
LE and feed shots straight into **GSPro** via its OpenConnect API â€” **no Rapsodo
phone app in the loop during play, and no manual daily re-authentication.**

It runs as a lightweight background service: it waits for GSPro, finds your
monitor, fetches a fresh session token automatically each time, arms the device,
and forwards every shot to GSPro. Auto-reconnects if the monitor sleeps.

> **Interoperability tool for people who own the hardware and the software.**
> Not affiliated with, endorsed by, or supported by Rapsodo or GSPro. See
> [CREDITS.md](CREDITS.md) for trademarks and attribution.

---

## Features

- **Direct BLE â†’ GSPro** â€” talks to the MLM2PRO over Bluetooth, decodes shots,
  sends them to GSPro OpenConnect (`127.0.0.1:921`).
- **Automatic token refresh** â€” no more daily reauth dance; it gets a session
  token the same way the official app does, every run.
- **Resilient service mode** â€” one persistent GSPro connection, auto-reconnect to
  the monitor, rotating log file. Designed to run hidden at logon and just work.
- **One-file executable** â€” build a single `.exe`; end users don't need Python.
- **Windows auto-start** â€” per-user, no admin required.

## Requirements

- Windows 10/11 with Bluetooth.
- A Rapsodo MLM2PRO.
- GSPro with the OpenConnect API enabled.
- A Rapsodo **third-party** subscription, authorized once (see below).

## One-time setup (required)

In the **Rapsodo phone app**: `Play â†’ Third Party â†’ authorize a third-party slot`
(e.g. "Awesome Golf"). This binds your account to the device so it will issue
session tokens. You only redo this if that authorization lapses. After this, you
don't need the phone app day to day.

> **Why one cloud call remains:** the MLM2PRO firmware requires a valid
> Rapsodo-issued session token to arm. This tool fetches that token for you
> automatically instead of making you re-auth by hand â€” it can't be removed
> without new device firmware.

## Quick start (one-click setup)

1. Pair the MLM2PRO in Windows Bluetooth settings (pick the `MLM2-<serial>` entry).
2. Double-click **`Configure.bat`**. A small window opens â€” pick your club, optionally
   **Scan** for your monitor, and click **Save & Start now**. You can also tick
   "Start automatically at Windows login".
3. Start GSPro and open its OpenConnect API. Done.

The setup window writes a `config.json` next to the program; the connector reads it
on every launch, so you never touch the command line. Re-run `Configure.bat` any time
to change your club or device.

## Install & run (manual)

### Option A â€” one-file executable (easiest)

1. Download `mlm2pro-gspro-connector.exe` from the
   [Releases](https://github.com/adamkoehler1990/mlm2pro-gspro-connector/releases)
   page (or build it: `powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1`).
2. Pair the MLM2PRO in Windows Bluetooth settings (pick the `MLM2-<serial>` entry).
3. Start GSPro and open its OpenConnect API.
4. Run it:

```bash
mlm2pro-gspro-connector.exe --service --club 7i
```

### Option B â€” from source

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

L›ÜÈHY[‹[][˜ÚÚÜİ][ˆ[İ\ˆ\‹]\Ù\ˆ
Š”İ\\›Û\ŠŠˆ
›ÈYZ[ŠKˆ]œ™Y™\œÈHZ[™^XYˆ™\Ù[İ\Ú\ÙH\Ù\È]Û‹ˆY]	ÛX˜[ˆBœØÜš\ÈÚ[™ÙH[İ\ˆY˜][ÛX‹ˆ™[[İ™HÚ]ØÜš\×[š[œİ[Ø]]Üİ\œÌX‚‚ŠŠÚXÚÈ]	ÜÈ[]™NŠŠˆÜ[ˆ[Lœ›×ØœšYÙK›ÙØ‚‚ˆÈÈİÈ]ÛÜšÜÂ‚ŒKˆÛÛ›™XİÈÈHSL”“Èİ™\ˆ“K‚Œ‹ˆ[œÈH]][™ÚZÙH8¡¤ˆH]šXÙH™]\›œÈH\Ù\ˆY‚ŒËˆ™]Ú\ÈHÙ\ÜÚ[ÛˆÚÙ[ˆœ›ÛH˜\ÛÙÉÜÈÙXˆTH›Üˆ]Y‚ˆÜš]\ÈH[˜Ü\Y[š]X[\˜[Y]\œÈ
[˜ÛˆHÚÙ[ŠH[™\›\ÈH]šXÙK‚KˆXÛÙ\ÈXXÚÚİ
QTËLM‹PĞÊH[™Ù[™È]ÈÔÔ›ÈÜ[ÛÛ›™Xİ‚‚ˆÈÈ›İX›\ÚÛİ[™Â‚‹H
Š‘ÔÔ›ÈÚİÜÈ››İ™XYHˆ]HÛÛ›™XİÜˆ\È[›š[™ÊŠˆ8 %ÔÔ›ÉÜÈ[™XØ]Ü‚ˆ\XØ[HÛX\œÈÚ[ˆ]™XÙZ]™\ÈHš\œİ™X[ÚİˆYˆHÙÈÚİÜÂˆŒˆÔÔ›È™XYXH\[[™H\ÈÛÛ›™XİYÈ\İ]H˜[‚‹H
ŠÛÛ›™XİÜˆÛÛ›™XİÈ]›È˜[›Y\ÈÈ›È™\ÜÛœÙHÛˆLŒJŠˆ8 %ÔÔ›ÈÛÛ›™Xİ\ÂˆÚ[™ÛKXÛÛ›™Xİ[Ûˆ[™Ù\Û‰İÛX[ˆ\ÛÛØÚÙ]Ëˆ]Z][™™[][˜ÚÔÔ›ÈÂˆÛX\ˆÜLŒK[ˆİ\HÛÛ›™XİÜˆ
Š›Û˜ÙJŠˆ[™X]™H][›š[™ËˆÛ‰İˆ[ˆÛÈÛY[ÈYØZ[œİLŒH]HØ[YH[YK‚‹H
Š”ÚİZ\Ü™XYÊŠˆ8 %Œ™\›È]\Èœ›ÛHH]šXÙHHHZ\Ü™XYÈ]	ÜÈYÛ›Ü™Y‚‚ˆÈÈÛÛšX][™Â‚’\ÜİY\È[™œÈÙ[ÛÛYKˆ™XØ]\ÙH\ÈZ[ÈÛˆÔLËŒ\İ™X[HÛÜšËH›Ú™Xİš\ÈÔLËŒÈÛÛšX][ÛœÈ\™HXØÙ\Y[™\ˆHØ[YHXÙ[œÙK‚‚ˆÈÈXÙ[œÙB‚ŠŠ‘ÔLËŒ
Šˆ8 %ÙYHÓPÑS”ÑWJPÑS”ÑJKˆÜ[ÛœÈ\š]™Yœ›ÛB–ÜÜš[™Ø›ÚËÓSL”“ËQÔÔ›ËPÛÛ›™XİÜ—JÎ‹ËÙÚ]X‹˜ÛÛKÜÜš[™Ø›ÚËÓSL”“ËQÔÔ›ËPÛÛ›™XİÜŠBŠÔLËŒ
H[™Ñ]Ø^[™Y‹ÓSL”“ËP•PTJÎ‹ËÙÚ]X‹˜ÛÛKÑ]Ø^[™Y‹ÓSL”“ËP•PT
BŠRU
Kˆ[]šX][Ûˆ[ˆĞÔ‘QUË›YJÔ‘QUË›Y
K‚