import os
import stat
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

from ...utils import log


RAMDISK_SCRIPTS = {
    "mount_rootfs.sh": """#!/bin/bash
# Mount rootfs as read-write
mount -o rw,union /dev/disk0s1s1 /mnt
""",

    "install_bootstrap.sh": """#!/bin/bash
# Extract and install bootstrap
BOOTSTRAP_PATH="/bootstrap.tar.gz"
ROOTFS_MNT="/mnt"

echo "stalinra1n: Installing bootstrap..."
if [ -f "$BOOTSTRAP_PATH" ]; then
    tar -xzf "$BOOTSTRAP_PATH" -C "$ROOTFS_MNT"
    echo "stalinra1n: Bootstrap extracted"
fi

# Run post-install scripts
if [ -f "$ROOTFS_MNT/bootstrap/postinst.sh" ]; then
    chroot "$ROOTFS_MNT" /bin/bash /bootstrap/postinst.sh
fi
""",

    "install_package_manager.sh": """#!/bin/bash
# Install Sileo or Zebra
PM_DEB="$1"
ROOTFS_MNT="/mnt"

if [ -f "$PM_DEB" ]; then
    cp "$PM_DEB" "$ROOTFS_MNT/tmp/"
    chroot "$ROOTFS_MNT" /usr/bin/dpkg -i "/tmp/$(basename $PM_DEB)" 2>/dev/null || true
    rm -f "$ROOTFS_MNT/tmp/$(basename $PM_DEB)"
    echo "stalinra1n: Package manager installed"
fi
""",

    "deploy_loader.sh": """#!/bin/bash
# Deploy loader app to Applications
LOADER_APP="/Loader.app"
ROOTFS_MNT="/mnt"

if [ -d "$LOADER_APP" ]; then
    cp -r "$LOADER_APP" "$ROOTFS_MNT/Applications/"
    chown -R 0:0 "$ROOTFS_MNT/Applications/Loader.app"
    chmod -R 755 "$ROOTFS_MNT/Applications/Loader.app"
    echo "stalinra1n: Loader app deployed"
fi
""",

    "finalize.sh": """#!/bin/bash
# Finalize jailbreak
ROOTFS_MNT="/mnt"

# Create jailbreak marker
echo "stalinra1n 1.0.0" > "$ROOTFS_MNT/.stalinra1n_jb"

# Fix permissions
chmod 755 "$ROOTFS_MNT/usr/bin/"* 2>/dev/null || true

# Sync and prepare to reboot
sync

echo "stalinra1n: Jailbreak finalized. Rebooting userspace..."
launchctl reboot userspace
""",
}


@dataclass
class RamdiskConfig:
    ios_version: str = ""
    device_model: str = ""
    include_ssh: bool = True
    include_loader: bool = True
    include_bootstrap: bool = True
    custom_scripts_dir: Optional[str] = None
    output_name: str = "stalinra1n_ramdisk"


class RamdiskBuilder:
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = Path(work_dir or Path.home() / ".stalinra1n" / "ramdisk")
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def create_rootfs(self, config: RamdiskConfig) -> Optional[Path]:
        rootfs = self.work_dir / "rootfs"
        if rootfs.exists():
            import shutil
            shutil.rmtree(rootfs)
        rootfs.mkdir(parents=True)

        dirs = [
            "usr/bin", "usr/lib", "usr/sbin",
            "bin", "sbin", "etc", "tmp", "var",
            "mnt", "bootstrap",
            "Library",
            "System/Library/CoreServices",
        ]
        for d in dirs:
            (rootfs / d).mkdir(parents=True, exist_ok=True)

        self._write_scripts(rootfs)
        self._write_services(rootfs, config)

        if config.include_ssh:
            self._setup_ssh(rootfs)

        log.info(f"Ramdisk rootfs created at {rootfs}")
        return rootfs

    def _write_scripts(self, rootfs: Path):
        scripts_dir = rootfs / "bootstrap"
        scripts_dir.mkdir(exist_ok=True)

        for name, content in RAMDISK_SCRIPTS.items():
            path = scripts_dir / name
            path.write_text(content)
            path.chmod(0o755)

    def _write_services(self, rootfs: Path, config: RamdiskConfig):
        launchd = rootfs / "System/Library/CoreServices"
        plist = launchd / "stalinra1n.plist"
        plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.stalinra1n.ramdisk</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/bootstrap/install_bootstrap.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>""")

    def _setup_ssh(self, rootfs: Path):
        etc = rootfs / "etc"
        (etc / "ssh").mkdir(parents=True, exist_ok=True)

        sshd_config = etc / "ssh/sshd_config"
        sshd_config.write_text("""Port 22
PermitRootLogin yes
PasswordAuthentication yes
PermitEmptyPasswords yes
UseDNS no
Subsystem sftp /usr/libexec/sftp-server
""")

        if not (rootfs / "etc/master.passwd").exists():
            rootfs.joinpath("etc/master.passwd").write_text(
                "root:*:0:0::0:0:System Administrator:/var/root:/bin/sh\n"
            )

        if not (rootfs / "etc/rc").exists():
            rootfs.joinpath("etc/rc").write_text("""#!/bin/sh
. /etc/rc.common
""")

    def build_dmg(self, rootfs_path: Path, config: RamdiskConfig) -> Optional[Path]:
        import subprocess
        import shutil

        dmg_path = self.work_dir / f"{config.output_name}.dmg"
        if dmg_path.exists():
            dmg_path.unlink()

        size_mb = 200
        log.info(f"Creating DMG ({size_mb} MB)...")

        try:
            result = subprocess.run(
                ["hdiutil", "create", "-size", f"{size_mb}m",
                 "-fs", "HFS+", "-volname", "stalinra1n",
                 "-srcfolder", str(rootfs_path),
                 str(dmg_path)],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                log.error(f"hdiutil failed: {result.stderr}")
                return None

            log.info(f"DMG created: {dmg_path} ({dmg_path.stat().st_size / 1024 / 1024:.0f} MB)")
            return dmg_path

        except FileNotFoundError:
            log.warn("hdiutil not found (macOS only). Creating flat archive instead.")
            return self._build_flat_archive(rootfs_path, config)
        except subprocess.TimeoutExpired:
            log.error("hdiutil timed out")
            return None

    def _build_flat_archive(self, rootfs_path: Path, config: RamdiskConfig) -> Optional[Path]:
        import tarfile

        archive_path = self.work_dir / f"{config.output_name}.tar.gz"
        log.info(f"Creating tar archive: {archive_path}")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(rootfs_path, arcname="")

        log.info(f"Archive created: {archive_path} ({archive_path.stat().st_size / 1024 / 1024:.0f} MB)")
        return archive_path

    def cleanup(self):
        import shutil
        rootfs = self.work_dir / "rootfs"
        if rootfs.exists():
            shutil.rmtree(rootfs)
            log.info("Cleaned up ramdisk rootfs")
