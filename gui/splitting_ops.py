# gui/splitting_ops.py
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText 
import subprocess
import time

from logic.split import split_pdf  # Import the split logic
from .utils import ToolTip, CustomText

class SplittingOps:
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

    # --------------------- UI Splitting Components Setup Methods ---------------------
    def setup_splitting_ui(self, parent):
        """Set up UI components for splitting."""
        self.splitting_frame = ttk.Frame(parent)
        self.splitting_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI components setup for splitting in order
        self.setup_header()
        self.setup_file_selection()
        self.setup_compression_options()
        self.setup_output_folder()
        self.setup_progress_bar()
        self.setup_start_split()
        self.setup_split_status()        
        self.setup_log_area()
        self.setup_post_split_ops()    

    def setup_header(self):
        """Main header for splitting section."""
        self.split_label = ttk.Label(self.splitting_frame, text="Split PDF File", style="Green_Header.TLabel")
        self.split_label.pack(pady=3)

    def setup_file_selection(self):
        # File selection button for splitting
        self.select_split_file_button = ttk.Button(
            self.splitting_frame,
            text="Select PDF to Split",
            command=self.select_split_file
        )
        self.select_split_file_button.pack(pady=5)
        ToolTip(self.select_split_file_button, "Select a PDF file to split.")    

    def setup_compression_options(self):
        """Compression-related controls."""
        # Compression checkbox
        self.compress_after_split_var = tk.BooleanVar(value=False)
        self.compress_checkbox = ttk.Checkbutton(
            self.splitting_frame,
            text="Try to compress files after splitting",
            variable=self.compress_after_split_var,
            command=self.toggle_compress_options
        )
        self.compress_checkbox.pack(pady=5)
        ToolTip(self.compress_checkbox, "Compress PDFs after splitting them")

    # Compression level radio buttons
        self.split_compression_level_var = tk.StringVar(value="medium")
        self.compression_frame = ttk.Frame(self.splitting_frame)
        self.compression_frame.pack(pady=5)
        
        for text, value in [("High", "high"), ("Medium", "medium"), ("Low", "low")]:
            rb = ttk.Radiobutton(
                self.compression_frame,
                text=text,
                variable=self.split_compression_level_var,
                value=value
            )
            rb.pack(side="left", padx=5)
            ToolTip(rb, "If the PDF has been previously compressed, further compression will yield minimal or no improvements.")

        # Delete originals checkbox
        self.delete_after_split_var = tk.BooleanVar(value=False)
        self.delete_checkbox = ttk.Checkbutton(
            self.splitting_frame,
            text="Delete original files after splitting",
            variable=self.delete_after_split_var, style = 'Warning.TCheckbutton',
        )
        self.delete_checkbox.pack(pady=10)
        ToolTip(self.delete_checkbox, "Permanently remove original files after split")

        self.toggle_compress_options()

    def setup_output_folder(self):
        # Output folder selection
        self.select_split_output_folder_button = ttk.Button(
            self.splitting_frame,
            text="Select Output Folder for Split",
            command=self.select_split_output_folder
        )
        self.select_split_output_folder_button.pack(pady=10)
        ToolTip(self.select_split_output_folder_button, "Choose where to save split PDFs")

    def setup_progress_bar(self):
        """Progress bar and status labels."""
        self.progress_frame = ttk.Frame(self.splitting_frame)
        self.progress_frame.pack(pady=35)
        
        self.progress = ttk.Progressbar(
            self.progress_frame,
            orient="horizontal",
            length=300,
            mode="determinate",
            style='Normal.Horizontal.TProgressbar'  # Initial style
        )
        self.progress.pack(side="left", padx=5)
        
        self.progress_percentage_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_percentage_label.pack(side="right", padx=5)

    def setup_start_split(self):
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

    def setup_split_status(self):
        # Selected files counter
        self.split_status_label_selected = ttk.Label(
            self.splitting_frame,
            text="Select a PDF file to begin",            
            wraplength=400
        )
        self.split_status_label_selected.pack(pady=10)    

    def setup_log_area(self):
        # Create a frame to hold the text widget and scrollbar
        text_frame = ttk.Frame(self.splitting_frame)
        text_frame.pack(fill="both", expand=True, pady=10, padx=10)

        """Logging textarea for split/compress messages."""
        self.log_area = CustomText(
            text_frame, 
            height=36, 
            width=46, 
            wrap="word", 
            state="disabled", 
            font=("Consolas", 9)
            )
        self.log_area.pack(side="left", fill="both", expand=True)        

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_area)
        scrollbar.pack(side="right", fill="y")
        self.log_area.config(yscrollcommand=scrollbar.set)

    def setup_post_split_ops(self):
        post_split_frame = ttk.Frame(self.splitting_frame)
        post_split_frame.pack(pady=10)
        
        # Open Output Folder button
        self.open_output_folder_button = ttk.Button(
            post_split_frame,
            text="Open Output Folder",
            command=self.open_output_folder,
            state=tk.DISABLED
        )
        self.open_output_folder_button.pack(side="left", padx=5)
        ToolTip(self.open_output_folder_button, "Open the output folder in file explorer")

        # Print splited files button
        self.print_split_files_button = ttk.Button(
            post_split_frame,
            text="Print Split Pages",  # Fixed grammar
            command=self.print_split_files,
            state=tk.DISABLED
        )
        self.print_split_files_button.pack(side="left", padx=5)
        ToolTip(self.print_split_files_button, "Print all individual split pages")  

    def select_split_output_folder(self):
        """Handle output folder selection for split files."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.split_output_folder = folder
            self.split_status_label_selected.config(text=f"Output folder: {folder}")
            #self.open_output_folder_button.config(state=tk.NORMAL)  # Enable open button

    def open_output_folder(self):
        """Open the output folder in system file explorer."""
        if not self.split_output_folder:
            messagebox.showwarning("No Folder", "No output folder selected")
            return
            
        if not os.path.isdir(self.split_output_folder):
            messagebox.showerror("Missing Folder", "Output folder no longer exists")
            return

        try:
            # Platform-specific folder opening
            if sys.platform == "win32":
                os.startfile(self.split_output_folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.split_output_folder], check=True)
            else:
                subprocess.run(["xdg-open", self.split_output_folder], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Couldn't open folder: {str(e)}")      

    def append_log(self, message):
        """Handle progress updates and regular messages"""
        self.log_area.configure(state="normal")
        
        # Check for split progress pattern
        if message.startswith("SPLIT_PROGRESS:"):
            _, progress = message.split(":", 1)
            current, total = progress.split("/")
            new_text = f"Splitting page {current}/{total} completed"
            
            # Check if last line was a progress update
            last_line_index = self.log_area.index('end-2c linestart')  # Get last line start
            last_line_text = self.log_area.get(last_line_index, 'end-1c')
            
            if "Splitting page" in last_line_text:
                # Delete previous progress line
                self.log_area.delete(last_line_index, 'end-1c lineend')
                self.log_area.insert(last_line_index, new_text)
            else:
                # New progress line
                self.log_area.insert('end', '\n' + new_text)
        else:
            # Regular message (preserve newlines)
            self.log_area.insert('end', message)
        
        self.log_area.configure(state="disabled")
        self.log_area.see('end')  # Auto-scroll     

    # --------------------- Core Functionality for Splitting ---------------------
    def toggle_compress_options(self):
        """Toggle compression level options visibility."""
        state = tk.NORMAL if self.compress_after_split_var.get() else tk.DISABLED
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
            self.split_status_label_selected.config(text=f"Selected file: {os.path.basename(file)}")
            self.start_split_button.config(state=tk.NORMAL)

    def select_split_output_folder(self):
        """Handle output folder selection for split files."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.split_output_folder = folder
            self.split_status_label_selected.config(text=f"Output folder: {folder}")

    def start_split(self):
        if self.compress_after_split_var.get():
            try:
                gs_cmd = 'gswin64c' if sys.platform == 'win32' else 'gs'
                subprocess.run([gs_cmd, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                messagebox.showerror("Ghostscript Required", "Install Ghostscript to use compression. \nDownload Ghostscript from https://www.ghostscript.com/")
                self._reset_ui_state()  # Add this
                return
            
        if not self.split_file or not self.split_output_folder:
            messagebox.showwarning("Missing Input", "Select a file and output folder before splitting.")
            return

        # Get compression settings from UI
        compress = self.compress_after_split_var.get()
        compression_level = self.split_compression_level_var.get()
        
        self._prepare_for_split()
        
        # Pass parameters to thread
        threading.Thread(
            target=self.split_file_thread,
            daemon=True,
            args=(compress, compression_level)  
        ).start()

    def split_file_thread(self, compress, compression_level):
        try:
            # Modified to receive 3 return values
            success, summary, output_files = split_pdf(
                self.split_file,
                self.split_output_folder,
                compress=compress,
                compression_level=compression_level,
                update_callback=lambda f, p: self.root.after_idle(self._update_split_progress, f, p),
                log_callback=lambda msg: self.root.after(0, self.append_log, msg)
            )
            
            if success:
                self.generated_files = output_files  # Store actual split files
                self._handle_split_success(summary)
            else:
                self.generated_files = []
                self._handle_split_error(summary)

        except Exception as e:
            if "Ghostscript" in str(e):
                self.root.after(0, lambda: messagebox.showerror(
                    "Ghostscript Required",
                    "Compression requires Ghostscript. Download it from:\nhttps://www.ghostscript.com/"
                ))
            else:
                self.root.after(0, self._handle_critical_error, e)  # Use the method
        finally:
            self._reset_ui_state()

    def _prepare_for_split(self):
        """Prepare UI for splitting process."""
        self.split_status_label_selected.config(text="Starting splitting process...")
        self.start_split_button.config(state=tk.DISABLED)

    def _update_split_progress(self, current_page, total_pages):
        """Update progress indicators with immediate UI refresh."""
        progress = int((current_page / total_pages) * 100)
        
        # Update progress components
        self.total_pages = total_pages
        self.progress["value"] = progress
        self.progress_percentage_label.config(text=f"{progress}%")
        self.split_status_label_selected.config(text=f"Splitting page {current_page} of {total_pages}")
        
        # Change progress bar style based on compression
        if self.compress_after_split_var.get():
            self.progress.config(style='Compress.Horizontal.TProgressbar')
        else:
            self.progress.config(style='Normal.Horizontal.TProgressbar')
        
        # Force immediate UI update
        self.root.update_idletasks()        

    def _handle_split_success(self, summary):
        msg = summary
        if self.delete_after_split_var.get():
            if messagebox.askyesno("Confirm Deletion", "Delete original file?"):
                os.remove(self.split_file)
                msg += f"\n\nOriginal file '{os.path.basename(self.split_file)}' deleted."
        messagebox.showinfo("Split Successful", msg)

    def _handle_split_error(self, error):
        """Handle split errors."""
        messagebox.showerror("Split Failed", f"Error: {error}")

    def _handle_critical_error(self, error):
        """Handle unexpected errors."""        
        messagebox.showerror(
            "Critical Error",
            f"Unexpected error:\n{str(error)}\nSee logs for details."
        )
        self.split_status_label_selected.config(text="Critical error occurred")

    def print_split_files(self):
        if not self.generated_files:
            messagebox.showwarning("Error", "No split files available for printing")
            return

        # Check if ANY files exist before proceeding
        existing_files = [f for f in self.generated_files if os.path.exists(f)]
        if not existing_files:
            messagebox.showerror("No Files", "All split files appear to be missing!")
            self._reset_ui_state()  # Will disable the print button
            return

        try:
            # Update confirmation message with ACTUAL existing files count
            confirmed = messagebox.askyesno(
                "Confirm Print",
                f"Found {len(existing_files)}/{len(self.generated_files)} files\n"
                "Proceed with printing available files?"
            )
            if not confirmed:
                return

            # Track successful print operations
            successfully_printed = 0
            
            for file_path in self.generated_files:
                if not os.path.exists(file_path):
                    self.append_log(f"⚠️ Missing: {os.path.basename(file_path)}")
                    continue

                try:
                    if sys.platform == "win32":
                        os.startfile(file_path, "print")
                    else:
                        subprocess.run(["lp", file_path], check=True)
                    
                    successfully_printed += 1
                    self.append_log(f"✅ Sent: {os.path.basename(file_path)}")
                    time.sleep(0.5)
                    
                except Exception as file_error:
                    self.append_log(f"❌ Failed {os.path.basename(file_path)}: {str(file_error)}")

            # Accurate final message
            msg = (
                f"Print jobs submitted: {successfully_printed}\n"
                f"Missing files: {len(self.generated_files) - len(existing_files)}\n"
                f"Print errors: {len(existing_files) - successfully_printed}"
            )
            
            if successfully_printed > 0:
                messagebox.showinfo("Print Summary", msg)
            else:
                messagebox.showerror("Print Failed", "No files were printed successfully")

        except Exception as e:
            messagebox.showerror("Print Error", f"Critical failure: {str(e)}")        

    def _reset_ui_state(self):
        """Check ACTUAL file existence for UI state"""
        existing_files = [f for f in self.generated_files if os.path.exists(f)]
        has_available_files = len(existing_files) > 0
        
        self.print_split_files_button.config(state=tk.NORMAL if has_available_files else tk.DISABLED)
        self.open_output_folder_button.config(state=tk.NORMAL if has_available_files else tk.DISABLED)
        self.start_split_button.config(state=tk.NORMAL if (self.split_file and self.split_output_folder) else tk.DISABLED)
        
        # Update status label with availability info
        status_text = (
            f"Ready - {len(existing_files)}/{len(self.generated_files)} files available"
            if self.generated_files else 
            "Ready for new operation"
        )
        self.split_status_label_selected.config(text=status_text)
        
        # Reset progress bar
        self.progress["value"] = 0
        self.progress_percentage_label.config(text="0%")     