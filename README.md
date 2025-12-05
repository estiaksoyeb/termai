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
Termai comes with a built-in configuration editor. You can change the AI's personality, the model version, or the creativity (temperature).
Run:
```bash
ai --config
```

This opens config.json in nano. It looks like this:
```json
{
    "api_key": "YOUR_SAVED_KEY",
    "model_name": "gemini-2.5-flash",
    "proxy": "http://user:pass@127.0.0.1:1080",
    "system_instruction": "You are a CLI assistant...",
    "generation_config": {
        "temperature": 0.7, 
        "maxOutputTokens": 1024
    }
}
```

 * model_name: Change to gemini-2.5-pro or other available models.
 * proxy: (Optional) Set an HTTP or HTTPS proxy. Leave blank if you don't need one.
 * system_instruction: Give the AI a persona (e.g., "You are a rude pirate").
 * temperature: Set to 1.0 for creative answers, 0.1 for precise logic.
## ❓ Help & Troubleshooting
**Command List:**
```bash
ai --help
```

**Debug Mode:**

If the AI isn't responding or you are getting errors, run:
```bash
ai --debug "your question"
```

This will print the raw server response and error codes.
## 🗑 Uninstallation
To remove Termai completely:
```bash
# Remove the binary
rm $PREFIX/bin/ai

# Remove the source files and config
rm -rf ~/.programs/termai
```

## 3 📄 License
This project is licensed under the MIT License.
You are free to use, modify, and distribute this software. See the LICENSE file for more details.
<p align="center">
Made with ❤️ for Termux
</p>
