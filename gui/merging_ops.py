# gui/merging_ops.py
import os
import logging
import threading
import traceback
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
#from datetime import datetime
from threading import Lock
import sys

from logic.merging import merge_pdfs
from .utils import ToolTip, CustomText
from .utils import truncate_path, is_directory_writable


class MergingOps:
    def __init__(self, root):
        self.root = root
        self.setup_variables()
        self.font = ("Segoe UI", 10)
        self.log_lock = Lock()        

    def setup_variables(self):
        """Initialize merging variables."""
        self.merge_files = []
        self.output_folder = ""
        self.merged_file_path = None        

    def setup_merging_ui(self, parent):
        """Set up merging UI components."""
        self.merging_frame = ttk.Frame(parent)
        self.merging_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # ---------------- UI Components in Order ---------------
        self.setup_header()
        self.setup_file_selection()        
        self.setup_compression_options()
        self.setup_delete_originals_lbl()
        self.setup_output_controls()
        self.setup_progress_indicators()
        self.setup_merge_status_label()        
        self.setup_log_area()    
        self.setup_post_merge_controls()

    # --------------------- UI Setup Methods ---------------------
    def setup_header(self):
        """Main header for merging section."""
        self.merge_label = ttk.Label(self.merging_frame, text="Merge PDF Files", style="Blue_Header.TLabel")
        self.merge_label.pack(pady=5)

    def setup_file_selection(self):
        """File selection controls."""
        # File selection button
        self.select_merge_files_button = ttk.Button(
            self.merging_frame,
            text="Select PDFs to Merge",
            command=self.select_merge_files
        )
        self.select_merge_files_button.pack(pady=20)
        ToolTip(self.select_merge_files_button, "Select multiple PDF files to merge.")

    def setup_merge_status_label(self):
        # Selected files counter
        self.merge_status_label = ttk.Label(
            self.merging_frame,
            text="Select at least 2 PDFs to merge",            
            wraplength=400
        )
        self.merge_status_label.pack(pady=10)

    def setup_compression_options(self):
        """Compression-related controls."""
        # Compression checkbox
        self.compress_before_merge_var = tk.BooleanVar(value=False)
        self.compress_checkbox = ttk.Checkbutton(
            self.merging_frame,
            text="Try to compress files before merging",
            variable=self.compress_before_merge_var,
            command=self.toggle_compress_options
        )
        self.compress_checkbox.pack(pady=5)
        ToolTip(self.compress_checkbox, "Compress PDFs before merging them")

        # Compression level radio buttons
        self.merge_compression_level_var = tk.StringVar(value="medium")
        self.compression_frame = ttk.Frame(self.merging_frame)
        self.compression_frame.pack(pady=5)
        
        for text, value in [("High", "high"), ("Medium", "medium"), ("Low", "low")]:
            rb = ttk.Radiobutton(
                self.compression_frame,
                text=text,
                variable=self.merge_compression_level_var,
                value=value
            )
            rb.pack(side="left", padx=5)
            ToolTip(rb, "If the PDF has been previously compressed, further compression will yield minimal or no improvements.")

    def setup_delete_originals_lbl(self):        
        # Delete originals checkbox
        self.delete_after_merge_var = tk.BooleanVar(value=False)
        self.delete_checkbox = ttk.Checkbutton(
            self.merging_frame,
            text="Delete original files after merging", 
            variable=self.delete_after_merge_var, style = 'Warning.TCheckbutton'
        )
        self.delete_checkbox.pack(pady=10)
        ToolTip(self.delete_checkbox, "Permanently remove original files after merge")
        self.toggle_compress_options()

    def setup_output_controls(self):
        """Output destination controls."""
        # Output folder selection
        self.select_output_folder_button = ttk.Button(
            self.merging_frame,
            text="Select Output Folder",
            command=self.select_output_folder
        )
        self.select_output_folder_button.pack(pady=10)
        ToolTip(self.select_output_folder_button, "Choose where to save merged PDF")

        # Output filename entry in frame
        self.output_filename_frame = ttk.Frame(self.merging_frame)
        self.output_filename_frame.pack(pady=3)

        #Label
        ttk.Label(self.output_filename_frame, text = "Name your filename ").pack(side='left', pady=5)

        #Entry
        self.output_name_var = tk.StringVar(value="merged_file.pdf")
        self.output_entry = ttk.Entry(
            self.output_filename_frame,
            textvariable=self.output_name_var,
            width=15,            
            font=self.font
        )
        self.output_entry.pack(side='left', pady=5)
        ToolTip(self.output_entry, "Name for merged PDF file")

    def setup_progress_indicators(self):
        """Progress bar and status labels."""
        self.merge_progress_frame = ttk.Frame(self.merging_frame)
        self.merge_progress_frame.pack(pady=20)

        self.merge_progress = ttk.Progressbar(self.merge_progress_frame,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        self.merge_progress.config(style='Normal.Horizontal.TProgressbar')
        self.merge_progress.pack(side="left", padx=5)

        self.progress_percentage_label = ttk.Label(self.merge_progress_frame, text="0%")
        self.progress_percentage_label.pack(side="left", padx=5)

        # Action button
        self.start_merge_button = ttk.Button(
            self.merging_frame,
            text="Start Merging",
            command=self.start_merge,
            style="Red.TButton",
            state=tk.DISABLED
        )
        self.start_merge_button.pack(pady=10)
        ToolTip(self.start_merge_button, "Begin merging process")

    def setup_log_area(self):
        """Unified logging area for merge operations."""
        log_frame = ttk.Frame(self.merging_frame)
        log_frame.pack(fill="both", expand=True, pady=5, padx=10)

        self.log_area = CustomText(
            log_frame, 
            height=36,
            width=46,
            wrap="word",
            state="disabled",
            font=("Consolas", 9)
        )
        self.log_area.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_area.configure(yscrollcommand=scrollbar.set)

    def append_log(self, message, tag=None):
        """Thread-safe log appending with styling support."""
        #timestamp = datetime.now().strftime("%H:%M:%S")        
        with self.log_lock:
            formatted_message = f"{message}"            
            self.log_area.configure(state="normal")
            self.log_area.insert(tk.END, formatted_message + "\n", tag)
            self.log_area.configure(state="disabled")
            self.log_area.see(tk.END)
            
            # Auto-scroll if not paused
            self.log_area.see(tk.END)

    def setup_post_merge_controls(self):
        """Post-merge action controls."""
        post_merge_frame = ttk.Frame(self.merging_frame)
        post_merge_frame.pack(pady=10)

        # Open Output Folder btn
        self.open_output_folder_button= ttk.Button(
            post_merge_frame,
            text="Open Output Folder",
            command=self.open_output_folder,
            state=tk.DISABLED
        )
        self.open_output_folder_button.pack(side="left", padx=5)
        ToolTip(self.open_output_folder_button, "Open the output folder in file explorer")

        # Open merged file btn
        self.open_merged_file_button = ttk.Button(
            post_merge_frame ,
            text="Open Merged File",
            command=self.open_merged_file,
            state=tk.DISABLED
        )
        self.open_merged_file_button.pack(side="left", padx=5)
        ToolTip(self.open_merged_file_button, "Open merged PDF in default viewer")

        # Print merged file btn
        self.print_merged_file_button = ttk.Button(
            post_merge_frame,
            text="Print Merged File",
            command=self.print_merged_file,
            state=tk.DISABLED
        )
        self.print_merged_file_button.pack(side="left", padx=5)
        ToolTip(self.print_merged_file_button, "Print merged PDF using default printer")         


    # --------------------- Core Functionality for Merging---------------------
    def toggle_compress_options(self):
        """Toggle compression level options visibility."""
        state = tk.NORMAL if self.compress_before_merge_var.get() else tk.DISABLED
        for widget in self.compression_frame.winfo_children():
            widget.config(state=state)

    def select_merge_files(self):
        """Handle PDF file selection."""
        files = filedialog.askopenfilenames(
            title="Select PDF Files to Merge",
            filetypes=[("PDF files", "*.pdf")]
        )
        if files:
            self.merge_files = list(files)
            self._update_selected_count(len(files))
            self.start_merge_button.config(state=tk.NORMAL, style = 'Ready.TButton')

    def select_output_folder(self):
        """Handle output folder selection."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.merge_status_label.config(text=f"Output folder: {folder}")

    def start_merge(self):
        """Initiate merging process."""
        # Validate basic inputs first (files selected and PDF extension)
        if not self._validate_inputs():
            return

        # Get output path - returns None if user cancels folder selection
        output_file = self._get_output_path()
        
        # Check if user canceled output path selection
        if not output_file:
            return  # Exit silently without error
        
        # Check file overwrite if path exists
        if not self._confirm_overwrite(output_file):
            return

        # Proceed with merging
        self._prepare_for_merge(output_file)
        threading.Thread(
            target=self.merge_files_thread,
            args=(output_file,),
            daemon=True).start()

    def merge_files_thread(self, output_file):
        """Background thread for merging process."""
        try:
            success, summary, error = merge_pdfs(
                self.merge_files,
                output_file,
                compress_before_merge=self.compress_before_merge_var.get(),
                compression_level=self.merge_compression_level_var.get(),
                update_callback=lambda f, p: self.root.after(0, self._update_progress, f, p),
                log_callback=lambda msg: self.root.after(0, self.append_log, msg)
            )

            if success:
                self._handle_merge_success(output_file, summary)
                if self.delete_after_merge_var.get():
                    self._handle_file_deletion()
            else:
                self._handle_merge_error(error)
                
        except Exception as e:
            self._handle_critical_error(e)
        finally:
            self._reset_ui_state()

    # --------------------- Helper Methods for Merging---------------------
    def _update_selected_count(self, count):
        """Update selected files counter."""
        self.merge_status_label.config(text=f"{count} PDF files selected")
        self.merge_progress.config(maximum=count)

    def _validate_inputs(self):
        """Validate user inputs before merging."""
        if not self.merge_files:
            messagebox.showwarning("No Files", "Select PDF files to merge first")
            return False 
        
        if len(self.merge_files) < 2:
            messagebox.showwarning("Insufficient Files", "Select at least two PDF files to merge.")
            return False
        
        self.output_name = self.output_name_var.get()
        if not self.output_name_var.get().endswith(".pdf"):
            messagebox.showerror("Invalid Name", "Output file must end with .pdf")
            return False
        
        # Check for invalid characters in output filename
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.output_name for char in invalid_chars):
            messagebox.showerror("Invalid Name", f"Output filename contains invalid characters: {invalid_chars}")
            return False

        return True

    def _get_output_path(self):
        """Determine output file path. Returns None if user cancels."""
        if not self.output_folder:
            # Get directory of first file if no output folder selected
            first_file = self.merge_files[0]
            default_output_folder = os.path.dirname(first_file)
                        
            # === 1. ACTUAL WRITE TEST (not os.access) ===
            is_writable, error = is_directory_writable(default_output_folder)
            if not is_writable:
                # Show error with truncated path
                truncated_path = truncate_path(default_output_folder, max_folders=1,ellipsis='-->')
                #print(truncated_path)
                messagebox.showerror(
                    "Permission Denied",
                    f"Cannot write to:\n{truncated_path}\n\nError: {error}\n\nSelect ANOTHER FOLDER."
                )
                self.select_output_folder()  # Trigger folder selection
                return None          

            # === 2. Confirm Default Folder Usage ===
            confirmed = messagebox.askokcancel(
                "Confirm Output Folder",
                f"Files will be merged into:\n{truncate_path(default_output_folder, max_folders=1, ellipsis='-->')}\nProceed?"
            )
            if not confirmed:
                return None  # User canceled

            return os.path.join(default_output_folder, self.output_name_var.get())
        
        # If output folder was explicitly selected earlier
        return os.path.join(self.output_folder, self.output_name_var.get())  

    def _confirm_overwrite(self, path):
        """Handle existing file overwrite confirmation."""
        if not path:  # Add this check first
            return False
        
        if os.path.exists(path):
            return messagebox.askyesno(
                "Overwrite File",
                f"{path} already exists.\nOverwrite?"
            )
        return True

    def _prepare_for_merge(self, output_file):
        """Prepare UI for merging process."""
        self.merged_file_path = output_file
        self.start_merge_button.config(state=tk.DISABLED)
        self.merge_progress["value"] = 0        
        

    def _update_progress(self, current_file, progress):
        """Update progress indicators."""
        filename = os.path.basename(current_file)
        if len(filename) >= 30:
            filename = f"{filename[:27]}..."

        self.merge_status_label.config(text=f"Processing: {filename}")
        self.merge_progress["value"] = progress
        percentage = int((progress / len(self.merge_files)) * 100)
        self.progress_percentage_label.config(text=f"{percentage}%")
        self.merge_status_label.config(
            text=f"Merging file {progress} of {len(self.merge_files)}"
        )

    def _handle_merge_success(self, output_file, summary_data):
        """Handle successful merge with clean formatting."""        
        self.open_merged_file_button.config(state=tk.NORMAL)
        self.print_merged_file_button.config(state=tk.NORMAL)
        self.open_output_folder_button.config(state=tk.NORMAL)
        
        # Helper function for size formatting
        def format_size(bytes_size):
            return f"{bytes_size / 1024 / 1024:.2f} MB" if bytes_size > 0 else "N/A"

        # Create visual separation        
        success_banner = f"\nMerge Successful"       
        
        # Build summary content
        summary_content = [
            success_banner,
            f"📄 Merged Files: {summary_data['file_count']}",
            f"📂 Output Folder: {truncate_path(output_file, max_folders=3, ellipsis='-->')}",
            f"💾 Output File: {truncate_path(output_file)}",
            f"📦 Total Size: {format_size(summary_data['total_original'])}"
        ]

        # Add compression results if used
        if summary_data['used_compression']:
            # Calculate safe values
            original = summary_data['total_original']
            compressed = summary_data['total_compressed']
            saved = max(original - compressed, 0)  # Never show negative
            ratio = (saved / original * 100) if original > 0 else 0
            ratio_display = max(ratio, 0)  # Ensure non-negative
            
            summary_content.extend([
                f"\n🔍 Compression Results:",
                f"   Original Size: {format_size(original)}",
                f"   Compressed Size: {format_size(compressed)}",
                f"   Space Saved: {format_size(saved)} (▼{ratio_display:.1f}%)"
            ])                   

        # Add to log
        for line in summary_content:
            self.append_log(line)
        
        self.merge_status_label.config(text=f"Success! Merged {summary_data['file_count']} files")
        self.append_log("\nAll done, ready to start new merge\n") if not self.delete_after_merge_var.get() else ""

    def _handle_merge_error(self, error):
        """Handle merge errors."""
        messagebox.showerror("Merge Failed", f"Error: {error}\n\nCheck logs for details.")
        self.merge_status_label.config(text=f"Error: {error[:100]}...")

    def _handle_critical_error(self, error):
        """Handle unexpected errors."""
        logging.error(f"Critical error: {traceback.format_exc()}")
        messagebox.showerror(
            "Critical Error",
            f"Unexpected error:\n{str(error)}\nSee logs for details."
        )
        self.merge_status_label.config(text="Critical error occurred")

    def _handle_file_deletion(self):
        """Handle original file deletion with logging."""
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete {len(self.merge_files)} original files?"
        ):
            self.append_log("File deletion canceled by user")
            self.append_log("\nAll done, ready to start new merge\n")
            return

        deleted, failed = [], []
        for file in self.merge_files:
            if not os.path.exists(self.merged_file_path):
                messagebox.showerror("Error", "Merged file not found. Deletion canceled.")
                return
            try:
                os.remove(file)
                deleted.append(os.path.basename(file))                
            except Exception as e:
                failed.append(f"{os.path.basename(file)}: {str(e)}")

        # Build deletion summary directly in log
        #self.append_log("\nFile Deletion Results:")
        if deleted:
            self.append_log("\nSuccessfully deleted:")
            for f in deleted:
                self.append_log(f"  ✓ {f}")
        if failed:
            self.append_log("\nFailed deletions:")
            for f in failed:
                self.append_log(f"  ✗ {f}")
        self.append_log("\nAll done, ready to start new merge\n")        

    def _format_deletion_summary(self, deleted, failed):
        """Format deletion results for display."""
        summary = []
        if deleted:
            summary.append("Successfully deleted: - " + "\n- ".join(deleted))
        if failed:
            summary.append("\nFailed to delete: - " + "\n- ".join(failed))
        return "\n".join(summary)

    def _reset_ui_state(self):
        """Reset UI to initial state."""
        self.start_merge_button.config(state=tk.DISABLED, style = 'TButton') 
        self.merge_progress["value"] = 0
        self.progress_percentage_label.config(text="0%")
        self.merge_status_label.config(text="Ready for new merge. Select at least 2 PDFs")

    # --------------------- Post-Merge Actions ---------------------
    def open_output_folder(self):
        """Open the output folder in system file explorer."""
        if not self.merged_file_path:
            messagebox.showwarning("Error", "No output folder available")
            return

        output_dir = os.path.dirname(self.merged_file_path)
        
        if not os.path.exists(output_dir):
            messagebox.showerror(
                "Folder Not Found",
                f"The output folder no longer exists:\n{truncate_path(output_dir)}"
            )
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # macOS or Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', output_dir])
        except Exception as e:
            messagebox.showerror(
                "Open Failed",
                f"Could not open output folder:\n{str(e)}\n\nPath: {truncate_path(output_dir)}"
            )
    
    def open_merged_file(self):
        """Open merged file in default viewer."""
        if not self.merged_file_path or not os.path.exists(self.merged_file_path):
            messagebox.showwarning("Error", "Merged file not found")
            return

        try:
            if os.name == "nt":
                os.startfile(self.merged_file_path)
            else:
                subprocess.run(["xdg-open", self.merged_file_path])
        except Exception as e:
            messagebox.showerror(
                "Open Failed",
                f"Could not open file:\n{str(e)}\n\nLocation: {self.merged_file_path}"
            )

    def print_merged_file(self):
        """Print merged file using system default printer."""
        if not self.merged_file_path or not os.path.exists(self.merged_file_path):
            messagebox.showwarning("Error", "Merged file not found")
            return

        try:
            if os.name == "nt":
                os.startfile(self.merged_file_path, "print")
            else:
                subprocess.run(["lp", self.merged_file_path])
            messagebox.showinfo("Print", "File sent to default printer")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print:\n{str(e)}")    