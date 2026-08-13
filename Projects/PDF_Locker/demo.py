# Import Tkinter for GUI
import tkinter as tk
from tkinter import filedialog, messagebox

# Import pikepdf for PDF encryption
import pikepdf

# OS module for file handling
import os


# -------------------------------
# Function to check if PDF is locked
# -------------------------------
def is_pdf_locked(file_path):
    try:
        # Try opening PDF without password
        with pikepdf.open(file_path):
            return False  # PDF is NOT locked
    except pikepdf.PasswordError:
        return True   # PDF IS locked
    except Exception as e:
        # Any other error
        print(f"Error checking PDF: {e}")
        return None


# -------------------------------
# Main Application Class
# -------------------------------
class PDFLockerApp:
    def __init__(self, root):
        self.root = root

        # Window settings
        self.root.title("PDF Password Locker")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        # App title label
        tk.Label(
            root,
            text="Password-Protected PDF Locker",
            font=("Helvetica", 14, "bold")
        ).pack(pady=10)

        # Button to select PDF
        self.select_btn = tk.Button(
            root,
            text="Select PDF File",
            command=self.select_file
        )
        self.select_btn.pack(pady=10)

        # Label to show selected file status
        self.file_label = tk.Label(
            root,
            text="No file selected",
            fg="red"
        )
        self.file_label.pack()

        # Password entry label
        tk.Label(
            root,
            text="Enter password to lock PDF:"
        ).pack(pady=(15, 0))

        # Password input field (hidden by *)
        self.password_entry = tk.Entry(
            root,
            show="*",
            width=20
        )
        self.password_entry.pack()

        # Label to show password strength feedback
        self.feedback_label = tk.Label(
            root,
            text="",
            fg="red",
            font=("Arial", 9)
        )
        self.feedback_label.pack()

        # Validate password on every key release
        self.password_entry.bind("<KeyRelease>", self.validate_password)

        # Eye button to show/hide password
        self.password_shown = False
        self.eye_btn = tk.Button(
            root,
            text="👁️",
            width=4,
            command=self.toggle_password_visibility,
            relief="flat"
        )

        # Manually positioning the eye button
        self.eye_btn.place(
            x=340,
            y=self.password_entry.winfo_y() + 150
        )

        # Confirm password label
        tk.Label(
            root,
            text="Retype password:"
        ).pack(pady=(10, 0))

        # Confirm password entry
        self.confirm_entry = tk.Entry(
            root,
            show="*",
            width=20
        )
        self.confirm_entry.pack()

        # Button to lock the PDF
        self.lock_btn = tk.Button(
            root,
            text="Lock PDF",
            command=self.lock_pdf
        )
        self.lock_btn.pack(pady=20)

        # Store selected file path
        self.file_path = None

        # Flag to check if PDF is already locked
        self.is_locked = False


    # -------------------------------
    # Toggle password visibility
    # -------------------------------
    def toggle_password_visibility(self):
        if self.password_shown:
            # Hide password
            self.password_entry.config(show="*")
            self.eye_btn.config(text="👁️")
        else:
            # Show password
            self.password_entry.config(show="")
            self.eye_btn.config(text="👁️*")

        self.password_shown = not self.password_shown


    # -------------------------------
    # Select PDF file
    # -------------------------------
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if file_path:
            self.file_path = file_path

            # Check if PDF is already locked
            locked = is_pdf_locked(file_path)

            if locked is None:
                self.file_label.config(text="Error checking file", fg="red")
            elif locked:
                self.file_label.config(text="PDF is already locked", fg="orange")
                self.is_locked = True
            else:
                self.file_label.config(
                    text=os.path.basename(file_path),
                    fg="green"
                )
                self.is_locked = False
        else:
            self.file_label.config(text="No file selected", fg="red")


    # -------------------------------
    # Validate password strength
    # -------------------------------
    def validate_password(self, event=None):
        password = self.password_entry.get()
        messages = []

        # Check for spaces
        if " " in password:
            messages.append("Password should not contain spaces.")

        # Password rules
        if len(password) < 8:
            messages.append("8+ characters")
        if not any(char.isdigit() for char in password):
            messages.append("1 digit")
        if not any(char.isupper() for char in password):
            messages.append("1 uppercase")
        if not any(char.islower() for char in password):
            messages.append("1 lowercase")
        if not any(char in "!@#$%^&*()-_=+[{]};:<>/?\\|" for char in password):
            messages.append("1 special char")

        # Update feedback label
        if messages:
            self.feedback_label.config(
                text="Missing: " + ", ".join(messages),
                fg="red"
            )
        else:
            self.feedback_label.config(
                text="Strong password ✅",
                fg="green"
            )


    # -------------------------------
    # Lock the PDF file
    # -------------------------------
    def lock_pdf(self):
        # Check if file is selected
        if not self.file_path:
            messagebox.showerror("Error", "Please select a PDF file first.")
            return

        # Check if already locked
        if self.is_locked:
            messagebox.showerror("Error", "This PDF is already locked.")
            return

        # Get password
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Error", "Please enter a password.")
            return

        # Check password strength
        if self.feedback_label.cget("fg") == "red":
            messagebox.showerror(
                "Error",
                "Password is too weak. Please fix issues shown."
            )
            return

        # Confirm password match
        confirm_password = self.confirm_entry.get()
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        # Ask user where to save locked PDF
        save_path = filedialog.asksaveasfilename(
            title="Save Locked PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=f"locked_{os.path.basename(self.file_path)}"
        )

        if not save_path:
            messagebox.showwarning("Cancelled", "Save operation cancelled.")
            return

        try:
            # Open original PDF
            pdf = pikepdf.open(self.file_path)

            # Save with encryption
            pdf.save(
                save_path,
                encryption=pikepdf.Encryption(
                    owner=password,
                    user=password,
                    R=6
                )
            )

            messagebox.showinfo(
                "Success",
                f"PDF locked successfully:\n{save_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to lock PDF:\n{str(e)}"
            )


# -------------------------------
# Main function
# -------------------------------
def main():
    root = tk.Tk()
    app = PDFLockerApp(root)
    root.mainloop()


# Run the application
if __name__ == "__main__":
    main()
