# gui/spliting_ops.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from logic.split import split_pdf  # Import the split logic
from .utils import ToolTip

class SplitingOps:
    def __init__(self, root):
        self.root = root        
        self.font = ("Segoe UI", 10)
        self.split_file = None
        self.split_output_folder = ""

    # --------------------- UI Spliting Components Setup Methods ---------------------
    def setup_splitting_ui(self, parent):
        """Set up UI components for splitting."""
        self.splitting_frame = ttk.Frame(parent)
        self.splitting_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.split_label = ttk.Label(self.splitting_frame, text="Split PDF File", style="Blue.TLabel")
        self.split_label.pack(pady=3)

        # File selection button for splitting
        self.select_split_file_button = ttk.Button(
            self.splitting_frame,
            text="Select PDF to Split",
            command=self.select_split_file
        )
        self.select_split_file_button.pack(pady=5)
        ToolTip(self.select_split_file_button, "Select a PDF file to split.")

        # Output folder selection
        self.select_split_output_folder_button = ttk.Button(
            self.splitting_frame,
            text="Select Output Folder for Split",
            command=self.select_split_output_folder
        )
        self.select_split_output_folder_button.pack(pady=10)
        ToolTip(self.select_split_output_folder_button, "Choose where to save split PDFs")

        # Action button to start splitting
        self.start_split_button = ttk.Button(
            self.splitting_frame,
            text="Start Splitting",
            command=self.start_split,
            style="Red.TButton",
            state=tk.DISABLED
        )
        self.start_split_button.pack(pady=10)
        ToolTip(self.start_split_button, "Begin splitting process")

        # Status label
        self.split_status_label = ttk.Label(
            self.splitting_frame,
            text="Waiting to start...",
            font=self.font,
            wraplength=400
        )
        self.split_status_label.pack(pady=5)

    # --------------------- Core Functionality for Spliting ---------------------
    def select_split_file(self):
        """Handle PDF file selection for splitting."""
        file = filedialog.askopenfilename(
            title="Select PDF File to Split",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file:
            self.split_file = file
            self.split_status_label.config(text=f"Selected file: {os.path.basename(file)}")
            self.start_split_button.config(state=tk.NORMAL)

    def select_split_output_folder(self):
        """Handle output folder selection for split files."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.split_output_folder = folder
            self.split_status_label.config(text=f"Output folder: {folder}")

    def start_split(self):
        """Initiate splitting process."""
        if not self.split_file or not self.split_output_folder:
            messagebox.showwarning("Missing Input", "Select a file and output folder before splitting.")
            return

        # Proceed with splitting
        self._prepare_for_split()
        threading.Thread(target=self.split_file_thread, daemon=True).start()

    def split_file_thread(self):
        """Background thread for splitting process."""        
        try:
            success, summary = split_pdf(
                self.split_file,
                self.split_output_folder,
                update_callback=lambda f, p: self.root.after(0, self._update_split_progress, f, p)
            )
            if success:
                self._handle_split_success(summary)
            else:
                self._handle_split_error(summary)
        except Exception as e:
            self._handle_critical_error(e)
        finally:
            self._reset_ui_state()

    def _prepare_for_split(self):
        """Prepare UI for splitting process."""
        self.split_status_label.config(text="Starting splitting process...")

    def _update_split_progress(self, current_page, total_pages):
        """Update progress indicators."""
        self.split_status_label.config(text=f"Splitting page {current_page} of {total_pages}")

    def _handle_split_success(self, summary):
        """Handle successful split."""
        messagebox.showinfo("Split Successful", summary)
        self.split_status_label.config(text="Split complete")

    def _handle_split_error(self, error):
        """Handle split errors."""
        messagebox.showerror("Split Failed", f"Error: {error}")

    def _reset_ui_state(self):
        """Reset UI to initial state after splitting."""
        self.start_split_button.config(state=tk.NORMAL)

    