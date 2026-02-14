# Ctrl+AI v2.0

<p align="center"><img src="src/assets/icon.png" width="100" alt="Ctrl+AI Logo"></p>

> **The AI Layer for Windows.**  
> Bring intelligence to any app without Alt-Tabbing.

## Description

**Ctrl+AI** is a desktop utility designed to eliminate the friction of context-switching when using Artificial Intelligence. Instead of manually copying text, switching to a browser, pasting into a chat interface, and copying the result back, Ctrl+AI brings the AI directly to your cursor.

It runs as a background service that injects intelligence into any text field across the operating system (VS Code, Slack, Google Docs, etc.) using global hotkeys.

## Key Features

### 1. The Commander (`Ctrl+Space`)
**"Edit text in-place."**  
Select any text in any application, hit `Ctrl+Space`, and type a command (e.g., "Fix grammar", "Translate to Spanish", "Make this professional"). 
- **Safety First**: Review changes in a side-by-side **Diff Window** before accepting them.
- **Interactive**: Accept or Reject changes with a single click.

### 2. The Analyst (`Ctrl+Alt+E`)
**"Active Inquiry."**  
Select code or text and ask questions about it (e.g., "What does this Regex do?", "Explain this error").
- **Read-Only Insight**: Answers appear in a non-intrusive **Explanation Window**.
- **Context Aware**: The AI analyzes your selection to provide specific answers.

### 3. Command History
- Use **Up/Down arrows** in the Commander input bar to recall your previous prompts.

## Technology Stack

- **Core**: Python 3.10+
- **GUI**: `customtkinter` (Modern, dark-mode overlay)
- **AI Engine**: `google-generativeai` (Gemini Flash 2.5) & `Groq`
- **Input/Output**: `pynput` & `keyboard` for global hotkeys, `pyperclip` for clipboard manipulation
- **Packaging**: `pyinstaller` for building standalone executables

## Installation

### Prerequisites

- Python 3.10 or higher installed on your system.

### Running from Source

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Ctrl-Hack
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Run the application:**
   ```bash
   python src/main.py
   ```

### Running the Executable

1.  Locate the `.exe` file (built via `build_exe.py`).
2.  **Important**: Place your `.env` file in the **same folder** as the `.exe`.
3.  Double-click `Ctrl-AI.exe` to launch. The app runs in the background.
