from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class Payload:
    name: str
    description: str
    path: str
    payload_type: str
    size: int = 0


def discover_payloads(payload_dir: Optional[str] = None) -> List[Payload]:
    if payload_dir is None:
        payload_dir = _default_payload_dir()

    payload_dir_path = Path(payload_dir)
    if not payload_dir_path.exists():
        return []

    payloads = []
    for f in payload_dir_path.iterdir():
        if f.is_file() and f.suffix in (".img4", ".raw", ".iBoot", ".bin", ".im4p", ".dmg"):
            payloads.append(Payload(
                name=f.stem,
                description=f"",
                path=str(f),
                payload_type=f.suffix.lstrip("."),
                size=f.stat().st_size,
            ))
    return payloads


def _default_payload_dir() -> str:
    from pathlib import Path
    return str(Path.home() / ".usbliter8" / "payloads")
