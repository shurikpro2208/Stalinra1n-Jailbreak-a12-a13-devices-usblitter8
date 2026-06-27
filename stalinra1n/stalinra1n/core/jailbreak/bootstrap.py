import os
import shutil
import tarfile
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from ...utils import log


PROCURSUS_URL = "https://github.com/ProcursusTeam/Procursus/releases/latest/download/bootstrap-iphoneos-arm64.tar.gz"
SILEO_DEB_URL = "https://github.com/Sileo/Sileo/releases/latest/download/sileo.deb"
ZEBRA_DEB_URL = "https://apt.binger.xyz/debs/zebra.deb"


@dataclass
class BootstrapConfig:
    version: str = "1.0.0"
    architecture: str = "iphoneos-arm64"
    include_sileo: bool = True
    include_zebra: bool = False
    include_cydia: bool = False
    extra_packages: List[str] = field(default_factory=list)


class BootstrapManager:
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = Path(work_dir or Path.home() / ".stalinra1n" / "bootstrap")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.work_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir = self.work_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

    def download_procursus(self) -> Optional[Path]:
        dest = self.cache_dir / "bootstrap-iphoneos-arm64.tar.gz"
        if dest.exists():
            log.info(f"Procursus bootstrap already cached: {dest}")
            return dest

        log.info("Downloading Procursus bootstrap...")
        try:
            import urllib.request
            urllib.request.urlretrieve(PROCURSUS_URL, dest)
            log.info(f"Downloaded: {dest}")
            return dest
        except Exception as e:
            log.error(f"Failed to download Procursus: {e}")
            log.info("You can manually place bootstrap in: {self.cache_dir}")
            return None

    def download_sileo(self) -> Optional[Path]:
        dest = self.cache_dir / "sileo.deb"
        if dest.exists():
            return dest

        log.info("Downloading Sileo...")
        try:
            import urllib.request
            urllib.request.urlretrieve(SILEO_DEB_URL, dest)
            log.info(f"Downloaded: {dest}")
            return dest
        except Exception as e:
            log.error(f"Failed to download Sileo: {e}")
            return None

    def download_zebra(self) -> Optional[Path]:
        dest = self.cache_dir / "zebra.deb"
        if dest.exists():
            return dest

        log.info("Downloading Zebra...")
        try:
            import urllib.request
            urllib.request.urlretrieve(ZEBRA_DEB_URL, dest)
            log.info(f"Downloaded: {dest}")
            return dest
        except Exception as e:
            log.error(f"Failed to download Zebra: {e}")
            return None

    def build_bootstrap_package(self, config: BootstrapConfig) -> Optional[Path]:
        build_dir = self.output_dir / f"stalinra1n-bootstrap-{config.version}"
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True)

        procursus = self.download_procursus()
        if procursus and procursus.exists():
            log.info("Extracting Procursus bootstrap...")
            with tarfile.open(procursus, "r:gz") as tar:
                tar.extractall(build_dir)
        else:
            log.warn("No Procursus bootstrap available")
            for d in ["usr/bin", "usr/lib", "usr/share", "etc", "Library"]:
                (build_dir / d).mkdir(parents=True, exist_ok=True)

        self._write_version(build_dir, config.version)
        self._write_apt_sources(build_dir)
        self._write_postinst(build_dir)

        pm_count = 0
        if config.include_sileo:
            sileo = self.download_sileo()
            if sileo:
                shutil.copy2(sileo, build_dir / "sileo.deb")
                pm_count += 1

        if config.include_zebra:
            zebra = self.download_zebra()
            if zebra:
                shutil.copy2(zebra, build_dir / "zebra.deb")
                pm_count += 1

        output_path = self.output_dir / f"stalinra1n-bootstrap-{config.version}.tar.gz"
        if output_path.exists():
            output_path.unlink()

        log.info(f"Creating bootstrap archive ({pm_count} PM(s))...")
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(build_dir, arcname="bootstrap")

        size_mb = output_path.stat().st_size / 1024 / 1024
        log.info(f"Bootstrap package created: {output_path.name} ({size_mb:.1f} MB)")
        return output_path

    def _write_version(self, build_dir: Path, version: str):
        (build_dir / "version.txt").write_text(
            f"stalinra1n bootstrap v{version}\n"
            f"Built: 2026\n"
            f"Exploit: usbliter8\n"
            f"Architecture: arm64e\n"
        )

    def _write_apt_sources(self, build_dir: Path):
        apt_dir = build_dir / "etc/apt/sources.list.d"
        apt_dir.mkdir(parents=True, exist_ok=True)

        (apt_dir / "sileo.sources").write_text("""Types: deb
URIs: https://repo.chariz.com/
Suites: ./
Components:
""")
        (apt_dir / "procursus.sources").write_text("""Types: deb
URIs: https://repo.procursus.com/
Suites: ./
Components:
""")

    def _write_postinst(self, build_dir: Path):
        postinst = build_dir / "postinst.sh"
        postinst.write_text("""#!/bin/bash
# stalinra1n bootstrap post-install
echo "Running stalinra1n bootstrap post-install..."

# Install package managers
for deb in /bootstrap/*.deb; do
    if [ -f "$deb" ]; then
        echo "Installing: $(basename $deb)"
        dpkg -i "$deb" 2>/dev/null || true
    fi
done

# Update APT
apt-get update 2>/dev/null || true

# Fix uicache for loader app
uicache -a 2>/dev/null || true

echo "stalinra1n bootstrap installed successfully!"
""")
        postinst.chmod(0o755)
