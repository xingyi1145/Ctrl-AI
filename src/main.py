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
import pystray
from PIL import Image, ImageDraw

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

def create_icon():
    # Try to load custom icon
    try:
        # Look for Ctrl+AI.png in the project root (one level up from src)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Ctrl+AI.png')
        if os.path.exists(icon_path):
             img = Image.open(icon_path)
             img = img.resize((64, 64), Image.LANCZOS)
             return img
    except Exception as e:
        logging.warning(f"Could not load Ctrl+AI.png: {e}")

    # Fallback: Generate a simple 64x64 blue image
    width = 64
    height = 64
    color1 = "blue"
    color2 = "white"

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image

class CtrlAIApp:
    def __init__(self):
        logging.info("Initializing App")
        self.running = True
        self.listener = None
        self.ai = AIHandler()
        self.gui = None
        self.captured_text_for_commander = ""
        self.current_mode = "commander"
        self.active_toast = None

        if GUI_AVAILABLE:
            self.gui = OverlayApp(submit_callback=self.on_commander_submit)
            
            # Set window icon if available
            try:
                # Look for Ctrl+AI.png in the project root (one level up from src)
                icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Ctrl+AI.png')
                if os.path.exists(icon_path):
                    # For CustomTkinter/Tkinter on Windows, iconbitmap expects .ico mostly, 
                    # but wm_iconphoto allows PNG.
                    from PIL import ImageTk
                    icon_img = ImageTk.PhotoImage(file=icon_path)
                    self.gui.wm_iconphoto(True, icon_img)
            except Exception as e:
                logging.warning(f"Could not set window icon: {e}")

    def stop_app(self, icon, item):
        logging.info("Stopping app from tray...")
        icon.stop()
        if self.gui:
            self.gui.quit()
        os._exit(0)

    def run_tray_icon(self):
        icon = pystray.Icon("Ctrl-AI", create_icon(), menu=pystray.Menu(
            pystray.MenuItem("Quit", self.stop_app)
        ))
        icon.run()

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
            self.current_mode = "commander"
            self.gui.after(0, lambda: self._show_overlay_for_mode("commander"))
        else:
            print("[Commander] No text selected.")

    def _show_overlay_for_mode(self, mode):
        self.gui.configure_mode(mode)
        self.gui.show_overlay()

    def on_commander_submit(self, prompt):
        print(f"[{self.current_mode.capitalize()}] Prompt: {prompt}")
        if self.current_mode == "explain":
            threading.Thread(target=self.process_explain, args=(prompt,)).start()
        else:
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
        logging.info("[Explain] Triggered (Ctrl+Alt+E)")
        print("[Explain] Triggered (Ctrl+Alt+E)")

        if not self.gui:
            print("Explain mode requires GUI (tkinter missing).")
            return

        text = capture_selection()
        if not text:
            logging.warning("[Explain] No text selected.")
            print("[Explain] No text selected.")
            self.show_progress("No text selected")
            threading.Timer(1.0, self.hide_progress).start()
            return

        print(f"[Explain] Context captured: '{text[:20]}...'")
        self.captured_text_for_commander = text
        self.current_mode = "explain"
        self.gui.after(0, lambda: self._show_overlay_for_mode("explain"))

    def process_explain(self, user_question):
        logging.info(f"[Explain] Question: {user_question}")
        print(f"[Explain] Question: {user_question}")
        self.show_progress("Explaining...")
        
        try:
            original = self.captured_text_for_commander
            result = self.ai.process_text(original, mode="explain", prompt_instruction=user_question)
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

        # Start tray icon in background
        threading.Thread(target=self.run_tray_icon, daemon=True).start()

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
