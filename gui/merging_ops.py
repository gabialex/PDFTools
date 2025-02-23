# gui/merging_ops.py
import os
import logging
import threading
import traceback
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from logic.merging import merge_pdfs
from .utils import ToolTip
from logic.split import split_pdf  # Import the split logic

class MergingOps:
    def __init__(self, root):
        self.root = root
        self.setup_variables()
        self.font = ("Segoe UI", 10)        

    def setup_variables(self):
        """Initialize merging variables."""
        self.merge_files = []
        self.output_folder = ""
        self.merged_file_path = None

    def setup_merging_ui(self, parent):
        """Set up merging UI components."""
        self.merging_frame = ttk.Frame(parent)
        self.merging_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI components setup for merging in order
        self.setup_header()
        self.setup_file_selection()
        self.setup_compression_options()
        self.setup_output_controls()
        self.setup_progress_indicators()
        self.setup_post_merge_controls()
        
    def setup_header(self):
        """Main header for merging section."""
        self.merge_label = ttk.Label(self.merging_frame, text="Merge PDF Files", style="Blue.TLabel")
        self.merge_label.pack(pady=3)

    def setup_file_selection(self):
        """File selection controls."""
        # File selection button
        self.select_merge_files_button = ttk.Button(
            self.merging_frame,
            text="Select PDFs to Merge",
            command=self.select_merge_files
        )
        self.select_merge_files_button.pack(pady=5)
        ToolTip(self.select_merge_files_button, "Select multiple PDF files to merge.")

        # Selected files counter
        self.merge_status_label_selected = ttk.Label(
            self.merging_frame,
            text="No files selected yet",
            font=self.font,
            wraplength=400
        )
        self.merge_status_label_selected.pack(pady=10)

    def setup_compression_options(self):
        """Compression-related controls."""
        # Compression checkbox
        self.compress_before_merge_var = tk.BooleanVar(value=False)
        self.compress_checkbox = ttk.Checkbutton(
            self.merging_frame,
            text="Compress files before merging",
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
            ttk.Radiobutton(
                self.compression_frame,
                text=text,
                variable=self.merge_compression_level_var,
                value=value
            ).pack(side="left", padx=5)
        
        # Delete originals checkbox
        self.delete_after_merge_var = tk.BooleanVar(value=False)
        self.delete_checkbox = ttk.Checkbutton(
            self.merging_frame,
            text="Delete original files after merging",
            variable=self.delete_after_merge_var
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

        # Progress labels
        self.current_merge_file_label = ttk.Label(
            self.merging_frame,
            text="Current File: None",
            font=self.font,
            wraplength=400
        )
        self.current_merge_file_label.pack(pady=5)

        self.merge_status_label = ttk.Label(
            self.merging_frame,
            text="Waiting to start...",
            font=self.font,
            wraplength=400
        )
        self.merge_status_label.pack(pady=5)        

    def setup_post_merge_controls(self):
        """Post-merge action controls."""
        button_frame = ttk.Frame(self.merging_frame)
        button_frame.pack(pady=10)

        self.open_merged_file_button = ttk.Button(
            button_frame,
            text="Open Merged File",
            command=self.open_merged_file,
            state=tk.DISABLED
        )
        self.open_merged_file_button.pack(side="left", padx=5)
        ToolTip(self.open_merged_file_button, "Open merged PDF in default viewer")

        self.print_merged_file_button = ttk.Button(
            button_frame,
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
            self.start_merge_button.config(state=tk.NORMAL)

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
        threading.Thread(target=self.merge_files_thread, args=(output_file,), daemon=True).start()

    def merge_files_thread(self, output_file):
        """Background thread for merging process."""
        try:
            success, summary, error = merge_pdfs(
                self.merge_files,
                output_file,
                compress_before_merge=self.compress_before_merge_var.get(),
                compression_level=self.merge_compression_level_var.get(),
                update_callback=lambda f, p: self.root.after(0, self._update_progress, f, p)
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
        self.merge_status_label_selected.config(text=f"{count} PDF files selected")
        self.merge_progress.config(maximum=count)

    def _validate_inputs(self):
        """Validate user inputs before merging."""
        if not self.merge_files:
            messagebox.showwarning("No Files", "Select PDF files to merge first")
            return False
        if not self.output_name_var.get().endswith(".pdf"):
            messagebox.showerror("Invalid Name", "Output file must end with .pdf")
            return False
        """Validate user inputs before merging."""
        if len(self.merge_files) < 2:
            messagebox.showwarning("Insufficient Files", "Select at least two PDF files to merge.")
            return False
        if not self.output_name_var.get().endswith(".pdf"):
            messagebox.showerror("Invalid Name", "Output file must end with .pdf")
            return False
        return True

    def _get_output_path(self):
        """Determine output file path. Returns None if user cancels."""
        if not self.output_folder:
            # Get directory of first file if no output folder selected
            first_file = self.merge_files[0]
            default_output_folder = os.path.dirname(first_file)
            
            # Ask for confirmation
            if not messagebox.askokcancel(
                "No Output Folder",
                f"Files will be merged into:\n{default_output_folder}\nProceed?"
            ):
                return None  # Explicitly return None on cancel
            
            return os.path.join(default_output_folder, self.output_name_var.get())
        
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
        self.current_merge_file_label.config(text="Current File: None")
        self.merge_status_label.config(text="Starting merging process...")

    def _update_progress(self, current_file, progress):
        """Update progress indicators."""
        filename = os.path.basename(current_file)
        if len(filename) >= 30:
            filename = f"{filename[:27]}..."
            
        self.current_merge_file_label.config(text=f"Processing: {filename}")
        self.merge_progress["value"] = progress
        percentage = int((progress / len(self.merge_files)) * 100)
        self.progress_percentage_label.config(text=f"{percentage}%")
        self.merge_status_label.config(
            text=f"Merging file {progress} of {len(self.merge_files)}"
        )

    def _handle_merge_success(self, output_file, summary):
        """Handle successful merge."""
        self.open_merged_file_button.config(state=tk.NORMAL)
        self.print_merged_file_button.config(state=tk.NORMAL)
        self.show_summary("Merge Successful", f"Saved to: {output_file}\n\n{summary}")
        self.merge_status_label.config(text=f"Success! Merged to:\n{output_file}")

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
        """Handle original file deletion."""
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete {len(self.merge_files)} original files?"
        ):
            return

        deleted, failed = [], []
        for file in self.merge_files:
            try:
                os.remove(file)
                deleted.append(file)
            except Exception as e:
                failed.append(f"{file}: {str(e)}")

        if deleted or failed:
            self.show_summary(
                "Deletion Results",
                self._format_deletion_summary(deleted, failed)
            )

    def _format_deletion_summary(self, deleted, failed):
        """Format deletion results for display."""
        summary = []
        if deleted:
            summary.append("Successfully deleted:\n- " + "\n- ".join(deleted))
        if failed:
            summary.append("\nFailed to delete:\n- " + "\n- ".join(failed))
        return "\n".join(summary)

    def _reset_ui_state(self):
        """Reset UI to initial state."""
        self.start_merge_button.config(state=tk.NORMAL)
        self.merge_progress["value"] = 0
        self.current_merge_file_label.config(text="Current File: None")
        self.merge_status_label.config(text="Ready to start new merge")

    # --------------------- Post-Merge Actions ---------------------
    def show_summary(self, title, message):
        """Display merge summary in scrollable dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        
        text_area = scrolledtext.ScrolledText(
            dialog,
            width=90,
            height=45,
            font=("Segoe UI", 10),
            wrap=tk.WORD
        )
        text_area.pack(padx=10, pady=10, expand=True, fill="both")
        text_area.insert(tk.END, message)
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)
        dialog.transient(self.root)
        dialog.grab_set()

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