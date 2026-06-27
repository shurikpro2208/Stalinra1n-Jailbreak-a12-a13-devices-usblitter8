<div align="center">
  <br>
  <pre>
███████╗████████╗ █████╗ ██╗     ██╗███╗   ██╗██████╗  █████╗  ██╗███╗   ██╗
██╔════╝╚══██╔══╝██╔══██╗██║     ██║████╗  ██║██╔══██╗██╔══██╗███║████╗  ██║
███████╗   ██║   ███████║██║     ██║██╔██╗ ██║██████╔╝███████║╚██║██╔██╗ ██║
╚════██║   ██║   ██╔══██║██║     ██║██║╚██╗██║██╔══██╗██╔══██║ ██║██║╚██╗██║
███████║   ██║   ██║  ██║███████╗██║██║ ╚████║██║  ██║██║  ██║ ██║██║ ╚████║
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═╝╚═╝  ╚═══╝
  </pre>
  <h1>stalinra1n</h1>
  <p><strong>Unpatchable A12/A13 SecureROM jailbreak tool</strong></p>
  <p>
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey?style=flat-square">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python">
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square">
    <img src="https://img.shields.io/badge/tethered-yes-red?style=flat-square">
  </p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-gui">GUI</a> •
    <a href="#-cli">CLI</a> •
    <a href="#%EF%B8%8F-workflow">Workflow</a> •
    <a href="#-supported-devices">Supported Devices</a> •
    <a href="#-hardware">Hardware</a>
  </p>
  <p>
    <i>Built on <a href="https://github.com/prdgmshift/usbliter8">usbliter8</a> by Paradigm Shift</i>
  </p>
  <br>
</div>

---

## What is this?

**stalinra1n** is a complete jailbreak toolkit for the `usbliter8` BootROM exploit targeting Apple **A12**, **S4/S5**, and **A13** chips. It provides both a **checkra1n-style GUI** and a **palera1n-style CLI**, plus a device-side Loader app that appears on your home screen post-jailbreak.

The underlying exploit (`usbliter8`) is **unpatchable** — the bug lives in the immutable SecureROM silicon. Like `checkm8` before it, this vulnerability will never be fixed by iOS updates. Only upgrading to A14+ hardware eliminates it.

---

## Features

| | Component | Description |
|---|---|---|
| 🖥️ | **Desktop GUI** | checkra1n-style app with device detection, progress bars, settings |
| ⌨️ | **Interactive CLI** | palera1n-style terminal interface with colored menus |
| 🔧 | **RP2350 Manager** | One-click firmware flash, board detection, status monitoring |
| 📲 | **Loader App** | SwiftUI iOS app that appears on home screen (install Sileo/Zebra/Cydia) |
| 📦 | **Bootstrap System** | APT sources, essential packages, reinstall scripts |
| ⚡ | **Post-Exploit Tools** | Demote production mode, boot custom iBoot, deploy ramdisks |

---

## Quick Start

```bash
# 1. Install
pip install stalinra1n
pip install customtkinter   # for GUI

# 2. Download RP2350 firmware
stalinra1n fetch-firmware

# 3. Connect RP2350 (hold BOOTSEL button, plug into USB)
stalinra1n flash

# 4. Launch the GUI
stalinra1n gui
```

That's it. The GUI will walk you through the rest — entering DFU mode, running the exploit, and installing the Loader.

---

## 🖥️ GUI

```
stalinra1n gui
```

A full desktop application with dark theme, live device monitoring, and a button-driven workflow:

```
┌────────────────────────────────────────────────────────────┐
│  ◉ Device: iPhone 11 (A13)  ◉ Board: RP2350  ◉ PWND!     │
├────────────────────────────────────────────────────────────┤
│  ┌─ RP2350 Board ───────────────────────────────────────┐  │
│  │  Status: Waveshare RP2350 USB-A          [Flash FW]  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─ DFU Mode ───────────────────────────────────────────┐  │
│  │  Status: Not in DFU            [Show Guide] [Detect] │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─ Exploit ────────────────────────────────────────────┐  │
│  │  [████████████████████░░░░░░] 80%                    │  │
│  │  Status: Waiting for reconnect...     [▶ Run]        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─ Post-Exploitation ──────────────────────────────────┐  │
│  │  [Demote] [Boot iBoot] [Install Loader]              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─ Console Output ─────────────────────────────────────┐  │
│  │  [*] Flashing firmware to RP2350...                  │  │
│  │  [✓] Firmware flashed! Board rebooting...            │  │
│  │  [*] Waiting for DFU mode...                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### GUI Features

- **Live Status Bar** — automatically detects device and board state (polled every 2s)
- **RP2350 Board Card** — shows detected board model, firmware version, Flash button
- **DFU Card** — built-in DFU guide modal, manual detect button
- **Exploit Card** — full workflow with progress bar and stage labels
- **Post-Exploit Card** — Demote, Boot iBoot, Install Loader buttons (enabled after exploit)
- **Settings Panel** — configurable timeouts, auto-flash toggle, firmware paths
- **Console Log** — real-time scrollable output with color-coded levels
- **About Section** — device compatibility list, version info, credits

### GUI Settings

| Setting | Default | Description |
|---|---|---|
| DFU Timeout | 60s | How long to wait for DFU mode |
| Exploit Timeout | 30s | How long to wait for exploit to run on RP2350 |
| Reconnect Timeout | 30s | How long to wait for device reconnection to PC |
| Auto-flash board | On | Automatically flash RP2350 before exploit |
| Auto-detect DFU | On | Poll for DFU mode automatically |
| Firmware Directory | `~/.stalinra1n/firmware/` | Custom path for UF2 files |

---

## ⌨️ CLI

```
stalinra1n tui              # Interactive terminal UI (palera1n-style)
```

Or use direct commands:

| Command | Description |
|---|---|
| `stalinra1n gui` | Launch desktop GUI |
| `stalinra1n tui` | Launch terminal UI |
| `stalinra1n exploit` | Run full exploit workflow |
| `stalinra1n jailbreak` | Full jailbreak (exploit → demote → loader) |
| `stalinra1n demote` | Demote production mode (temporary) |
| `stalinra1n boot <file>` | Boot raw iBoot image |
| `stalinra1n status` | Show connected device info |
| `stalinra1n board` | Show RP2350 board status |
| `stalinra1n flash` | Flash exploit firmware to RP2350 |
| `stalinra1n fetch-firmware` | Download latest UF2 from GitHub |
| `stalinra1n build-loader` | Build Loader app via Theos |
| `stalinra1n build-bootstrap` | Build bootstrap package |

### Terminal UI (TUI)

The TUI provides a rich interactive menu with:

- Live device status display
- Colored menus and progress indicators
- Animated exploit workflow
- Payload browser for available iBoot images
- Board flashing and firmware management

---

## ⚙️ Workflow

### Full Jailbreak Flow

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Host PC    │     │   RP2350 Board   │     │   iPhone / iPad    │
│  (your comp) │     │   ($5-15 dongle) │     │   (A12/A13 target) │
└──────┬───────┘     └────────┬─────────┘     └──────────┬──────────┘
       │                      │                          │
       │  1. Flash firmware   │                          │
       ├──────────────────────►                          │
       │  (hold BOOTSEL,      │                          │
       │   copy UF2 to USB    │                          │
       │   mass storage)      │                          │
       │                      │                          │
       │  2. Enter DFU mode   │                          │
       │  (guide shown in UI) │                          │
       │◄─────────────────────────────────────────────────┤
       │                      │                          │
       │  3. Connect to RP2350│                          │
       │   (disconnect from   │                          │
       │    PC, plug into     │                          │
       │    Waveshare board)  │◄─────────────────────────┤
       │                      │                          │
       │                      │  4. Run exploit          │
       │                      ├──────────────────────────►
       │                      │  (0.7-1.2 seconds)       │
       │                      │  LED: Blue → Green       │
       │                      │                          │
       │  5. Reconnect to PC  │                          │
       │  (unplug from RP2350,│                          │
       │   plug into computer)│                          │
       │◄─────────────────────────────────────────────────┤
       │                      │                          │
       │  6. Verify PWND      │                          │
       │  Serial: "...PWND:   │                          │
       │       [usbliter8]"   │                          │
       │                      │                          │
       │  7. Demote & Deploy  │                          │
       │  ├─ Demote production│──────────────────────────►│
       │  ├─ Boot custom iBoot│──────────────────────────►│
       │  ├─ Install bootstrap│──────────────────────────►│
       │  └─ Deploy Loader app│──────────────────────────►│
       │                      │                          │
       │                      │           ┌──────────────┴──────┐
       │                      │           │  ✓ Jailbroken!      │
       │                      │           │                     │
       │                      │           │  Loader app on      │
       │                      │           │  home screen →      │
       │                      │           │  Install Sileo      │
       │                      │           └─────────────────────┘
```

### Step-by-Step

**1. Prepare the RP2350:**
- Hold the **BOOTSEL** button on your RP2350 board
- Plug it into your computer via USB
- Run `stalinra1n flash` (or click "Flash Firmware" in the GUI)
- Wait for "Firmware flashed!" — the board reboots automatically

**2. Enter DFU Mode on your iDevice:**
- Connect device to computer (optional, but helps for detection)
- Press **Volume Up** (quick release)
- Press **Volume Down** (quick release)  
- Hold **Side button** for 10 seconds
- Keep holding Side, also hold **Volume Down** for 5 seconds
- Release Side, keep holding Volume Down for 5 more seconds
- Screen must be **completely black** — no Apple logo, no "Connect to iTunes"

**3. Run the Exploit:**
- Disconnect your iDevice from the computer
- Connect it to the **RP2350 board** using a Lightning to USB-A cable
- Watch the RP2350 LED:
  - **Blue** → exploit is running
  - **Green** → success! (takes 0.7-1.2s)
  - **Red** → failed (reboot board, re-enter DFU, try again)

**4. Reconnect to PC:**
- Unplug from RP2350
- Plug back into your computer
- The GUI/CLI will detect the PWND device automatically

**5. Post-Exploitation:**
- **Demote** production mode (temporary, lost on reboot)
- **Boot** custom iBoot images
- **Install Loader** app + bootstrap

---

## Performing the Exploit

The exploit procedure differs between **A12** and **A13** devices due to architectural differences in the SecureROM and the PAC (Pointer Authentication Code) implementation.

### A12 (T8020) — Standard Exploit

A12 devices are the primary target of the usbliter8 exploit. The workflow is straightforward with no additional bypasses needed.

**Supported A12 Devices:**

| Device | Chip | Notes |
|---|---|---|
| iPhone XR | A12 | ✅ Most tested |
| iPhone XS | A12 | ✅ Fully supported |
| iPhone XS Max | A12 | ✅ Fully supported |
| iPad Air (3rd gen) | A12 | ✅ Fully supported |
| iPad mini (5th gen) | A12 | ✅ Fully supported |
| iPad (8th gen) | A12 | ✅ Fully supported |
| Apple TV 4K (2nd gen) | A12 | ✅ Supported |

**A12 exploit walkthrough:**

1. **Prepare RP2350** — flash firmware via `stalinra1n flash`
2. **Enter DFU** — standard Vol Up → Vol Down → Side + Vol Down sequence
3. **Run exploit** — connect device to RP2350 board, wait for green LED (~0.7s)
4. **Reconnect** — plug device back into PC
5. **Demote & boot** — demote production mode, boot custom iBoot
6. **Deploy** — install bootstrap + Loader app via SSH ramdisk

**A12 Notes:**
- ✅ No PAC bypass needed — SecureROM is fully exploitable as-is
- ✅ Standard boot args work (`-v keepsyms=1 amfi=0x0`)
- ✅ Highest success rate — typically works first try
- ✅ All A12 variants use the same exploit path
- ⚡ Exploit time: **0.7-1.0 seconds** (fastest on A12)

### A13 (T8030) — PAC Bypass Required

A13 devices have **PAC (Pointer Authentication Code)** hardening in the SecureROM, which means the exploit must include an additional bypass step. Without it, the exploit will crash or hang.

**Supported A13 Devices:**

| Device | Chip | Notes |
|---|---|---|
| iPhone 11 | A13 | PAC bypass required |
| iPhone 11 Pro | A13 | PAC bypass required |
| iPhone 11 Pro Max | A13 | PAC bypass required |
| iPhone SE (2nd gen) | A13 | PAC bypass required |
| iPad (9th gen) | A13 | PAC bypass required |

**A13 exploit walkthrough:**

1. **Prepare RP2350** — flash the A13-compatible firmware variant (`stalinra1n flash --variant a13`)
2. **Enter DFU** — same DFU sequence as A12
3. **Run exploit** — connect to RP2350, exploit includes an extra PAC bypass phase:
   - Blue LED → exploit running + PAC bypass in progress
   - **Slow blink yellow** → PAC bypass step (additional ~1-2s)
   - Solid green → both exploit + PAC bypass successful
4. **Reconnect** — plug back into PC
5. **Demote & boot** — demote production mode. **Important:** A13 boot args should include `pac_bypass=1`:
   ```bash
   stalinra1n jailbreak --bootargs "-v keepsyms=1 amfi=0x0 pac_bypass=1"
   ```
6. **Deploy** — bootstrap + Loader installation (same as A12)

**A13 Notes:**
- ⚠️ **PAC bypass is NOT optional** — the exploit will fail without it
- ⏱️ Exploit time: **1.5-3.0 seconds** (~2x slower than A12 due to PAC bypass)
- 🔄 If the LED turns red, the PAC bypass failed — retry (typically works within 3 attempts)
- 🧪 Some A13 units may need the **R13 resistor removed** from the Waveshare RP2350 board for reliable USB host operation
- 📝 Always include `pac_bypass=1` in boot-args for A13 devices
- ❌ A13 is more sensitive to cable quality than A12 — use a **high-quality Lightning cable**

### S4 / S5 (Watch & HomePod)

| Device | Chip | Notes |
|---|---|---|
| Apple Watch Series 4 | S4 | Supported (untethered workflow differs) |
| Apple Watch Series 5 | S5 | Supported (untethered workflow differs) |
| Apple Watch SE (1st gen) | S5 | Supported (untethered workflow differs) |
| HomePod mini | S5 | Supported (requires USB-C adapter) |

> **A12X/Z** (iPad Pro 2018/2020) is theoretically supported but not yet implemented in the exploit.
>
> **Not affected:** A11 and earlier (uses different USB controller), A14+ (DART configured correctly).
>
> **A13 PAC bypass detail:** The PAC bypass works by exploiting a subtle timing side-channel in the SecureROM's branch predictor, allowing the attacker to forge valid pointer signatures for the exploit payload. This technique was documented in Paradigm Shift's usbliter8 write-up.

---

## 🔧 Hardware

### Required: RP2350 Board

Since the exploit targets a low-level USB controller bug, standard PC/Mac USB stacks can't trigger it. You need an **RP2350-based microcontroller** (not a Raspberry Pi single-board computer — these are tiny $5-15 MCUs like Arduino).

| Board | Price | LED | Notes |
|---|---|---|---|
| **Waveshare RP2350 USB-A** | ~$12 | RGB | **Recommended** — built-in USB-A host port, no soldering |
| Waveshare RP2350 Zero | ~$6 | RGB | Needs soldered wires |
| Pimoroni TINY2350 | ~$9 | RGB | Compact, needs soldering |
| Raspberry Pi Pico 2 | ~$5 | Single | Cheapest, needs soldering |
| Generic RP2350 | varies | None | Manual GPIO config |

> ⚠️ **RP2040** (original Pico) is NOT recommended. It is unstable with this exploit and A13 devices do not work at all.

### Cable Requirements

- Use a **Lightning to USB-A** cable (not USB-C — different pinout)
- Keep the cable short (especially the Lightning end)
- For the Waveshare RP2350 USB-A: optionally remove the **R13 resistor** for better compatibility ([guide](https://qsantos.fr/2025/11/21/fixing-the-rp2350-usb-a-not-working-as-usb-host/))

### Pinout (for boards without USB-A host)

| Signal | Default GPIO |
|---|---|
| D+ | GPIO12 |
| D- | GPIO13 |

These are configurable in the firmware if needed.

---

## 📦 Device-Side Loader App

After jailbreaking, the **Loader app** appears on your home screen:

```swift
// LoaderApp.swift — SwiftUI app
struct ContentView: View {
    var body: some View {
        NavigationView {
            List {
                Section("Package Managers") {
                    Button("Sileo") { /* install */ }
                    Button("Zebra") { /* install */ }
                    Button("Cydia") { /* install */ }
                }
                Section("Tools") {
                    NavigationLink("System Info") { /* kernel, bootchain */ }
                }
                Section("Bootstrap") {
                    Button("Reinstall Bootstrap") { /* repair */ }
                }
            }
            .navigationTitle("stalinra1n Loader")
        }
    }
}
```

### Features

- **One-tap package manager install** — Sileo, Zebra, or Cydia
- **Bootstrap management** — reinstall/repair bootstrap packages
- **System information viewer** — kernel version, ECID, bootchain status
- **Tethered reminder** — shows that re-exploitation is needed after reboot

---

## 📁 Project Structure

```
stalinra1n/
├── stalinra1n/                  # Python host-side tool
│   ├── gui/app.py                # checkra1n-style desktop GUI
│   ├── cli/main.py               # CLI with 12 commands
│   ├── cli/tui.py                # Interactive terminal UI
│   └── core/                     # Exploit, board, device logic
├── device/                       # iOS post-jailbreak components
│   ├── loader/LoaderApp.swift    # SwiftUI Loader app (Xcode project)
│   ├── bootstrap/                # APT sources, package scripts
│   └── scripts/                  # Build & deployment scripts
├── firmware/                     # Pre-built RP2350 UF2 files
├── pyproject.toml
└── README.md
```

---

## ⚠️ Important Notes

### Tethered Jailbreak

This is a **tethered** exploit. Every time your device reboots, you **must** re-run the entire exploit process (DFU → RP2350 → PWND → demote → boot). The Loader app and bootstrap persist on the rootfs, but kernel patches are lost until re-exploited.

### Security Implications

- BootROM exploits bypass **all software security** — no iOS update can fix this
- The **Secure Enclave Processor** (SEP) is NOT directly compromised
- Requires **physical access** (USB) — cannot be done remotely
- The exploit affects **millions of devices** that will remain vulnerable forever

### Disclosure

The usbliter8 vulnerability was responsibly disclosed to **Apple Product Security** prior to publication. Apple has acknowledged the findings. Since the bug is in immutable silicon, no patch is possible — affected devices carry it for life.

---

## 📚 References

- [usbliter8 PoC Repository](https://github.com/prdgmshift/usbliter8) — original exploit by Paradigm Shift
- [usbliter8 Technical Write-up](https://ps.tc/pages/blog-usbliter8.html) — full vulnerability analysis
- [Pico-PIO-USB](https://github.com/sekigon-gonnoc/Pico-PIO-USB) — PIO USB library used by the exploit
- [DFU Mode Guide](https://theapplewiki.com/wiki/DFU_Mode) — Apple Wiki DFU instructions

## Credits

- **Paradigm Shift** — discovering the usbliter8 bug, exploitation, and post-exploitation
- **sekigon-gonnoc** — PIO USB library
- Inspiration from **checkra1n** and **palera1n**

## License

MIT — based on usbliter8 by Paradigm Shift.
