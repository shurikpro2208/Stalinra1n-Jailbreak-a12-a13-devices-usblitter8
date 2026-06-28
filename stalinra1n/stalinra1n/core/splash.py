import struct
from pathlib import Path
from typing import Optional, Tuple

from ..utils import log


DEVICE_RESOLUTIONS = {
    "d321": (828, 1792),
    "d331": (1125, 2436),
    "d331p": (1242, 2688),
    "d421": (828, 1792),
    "d431": (1125, 2436),
    "d431p": (1242, 2688),
    "j421": (1668, 2224),
    "j410": (1536, 2048),
    "j471": (1620, 2160),
    "j121": (3840, 2160),
    "t8006": (272, 340),
}


SPLASH_PATH = str(Path(__file__).parent.parent.parent / "stalinra1n_splashscreen.png")
SPLASH_DIR = Path.home() / ".stalinra1n" / "splash"


def rgba_to_rgb565(r: int, g: int, b: int) -> int:
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def load_image(image_path: str, target_size: Optional[Tuple[int, int]] = None) -> Optional[bytes]:
    try:
        from PIL import Image
    except ImportError:
        log.error("Pillow not installed. Run: pip install Pillow")
        return None

    path = Path(image_path)
    if not path.exists():
        log.error(f"Image not found: {image_path}")
        return None

    try:
        img = Image.open(path).convert("RGBA")
    except Exception as e:
        log.error(f"Failed to load image: {e}")
        return None

    w, h = img.size
    if target_size:
        tw, th = target_size
        if (w, h) != (tw, th):
            img = img.resize((tw, th), Image.LANCZOS)

    pixels = list(img.getdata())
    raw = bytearray(len(pixels) * 2)

    for i, (r, g, b, a) in enumerate(pixels):
        struct.pack_into("<H", raw, i * 2, rgba_to_rgb565(r, g, b))

    return bytes(raw)


def save_splash_image(image_path: str, output_name: str = "splash.raw") -> Optional[Path]:
    SPLASH_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = SPLASH_DIR / output_name
    data = load_image(image_path)
    if data is None:
        return None
    raw_path.write_bytes(data)
    from PIL import Image
    img = Image.open(image_path)
    w, h = img.size
    log.info(f"Saved raw splash: {raw_path} ({w}x{h}, {len(data)/1024:.0f} KB)")
    return raw_path


def get_screen_resolution(chip_id: str) -> Tuple[int, int]:
    for model, res in DEVICE_RESOLUTIONS.items():
        if model in chip_id.lower():
            return res
    return (1125, 2436)


def send_via_usb(image_data: bytes) -> bool:
    try:
        import usb.core
        import usb.util
    except ImportError:
        log.error("pyusb not installed. Run: pip install pyusb")
        return False

    device = usb.core.find(idVendor=0x05AC)
    if device is None:
        log.error("No Apple device found. Ensure device is connected and in PWND mode.")
        return False

    log.info(f"Device found: 0x{device.idVendor:04x}:0x{device.idProduct:04x}")

    try:
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0)
        device.set_configuration()
    except usb.core.USBError as e:
        log.warn(f"USB init: {e}")

    try:
        chunk_size = 16384
        total = len(image_data)
        offset = 0
        while offset < total:
            chunk = image_data[offset:offset + chunk_size]
            try:
                device.ctrl_transfer(
                    bmRequestType=0x40,
                    bRequest=0x05,
                    wValue=offset & 0xFFFF,
                    wIndex=(offset >> 16) & 0xFFFF,
                    data_or_wLength=chunk,
                    timeout=10000,
                )
            except usb.core.USBError:
                device.ctrl_transfer(
                    bmRequestType=0x40,
                    bRequest=0x04,
                    wValue=offset & 0xFFFF,
                    wIndex=(offset >> 16) & 0xFFFF,
                    data_or_wLength=chunk,
                    timeout=10000,
                )
            offset += len(chunk)
            pct = min(100, offset * 100 // total)
            log.info(f"Splash: {pct}%")

        log.info("Splash screen sent to device!")
        return True

    except usb.core.USBError as e:
        log.error(f"USB send failed: {e}")
        return False
    finally:
        usb.util.dispose_resources(device)


def show_splash(image_path: str, chip_id: str = "") -> bool:
    target = get_screen_resolution(chip_id) if chip_id else None

    raw_data = load_image(image_path, target_size=target)
    if raw_data is None:
        return False

    if target:
        log.info(f"Target: {target[0]}x{target[1]}")
    log.info(f"Data: {len(raw_data)} bytes ({len(raw_data)/1024:.0f} KB)")

    return send_via_usb(raw_data)
