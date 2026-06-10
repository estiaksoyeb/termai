## Termai
Termai is a lightweight, zero-dependency CLI wrapper for Google's Gemini AI, built for Termux on Android and general Linux environments.
It brings the power of Large Language Models (LLMs) directly to your command line, following the Unix philosophy of piping and standard streams.

## ⚡ Features
 * **🚀 Lightweight:** Uses standard Python requests. No heavy SDKs or complex dependencies.
 * **🟢 Unix Compatible:** Supports piping (stdin). Feed logs, code, or text files directly into the AI.
 * **🛠 Configurable:** Built-in JSON configuration system (ai --config) to edit System Prompts, Temperature, and Models.
 * **⚡ Fast:** Defaults to gemini-2.5-flash for instant responses.
 * **🎨 Clean UI:** Minimalist output with syntax-highlighted green text.
 * **🧹 Auto-Cleanup:** The installer sets everything up and deletes the repository to save space.

 ## 📥 Installation

### ⚡ Quick One-Line Install
Open your terminal and run:
```bash
curl -fsSL https://raw.githubusercontent.com/estiaksoyeb/termai/master/install.sh | bash
```

### 🛠 Alternative Manual Install
Open Termux / Ubuntu and run the following commands:
```bash
# 1. Clone the repository
git clone https://github.com/estiaksoyeb/termai

# 2. Enter the directory
cd termai

# 3. Run the installer
bash install.sh
```

**What the installer does:**
 * **Dependency Check:** Verifies if Python 3 is installed and automatically installs the required libraries (`requests`, `rich`).
 * **Installs Core Logic:** Moves the script safely to a hidden directory (`~/.programs/termai`).
 * **Creates Binary Alias:** Generates the global `ai` execution alias in your binary directory (`$PREFIX/bin` on Termux, or `$HOME/.local/bin` on standard Linux).
 * **Optional Cleanup:** For manual installations, it offers to safely delete the cloned repository folder afterwards to save space.
## 🔑 Setup
On the very first run, Termai will ask for your Google Gemini API Key.
 * Get a free API key here: Google AI Studio
 * Run the command:
 ```bash
   ai "hello"
   ```

 * Paste your key when prompted. It will be saved locally.
## 💻 Usage
1. Basic Questions
Ask anything directly from the terminal.
ai "How do I untar a file in Linux?"

2. Piping (The Power Move)
Feed output from other commands into Termai.
Debug an error log:
```bash
cat error.log | ai "Explain what caused this crash"
```

Explain a script:
```bash
cat install.sh | ai "What does this script do?"
```

Generate code and save it:
 ```bash
 ai "Write a Python hello world script" > hello.py
 ```

3. Saving Outputs (With Terminal Output)
You can save the response to a file while still viewing the output in your terminal:
 ```bash
 # Save a single-query response
 ai "Explain machine learning in 1 sentence" -o ml_concept.txt

 # Automatically save a chat session transcript when you exit
 ai chat -o chat_session.md
 ```

4. Interactive Chat
Start an interactive, multi-turn chat session with memory:
 ```bash
 ai chat
 ```
 * **Rich Terminal Aesthetics**: Interactive chat features a beautiful slate-blue header card and full-width royal-purple highlight blocks for user messages (properly aligned even when emojis are used).
 * **Conversation Snapshots**: Save your chat transcript in clean Markdown format at any point during the conversation by typing:
   ```text
   save snapshot.md
   ```

 ## 👥 Profile Management
 Termai supports multiple AI provider configurations. You can manage them using the `profile` subcommand:
 
 * **List profiles**:
   ```bash
   ai profile
   ```
   *(Alias: `ai profile list`)*
 * **Switch default active profile**:
   ```bash
   ai profile use [profile_name]
   ```
   *(Launches an interactive selection list if no profile name is provided)*
 * **Add a new profile**:
   ```bash
   ai profile add <name>
   ```
 * **Remove a profile**:
   ```bash
   ai profile remove <name>
   ```
   *(Alias: `ai profile rm`)*
 * **Run query with temporary profile**:
   ```bash
   ai -p <profile_name> "your query"
   ```

 ## ⚙️ Configuration
Termai comes with a built-in configuration editor. You can change the AI provider, model, and personality.
Run:
```bash
ai --config
```

This opens `config.json` in your preferred editor. The editor is chosen based on the following priority:
1.  The `$EDITOR` environment variable.
2.  `vim` (if installed).
3.  `nano` (as a fallback).

The configuration file looks like this:
```json
{
    "provider": "gemini",
    "proxy": "http://user:pass@127.0.0.1:1080",
    "gemini_config": {
        "api_key": "YOUR_GEMINI_KEY",
        "model_name": "gemini-2.5-flash",
        "system_instruction": "You are a CLI assistant for Termux...",
        "generation_config": {
            "temperature": 0.7,
            "maxOutputTokens": 1024
        }
    },
    "openai_config": {
        "api_key": "YOUR_OPENAI_KEY",
        "model_name": "gpt-4o",
        "system_instruction": "You are a helpful assistant.",
        "temperature": 0.7,
        "max_tokens": 1024
    }
}
```

*   **`provider`**: Set to `"gemini"` or `"openai"` to choose your AI provider.
*   **`proxy`**: (Optional) Set an HTTP or HTTPS proxy for all requests.
*   **`gemini_config`**: Settings for when `provider` is `"gemini"`.
    *   `model_name`: Change to `gemini-2.5-pro` or other available models.
    *   `system_instruction`: Give the AI a persona.
    *   `temperature`: Set to `1.0` for creative answers, `0.1` for precise logic.
*   **`openai_config`**: Settings for when `provider` is `"openai"`.
    *   `model_name`: Change to `gpt-3.5-turbo`, etc.
    *   `system_instruction`: A different persona for ChatGPT.
    *   `temperature`: Controls randomness.
    *   `max_tokens`: The maximum number of tokens to generate.

## ⌨️ Shell Auto-Completion
Termai includes built-in dynamic shell autocompletion for subcommands, options, profile names, and models.

The installer automatically configures autocomplete for your shell (`.bashrc` / `.zshrc`). You can also manually source the autocompletion loaders:

* **Bash**:
  ```bash
  source <(ai completion bash)
  ```
* **Zsh**:
  ```zsh
  source <(ai completion zsh)
  ```

## ❓ Help & Troubleshooting
**Command List:**
```bash
ai --help
```

**Re-configure API Keys:**

To reset and re-enter your API keys, use the `--reinstall` flag.
```bash
ai --reinstall
```

**Debug Mode:**

If the AI isn't responding or you are getting errors, run:
```bash
ai --debug "your question"
```
This will print the raw server response and error codes.

**Debug Configuration:**
If you are having issues with your configuration, you can use the `--debug-config` flag to print the loaded configuration. API keys will be redacted for security.
```bash
ai --debug-config
```

## 🗑 Uninstallation
To remove Termai completely:
```bash
# Remove the 'ai' command
rm $PREFIX/bin/ai

# Remove the program and configuration files
rm -rf ~/.programs/termai
rm -rf ~/.local/share/termai
```

## 3 📄 License
This project is licensed under the MIT License.
You are free to use, modify, and distribute this software. See the LICENSE file for more details.
<p align="center">
Made with ❤️ for CLI enthusiasts
</p>
