# stalinra1n Loader App

iOS app that appears on the home screen after jailbreaking with stalinra1n.

## Features

- Package manager installer (Sileo, Zebra, Cydia)
- Bootstrap management
- System info viewer
- Jailbreak tool launcher

## Building

Requires macOS with Xcode 14+ and Theos (https://theos.dev) for ARM64 cross-compilation.

```bash
# Using Theos (recommended for jailbreak devices)
git clone https://github.com/theos/theos.git
export THEOS=~/theos
make package

# Or using Swift toolchain directly
swift build -c release
```

## Deployment

The built `.ipa` or `.deb` gets deployed to the device during post-exploitation
via the custom USB request handler. The loader installs the bootstrap and
package manager onto the rootfilesystem.

## Dependencies

- Theos or Xcode toolchain
- ldid (for code signing with iOS entitlements)
