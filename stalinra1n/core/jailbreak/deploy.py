import os
import shutil
import time
import subprocess
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field

from ...utils import log
from ..device import find_pwned_device, DeviceInfo
from ..board import get_firmware_path, find_mass_storage_devices, flash_firmware
from ..exploit import ExploitManager

from .iboot import iBootPatcher, KNOWN_BOOTARGS
from .ramdisk import RamdiskBuilder, RamdiskConfig
from .bootstrap import BootstrapManager, BootstrapConfig


@dataclass
class JailbreakConfig:
    device_model: str = ""
    ios_version: str = ""
    boot_args: list = field(default_factory=lambda: ["-v", "keepsyms=1", "amfi=0x0"])
    package_manager: str = "sileo"
    include_loader: bool = True
    skip_exploit: bool = False
    skip_demote: bool = False
    output_dir: str = ""
    auto_reboot: bool = True


class JailbreakDeployer:
    def __init__(self):
        self.config = JailbreakConfig()
        self.device: Optional[DeviceInfo] = None
        self.exploit_mgr = ExploitManager()
        self.iboot_patcher = iBootPatcher()
        self.ramdisk_builder = RamdiskBuilder()
        self.bootstrap_mgr = BootstrapManager()
        self._listeners: list[Callable] = []

    def add_listener(self, cb: Callable[[str, float], None]):
        self._listeners.append(cb)

    def _emit(self, status: str, progress: float):
        for cb in self._listeners:
            try:
                cb(status, progress)
            except Exception:
                pass

    def run_jailbreak(self, config: Optional[JailbreakConfig] = None) -> bool:
        if config:
            self.config = config

        log.info("=" * 50)
        log.info("  stalinra1n - Full Jailbreak")
        log.info("=" * 50)

        if not self.config.skip_exploit:
            if not self._step_exploit():
                return False
        else:
            self.device = find_pwned_device()
            if not self.device:
                log.error("No PWND device and skip_exploit=True")
                return False

        if not self.config.skip_demote:
            self._step_demote()

        if not self._step_prepare_bootstrap():
            return False

        if not self._step_boot():
            return False

        if not self._step_deploy():
            return False

        log.info("=" * 50)
        log.info("  Jailbreak complete!")
        log.info(f"  Device: {self.device.model_name() if self.device else 'Unknown'}")
        log.info("  Open the Loader app on your home screen")
        log.info("  to install Sileo/Zebra/Cydia")
        log.info("=" * 50)
        return True

    def _step_exploit(self) -> bool:
        self._emit("Running exploit...", 0.1)

        if not self.exploit_mgr.check_board_connected():
            log.step("Hold BOOTSEL on RP2350 and connect to USB")
            for _ in range(30):
                if self.exploit_mgr.check_board_connected():
                    break
                time.sleep(1)
            else:
                log.error("RP2350 not detected")
                return False

        fw_path = get_firmware_path()
        if not fw_path:
            log.info("Firmware not found, downloading...")
            self._download_firmware()
            fw_path = get_firmware_path()
            if not fw_path:
                log.error("Could not obtain firmware")
                return False

        devices = find_mass_storage_devices()
        if devices:
            mount = devices[0].get("mount")
            if mount:
                log.info("Flashing RP2350 firmware...")
                flash_firmware(fw_path, mount)
                time.sleep(3)

        self._emit("Waiting for DFU mode...", 0.3)
        log.step("Enter DFU mode on your device:")
        log.info("  Vol Up → Vol Down → Hold Side (10s) → Side+Vol Down (5s)")
        input("  Press Enter when device is in DFU mode...")

        self._emit("Running exploit on RP2350...", 0.5)
        log.step("Disconnect from PC → Connect to RP2350 board")
        log.step("Wait for green LED on RP2350")
        input("  Press Enter when LED is green (or wait 10s)...")
        time.sleep(2)

        self._emit("Reconnecting device...", 0.7)
        log.step("Disconnect from RP2350 → Reconnect to PC")

        self.device = None
        for _ in range(30):
            self.device = find_pwned_device()
            if self.device:
                break
            time.sleep(1)

        if not self.device:
            log.error("Device not detected after exploit")
            return False

        log.info(f"Device PWND: {self.device.model_name()}")
        self._emit("Exploit complete!", 1.0)
        return True

    def _step_demote(self):
        self._emit("Demoting production mode...", 0.2)
        from ..device import usbliter8ctl_demote
        if usbliter8ctl_demote(self.device):
            log.info("Production mode demoted")
        else:
            log.warn("Demotion failed (continuing anyway)")

    def _step_prepare_bootstrap(self) -> bool:
        self._emit("Preparing bootstrap...", 0.3)

        bs_config = BootstrapConfig(
            include_sileo=(self.config.package_manager == "sileo"),
            include_zebra=(self.config.package_manager == "zebra"),
        )

        bootstrap_path = self.bootstrap_mgr.build_bootstrap_package(bs_config)
        if not bootstrap_path:
            log.error("Failed to build bootstrap package")
            return False

        ramdisk_config = RamdiskConfig(
            ios_version=self.config.ios_version,
            device_model=self.config.device_model,
            include_ssh=True,
            include_loader=self.config.include_loader,
            include_bootstrap=True,
        )

        rootfs = self.ramdisk_builder.create_rootfs(ramdisk_config)
        if not rootfs:
            log.error("Failed to create ramdisk rootfs")
            return False

        shutil.copy2(bootstrap_path, rootfs / "bootstrap.tar.gz")

        if self.config.include_loader:
            loader_src = Path(__file__).parent.parent.parent.parent / "device" / "loader"
            loader_app = rootfs / "Loader.app"
            if loader_src.exists():
                loader_app.mkdir(exist_ok=True)
                for f in loader_src.iterdir():
                    if f.is_file():
                        shutil.copy2(f, loader_app / f.name)
                log.info("Loader app included in ramdisk")
            else:
                log.warn("Loader app source not found, skipping")

        dmg = self.ramdisk_builder.build_dmg(rootfs, ramdisk_config)
        if not dmg:
            log.error("Failed to build ramdisk image")
            return False

        log.info(f"Ramdisk ready: {dmg.name}")
        self.ramdisk_builder.cleanup()
        return True

    def _step_boot(self) -> bool:
        self._emit("Booting custom iBoot...", 0.6)

        boot_args = " ".join(self.config.boot_args)

        if self.config.ios_version and self.config.device_model:
            ipsw = self.iboot_patcher.download_ipsw(
                self.config.device_model, self.config.ios_version
            )
            if ipsw:
                iboot = self.iboot_patcher.extract_iboot(ipsw)
                if iboot:
                    for patch_name in ["disable_sigcheck", "allow_custom_bootargs", "skip_fsck"]:
                        self.iboot_patcher.apply_patch(iboot, patch_name)

                    iboot_path = iboot.parent / f"{iboot.name}.patched"
                    if iboot_path.exists():
                        log.info(f"Patched iBoot: {iboot_path}")
                        log.info("Booting with boot-args: {boot_args}")
                        log.info("Use usbliter8ctl to boot:")
                        log.info(f"  usbliter8ctl boot {iboot_path}")
                        return True

        log.info("No iBoot patching available yet (community needs to find offsets)")
        log.info("Booting raw iBoot with usbliter8ctl...")
        return True

    def _step_deploy(self) -> bool:
        self._emit("Deploying jailbreak...", 0.8)
        log.info("Booted custom ramdisk. Deploying via SSH...")

        ip = "127.0.0.1"
        port = 2222

        log.info(f"Connect to device: ssh root@{ip} -p {port}")
        log.info("  Password: (blank / alpine)")

        log.info("Run these commands on the device:")
        log.info("  /bootstrap/install_bootstrap.sh")
        log.info("  /bootstrap/deploy_loader.sh")
        log.info("  /bootstrap/finalize.sh")

        attempts = 0
        while attempts < 15:
            try:
                result = subprocess.run(
                    ["ssh", "-o", "StrictHostKeyChecking=no",
                     "-o", "ConnectTimeout=3",
                     "-p", str(port),
                     f"root@{ip}",
                     "ls /bootstrap/ 2>/dev/null"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    log.info("Device reachable via SSH!")
                    log.info("Running deployment scripts...")

                    for script in ["install_bootstrap.sh", "install_package_manager.sh",
                                   "deploy_loader.sh", "finalize.sh"]:
                        subprocess.run([
                            "ssh", "-o", "StrictHostKeyChecking=no",
                            "-p", str(port), f"root@{ip}",
                            f"bash /bootstrap/{script}",
                        ], timeout=120)

                    log.info("Deployment complete!")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            attempts += 1
            time.sleep(5)

        log.warn("Could not reach device via SSH")
        log.info("Deployment scripts are on the ramdisk.")
        log.info("If you can SSH in, run them manually.")
        return True

    def _download_firmware(self):
        import urllib.request
        import json
        try:
            url = "https://api.github.com/repos/prdgmshift/usbliter8/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "stalinra1n"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            dest = Path.home() / ".stalinra1n" / "firmware"
            dest.mkdir(parents=True, exist_ok=True)
            for asset in data.get("assets", []):
                if asset["name"].endswith(".uf2"):
                    urllib.request.urlretrieve(asset["browser_download_url"], dest / asset["name"])
            log.info("Firmware downloaded")
        except Exception as e:
            log.error(f"Download failed: {e}")
