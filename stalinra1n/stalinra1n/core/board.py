import platform
import subprocess
import time
import shutil
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


SUPPORTED_BOARDS = {
    "waveshare_rp2350_usb_a": {
        "name": "Waveshare RP2350 USB-A",
        "led_rgb": True,
        "sdk_board": "waveshare_rp2350_usb_a",
    },
    "waveshare_rp2350_zero": {
        "name": "Waveshare RP2350 Zero",
        "led_rgb": True,
        "sdk_board": "waveshare_rp2350_zero",
    },
    "pimoroni_tiny2350": {
        "name": "Pimoroni TINY2350",
        "led_rgb": True,
        "sdk_board": "pimoroni_tiny2350",
    },
    "pico2": {
        "name": "Raspberry Pi Pico 2",
        "led_rgb": False,
        "sdk_board": "pico2",
    },
    "unknown": {
        "name": "Generic RP2350",
        "led_rgb": False,
        "sdk_board": "unknown",
    },
}


@dataclass
class RP2350Board:
    model: str
    serial: Optional[str] = None
    port: Optional[str] = None
    firmware_ready: bool = False


def find_mass_storage_devices():
    system = platform.system().lower()
    devices = []

    if system == "linux":
        try:
            result = subprocess.run(
                ["lsblk", "-o", "NAME,LABEL,MODEL,SIZE,MOUNTPOINT", "-l", "-n"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if "RPI-RP2" in line.upper() or "RP2350" in line.upper():
                    parts = line.split()
                    if parts:
                        dev = parts[0]
                        mount = parts[-1] if len(parts) > 4 else None
                        devices.append({
                            "device": f"/dev/{dev}",
                            "mount": mount,
                            "raw": line,
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    elif system == "darwin":
        try:
            result = subprocess.run(
                ["diskutil", "list"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split("\n")
            current_disk = None
            for line in lines:
                if line.startswith("/dev/"):
                    current_disk = line.split()[-1]
                if "RPI-RP2" in line.upper() or "RP2350" in line.upper():
                    if current_disk:
                        mount_result = subprocess.run(
                            ["diskutil", "info", current_disk],
                            capture_output=True, text=True, timeout=5
                        )
                        mount_point = None
                        for info_line in mount_result.stdout.split("\n"):
                            if "Mount Point:" in info_line:
                                mount_point = info_line.split(":", 1)[-1].strip()
                                break
                        devices.append({
                            "device": current_disk,
                            "mount": mount_point,
                            "raw": line,
                        })
                        current_disk = None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    elif system == "windows":
        try:
            import string
            available = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        label = subprocess.run(
                            ["vol", drive],
                            capture_output=True, text=True, timeout=3,
                            shell=True,
                        )
                        if "RPI-RP2" in label.stdout.upper() or "RP2350" in label.stdout.upper():
                            available.append({
                                "device": drive,
                                "mount": drive,
                                "raw": label.stdout,
                            })
                    except:
                        pass
            devices = available
        except:
            pass

    return devices


def find_serial_ports():
    system = platform.system().lower()
    ports = []

    try:
        if system == "linux":
            result = subprocess.run(
                ["ls", "-l", "/dev/serial/by-id/"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.strip().split("\n"):
                if "RP2350" in line or "Pico" in line:
                    parts = line.split()
                    if parts:
                        link = parts[-1]
                        full_path = os.path.realpath(
                            os.path.join("/dev/serial/by-id", link)
                        )
                        ports.append(full_path)

        elif system == "darwin":
            result = subprocess.run(
                ["ls", "/dev/cu.*"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.strip().split("\n"):
                if "usbmodem" in line.lower() or "usbserial" in line.lower():
                    ports.append(line.strip())

        elif system == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_SerialPort", "get", "DeviceID,Description"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.strip().split("\n"):
                    if "RP2350" in line or "USB Serial" in line or "Pico" in line:
                        parts = line.split()
                        if parts:
                            ports.append(parts[0])
            except:
                pass
    except:
        pass

    return ports


def flash_firmware(uf2_path: str, mount_point: str) -> bool:
    dest = os.path.join(mount_point, "usbliter8.uf2")
    try:
        shutil.copy2(uf2_path, dest)
        time.sleep(2)
        return True
    except (shutil.Error, OSError) as e:
        return False


def reboot_board(mount_point: str = None):
    if mount_point and os.path.exists(mount_point):
        try:
            reset_file = os.path.join(mount_point, "RESET.TXT")
            with open(reset_file, "w") as f:
                f.write("reset")
        except:
            pass


def wait_for_board_reconnect(timeout: int = 15) -> bool:
    for _ in range(timeout):
        if find_mass_storage_devices():
            return True
        time.sleep(1)
    return False


def get_firmware_path() -> Optional[str]:
    search_paths = [
        Path(__file__).parent.parent.parent / "firmware" / "usbliter8.uf2",
        Path(__file__).parent.parent / "firmware" / "usbliter8.uf2",
        Path.home() / ".usbliter8" / "firmware" / "usbliter8.uf2",
        Path("/usr/share/usbliter8/firmware/usbliter8.uf2"),
        Path("/usr/local/share/usbliter8/firmware/usbliter8.uf2"),
    ]
    for path in search_paths:
        if path.exists():
            return str(path)
    return None
