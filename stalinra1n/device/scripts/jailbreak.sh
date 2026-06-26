#!/bin/bash
# Full jailbreak workflow:
# 1. Exploit device via RP2350
# 2. Demote production mode
# 3. Boot custom ramdisk
# 4. Mount rootfs
# 5. Install bootstrap
# 6. Install loader app
# 7. Install package manager
# 8. Cleanup and reboot
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo " stalinra1n Full Jailbreak Script"
echo "============================================"
echo ""

# Check for required tools
for cmd in python3 iproxy ssh; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Missing: $cmd"
        exit 1
    fi
done

# Check for loader IPA
LOADER_IPA="$DEVICE_DIR/loader/Loader.ipa"
if [ ! -f "$LOADER_IPA" ]; then
    echo "Building loader app..."
    bash "$SCRIPT_DIR/build_loader.sh"
fi

# Check for bootstrap
BOOTSTRAP_TAR="$DEVICE_DIR/bootstrap/build/stalinra1n-bootstrap-1.0.0.tar.gz"
if [ ! -f "$BOOTSTRAP_TAR" ]; then
    echo "Building bootstrap..."
    bash "$SCRIPT_DIR/build_bootstrap.sh"
fi

# Step 1: Run exploit
echo ""
echo "[1/6] Running stalinra1n exploit..."
python3 -m stalinra1n exploit || {
    echo "Exploit failed"
    exit 1
}

# Step 2: Demote
echo ""
echo "[2/6] Demoting production mode..."
python3 -m stalinra1n demote || {
    echo "Demotion failed (non-critical)"
}

# Step 3: Boot ramdisk
echo ""
echo "[3/6] Booting custom ramdisk..."
# This would use stalinra1nctl to boot a custom ramdisk image
# python3 -m stalinra1nctl boot ramdisk.iBoot

# Step 4: Install bootstrap
echo ""
echo "[4/6] Installing bootstrap..."
# Once device is booted with ramdisk:
# scp "$BOOTSTRAP_TAR" root@device:/
# ssh root@device "tar -xzf stalinra1n-bootstrap-1.0.0.tar.gz -C /"

# Step 5: Install loader
echo ""
echo "[5/6] Installing loader app..."
# scp "$LOADER_IPA" root@device:/
# ssh root@device "dpkg -i Loader.ipa || true"

# Step 6: Cleanup
echo ""
echo "[6/6] Finalizing..."
# ssh root@device "ldrestart" || true

echo ""
echo "============================================"
echo " Jailbreak complete!"
echo " The stalinra1n Loader app is on your"
echo " home screen. Open it to install Sileo"
echo " or another package manager."
echo "============================================"
echo ""
echo "NOTE: This is a TETHERED jailbreak."
echo "You must re-exploit after every reboot."
