import sys
import os
import threading
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..core.exploit import ExploitManager, ExploitStage
from ..core.device import find_pwned_device, find_devices, DeviceInfo
from ..core.board import find_mass_storage_devices, get_firmware_path, flash_firmware
from ..utils import log

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


COLORS = {
    "bg": "#0d1117",
    "fg": "#161b22",
    "card": "#1c2333",
    "border": "#30363d",
    "accent": "#1f6feb",
    "accent_hover": "#388bfd",
    "success": "#3fb950",
    "error": "#f85149",
    "warning": "#d29922",
    "info": "#58a6ff",
    "text": "#e6edf3",
    "text_dim": "#8b949e",
    "text_bright": "#f0f6fc",
}

PADDING = {"x": 16, "y": 12}
FONT = ("SF Mono", "Segoe UI", "Helvetica Neue", "Consolas")


def _build_record(level, message):
    return logging.LogRecord("usbliter8", level.value, "", 0, message, (), None)


class GUILogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.tag_styles = {
            logging.DEBUG: (" dim", COLORS["text_dim"]),
            logging.INFO: ("", COLORS["text"]),
            logging.WARNING: (" warn", COLORS["warning"]),
            logging.ERROR: (" err", COLORS["error"]),
        }

    def emit(self, record):
        try:
            self.text_widget.after(0, self._append, record)
        except:
            pass

    def _append(self, record):
        try:
            suffix, color = self.tag_styles.get(record.levelno, ("", COLORS["text"]))
            tag = f"log_{record.levelno}_{id(self)}"
            msg = f"{record.msg}\n"
            self.text_widget.tag_config(tag, foreground=color)
            self.text_widget.insert("end", msg, tag)
            self.text_widget.see("end")
        except:
            pass


def _gui_log_callback(level, message):
    record = _build_record(level, message)
    for h in logging.getLogger().handlers:
        if isinstance(h, GUILogHandler):
            h.emit(record)


class ExploitGUI:
    def __init__(self):
        if not CTK_AVAILABLE:
            print("customtkinter not installed. Run: pip install customtkinter")
            sys.exit(1)

        self.root = ctk.CTk()
        self.root.title("stalinra1n")
        self.root.geometry("960x680")
        self.root.minsize(800, 600)

        self.mgr = ExploitManager()
        self._exploit_thread: Optional[threading.Thread] = None
        self._monitor_active = True

        self._build_ui()
        self._setup_logging()

        log.set_gui_callback(_gui_log_callback)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_monitor()

    def _build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        side = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)
        side.configure(fg_color=COLORS["fg"])

        icon_frame = ctk.CTkFrame(side, fg_color="transparent")
        icon_frame.pack(pady=(30, 10))

        logo = ctk.CTkLabel(
            icon_frame,
            text="\u2b22",
            font=("Helvetica", 36, "bold"),
            text_color=COLORS["info"],
        )
        logo.pack()

        title = ctk.CTkLabel(
            icon_frame,
            text="usbliter8",
            font=("Helvetica", 18, "bold"),
            text_color=COLORS["text_bright"],
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            icon_frame,
            text="Payload Injector",
            font=("Helvetica", 11),
            text_color=COLORS["text_dim"],
        )
        subtitle.pack(pady=(0, 6))

        ver = ctk.CTkLabel(
            icon_frame,
            text="v1.0.0",
            font=("Helvetica", 10),
            text_color=COLORS["text_dim"],
        )
        ver.pack()

        sep = ctk.CTkFrame(side, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=16, pady=16)

        nav_frame = ctk.CTkFrame(side, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=4)

        sections = [
            ("\u25b6  Exploit", self._show_exploit),
            ("\u2699  Settings", self._show_settings),
            ("\u2139  About", self._show_about),
        ]

        self._nav_buttons = []
        for text, cmd in sections:
            btn = ctk.CTkButton(
                nav_frame,
                text=text,
                command=cmd,
                anchor="w",
                fg_color="transparent",
                text_color=COLORS["text_dim"],
                hover_color=COLORS["card"],
                font=(FONT, 13),
                height=36,
            )
            btn.pack(fill="x", pady=1)
            self._nav_buttons.append(btn)

        self._nav_buttons[0].configure(text_color=COLORS["text_bright"], fg_color=COLORS["card"])

        sep2 = ctk.CTkFrame(side, height=1, fg_color=COLORS["border"])
        sep2.pack(fill="x", padx=16, pady=16)

        credit = ctk.CTkLabel(
            side,
            text="Based on usbliter8\nby Paradigm Shift",
            font=("Helvetica", 9),
            text_color=COLORS["text_dim"],
            justify="left",
        )
        credit.pack(side="bottom", pady=16, padx=16)

    def _build_main(self):
        main = ctk.CTkFrame(self.root, fg_color=COLORS["bg"])
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=0)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(2, weight=0)

        self._build_status_bar(main)
        self._build_content(main)

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, height=32, fg_color=COLORS["fg"])
        footer.grid(row=2, column=0, sticky="ew")
        self.footer_label = ctk.CTkLabel(
            footer,
            text="stalinra1n v1.0.0 | Based on Paradigm Shift research",
            font=(FONT, 10), text_color=COLORS["text_dim"],
        )
        self.footer_label.pack(pady=4)

    def _build_status_bar(self, parent):
        bar = ctk.CTkFrame(parent, height=48, fg_color=COLORS["fg"])
        bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.status_device = ctk.CTkLabel(
            bar,
            text="Device: \u25cf Not detected",
            font=(FONT, 12),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        self.status_device.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        self.status_board = ctk.CTkLabel(
            bar,
            text="Board: \u25cf Not detected",
            font=(FONT, 12),
            text_color=COLORS["text_dim"],
            anchor="center",
        )
        self.status_board.grid(row=0, column=1, padx=16, pady=8)

        self.status_exploit = ctk.CTkLabel(
            bar,
            text="Exploit: \u25cf Idle",
            font=(FONT, 12),
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        self.status_exploit.grid(row=0, column=2, padx=16, pady=8, sticky="e")

    def _build_content(self, parent):
        self.content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self._show_exploit()

    def _show_exploit(self):
        self._clear_content()
        self._highlight_nav(0)

        frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="usbliter8 BootROM Exploit",
            font=(FONT, 20, "bold"),
            text_color=COLORS["text_bright"],
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 20))

        row = 1

        board_card = self._card(frame, "RP2350 Board", row, 0)
        board_card.grid_columnconfigure(1, weight=1)
        self.board_label = ctk.CTkLabel(
            board_card, text="No board detected",
            font=(FONT, 12), text_color=COLORS["text_dim"],
        )
        self.board_label.grid(row=0, column=0, padx=12, pady=8, sticky="w")

        self.btn_flash = ctk.CTkButton(
            board_card, text="Flash Firmware",
            command=self._on_flash,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
            width=140,
        )
        self.btn_flash.grid(row=0, column=1, padx=12, pady=8, sticky="e")
        row += 1

        dfu_card = self._card(frame, "DFU Mode", row, 0)
        dfu_card.grid_columnconfigure(1, weight=1)
        dfu_btn_frame = ctk.CTkFrame(dfu_card, fg_color="transparent")
        dfu_btn_frame.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        self.btn_dfu_guide = ctk.CTkButton(
            dfu_btn_frame, text="Show DFU Guide",
            command=self._show_dfu_guide_dialog,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
        )
        self.btn_dfu_guide.pack(side="left", padx=(0, 8))

        self.btn_check_dfu = ctk.CTkButton(
            dfu_btn_frame, text="Detect DFU",
            command=self._on_check_dfu,
            fg_color=COLORS["card"], hover_color=COLORS["border"],
            font=(FONT, 12),
        )
        self.btn_check_dfu.pack(side="left")

        self.dfu_label = ctk.CTkLabel(
            dfu_card, text="Not in DFU mode",
            font=(FONT, 12), text_color=COLORS["text_dim"],
        )
        self.dfu_label.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        row += 1

        exploit_card = self._card(frame, "Exploit", row, 0)
        exploit_card.grid_columnconfigure(1, weight=1)

        self.btn_exploit = ctk.CTkButton(
            exploit_card, text="\u25b6  Run Exploit",
            command=self._on_exploit,
            fg_color=COLORS["success"], hover_color="#2ea043",
            font=(FONT, 14, "bold"),
            height=44,
            width=200,
        )
        self.btn_exploit.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        self.exploit_label = ctk.CTkLabel(
            exploit_card, text="Ready",
            font=(FONT, 12), text_color=COLORS["text_dim"],
        )
        self.exploit_label.grid(row=0, column=0, padx=12, pady=8, sticky="w")

        self.progress = ctk.CTkProgressBar(
            exploit_card, height=6,
            fg_color=COLORS["card"], progress_color=COLORS["info"],
        )
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        self.progress.set(0)
        row += 1

        post_card = self._card(frame, "Post-Exploitation", row, 0)
        post_card.grid_columnconfigure(1, weight=1)
        post_btn_frame = ctk.CTkFrame(post_card, fg_color="transparent")
        post_btn_frame.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        self.btn_demote = ctk.CTkButton(
            post_btn_frame, text="Demote",
            command=self._on_demote,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
            state="disabled",
        )
        self.btn_demote.pack(side="left", padx=(0, 6))

        self.btn_boot = ctk.CTkButton(
            post_btn_frame, text="Boot iBoot",
            command=self._on_boot,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
            state="disabled",
        )
        self.btn_boot.pack(side="left", padx=(0, 6))

        self.btn_loader = ctk.CTkButton(
            post_btn_frame, text="Install Loader",
            command=self._on_install_loader,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
            state="disabled",
        )
        self.btn_loader.pack(side="left")

        self.post_label = ctk.CTkLabel(
            post_card, text="Run exploit first",
            font=(FONT, 12), text_color=COLORS["text_dim"],
        )
        self.post_label.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        row += 1

        log_card = self._card(frame, "Console Output", row, 0)
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_card,
            font=(FONT, 11),
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            wrap="word",
            height=180,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self.proxy_label = ctk.CTkLabel(
            log_card,
            text="(Using system_profiler / lsusb for device detection)",
            font=(FONT, 9), text_color=COLORS["text_dim"],
        )
        self.proxy_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 8))

    def _show_settings(self):
        self._clear_content()
        self._highlight_nav(1)

        frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="Settings",
            font=(FONT, 20, "bold"),
            text_color=COLORS["text_bright"],
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        gen_card = self._card(frame, "General", 1, 0)
        gen_card.grid_columnconfigure(1, weight=1)

        row = 0
        for cfg_key, cfg_label, cfg_default, cfg_type in [
            ("dfu_timeout", "DFU detection timeout (seconds)", 60, int),
            ("exploit_timeout", "Exploit wait timeout (seconds)", 30, int),
            ("reconnect_timeout", "Reconnect timeout (seconds)", 30, int),
            ("auto_flash", "Auto-flash board before exploit", True, bool),
            ("auto_detect_dfu", "Auto-detect DFU mode", True, bool),
            ("firmware_dir", "Custom firmware directory", "", str),
        ]:
            lbl = ctk.CTkLabel(
                gen_card, text=cfg_label,
                font=(FONT, 12), text_color=COLORS["text"],
                anchor="w",
            )
            lbl.grid(row=row, column=0, padx=12, pady=6, sticky="w")

            if cfg_type == bool:
                var = ctk.BooleanVar(value=cfg_default)
                cb = ctk.CTkCheckBox(
                    gen_card, text="", variable=var,
                    fg_color=COLORS["accent"],
                )
                cb.grid(row=row, column=1, padx=12, pady=6, sticky="e")
                setattr(self, f"_setting_{cfg_key}", var)
            elif cfg_type == int:
                var = ctk.StringVar(value=str(cfg_default))
                entry = ctk.CTkEntry(
                    gen_card, textvariable=var,
                    font=(FONT, 12), width=100,
                    fg_color=COLORS["bg"], border_color=COLORS["border"],
                )
                entry.grid(row=row, column=1, padx=12, pady=6, sticky="e")
                setattr(self, f"_setting_{cfg_key}", var)
            else:
                var = ctk.StringVar(value=cfg_default)
                entry = ctk.CTkEntry(
                    gen_card, textvariable=var,
                    font=(FONT, 12), width=200,
                    fg_color=COLORS["bg"], border_color=COLORS["border"],
                )
                entry.grid(row=row, column=1, padx=12, pady=6, sticky="e")
                setattr(self, f"_setting_{cfg_key}", var)
            row += 1

        dev_card = self._card(frame, "Device-Side Loader", 2, 0)
        dev_card.grid_columnconfigure(1, weight=1)

        self.btn_build_loader = ctk.CTkButton(
            dev_card, text="Build Loader App",
            command=self._on_build_loader,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
        )
        self.btn_build_loader.grid(row=0, column=0, padx=12, pady=8, sticky="w")

        self.btn_build_bootstrap = ctk.CTkButton(
            dev_card, text="Build Bootstrap",
            command=self._on_build_bootstrap,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=(FONT, 12, "bold"),
        )
        self.btn_build_bootstrap.grid(row=0, column=1, padx=12, pady=8, sticky="e")

    def _show_about(self):
        self._clear_content()
        self._highlight_nav(2)

        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        about_text = (
            "stalinra1n v1.0.0\n\n"
            "A payload injection and jailbreak tool for the usbliter8\n"
            "SecureROM exploit targeting Apple A12 and A13 devices.\n\n"
            "Based on usbliter8 by Paradigm Shift\n"
            "  https://github.com/prdgmshift/usbliter8\n"
            "  https://ps.tc/pages/blog-usbliter8.html\n\n"
            "Affected Devices:\n"
            "  A12: iPhone XR, XS/XS Max, iPad Air 3,\n"
            "        iPad mini 5, iPad 8, Apple TV 4K (2nd gen)\n"
            "  A13: iPhone 11/11 Pro/11 Pro Max,\n"
            "        iPhone SE (2nd gen), iPad 9\n"
            "  S4/S5: Apple Watch S4/S5/SE, HomePod mini\n\n"
            "This exploit is TETHERED - requires re-exploitation\n"
            "after every reboot via the RP2350 board."
        )

        about = ctk.CTkLabel(
            frame,
            text=about_text,
            font=(FONT, 12),
            text_color=COLORS["text"],
            justify="left",
        )
        about.pack(pady=40, padx=40, anchor="w")

    def _card(self, parent, title, row, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=8)
        card.grid(row=row, column=col, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            card,
            text=title,
            font=(FONT, 13, "bold"),
            text_color=COLORS["text_bright"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 2))
        return card

    def _clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _highlight_nav(self, idx):
        for i, btn in enumerate(self._nav_buttons):
            if i == idx:
                btn.configure(text_color=COLORS["text_bright"], fg_color=COLORS["card"])
            else:
                btn.configure(text_color=COLORS["text_dim"], fg_color="transparent")

    def _setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(GUILogHandler(self.log_text))

    def _start_monitor(self):
        def monitor():
            while self._monitor_active:
                try:
                    self._update_status()
                except:
                    pass
                time.sleep(2)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

    def _update_status(self):
        device = find_pwned_device()
        boards = find_mass_storage_devices()

        if device:
            txt = f"Device: \u25cf {device.model_name()} (PWND)"
            clr = COLORS["success"]
        else:
            devs = find_devices()
            if devs:
                txt = f"Device: \u25cf {devs[0].model_name()} (Normal)"
                clr = COLORS["warning"]
            else:
                txt = "Device: \u25cf Not detected"
                clr = COLORS["text_dim"]

        self.root.after(0, lambda: self.status_device.configure(text=txt, text_color=clr))

        if boards:
            self.root.after(0, lambda: self.status_board.configure(
                text=f"Board: \u25cf {boards[0]['device']}", text_color=COLORS["info"]
            ))
        else:
            self.root.after(0, lambda: self.status_board.configure(
                text="Board: \u25cf Not detected", text_color=COLORS["text_dim"]
            ))

    def _on_flash(self):
        t = threading.Thread(target=self._flash_worker, daemon=True)
        t.start()

    def _flash_worker(self):
        self.root.after(0, lambda: self.btn_flash.configure(state="disabled", text="Flashing..."))
        log.info("Looking for RP2350 board in BOOTSEL mode...")

        devices = find_mass_storage_devices()
        if not devices:
            log.warn("Press BOOTSEL on RP2350 and connect to USB")
            for _ in range(30):
                devices = find_mass_storage_devices()
                if devices:
                    break
                time.sleep(1)

        if not devices:
            log.error("RP2350 not detected after 30s")
            self.root.after(0, lambda: self.btn_flash.configure(state="normal", text="Flash Firmware"))
            return

        fw_path = get_firmware_path()
        if not fw_path:
            log.info("Firmware not found locally, downloading...")
            self._download_firmware()
            fw_path = get_firmware_path()
            if not fw_path:
                log.error("Could not obtain firmware")
                self.root.after(0, lambda: self.btn_flash.configure(state="normal", text="Flash Firmware"))
                return

        mount = devices[0].get("mount")
        if not mount:
            log.error("Cannot determine mount point")
            self.root.after(0, lambda: self.btn_flash.configure(state="normal", text="Flash Firmware"))
            return

        log.info(f"Flashing {Path(fw_path).name} to {devices[0]['device']}...")
        if flash_firmware(fw_path, mount):
            log.info("Firmware flashed! Board rebooting...")
            time.sleep(3)
        else:
            log.error("Firmware flash failed")

        self.root.after(0, lambda: self.btn_flash.configure(state="normal", text="Flash Firmware"))

    def _download_firmware(self):
        import urllib.request, json
        try:
            url = "https://api.github.com/repos/prdgmshift/usbliter8/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "stalinra1n"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            dest = Path.home() / ".usbliter8" / "firmware"
            dest.mkdir(parents=True, exist_ok=True)
            for asset in data.get("assets", []):
                if asset["name"].endswith(".uf2"):
                    log.info(f"Downloading {asset['name']}...")
                    urllib.request.urlretrieve(asset["browser_download_url"], dest / asset["name"])
            log.info("Firmware download complete")
        except Exception as e:
            log.error(f"Download failed: {e}")

    def _on_exploit(self):
        if self._exploit_thread and self._exploit_thread.is_alive():
            log.warn("Exploit already running")
            return

        self.root.after(0, lambda: self.btn_exploit.configure(state="disabled", text="\u25b6  Running..."))
        self.root.after(0, lambda: self.exploit_label.configure(text="Starting exploit...", text_color=COLORS["warning"]))
        self.root.after(0, lambda: self.progress.set(0))

        self._exploit_thread = threading.Thread(target=self._exploit_worker, daemon=True)
        self._exploit_thread.start()

    def _exploit_worker(self):
        def status_cb(status):
            stage_map = {
                "checking_board": 0.05, "flashing_board": 0.15,
                "waiting_dfu": 0.25, "exploiting": 0.50,
                "waiting_reconnect": 0.75, "verifying": 0.90,
                "ready": 1.0, "complete": 1.0, "failed": 0.0,
            }
            pct = stage_map.get(status, 0)
            labels = {
                "checking_board": "Checking board...",
                "flashing_board": "Flashing firmware...",
                "waiting_dfu": "Waiting for DFU mode...",
                "exploiting": "Running exploit on RP2350...",
                "waiting_reconnect": "Waiting for device reconnect...",
                "verifying": "Verifying PWND status...",
                "ready": "Device PWND!",
                "complete": "Exploit complete!",
                "failed": "Exploit failed",
            }
            lbl = labels.get(status, status)
            self.root.after(0, lambda: self.progress.set(pct))
            self.root.after(0, lambda: self.exploit_label.configure(text=lbl))

        success = self.mgr.run_exploit_workflow(
            on_status=status_cb,
            dfu_timeout=self._get_setting("dfu_timeout", 60),
            exploit_timeout=self._get_setting("exploit_timeout", 30),
            reconnect_timeout=self._get_setting("reconnect_timeout", 30),
        )

        self.root.after(0, lambda: self.btn_exploit.configure(state="normal", text="\u25b6  Run Exploit"))
        if success:
            self.root.after(0, lambda: self.exploit_label.configure(text="Device PWND!", text_color=COLORS["success"]))
            self.root.after(0, lambda: self.btn_demote.configure(state="normal"))
            self.root.after(0, lambda: self.btn_boot.configure(state="normal"))
            self.root.after(0, lambda: self.btn_loader.configure(state="normal"))
            self.root.after(0, lambda: self.post_label.configure(text="Ready for payload injection", text_color=COLORS["success"]))
        else:
            self.root.after(0, lambda: self.exploit_label.configure(text="Exploit failed", text_color=COLORS["error"]))
            self.root.after(0, lambda: self.progress.set(0))

    def _on_demote(self):
        t = threading.Thread(target=self._demote_worker, daemon=True)
        t.start()

    def _demote_worker(self):
        log.info("Demoting production mode...")
        device = find_pwned_device()
        if not device:
            log.error("No PWND device found")
            return
        from ..core.device import usbliter8ctl_demote
        if usbliter8ctl_demote(device):
            log.info("Device demoted!")
        else:
            log.error("Demotion failed")

    def _on_boot(self):
        t = threading.Thread(target=self._boot_worker, daemon=True)
        t.start()

    def _boot_worker(self):
        device = find_pwned_device()
        if not device:
            log.error("No PWND device found")
            return

        payload_dir = Path.home() / ".usbliter8" / "payloads"
        payload_dir.mkdir(parents=True, exist_ok=True)
        files = [f for f in payload_dir.iterdir() if f.suffix in (".img4", ".iBoot", ".raw", ".bin")]

        if not files:
            log.warn(f"No payloads in {payload_dir}")
            log.info("Place .img4/.iBoot files there, or select a custom path")
            return

        log.info(f"Found {len(files)} payload(s) in {payload_dir}")
        for f in files:
            log.info(f"  {f.name} ({f.stat().st_size/1024:.0f} KB)")

        path = str(files[0])
        log.info(f"Booting {files[0].name}...")
        from ..core.device import usbliter8ctl_boot_iboot
        if usbliter8ctl_boot_iboot(device, path):
            log.info("iBoot booted!")
        else:
            log.error("Boot failed")

    def _on_install_loader(self):
        t = threading.Thread(target=self._loader_worker, daemon=True)
        t.start()

    def _loader_worker(self):
        device = find_pwned_device()
        if not device:
            log.error("No PWND device found")
            return

        log.info("Building and installing loader app...")
        loader_path = Path(__file__).parent.parent.parent / "device" / "loader"
        scripts_path = Path(__file__).parent.parent.parent / "device" / "scripts"

        if not (loader_path / "Loader.ipa").exists():
            log.info("No pre-built loader IPA found, building from source...")
            build_script = scripts_path / "build_loader.sh"
            if build_script.exists():
                result = subprocess.run(
                    ["bash", str(build_script)],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(loader_path),
                )
                if result.returncode == 0:
                    log.info("Loader built successfully")
                else:
                    log.error(f"Build failed: {result.stderr}")
                    return
            else:
                log.warn("Build script not found; provide your own Loader.ipa")
                return

        log.info("Sending loader to device via usbliter8ctl...")
        ipa_path = loader_path / "Loader.ipa"
        if ipa_path.exists():
            log.info(f"Use usbliter8ctl to deploy: {ipa_path}")
            log.info("Loader deployment requires custom ramdisk with installation daemon")
        else:
            log.error("Loader.ipa not found")

    def _on_check_dfu(self):
        t = threading.Thread(target=self._check_dfu_worker, daemon=True)
        t.start()

    def _check_dfu_worker(self):
        devices = find_devices()
        for d in devices:
            if d.pwnd:
                self.root.after(0, lambda: self.dfu_label.configure(
                    text="Device is PWND!", text_color=COLORS["success"]
                ))
                return
        self.root.after(0, lambda: self.dfu_label.configure(
            text="No DFU/PWND device detected", text_color=COLORS["text_dim"]
        ))

    def _show_dfu_guide_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("DFU Mode Guide")
        dialog.geometry("420x380")

        text = (
            "Entering DFU Mode (A12/A13 devices):\n\n"
            "1. Connect device to your computer\n"
            "2. Press Volume Up (quickly release)\n"
            "3. Press Volume Down (quickly release)\n"
            "4. Hold Side button for 10 seconds\n"
            "5. Keep holding Side, also hold\n"
            "   Volume Down for 5 seconds\n"
            "6. Release Side but keep holding\n"
            "   Volume Down for 5 more seconds\n\n"
            "Screen should be completely BLACK.\n"
            "If you see the Apple logo or 'Connect\n"
            "to iTunes', you're NOT in DFU mode.\n\n"
            "Note: Do NOT enter DFU by breaking LLB\n"
            "       (\u2191, \u2193, Side) - that won't work"
        )

        label = ctk.CTkLabel(
            dialog, text=text,
            font=(FONT, 12), text_color=COLORS["text"],
            justify="left",
        )
        label.pack(padx=20, pady=20, fill="both", expand=True)

        close = ctk.CTkButton(
            dialog, text="Got it",
            command=dialog.destroy,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
        )
        close.pack(pady=(0, 16))

    def _on_build_loader(self):
        log.info("Building loader app...")
        scripts = Path(__file__).parent.parent.parent / "device" / "scripts"
        build_script = scripts / "build_loader.sh"
        if build_script.exists():
            t = threading.Thread(
                target=lambda: subprocess.run(
                    ["bash", str(build_script)],
                    cwd=str(build_script.parent),
                ),
                daemon=True,
            )
            t.start()
        else:
            log.info("Loader build: see device/ directory for Xcode project")

    def _on_build_bootstrap(self):
        log.info("Building bootstrap package...")
        scripts = Path(__file__).parent.parent.parent / "device" / "scripts"
        build_script = scripts / "build_bootstrap.sh"
        if build_script.exists():
            t = threading.Thread(
                target=lambda: subprocess.run(
                    ["bash", str(build_script)],
                    cwd=str(build_script.parent),
                ),
                daemon=True,
            )
            t.start()
        else:
            log.info("Bootstrap build: see device/bootstrap/ directory")

    def _get_setting(self, key, default):
        var = getattr(self, f"_setting_{key}", None)
        if var is not None:
            try:
                val = var.get()
                if isinstance(default, bool):
                    return bool(val)
                if isinstance(default, int):
                    return int(val)
                return val
            except:
                return default
        return default

    def _on_close(self):
        self._monitor_active = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = ExploitGUI()
    app.run()


if __name__ == "__main__":
    main()
