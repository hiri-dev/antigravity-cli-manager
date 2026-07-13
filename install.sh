#!/usr/bin/env bash

set -euo pipefail

BIN_DIR="$HOME/.local/bin"
DEST="$BIN_DIR/acm"

echo "Installing Antigravity CLI Manager (acm)..."

mkdir -p "$BIN_DIR"

cp -f "$(dirname "$0")/acm" "$DEST"
cp -f "$(dirname "$0")/acm_helper.py" "$BIN_DIR/acm_helper.py"
cp -f "$(dirname "$0")/credentials.py" "$BIN_DIR/credentials.py"
chmod +x "$DEST"
chmod +x "$BIN_DIR/acm_helper.py"
chmod +x "$BIN_DIR/credentials.py"

echo "[+] Successfully installed acm to $DEST"

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "WARNING: $BIN_DIR is not in your PATH."
    echo "To run 'acm' from anywhere, add the following line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "──────────────────────────────────────────────────"
echo "  Installation complete! To launch the manager:"
echo "  Simply run: acm"
echo "──────────────────────────────────────────────────"
