"""
PDF Locker + Master Key (single-file)
- Lock PDFs with a user password
- Save a plaintext sidecar (lockedfile.pw) containing the user password (used for master-key recovery)
- Hard-coded master keys (you provided 3)
- UI to add more master keys (saved to master_keys.txt)
- After 3 wrong password attempts, a Master Key popup appears; if matched, it will try to recover/open the PDF
Requirements:
    pip install pikepdf
Run with Python 3.8+
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pikepdf
import os

# ---------------------------
# Hard-coded master keys (you asked)
# ---------------------------
MASTER_KEYS = [
    "rajashree@1234",
    "rajashree####",
    "rajashree%%%%"
]

MASTER_KEYS_FILE = "master_keys.txt"  # optional persistent storage for added keys

# Try to load saved keys (keeps the hardcoded ones plus user-added)
def load_master_keys_from_file():
    if not os.path.exists(MASTER_KEYS_FILE):
        return
    try:
        with open(MASTER_KEYS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                k = line.strip()
                if k and k not in MASTER_KEYS:
                    MASTER_KEYS.append(k)
    except Exception:
        pass

def save_master_key_to_file(key):
    try:
        with open(MASTER_KEYS_FILE, "a", encoding="utf-8") as f:
            f.write(key.replace("\n","") + "\n")
    except Exception:
        pass


# load on start
load_master_keys_from_file()

# ---------------------------
# Utility functions
# ---------------------------
def is_pdf_locked(file_path):
    try:
        with pikepdf.open(file_path):
            return False
    except pikepdf.PasswordError:
        return True
    except Exception:
        # treat other errors as locked/unopenable
        return True

def save_sidecar_password(locked_pdf_path, password):
    """Save the user password in a sidecar file (plain text) next to the locked PDF.
    Sidecar filename: <base>.pw
    """
    try:
        base, _ = os.path.splitext(locked_pdf_path)
        sidecar = base + ".pw"
        with open(sidecar, "w", encoding="utf-8") as f:
            f.write(password)
    except Exception:
        pass

def read_sidecar_password(pdf_path):
    try:
        base, _ = os.path.splitext(pdf_path)
        sidecar = base + ".pw"
        if not os.path.exists(sidecar):
            return None
        with open(sidecar, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

# ---------------------------
# Main App
# ---------------------------
class PDFLockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Locker + Master Key")
        self.root.geometry("920x640")
        self.root.resizable(False, False)

        # state
        self.file_path = None
        self.is_locked = False
        self.failed_attempts = 0

        # left frame: file + lock/unlock
        left = tk.Frame(root, padx=12, pady=12)
        left.pack(side="left", fill="y")

        tk.Label(left, text="PDF Locker", font=("Helvetica", 18, "bold")).pack(pady=(0,8))

        tk.Button(left, text="Select PDF", width=20, command=self.select_pdf).pack(pady=6)
        self.lbl_file = tk.Label(left, text="No file selected", fg="red")
        self.lbl_file.pack()

        tk.Label(left, text="Enter password to Lock/Unlock:", pady=6).pack()
        self.pw_entry = tk.Entry(left, show="*", width=36)
        self.pw_entry.pack()

        # confirm for locking
        tk.Label(left, text="Retype password (for Lock):", pady=6).pack()
        self.pw_confirm_entry = tk.Entry(left, show="*", width=36)
        self.pw_confirm_entry.pack()

        tk.Button(left, text="Lock PDF (save as new file)", width=22, command=self.lock_pdf).pack(pady=(12,6))
        tk.Button(left, text="Unlock PDF (use entered password)", width=22, command=self.unlock_pdf).pack(pady=6)

        # Manual master key unlock (if user wants to try one of the master keys manually)
        tk.Label(left, text="Manual Master Key (try manually):", pady=8).pack()
        self.manual_mk_entry = tk.Entry(left, show="*", width=36)
        self.manual_mk_entry.pack()
        tk.Button(left, text="Use Manual Master Key", width=22, command=self.use_manual_master).pack(pady=(6,0))

        # status
        self.status_label = tk.Label(left, text="Status: Ready", fg="blue")
        self.status_label.pack(pady=(18,0))

        # right frame: master key management
        right = tk.Frame(root, padx=12, pady=12, relief="groove", borderwidth=1)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Master Key Management", font=("Helvetica", 16, "bold")).pack(pady=(4,8))

        tk.Label(right, text="Hard-coded keys (preloaded):").pack(anchor="w")
        self.hk_listbox = tk.Listbox(right, height=6)
        self.hk_listbox.pack(fill="x", padx=6, pady=(4,8))
        self.refresh_master_keys_listbox()

        # add new master key section
        add_frame = tk.Frame(right)
        add_frame.pack(pady=(6,4), fill="x", padx=6)

        tk.Label(add_frame, text="Add Master Key:").grid(row=0, column=0, sticky="w")
        self.add_mk_entry = tk.Entry(add_frame, show="*", width=30)
        self.add_mk_entry.grid(row=0, column=1, padx=6)
        tk.Label(add_frame, text="Confirm:").grid(row=1, column=0, sticky="w")
        self.add_mk_confirm = tk.Entry(add_frame, show="*", width=30)
        self.add_mk_confirm.grid(row=1, column=1, padx=6)
        tk.Button(add_frame, text="Add & Save", command=self.add_master_key).grid(row=2, column=0, columnspan=2, pady=8)
        
        #Edit button
        tk.Button(add_frame, text="Edit", command=self.edit_master_key).grid(row=3,column=0,columnspan=3, pady=8)

        tk.Label(right, text="Notes:", anchor="w").pack(fill="x", padx=6, pady=(8,0))
        notes = ("• If password is entered wrong 3 times when unlocking, a Master Key dialog will appear.\n"
                 "• Master Key will try to recover saved password (sidecar .pw) and open the PDF.\n"
                 "• Sidecar file is created when you lock a PDF (saved alongside the locked PDF).\n"
                 "• Master keys are stored plaintext in master_keys.txt (if you press Add & Save).")
        tk.Label(right, text=notes, justify="left", wraplength=340).pack(padx=6, pady=(2,6))

    # -------------------------
    def refresh_master_keys_listbox(self):
        self.hk_listbox.delete(0, tk.END)
        for k in MASTER_KEYS:
            # show masked keys (partial)
            if len(k) > 6:
                display = k[:3] + "*" * (len(k) - 6) + k[-3:]
            else:
                display = "*" * len(k)
            self.hk_listbox.insert(tk.END, display)

    # -------------------------
    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return
        self.file_path = path
        self.is_locked = is_pdf_locked(path)
        self.failed_attempts = 0
        if self.is_locked:
            self.lbl_file.config(text=os.path.basename(path) + " (locked)", fg="orange")
            self.status_label.config(text="Status: Locked PDF selected")
        else:
            self.lbl_file.config(text=os.path.basename(path) + " (unlocked)", fg="green")
            self.status_label.config(text="Status: Unlocked PDF selected")

    # -------------------------
    def lock_pdf(self):
        if not self.file_path:
            messagebox.showerror("Error", "Select a PDF file first")
            return

        pwd = self.pw_entry.get()
        pwdc = self.pw_confirm_entry.get()
        if not pwd:
            messagebox.showerror("Error", "Enter a password to lock the PDF")
            return
        if pwd != pwdc:
            messagebox.showerror("Error", "Passwords do not match for locking")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 filetypes=[("PDF Files", "*.pdf")],
                                                 initialfile=f"locked_{os.path.basename(self.file_path)}")
        if not save_path:
            return

        try:
            pdf = pikepdf.open(self.file_path)
            pdf.save(save_path, encryption=pikepdf.Encryption(owner=pwd, user=pwd, R=6))
            # Save sidecar with the password (plain text) so master key can recover it later
            save_sidecar_password(save_path, pwd)
            self.is_locked = True
            self.file_path = save_path
            self.lbl_file.config(text=os.path.basename(self.file_path) + " (locked)", fg="orange")
            self.status_label.config(text=f"Status: Locked and saved -> {os.path.basename(save_path)}")
            messagebox.showinfo("Success", f"PDF locked and saved as:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to lock PDF:\n{e}")

    # -------------------------
    def unlock_pdf(self):
        if not self.file_path:
            messagebox.showerror("Error", "Select a PDF file first")
            return

        entered_pw = self.pw_entry.get()

        # first try with entered password
        try:
            with pikepdf.open(self.file_path, password=entered_pw):
                # success
                self._save_unlocked_via_password(entered_pw)
                self.failed_attempts = 0
                return
        except pikepdf.PasswordError:
            # wrong password
            self.failed_attempts += 1
            remaining = max(0, 3 - self.failed_attempts)
            if self.failed_attempts < 3:
                messagebox.showerror("Wrong Password", f"Wrong password. {remaining} attempts left.")
                self.status_label.config(text=f"Status: Wrong password ({self.failed_attempts}/3)")
                return
            # reached 3 attempts -> show master key popup
            self.failed_attempts = 0
            self.status_label.config(text="Status: 3 wrong attempts -> asking Master Key")
            mk = simpledialog.askstring("Master Key Required", "You entered wrong password 3 times.\nEnter Master Key:", show="*")
            if mk is None:
                messagebox.showwarning("Cancelled", "Master key prompt cancelled.")
                return
            # check master key against list
            if mk in MASTER_KEYS:
                # first try to recover the stored password from sidecar
                recovered = read_sidecar_password(self.file_path)
                if recovered:
                    try:
                        with pikepdf.open(self.file_path, password=recovered):
                            self._save_unlocked_via_password(recovered)
                            messagebox.showinfo("Unlocked", "PDF unlocked using Master Key (recovered password).")
                            return
                    except Exception:
                        # fallthrough to next attempts
                        pass
                # if sidecar not found or failed, try opening without password (some locked PDFs might allow owner open)
                try:
                    with pikepdf.open(self.file_path):
                        # opened without password (rare), save
                        self._save_unlocked_via_password(None)
                        messagebox.showinfo("Unlocked", "PDF unlocked using Master Key (no password needed).")
                        return
                except Exception:
                    pass
                # lastly try using the master key itself as a password
                try:
                    with pikepdf.open(self.file_path, password=mk):
                        self._save_unlocked_via_password(mk)
                        messagebox.showinfo("Unlocked", "PDF unlocked using Master Key (used as password).")
                        return
                except Exception:
                    messagebox.showerror("Failed", "Master Key recognized but could not open the PDF.")
                    return
            else:
                messagebox.showerror("Invalid", "Entered master key is not valid.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF:\n{e}")
            return

    def _save_unlocked_via_password(self, password_used):
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 filetypes=[("PDF Files", "*.pdf")],
                                                 initialfile=f"unlocked_{os.path.basename(self.file_path)}")
        if not save_path:
            return
        try:
            if password_used is None:
                # open without password and save
                with pikepdf.open(self.file_path) as pdf:
                    pdf.save(save_path)
            else:
                with pikepdf.open(self.file_path, password=password_used) as pdf:
                    pdf.save(save_path)
            messagebox.showinfo("Saved", f"Unlocked PDF saved as:\n{save_path}")
            self.status_label.config(text=f"Status: Unlocked and saved -> {os.path.basename(save_path)}")
            # Optionally update state (not changing the locked file itself)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save unlocked PDF:\n{e}")

    # -------------------------
    def use_manual_master(self):
        if not self.file_path:
            messagebox.showerror("Error", "Select a PDF file first")
            return
        mk = self.manual_mk_entry.get()
        if not mk:
            messagebox.showerror("Error", "Enter a manual master key to try")
            return
        if mk not in MASTER_KEYS:
            messagebox.showerror("Invalid", "Manual master key not in stored master keys")
            return
        # try recovery flow same as above
        recovered = read_sidecar_password(self.file_path)
        if recovered:
            try:
                with pikepdf.open(self.file_path, password=recovered):
                    self._save_unlocked_via_password(recovered)
                    messagebox.showinfo("Unlocked", "PDF unlocked using manual Master Key (recovered password).")
                    return
            except Exception:
                pass
        try:
            with pikepdf.open(self.file_path):
                self._save_unlocked_via_password(None)
                messagebox.showinfo("Unlocked", "PDF unlocked using manual Master Key (no password needed).")
                return
        except Exception:
            pass
        try:
            with pikepdf.open(self.file_path, password=mk):
                self._save_unlocked_via_password(mk)
                messagebox.showinfo("Unlocked", "PDF unlocked using manual Master Key (used as password).")
                return
        except Exception:
            messagebox.showerror("Failed", "Manual Master Key recognized but could not open the PDF.")
            return

    # -------------------------
    def add_master_key(self):
        k = self.add_mk_entry.get().strip()
        kc = self.add_mk_confirm.get().strip()
        if not k:
            messagebox.showerror("Error", "Master key is empty")
            return
        if k != kc:
            messagebox.showerror("Error", "Master keys do not match")
            return
        if k in MASTER_KEYS:
            messagebox.showinfo("Exists", "This master key already exists")
            return
        MASTER_KEYS.append(k)
        save_master_key_to_file(k)
        self.add_mk_entry.delete(0, tk.END)
        self.add_mk_confirm.delete(0, tk.END)
        self.refresh_master_keys_listbox()
        messagebox.showinfo("Added", "Master key added and saved to file")
    
    #-----------------------------
    def edit_master_key(self):
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Master Keys")
        edit_win.geometry("400x350")
        edit_win.resizable(False, False)

        tk.Label(edit_win, text="Stored Master Keys",
                font=("Helvetica", 14, "bold")).pack(pady=10)

        listbox = tk.Listbox(edit_win, height=10, width=40)
        listbox.pack(padx=10, pady=5)

        # Populate listbox (masked display)
        for k in MASTER_KEYS:
            if len(k) > 6:
                display = k[:3] + "*" * (len(k) - 6) + k[-3:]
            else:
                display = "*" * len(k)
            listbox.insert(tk.END, display)

        def delete_selected():
            sel = listbox.curselection()
            if not sel:
                messagebox.showerror("Error", "Select a master key to remove")
                return

            idx = sel[0]
            key_to_remove = MASTER_KEYS[idx]

            if not messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to permanently remove this master key?"
            ):
                return

            # Remove from memory
            MASTER_KEYS.remove(key_to_remove)

            # Rewrite file (remove deleted key)
            try:
                with open(MASTER_KEYS_FILE, "w", encoding="utf-8") as f:
                    for k in MASTER_KEYS:
                        f.write(k + "\n")
            except Exception:
                pass

            listbox.delete(idx)
            self.refresh_master_keys_listbox()
            messagebox.showinfo("Removed", "Master key removed successfully")

        tk.Button(edit_win, text="Remove Selected Master Key",
                fg="red", command=delete_selected).pack(pady=12)

        
        
        

# ---------------------------
def main():
    root = tk.Tk()
    app = PDFLockerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()