# Credits & attribution

This tool stands on the reverse-engineering work of the MLM2PRO community. The
Bluetooth LE protocol for the Rapsodo MLM2PRO (the auth handshake, the AES
parameters, the arm/heartbeat sequence, and the shot-data byte layout) and the
GSPro OpenConnect message format were **not** originated here — they were worked
out by the projects below, and portions of this code are derived from them.

## Upstream projects

- **[springbok/MLM2PRO-GSPro-Connector](https://github.com/springbok/MLM2PRO-GSPro-Connector)**
  — License: **GPL-3.0**.
  The MLM2PRO BLE device protocol and GSPro OpenConnect handling are derived from
  this project. Because it is GPL-3.0, this repository is also released under
  **GPL-3.0** (see `LICENSE`).

- **[Duwaynef/MLM2PRO-BT-APP](https://github.com/Duwaynef/MLM2PRO-BT-APP)**
  — License: **MIT**.
  Additional protocol details (byte builders, shot decoding) were cross-checked
  against this project. MIT-licensed material is included under terms compatible
  with GPL-3.0.

## What is original here

- A single-file, dependency-light Python bridge (`mlm2pro_bridge.py`).
- A resilient `--service` mode that holds one persistent GSPro connection,
  auto-reconnects to the monitor, and logs with rotation.
- Hardened GSPro OpenConnect client (background reader that splits glued JSON
  responses, non-blocking sends, fire-and-forget heartbeats).
- Windows per-user auto-start (Startup-folder, no admin) and a PyInstaller build
  for a one-file executable.

## Credentials / endpoints

The Rapsodo `Secret` GUID, AES key/IV, and web-API endpoint used here are
Rapsodo's own values, already published by the community projects above. They are
included so the tool can obtain a per-session token the way the official app
does. If Rapsodo rotates them, update the constants at the top of
`mlm2pro_bridge.py`.

## Trademarks

"Rapsodo" and "MLM2PRO" are trademarks of Rapsodo Inc. "GSPro" is a trademark of
its respective owner. This project is **not affiliated with, endorsed by, or
supported by** Rapsodo or GSPro. It is an independent interoperability tool for
owners of the hardware and software.
