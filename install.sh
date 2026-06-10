#!/bin/bash

# Define paths
INSTALL_DIR="$HOME/.programs/termai"
if [ -n "$PREFIX" ]; then
    BIN_DIR="$PREFIX/bin"
else
    BIN_DIR="$HOME/.local/bin"
    # Ensure standard local bin directory exists and warn if not in PATH
    mkdir -p "$BIN_DIR"
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "\033[1;33m[*] Note: $BIN_DIR is not in your PATH. You may need to add it to ~/.bashrc or ~/.zshrc\033[0m"
    fi
fi
SOURCE_FILE="termai.py"

# Colors
BLUE="\033[1;34m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${BLUE}[+] Starting Termai Installer...${RESET}"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[!] Error: Python is not installed. Please install Python 3.${RESET}"
    exit 1
fi

# 1. Install Dependencies
echo -e "${YELLOW}[*] Installing dependencies (python, requests)...${RESET}"

# Check if requests is installed before trying to install it
if ! $PYTHON_CMD -c "import requests" &> /dev/null; then
    echo "    'requests' not found. Installing..."
    $PYTHON_CMD -m pip install requests &> /dev/null || $PYTHON_CMD -m pip install requests --break-system-packages &> /dev/null
else
    echo "    'requests' is already installed."
fi

# 2. Create Hidden Program Directory
echo -e "${YELLOW}[*] Creating installation directory: $INSTALL_DIR${RESET}"
mkdir -p "$INSTALL_DIR"

# 4. Move Source Code
if [ -f "$SOURCE_FILE" ]; then
    cp "$SOURCE_FILE" "$INSTALL_DIR/"
    echo "    Source copied."
else
    echo -e "${YELLOW}[*] Source $SOURCE_FILE not found locally. Downloading from GitHub...${RESET}"
    if command -v curl &> /dev/null; then
        curl -fsSL "https://raw.githubusercontent.com/estiaksoyeb/termai/master/termai.py" -o "$INSTALL_DIR/$SOURCE_FILE"
    elif command -v wget &> /dev/null; then
        wget -qO "$INSTALL_DIR/$SOURCE_FILE" "https://raw.githubusercontent.com/estiaksoyeb/termai/master/termai.py"
    else
        echo -e "${RED}[!] Error: Neither curl nor wget is installed. Cannot download source files.${RESET}"
        exit 1
    fi
    echo "    Source downloaded successfully."
fi

# 5. Create Binary Alias ('ai')
echo -e "${YELLOW}[*] Creating 'ai' command in $BIN_DIR...${RESET}"
echo '#!/bin/bash' > "$BIN_DIR/ai"
echo "$PYTHON_CMD \"$INSTALL_DIR/$SOURCE_FILE\" \"\$@\"" >> "$BIN_DIR/ai"
chmod +x "$BIN_DIR/ai"

# 6. Verify Installation
if command -v ai &> /dev/null; then
    echo -e "${GREEN}[✓] Termai installed successfully!${RESET}"
    echo "    Type 'ai \"hello\"' to start."
    echo "    Type 'ai --help' to see commands."
elif [ -f "$BIN_DIR/ai" ]; then
    echo -e "${GREEN}[✓] Termai installed successfully at $BIN_DIR/ai!${RESET}"
    echo -e "${YELLOW}[!] However, $BIN_DIR is not in your PATH.${RESET}"
    echo "    To run it anywhere, add this to your ~/.bashrc or ~/.zshrc:"
    echo "    export PATH=\"\$PATH:$BIN_DIR\""
    echo "    After adding, restart your terminal or run: source ~/.bashrc"
else
    echo -e "${RED}[!] Installation failed. 'ai' command not found.${RESET}"
    exit 1
fi

# 7. Setup Auto-completion
echo -e "${YELLOW}[*] Setting up shell auto-completion...${RESET}"
if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "_ai_completion" "$HOME/.bashrc"; then
        echo "    Adding completion to ~/.bashrc..."
        echo -e "\n# Termai auto-completion\nsource <(\"$BIN_DIR/ai\" completion bash)" >> "$HOME/.bashrc"
    fi
fi
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "_ai_completion" "$HOME/.zshrc"; then
        echo "    Adding completion to ~/.zshrc..."
        echo -e "\n# Termai auto-completion\nsource <(\"$BIN_DIR/ai\" completion zsh)" >> "$HOME/.zshrc"
    fi
fi

# 8. Safe Cleanup (Interactive)
if [ -f "$SOURCE_FILE" ]; then
    echo ""
    echo -e "${BLUE}[?] Do you want to delete this installation folder to save space?${RESET}"
    echo -e "    (This deletes the repo you just cloned, NOT the installed tool)"
    read -p "    Delete? [y/N]: " confirm

    if [[ "$confirm" =~ ^[yY]$ ]]; then
        CURRENT_DIR_NAME=$(basename "$PWD")
        
        # Enable case-insensitive matching
        shopt -s nocasematch
        
        # SAFETY CHECK: Only delete if the folder is named 'termai' (case-insensitive)
        if [[ "$CURRENT_DIR_NAME" == "termai" ]]; then
            echo -e "${YELLOW}[*] Cleaning up...${RESET}"
            cd ..
            rm -rf "$CURRENT_DIR_NAME"
            echo -e "${GREEN}[✓] Cleaned up. Enjoy Termai!${RESET}"
        else
            echo -e "${RED}[!] Safety Stop: Current folder is named '$CURRENT_DIR_NAME', not 'termai'.${RESET}"
            echo "    Cleanup aborted to prevent accidental deletion of wrong files."
        fi
        
        # Disable case-insensitive matching
        shopt -u nocasematch
    else
        echo -e "${GREEN}[✓] Setup complete. Files kept.${RESET}"
    fi
else
    echo ""
    echo -e "${GREEN}[✓] Setup complete. Enjoy Termai!${RESET}"
fi
