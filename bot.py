import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
import subprocess
import queue
import shutil

# ------------------------ Configuration ------------------------
MODEL_NAME = "tinyllama"  # model name
USE_CLI = True
SYSTEM_PROMPT = "You are a helpful assistant. Keep replies concise and friendly."
OLLAMA_TIMEOUT = 60  # seconds

# Visual options
USER_BG = "#DCF8C6"    # Messenger green (user)
BOT_BG = "#FFFFFF"     # White bubble (bot)
USER_FG = "#000000"    # Text color (user)
BOT_FG = "#000000"     # Text color (bot)
WINDOW_BG = "#F0F2F5"

# ------------------------ Helper functions ------------------------
def timestamp():
    return datetime.now().strftime('%H:%M')

def ollama_cli_query(prompt_text, model=MODEL_NAME, timeout=OLLAMA_TIMEOUT):
    """
    Calls Ollama via CLI and returns the model's output.
    """
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt_text}"
    cmd = ["ollama", "run", model]
    try:
        if shutil.which("ollama") is None:
            raise FileNotFoundError("`ollama` not found in PATH.")
        proc = subprocess.run(cmd, input=full_prompt, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"Ollama error {proc.returncode}: {proc.stderr}")
        return proc.stdout.strip()
    except subprocess.TimeoutExpired:
        return "(error) model call timed out"
    except Exception as e:
        return f"(error) {e}"

# ------------------------ GUI ------------------------
class MessengerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiny Llama Messenger")
        self.configure(bg=WINDOW_BG)
        self.geometry("640x720")
        self.minsize(420, 420)

        # Header
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(top, text="Tiny Llama Chat", font=(None, 16, "bold")).pack(side=tk.LEFT)
        self.status_label = ttk.Label(top, text="Ready", font=(None, 9))
        self.status_label.pack(side=tk.RIGHT)

        # Chat area (Canvas + Scrollbar)
        self.chat_frame = ttk.Frame(self)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.chat_frame, bg=WINDOW_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.chat_frame, orient="vertical", command=self.canvas.yview)
        self.messages_container = ttk.Frame(self.canvas)

        self.canvas.create_window((0, 0), window=self.messages_container, anchor="nw")
        self.chat_frame.bind("<Configure>", lambda e: self.canvas.itemconfig(1, width=e.width))
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.messages_container.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Entry area
        entry_frame = ttk.Frame(self)
        entry_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.msg_var = tk.StringVar()
        self.entry = ttk.Entry(entry_frame, textvariable=self.msg_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", self.on_send)

        self.send_btn = ttk.Button(entry_frame, text="Send", command=self.on_send)
        self.send_btn.pack(side=tk.RIGHT)

        # Data
        self.history = []
        self.ui_queue = queue.Queue()
        self.after(100, self._poll_queue)

        # Initial bot message
        self._add_message_widget("Hey — I'm Tiny LLaMA. How can I help you today?", from_user=False)

    # ---------------- Message helpers ----------------
    def _add_message_widget(self, text, from_user=False):
        outer = ttk.Frame(self.messages_container)
        outer.pack(fill=tk.X, expand=True, padx=10, pady=4)

        # dynamic wrap width relative to current window size
        wraplength = max(self.winfo_width() - 180, 260)

        inner_frame = tk.Frame(outer, bg=WINDOW_BG)
        inner_frame.pack(fill=tk.X)

        if from_user:
            bubble = tk.Label(
                inner_frame,
                text=text,
                justify=tk.LEFT,
                wraplength=wraplength,
                bg=USER_BG,
                fg=USER_FG,
                padx=12,
                pady=8,
                font=("Segoe UI", 10),
                anchor='e',
                bd=0,
                relief='flat'
            )
            bubble.pack(anchor='e', padx=(80, 0), ipadx=4, ipady=2)
            meta = tk.Label(
                inner_frame,
                text=timestamp(),
                font=("Segoe UI", 8),
                bg=WINDOW_BG,
                anchor='e'
            )
            meta.pack(anchor='e', padx=(80, 0))
        else:
            bubble = tk.Label(
                inner_frame,
                text=text,
                justify=tk.LEFT,
                wraplength=wraplength,
                bg=BOT_BG,
                fg=BOT_FG,
                padx=12,
                pady=8,
                font=("Segoe UI", 10),
                anchor='w',
                bd=0,
                relief='flat'
            )
            bubble.pack(anchor='w', padx=(0, 80), ipadx=4, ipady=2)
            meta = tk.Label(
                inner_frame,
                text=timestamp(),
                font=("Segoe UI", 8),
                bg=WINDOW_BG,
                anchor='w'
            )
            meta.pack(anchor='w', padx=(0, 80))

        # auto-scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _add_user_message(self, text):
        """Adds a user message to the chat and stores it in history."""
        self._add_message_widget(text, from_user=True)
        self.history.append(("user", text))

    def _add_bot_message(self, text):
        """Adds a bot message to the chat and stores it in history."""
        self._add_message_widget(text, from_user=False)
        self.history.append(("bot", text))

    # ---------------- Model worker ----------------
    def _model_worker(self, prompt):
        try:
            self.ui_queue.put(("status", "Thinking..."))
            if USE_CLI:
                response = ollama_cli_query(prompt)
            else:
                response = "(HTTP mode not implemented)"
        except Exception as e:
            response = f"(error) {e}"
        self.ui_queue.put(("response", response))

    def on_send(self, event=None):
        text = self.msg_var.get().strip()
        if not text:
            return
        self._add_user_message(text)
        self.msg_var.set("")
        self.send_btn.state(["disabled"])
        self.entry.state(["disabled"])

        conv = [f"{'User' if who=='user' else 'Assistant'}: {msg}" for who, msg in self.history]
        prompt_text = "\n".join(conv[-12:])  # limit to recent turns

        thread = threading.Thread(target=self._model_worker, args=(prompt_text,), daemon=True)
        thread.start()

    # ---------------- Queue polling ----------------
    def _poll_queue(self):
        try:
            while True:
                item = self.ui_queue.get_nowait()
                kind, data = item
                if kind == "status":
                    self.status_label.config(text=data)
                elif kind == "response":
                    self._add_bot_message(data)
                    self.status_label.config(text="Ready")
                    self.send_btn.state(["!disabled"])
                    self.entry.state(["!disabled"])
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

# ------------------------ Run ------------------------
if __name__ == "__main__":
    if USE_CLI and shutil.which("ollama") is None:
        print("⚠️ Ollama not found. Please install it or add to PATH.")
    app = MessengerApp()
    app.mainloop()