#!/bin/bash
# Build the loader app for iOS using Theos
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOADER_DIR="$(dirname "$SCRIPT_DIR")/loader"
OUTPUT_DIR="$LOADER_DIR/build"

echo "==> stalinra1n Loader App Builder"
echo ""

# Check for Theos
if [ -z "${THEOS:-}" ]; then
    if [ -d "$HOME/theos" ]; then
        export THEOS="$HOME/theos"
    elif [ -d "/opt/theos" ]; then
        export THEOS="/opt/theos"
    else
        echo "Theos not found. Set THEOS env var or install it:"
        echo "  git clone https://github.com/theos/theos.git ~/theos"
        exit 1
    fi
fi

echo "Using Theos: $THEOS"
echo ""

# Create Makefile if not present
if [ ! -f "$LOADER_DIR/Makefile" ]; then
    cat > "$LOADER_DIR/Makefile" << 'MAKEEOF'
include $(THEOS)/makefiles/common.mk

TOOL_NAME = stalinra1n_loader
stalinra1n_loader_FILES = main.m
stalinra1n_loader_CFLAGS = -fobjc-arc
stalinra1n_loader_CODESIGN_FLAGS = -S entitlements.plist

include $(THEOS_MAKE_PATH)/tool.mk
MAKEEOF
    echo "Created Makefile"
fi

# Create basic main.m if not present
if [ ! -f "$LOADER_DIR/main.m" ]; then
    cat > "$LOADER_DIR/main.m" << 'MAINEOF'
#import <UIKit/UIKit.h>

int main(int argc, char *argv[]) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, @"LoaderAppDelegate");
    }
}
MAINEOF
    echo "Created main.m"
fi

# Build
cd "$LOADER_DIR"
make package

echo ""
echo "Build complete! Package in:"
echo "  $LOADER_DIR/packages/"
ls -la "$LOADER_DIR/packages/" 2>/dev/null || echo "  (check build output)"
