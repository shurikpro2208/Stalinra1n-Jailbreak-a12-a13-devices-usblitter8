import struct
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

from ...utils import log


@dataclass
class iBootPatch:
    offset: int
    original: bytes
    patch: bytes
    description: str = ""
    soc: str = "all"


KNOWN_PATCHES: Dict[str, List[iBootPatch]] = {
    "disable_sigcheck": [
        iBootPatch(
            offset=-1, original=b"", patch=b"",
            description="Disables iBoot signature verification",
            soc="all",
        ),
    ],
    "allow_custom_bootargs": [
        iBootPatch(
            offset=-1, original=b"", patch=b"",
            description="Allows arbitrary boot-args",
            soc="all",
        ),
    ],
    "debug_enabled": [
        iBootPatch(
            offset=-1, original=b"", patch=b"",
            description="Enables iBoot serial debug output",
            soc="all",
        ),
    ],
    "skip_fsck": [
        iBootPatch(
            offset=-1, original=b"", patch=b"",
            description="Skips filesystem check on boot",
            soc="all",
        ),
    ],
}


KNOWN_BOOTARGS = [
    "rd=md0",              # boot from ramdisk
    "debug=0x14e",         # enable all debug
    "-v",                  # verbose boot
    "keepsyms=1",          # keep kernel symbols
    "amfi=0x0",            # disable AMFI (needs patch)
    "amfi_get_out_of_my_way=1",  # alternative AMFI bypass
    "cs_enforcement_disable=1",  # disable code signing
    "msgbuf=1048576",      # larger kernel log buffer
]


class iBootPatcher:
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = Path(work_dir or Path.home() / ".stalinra1n" / "iboot")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._patches_applied: List[str] = []

    def download_ipsw(self, device: str, ios_version: str) -> Optional[Path]:
        import urllib.request
        import json
        import plistlib

        url = (
            f"https://api.ipsw.me/v2.1/{device}/{ios_version}/url"
        )
        log.info(f"Fetching IPSW URL for {device} iOS {ios_version}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "stalinra1n"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                ipsw_url = data.get("url")
                if not ipsw_url:
                    log.error("No IPSW URL in response")
                    return None
        except Exception as e:
            log.error(f"Failed to get IPSW URL: {e}")
            log.info("Falling back to manual IPSW download")
            return None

        dest = self.work_dir / f"{device}_{ios_version}.ipsw"
        if dest.exists():
            log.info(f"IPSW already cached: {dest}")
            return dest

        log.info(f"Downloading IPSW ({ipsw_url})...")
        log.info("This may take several minutes (4-6 GB)")
        try:
            urllib.request.urlretrieve(ipsw_url, dest)
            log.info(f"IPSW downloaded: {dest}")
            return dest
        except Exception as e:
            log.error(f"Download failed: {e}")
            return None

    def extract_iboot(self, ipsw_path: Path) -> Optional[Path]:
        import zipfile
        import shutil

        log.info(f"Extracting iBoot from {ipsw_path.name}...")
        extract_dir = self.work_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)

        try:
            with zipfile.ZipFile(ipsw_path, "r") as zf:
                iboot_files = [
                    n for n in zf.namelist()
                    if "iBoot" in n and not n.endswith(".manifest") and not n.endswith(".plist")
                ]
                if not iboot_files:
                    log.warn("No iBoot found in IPSW")
                    log.info("Files in IPSW root:")
                    for n in zf.namelist()[:30]:
                        log.info(f"  {n}")
                    return None

                iboot_name = iboot_files[0]
                log.info(f"Found: {iboot_name}")
                zf.extract(iboot_name, extract_dir)
                iboot_path = extract_dir / iboot_name
                log.info(f"Extracted to {iboot_path}")
                return iboot_path
        except zipfile.BadZipFile:
            log.error("Invalid IPSW file")
            return None

    def apply_patch(self, iboot_path: Path, patch_name: str) -> bool:
        patches = KNOWN_PATCHES.get(patch_name)
        if not patches:
            log.error(f"Unknown patch: {patch_name}")
            return False

        data = bytearray(iboot_path.read_bytes())
        applied = 0

        for patch in patches:
            if patch.offset == -1:
                log.warn(f"Patch '{patch_name}' has no offset defined")
                log.info("  Jailbreak community needs to find the offset for iBoot")
                log.info(f"  Description: {patch.description}")
                continue

            if patch.offset + len(patch.patch) > len(data):
                log.warn(f"Patch offset {patch.offset:#x} out of range")
                continue

            current = data[patch.offset:patch.offset + len(patch.original)]
            if current != patch.original:
                log.warn(f"Patch at {patch.offset:#x}: unexpected bytes")
                log.info(f"  Expected: {patch.original.hex()}")
                log.info(f"  Found:    {current.hex()}")
                continue

            data[patch.offset:patch.offset + len(patch.patch)] = patch.patch
            applied += 1

        if applied > 0:
            patched_path = iboot_path.parent / f"{iboot_path.name}.patched"
            patched_path.write_bytes(bytes(data))
            log.info(f"Applied {applied} patch(es) to {patched_path.name}")
            self._patches_applied.append(patch_name)
            return True
        else:
            log.warn(f"No patches applied for '{patch_name}'")
            return False

    def save_patch_definition(self, name: str, patches: List[iBootPatch]):
        KNOWN_PATCHES[name] = patches
        patch_file = self.work_dir / f"patch_{name}.json"
        import json
        data = []
        for p in patches:
            data.append({
                "offset": p.offset,
                "original": p.original.hex(),
                "patch": p.patch.hex(),
                "description": p.description,
                "soc": p.soc,
            })
        patch_file.write_text(json.dumps(data, indent=2))
        log.info(f"Patch definition saved: {patch_file}")

    def load_patch_definition(self, name_or_path: str) -> Optional[List[iBootPatch]]:
        if name_or_path in KNOWN_PATCHES:
            return KNOWN_PATCHES[name_or_path]

        path = Path(name_or_path)
        if path.exists():
            import json
            try:
                data = json.loads(path.read_text())
                patches = []
                for d in data:
                    patches.append(iBootPatch(
                        offset=d["offset"],
                        original=bytes.fromhex(d["original"]),
                        patch=bytes.fromhex(d["patch"]),
                        description=d.get("description", ""),
                        soc=d.get("soc", "all"),
                    ))
                return patches
            except Exception as e:
                log.error(f"Failed to load patch: {e}")
                return None
        return None

    @property
    def patches_applied(self) -> List[str]:
        return list(self._patches_applied)
