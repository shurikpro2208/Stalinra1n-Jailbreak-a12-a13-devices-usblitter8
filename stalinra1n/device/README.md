# stalinra1n Device-Side Components

This directory contains everything that runs **on the iOS device** post-exploitation.

## Structure

```
device/
├── loader/              # Loader app (appears on home screen)
│   ├── LoaderApp.swift  # SwiftUI app
│   ├── Info.plist       # App metadata
│   └── Package.swift    # Swift package config
├── bootstrap/           # Bootstrap package
│   ├── build/           # Built bootstrap artifacts
│   └── reinstall.sh     # On-device reinstall script
└── scripts/             # Build and deployment scripts
    ├── build_loader.sh      # Build loader with Theos
    ├── build_bootstrap.sh   # Build bootstrap tar
    └── jailbreak.sh         # Full jailbreak workflow
```

## How it works

1. **Exploit** (via RP2350) → device enters PWND state
2. **Demote** → production mode disabled (temporary)
3. **Boot ramdisk** → custom iOS ramdisk with SSH
4. **Install** → copy files over SSH:
   - Bootstrap (`/bootstrap/`)
   - Loader app (`/Applications/`)
   - Package manager (Sileo/Zebra/Cydia)
5. **Cleanup** → reboot userspace, loader appears on springboard

## Building

### Loader App
Requires [Theos](https://theos.dev) on macOS:
```bash
bash device/scripts/build_loader.sh
```

### Bootstrap
Works on any platform:
```bash
bash device/scripts/build_bootstrap.sh
```

### Full Workflow
```bash
bash device/scripts/jailbreak.sh
```

## Tethered Note

stalinra1n is a **tethered** exploit. After every reboot:
1. Re-enter DFU mode
2. Re-run exploit via RP2350
3. Re-demote
4. Re-boot custom iBoot
5. Device will be jailbroken again

The loader app and bootstrap persist on the rootfs, but the kernel patches
are lost on reboot until re-exploited.
