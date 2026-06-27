import argparse
import sys
import os
from pathlib import Path

from ..core.exploit import ExploitManager
from ..core.device import DeviceInfo, find_pwned_device, find_devices
from ..core.board import get_firmware_path, find_mass_storage_devices, flash_firmware
from ..core.jailbreak import iBootPatcher, RamdiskBuilder, BootstrapManager, JailbreakDeployer
from ..core.jailbreak.deploy import JailbreakConfig
from ..core.jailbreak.bootstrap import BootstrapConfig
from ..core.jailbreak.ramdisk import RamdiskConfig
from ..utils import log

from .tui import InteractiveTUI


def cmd_exploit(args):
    mgr = ExploitManager()

    def status_callback(status: str):
        sys.stdout.flush()

    success = mgr.run_exploit_workflow(
        on_status=status_callback,
        dfu_timeout=args.dfu_timeout,
        exploit_timeout=args.exploit_timeout,
        reconnect_timeout=args.reconnect_timeout,
    )

    if success:
        print()
        log.info("Device is now PWND and ready for payload injection")
        return 0
    return 1


def cmd_demote(args):
    device = find_pwned_device()
    if not device:
        log.error("No PWND device found. Run exploit first.")
        return 1

    from ..core.device import usbliter8ctl_demote
    if usbliter8ctl_demote(device):
        log.info("Device demoted successfully!")
        return 0
    log.error("Demotion failed")
    return 1


def cmd_boot(args):
    device = find_pwned_device()
    if not device:
        log.error("No PWND device found. Run exploit first.")
        return 1

    iboot_path = args.iboot
    if not os.path.exists(iboot_path):
        log.error(f"iBoot not found: {iboot_path}")
        return 1

    from ..core.device import usbliter8ctl_boot_iboot
    if usbliter8ctl_boot_iboot(device, iboot_path):
        log.info("iBoot booted successfully!")
        return 0
    log.error("Failed to boot iBoot")
    return 1


def cmd_status(args):
    devices = find_devices()
    if not devices:
        print("No Apple devices detected")
        return 0

    for d in devices:
        print(f"  Model:    {d.model_name()}")
        print(f"  ECID:     {d.ecid or 'N/A'}")
        print(f"  CPID:     {d.chip_id or 'N/A'}")
        print(f"  BDID:     {d.board_id or 'N/A'}")
        print(f"  iBoot:    {d.iboot_version or 'N/A'}")
        print(f"  PWND:     {'Yes' if d.pwnd else 'No'}")
        if d.pwnd:
            print(f"  Exploit:  {d.exploit_tag or 'N/A'}")
        print()

    return 0


def cmd_board(args):
    devices = find_mass_storage_devices()
    if not devices:
        print("No RP2350 board detected in mass storage mode")
        print("Hold BOOTSEL and connect to USB")
        return 1

    for d in devices:
        print(f"  Device: {d['device']}")
        print(f"  Mount:  {d.get('mount', 'N/A')}")
    return 0


def cmd_flash(args):
    fw_path = get_firmware_path()
    if not fw_path:
        log.error("Firmware not found. Run 'stalinra1n fetch-firmware'")
        return 1

    devices = find_mass_storage_devices()
    if not devices:
        log.error("No RP2350 board in mass storage mode")
        log.info("Hold BOOTSEL on RP2350 and connect to USB")
        return 1

    mount = devices[0].get("mount")
    if not mount:
        log.error("Board mount point not found")
        return 1

    log.info(f"Flashing {fw_path} to {mount}...")
    if flash_firmware(fw_path, mount):
        log.info("Firmware flashed successfully!")
        return 0
    log.error("Flashing failed")
    return 1


def cmd_fetch_firmware(args):
    import urllib.request
    import json

    url = "https://api.github.com/repos/prdgmshift/usbliter8/releases/latest"
    log.info("Fetching latest firmware from GitHub...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "stalinra1n"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        dest_dir = Path.home() / ".usbliter8" / "firmware"
        dest_dir.mkdir(parents=True, exist_ok=True)

        assets = data.get("assets", [])
        downloaded = 0
        for asset in assets:
            name = asset["name"]
            if name.endswith(".uf2"):
                download_url = asset["browser_download_url"]
                dest_path = dest_dir / name
                log.info(f"Downloading {name}...")
                urllib.request.urlretrieve(download_url, dest_path)
                log.info(f"  Saved to {dest_path}")
                downloaded += 1

        if downloaded == 0:
            log.warn("No UF2 files found in latest release")
        else:
            log.info(f"Downloaded {downloaded} firmware file(s) to {dest_dir}")

        return 0
    except Exception as e:
        log.error(f"Failed to fetch firmware: {e}")
        return 1


def cmd_tui(args):
    tui = InteractiveTUI()
    tui.run()


def cmd_gui(args):
    try:
        from ..gui.app import main as gui_main
        gui_main()
    except ImportError as e:
        log.error(f"Cannot start GUI: {e}")
        log.info("Install customtkinter: pip install customtkinter")
        return 1
    return 0


def cmd_jailbreak(args):
    log.info("Starting full jailbreak workflow...")
    config = JailbreakConfig(
        device_model=args.model or "",
        ios_version=args.ios or "",
        package_manager=args.pm or "sileo",
        include_loader=not args.no_loader,
        boot_args=args.bootargs.split() if args.bootargs else ["-v", "keepsyms=1", "amfi=0x0"],
        skip_exploit=args.skip_exploit,
        skip_demote=args.skip_demote,
        auto_reboot=not args.no_reboot,
    )
    deployer = JailbreakDeployer()
    success = deployer.run_jailbreak(config)
    return 0 if success else 1


def cmd_build_loader(args):
    import subprocess
    scripts_dir = Path(__file__).parent.parent.parent / "device" / "scripts"
    build_script = scripts_dir / "build_loader.sh"
    if build_script.exists():
        log.info("Building loader app...")
        result = subprocess.run(["bash", str(build_script)])
        return result.returncode
    else:
        log.error("build_loader.sh not found")
        return 1


def cmd_build_bootstrap(args):
    config = BootstrapConfig(
        include_sileo=(args.pm == "sileo"),
        include_zebra=(args.pm == "zebra"),
    )
    mgr = BootstrapManager()
    path = mgr.build_bootstrap_package(config)
    if path:
        log.info(f"Bootstrap created: {path}")
        return 0
    log.error("Failed to build bootstrap")
    return 1


def cmd_fetch_ipsw(args):
    patcher = iBootPatcher()
    ipsw = patcher.download_ipsw(args.model, args.ios)
    if ipsw:
        log.info(f"IPSW downloaded: {ipsw}")
        return 0
    return 1


def cmd_build_ramdisk(args):
    config = RamdiskConfig(
        ios_version=args.ios or "",
        device_model=args.model or "",
        include_ssh=not args.no_ssh,
        include_loader=not args.no_loader,
        include_bootstrap=not args.no_bootstrap,
    )
    builder = RamdiskBuilder()
    rootfs = builder.create_rootfs(config)
    if rootfs:
        dmg = builder.build_dmg(rootfs, config)
        if dmg:
            log.info(f"Ramdisk created: {dmg}")
            builder.cleanup()
            return 0
    return 1


def cmd_iboot_patch(args):
    patcher = iBootPatcher()
    iboot_path = Path(args.iboot)
    if not iboot_path.exists():
        log.error(f"iBoot not found: {iboot_path}")
        return 1

    patches_to_apply = args.patches or ["disable_sigcheck", "allow_custom_bootargs"]
    for p in patches_to_apply:
        patcher.apply_patch(iboot_path, p)

    if patcher.patches_applied:
        log.info(f"Patches applied: {patcher.patches_applied}")
        return 0
    log.warn("No patches were applied (offsets not yet defined)")
    log.info("Community needs to find iBoot patch offsets first")
    return 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="stalinra1n",
        description="A12/A13 BootROM exploit + jailbreak tool (usbliter8)",
        epilog="Based on usbliter8 by Paradigm Shift (github.com/prdgmshift/usbliter8)",
    )

    sub = parser.add_subparsers(dest="command", help="Command")

    p_exploit = sub.add_parser("exploit", help="Run full exploit workflow")
    p_exploit.add_argument("--dfu-timeout", type=int, default=60, help="DFU wait timeout (s)")
    p_exploit.add_argument("--exploit-timeout", type=int, default=30, help="Exploit wait timeout (s)")
    p_exploit.add_argument("--reconnect-timeout", type=int, default=30, help="Reconnect wait timeout (s)")

    sub.add_parser("gui", help="Launch GUI application")
    sub.add_parser("tui", help="Interactive terminal UI")

    p_jb = sub.add_parser("jailbreak", help="Full jailbreak workflow")
    p_jb.add_argument("--model", type=str, default="", help="Device model (e.g. D321AP)")
    p_jb.add_argument("--ios", type=str, default="", help="iOS version (e.g. 16.5)")
    p_jb.add_argument("--pm", type=str, default="sileo", choices=["sileo", "zebra"], help="Package manager")
    p_jb.add_argument("--bootargs", type=str, default="", help="Custom boot-args (space-separated)")
    p_jb.add_argument("--no-loader", action="store_true", help="Skip loader app")
    p_jb.add_argument("--skip-exploit", action="store_true", help="Skip exploit step")
    p_jb.add_argument("--skip-demote", action="store_true", help="Skip demotion")
    p_jb.add_argument("--no-reboot", action="store_true", help="Don't auto-reboot")

    p_boot = sub.add_parser("boot", help="Boot raw iBoot image")
    p_boot.add_argument("iboot", type=str, help="Path to raw iBoot image")

    sub.add_parser("demote", help="Demote production mode")
    sub.add_parser("status", help="Show device status")
    sub.add_parser("board", help="Show RP2350 board info")
    sub.add_parser("flash", help="Flash firmware to RP2350 board")
    sub.add_parser("fetch-firmware", help="Download latest firmware from GitHub")
    sub.add_parser("build-loader", help="Build device-side loader app")

    p_bb = sub.add_parser("build-bootstrap", help="Build bootstrap package")
    p_bb.add_argument("--pm", type=str, default="sileo", choices=["sileo", "zebra"], help="Package manager")

    p_fetch = sub.add_parser("fetch-ipsw", help="Download IPSW for iBoot extraction")
    p_fetch.add_argument("model", type=str, help="Device model (e.g. D321AP)")
    p_fetch.add_argument("ios", type=str, help="iOS version (e.g. 16.5)")

    p_rd = sub.add_parser("build-ramdisk", help="Build custom ramdisk")
    p_rd.add_argument("--model", type=str, default="", help="Device model")
    p_rd.add_argument("--ios", type=str, default="", help="iOS version")
    p_rd.add_argument("--no-ssh", action="store_true", help="Skip SSH")
    p_rd.add_argument("--no-loader", action="store_true", help="Skip loader app")
    p_rd.add_argument("--no-bootstrap", action="store_true", help="Skip bootstrap")

    p_iboot = sub.add_parser("iboot-patch", help="Patch iBoot image")
    p_iboot.add_argument("iboot", type=str, help="Path to iBoot image")
    p_iboot.add_argument("--patches", type=str, nargs="*",
                        default=["disable_sigcheck", "allow_custom_bootargs"],
                        help="Patches to apply")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "gui":
        return cmd_gui(args)
    elif args.command == "tui":
        return cmd_tui(args)
    elif args.command == "jailbreak":
        return cmd_jailbreak(args)
    elif args.command == "exploit":
        return cmd_exploit(args)
    elif args.command == "demote":
        return cmd_demote(args)
    elif args.command == "boot":
        return cmd_boot(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "board":
        return cmd_board(args)
    elif args.command == "flash":
        return cmd_flash(args)
    elif args.command == "fetch-firmware":
        return cmd_fetch_firmware(args)
    elif args.command == "build-loader":
        return cmd_build_loader(args)
    elif args.command == "build-bootstrap":
        return cmd_build_bootstrap(args)
    elif args.command == "fetch-ipsw":
        return cmd_fetch_ipsw(args)
    elif args.command == "build-ramdisk":
        return cmd_build_ramdisk(args)
    elif args.command == "iboot-patch":
        return cmd_iboot_patch(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
