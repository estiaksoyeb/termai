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
if sys.stdout.isatty():
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BG_USER = "\033[48;5;99m\033[38;5;255m"
    BG_HEADER = "\033[48;5;24m\033[38;5;255m"
else:
    GREEN = ""
    CYAN = ""
    YELLOW = ""
    RED = ""
    BLUE = ""
    RESET = ""
    BG_USER = ""
    BG_HEADER = ""

# --- Default Settings ---
# If the config file is deleted/missing, these values are used to recreate it.
DEFAULT_CONFIG = {
    "active_profile": "gemini-default",
    "profiles": {
        "gemini-default": {
            "provider": "gemini",
            "api_key": "",
            "model_name": "gemini-2.5-flash",
            "system_instruction": "You are a CLI assistant for command-line users. Answer concisely and use clear formatting. Use standard Markdown for headers, bolding, bullet points, and code blocks.",
            "generation_config": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "maxOutputTokens": 1024
            }
        },
        "openai-default": {
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model_name": "gpt-4o",
            "system_instruction": "You are a CLI assistant for command-line users. Answer concisely and use clear formatting. Use standard Markdown for headers, bolding, bullet points, and code blocks.",
            "temperature": 0.7,
            "max_tokens": 1024
        }
    },
    "proxy": ""
}

def load_config():
    """
    Loads config.json. 
    Handles migration from old nested structure and creates default file if missing.
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

        # Migration from old static structure to profile-based structure
        if "profiles" not in config:
            print(f"[{APP_NAME}] Migrating config to profile-based structure...")
            old_provider = config.get("provider", "gemini")
            old_proxy = config.get("proxy", "")
            
            new_config = copy.deepcopy(DEFAULT_CONFIG)
            new_config["proxy"] = old_proxy
            
            if "gemini_config" in config:
                new_config["profiles"]["gemini-default"] = {
                    "provider": "gemini",
                    "api_key": config["gemini_config"].get("api_key", ""),
                    "model_name": config["gemini_config"].get("model_name", "gemini-2.5-flash"),
                    "system_instruction": config["gemini_config"].get("system_instruction", DEFAULT_CONFIG["profiles"]["gemini-default"]["system_instruction"]),
                    "generation_config": config["gemini_config"].get("generation_config", DEFAULT_CONFIG["profiles"]["gemini-default"]["generation_config"])
                }
            
            if "openai_config" in config:
                new_config["profiles"]["openai-default"] = {
                    "provider": "openai",
                    "base_url": config["openai_config"].get("base_url", "https://api.openai.com/v1"),
                    "api_key": config["openai_config"].get("api_key", ""),
                    "model_name": config["openai_config"].get("model_name", "gpt-4o"),
                    "system_instruction": config["openai_config"].get("system_instruction", DEFAULT_CONFIG["profiles"]["openai-default"]["system_instruction"]),
                    "temperature": config["openai_config"].get("temperature", 0.7),
                    "max_tokens": config["openai_config"].get("max_tokens", 1024)
                }
            
            if old_provider == "openai":
                new_config["active_profile"] = "openai-default"
            else:
                new_config["active_profile"] = "gemini-default"
                
            config = new_config
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            print("Migration complete.")
            return new_config

        # Modernize profiles to have base_url if they are openai provider and missing base_url
        updated = False
        if "profiles" in config:
            for p_name, p_config in config["profiles"].items():
                if p_config.get("provider") == "openai" and "base_url" not in p_config:
                    p_config["base_url"] = "https://api.openai.com/v1"
                    updated = True
                
                # Check for restrictive legacy system instruction
                sys_instr = p_config.get("system_instruction", "")
                if "Do NOT use Markdown" in sys_instr or "Do NOT use backticks" in sys_instr:
                    if p_config.get("provider") == "gemini":
                        p_config["system_instruction"] = DEFAULT_CONFIG["profiles"]["gemini-default"]["system_instruction"]
                    else:
                        p_config["system_instruction"] = DEFAULT_CONFIG["profiles"]["openai-default"]["system_instruction"]
                    updated = True
        
        if updated:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)

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
    if sys.stdin.isatty() and "--complete" not in sys.argv:
        print(f"[{APP_NAME}] First run! Choose your primary AI provider.")
        provider = ""
        while provider not in ["1", "2"]:
            provider = input("Enter 1 for Gemini or 2 for OpenAI: ").strip()

        if provider == "1":
            new_config["active_profile"] = "gemini-default"
            if not gemini_api_key:
                print(f"[{APP_NAME}] Enter your Gemini API Key. Get it from aistudio.google.com")
                gemini_api_key = input("Gemini API Key: ").strip()
                if not gemini_api_key:
                    print("Error: Gemini key cannot be empty.")
                    sys.exit(1)
            new_config["profiles"]["gemini-default"]["api_key"] = gemini_api_key
        
        elif provider == "2":
            new_config["active_profile"] = "openai-default"
            print(f"[{APP_NAME}] Enter OpenAI Base URL (Press Enter for default: https://api.openai.com/v1)")
            base_url = input("Base URL: ").strip()
            if base_url:
                new_config["profiles"]["openai-default"]["base_url"] = base_url
            
            print(f"[{APP_NAME}] Enter your OpenAI or custom API Key.")
            openai_api_key = input("API Key: ").strip()
            if not openai_api_key:
                print("Error: API Key cannot be empty.")
                sys.exit(1)
            new_config["profiles"]["openai-default"]["api_key"] = openai_api_key
            
            print(f"[{APP_NAME}] Enter Model Name (Press Enter for default: gpt-4o)")
            model_name = input("Model Name: ").strip()
            if model_name:
                new_config["profiles"]["openai-default"]["model_name"] = model_name
    else:
        # Default to Gemini if non-interactive and no config exists
        if not gemini_api_key:
             return None # Cannot proceed without an API key
        new_config["profiles"]["gemini-default"]["api_key"] = gemini_api_key

    # Save the new configuration
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_config, f, indent=4)
    
    print(f"Configuration saved to {CONFIG_FILE}\n")

    # Clean up the legacy key backup file if it exists after migration
    if backup_file.exists():
         backup_file.unlink()

    return new_config

def open_editor():
    """Opens config.json in the user's terminal editor."""
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
    help_markdown = """
# Termai - A CLI AI Assistant
A lightweight CLI tool for AI integration in your terminal.

## Usage
* `ai [OPTIONS] "YOUR QUERY"`
* `cat file.txt | ai [OPTIONS] "OPTIONAL PROMPT"`

## Options
* `-i`, `--chat`, `chat` : Start an interactive chat session
* `-p`, `--profile [name]` : Run query using or switching temporarily to a profile
* `-m`, `--model [name]` : List available Gemini models or set a specific one
* `profile [action]` : Profile management: `list`, `use`, `add`, `remove` (or `rm`)
* `completion [shell]` : Generate shell auto-completion script (`bash` or `zsh`)
* `-o`, `--save <file>` : Save the response or chat session to a file
* `--config` : Open configuration file
* `--debug` : Enable debug mode
* `--debug-config` : Print the loaded configuration (redacts keys)
* `--help`, `-h` : Show this help message
* `--reinstall` : Re-run the first-time setup

## Legacy Profile Flags (deprecated)
* `--profiles` : List all configured profiles
* `--use [name]` : Set active profile default
* `--profile-add <name>` : Add a new custom profile
* `--profile-remove <n>` : Remove a profile

## Examples
* `ai "How do I unzip a tar file?"`
* `ai chat`
* `ai chat -o session.md`
* `ai profile use`
* `ai -p local-ollama "What is Python?"`
* `ai --model`
* `cat error.log | ai "Explain this error briefly"`
"""
    print(render_markdown(help_markdown.strip()))
    return 0 # Return 0 for success

def handle_completion(config):
    """Generates autocomplete suggestions for bash/zsh tab completion."""
    try:
        complete_idx = sys.argv.index("--complete")
        cword_idx = sys.argv.index("--cword")
        # Extract command line words
        words = sys.argv[complete_idx + 1:cword_idx]
        cword = int(sys.argv[cword_idx + 1])
    except (ValueError, IndexError):
        return 0

    if cword < 0 or cword >= len(words):
        return 0

    cur = words[cword]
    suggestions = []

    # Case 1: First argument completion (ai [tab] or ai ch[tab])
    if cword == 1:
        suggestions = [
            "chat", "profile", "completion", "help",
            "-i", "--chat", "-p", "--profile", "-m", "--model",
            "--profiles", "--use", "--profile-add", "--profile-remove",
            "--config", "--debug", "--debug-config", "--help", "-h", "--reinstall"
        ]

    # Case 2: Subcommands/Options under 'profile'
    elif cword == 2 and words[1] == "profile":
        suggestions = ["list", "use", "set", "add", "remove", "rm", "help", "--help", "-h"]

    # Case 3: Profile names for 'profile use/set/remove/rm'
    elif cword == 3 and words[1] == "profile" and words[2] in ["use", "set", "remove", "rm"]:
        if config:
            suggestions = list(config.get("profiles", {}).keys())

    # Case 4: Profile names for legacy/temporary profile flags
    elif cword >= 2 and words[cword - 1] in ["--use", "--profile-remove", "--profile", "-p"]:
        if config:
            suggestions = list(config.get("profiles", {}).keys())

    # Case 5: Model names for --model/-m
    elif cword >= 2 and words[cword - 1] in ["--model", "-m"]:
        suggestions = ["gemini-2.5-flash", "gemini-2.5-pro", "gpt-4o", "gpt-4o-mini"]

    # Case 6: Shell options for 'completion'
    elif cword == 2 and words[1] == "completion":
        suggestions = ["bash", "zsh"]

    # Filter and print matching suggestions
    matches = [s for s in suggestions if s.startswith(cur)]
    for m in matches:
        print(m)
    return 0

def visual_len(s):
    """Calculates the visual column width of a string in the terminal, accounting for double-width wide characters/emojis."""
    length = 0
    for char in s:
        if ord(char) > 0x2000:
            length += 2
        else:
            length += 1
    return length

def visual_ljust(s, width):
    """Pads a string with spaces to a visual width, rather than character count width."""
    v_len = visual_len(s)
    needed = width - v_len
    if needed > 0:
        return s + (" " * needed)
    return s

def save_chat_history(history, filename, provider, target_profile, model_name):
    """Saves the chat history to a file in a clean Markdown format."""
    from datetime import datetime
    try:
        filepath = Path(filename).resolve()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w") as f:
            f.write(f"# Termai Chat Session\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Profile: {target_profile} | Provider: {provider.capitalize()} | Model: {model_name}\n\n")
            f.write(f"---\n\n")
            
            for msg in history:
                if provider == "gemini":
                    role = "You" if msg.get("role") == "user" else "AI"
                    text = msg.get("parts", [{}])[0].get("text", "")
                else: # openai
                    role = "You" if msg.get("role") == "user" else "AI"
                    text = msg.get("content", "")
                
                f.write(f"### {role}\n{text}\n\n")
                
        print(f"{GREEN}[✓] Chat history saved successfully to: {filepath}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}[Error] Failed to save chat history: {e}{RESET}")
        return False

def save_single_response(text, filename):
    """Saves a single AI response to a file."""
    try:
        filepath = Path(filename).resolve()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(text.strip() + "\n")
        print(f"\n{GREEN}[✓] Response saved to: {filepath}{RESET}")
    except Exception as e:
        print(f"\n{RED}[Error] Failed to save response: {e}{RESET}")

def print_user_message(prompt_text, message_text):
    """Prints a styled user message block with full-width background color and clean word wrapping."""
    if not BG_USER:
        print(f"{prompt_text}{message_text}")
        return

    import shutil
    import textwrap

    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        cols = 80

    width = cols - 1 if cols > 1 else 1

    lines = textwrap.wrap(message_text, width=width, initial_indent=prompt_text, subsequent_indent=" " * len(prompt_text))
    for line in lines:
        padded = visual_ljust(line, width)
        print(f"{BG_USER}{padded}{RESET}")

def print_header_block(target_profile, provider, model_name):
    """Prints the chat session header block with full-width background color."""
    if not BG_HEADER:
        print(f"\n💬 Termai Interactive Chat Session")
        print(f"Using Profile: {target_profile} | Provider: {provider.capitalize()} | Model: {model_name}")
        print(f"Type exit or quit (or Ctrl+D) to end the chat.\n")
        return

    import shutil
    import textwrap

    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        cols = 80

    width = cols - 1 if cols > 1 else 1

    title = "💬 Termai Interactive Chat Session"
    details = f"Using Profile: {target_profile} | Provider: {provider.capitalize()} | Model: {model_name}"
    info = "Type exit or quit (or Ctrl+D) to end the chat."

    lines = []
    for text in [title, details, info]:
        wrapped = textwrap.wrap(text, width=width - 4)
        for w in wrapped:
            lines.append(f"  {w}")

    pad = " " * width
    print()
    print(f"{BG_HEADER}{pad}{RESET}")
    for line in lines:
        padded = visual_ljust(line, width)
        print(f"{BG_HEADER}{padded}{RESET}")
    print(f"{BG_HEADER}{pad}{RESET}")

def list_profiles(config):
    """Displays a formatted list of all configured profiles and indicates which is currently active."""
    profiles = config.get("profiles", {})
    active = config.get("active_profile", "")
    
    print(f"\n{BLUE}💬 Configured Profiles:{RESET}")
    for idx, p_name in enumerate(profiles.keys(), 1):
        is_active = f" {GREEN}(active){RESET}" if p_name == active else ""
        p_config = profiles[p_name]
        prov = p_config.get("provider", "gemini")
        model = p_config.get("model_name", "")
        extra = f" ({p_config['base_url']})" if prov == "openai" and "base_url" in p_config else ""
        print(f"  {CYAN}{idx}. {p_name}{RESET} [{YELLOW}{prov}{RESET}] -> {model}{extra}{is_active}")
    print()
    return 0

def switch_profile(config, profile_name=None):
    """Changes the active profile globally, either directly or via an interactive selection list."""
    profiles = config.get("profiles", {})
    
    if not profile_name:
        # Interactive Selection list
        print(f"\n{BLUE}💬 Select a profile to set as default active profile:{RESET}")
        profile_list = list(profiles.keys())
        active = config.get("active_profile", "")
        
        for idx, p_name in enumerate(profile_list, 1):
            is_active = f" {GREEN}(active){RESET}" if p_name == active else ""
            p_config = profiles[p_name]
            prov = p_config.get("provider", "gemini")
            model = p_config.get("model_name", "")
            print(f"  {CYAN}{idx}. {p_name}{RESET} [{YELLOW}{prov}{RESET}] -> {model}{is_active}")
            
        try:
            choice = input(f"\nSelect a profile number to set as active (or press Enter to cancel): ").strip()
            if not choice:
                print("Cancelled.")
                return 0
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(profile_list):
                profile_name = profile_list[choice_idx]
            else:
                print(f"{RED}[!] Invalid choice.{RESET}")
                return 1
        except ValueError:
            print(f"{RED}[!] Invalid number entered.{RESET}")
            return 1
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 0

    if profile_name in profiles:
        config["active_profile"] = profile_name
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}[✓] Default active profile switched successfully to: {profile_name}{RESET}")
        return 0
    else:
        print(f"{RED}[Error] Profile '{profile_name}' not found.{RESET}")
        return 1

def add_profile(config, profile_name):
    """Adds a new profile to config.json interactively."""
    profiles = config.get("profiles", {})
    if profile_name in profiles:
        print(f"{RED}[Error] Profile '{profile_name}' already exists.{RESET}")
        return 1

    print(f"\n{BLUE}🚀 Adding new profile: {profile_name}{RESET}")
    print("Choose profile provider type:")
    print("  1. Gemini")
    print("  2. OpenAI (or OpenAI-compatible custom endpoint)")
    
    provider_type = ""
    while provider_type not in ["1", "2"]:
        try:
            provider_type = input("Choice [1-2]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 0

    new_profile = {}
    if provider_type == "1":
        new_profile["provider"] = "gemini"
        print(f"[{APP_NAME}] Enter your Gemini API Key. Get it from aistudio.google.com")
        api_key = input("Gemini API Key: ").strip()
        if not api_key:
            print("Error: Key cannot be empty.")
            return 1
        new_profile["api_key"] = api_key
        new_profile["model_name"] = "gemini-2.5-flash"
        new_profile["system_instruction"] = DEFAULT_CONFIG["profiles"]["gemini-default"]["system_instruction"]
        new_profile["generation_config"] = DEFAULT_CONFIG["profiles"]["gemini-default"]["generation_config"]
    else:
        new_profile["provider"] = "openai"
        print(f"[{APP_NAME}] Enter OpenAI/Custom Base URL (Press Enter for default: https://api.openai.com/v1)")
        base_url = input("Base URL: ").strip()
        new_profile["base_url"] = base_url if base_url else "https://api.openai.com/v1"
        
        print(f"[{APP_NAME}] Enter your OpenAI/Custom API Key.")
        api_key = input("API Key: ").strip()
        if not api_key:
            print("Error: Key cannot be empty.")
            return 1
        new_profile["api_key"] = api_key
        
        print(f"[{APP_NAME}] Enter Model Name (Press Enter for default: gpt-4o)")
        model_name = input("Model Name: ").strip()
        new_profile["model_name"] = model_name if model_name else "gpt-4o"
        new_profile["system_instruction"] = DEFAULT_CONFIG["profiles"]["openai-default"]["system_instruction"]
        new_profile["temperature"] = 0.7
        new_profile["max_tokens"] = 1024

    config["profiles"][profile_name] = new_profile
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print(f"{GREEN}[✓] Profile '{profile_name}' created successfully!{RESET}")
    return 0

def remove_profile(config, profile_name):
    """Deletes a profile from config.json."""
    profiles = config.get("profiles", {})
    active = config.get("active_profile", "")
    
    if profile_name not in profiles:
        print(f"{RED}[Error] Profile '{profile_name}' not found.{RESET}")
        return 1
        
    if profile_name == active:
        print(f"{RED}[Error] Cannot remove currently active profile '{profile_name}'. Please switch to another profile first.{RESET}")
        return 1
        
    del config["profiles"][profile_name]
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print(f"{GREEN}[✓] Profile '{profile_name}' deleted successfully.{RESET}")
    return 0

def handle_model_option(config):
    """Fetches and displays available Gemini models interactively, or directly sets the model if specified."""
    active_profile = config.get("active_profile", "")
    profiles = config.get("profiles", {})
    profile_config = profiles.get(active_profile, {})
    
    provider = profile_config.get("provider", "gemini")
    if provider != "gemini":
        print(f"{YELLOW}[*] Model listing/switching is currently supported for profiles using the Gemini provider.{RESET}")
        return 0

    api_key = profile_config.get("api_key")
    current_model = profile_config.get("model_name", "gemini-2.5-flash")

    # Check if a model argument is provided after the flag
    model_arg = ""
    model_flags = ["--model", "-m"]
    for i, arg in enumerate(sys.argv):
        if arg in model_flags and i + 1 < len(sys.argv):
            # Ensure it is not another flag
            if not sys.argv[i + 1].startswith("-"):
                model_arg = sys.argv[i + 1].strip()
                break

    if model_arg:
        clean_model = model_arg.replace("models/", "")
        config["profiles"][active_profile]["model_name"] = clean_model
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}[✓] Model for profile '{active_profile}' updated successfully to: {clean_model}{RESET}")
        return 0

    if not api_key:
        print(f"{RED}[Error] Gemini API key not found for active profile '{active_profile}'. Please configure it first.{RESET}")
        return 1

    print(f"{BLUE}[*] Fetching available models from Gemini API...{RESET}")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"{RED}[Error {response.status_code}] Failed to fetch models: {response.text}{RESET}")
            return 1
        data = response.json()
        models = data.get("models", [])
        
        generation_models = []
        for m in models:
            name = m.get("name", "")
            if "generateContent" in m.get("supportedGenerationMethods", []):
                short_name = name.replace("models/", "")
                display_name = m.get("displayName", short_name)
                desc = m.get("description", "No description available.")
                generation_models.append({
                    "name": short_name,
                    "displayName": display_name,
                    "description": desc
                })

        if not generation_models:
            print(f"{YELLOW}[!] No text generation models returned from Gemini API.{RESET}")
            return 0

        print(f"\n{BLUE}🔍 Available Gemini Text Models:{RESET}")
        for idx, m in enumerate(generation_models, 1):
            is_current = f" {GREEN}(active){RESET}" if m["name"] == current_model else ""
            print(f"  {CYAN}{idx}. {m['displayName']}{RESET} [{YELLOW}{m['name']}{RESET}]{is_current}")
            print(f"     {m['description']}")
            print()

        try:
            choice = input(f"Select a model number to set as active (or press Enter to cancel): ").strip()
            if not choice:
                print("Cancelled.")
                return 0
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(generation_models):
                selected_model = generation_models[choice_idx]["name"]
                config["profiles"][active_profile]["model_name"] = selected_model
                with open(CONFIG_FILE, "w") as f:
                    json.dump(config, f, indent=4)
                print(f"{GREEN}[✓] Gemini model for profile '{active_profile}' successfully updated to: {selected_model}{RESET}")
            else:
                print(f"{RED}[!] Invalid choice.{RESET}")
        except ValueError:
            print(f"{RED}[!] Invalid number entered.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            
        return 0
    except Exception as e:
        print(f"{RED}[Connection Error] Failed to contact Gemini API: {e}{RESET}")
        return 1

def render_markdown(text):
    """Renders basic Markdown beautifully in terminal using ANSI escape codes, with an optional rich-library fallback."""
    if not sys.stdout.isatty():
        return text

    # Try to use rich library if available
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        import io
        string_io = io.StringIO()
        console = Console(file=string_io, force_terminal=True)
        console.print(Markdown(text))
        return string_io.getvalue().strip()
    except ImportError:
        pass

    # High-fidelity custom ANSI renderer fallback
    lines = text.split("\n")
    rendered_lines = []
    in_code_block = False
    code_lang = ""

    for line in lines:
        # 1. Handle Code Block boundaries
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                lang_str = f" {code_lang.upper()} " if code_lang else " CODE "
                border = f"\033[96m┌──────────────────{lang_str}──────────────────\033[0m"
                rendered_lines.append(border)
            else:
                in_code_block = False
                border = "\033[96m└───────────────────────────────────────────────\033[0m"
                rendered_lines.append(border)
            continue

        # 2. Inside Code Block
        if in_code_block:
            rendered_lines.append(f"\033[93m{line}\033[0m")
            continue

        # 3. Headers (# Header, ## Header, etc.)
        if line.strip().startswith("#"):
            stripped = line.strip()
            header_text = stripped.lstrip("#").strip()
            rendered_lines.append(f"\033[1;96m✦ {header_text}\033[0m")
            continue

        # 4. Bullet Points (* item, - item, etc.)
        stripped_line = line.lstrip()
        indent = line[:len(line) - len(stripped_line)]
        if stripped_line.startswith("* ") or stripped_line.startswith("- ") or stripped_line.startswith("+ "):
            bullet_text = stripped_line[2:]
            rendered_lines.append(f"{indent}\033[92m•\033[0m {bullet_text}")
            continue

        # 5. Inline formatting (Bold, Italic, Inline Code)
        formatted_line = line
        import re
        formatted_line = re.sub(r'`([^`]+)`', r'\033[96m\1\033[0m', formatted_line)
        formatted_line = re.sub(r'\*\*([^*]+)\*\*', r'\033[1m\1\033[22m', formatted_line)
        formatted_line = re.sub(r'\*([^*]+)\*', r'\033[3m\1\033[23m', formatted_line)

        rendered_lines.append(formatted_line)

    return "\n".join(rendered_lines)

def send_gemini_request(profile_config, user_input, debug_mode, proxy="", history=None, output_file=None):
    api_key = profile_config.get("api_key")
    model_name = profile_config.get("model_name", "gemini-2.5-flash")
    system_instr = profile_config.get("system_instruction", "")
    gen_config = profile_config.get("generation_config", {})
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    payload_contents = history if history is not None else [{"parts": [{"text": user_input}]}]
    payload = {
        "contents": payload_contents,
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
                response_text = cand['content']['parts'][0]['text']
                rendered_text = render_markdown(response_text)
                print(rendered_text.strip())
                if history is not None:
                    history.append({"role": "model", "parts": [{"text": response_text}]})
                if output_file and history is None:
                    save_single_response(response_text, output_file)
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

def send_openai_request(profile_config, user_input, debug_mode, proxy="", history=None, output_file=None):
    api_key = profile_config.get("api_key")
    model_name = profile_config.get("model_name", "gpt-4o")
    system_instr = profile_config.get("system_instruction", "")
    temperature = profile_config.get("temperature", 0.7)
    max_tokens = profile_config.get("max_tokens", 1024)
    base_url = profile_config.get("base_url", "https://api.openai.com/v1")
    # Form the completions endpoint URL robustly
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    
    if base_url.endswith("/chat/completions"):
        api_url = base_url
    else:
        api_url = f"{base_url}/chat/completions"
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if history is not None:
        payload_messages = [{"role": "system", "content": system_instr}] + history
    else:
        payload_messages = [
            {"role": "system", "content": system_instr},
            {"role": "user", "content": user_input}
        ]

    payload = {
        "model": model_name,
        "messages": payload_messages,
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
                rendered_text = render_markdown(content)
                print(rendered_text.strip())
                if history is not None:
                    history.append({"role": "assistant", "content": content})
                if output_file and history is None:
                    save_single_response(content, output_file)
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
    
    if "--complete" in sys.argv:
        return handle_completion(config)
    
    if "--reinstall" in sys.argv:
        print(f"[{APP_NAME}] Reinstall complete.")
        return 0

    # Handle --debug-config flag
    if "--debug-config" in sys.argv:
        if not config:
            print("[Error] No configuration file found. Run `ai --reinstall` to create one.")
            return 1
        
        debug_config = copy.deepcopy(config)
        if "profiles" in debug_config:
            for p_name in debug_config["profiles"]:
                p_cfg = debug_config["profiles"][p_name]
                if "api_key" in p_cfg:
                    key = p_cfg["api_key"]
                    p_cfg["api_key"] = f"***{key[-4:]}" if key else ""
            
        print(json.dumps(debug_config, indent=4))
        return 0

    if config is None and not sys.stdin.isatty():
        return 1
    
    # Handle 'profile' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "profile" and sys.stdin.isatty():
        subcommand = sys.argv[2] if len(sys.argv) > 2 else "list"
        
        if subcommand in ["--help", "-h", "help"]:
            print(f"\n{GREEN}Termai Profile Management{RESET}")
            print(f"Manage different AI configuration profiles.\n")
            print(f"{YELLOW}Usage:{RESET}")
            print(f"  ai profile list                List all configured profiles (alias: ai profile)")
            print(f"  ai profile use [name]          Set a profile as the active default (interactive if no name)")
            print(f"  ai profile add <name>          Add a new custom profile")
            print(f"  ai profile remove <name>       Remove a profile (alias: rm)")
            return 0
            
        elif subcommand == "list":
            return list_profiles(config)
            
        elif subcommand in ["use", "set"]:
            profile_name = sys.argv[3] if len(sys.argv) > 3 else None
            return switch_profile(config, profile_name)
            
        elif subcommand == "add":
            if len(sys.argv) > 3:
                return add_profile(config, sys.argv[3])
            else:
                print(f"{RED}[Error] Please provide a name for the new profile: ai profile add <name>{RESET}")
                return 1
                
        elif subcommand in ["remove", "rm"]:
            if len(sys.argv) > 3:
                return remove_profile(config, sys.argv[3])
            else:
                print(f"{RED}[Error] Please provide a profile name to remove: ai profile remove <name>{RESET}")
                return 1
        else:
            print(f"{RED}[Error] Unknown profile subcommand '{subcommand}'.")
            print(f"Run 'ai profile --help' to see available commands.{RESET}")
            return 1

    # Handle 'completion' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "completion" and sys.stdin.isatty():
        shell = sys.argv[2] if len(sys.argv) > 2 else None
        if not shell:
            print(f"{RED}[Error] Please specify a shell: ai completion [bash|zsh]{RESET}")
            return 1
        
        if shell == "bash":
            print(f"""# Bash completion for termai (ai)
_ai_completion() {{
    local cur
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    local IFS=$'\\n'
    COMPREPLY=( $(ai --complete "${{COMP_WORDS[@]}}" --cword "$COMP_CWORD") )
    return 0
}}
complete -F _ai_completion ai""")
            return 0
        elif shell == "zsh":
            print(f"""# Zsh completion for termai (ai)
(( $+functions[compdef] )) || {{ autoload -Uz compinit && compinit; }}
_ai_completion() {{
    local -a replies
    local IFS=$'\\n'
    replies=($(ai --complete "${{words[@]}}" --cword $((CURRENT-1))))
    compadd -a replies
}}
compdef _ai_completion ai""")
            return 0
        else:
            print(f"{RED}[Error] Unsupported shell '{shell}'. Supported: bash, zsh.{RESET}")
            return 1

    if "--help" in sys.argv or "-h" in sys.argv:
        return print_help()

    if "--config" in sys.argv:
        return open_editor()

    # Legacy Profile management options
    if "--profiles" in sys.argv:
        return list_profiles(config)
        
    if "--use" in sys.argv:
        idx = sys.argv.index("--use")
        profile_name = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        return switch_profile(config, profile_name)
        
    if "--profile-add" in sys.argv:
        idx = sys.argv.index("--profile-add")
        if idx + 1 < len(sys.argv):
            return add_profile(config, sys.argv[idx + 1])
        else:
            print(f"{RED}[Error] Please provide a name for the new profile: ai --profile-add <name>{RESET}")
            return 1

    if "--profile-remove" in sys.argv:
        idx = sys.argv.index("--profile-remove")
        if idx + 1 < len(sys.argv):
            return remove_profile(config, sys.argv[idx + 1])
        else:
            print(f"{RED}[Error] Please provide a profile name to remove: ai --profile-remove <name>{RESET}")
            return 1

    if "--model" in sys.argv or "-m" in sys.argv:
        return handle_model_option(config)

    debug_mode = "--debug" in sys.argv
    chat_mode = any(x in sys.argv for x in ["--chat", "-i", "chat"])
    
    chat_flags = ["--chat", "-i", "chat"]
    profile_flags = ["--profile", "-p"]
    model_flags = ["--model", "-m"]
    save_flags = ["--save", "-o"]
    
    output_file = None
    for flag in save_flags:
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-"):
                output_file = sys.argv[idx + 1].strip()
                break

    # Check if a custom profile is temporarily chosen
    target_profile = config.get("active_profile", "")
    temp_profile = None
    for flag in profile_flags:
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-"):
                temp_profile = sys.argv[idx + 1].strip()
                break
            else:
                # Interactive Run - no direct profile argument provided, prompt user to select a profile
                profiles = config.get("profiles", {})
                profile_list = list(profiles.keys())
                print(f"\n{BLUE}💬 Select a profile to run this query:{RESET}")
                for p_idx, p_name in enumerate(profile_list, 1):
                    p_config = profiles[p_name]
                    prov = p_config.get("provider", "gemini")
                    print(f"  {CYAN}{p_idx}. {p_name}{RESET} [{YELLOW}{prov}{RESET}]")
                try:
                    choice = input(f"\nSelect a profile number: ").strip()
                    if not choice:
                        print("Cancelled.")
                        return 0
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(profile_list):
                        temp_profile = profile_list[choice_idx]
                    else:
                        print(f"{RED}[!] Invalid choice.{RESET}")
                        return 1
                except (ValueError, IndexError):
                    print(f"{RED}[!] Invalid choice.{RESET}")
                    return 1
                except (KeyboardInterrupt, EOFError):
                    print("\nCancelled.")
                    return 0

    if temp_profile:
        if temp_profile in config.get("profiles", {}):
            target_profile = temp_profile
        else:
            print(f"{RED}[Error] Profile '{temp_profile}' not found in configuration.{RESET}")
            return 1

    # Filter out configuration, help, reinstall, chat, model, profile, and save flags/arguments from prompt text
    filtered_args = []
    skip = False
    for idx, arg in enumerate(sys.argv[1:]):
        if skip:
            skip = False
            continue
        if arg in model_flags + profile_flags + save_flags:
            if idx + 2 < len(sys.argv) and not sys.argv[idx + 2].startswith("-"):
                skip = True
            continue
        if arg in ["--debug", "--config", "--help", "-h", "--reinstall", "--debug-config", "--profiles", "--use", "--profile-add", "--profile-remove"] + chat_flags:
            continue
        filtered_args.append(arg)
    args = filtered_args

    # Handle interactive chat session mode
    if chat_mode:
        active_config = config["profiles"][target_profile]
        provider = active_config.get("provider", "gemini")
        proxy = config.get("proxy", "")
        if provider == "gemini":
            model_name = active_config.get("model_name", "gemini-2.5-flash")
        else:
            model_name = active_config.get("model_name", "gpt-4o")
            
        # Read piped content if stdin is not a TTY (before we redirect it)
        piped_content = ""
        if not sys.stdin.isatty():
            piped_content = sys.stdin.read().strip()
            # Redirect stdin back to the interactive terminal (/dev/tty) so input() works
            try:
                sys.stdin = open('/dev/tty')
            except OSError:
                pass

        print_header_block(target_profile, provider, model_name)
        
        history = []
        initial_prompt = ""
        display_prompt = ""
        
        if piped_content:
            if args:
                user_question = " ".join(args)
                initial_prompt = f"Context:\n```\n{piped_content}\n```\n\nQuestion: {user_question}"
                display_prompt = f"[Piped Context] + {user_question}"
            else:
                initial_prompt = f"I have provided some context below. Please acknowledge receipt of this context, briefly summarize it, and wait for my questions about it.\n\nContext:\n```\n{piped_content}\n```"
                display_prompt = "[Piped Context] (Awaiting your questions)"
        elif args:
            initial_prompt = " ".join(args)
            display_prompt = initial_prompt

        if initial_prompt:
            print_user_message(" You >>> ", display_prompt)
            if provider == "gemini":
                history.append({"role": "user", "parts": [{"text": initial_prompt}]})
                status = send_gemini_request(active_config, "", debug_mode, proxy=proxy, history=history)
            else:
                history.append({"role": "user", "content": initial_prompt})
                status = send_openai_request(active_config, "", debug_mode, proxy=proxy, history=history)
            
            if status != 0:
                print(f"{RED}[Error] Failed to get response. Continuing session...{RESET}")
                
        while True:
            try:
                prompt = f"\n You >>> "
                user_input = input(prompt)
                user_input = user_input.strip()
                if not user_input:
                    continue
                
                # Rewrite typed text with beautiful full-width purple background block
                if BG_USER:
                    import shutil
                    import math
                    try:
                        cols = shutil.get_terminal_size().columns
                    except Exception:
                        cols = 80
                    total_len = len(prompt) + len(user_input)
                    n_lines = math.ceil(total_len / cols) if cols else 1
                    sys.stdout.write(f"\033[{n_lines}A\r\033[J")
                    sys.stdout.flush()
                
                print_user_message(" You >>> ", user_input)
                
                if user_input.lower() in ["exit", "quit"]:
                    print(f"\n{YELLOW}Goodbye!{RESET}")
                    break
                
                if user_input.lower().startswith("save ") or user_input.lower().startswith("/save "):
                    parts = user_input.split(None, 1)
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        save_chat_history(history, filename, provider, target_profile, model_name)
                    else:
                        print(f"{RED}[Error] Please provide a filename: save <filename>{RESET}")
                    continue
                
                if provider == "gemini":
                    history.append({"role": "user", "parts": [{"text": user_input}]})
                    status = send_gemini_request(active_config, "", debug_mode, proxy=proxy, history=history)
                else:
                    history.append({"role": "user", "content": user_input})
                    status = send_openai_request(active_config, "", debug_mode, proxy=proxy, history=history)
                    
                if status != 0:
                    print(f"{RED}[Error] Failed to get response. Continuing session...{RESET}")
            except (KeyboardInterrupt, EOFError):
                print(f"\n{YELLOW}Goodbye!{RESET}")
                break

        # Auto-save history on exit if output_file is set
        if output_file and history:
            save_chat_history(history, output_file, provider, target_profile, model_name)
        return 0

    user_input = ""
    if not sys.stdin.isatty():
        user_input = sys.stdin.read().strip()
        if args: user_input += "\n" + " ".join(args)
    elif args:
        user_input = " ".join(args)
    else:
        return print_help()

    active_config = config["profiles"][target_profile]
    provider = active_config.get("provider", "gemini")
    proxy = config.get("proxy", "")
    
    if provider == "gemini":
        return send_gemini_request(active_config, user_input, debug_mode, proxy=proxy, output_file=output_file)
    elif provider == "openai":
        return send_openai_request(active_config, user_input, debug_mode, proxy=proxy, output_file=output_file)
    else:
        print(f"[Error] Invalid provider '{provider}' in profile '{target_profile}'. Use 'gemini' or 'openai'.")
        return 1

def main():
    try:
        sys.exit(cli_entry_point())
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)

if __name__ == "__main__":
    main()