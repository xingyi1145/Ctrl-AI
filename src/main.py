print("Main starting...")
import logging
import ctypes
import os
import platform
import traceback
logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.info("Main script starting...")

import time
import threading
try:
    import keyboard as keyboard_lib # Use updated name to avoid conflict with pynput variable if mixed
except ImportError:
    keyboard_lib = None

# Fallback for non-linux systems or if keyboard lib fails
try:
    from pynput import keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None

from clipboard_utils import capture_selection, paste_text
from ai_handler import AIHandler

# Try importing GUI; gracefully handle if tkinter is missing (e.g. on headless/some Linux)
try:
    from gui import OverlayApp
    GUI_AVAILABLE = True
except ImportError as e:
    logging.error(f"GUI Import failed: {e}")
    print(f"WARNING: GUI not available ({e}). Commander mode will be disabled.")
    GUI_AVAILABLE = False
    OverlayApp = None

class CtrlAIApp:
    def __init__(self):
        logging.info("Initializing App")
        self.running = True
        self.listener = None
        self.ai = AIHandler()
        self.gui = None
        self.captured_text_for_commander = ""
        self.active_toast = None

        if GUI_AVAILABLE:
            self.gui = OverlayApp(submit_callback=self.on_commander_submit)

    def show_progress(self, message):
        if self.gui:
            self.gui.after(0, lambda: self._gui_show_toast(message))
            
    def _gui_show_toast(self, message):
        if self.active_toast:
            try:
                self.active_toast.hide()
            except: 
                pass
        self.active_toast = self.gui.show_toast(message)
        
    def hide_progress(self):
        if self.gui:
            self.gui.after(0, self._gui_hide_toast)
            
    def _gui_hide_toast(self):
        if self.active_toast:
            try:
                self.active_toast.hide()
            except:
                pass
            self.active_toast = None

    def on_commander(self):
        logging.info("[Commander] Triggered (Ctrl+Space)")
        print("[Commander] Triggered (Ctrl+Space)")
        
        if not self.gui:
            print("Commander mode requires GUI (tkinter missing).")
            return

        # 1. Capture text first (The "Context")
        text = capture_selection()
        if text:
            print(f"[Commander] Context captured: '{text[:20]}...'")
            self.captured_text_for_commander = text
            # 2. Show UI
            # Use `after` to schedule GUI update safely in main thread if possible, 
            # or relying on ctk thread safety. Best practice is `after`.
            # Since self.gui is running in main thread and we are in listener thread:
            self.gui.after(0, self.gui.show_overlay)
        else:
            print("[Commander] No text selected.")

    def on_commander_submit(self, prompt):
        print(f"[Commander] Prompt: {prompt}")
        threading.Thread(target=self.process_commander, args=(prompt,)).start()

    def process_commander(self, prompt):
        logging.info(f"Processing Commander: {prompt}")
        self.show_progress(f"Commander: {prompt}...")
        try:
            original = self.captured_text_for_commander
            result = self.ai.process_text(original, mode="commander", prompt_instruction=prompt)
            logging.info("Commander done.")
            self._show_diff_or_paste(original, result)
        finally:
            self.hide_progress()

    def on_refactor(self):
        pass  # REMOVED in v2.0

    def on_redactor(self):
        pass  # REMOVED in v2.0

    def on_explain(self):
        logging.info("[Explain] Triggered (Ctrl+Shift+E)")
        print("[Explain] Triggered (Ctrl+Shift+E)")
        text = capture_selection()
        if not text:
            logging.warning("[Explain] No text selected.")
            print("[Explain] No text selected.")
            self.show_progress("No text selected")
            threading.Timer(1.0, self.hide_progress).start()
            return

        logging.info(f"[Explain] Processing text: '{text[:50]}...'")
        print(f"[Explain] Processing text: '{text[:50]}...'")
        threading.Thread(target=self.process_explain, args=(text,)).start()

    def process_explain(self, text):
        logging.info("[Explain] Sending to AI...")
        print("[Explain] Sending to AI...")
        self.show_progress("Explaining...")
        
        try:
            result = self.ai.process_text(text, mode="explain")
            logging.info("[Explain] Showing explanation...")
            print("[Explain] Showing explanation...")
            if self.gui:
                self.gui.after(0, lambda: self.gui.show_explanation(result))
            logging.info("[Explain] Done.")
        finally:
            self.hide_progress()

    def _show_diff_or_paste(self, original, result):
        """Show the diff window for review. Paste only if user accepts."""
        def on_accept(final_text):
            logging.info("[Diff] User accepted. Pasting...")
            print("[Diff] User accepted. Pasting...")
            paste_text(final_text)

        if self.gui:
            self.gui.after(0, lambda: self.gui.show_diff(original, result, on_accept))
        else:
            # No GUI available — fall back to auto-paste
            paste_text(result)

    def start_listener(self):
        # Determine backend based on OS
        system = platform.system()
        
        # On Linux with root, prefer 'keyboard' library for Wayland support
        if system == "Linux" and is_admin() and keyboard_lib:
            logging.info("Starting Hotkey Listener (Backend: keyboard library)...")
            print("Backend: 'keyboard' (Wayland/EVDEV compatible)")
            
            # keyboard library format
            try:
                # Debug hook to see what keys are detected (helps diagnose mapping issues)
                def debug_key_hook(event):
                    logging.debug(f"KEY_EVENT: {event.name} ({event.event_type})")
                keyboard_lib.hook(debug_key_hook)

                logging.info("Registering hotkey: ctrl+space")
                keyboard_lib.add_hotkey('ctrl+space', self.on_commander)
                
                logging.info("Registering hotkey: ctrl+alt+e")
                keyboard_lib.add_hotkey('ctrl+alt+e', self.on_explain)
                
                logging.info("Waiting for hotkeys...")
                keyboard_lib.wait()
            except Exception as e:
                logging.error(f"Keyboard lib error: {e}")
                logging.error(traceback.format_exc())
                print(f"Keyboard lib error: {e}")
                print("Check debug.log for full traceback.")
                
        elif pynput_keyboard:
            logging.info("Starting Hotkey Listener (Backend: pynput)...")
            print("Backend: 'pynput' (X11/Win/Mac compatible)")
            
            # pynput format: <modifier>+<key>
            hotkeys = {
                '<ctrl>+<space>': self.on_commander,
                '<ctrl>+<alt>+e': self.on_explain
            }
            
            with pynput_keyboard.GlobalHotKeys(hotkeys) as self.listener:
                try:
                    self.listener.join()
                except Exception as e:
                    logging.error(f"Listener execution error: {e}")
                    print(f"Listener error: {e}")
        else:
            print("Critical Error: No valid keyboard backend found (install 'keyboard' or 'pynput').")

    def start(self):
        print("Starting Ctrl+AI v2.0...")
        print("Hotkeys:")
        print("  Commander: Ctrl+Space")
        print("  Explain:   Ctrl+Alt+E")
        print("Press Ctrl+C to exit.")

        # Start listener in a separate thread so GUI can run in main thread
        listener_thread = threading.Thread(target=self.start_listener)
        listener_thread.daemon = True
        listener_thread.start()

        if self.gui:
            # Blocks main thread
            try:
                self.gui.start()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"GUI Error: {e}")
        else:
            # If no GUI, just keep main thread alive or join listener thread
            try:
                listener_thread.join()
            except KeyboardInterrupt:
                print("\nStopping...")

def is_admin():
    system = platform.system()
    if system == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    elif system == "Linux":
        return os.geteuid() == 0
    elif system == "Darwin":
        # macOS: root check covers most cases; Accessibility permissions
        # are a separate concern handled by the OS prompt.
        return os.geteuid() == 0
    return True

def get_privilege_warning():
    system = platform.system()
    if system == "Windows":
        return (
            " WARNING: Not running as Administrator. "
            "Global hotkeys may fail. Right-click your terminal and select 'Run as Administrator'."
        )
    elif system == "Linux":
        return (
            " WARNING: Not running as root. "
            "Global hotkeys may fail. Try: sudo python3 src/main.py  "
            "Or add your user to the 'input' group: sudo usermod -aG input $USER  (then log out/in)."
        )
    elif system == "Darwin":
        return (
            " WARNING: Not running as root. "
            "Global hotkeys may fail. Grant Accessibility access to your terminal in "
            "System Settings > Privacy & Security > Accessibility, or run with: sudo python3 src/main.py"
        )
    return ""

if __name__ == "__main__":
    if not is_admin():
        msg = get_privilege_warning()
        print(msg)
        logging.warning(msg)

    app = CtrlAIApp()
    try:
        app.start()
    except KeyboardInterrupt:
        print("\nStopping...")
