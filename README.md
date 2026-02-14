# Ctrl+AI

## Description

Ctrl+AI is a desktop utility designed to eliminate the "Alt-Tab Tax" of using Artificial Intelligence. Instead of manually copying text, switching to a browser, pasting into a chat interface, and copying the result back, Ctrl+AI brings the AI directly to your cursor.

It runs as a background service that injects intelligence into any text field across the operating system (VS Code, Slack, Google Docs, etc.) using global hotkeys.

## Key Features

### 1. The Commander
**Trigger**: `Ctrl+Space`
Opens a minimalist spotlight-bar overlay. The user types a specific instruction (e.g., "Make this professional", "Translate to Spanish"), and the selected text is replaced in-place with the AI-processed version.

### 2. The Refactor (Ghost Mode)
**Trigger**: `Ctrl+Shift+H`
A "headless" mode for code and text optimization. It detects the selected content and automatically sends it to the AI with a prompt to fix bugs, optimize logic, or correct grammar, pasting the result back immediately.

### 3. The Redactor (Ghost Mode)
**Trigger**: `Ctrl+Shift+D`
A privacy-focused mode that processes selected text to identify and remove Personal Identifiable Information (PII) or summarize "fluff", returning a sanitized version.

## Technology Stack

- **Core**: Python 3.10+
- **GUI**: customtkinter (Modern, dark-mode overlay)
- **Input/Output**: 
  - `pynput` for global hotkey listening
  - `pyperclip` for clipboard manipulation
- **Concurrency**: `threading` for non-blocking UI and API calls

## Installation

### Prerequisites

- Python 3.10 or higher installed on your system.

**Linux Users:**
This project relies on system-level clipboard hooks which require `tkinter`.
```bash
sudo apt-get install python3-tk python3-dev
```

### Setup Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Ctrl-Hack
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python src/main.py
   ```

2. The application will start in the background. Select text in any application (Editor, Browser, etc.) and use the hotkeys:

   - **Refactor**: Press `Ctrl+Shift+H` to simulate fixing/optimizing the text.
   - **Redact**: Press `Ctrl+Shift+D` to simulate sanitizing the text.
   - **Commander**: Press `Ctrl+Space` (UI coming in next update).

3. Watch the terminal for logs regarding capture and processing status.

4. To exit, press `Ctrl+C` in the terminal window running the script.

## Roadmap

- [x] **Phase 1: The Skeleton** - Basic hotkey listening and clipboard manipulation.
- [ ] **Phase 2: The Brain** - Integration with LLM APIs (Groq/OpenAI).
- [ ] **Phase 3: The Face** - Floating UI overlay with `customtkinter`.
- [ ] **Phase 4: Polish** - Visual feedback spinners and diff views.

## Project Structure

```
Ctrl-Hack/
├── docs/               # Project documentation and charter
├── src/
│   ├── main.py         # Application entry point & hotkey listener
│   └── clipboard_utils.py # Clipboard capture and injection logic
├── requirements.txt    # Python dependencies
└── README.md           # Project overview
```

## Authors

- Ctrl+AI Team