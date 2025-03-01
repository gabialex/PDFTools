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
        self.status_label = ttk.Label(self.status_label_frame, text="Status: Idle", wraplength=400)
        self.status_label.pack(side="left", padx=5)
        self.log_message("Ready to process PDF files")  # Initial status message

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
        self.message_text.tag_config("ERROR", foreground="red")
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

    # --------------------- Core Logic ---------------------
    def log_message(self, message: str, is_error: bool = False):
        """Thread-safe message logging with progress formatting"""
        def update_gui():
            self.message_text.configure(state='normal')
            
            if is_error:
                tag = "ERROR"
                prefix = "[ERROR] "
                fg_color = "red"
            else:
                tag = "PROGRESS"
                prefix = "• "
                fg_color = "#2c3e50"  # Dark blue-grey
            
            self.message_text.tag_config(tag, foreground=fg_color)
            self.message_text.insert('end', f"{prefix}{message}\n", (tag,))
            self.message_text.see('end')
            self.message_text.configure(state='disabled')
        
        self.root.after(0, update_gui)

    def select_directory(self):
        self.directory = filedialog.askdirectory()
        if self.directory:
            self.log_message(f"Scanning directory: {self.directory}")
            self.pdf_files = find_pdfs(self.directory)
            self.log_message(f"Found {len(self.pdf_files)} PDF files")

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
        self.log_message("\n=== New Compression Session ===")
        self.log_message(f"Level: {self.compression_level_var.get().upper()}")
        self.log_message(f"Min Size: {self.min_size_var.get()} KB")
        self.log_message(f"Delete Originals: {self.delete_original_var.get()}")
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
                    result = future.result()
                    if not result:  # Handle failed results
                        stats["skipped"] += 1
                        continue

                    success, original, compressed = result
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
                    logging.error(f"Future error: {e}")
                    self.root.after(0, self.log_message,
                        f"Processing failed for {pdf_file}: {e}", True)
                    stats["skipped"] += 1

        self.root.after(0, self._finalize_compression, stats)

    def process_single_file(self, pdf_file: str, level: str, delete_original: bool, min_size_kb: int):
        """Process individual PDF file."""
        try:
            # Generate output path
            if delete_original:
                output_path = pdf_file
            else:
                base = os.path.splitext(pdf_file)[0]
                output_path = f"{base}_compressed.pdf"

            # Get all 4 return values
            success, result, original_size, compressed_size = compress_pdf(
                pdf_file,
                output_path,
                level=level,
                overwrite=delete_original
            )

            if success:
                self.root.after(0, self._update_current_file, 
                            pdf_file, original_size, compressed_size)
                return True, original_size, compressed_size
            else:
                error_msg = result
                self.root.after(0, self.log_message,
                            f"Failed {pdf_file}: {error_msg}", True)
                return False, original_size, 0

        except Exception as e:
            logging.error(f"Critical error processing {pdf_file}: {e}")
            self.root.after(0, self.log_message,
                        f"CRITICAL ERROR: {pdf_file} - {str(e)}", True)
            return False, 0, 0

    def cancel_compression(self):
        """Handle compression cancellation."""
        self.cancel_flag = True
        self.status_label.config(text="Cancelling...")
        self.cancel_button.config(state=tk.DISABLED)

    # --------------------- UI Update Methods ---------------------
    def _update_ui_state(self, start: bool):
        """Toggle UI elements during compression."""
        state = tk.DISABLED if start else tk.NORMAL
        self.start_button.config(state=state)
        self.cancel_button.config(state=not state)

    def _update_progress(self, progress: int, current_file: str):
        """Update progress bar and log processing status"""
        display_name = truncate_path(os.path.basename(current_file))
        self.progress["value"] = progress
        percentage = int((progress / len(self.pdf_files)) * 100)
        
        # Update progress percentage
        self.progress_percentage_label.config(text=f"{percentage}%")
        
        # Log to text area instead of label
        self.log_message(f"Processing: {display_name}")

    def _update_current_file(self, file_path: str, original: int, compressed: int):
        """Show detailed file compression results in text area"""
        ratio = ((original - compressed) / original) * 100 if original > 0 else 0
        ratio = max(ratio, 0.0)
        
        message = (
            f"Completed: {truncate_path(os.path.basename(file_path))}\n"
            f"Reduction: {ratio:.1f}% ({original//1024}KB → {compressed//1024}KB)\n"
            f"{'-' * 40}"
        )
        
        self.log_message(message)

    def _finalize_compression(self, stats):
        summary = (
            f"\n=== Summary ===\n"
            f"Processed: {len(self.pdf_files)} files\n"
            f"Success: {len(self.pdf_files) - stats['skipped']}\n"
            f"Failed/Skipped: {stats['skipped']}\n"
            f"Total Reduction: {(stats['original'] - stats['compressed'])/1024/1024:.1f}MB"
        )
        self.log_message(summary)