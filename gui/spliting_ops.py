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

    def setup_variables(self):
        """Initialize merging variables."""
        self.split_files = []
        self.output_folder = ""
        self.split_file_path = None    

    # --------------------- UI Spliting Components Setup Methods ---------------------
    def setup_splitting_ui(self, parent):
        """Set up UI components for splitting."""
        self.spliting_frame = ttk.Frame(parent)
        self.spliting_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI components setup for spliting in order
        self.setup_header()
        self.setup_file_selection()
        self.setup_compression_options()
        self.setup_output_folder()
        self.setup_start_split()
        self.setup_status_lbl()        

    def setup_header(self):
        """Main header for spliting section."""
        self.split_label = ttk.Label(self.spliting_frame, text="Split PDF File", style="Blue.TLabel")
        self.split_label.pack(pady=3)

    def setup_file_selection(self):
        # File selection button for splitting
        self.select_split_file_button = ttk.Button(
            self.spliting_frame,
            text="Select PDF to Split",
            command=self.select_split_file
        )
        self.select_split_file_button.pack(pady=5)
        ToolTip(self.select_split_file_button, "Select a PDF file to split.")

        # Selected files counter
        self.split_status_label_selected = ttk.Label(
            self.spliting_frame,
            text="No files selected yet",
            font=self.font,
            wraplength=400
        )
        self.split_status_label_selected.pack(pady=10)

    def setup_compression_options(self):
        """Compression-related controls."""
        # Compression checkbox
        self.compress_before_split_var = tk.BooleanVar(value=False)
        self.compress_checkbox = ttk.Checkbutton(
            self.spliting_frame,
            text="Compress files after spliting",
            variable=self.compress_before_split_var,
            command=self.toggle_compress_options
        )
        self.compress_checkbox.pack(pady=5)
        ToolTip(self.compress_checkbox, "Compress PDFs after merging them")

    # Compression level radio buttons
        self.split_compression_level_var = tk.StringVar(value="medium")
        self.compression_frame = ttk.Frame(self.spliting_frame)
        self.compression_frame.pack(pady=5)
        
        for text, value in [("High", "high"), ("Medium", "medium"), ("Low", "low")]:
            ttk.Radiobutton(
                self.compression_frame,
                text=text,
                variable=self.split_compression_level_var,
                value=value
            ).pack(side="left", padx=5)

        # Delete originals checkbox
        self.delete_after_split_var = tk.BooleanVar(value=False)
        self.delete_checkbox = ttk.Checkbutton(
            self.spliting_frame,
            text="Delete original files after splitting",
            variable=self.delete_after_split_var
        )
        self.delete_checkbox.pack(pady=10)
        ToolTip(self.delete_checkbox, "Permanently remove original files after split")

        self.toggle_compress_options()    

    def setup_output_folder(self):
        # Output folder selection
        self.select_split_output_folder_button = ttk.Button(
            self.spliting_frame,
            text="Select Output Folder for Split",
            command=self.select_split_output_folder
        )
        self.select_split_output_folder_button.pack(pady=10)
        ToolTip(self.select_split_output_folder_button, "Choose where to save split PDFs")

    def setup_start_split(self):
        # Action button to start splitting
        self.start_split_button = ttk.Button(
            self.spliting_frame,
            text="Start Splitting",
            command=self.start_split,
            style="Red.TButton",
            state=tk.DISABLED
        )
        self.start_split_button.pack(pady=10)
        ToolTip(self.start_split_button, "Begin splitting process")

    def setup_status_lbl(self):
        # Status label
        self.split_status_label = ttk.Label(
            self.spliting_frame,
            text="Waiting to start...",
            font=self.font,
            wraplength=400
        )
        self.split_status_label.pack(pady=5)

    # --------------------- Core Functionality for Spliting ---------------------
    def toggle_compress_options(self):
        """Toggle compression level options visibility."""
        state = tk.NORMAL if self.compress_before_split_var.get() else tk.DISABLED
        for widget in self.compression_frame.winfo_children():
            widget.config(state=state)

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
        if not self.split_file or not self.split_output_folder:
            messagebox.showwarning("Missing Input", "Select a file and output folder before splitting.")
            return

        # Get compression settings from UI
        compress = self.compress_before_split_var.get()
        compression_level = self.split_compression_level_var.get()
        
        self._prepare_for_split()
        
        # Pass parameters to thread
        threading.Thread(
            target=self.split_file_thread,
            daemon=True,
            args=(compress, compression_level)  # <-- ADD THIS
        ).start()

    def split_file_thread(self, compress, compression_level):  # <-- ADD PARAMETERS
        try:
            success, summary = split_pdf(
                self.split_file,
                self.split_output_folder,
                compress=compress,  # <-- PASS TO split_pdf
                compression_level=compression_level,  # <-- PASS TO split_pdf
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

    

    