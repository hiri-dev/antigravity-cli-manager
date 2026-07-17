#!/usr/bin/env bash

set -euo pipefail

BIN_DIR="$HOME/.local/bin"
DEST="$BIN_DIR/acm"

echo "Installing Antigravity CLI Manager (acm)..."

mkdir -p "$BIN_DIR"

if [[ ! -f "$(dirname "$0")/credentials.py" ]]; then
    cat << 'EOF' > "$(dirname "$0")/credentials.py"
import base64
SEC_B64 = 'R0NTUFgtSzU4RldSNDg2TGRMSjFtTEI4c1hDNHo2cURBZg=='
def get_client_secret() -> str:
    return base64.b64decode(SEC_B64).decode('utf-8')
CLIENT_ID = '1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com'
USER_AGENT = 'vscode/1.X.X (Antigravity/4.2.4)'
EOF
fi

cp -f "$(dirname "$0")/acm" "$DEST"
cp -f "$(dirname "$0")/acm_helper.py" "$BIN_DIR/acm_helper.py"
cp -f "$(dirname "$0")/credentials.py" "$BIN_DIR/credentials.py"
chmod +x "$DEST"
chmod +x "$BIN_DIR/acm_helper.py"
chmod +x "$BIN_DIR/credentials.py"

PROFILES_DIR="$HOME/.config/acm/profiles"
TOKEN_PATH="$HOME/.gemini/antigravity-cli/antigravity-oauth-token"
AGY_PID_FILE="$HOME/.config/acm/agy.pid"

if [[ -t 0 ]]; then
    if [[ ! -d "$PROFILES_DIR" || -z "$(find "$PROFILES_DIR" -name "*.json" 2>/dev/null)" ]]; then
        echo "No accounts saved yet. Starting OAuth login flow..."
        rm -f "$AGY_PID_FILE"
        (
            while [[ ! -f "$TOKEN_PATH" ]]; do
                if [[ -f "$AGY_PID_FILE" ]]; then
                    read -r AGY_PID < "$AGY_PID_FILE"
                    if [[ -n "$AGY_PID" ]] && ! kill -0 "$AGY_PID" 2>/dev/null; then
                        exit 0
                    fi
                fi
                sleep 0.5
            done
            sleep 0.2
            if [[ -f "$AGY_PID_FILE" ]]; then
                read -r AGY_PID < "$AGY_PID_FILE"
                kill -TERM "$AGY_PID" 2>/dev/null
            fi
        ) &
        WATCHER_PID=$!
        
        AGY_PID_FILE="$AGY_PID_FILE" bash -c 'echo $$ > "$AGY_PID_FILE"; exec agy' || true
        
        kill -TERM "$WATCHER_PID" 2>/dev/null || true
        rm -f "$AGY_PID_FILE"
        
        if [[ -f "$TOKEN_PATH" ]]; then
            email=$(python3 "$BIN_DIR/acm_helper.py" get_email "$TOKEN_PATH" 2>/dev/null || echo "")
            email=$(echo "$email" | sed 's/[^a-zA-Z0-9@._+-]/_/g')
            if [[ -z "$email" ]]; then
                email="account_$(date +%s)"
            fi
            mkdir -p "$PROFILES_DIR"
            cp "$TOKEN_PATH" "$PROFILES_DIR/${email}.json"
            echo "[+] Account '${email}' successfully saved!"
            python3 "$BIN_DIR/acm_helper.py" refresh "$PROFILES_DIR/${email}.json" 3 >/dev/null 2>&1 &
        else
            echo "[-] Login failed or token not found."
        fi
    fi
fi

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
