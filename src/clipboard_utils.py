import time
import platform
import threading
import pyperclip
try:
    from pynput.keyboard import Key, Controller
    keyboard_controller = Controller()
except ImportError:
    keyboard_controller = None

try:
    import keyboard as keyboard_lib
except ImportError:
    keyboard_lib = None

def capture_selection(timeout=0.5):
    """
    Captures the currently selected text by manipulating the clipboard.
    """
    # 1. Save current clipboard
    try:
        temp_backup = pyperclip.paste()
    except Exception:
        temp_backup = ""

    # 2. Clear clipboard to detect new copy action
    try:
        pyperclip.copy("")
    except Exception:
        pass

    # 3. Simulate Copy
    system = platform.system()
    
    # Use 'keyboard' library on Linux if available (for Wayland support)
    if system == "Linux" and keyboard_lib:
        time.sleep(0.05)
        keyboard_lib.send('ctrl+c')
    elif keyboard_controller:
        # Fallback to pynput
        if system == "Darwin":
            modifier = Key.cmd
        else:
            modifier = Key.ctrl

        time.sleep(0.05) 
        
        with keyboard_controller.pressed(modifier):
            keyboard_controller.press('c')
            keyboard_controller.release('c')
    else:
        print("Error: No keyboard controller available.")
        return ""
    
    # 4. Wait for clipboard to update
    start_time = time.time()
    captured_text = ""
    
    while time.time() - start_time < timeout:
        try:
            current_content = pyperclip.paste()
            if current_content != "":
                captured_text = current_content
                break
        except Exception:
            pass
        time.sleep(0.05) 

    # 5. Handle result
    if captured_text:
        return captured_text
    else:
        if temp_backup:
            pyperclip.copy(temp_backup)
        return ""

def paste_text(text):
    """
    Pastes the given text at the current cursor location.
    """
    pyperclip.copy(text)
    system = platform.system()
    
    if system == "Linux" and keyboard_lib:
        # Important: Wait a split second for focus to return if triggered by UI
        time.sleep(0.1) 
        keyboard_lib.send('ctrl+v')
    elif keyboard_controller:
        if system == "Darwin":
            modifier = Key.cmd
        else:
            modifier = Key.ctrl
        
        with keyboard_controller.pressed(modifier):
            keyboard_controller.press('v')
            keyboard_controller.release('v')
