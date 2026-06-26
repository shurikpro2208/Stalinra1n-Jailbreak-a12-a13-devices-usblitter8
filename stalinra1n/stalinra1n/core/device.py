import platform
import subprocess
import re
import time
from dataclasses import dataclass, field
from typing import Optional, List


A12_DEVICES = {
    "iPhone XR": "d321",
    "iPhone XS": "d331",
    "iPhone XS Max": "d331p",
    "iPad Air 3": "j421",
    "iPad mini 5": "j410",
    "iPad 8": "d331",
    "Apple TV 4K (2nd gen)": "j121",
}

A13_DEVICES = {
    "iPhone 11": "d421",
    "iPhone 11 Pro": "d431",
    "iPhone 11 Pro Max": "d431p",
    "iPhone SE (2nd gen)": "d421",
    "iPad 9": "j471",
}

S4_DEVICES = {
    "Apple Watch Series 4": "t8006",
}

S5_DEVICES = {
    "Apple Watch Series 5": "t8006",
    "Apple Watch SE (1st gen)": "t8006",
    "HomePod mini": "t8006",
}


@dataclass
class DeviceInfo:
    serial: str = ""
    ecid: Optional[str] = None
    board_id: Optional[str] = None
    chip_id: Optional[str] = None
    cpfm: Optional[str] = None
    scep: Optional[str] = None
    iboot_version: Optional[str] = None
    pwnd: bool = False
    exploit_tag: Optional[str] = None
    mode: str = "unknown"

    def model_name(self) -> str:
        if not self.chip_id:
            return "Unknown Device"
        chip_int = int(self.chip_id, 16) if self.chip_id.startswith("0x") else 0
        if chip_int == 0x8020:
            return "iPhone XS/XR (A12)"
        elif chip_int == 0x8030:
            return "iPhone 11 (A13)"
        elif chip_int == 0x8006:
            return "Apple Watch (S4/S5)"
        return f"Unknown (CPID: {self.chip_id})"

    def is_supported(self) -> bool:
        return self.chip_id in ("0x8020", "0x8030", "0x8006")


def _parse_pwnd_serial(serial: str) -> Optional[DeviceInfo]:
    if "PWND" not in serial:
        return None

    info = DeviceInfo(serial=serial, pwnd=True)
    patterns = {
        "chip_id": r"CPID:(\w+)",
        "board_id": r"BDID:(\w+)",
        "ecid": r"ECID:(\w+)",
        "cpfm": r"CPFM:(\w+)",
        "scep": r"SCEP:(\w+)",
        "iboot_version": r"SRTG:\[([^\]]+)\]",
        "exploit_tag": r"PWND:\[([^\]]+)\]",
    }

    for attr, pattern in patterns.items():
        match = re.search(pattern, serial)
        if match:
            setattr(info, attr, match.group(1))

    if info.chip_id:
        info.chip_id = f"0x{info.chip_id}" if not info.chip_id.startswith("0x") else info.chip_id

    info.mode = "pwnd"
    return info


def find_devices() -> List[DeviceInfo]:
    devices = []
    system = platform.system().lower()

    try:
        if system == "linux" or system == "darwin":
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType"] if system == "darwin"
                else ["lsusb"],
                capture_output=True, text=True, timeout=10,
            )
            output = result.stdout

            if system == "linux":
                result_detailed = subprocess.run(
                    ["lsusb", "-v"],
                    capture_output=True, text=True, timeout=15,
                )
                for line in result_detailed.stdout.split("\n"):
                    if "iSerial" in line or "SerialNumber" in line:
                        serial = line.split()[-1].strip()
                        parsed = _parse_pwnd_serial(serial)
                        if parsed:
                            devices.append(parsed)

            elif system == "darwin":
                current_device = {}
                for line in output.split("\n"):
                    if ":" in line and not line.startswith(" "):
                        if current_device.get("serial"):
                            parsed = _parse_pwnd_serial(current_device["serial"])
                            if parsed:
                                devices.append(parsed)
                        current_device = {}
                    elif "Serial Number:" in line:
                        current_device["serial"] = line.split(":")[-1].strip()

                if current_device.get("serial"):
                    parsed = _parse_pwnd_serial(current_device["serial"])
                    if parsed:
                        devices.append(parsed)

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        import usb.core
        import usb.util

        for device in usb.core.find(find_all=True):
            try:
                serial = usb.util.get_string(device, device.iSerialNumber)
                if serial and "PWND" in serial:
                    parsed = _parse_pwnd_serial(serial)
                    if parsed:
                        devices.append(parsed)
            except (usb.core.USBError, ValueError):
                pass
    except (ImportError, usb.core.NoBackendError):
        pass

    return devices


def find_pwned_device() -> Optional[DeviceInfo]:
    devices = find_devices()
    for d in devices:
        if d.pwnd and d.is_supported():
            return d
    return None


def wait_for_pwned_device(timeout: int = 30) -> Optional[DeviceInfo]:
    for _ in range(timeout):
        device = find_pwned_device()
        if device:
            return device
        time.sleep(1)
    return None


def usbliter8ctl_demote(device: DeviceInfo) -> bool:
    try:
        from usb.core import find as usb_find
    except ImportError:
        return False

    try:
        result = subprocess.run(
            ["python", "-m", "usbliter8ctl", "demote"],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def usbliter8ctl_boot_iboot(device: DeviceInfo, iboot_path: str) -> bool:
    try:
        result = subprocess.run(
            ["python", "-m", "usbliter8ctl", "boot", iboot_path],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
