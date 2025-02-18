# gui/compression_ops.py
import os
import tkinter as tk
import logging
import threading
import time
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple

# Local imports
from logic.compression import compress_pdf, find_pdfs
from .utils import ToolTip

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
        self.left_frame = ttk.Frame(parent)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI Components
        self.setup_compression_header()
        self.setup_compression_buttons()
        self.setup_compression_options()
        self.setup_batch_options()
        self.setup_delete_originals()
        self.setup_progress_indicators()
        self.setup_action_buttons()

    # --------------------- UI Setup Methods ---------------------
    def setup_compression_header(self):
        self.compress_label = ttk.Label(self.left_frame, text="Compress PDF Files", style="Blue.TLabel")
        self.compress_label.pack(pady=5)

    def setup_compression_buttons(self):
        """Buttons for selecting directory/files."""
        self.select_buttons_frame = ttk.Frame(self.left_frame)
        self.select_buttons_frame.pack(pady=10)

        buttons = [
            ("Select Directory", self.select_directory, "Choose a directory containing PDF files"),
            ("Select Files", self.select_files, "Choose individual PDF files")
        ]

        for text, command, tooltip in buttons:
            btn = ttk.Button(self.select_buttons_frame, text=text, command=command)
            btn.pack(side="left", padx=5)
            ToolTip(btn, tooltip, delay=500)

    def setup_compression_options(self):
        """Compression level radio buttons."""
        self.compression_level_var = tk.StringVar(value="medium")
        levels = [("High", "high"), ("Medium", "medium"), ("Low", "low")]

        ttk.Label(self.left_frame, text="Compression Level:").pack(pady=5)
        frame = ttk.Frame(self.left_frame)
        frame.pack(pady=5)

        for text, value in levels:
            ttk.Radiobutton(frame, text=text, variable=self.compression_level_var, value=value).pack(side="left", padx=5)
        ToolTip(frame, "Compression intensity: High (smaller files), Low (faster)")

    def setup_batch_options(self):
        """Batch processing controls."""
        settings = [
            ("Number of PDFs per batch:", "batch_size_var", 20, 1, 50),
            ("Pause between batches (sec):", "pause_duration_var", 1.0, 0.0, 10.0),
            ("Minimum file size (KB):", "min_size_var", 1024, 100, 10000)
        ]

        for label_text, var_name, default, min_val, max_val in settings:
            self.batch_frame = ttk.Frame(self.left_frame)
            self.batch_frame.pack(pady=3)
            # Create a frame for batch elements
            ttk.Label(self.batch_frame, text=label_text).pack(side='left', pady=5)
            
            var = tk.DoubleVar(value=default) if "pause" in var_name else tk.IntVar(value=default)
            setattr(self, var_name, var)
            
            entry = ttk.Entry(self.batch_frame, textvariable=var, width=5)
            entry.pack(side='left', padx=5, pady=5)
            ToolTip(entry, f"Value between {min_val}-{max_val}")

    def setup_delete_originals(self):
        """Checkbox for deleting original files."""
        self.delete_original_var = tk.BooleanVar()
        cb = ttk.Checkbutton(self.left_frame, 
                            text="Delete originals after compression", 
                            variable=self.delete_original_var)
        cb.pack(pady=10)
        ToolTip(cb, "Permanently removes original files after successful compression")

    def setup_progress_indicators(self):
        """Progress bar and status labels."""
        self.progress_frame = ttk.Frame(self.left_frame)
        self.progress_frame.pack(pady=20)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(side="left", padx=5)
        
        self.progress_percentage_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_percentage_label.pack(side="left", padx=5)
        
        self.current_file_label = ttk.Label(self.left_frame, text="Current File: None", wraplength=400)
        self.current_file_label.pack(pady=10)
        
        self.status_label = ttk.Label(self.left_frame, text="Waiting to start...", wraplength=400)
        self.status_label.pack(pady=10)

    def setup_action_buttons(self):
        """Start/Cancel buttons."""
        self.action_buttons_frame = ttk.Frame(self.left_frame)
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

    # --------------------- UI Update Methods ---------------------
    def _update_ui_state(self, start: bool):
        """Toggle UI elements during compression."""
        state = tk.DISABLED if start else tk.NORMAL
        self.start_button.config(state=state)
        self.cancel_button.config(state=not state)

    def _update_progress(self, progress: int, current_file: str):
        """Update progress bar and percentage."""
        self.progress["value"] = progress
        percentage = int((progress / len(self.pdf_files)) * 100)
        self.progress_percentage_label.config(text=f"{percentage}%")
        self.current_file_label.config(text=f"Processing: {os.path.basename(current_file)}")

    def _update_current_file(self, file_path: str, original: int, compressed: int):
        """Show detailed file compression results."""
        ratio = ((original - compressed) / original) * 100 if original > 0 else 0
        ratio = max(ratio, 0.0)  # Force non-negative
        self.current_file_label.config(
            text=f"Completed: {os.path.basename(file_path)}\n"
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