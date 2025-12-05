## Termai
Termai is a lightweight, zero-dependency CLI wrapper for Google's Gemini AI, built specifically for the Termux environment on Android.
It brings the power of Large Language Models (LLMs) directly to your mobile command line, following the Unix philosophy of piping and standard streams.

## ⚡ Features
 * **🚀 Lightweight:** Uses standard Python requests. No heavy SDKs or complex dependencies.
 * **🟢 Unix Compatible:** Supports piping (stdin). Feed logs, code, or text files directly into the AI.
 * **🛠 Configurable:** Built-in JSON configuration system (ai --config) to edit System Prompts, Temperature, and Models.
 * **⚡ Fast:** Defaults to gemini-2.5-flash for instant responses.
 * **🎨 Clean UI:** Minimalist output with syntax-highlighted green text.
 * **🧹 Auto-Cleanup:** The installer sets everything up and deletes the repository to save space.

 ## 📥 Installation
Open Termux and run the following commands:
```bash
# 1. Clone the repository
git clone https://github.com/estiaksoyeb/termai

# 2. Enter the directory
cd termai

# 3. Run the installer
bash install.sh
```

**What the installer does:**
 * Installs Python and required libraries.
 * Moves the core logic to a hidden folder (~/.programs/termai).
 * Creates a global ai command.
 * Self-Destructs: Deletes the downloaded source folder to keep your home directory clean.
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
Made with ❤️ for Termux
</p>
