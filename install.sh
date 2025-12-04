#!/bin/bash

# Define paths
INSTALL_DIR="$HOME/.programs/termai"
BIN_DIR="$PREFIX/bin"
SOURCE_FILE="termai.py"

echo -e "\033[1;34m[+] Starting Termai Installer...\033[0m"

# 1. Check for Termux environment
if [ -z "$PREFIX" ]; then
    echo "Warning: This script is designed for Termux. Proceeding anyway..."
fi

# 2. Install Dependencies
echo -e "\033[1;33m[*] Installing dependencies (python, requests)...\033[0m"
pkg install python -y
pip install requests

# 3. Create Hidden Program Directory
echo -e "\033[1;33m[*] Creating installation directory: $INSTALL_DIR\033[0m"
mkdir -p "$INSTALL_DIR"

# 4. Move Source Code
if [ -f "$SOURCE_FILE" ]; then
    cp "$SOURCE_FILE" "$INSTALL_DIR/"
    echo "    Source copied."
else
    echo -e "\033[1;31m[!] Error: $SOURCE_FILE not found in current folder.\033[0m"
    exit 1
fi

# 5. Create Binary Alias ('ai')
echo -e "\033[1;33m[*] Creating 'ai' command in $BIN_DIR...\033[0m"
echo '#!/bin/bash' > "$BIN_DIR/ai"
echo "python \"$INSTALL_DIR/$SOURCE_FILE\" \"\$@\"" >> "$BIN_DIR/ai"
chmod +x "$BIN_DIR/ai"

# 6. Verify Installation
if command -v ai &> /dev/null; then
    echo -e "\033[1;32m[✓] Termai installed successfully!\033[0m"
    echo "    Type 'ai \"hello\"' to start."
    echo "    Type 'ai --help' to see commands."
else
    echo -e "\033[1;31m[!] Installation failed. 'ai' command not found.\033[0m"
    exit 1
fi
