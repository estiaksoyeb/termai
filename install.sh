#!/bin/bash

# Define paths
INSTALL_DIR="$HOME/.programs/termai"
BIN_DIR="$PREFIX/bin"
SOURCE_FILE="termai.py"

# Colors
BLUE="\033[1;34m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${BLUE}[+] Starting Termai Installer...${RESET}"

# 1. Check for Termux environment
if [ -z "$PREFIX" ]; then
    echo "Warning: This script is designed for Termux. Proceeding anyway..."
fi

# 2. Install Dependencies
echo -e "${YELLOW}[*] Installing dependencies (python, requests)...${RESET}"
pkg install python -y &> /dev/null

# Check if requests is installed before trying to install it
if ! pip show requests &> /dev/null; then
    echo "    'requests' not found. Installing..."
    pip install requests &> /dev/null
else
    echo "    'requests' is already installed."
fi

# 3. Create Hidden Program Directory
echo -e "${YELLOW}[*] Creating installation directory: $INSTALL_DIR${RESET}"
mkdir -p "$INSTALL_DIR"

# 4. Move Source Code
if [ -f "$SOURCE_FILE" ]; then
    cp "$SOURCE_FILE" "$INSTALL_DIR/"
    echo "    Source copied."
else
    echo -e "${RED}[!] Error: $SOURCE_FILE not found in current folder.${RESET}"
    exit 1
fi

# 5. Create Binary Alias ('ai')
echo -e "${YELLOW}[*] Creating 'ai' command in $BIN_DIR...${RESET}"
echo '#!/bin/bash' > "$BIN_DIR/ai"
echo "python \"$INSTALL_DIR/$SOURCE_FILE\" \"\$@\"" >> "$BIN_DIR/ai"
chmod +x "$BIN_DIR/ai"

# 6. Verify Installation
if command -v ai &> /dev/null; then
    echo -e "${GREEN}[✓] Termai installed successfully!${RESET}"
    echo "    Type 'ai \"hello\"' to start."
    echo "    Type 'ai --help' to see commands."
else
    echo -e "${RED}[!] Installation failed. 'ai' command not found.${RESET}"
    exit 1
fi

# 7. Safe Cleanup (Interactive)
echo ""
echo -e "${BLUE}[?] Do you want to delete this installation folder to save space?${RESET}"
echo -e "    (This deletes the repo you just cloned, NOT the installed tool)"
read -p "    Delete? [y/N]: " confirm

if [[ "$confirm" =~ ^[yY]$ ]]; then
    CURRENT_DIR_NAME=$(basename "$PWD")
    
    # SAFETY CHECK: Only delete if the folder is named 'termai'
    if [[ "$CURRENT_DIR_NAME" == "termai" ]]; then
        echo -e "${YELLOW}[*] Cleaning up...${RESET}"
        cd ..
        rm -rf "$CURRENT_DIR_NAME"
        echo -e "${GREEN}[✓] Cleaned up. Enjoy Termai!${RESET}"
    else
        echo -e "${RED}[!] Safety Stop: Current folder is named '$CURRENT_DIR_NAME', not 'termai'.${RESET}"
        echo "    Cleanup aborted to prevent accidental deletion of wrong files."
    fi
else
    echo -e "${GREEN}[✓] Setup complete. Files kept.${RESET}"
fi
