import sys
import os
import shutil
import time
import threading
from pathlib import Path

from ..core.exploit import ExploitManager, ExploitStage
from ..core.device import find_pwned_device, find_devices
from ..core.board import find_mass_storage_devices, get_firmware_path
from ..utils import log


BANNER = r"""
███████╗████████╗ █████╗ ██╗     ██╗███╗   ██╗██████╗  █████╗  ██╗███╗   ██╗
██╔════╝╚══██╔══╝██╔══██╗██║     ██║████╗  ██║██╔══██╗██╔══██╗███║████╗  ██║
███████╗   ██║   ███████║██║     ██║██╔██╗ ██║██████╔╝███████║╚██║██╔██╗ ██║
╚════██║   ██║   ██╔══██║██║     ██║██║╚██╗██║██╔══██╗██╔══██║ ██║██║╚██╗██║
███████║   ██║   ██║  ██║███████╗██║██║ ╚████║██║  ██║██║  ██║ ██║██║ ╚████║
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═╝╚═╝  ╚═══╝
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    clear_screen()
    print("\033[36m" + BANNER + "\033[0m")
    print("  stalinra1n - A12/A13 SecureROM Jailbreak")
    print("  Based on usbliter8 by Paradigm Shift")
    print("  github.com/prdgmshift/usbliter8")
    print()
    print("=" * 60)
    print()


def print_menu(options, title="Menu"):
    print(f"  \033[1m{title}\033[0m")
    print()
    for i, (key, label, _) in enumerate(options, 1):
        print(f"    \033[33m{i}\033[0m. {label}")
    print()
    print("    \033[33m0\033[0m. Exit")
    print()


def get_choice(options):
    while True:
        try:
            choice = input("  \033[1mSelect > \033[0m").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"  Invalid choice. Enter 1-{len(options)} or 0.")
        except (ValueError, IndexError):
            print(f"  Invalid choice. Enter 1-{len(options)} or 0.")
        except (EOFError, KeyboardInterrupt):
            return None


def wait_for_key():
    try:
        input("\n  Press Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        pass


def animated_status(message, success=None):
    if success is True:
        print(f"  \033[32m\u2713\033[0m {message}")
    elif success is False:
        print(f"  \033[31m\u2717\033[0m {message}")
    else:
        print(f"  \033[36m*\033[0m {message}")


class InteractiveTUI:
    def __init__(self):
        self.mgr = ExploitManager()

    def show_device_status(self):
        print()
        devices = find_devices()
        if not devices:
            animated_status("No Apple devices detected", False)
            return

        for d in devices:
            print(f"    Model:     \033[1m{d.model_name()}\033[0m")
            print(f"    ECID:      {d.ecid or 'N/A'}")
            print(f"    Chip ID:   {d.chip_id or 'N/A'}")
            print(f"    Board ID:  {d.board_id or 'N/A'}")
            print(f"    iBoot:     {d.iboot_version or 'N/A'}")
            if d.pwnd:
                print(f"    Status:    \033[32mPWND ({d.exploit_tag})\033[0m")
            else:
                print(f"    Status:    \033[33mNormal\033[0m")
            print()

    def run_exploit(self):
        print()
        animated_status("Starting exploit workflow...")

        def status_cb(status):
            pass

        success = self.mgr.run_exploit_workflow(
            on_status=status_cb,
            dfu_timeout=60,
            exploit_timeout=30,
            reconnect_timeout=30,
        )

        if success:
            animated_status("Exploit successful! Device is PWND", True)
        else:
            animated_status("Exploit failed", False)

        wait_for_key()

    def demote_device(self):
        print()
        device = find_pwned_device()
        if not device:
            animated_status("No PWND device found. Run exploit first.", False)
            wait_for_key()
            return

        animated_status("Demoting production mode...")
        from ..core.device import usbliter8ctl_demote
        if usbliter8ctl_demote(device):
            animated_status("Device demoted! Changes lost on reboot", True)
        else:
            animated_status("Demotion failed", False)
        wait_for_key()

    def boot_iboot(self):
        print()
        device = find_pwned_device()
        if not device:
            animated_status("No PWND device found. Run exploit first.", False)
            wait_for_key()
            return

        iboot_dir = Path.home() / ".usbliter8" / "payloads"
        iboot_dir.mkdir(parents=True, exist_ok=True)

        iboot_files = list(iboot_dir.glob("*"))
        iboot_files = [f for f in iboot_files if f.is_file() and f.suffix in (".img4", ".iBoot", ".raw", ".bin")]

        if not iboot_files:
            animated_status(f"No payloads found in {iboot_dir}", False)
            animated_status("Place .img4 or .iBoot files in ~/.usbliter8/payloads/")
            wait_for_key()
            return

        print(f"  Available payloads in {iboot_dir}:")
        print()
        for i, f in enumerate(iboot_files, 1):
            size = f.stat().st_size
            size_str = f"{size / 1024:.0f} KB" if size < 1024*1024 else f"{size / 1024 / 1024:.1f} MB"
            print(f"    \033[33m{i}\033[0m. {f.name} ({size_str})")

        print()
        try:
            choice = input("  \033[1mSelect payload > \033[0m").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(iboot_files):
                path = str(iboot_files[idx])
                animated_status(f"Booting {iboot_files[idx].name}...")
                from ..core.device import usbliter8ctl_boot_iboot
                if usbliter8ctl_boot_iboot(device, path):
                    animated_status("iBoot booted successfully!", True)
                else:
                    animated_status("Failed to boot iBoot", False)
            else:
                animated_status("Invalid selection", False)
        except (ValueError, EOFError, KeyboardInterrupt):
            pass

        wait_for_key()

    def flash_board(self):
        print()
        fw_path = get_firmware_path()
        if not fw_path:
            animated_status("Firmware not found locally", False)
            animated_status("Run 'Fetch firmware' from menu or 'stalinra1n fetch-firmware'")
            wait_for_key()
            return

        animated_status(f"Firmware found: {fw_path}")
        animated_status("Hold BOOTSEL on RP2350 and connect to USB...")

        devices = find_mass_storage_devices()
        if not devices:
            for _ in range(30):
                devices = find_mass_storage_devices()
                if devices:
                    break
                time.sleep(1)
            else:
                animated_status("Board not detected", False)
                wait_for_key()
                return

        from ..core.board import flash_firmware
        mount = devices[0].get("mount")
        if not mount:
            animated_status("Cannot find board mount point", False)
            wait_for_key()
            return

        animated_status(f"Flashing to {devices[0]['device']}...")
        if flash_firmware(fw_path, mount):
            animated_status("Firmware flashed! Board rebooting...", True)
            time.sleep(3)
        else:
            animated_status("Flashing failed", False)
        wait_for_key()

    def fetch_firmware(self):
        print()
        animated_status("Fetching latest firmware from GitHub...")
        import urllib.request
        import json

        try:
            url = "https://api.github.com/repos/prdgmshift/usbliter8/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "stalinra1n"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())

            dest_dir = Path.home() / ".usbliter8" / "firmware"
            dest_dir.mkdir(parents=True, exist_ok=True)

            assets = data.get("assets", [])
            count = 0
            for asset in assets:
                name = asset["name"]
                if name.endswith(".uf2"):
                    dl_url = asset["browser_download_url"]
                    dest_path = dest_dir / name
                    animated_status(f"Downloading {name}...")
                    urllib.request.urlretrieve(dl_url, dest_path)
                    count += 1

            animated_status(f"Downloaded {count} firmware file(s) to {dest_dir}", True)
        except Exception as e:
            animated_status(f"Failed: {e}", False)
        wait_for_key()

    def run(self):
        while True:
            print_header()

            device = find_pwned_device()
            board_in_bootsel = bool(find_mass_storage_devices())

            if device:
                print(f"  \033[32m\u25cf PWND\033[0m {device.model_name()} (ECID: {device.ecid})")
            else:
                print(f"  \033[90m\u25cf No exploited device detected\033[0m")

            if board_in_bootsel:
                print(f"  \033[36m\u25cf RP2350 in BOOTSEL mode detected\033[0m")
            print()

            menu = [
                ("exploit", "Run exploit (full workflow)", self.run_exploit),
                ("demote", "Demote production mode", self.demote_device),
                ("boot", "Boot payload (iBoot/ramdisk)", self.boot_iboot),
                ("flash", "Flash RP2350 board firmware", self.flash_board),
                ("fetch", "Fetch latest firmware from GitHub", self.fetch_firmware),
                ("status", "Show device status", self.show_device_status),
            ]

            print_menu(menu, "Main Menu")

            choice = get_choice(menu)
            if choice is None:
                print()
                animated_status("Goodbye!", True)
                break

            _, _, action = choice
            if action:
                print_header()
                action()
