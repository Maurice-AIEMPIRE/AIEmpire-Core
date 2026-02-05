#!/usr/bin/env bash
set -euo pipefail

APP_NAME="AgentMonitor"
ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT/build"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
BIN_DIR="$APP_DIR/Contents/MacOS"

/bin/mkdir -p "$BIN_DIR"

MODULE_CACHE="$BUILD_DIR/ModuleCache"
/bin/mkdir -p "$MODULE_CACHE"

/usr/bin/swiftc -O -framework Cocoa -module-cache-path "$MODULE_CACHE" "$ROOT/Sources/main.swift" -o "$BIN_DIR/$APP_NAME"

/bin/cp "$ROOT/Info.plist" "$APP_DIR/Contents/Info.plist"

/usr/bin/codesign --force --deep --sign - "$APP_DIR" >/dev/null 2>&1 || true

/bin/echo "Built: $APP_DIR"
