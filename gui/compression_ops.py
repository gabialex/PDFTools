# gui/compression_ops.py
import os
import tkinter as tk
import logging
import threading
import time
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple
import subprocess
import sys

# Local imports
from logic.compression import compress_pdf, find_pdfs
from .utils import ToolTip
from .utils import truncate_path

class CompressionOps:
    def __init__(self, root):
        self.root = root
        self.setup_variables()
        self.font = ("Segoe UI", 10)

    def setup_variables(self):
        """Initialize compression variables."""
        self.directory = ""
        self.pdf_files = []
        self.cancel_flag = False

    def setup_compression_ui(self, parent):        
        """Set up the compression UI components."""
        self.compression_frame = ttk.Frame(parent)
        self.compression_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI Components in order
        self.setup_compression_header()
        self.setup_compression_buttons()
        self.current_file_label()
        self.setup_compression_options()
        self.setup_batch_options()
        self.setup_delete_originals()
        self.setup_status_label()        
        self.setup_progress_indicators()        
        self.setup_action_buttons()
        self.setup_text_and_sb_frame()
        self.setup_open_output_folder()

    # --------------------- UI Setup Methods ---------------------
    def setup_compression_header(self):
        self.header_frame = ttk.Frame(self.compression_frame)
        self.header_frame.pack(pady=5)

        self.header_label = ttk.Label(self.header_frame, text="Compress PDF Files", font = ("Segoe UI", 10, "bold"), style="Green.TLabel", foreground = "green")
        self.header_label.pack(side="left", padx=5)

    def setup_compression_buttons(self):
        """Buttons for selecting directory/files."""
        self.select_buttons_frame = ttk.Frame(self.compression_frame)
        self.select_buttons_frame.pack(pady=10)

        buttons = [
            ("Select Folder", self.select_directory, "Choose a directory containing PDF files"),
            ("Select Files", self.select_files, "Choose individual PDF files")
        ]

        for text, command, tooltip in buttons:
            btn = ttk.Button(self.select_buttons_frame, text=text, command=command)
            btn.pack(side="left", padx=5)
            ToolTip(btn, tooltip, delay=500)

    def current_file_label(self):
        self.current_file_label_frame = ttk.Frame(self.compression_frame)
        self.current_file_label_frame.pack(pady=5)
        
        self.current_file_label = ttk.Label(self.current_file_label_frame, text="Current File: None", wraplength=400)
        self.current_file_label.pack(side="left", padx=5)

    def setup_compression_options(self):
        """Compression level radio buttons."""
        self.compression_options_frame = ttk.Frame(self.compression_frame)
        self.compression_options_frame.pack(pady=5)

        self.compression_level_var = tk.StringVar(value="medium")
        levels = [("High", "high"), ("Medium", "medium"), ("Low", "low")]

        ttk.Label(self.compression_frame, text="Compression Level:").pack(pady=5)        

        for text, value in levels:
            ttk.Radiobutton(self.compression_options_frame, text=text, variable=self.compression_level_var, value=value).pack(side="left", padx=5)
        ToolTip(self.compression_options_frame, "Compression intensity: High (smaller files), Low (faster)")

    def setup_batch_options(self):
        """Batch processing controls with improved validation."""
        settings = [
            ("Number of PDFs per batch:", "batch_size_var", 20, 1, 50, "int"),
            ("Pause between batches (sec):", "pause_duration_var", 1.0, 0.0, 10.0, "float"),
            ("Minimum file size (KB):", "min_size_var", 1024, 100, 10000, "int")
        ]

        for label_text, var_name, default, min_val, max_val, var_type in settings:
            frame = ttk.Frame(self.compression_frame)
            frame.pack(pady=3)

            ttk.Label(frame, text=label_text).pack(side='left', padx=5)

            # Variable initialization
            if var_type == "float":
                var = tk.DoubleVar(value=default)
            else:
                var = tk.IntVar(value=default)
            setattr(self, var_name, var)

            # Entry with format validation
            validate_cmd = (self.root.register(
                lambda v, t=var_type: self.validate_number_format(v, t)), '%P')
            
            entry = ttk.Entry(
                frame,
                textvariable=var,
                width=8,
                validate='key',
                validatecommand=validate_cmd
            )
            entry.pack(side='left', padx=5)
            ToolTip(entry, f"Range: {min_val}-{max_val}")

            # Add range enforcement after editing
            var.trace_add('write', 
                lambda *args, v=var, mn=min_val, mx=max_val: 
                    self.enforce_range(v, mn, mx))

    def validate_number_format(self, value, var_type):
        """Allow numeric input and empty fields during editing."""
        if value == "":
            return True  # Allow backspacing/empty field
        try:
            if var_type == "float":
                float(value)
            else:
                int(value)
            return True
        except ValueError:
            return False

    def enforce_range(self, var, min_val, max_val):
        """Ensure values stay within allowed range after editing."""
        try:
            current = var.get()
            if current < min_val:
                var.set(min_val)
            elif current > max_val:
                var.set(max_val)
        except tk.TclError:
            pass  # Ignore invalid intermediate states

    def setup_delete_originals(self):
        """Checkbox for deleting original files."""
        self.delete_originals_frame = ttk.Frame(self.compression_frame)
        self.delete_originals_frame .pack(pady=5)

        self.delete_original_var = tk.BooleanVar()
        cb = ttk.Checkbutton(self.delete_originals_frame, 
                            text="Delete originals after compression", 
                            variable=self.delete_original_var)
        cb.pack(pady=10)
        ToolTip(cb, "Permanently removes original files after successful compression")

    def setup_progress_indicators(self):
        """Progress bar and status labels."""
        self.progress_frame = ttk.Frame(self.compression_frame)
        self.progress_frame.pack(pady=5)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.config(style='Normal.Horizontal.TProgressbar')
        self.progress.pack(side="left", padx=5)
        
        self.progress_percentage_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_percentage_label.pack(side="left", padx=5)

    def setup_status_label(self):
        self.status_label_frame = ttk.Frame(self.compression_frame)
        self.status_label_frame.pack(pady=5)

        self.status_label = ttk.Label(self.status_label_frame, text="Waiting to start...", wraplength=400)
        self.status_label.pack(side="left", padx=5)

    def setup_action_buttons(self):
        """Start/Cancel buttons."""
        self.action_buttons_frame = ttk.Frame(self.compression_frame)
        self.action_buttons_frame.pack(pady=10)

        self.start_button = ttk.Button(
            self.action_buttons_frame,
            text="Start Compression",
            command=self.start_compression,
            state=tk.DISABLED
        )
        self.start_button.pack(side="left", padx=5)
        ToolTip(self.start_button, "Begin compression process")

        self.cancel_button = ttk.Button(
            self.action_buttons_frame,
            text="Cancel",
            command=self.cancel_compression,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side="left", padx=5)
        ToolTip(self.cancel_button, "Stop current operation")

    def setup_text_and_sb_frame(self):
        # Create a frame to hold the text widget and scrollbar
        self.text_frame = ttk.Frame(self.compression_frame)
        self.text_frame.pack(fill="both", expand=True, pady=15, padx=10)

        # Scrollable Text Widget for displaying messages
        self.message_text = tk.Text(self.text_frame, height=30, width=46, wrap="word", state="disabled")
        self.message_text.pack(side="left", fill="both", pady=1, expand=True)

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.message_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.message_text.config(yscrollcommand=scrollbar.set)

    def setup_open_output_folder(self):
        # Add Open Folder button under the text area
        self.open_output_folder_frame = ttk.Frame(self.compression_frame)
        self.open_output_folder_frame.pack(pady=5)

        self.open_folder_btn = ttk.Button(
            self.open_output_folder_frame,
            text="Open Output Folder",
            command=self.open_output_folder
        )
        self.open_folder_btn.pack(pady=5)
        ToolTip(self.open_folder_btn, "Open the output folder in file explorer")

    # --------------------- Core Logic ---------------------
    def select_directory(self):
        """Directory selection handler."""
        self.directory = filedialog.askdirectory(title="Select Directory")
        if self.directory:
            self.pdf_files = find_pdfs(self.directory)
            self._update_file_count()

    def select_files(self):
        """File selection handler."""
        files = filedialog.askopenfilenames(title="Select PDF Files", filetypes=[("PDF files", "*.pdf")])
        if files:
            self.pdf_files = list(files)
            self._update_file_count()

    def _update_file_count(self):
        """Update UI with selected file count."""
        count = len(self.pdf_files)
        if count > 0:
            self.status_label.config(text=f"Ready: {count} PDFs selected")
            self.start_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="No valid PDF files found")
            self.start_button.config(state=tk.DISABLED)

    def start_compression(self):
        """Start compression with validation."""
        try:
            # Validate numerical inputs
            self.batch_size = max(1, min(self.batch_size_var.get(), 50))
            self.pause_duration = max(0.0, self.pause_duration_var.get())
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Batch size and pause must be numbers")
            return

        if not self.pdf_files:
            messagebox.showwarning("No Files", "Select PDF files first")
            return

        # Reset UI state
        self.cancel_flag = False
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.pdf_files)
        self._update_ui_state(start=True)

        # Start thread
        threading.Thread(target=self.compress_files, daemon=True).start()

    def compress_files(self):
        """Process files in batches with threading."""
        total_files = len(self.pdf_files)
        stats = {"original": 0, "compressed": 0, "skipped": 0}

        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            futures = {executor.submit(
                self.process_single_file, 
                pdf_file, 
                self.compression_level_var.get(),
                self.delete_original_var.get(),
                self.min_size_var.get()
            ): pdf_file for pdf_file in self.pdf_files}

            for i, future in enumerate(as_completed(futures)):
                if self.cancel_flag:
                    break

                pdf_file = futures[future]
                try:
                    success, original, compressed = future.result()
                    if success:
                        stats["original"] += original
                        stats["compressed"] += compressed
                    else:
                        stats["skipped"] += 1

                    # Thread-safe UI update
                    self.root.after(0, self._update_progress, i+1, pdf_file)

                    # Batch pause
                    if (i+1) % self.batch_size == 0:
                        time.sleep(self.pause_duration)

                except Exception as e:
                    logging.error(f"Error processing {pdf_file}: {e}")
                    stats["skipped"] += 1

        self.root.after(0, self._finalize_compression, stats)

    def process_single_file(self, pdf_file: str, level: str, delete_original: bool, min_size_kb: int) -> Tuple[bool, int, int]:
        """Process individual PDF file."""
        original_size = os.path.getsize(pdf_file)
        if original_size < min_size_kb * 1024:
            logging.info(f"Skipped small file: {pdf_file}")
            return False, original_size, 0

        success, result = compress_pdf(
            pdf_file,
            pdf_file if delete_original else pdf_file.replace(".pdf", "_compressed.pdf"),
            level=level,
            overwrite=delete_original
        )

        if success:
            # Update UI with thread-safe callback
            self.root.after(0, self._update_current_file, pdf_file, original_size, result)
            return True, original_size, result
        else:
            # Show error in status
            self.root.after(0, lambda: self.status_label.config(text=f"Failed: {os.path.basename(pdf_file)} - {result}"))
            return False, original_size, 0

    def cancel_compression(self):
        """Handle compression cancellation."""
        self.cancel_flag = True
        self.status_label.config(text="Cancelling...")
        self.cancel_button.config(state=tk.DISABLED)

    def open_output_folder(self):
        """Open the output directory in system file explorer."""
        output_dir = self._get_output_directory()
        
        if not output_dir:
            messagebox.showwarning(
                "No Output Folder",
                "Please select PDF files or a directory first."
            )
            return
            
        if not os.path.isdir(output_dir):
            messagebox.showerror(
                "Invalid Directory",
                f"Directory not found:\n{output_dir}"
            )
            return

        try:
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", output_dir], check=True)
            else:
                subprocess.run(["xdg-open", output_dir], check=True)
        except Exception as e:
            messagebox.showerror(
                "Open Failed",
                f"Could not open folder:\n{str(e)}"
            )

    def _get_output_directory(self):
        """Determine the appropriate output directory."""
        if self.pdf_files:
            return os.path.dirname(self.pdf_files[0])
        if self.directory:
            return self.directory
        return None

    # --------------------- UI Update Methods ---------------------
    def _update_ui_state(self, start: bool):
        """Toggle UI elements during compression."""
        state = tk.DISABLED if start else tk.NORMAL
        self.start_button.config(state=state)
        self.cancel_button.config(state=not state)

    def _update_progress(self, progress: int, current_file: str):
        """Update progress bar and percentage."""
        filename = os.path.basename(current_file)
        #print(filename)
        #display_name = filename if len(filename) <= 30 else f"{filename[:27]}..."
        display_name = truncate_path(os.path.basename(current_file))
        #print(display_name)
        self.progress["value"] = progress
        percentage = int((progress / len(self.pdf_files)) * 100)
        self.progress_percentage_label.config(text=f"{percentage}%")
        self.current_file_label.config(text=f"Processing: {display_name}")

    def _update_current_file(self, file_path: str, original: int, compressed: int):
        """Show detailed file compression results."""
        ratio = ((original - compressed) / original) * 100 if original > 0 else 0
        ratio = max(ratio, 0.0)  # Force non-negative
        self.current_file_label.config(
            text=f"Completed: {truncate_path(os.path.basename(file_path), 2, '...', 40)}\n"
                 f"Reduction: {ratio:.1f}% ({original//1024}KB → {compressed//1024}KB)")

    def _finalize_compression(self, stats: dict):
        """Show final summary."""
        summary = (
            f"Processed {len(self.pdf_files)} files\n"
            f"Success: {len(self.pdf_files) - stats['skipped']} | "
            f"Failed/Skipped: {stats['skipped']}\n"
            f"Total reduction: {(stats['original'] - stats['compressed']) / 1024 / 1024:.1f}MB"
        )
        self.status_label.config(text=summary)
        self._update_ui_state(start=False)