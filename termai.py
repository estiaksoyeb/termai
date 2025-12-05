import os
import sys
import json
import requests
import subprocess
from pathlib import Path
import copy # Import copy for deepcopy
import shutil # Import shutil to check for editor availability

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
            new_config = copy.deepcopy(DEFAULT_CONFIG)
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
    new_config = copy.deepcopy(DEFAULT_CONFIG)
    if sys.stdin.isatty():
        print(f"[{APP_NAME}] First run! Choose your primary AI provider.")
        provider = ""
        while provider not in ["1", "2"]:
            provider = input("Enter 1 for Gemini or 2 for OpenAI: ").strip()

        if provider == "1":
            new_config["provider"] = "gemini"
            if not gemini_api_key:
                print(f"[{APP_NAME}] Enter your Gemini API Key. Get it from aistudio.google.com")
                gemini_api_key = input("Gemini API Key: ").strip()
                if not gemini_api_key:
                    print("Error: Gemini key cannot be empty.")
                    sys.exit(1)
            new_config["gemini_config"]["api_key"] = gemini_api_key
        
        elif provider == "2":
            new_config["provider"] = "openai"
            print(f"[{APP_NAME}] Enter your OpenAI API Key. Get it from platform.openai.com")
            openai_api_key = input("OpenAI API Key: ").strip()
            if not openai_api_key:
                print("Error: OpenAI key cannot be empty.")
                sys.exit(1)
            new_config["openai_config"]["api_key"] = openai_api_key
    else:
        # Default to Gemini if non-interactive and no config exists
        # This part might need adjustment based on desired non-interactive behavior
        if not gemini_api_key:
             return None # Cannot proceed without an API key
        new_config["gemini_config"]["api_key"] = gemini_api_key

    # Save the new configuration
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_config, f, indent=4)
    
    print(f"Configuration saved to {CONFIG_FILE}\n")

    # Clean up the legacy key backup file if it exists after migration
    if backup_file.exists():
         backup_file.unlink()

    return new_config

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
    print(f"  {CYAN}--config{RESET}        Open configuration file")
    print(f"  {CYAN}--debug{RESET}         Enable debug mode")
    print(f"  {CYAN}--debug-config{RESET}  Print the loaded configuration (redacts keys)")
    print(f"  {CYAN}--help, -h{RESET}      Show this help message")
    print(f"  {CYAN}--reinstall{RESET}    Re-run the first-time setup")
    
    print(f"\n{YELLOW}Examples:{RESET}")
    print(f"  ai \"How do I unzip a tar file?\"")
    print(f"  ai --config")
    print(f"  cat error.log | ai \"Explain this error briefly\"")
    return 0 # Return 0 for success

def send_gemini_request(config, user_input, debug_mode):
    # ... (existing code for send_gemini_request)
    gemini_config = config.get("gemini_config", {})
    api_key = gemini_config.get("api_key")
    model_name = gemini_config.get("model_name", "gemini-2.5-flash")
    system_instr = gemini_config.get("system_instruction", "")
    gen_config = gemini_config.get("generation_config", {})
    proxy = config.get("proxy", "")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": user_input}]}],
        "systemInstruction": {"parts": [{"text": system_instr}]},
        "generationConfig": gen_config
    }
    if debug_mode: print(f"[Debug] Provider: Gemini | Model: {model_name} | Temp: {gen_config.get('temperature')} | Proxy: {proxy if proxy else 'None'}")
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.post(api_url, json=payload, proxies=proxies)
        if debug_mode:
            print(f"[Debug] Status: {response.status_code}")
        if response.status_code != 200:
            if response.status_code == 429:
                print(f"\n[Error 429] You have exceeded your Gemini API quota.")
                print("Please check your usage and billing details at aistudio.google.com.")
            else:
                print(f"\n[Error {response.status_code}]")
                print(response.text)
            return 1
        data = response.json()
        if "promptFeedback" in data and "blockReason" in data["promptFeedback"]:
            print(f"[Blocked] Reason: {data['promptFeedback']['blockReason']}")
            return 0
        if "candidates" in data and data["candidates"]:
            cand = data["candidates"][0]
            if "content" in cand and "parts" in cand["content"] and cand["content"]["parts"]:
                print(f"{GREEN}{cand['content']['parts'][0]['text'].strip()}{RESET}")
            else:
                print("[No content returned]")
                if debug_mode: print(data)
        else:
            print("[Error] Invalid response format from Gemini")
            if debug_mode: print(data)
        return 0
    except Exception as e:
        print(f"\n[Connection Error] {e}")
        return 1

def send_openai_request(config, user_input, debug_mode):
    # ... (existing code for send_openai_request)
    openai_config = config.get("openai_config", {})
    api_key = openai_config.get("api_key")
    model_name = openai_config.get("model_name", "gpt-4o")
    system_instr = openai_config.get("system_instruction", "")
    temperature = openai_config.get("temperature", 0.7)
    max_tokens = openai_config.get("max_tokens", 1024)
    proxy = config.get("proxy", "")
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
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
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.post(api_url, headers=headers, json=payload, proxies=proxies)
        if debug_mode:
            print(f"[Debug] Status: {response.status_code}")
        if response.status_code != 200:
            if response.status_code == 429:
                print(f"\n[Error 429] You have exceeded your OpenAI API quota.")
                print("Please check your usage and billing details at platform.openai.com.")
            else:
                print(f"\n[Error {response.status_code}]")
                print(response.text)
            return 1
        data = response.json()
        if "choices" in data and data["choices"]:
            message = data["choices"][0].get("message", {})
            content = message.get("content", "")
            if content:
                print(f"{GREEN}{content.strip()}{RESET}")
            else:
                print("[No content returned]")
                if debug_mode: print(data)
        else:
            print("[Error] Invalid response format from OpenAI")
            if debug_mode: print(data)
        return 0
    except Exception as e:
        print(f"\n[Connection Error] {e}")
        return 1

def cli_entry_point():
    # Handle --reinstall flag first
    if "--reinstall" in sys.argv:
        if CONFIG_FILE.exists():
            print(f"[{APP_NAME}] Deleting existing config for reinstall...")
            CONFIG_FILE.unlink()
        else:
            print(f"[{APP_NAME}] No existing config found. Starting first-time setup...")
    
    config = load_config()
    
    if "--reinstall" in sys.argv:
        print(f"[{APP_NAME}] Reinstall complete.")
        return 0

    # Handle --debug-config flag
    if "--debug-config" in sys.argv:
        if not config:
            print("[Error] No configuration file found. Run `ai --reinstall` to create one.")
            return 1
        
        debug_config = copy.deepcopy(config)
        if "gemini_config" in debug_config and "api_key" in debug_config["gemini_config"]:
            key = debug_config["gemini_config"]["api_key"]
            debug_config["gemini_config"]["api_key"] = f"***{key[-4:]}" if key else ""
        if "openai_config" in debug_config and "api_key" in debug_config["openai_config"]:
            key = debug_config["openai_config"]["api_key"]
            debug_config["openai_config"]["api_key"] = f"***{key[-4:]}" if key else ""
            
        print(json.dumps(debug_config, indent=4))
        return 0

    if config is None and not sys.stdin.isatty():
        return 1
    
    if "--help" in sys.argv or "-h" in sys.argv:
        return print_help()

    if "--config" in sys.argv:
        return open_editor()

    debug_mode = "--debug" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg not in ["--debug", "--config", "--help", "-h", "--reinstall", "--debug-config"]]

    user_input = ""
    if not sys.stdin.isatty():
        user_input = sys.stdin.read().strip()
        if args: user_input += "\n" + " ".join(args)
    elif args:
        user_input = " ".join(args)
    else:
        return print_help()

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