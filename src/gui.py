import customtkinter as ctk
import threading
import time

# Set appearance mode and default color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OverlayApp(ctk.CTk):
    def __init__(self, submit_callback=None):
        super().__init__()

        self.submit_callback = submit_callback
        self.history = []
        self.history_index = -1
        
        # Configure window
        self.title("Ctrl+AI Commander")
        self.geometry("600x60")
        
        # Make the window frameless
        self.overrideredirect(True)
        
        # Make it stay on top
        self.attributes('-topmost', True)
        self.resizable(False, False)

        # Center the window on the screen
        self.center_window()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Input Frame
        self.input_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1e1e1e")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Icon/Label (Left)
        self.label = ctk.CTkLabel(self.input_frame, text="✨ AI", font=("Arial", 14, "bold"), width=40)
        self.label.grid(row=0, column=0, padx=10, pady=10)

        # Entry Field
        self.entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Type a command (e.g., 'Fix grammar', 'Make professional')...",
            border_width=0,
            fg_color="transparent",
            font=("Arial", 14)
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry.bind("<Return>", self.on_submit)
        self.entry.bind("<Escape>", self.hide_overlay)
        self.entry.bind("<Up>", self._history_up)
        self.entry.bind("<Down>", self._history_down)

    def center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = 600
        height = 60
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 3) - (height // 2) # Slightly above center
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_overlay(self):
        self.deiconify()
        self.attributes('-topmost', True)
        self.lift()
        self.focus_force()
        self.entry.focus_set()
        self.entry.delete(0, 'end')
        self.history_index = -1

    def hide_overlay(self, event=None):
        self.withdraw()

    def on_submit(self, event=None):
        text = self.entry.get()
        if text and self.submit_callback:
            # Save to history
            if not self.history or self.history[-1] != text:
                self.history.append(text)
            self.history_index = -1
            self.hide_overlay()
            self.submit_callback(text)

    def _history_up(self, event=None):
        if not self.history:
            return "break"
        if self.history_index == -1:
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        self.entry.delete(0, "end")
        self.entry.insert(0, self.history[self.history_index])
        return "break"

    def _history_down(self, event=None):
        if not self.history or self.history_index == -1:
            return "break"
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.history[self.history_index])
        else:
            self.history_index = -1
            self.entry.delete(0, "end")
        return "break"

    def start(self):
        self.withdraw() # Start hidden
        self.mainloop()

    def show_toast(self, message="Processing...", duration=None):
        """Displays a small toast notification near the center of the screen."""
        toast = ProcessingToast(self, message)
        if duration:
            self.after(int(duration * 1000), toast.destroy)
        return toast

    def show_diff(self, original_text, new_text, on_accept_callback):
        """Opens the DiffWindow for human review before pasting."""
        DiffWindow(self, original_text, new_text, on_accept_callback)

    def show_explanation(self, content):
        """Opens the ExplanationWindow to display AI explanation (read-only)."""
        ExplanationWindow(self, content)

class DiffWindow(ctk.CTkToplevel):
    """Human-in-the-loop review window showing original vs AI proposal side-by-side."""

    def __init__(self, master, original_text, new_text, on_accept_callback=None):
        super().__init__(master)

        self.on_accept_callback = on_accept_callback

        # --- Window setup ---
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(fg_color="#1a1a1a")

        width, height = 820, 420
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # --- Title bar ---
        title_bar = ctk.CTkFrame(self, height=30, fg_color="#252525", corner_radius=0)
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 0))
        title_label = ctk.CTkLabel(title_bar, text="\U0001f50d  Review Changes", font=("Arial", 13, "bold"), text_color="#cccccc")
        title_label.pack(side="left", padx=10)

        # Allow dragging the window
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._on_drag)

        # --- Grid weights ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Left panel: Original ---
        left_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", border_width=2, border_color="#5c3a3a", corner_radius=8)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(6, 3), pady=6)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        left_label = ctk.CTkLabel(left_frame, text="Original Text", font=("Arial", 12, "bold"), text_color="#e06060")
        left_label.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="w")

        self.original_box = ctk.CTkTextbox(left_frame, fg_color="#141414", text_color="#d4d4d4",
                                           font=("Consolas", 13), wrap="word", corner_radius=6,
                                           border_width=1, border_color="#5c3a3a")
        self.original_box.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.original_box.insert("1.0", original_text)
        self.original_box.configure(state="disabled")  # read-only

        # --- Right panel: AI Proposal (editable) ---
        right_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", border_width=2, border_color="#3a5c3a", corner_radius=8)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(3, 6), pady=6)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        right_label = ctk.CTkLabel(right_frame, text="AI Proposal  (editable)", font=("Arial", 12, "bold"), text_color="#60e060")
        right_label.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="w")

        self.proposal_box = ctk.CTkTextbox(right_frame, fg_color="#141414", text_color="#d4d4d4",
                                           font=("Consolas", 13), wrap="word", corner_radius=6,
                                           border_width=1, border_color="#3a5c3a")
        self.proposal_box.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.proposal_box.insert("1.0", new_text)

        # --- Bottom button bar ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(0, 8))

        reject_btn = ctk.CTkButton(btn_frame, text="\u2718  Reject (Esc)", width=160,
                                   fg_color="#4a2020", hover_color="#6a3030",
                                   text_color="#ff9090", font=("Arial", 13, "bold"),
                                   command=self._reject)
        reject_btn.pack(side="left", padx=10)

        accept_btn = ctk.CTkButton(btn_frame, text="\u2714  Accept (Enter)", width=160,
                                   fg_color="#204a20", hover_color="#306a30",
                                   text_color="#90ff90", font=("Arial", 13, "bold"),
                                   command=self._accept)
        accept_btn.pack(side="left", padx=10)

        # --- Key bindings ---
        self.bind("<Return>", lambda e: self._accept())
        self.bind("<Escape>", lambda e: self._reject())

        # Focus so key bindings work immediately
        self.after(100, self.focus_force)

    # --- Drag support ---
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    # --- Actions ---
    def _accept(self):
        final_text = self.proposal_box.get("1.0", "end-1c")
        
        # Hide window immediately and force update to return focus to underlying app
        self.withdraw()
        self.update_idletasks()
        time.sleep(0.2)  # Give OS time to switch focus back

        if self.on_accept_callback:
            self.on_accept_callback(final_text)
        self.destroy()

    def _reject(self):
        self.destroy()


class ExplanationWindow(ctk.CTkToplevel):
    """Read-only window displaying the AI's explanation of selected text."""

    def __init__(self, master, content):
        super().__init__(master)

        # --- Window setup ---
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(fg_color="#1a1a1a")

        width, height = 620, 400
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # --- Title bar ---
        title_bar = ctk.CTkFrame(self, height=30, fg_color="#252525", corner_radius=0)
        title_bar.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 0))
        title_label = ctk.CTkLabel(title_bar, text="\U0001f4a1  AI Explanation", font=("Arial", 13, "bold"), text_color="#cccccc")
        title_label.pack(side="left", padx=10)

        # Allow dragging
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._on_drag)

        # --- Grid ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Content textbox (read-only) ---
        content_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", border_width=2, border_color="#3a4a6a", corner_radius=8)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        self.text_box = ctk.CTkTextbox(content_frame, fg_color="#141414", text_color="#d4d4d4",
                                       font=("Consolas", 13), wrap="word", corner_radius=6,
                                       border_width=1, border_color="#3a4a6a")
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.text_box.insert("1.0", content)
        self.text_box.configure(state="disabled")  # read-only

        # --- Close button ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=(0, 8))

        close_btn = ctk.CTkButton(btn_frame, text="\u2718  Close (Esc)", width=160,
                                  fg_color="#2a3a5a", hover_color="#3a4a6a",
                                  text_color="#90b0ff", font=("Arial", 13, "bold"),
                                  command=self.destroy)
        close_btn.pack()

        # --- Key binding ---
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(100, self.focus_force)

    # --- Drag support ---
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")


class ProcessingToast(ctk.CTkToplevel):
    def __init__(self, master, message="Processing..."):
        super().__init__(master)
        
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Style
        self.configure(fg_color="#1e1e1e")
        
        # Content
        label = ctk.CTkLabel(self, text=f"⏳ {message}", font=("Arial", 12), text_color="white")
        label.pack(padx=20, pady=10)
        
        # Position (Center of screen for simplicity)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2) + 100 # Slightly below center
        self.geometry(f"+{x}+{y}")
        
    def hide(self):
        self.destroy()

# Test the UI standalone
if __name__ == "__main__":
    def mock_submit(text):
        print(f"Submitted: {text}")

    app = OverlayApp(submit_callback=mock_submit)
    # Simulate a trigger after 2 seconds
    def trigger():
        time.sleep(2)
        print("Showing overlay")
        app.show_overlay()
        
        time.sleep(2)
        print("Showing toast")
        # Use .after to run in main thread
        app.after(0, lambda: app.show_toast("Refactoring...", duration=2))
    
    threading.Thread(target=trigger).start()
    app.start()
