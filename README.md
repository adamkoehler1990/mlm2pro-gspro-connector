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

Instead of flags you can l›ÜHÛÛ™šYËšœÛÛ˜™^ÈH›ÙÜ˜[H
\È\ÈÚ]˜ÛÛ™šYİ\™K˜˜]Üš]\ÊKˆÙYHØÛÛ™šYË™^[\KšœÛÛ˜JÛÛ™šYË™^[\KšœÛÛŠN‚‚˜œÛÛ‚Âˆ˜ÛXˆˆÚH‹ˆ˜Y™\ÜÈˆ[ˆ™ÜÜ›×ÚÜİˆŒLËŒŒŒH‹ˆ™ÜÜ›×ÜÜˆLŒKˆœ™]HˆŸB˜‚ÛÛ[X[™[[™H›YÜÈİ™\œšYHÛÛ™šYËšœÛÛ˜Ú[ˆ›İ\™H™\Ù[‚‚ˆÈÈ[ˆ]]ÛX]XØ[H]Ú[™İÜÈÙÛÛˆ
Y[ŠB‚˜˜\ÚœİÙ\œÚ[Q^Xİ][Û”ÛXŞH\\ÜÈQš[HØÜš\×[œİ[Ø]]Üİ\œÌB˜‚“&÷2†–FFVâÖÆVæ6‚6†÷'F7WB–â–÷W"W"×W6W"¢¥7F'GWföÆFW"¢¢†æòFÖ–â’â—@§&VfW'2F†R'V–ÇBæW†V–b&W6VçBÂ÷F†W'v—6RW6W2—F†öââVF—BD6ÇV&–âF†P§67&—BFò6†ævR–÷W"FVfVÇB6ÇV"â&VÖ÷fRv—F‚67&—G5ÇVæ–ç7FÆÅöWF÷7F'Bç3à ¢¢¤6†V6²—Bw2Æ—fS¢¢¢÷VâÖÆÓ'&õö'&–FvRæÆövà ¢22†÷r—Bv÷&·0 £â6öææV7G2FòF†RÔÄÓ%$ò÷fW"$ÄRà£"â'Vç2F†RWF‚†æG6†¶R(i"F†RFWf–6R&WGW&ç2W6W"–Bà£2âfWF6†W26W76–öâFö¶Vâg&öÒ&6öFòw2vV"’f÷"F†B–Bà£Bâw&—FW2F†RVæ7'—FVB–æ—F–Â&ÖWFW'2†–æ6ÂâF†RFö¶Vâ’æB&×2F†RFWf–6Rà£RâFV6öFW2V6‚6†÷B„U2Ó#SbÔ4$2’æB6VæG2—BFòu5&ò÷Vä6öææV7Bà ¢22G&÷V&ÆW6†ö÷F–æp ¢Ò¢¤u5&ò6†÷w2&æ÷B&VG’"'WBF†R6öææV7F÷"—2'Vææ–ær¢¢(	Bu5&òw2–æF–6F÷ ¢G—–6ÆÇ’6ÆV'2v†Vâ—B&V6V—fW2F†Rf—'7B&VÂ6†÷Bâ–bF†RÆör6†÷w0¢#"u5&ò&VG–ÂF†R—VÆ–æR—26öææV7FVC²§W7B†—B&ÆÂà¢Ò¢¤6öææV7F÷"6öææV7G2'WBæò&ÆÂfÆ–W2òæò&W7öç6Röâ“#¢¢(	Bu5&ò6öææV7B—0¢6–ævÆRÖ6öææV7F–öâæBFöW6âwB6ÆVâWöÆB6ö6¶WG2âV—BæB&VÆVæ6‚u5&òFğ¢6ÆV"÷'B“#ÂF†Vâ7F'BF†R6öææV7F÷"¢¦öæ6R¢¢æBÆVfR—B'Vææ–ærâFöâw@¢'VâGvò6Æ–VçG2v–ç7B“#BF†R6ÖRF–ÖRà¢Ò¢¥6†÷BÖ—7&VG2¢¢(	B#¦W&ò'—FW2g&öÒF†RFWf–6RÒÖ—7&VC²—Bw2–væ÷&VBà ¢226öçG&–'WF–æp ¤—77VW2æB'2vVÆ6öÖRâ&V6W6RF†—2'V–ÆG2öâuÂÓ2ãW7G&VÒv÷&²ÂF†R&ö¦V7@¦—2uÂÓ2ã²6öçG&–'WF–öç2&R66WFVBVæFW"F†R6ÖRÆ–6Vç6Rà ¢22Æ–6Vç6P ¢¢¤uÂÓ2ã¢¢(	B6VR´Ä”4Tå4UÒ„Ä”4Tå4R’â÷'F–öç2•É¥Ù•™É½´)mÍÁÉ¥¹‰½¬½514ÉAI<µMAÉ¼µ½¹¹•Ñ½Ét¡¡ÑÑÁÌè¼½¥Ñ¡Õˆ¹½´½ÍÁÉ¥¹‰½¬½514ÉAI<µMAÉ¼µ½¹¹•Ñ½È¤(¡A0´Ì¸À¤…¹mÕİ…å¹•˜½514ÉAI<µ	PµAAt¡¡ÑÑÁÌè¼½¥Ñ¡Õˆ¹½´½Õİ…å¹•˜½514ÉAI<µ	PµA@¤(¡5%P¤¸Õ±°…ÑÑÉ¥‰ÕÑ¥½¸¥¸mI%QL¹µ‘t¡I%QL¹µ¤¸(