#!/usr/bin/env python3
#
# MLM2PRO -> GSPro Connector
# Copyright (C) 2026 Adam Koehler
# Licensed under GPL-3.0 (see LICENSE).
"""
configure.py - One-click setup GUI for the MLM2PRO -> GSPro connector.

Double-click Configure.bat (or run `python configure.py`) and fill in a couple
of fields. It writes config.json next to the program, and can install the hidden
auto-start shortcut for you. No command line needed.

Nothing here contacts any server - it only writes a local config.json.
"""

import json
import os
import subprocess
import sys
import threading

import tkinter as tk
from tkinter import messagebox, ttk

CLUBS = ["DR", "3w", "5w", "4i", "5i", "6i", "7i", "8i", "9i", "PW", "GW", "SW", "LW", "PT"]
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")


def load_existing() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


class App:
    def __init__(self, root):
        self.root = root
        root.title("MLM2PRO -> GSPro Connector - Setup")
        root.resizable(False, False)
        cfg = load_existing()

        pad = {"padx": 10, "pady": 6}
        frm = ttk.Frame(root, padding=16)
        frm.grid()

        row = 0
        ttk.Label(frm, text="MLM2PRO -> GSPro Connector", font=("Segoe UI", 13, "bold")).grid(
            column=0, row=row, columnspan=3, sticky="w")
        row += 1
        ttk.Label(frm, text="Fill these in, then click Save. That's it.",
                  foreground="#555").grid(column=0, row=row, columnspan=3, sticky="w", pady=(0, 10))

        # Club
        row += 1
        ttk.Label(frm, text="Default club:").grid(column=0, row=row, sticky="e", **pad)
        self.club = ttk.Combobox(frm, values=CLUBS, width=8, state="readonly")
        self.club.set(cfg.get("club", "7i"))
        self.club.grid(column=1, row=row, sticky="w", **pad)
        ttk.Label(frm, text="(PT = putter: shots ignored)", foreground="#777").grid(
            column=2, row=row, sticky="w")

        # Device address
        row += 1
        ttk.Label(frm, text="Monitor address:").grid(column=0, row=row, sticky="e", **pad)
        self.address = ttk.Entry(frm, width=26)
        self.address.insert(0, cfg.get("address") or "")
        self.address.grid(column=1, row=row, sticky="w", **pad)
        self.scan_btn = ttk.Button(frm, text="Scan...", command=self.scan)
        self.scan_btn.grid(column=2, row=row, sticky="w")
        row += 1
        ttk.Label(frm, text="Leave blank to auto-find a device named MLM2-...",
                  foreground="#777").grid(column=1, row=row, columnspan=2, sticky="w")

        # GSPro port
        row += 1
        ttk.Label(frm, text="GSPro port:").grid(column=0, row=row, sticky="e", **pad)
        self.port = ttk.Entry(frm, width=10)
        self.port.insert(0, str(cfg.get("gspro_port", 921)))
        self.port.grid(column=1, row=row, sticky="w", **pad)
        ttk.Label(frm, text="(default 921)", foreground="#777").grid(column=2, row=row, sticky="w")

        # Auto-start checkbox
        row += 1
        self.autostart = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Start automatically at Windows login (hidden)",
                        variable=self.autostart).grid(column=0, row=row, columnspan=3,
                                                       sticky="w", padx=10, pady=(10, 2))

        # One-time reminder
        row += 1
        box = tk.Text(frm, width=58, height=4, wrap="word", relief="solid", borderwidth=1)
        box.insert("1.0",
                   "One-time (required): in the Rapsodo phone app, go to "
                   "Play > Third Party and authorize a third-party slot (e.g. "
                   "\"Awesome Golf\"). This lets the monitor issue session tokens. "
                   "You only do this once.")
        box.configure(state="disabled", background="#fffceb")
        box.grid(column=0, row=row, columnspan=3, padx=10, pady=10)

        # Buttons
        row += 1
        btns = ttk.Frame(frm)
        btns.grid(column=0, row=row, columnspan=3, pady=(6, 0))
        ttk.Button(btns, text="Save", command=self.save).grid(column=0, row=0, padx=6)
        ttk.Button(btns, text="Save & Start now", command=self.save_and_start).grid(
            column=1, row=0, padx=6)
        ttk.Button(btns, text="Close", command=root.destroy).grid(column=2, row=0, padx=6)

        self.status = ttk.Label(frm, text="", foreground="#070")
        row += 1
        self.status.grid(column=0, row=row, columnspan=3, sticky="w", pady=(10, 0))

    # --- actions ---------------------------------------------------------- #
    def _collect(self) -> dict:
        try:
            port = int(self.port.get().strip() or "921")
        except ValueError:
            messagebox.showerror("Invalid port", "GSPro port must be a number.")
            return None
        return {
            "club": self.club.get().strip() or "7i",
            "address": self.address.get().strip() or None,
            "gspro_host": "127.0.0.1",
            "gspro_port": port,
            "retry": 8,
        }

    def save(self, start=False):
        cfg = self._collect()
        if cfg is None:
            return False
        save_config(cfg)
        msg = f"Saved to {CONFIG_PATH}"
        if self.autostart.get():
            ok, detail = self.install_autostart()
            msg += "\n" + detail
        self.status.configure(text="Saved.")
        if not start:
            messagebox.showinfo("Saved", msg)
        return True

    def save_and_start(self):
        if self.save(start=True):
            self.start_now()

    def install_autostart(self):
        ps1 = os.path.join(HERE, "scripts", "install_autostart.ps1")
        if not os.path.exists(ps1):
            return False, "install_autostart.ps1 not found; skipped auto-start."
        try:
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps1],
                check=True, capture_output=True, text=True)
            return True, "Auto-start installed (runs hidden at login)."
        except Exception as ex:
            return False, f"Auto-start step failed: {ex}"

    def _runner(self):
        """Path + args to launch the connector (compiled exe if present, else python)."""
        exe = os.path.join(HERE, "dist", "mlm2pro-gspro-connector.exe")
        club = self.club.get().strip() or "7i"
        if os.path.exists(exe):
            return [exe, "--service", "--club", club]
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        runner = pyw if os.path.exists(pyw) else sys.executable
        return [runner, os.path.join(HERE, "mlm2pro_bridge.py"), "--service", "--club", club]

    def start_now(self):
        try:
            subprocess.Popen(self._runner(), cwd=HERE)
            self.status.configure(text="Connector started (running hidden in the background).")
        except Exception as ex:
            messagebox.showerror("Could not start", str(ex))

    def scan(self):
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status.configure(text="Scanning for MLM2-... (10s)")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        found = None
        try:
            import asyncio
            from bleak import BleakScanner

            async def go():
                devs = await BleakScanner.discover(timeout=10.0)
                for d in devs:
                    if d.name and d.name.startswith("MLM2-"):
                        return d.address
                return None

            found = asyncio.run(go())
        except Excepv–öâ2Wƒ ¢6VÆbç&ö÷BægFW"ƒÂÆÖ&F¢ÖW76vV&÷‚ç6†÷vW'&÷"€¢%66âf–ÆVB"Âb'¶W‡ÕÆåÆä–ç7FÆÂFW2f—'7C¢—–ç7FÆÂ&ÆV²"’¢6VÆbç&ö÷BægFW"ƒÂÆÖ&F¢6VÆbå÷66åöFöæR†f÷VæB’ ¢FVb÷66åöFöæR‡6VÆbÂFG&W72“ ¢6VÆbç66åö'Fâæ6öæf–wW&R‡7FFSÒ&æ÷&ÖÂ"ÂFW‡CÒ%66ââââ"¢–bFG&W73 ¢6VÆbæFG&W72æFVÆWFRƒÂ&VæB"¢6VÆbæFG&W72æ–ç6W'BƒÂFG&W72¢6VÆbç7FGW2æ6öæf–wW&R‡FW‡CÖb$f÷VæBÖöæ—F÷#¢¶FG&W77Ò"¢VÇ6S ¢6VÆbç7FGW2æ6öæf–wW&R‡FW‡CÒ$æòÔÄÓ"ÒFWf–6Rf÷VæBâ—"—B–âv–æF÷w2&ÇVWFö÷F‚f—'7Bâ"  ¦FVbÖ–â‚“ ¢&ö÷BÒF²åF²‚¢‡&ö÷B¢&ö÷BæÖ–æÆö÷‚  ¦–bõöæÖUõòÓÒ%õöÖ–åõò# ¢Ö–â‚ 