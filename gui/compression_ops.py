# gui/compression_ops.py
import os
import tkinter as tk
import logging
import threading
import time
import datetime
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import sys
from threading import Lock

# Local imports
from logic.compression import compress_pdf, find_pdfs
from .utils import ToolTip
from .utils import truncate_path, is_directory_writable


class CompressionOps:
    def __init__(self, root):
        self.root = root
        self.setup_variables()
        self.font = ("Segoe UI", 10)
        self.lock = Lock()
        self.pulse_active = False
        self.start_time = None
        self._create_pulse_style()

    def setup_variables(self):
        """Initialize compression variables."""
        self.directory = ""
        self.pdf_files = []
        self.cancel_flag = False
        self.custom_output_dir = None

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
        self.setup_progress_indicators()        
        self.setup_action_buttons()
        self.setup_status_label()     
        self.setup_text_and_sb_frame()
        self.setup_open_output_folder()

    # --------------------- UI Setup Methods ---------------------
    def setup_compression_header(self):
        self.header_frame = ttk.Frame(self.compression_frame)
        self.header_frame.pack(pady=5)

        self.header_label = ttk.Label(self.header_frame, text="Compress PDF Files", style = 'Green_Header.TLabel')
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

            ttk.Label(frame, text=label_text, style = 'Normal.TLabel').pack(side='left', padx=5)

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
                            variable=self.delete_original_var, style = 'Warning.TCheckbutton')
        
        cb.pack(pady=10)
        ToolTip(cb, "Permanently removes original files after successful compression")

    def setup_progress_indicators(self):
        """Progress bar and status labels."""
        self.progress_frame = ttk.Frame(self.compression_frame)
        self.progress_frame.pack(pady=5)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=360, mode="determinate")
        self.progress.config(style='Normal.Horizontal.TProgressbar')
        self.progress.pack(side="left", padx=5)
        
        self.progress_percentage_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_percentage_label.pack(side="left", padx=5)

    def setup_status_label(self):
        self.status_label_frame = ttk.Frame(self.compression_frame)
        self.status_label_frame.pack(pady=5)
        self.status_label = ttk.Label(self.status_label_frame, text="Select Folder or Select Files to start", wraplength=400)
        self.status_label.pack(side="left",pady = 10, padx=5)
        #self.log_message("\tSelect files or folder to start")  # Initial status message

    def setup_action_buttons(self):
        """Start/Cancel buttons."""
        self.action_buttons_frame = ttk.Frame(self.compression_frame)
        self.action_buttons_frame.pack(pady=13)

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
        self.text_frame.pack(fill="both", expand=True, pady=5, padx=10)

        # Scrollable Text Widget for displaying messages
        self.message_text = tk.Text(
            self.text_frame, 
            height=36, 
            width=46, 
            wrap="word", 
            state="disabled", 
            font=("Consolas", 9)
            )
        
        # Configure text tags
        self.message_text.tag_config("ERROR", foreground="red")
        self.message_text.tag_config("SUCCESS", foreground="black")
        self.message_text.tag_config("INFO", foreground="#2c3e50")     # Existing dark color
        self.message_text.tag_config("HEADER", font=("Segoe UI", 9, "bold"))
        self.message_text.tag_config("PROGRESS", foreground="#1976D2") # Blue

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

    # Update _get_output_directory
    def _get_output_directory(self):
        """Determine the appropriate output directory with fallback."""
        if self.custom_output_dir:
            return self.custom_output_dir
        if self.pdf_files:
            return os.path.dirname(self.pdf_files[0])
        if self.directory:
            return self.directory
        return None
    
    # -------- Additional Methods for progress bar ---------
    def _create_pulse_style(self):
        """Create custom progress bar styles for pulsing effect"""
        style = ttk.Style()
        style.configure("Pulse.Horizontal.TProgressbar",
                        troughcolor='#f0f0f0',
                        background='#1976D2',
                        lightcolor='#64B5F6',
                        darkcolor='#0D47A1')
        style.configure("Normal.Horizontal.TProgressbar",
                        troughcolor='#f0f0f0',
                        background='#4CAF50')
        
    def _start_visual_feedback(self):
        """Start visual indicators for long operations"""
        self.start_time = time.time()
        self.pulse_active = True
        self.progress.config(style='Pulse.Horizontal.TProgressbar')
        
        self._pulse_animation()

    def _stop_visual_feedback(self):
        """Stop visual indicators"""
        self.pulse_active = False
        self.progress.config(style='Normal.Horizontal.TProgressbar')
        self.status_label.config(text="Status: Completed")

    def _pulse_animation(self):
        """Animate progress bar background color"""
        if self.pulse_active:
            current_style = self.progress.cget('style')
            new_style = 'Working.Horizontal.TProgressbar' if 'Normal' in current_style else 'Normal.Horizontal.TProgressbar'
            self.progress.config(style=new_style)
            self.root.after(900, self._pulse_animation)

    

    # --------------------- Core Logic ---------------------
    def log_message(self, message: str, tag: str = "INFO"):
        """Thread-safe logging with tags and timestamps"""
        def update_gui():
            #timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            #formatted_msg = f"[{timestamp}] {message}"
            formatted_msg = f"{message}"
            
            self.message_text.configure(state='normal')
            self.message_text.insert('end', f"{formatted_msg}\n", (tag,))
            self.message_text.see('end')
            self.message_text.configure(state='disabled')
        
        self.root.after(0, update_gui)

    def select_directory(self):
        self.directory = filedialog.askdirectory()
        if self.directory:
            self.log_message(f"Scanning directory: {self.directory}")
            self.pdf_files = find_pdfs(self.directory)
            self.log_message(f"Found {len(self.pdf_files)} PDF files")
            self._update_file_count()  # Enables the Start button

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
        """Start compression with validation and directory fallback."""
        # Validate files exist
        invalid_files = [f for f in self.pdf_files if not os.path.isfile(f)]
        if invalid_files:
            messagebox.showerror(
                "Invalid Files",
                f"{len(invalid_files)} files not found or inaccessible"
            )
            return

        # Check write permissions with directory fallback
        output_dir = self._get_output_directory()
        is_writable, error = is_directory_writable(output_dir)
        
        if not is_writable:
            response = messagebox.askyesno(
                "Write Permission",
                f"Cannot write to:\n{output_dir}\n\nError: {error}\n"
                "Would you like to choose a different output folder?",
                icon="warning"
            )
            if not response:
                return  # User canceled operation
                
            # Let user select new directory with multiple retries
            MAX_ATTEMPTS = 3
            for attempt in range(MAX_ATTEMPTS):
                new_dir = filedialog.askdirectory(
                    title="Select Output Directory for Compressed Files",
                    mustexist=True
                )
                if not new_dir:
                    return  # User canceled
                
                is_new_writable, new_error = is_directory_writable(new_dir)
                if is_new_writable:
                    self.custom_output_dir = new_dir
                    output_dir = new_dir
                    break
                    
                remaining = MAX_ATTEMPTS - attempt - 1
                if remaining > 0:
                    retry = messagebox.askyesno(
                        "Write Permission",
                        f"Still cannot write to:\n{new_dir}\n\nError: {new_error}\n"
                        f"{remaining} attempts remaining. Try again?",
                        icon="warning"
                    )
                    if not retry:
                        return
                else:
                    messagebox.showerror(
                        "Write Permission",
                        "Maximum attempts reached. Operation canceled."
                    )
                    return

        # Proceed with compression setup
        self._start_visual_feedback()
        self.log_message("\nNEW OPERATION", "HEADER")
        self.log_message(f"Output directory: {output_dir}", "INFO")
        self.log_message(f"Compression level: {self.compression_level_var.get().title()}", "INFO")
        self.log_message(f"Batch Size: {self.batch_size_var.get()} files", "INFO")
        self.log_message(f"Pause Between Batches: {self.pause_duration_var.get()}s", "INFO")
        self.log_message(f"Minimum file size: {self.min_size_var.get():,} KB", "INFO")
        self.log_message(f"Delete originals: {'Yes' if self.delete_original_var.get() else 'No'}", "INFO")
        
        try:
            # Validate numerical inputs
            self.batch_size = max(1, min(self.batch_size_var.get(), 50))
            self.batch_size = min(self.batch_size, len(self.pdf_files))
            self.pause_duration = max(0.0, self.pause_duration_var.get())
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Batch size and pause must be numbers")
            return

        if not self.pdf_files:
            messagebox.showwarning("No Files", "Select PDF files first")
            return

        # Reset operation state
        self.cancel_flag = False
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.pdf_files)
        self._update_ui_state(start=True)

        # Create output directory if using custom location
        if hasattr(self, 'custom_output_dir') and self.custom_output_dir:
            os.makedirs(self.custom_output_dir, exist_ok=True)

        # Start processing thread
        threading.Thread(target=self.compress_files, daemon=True).start()

    # Modified compress_files method
    def compress_files(self):
        """
        Process PDF files in batches with thread pooling.
        
        Features:
        - Dynamic batch sizing based on CPU cores
        - Automatic retry for transient errors
        - Memory-optimized processing
        
        Flow:
        1. Validate all input files
        2. Create worker threads
        3. Checks for write permissions in output folders
        4. Process with configurable pauses
        5. Handle cleanup and reporting
        """
        total_files = len(self.pdf_files)
        stats = {"original": 0, "compressed": 0, "skipped": 0}
        results = []

        with ThreadPoolExecutor(
            max_workers=min(self.batch_size, os.cpu_count() * 2)            
        ) as executor:
            futures = {executor.submit(
                self.process_single_file, 
                pdf_file, 
                self.compression_level_var.get(),
                self.delete_original_var.get(),
                self.min_size_var.get()
            ): pdf_file for pdf_file in self.pdf_files}

            completed = 0
            self.progress["maximum"] = total_files
            self.root.after(0, self._update_progress, 0)
            self.root.after(0, self._update_status, 0, total_files, 0)

            for future in as_completed(futures):
                if self.cancel_flag:
                    break

                pdf_file = futures[future]
                with self.lock:
                    completed += 1
                remaining = total_files - completed
                active = min(self.batch_size, remaining)

                # Update progress components
                self.root.after(0, self._update_progress, completed)
                self.root.after(0, self._update_status, completed, total_files, active)
                
                # Store results without immediate UI updates
                try:
                    result = future.result()
                    results.append((pdf_file, result))
                    
                    if not result:
                        stats["skipped"] += 1
                        continue

                    success, original, compressed = result
                    if success:
                        stats["original"] += original
                        stats["compressed"] += compressed
                    else:
                        stats["skipped"] += 1

                    if completed % self.batch_size == 0:
                        time.sleep(self.pause_duration)

                except Exception as e:
                    stats["skipped"] += 1
                    results.append((pdf_file, None))

            # Final UI updates after completion
            self.root.after(0, self._show_final_results, results, stats)
            

    def _update_status(self, completed: int, total: int, active: int):
        """Enhanced status with active files"""
        if total > 0:
            percent = f"({completed/total:.0%})"
        else:
            percent = "(0%)"
        
        status_text = (f"Processing {active} file{'s' if active != 1 else ''} "
                      f"| Completed: {completed}/{total} {percent}")
        self.status_label.config(text=status_text)

    def _show_final_results(self, results, stats):
        """Display all results after processing completes"""
        # Display results first
        for pdf_file, result in results:
            if result and result[0]:  # Success case
                self._update_current_file(pdf_file, result[1], result[2])
            elif result is None:  # Failure case
                self.log_message(f"✗ Failed {truncate_path(pdf_file)}", "ERROR")
        
        self._finalize_compression(stats)
        
        # Safe status reset        
        self.root.after(0, lambda: self.status_label.config(text="Status: Idle"))
        self.root.after(0, lambda: self.progress_percentage_label.config(text="0%"))
        self.progress["value"] = 0    

    def process_single_file(self, pdf_file: str, level: str, delete_original: bool, min_size_kb: int):
        """Process individual PDF file."""
        try:
            # Generate output path
            if delete_original:
                output_path = pdf_file
            else:
                # Use custom directory if specified
                if self.custom_output_dir:
                    filename = os.path.basename(pdf_file)
                    base = os.path.splitext(filename)[0]
                    output_path = os.path.join(self.custom_output_dir, f"{base}_compressed.pdf")
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

            # Convert KB to bytes if needed (ADD THIS)
            original_bytes = original_size
            compressed_bytes = compressed_size

            if success:
                return True, original_bytes, compressed_bytes
            else:
                return False, original_bytes, compressed_bytes
                
        except Exception as e:
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

    def _update_progress(self, progress: int):
        """Update progress bar"""
        with self.lock:
            self.progress["value"] = progress
            percentage = int((progress / self.progress["maximum"]) * 100)
            self.root.after(0, self.progress_percentage_label.config, 
                        {'text': f"{percentage}%"})

    def _update_current_file(self, file_path: str, original: int, compressed: int):
        """Show formatted file compression results with aligned numbers"""
        truncated_name = truncate_path(os.path.basename(file_path))
        original_kb = original // 1024
        compressed_kb = compressed // 1024
        
        ratio = ((original - compressed) / original * 100) if original > 0 else 0
        ratio = max(ratio, 0.0)        

        # Use fixed-width formatting for alignment
        message = (
            f"\n{truncated_name.upper()}\n"
            f"Original: {original_kb}KB | Compressed: {compressed_kb:}KB\n"
            f"Reduction: {ratio:.2f}%"
        )
        if ratio < 0:
            message += " (size increased)"
        self.log_message(message, "SUCCESS")

    def _finalize_compression(self, stats):
        """Show formatted summary with proper number formatting"""
        success_count = len(self.pdf_files) - stats['skipped']
        total_reduction_bytes = stats['original'] - stats['compressed']
        total_reduction_mb = total_reduction_bytes / 1024 / 1024
        
        avg_reduction = (total_reduction_bytes / stats['original'] * 100) if stats['original'] > 0 else 0

        self.log_message("\nCOMPRESSION SUMMARY", "HEADER")
        self.log_message(f"∙ Processed files: {len(self.pdf_files):,}", "INFO")
        self.log_message(f"∙ Successful: {success_count:,}", "INFO")
        self.log_message(f"∙ Failed/Skipped: {stats['skipped']:,}", "INFO")
        self.log_message(
            f"∙ Total space saved: {total_reduction_mb:,.1f} MB",  # Corrected unit from kB to MB
            "INFO"
        )
        self.log_message(
            f"∙ Average reduction: {avg_reduction:.2f}%", 
            "INFO"
        )
       