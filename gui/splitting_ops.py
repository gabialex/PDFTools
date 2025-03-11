import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import time

from .print_manager import PrintManager  
from logic.split import split_pdf
from .utils import ToolTip, CustomText, format_time, truncate_path, truncate_filename


# Constants
FONT = ("Segoe UI", 10)
UI_PADDING = 10
PROGRESS_BAR_LENGTH = 300
LOG_AREA_HEIGHT = 36
LOG_AREA_WIDTH = 46

class SplittingOps:
    def __init__(self, root):
        self.root = root
        self.font = FONT
        self.split_file = None
        self.split_output_folder = ""
        self.split_start_time = None
        self.last_update_time = None
        self.eta = "Calculating..."
        self.generated_files = []
        self.print_manager = None  # PrintManager instance holder
        self.setup_variables()

    def setup_variables(self):
        self.split_files = []
        self.output_folder = ""
        self.split_file_path = None

    # --------------------- UI Splitting Components Setup Methods ---------------------
    def setup_splitting_ui(self, parent):
        self.splitting_frame = ttk.Frame(parent)
        self.splitting_frame.pack(side="left", fill="both", expand=True, padx=UI_PADDING, pady=5)
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
        self.split_label = ttk.Label(self.splitting_frame, text="Split PDF File", style="Blue_Header.TLabel")
        self.split_label.pack(pady=5)

    def setup_file_selection(self):
        self.select_split_file_button = ttk.Button(self.splitting_frame, text="Select PDF to Split", command=self.select_split_file)
        self.select_split_file_button.pack(pady=20)
        ToolTip(self.select_split_file_button, "Select a PDF file to split.")

    def setup_compression_options(self):
        self.compress_after_split_var = tk.BooleanVar(value=False)
        self.compress_checkbox = ttk.Checkbutton(self.splitting_frame, text="Try to compress files after splitting", variable=self.compress_after_split_var, command=self.toggle_compress_options)
        self.compress_checkbox.pack(pady=7)
        ToolTip(self.compress_checkbox, "Compress PDFs after splitting them")

        self.split_compression_level_var = tk.StringVar(value="medium")
        self.compression_frame = ttk.Frame(self.splitting_frame)
        self.compression_frame.pack(pady=5)
        for text, value in [("High", "high"), ("Medium", "medium"), ("Low", "low")]:
            rb = ttk.Radiobutton(self.compression_frame, text=text, variable=self.split_compression_level_var, value=value)
            rb.pack(side="left", padx=5)
            ToolTip(rb, "If the PDF has been previously compressed, further compression will yield minimal or no improvements.")

        self.delete_after_split_var = tk.BooleanVar(value=False)
        self.delete_checkbox = ttk.Checkbutton(self.splitting_frame, text="Delete original files after splitting", variable=self.delete_after_split_var, style='Warning.TCheckbutton')
        self.delete_checkbox.pack(pady=10)
        ToolTip(self.delete_checkbox, "Permanently remove original files after split")
        self.toggle_compress_options()

    def setup_output_folder(self):
        self.select_split_output_folder_button = ttk.Button(self.splitting_frame, text="Select Output Folder for Split", command=self.select_split_output_folder)
        self.select_split_output_folder_button.pack(pady=10)
        ToolTip(self.select_split_output_folder_button, "Choose where to save split PDFs")

    def setup_progress_bar(self):
        empty_frame = ttk.Frame(self.splitting_frame)
        empty_frame.pack(pady=15) # Keep this empty for a future element
        self.progress_frame = ttk.Frame(self.splitting_frame)
        self.progress_frame.pack(pady=20)
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=PROGRESS_BAR_LENGTH, mode="determinate", style='Normal.Horizontal.TProgressbar')
        self.progress.pack(side="left", padx=5)
        self.progress_percentage_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_percentage_label.pack(side="right", padx=5)

    def setup_start_split(self):
        self.start_split_button = ttk.Button(self.splitting_frame, text="Start Splitting", command=self.start_split, style="Red.TButton", state=tk.DISABLED)
        self.start_split_button.pack(pady=10)
        ToolTip(self.start_split_button, "Begin splitting process")

    def setup_split_status(self):
        self.split_status_label_selected = ttk.Label(self.splitting_frame, text="Select a PDF file to begin", wraplength=400)
        self.split_status_label_selected.pack(pady=10)

    def setup_log_area(self):
        text_frame = ttk.Frame(self.splitting_frame)
        text_frame.pack(fill="both", expand=True, pady=10, padx=10)
        self.log_area = CustomText(text_frame, height=LOG_AREA_HEIGHT, width=LOG_AREA_WIDTH, wrap="word", state="disabled", font=("Consolas", 9))
        self.log_area.pack(side="left", fill="both", expand=True)          

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_area)
        scrollbar.pack(side="right", fill="y")
        self.log_area.config(yscrollcommand=scrollbar.set)

    def setup_post_split_ops(self):
        post_split_frame = ttk.Frame(self.splitting_frame)
        post_split_frame.pack(pady=10)
        self.open_output_folder_button = ttk.Button(post_split_frame, text="Open Output Folder", command=self.open_output_folder, state=tk.DISABLED)
        self.open_output_folder_button.pack(side="left", padx=5)
        ToolTip(self.open_output_folder_button, "Open the output folder in file explorer")
        self.print_split_files_button = ttk.Button(post_split_frame, text="Print Split Pages", command=self._handle_print_button, state=tk.DISABLED)
        self.print_split_files_button.pack(side="left", padx=5)
        ToolTip(self.print_split_files_button, "Print selected split pages with options")

    def _handle_print_button(self):
        if self.print_manager:
            self.print_manager.show_print_dialog()
        else:
            messagebox.showwarning("No Files", "Please split a file first")

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
        """Handle split progress and regular messages"""
        self.log_area.configure(state="normal")
        
        if message.startswith("SPLIT_PROGRESS:"):
            # Existing split progress handling
            _, progress = message.split(":", 1)
            current, total = progress.split("/")
            new_text = f"  ▶ Splitting page {current} of {total}"
            
            # Delete previous progress line
            last_line_index = self.log_area.index('end-2c linestart')
            last_line = self.log_area.get(last_line_index, 'end-1c')
            
            if "Splitting page" in last_line:
                self.log_area.delete(last_line_index, 'end-1c lineend')
                self.log_area.insert(last_line_index, new_text)
            else:
                #self.log_area.insert('end', '\n' + new_text)
                self.log_area.insert('end', new_text)
        else:
            # Regular messages with newlines preserved
            self.log_area.insert('end', message + '\n')
        
        self.log_area.configure(state="disabled")
        self.log_area.see('end')

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
            self._update_selection_display()            

    def select_split_output_folder(self):
        """Handle output folder selection for split files."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.split_output_folder = folder
            self._update_selection_display()
        self.start_split_button.config(state=tk.NORMAL, style = 'Ready.TButton' if (self.split_file and self.split_output_folder) else tk.DISABLED)

    def _update_selection_display(self):
        """Update log area with selection info."""
        self.log_area.configure(state="normal")
        self.log_area.delete('1.0', 'end')  # Clear existing content
        
        # Show selected file info       
        if self.split_output_folder:
            truncated_folder_line = truncate_path(self.split_output_folder, 2, '...', 45)
            folder_line = f"📁 {truncated_folder_line}\n"
            self.log_area.insert('end', folder_line)       
        
        if self.split_file:
            try:
                file_size = os.path.getsize(self.split_file)
                mb_size = file_size / (1024 * 1024)
                filename = os.path.basename(self.split_file)
                truncated_file_line = truncate_filename(filename, '...', 45)
                file_line = f"  📄 {truncated_file_line} ({mb_size:.2f} MB)\n"
                self.log_area.insert('end', file_line)
            except Exception as e:
                self.log_area.insert('end', f"⚠️ Error reading file: {str(e)}\n")
        
        # Show summary if both selected
        if self.split_file and self.split_output_folder:
            try:
                total_size = os.path.getsize(self.split_file) 
                mb_total = total_size / (1024 * 1024)
                summary = f"\nSelected 1 file ({mb_total:.2f} MB) for splitting"
                self.log_area.insert('end', summary)
            except:
                pass
        
        # Add separator for process logs
        self.log_area.insert('end', "\n" + "━" * 50 + "\n")
        self.log_area.configure(state="disabled")
        self.log_area.see('end')    

    def start_split(self):
        if self.compress_after_split_var.get():
            try:
                gs_cmd = 'gswin64c' if sys.platform == 'win32' else 'gs'
                subprocess.run([gs_cmd, "--version"], 
                             check=True, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
            except:
                messagebox.showerror("Ghostscript Required", "Install Ghostscript to use compression. \nDownload Ghostscript from https://www.ghostscript.com/")
                self._reset_ui_state()  
                return
            
        if not self.split_file or not self.split_output_folder:
            messagebox.showwarning("Missing Input", "Select a file and output folder before splitting.")
            return

        self._prepare_for_split() 
        threading.Thread(
            target=self.split_file_thread,
            daemon=True,
            args=(
                self.compress_after_split_var.get(),
                self.split_compression_level_var.get()
            )  
        ).start()

    def split_file_thread(self, compress, compression_level):
        try:
            success, summary, output_files = split_pdf(
                self.split_file,
                self.split_output_folder,
                compress=compress,
                compression_level=compression_level,
                update_callback=lambda f, p: self.root.after_idle(self._update_split_progress, f, p),
                log_callback=lambda msg: self.root.after(0, self.append_log, msg)
            )

            self.root.after(0, self._handle_split_result, success, summary, output_files)

        except Exception as e:
            self.root.after(0, self._handle_critical_error, e)
        finally:
            self.root.after(0, self._reset_ui_state)

    def _handle_split_result(self, success, summary, output_files):
        if success:
            self.generated_files = output_files
            self.print_manager = PrintManager(
                self.root,
                self.generated_files,
                self.append_log
            )
            self._handle_split_success(summary)
        else:
            self.generated_files = []
            self._handle_split_error(summary)

    def _prepare_for_split(self):
        """Prepare UI for splitting process."""
        self.split_start_time = time.time()
        self.last_update_time = self.split_start_time
        self.eta = "Calculating..."
        self.split_status_label_selected.config(text="\nStarting splitting process...")
        self.start_split_button.config(state=tk.DISABLED)

    def _update_split_progress(self, current_page, total_pages):
        """Update progress with ETA calculation"""
        now = time.time()

        # Add null check for safety
        if self.split_start_time is None:
            self.split_start_time = now  # Fallback initialization

        elapsed = now - self.split_start_time

        # Change progress bar style based on compression
        if self.compress_after_split_var.get():
            self.progress.config(style='Compress.Horizontal.TProgressbar')                
        
        # Calculate ETA only after first page to avoid division by zero
        if current_page > 1:
            time_per_page = elapsed / (current_page - 1)
            remaining_pages = total_pages - current_page
            eta_seconds = remaining_pages * time_per_page
            self.eta = format_time(eta_seconds)
        else:
            self.eta = "Calculating..."
            
        # Update progress components
        progress = int((current_page / total_pages) * 100)
        status_text = (            
            f" Time remaining: {self.eta}"
        )
        
        self.progress["value"] = progress
        if self.compress_after_split_var.get():
            self.split_status_label_selected.config(text=status_text, style = 'Orange.TLabel')
            self.progress_percentage_label.config(text=f"{progress}%  ", style = '')
        else:
            self.split_status_label_selected.config(text=status_text, style = 'Blue.TLabel')
            self.progress_percentage_label.config(text=f"{progress}%  ", style = 'Blue.TLabel' )
        
        # Force UI update
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
        self.split_status_label_selected.config(text=status_text, style = "")
        
        # Reset progress bar
        self.progress["value"] = 0
        self.progress_percentage_label.config(text="0%", style = "")
       