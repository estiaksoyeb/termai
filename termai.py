import os
import sys
import json
import requests
import subprocess
from pathlib import Path

# --- Configuration Paths ---
APP_NAME = "termai"
DATA_DIR = Path.home() / ".local/share" / APP_NAME
# We now use a JSON file for all settings
CONFIG_FILE = DATA_DIR / "config.json"
# Legacy file path for migration
OLD_KEY_FILE = DATA_DIR / "key"

# --- Colors ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# --- Default Settings ---
# If the config file is deleted/missing, these values are used to recreate it.
DEFAULT_CONFIG = {
    "provider": "gemini",
    "proxy": "",
    "gemini_config": {
        "api_key": "",
        "model_name": "gemini-2.5-flash",
        "system_instruction": (
            "You are a CLI assistant specific to Termux. "
            "Do NOT use Markdown. Do NOT use backticks. "
            "Do NOT use bolding. Just write plain text. "
            "Keep answers concise."
        ),
        "generation_config": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "maxOutputTokens": 1024
        }
    },
    "openai_config": {
        "api_key": "",
        "model_name": "gpt-4o",
        "system_instruction": "You are a helpful assistant.",
        "temperature": 0.7,
        "max_tokens": 1024
    }
}

def load_config():
    """
    Loads config.json. 
    Handles migration from old 'key' file and old flat config structure if needed.
    Creates default file if missing.
    """
    # Ensure directory exists
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    config = {}
    # 1. Check for Config File
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"[Error] Your config file ({CONFIG_FILE}) is invalid JSON.")
            print("Please fix it or delete it to reset defaults.")
            sys.exit(1)

        # Migration from old flat structure to new nested structure
        if "api_key" in config:
            print(f"[{APP_NAME}] Migrating config to new nested structure...")
            new_config = DEFAULT_CONFIG.copy()
            # Preserve old top-level keys
            new_config["proxy"] = config.get("proxy", "")
            
            # Move gemini-specific keys
            new_config["gemini_config"]["api_key"] = config.get("api_key", "")
            new_config["gemini_config"]["model_name"] = config.get("model_name", DEFAULT_CONFIG["gemini_config"]["model_name"])
            new_config["gemini_config"]["system_instruction"] = config.get("system_instruction", DEFAULT_CONFIG["gemini_config"]["system_instruction"])
            new_config["gemini_config"]["generation_config"] = config.get("generation_config", DEFAULT_CONFIG["gemini_config"]["generation_config"])
            
            with open(CONFIG_FILE, "w") as f:
                json.dump(new_config, f, indent=4)
            print("Migration complete.")
            return new_config

        return config

    # If no config file exists, proceed with first run setup
    # 2. Migration: If no config, check for old key file
    gemini_api_key = ""
    backup_file = DATA_DIR / "key.bak"
    if OLD_KEY_FILE.exists():
        print(f"[{APP_NAME}] Migrating legacy key file to new config format...")
        with open(OLD_KEY_FILE, "r") as f:
            gemini_api_key = f.read().strip()
        OLD_KEY_FILE.rename(backup_file)
        
    # 3. First Run Setup
    if not gemini_api_key:
        if sys.stdin.isatty(): # Only prompt if interactive
            print(f"[{APP_NAME}] First run! Enter your Gemini API Key. Get it from aistudio.google.com")
            gemini_api_key = input("Gemini API Key: ").strip()
            if not gemini_api_key:
                print("Error: Gemini key cannot be empty.")
                sys.exit(1)
        else:
            return None
    
    # Prompt for OpenAI key (optional)
    openai_api_key = ""
    if sys.stdin.isatty():
        print(f"[{APP_NAME}] (Optional) Enter your OpenAI API Key. Get it from platform.openai.com")
        openai_api_key = input("OpenAI API Key (press Enter to skip): ").strip()

    # 4. Create new Config Dictionary
    new_config = DEFAULT_CONFIG.copy()
    new_config["gemini_config"]["api_key"] = gemini_api_key
    new_config["openai_config"]["api_key"] = openai_api_key
    
    # Save it
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_config, f, indent=4)
    
    print(f"Configuration saved to {CONFIG_FILE}\n")

    # Clean up the legacy key backup file if it exists after migration
    if backup_file.exists():
         backup_file.unlink()

    return new_config

import shutil # Import shutil to check for editor availability

# ... (rest of the file remains the same until open_editor)

def open_editor():
    """
    Opens the config file in the user's preferred editor with a fallback mechanism.
    Priority: $EDITOR > vim > nano
    """
    # 1. Prioritize the user's explicit choice
    editor = os.getenv('EDITOR')

    # 2. If no $EDITOR, try to find 'vim'
    if not editor and shutil.which('vim'):
        editor = 'vim'
    
    # 3. If still no editor, fall back to 'nano'
    if not editor:
        editor = 'nano'

    print(f"Opening config in {editor}...")
    try:
        subprocess.call([editor, str(CONFIG_FILE)])
    except FileNotFoundError:
        print(f"[Error] Editor '{editor}' not found. Please install it or set the $EDITOR environment variable.")
        return 1
    return 0 # Return 0 for success


def print_help():
    """Prints the help menu with available commands."""
    print(f"\n{GREEN}Termai - Termux AI Assistant{RESET}")
    print(f"A lightweight CLI tool for Gemini AI integration in Termux.\n")
    
    print(f"{YELLOW}Usage:{RESET}")
    print(f"  ai [OPTIONS] \"YOUR QUERY\"")
    print(f"  cat file.txt | ai [OPTIONS] \"OPTIONAL PROMPT\"")
    
    print(f"\n{YELLOW}Options:{RESET}")
    print(f"  {CYAN}--config{RESET}      Open configuration file (Edit API key, Model, Proxy, Prompts)")
    print(f"  {CYAN}--debug{RESET}       Enable debug mode (Show raw status codes and errors)")
    print(f"  {CYAN}--help, -h{RESET}    Show this help message")
    
    print(f"\n{YELLOW}Examples:{RESET}")
    print(f"  ai \"How do I unzip a tar file?\"")
    print(f"  ai --config")
    print(f"  cat error.log | ai \"Explain this error briefly\"")
    return 0 # Return 0 for success instead of sys.exit(0)

def send_gemini_request(config, user_input, debug_mode):
    # Prepare Variables from Config
    gemini_config = config.get("gemini_config", {})
    api_key = gemini_config.get("api_key")
    model_name = gemini_config.get("model_name", "gemini-2.5-flash")
    system_instr = gemini_config.get("system_instruction", "")
    gen_config = gemini_config.get("generation_config", {})
    proxy = config.get("proxy", "")

    # Construct URL dynamically
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    # 4. Payload Construction
    payload = {
        "contents": [{"parts": [{"text": user_input}]}],
        "systemInstruction": {"parts": [{"text": system_instr}]},
        "generationConfig": gen_config
    }

    if debug_mode: print(f"[Debug] Provider: Gemini | Model: {model_name} | Temp: {gen_config.get('temperature')} | Proxy: {proxy if proxy else 'None'}")

    # 5. Send Request
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.post(api_url, json=payload, proxies=proxies)
        
        if debug_mode:
            print(f"[Debug] Status: {response.status_code}")

        if response.status_code != 200:
            print(f"\n[Error {response.status_code}]")
            print(response.text)
            return 1 # Return non-zero for error

        data = response.json()
        
        # Safety Check
        if "promptFeedback" in data and "blockReason" in data["promptFeedback"]:
            print(f"[Blocked] Reason: {data['promptFeedback']['blockReason']}")
            return 0 # Blocked is not an error, just no content

        # Output
        if "candidates" in data and data["candidates"]:
            # Check for content existence
            cand = data["candidates"][0]
            if "content" in cand and "parts" in cand["content"] and cand["content"]["parts"]:
                # GREEN OUTPUT HERE
                print(f"{GREEN}{cand['content']['parts'][0]['text'].strip()}{RESET}")
            else:
                print("[No content returned]")
                if debug_mode: print(data)
        else:
            print("[Error] Invalid response format from Gemini")
            if debug_mode: print(data)
        return 0 # Success
    except Exception as e:
        print(f"\n[Connection Error] {e}")
        return 1 # Error

def send_openai_request(config, user_input, debug_mode):
    # Prepare Variables from Config
    openai_config = config.get("openai_config", {})
    api_key = openai_config.get("api_key")
    model_name = openai_config.get("model_name", "gpt-4o")
    system_instr = openai_config.get("system_instruction", "")
    temperature = openai_config.get("temperature", 0.7)
    max_tokens = openai_config.get("max_tokens", 1024)
    proxy = config.get("proxy", "")

    # Construct URL dynamically
    api_url = "https://api.openai.com/v1/chat/completions"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Payload Construction
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instr},
            {"role": "user", "content": user_input}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    if debug_mode: print(f"[Debug] Provider: OpenAI | Model: {model_name} | Temp: {temperature} | Proxy: {proxy if proxy else 'None'}")

    # 5. Send Request
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.post(api_url, headers=headers, json=payload, proxies=proxies)
        
        if debug_mode:
            print(f"[Debug] Status: {response.status_code}")

        if response.status_code != 200:
            print(f"\n[Error {response.status_code}]")
            print(response.text)
            return 1 # Return non-zero for error

        data = response.json()
        
        # Output
        if "choices" in data and data["choices"]:
            message = data["choices"][0].get("message", {})
            content = message.get("content", "")
            if content:
                # GREEN OUTPUT HERE
                print(f"{GREEN}{content.strip()}{RESET}")
            else:
                print("[No content returned]")
                if debug_mode: print(data)
        else:
            print("[Error] Invalid response format from OpenAI")
            if debug_mode: print(data)
        return 0 # Success
    except Exception as e:
        print(f"\n[Connection Error] {e}")
        return 1 # Error


def cli_entry_point():
    # 0. Load Configuration (Variables System)
    config = load_config()

    # If config could not be loaded and it's not interactive, exit with error
    if config is None and not sys.stdin.isatty():
        return 1

    # 1. Handle Flags
    if "--help" in sys.argv or "-h" in sys.argv:
        return print_help()

    if "--config" in sys.argv:
        return open_editor()

    debug_mode = "--debug" in sys.argv
    # Filter flags out of arguments so they don't get sent to the AI
    args = [arg for arg in sys.argv[1:] if arg not in ["--debug", "--config", "--help", "-h"]]

    # 2. Input Handling
    user_input = ""
    if not sys.stdin.isatty():
        # Handle Piped Input (e.g., cat file | ai)
        user_input = sys.stdin.read().strip()
        if args: user_input += "\n" + " ".join(args)
    elif args:
        # Handle Standard Arguments (e.g., ai "query")
        user_input = " ".join(args)
    else:
        # No input provided, show help
        return print_help()

    # 3. Get provider and send request
    provider = config.get("provider", "gemini")
    if provider == "gemini":
        return send_gemini_request(config, user_input, debug_mode)
    elif provider == "openai":
        return send_openai_request(config, user_input, debug_mode)
    else:
        print(f"[Error] Invalid provider '{provider}' in config.json. Use 'gemini' or 'openai'.")
        return 1


def main():
    sys.exit(cli_entry_point())

if __name__ == "__main__":
    main()
