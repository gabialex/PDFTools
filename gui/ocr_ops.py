#gui/ocr_ops.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import tkinter.messagebox as messagebox
import threading
import re
import platform
import subprocess
import time
import datetime
import ctypes

from gui.utils import ToolTip, CustomText
from logic.ocr import ocr_pdf
from .utils import is_directory_writable, truncate_filename
from .print_manager import PrintManager 

class OCROpsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_variables()
        self.font = ("Segoe UI", 10)
        self.overwrite_files = False  # Flag for overwrite decision
        self.last_output_dir = None
        self.output_dir = None  # Variable for custom output directory
        self.alternative_dir_for_all = None 
        self.page_progress_tag = "page_progress"
        self.current_progress_start = None
        self.current_progress_end = None
        self.ocr_thread = None
        self.cancelled = False
        self.currently_processing = False 
        # Printing
        self.print_manager = None  
        self.ocr_output_files = []  # To store OCR results

        # Pause state variables
        self.pause_event = threading.Event()
        self.resume_event = threading.Event()
        self.paused_state = {
            'current_file': None,
            'current_page': 0,
            'remaining_files': []
        }

        # ETA variables
        self.processing_timers = {
            'start_time': None,
            'total_paused_duration': 0.0,
            'pause_start_time': None,
            'current_file_start': None,
            'current_file_paused': 0.0
        }

    def setup_variables(self):
        """Initialize OCR variables."""
        self.input_pdf = ""
        self.lang_var = tk.StringVar(value="ron")

    def setup_ocr_ui(self, parent):
        """Set up the OCR UI components with better alignment."""
        self.ocr_frame = ttk.Frame(parent)
        self.ocr_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI Components in order
        self.setup_ocr_header()
        self.setup_ocr_file_selection()        
        self.setup_ocr_language_selection()                       
        self.setup_output_directory_selector()  
        self.setup_pb_frames_and_label()
        self.setup_action_buttons()
        self.setup_selected_label()         
        self.setup_text_and_sb_frame()
        self.post_ocr_ops()        

    # ---------------------------------- UI Setup Methods ---------------------
    def setup_ocr_header(self):
        self.ocr_label = ttk.Label(self.ocr_frame, text="OCR PDF Files", style="Blue_Header.TLabel")
        self.ocr_label.pack(pady=5)

    def setup_ocr_file_selection(self): 
        """File selection for input PDF or directory for batch processing."""
        
        # Create a frame for the buttons
        button_frame = ttk.Frame(self.ocr_frame)
        button_frame.pack(pady=20)

        # Button for selecting folder        
        folder_button = ttk.Button(button_frame, text="Select Folder", command=self.select_folder)
        folder_button.pack(side="left", padx=5, pady=5)

        # Button for selecting individual PDF
        browse_button = ttk.Button(button_frame, text="Select Files", command=self.select_pdf)
        browse_button.pack(side="left", padx=5, pady=5)               

        # Tooltips for user guidance        
        ToolTip(browse_button, "Browse and select the PDF file", delay=500)
        ToolTip(folder_button, "Browse and select a folder for batch OCR", delay=500)     

    def setup_ocr_language_selection(self):
        """Language selection for OCR."""
        lang_frame = ttk.Frame(self.ocr_frame)
        lang_frame.pack(pady=5)
        
        ttk.Label(lang_frame, text="Select OCR Language:").pack(side="left", padx=5)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=["ron", "eng", "fra", "deu", "spa"], width=5)
        lang_combo.pack(side="left", padx=5)        
        ToolTip(lang_combo, "Language for OCR (Tesseract)", delay=500)

        # Format selection
        self.format_var = tk.StringVar(value="docx")
        ttk.Label(lang_frame, text="Format:").pack(side="left", padx=5)
        format_combo = ttk.Combobox(lang_frame, textvariable=self.format_var,
                                values=["docx", "rtf"], width=5)
        format_combo.pack(side="left", padx=5)        
        ToolTip(format_combo, "Output file format", delay=500)

    def setup_output_directory_selector(self):
        """Add output directory selection components."""
        output_frame = ttk.Frame(self.ocr_frame)
        output_frame.pack(pady=5, fill="x", padx=5)        

        # Output directory button
        output_btn = ttk.Button(output_frame, text="Select Output Folder", command=self.select_output_folder, style="Small.TButton")
        output_btn.pack(pady=20)
        ToolTip(output_btn, "Select custom output directory for OCR results")

    def setup_pb_frames_and_label(self):        
        self.per_file_progress_frame = ttk.Frame(self.ocr_frame)
        self.per_file_progress_frame.pack(pady=0, padx=5)        

        # Per-file progress text
        self.per_file_progress_text = ttk.Label(self.per_file_progress_frame, text="", style="Orange.TLabel")
        self.per_file_progress_text.pack(pady=0)        

        # Progress Bar for File Completion (Per-File)
        self.per_file_progress_bar = ttk.Progressbar(self.per_file_progress_frame, 
            orient="horizontal", length=300, mode="determinate")
        self.per_file_progress_bar.config(style='Compress.Horizontal.TProgressbar')
        self.per_file_progress_bar.pack(side="left", padx=5, pady=0)

        # Per-file percent text
        self.per_file_percentage_label = ttk.Label(self.per_file_progress_frame, text="0%")
        self.per_file_percentage_label.pack(side="left", padx=5)

        # Progress Bar for Total Completion (Across All Files)
        self.total_progress_frame = ttk.Frame(self.ocr_frame)
        self.total_progress_frame.pack(pady=0, padx=5)

        # Total progress text
        self.total_progress_text = ttk.Label(self.total_progress_frame, text="", style="Blue.TLabel"
        )
        self.total_progress_text.pack(pady=0)    

        # Progress Bar for Total Files Completion
        self.total_progress_bar = ttk.Progressbar(self.total_progress_frame, 
            orient="horizontal", length=300, mode='determinate')        
        self.total_progress_bar.config(style='Normal.Horizontal.TProgressbar')
        self.total_progress_bar.pack(side="left", pady=0, padx=5)

        # Total percent text
        self.total_percentage_label = ttk.Label(self.total_progress_frame, text="0%")
        self.total_percentage_label.pack(side="left", padx=5)

    def setup_action_buttons(self):
        """Run OCR button setup with an initial disabled state."""
        action_buttons_frame = ttk.Frame(self.ocr_frame)
        action_buttons_frame.pack(pady=35)        

        # Run OCR button
        self.run_button = ttk.Button(
            action_buttons_frame,
            text="▶ Run OCR",
            command=self.run_ocr,
            state="disabled"  # Button is disabled initially
        )
        self.run_button.pack(side = "left", padx=5, pady=1)
        ToolTip(self.run_button, "Extract text from PDF using OCR. \nSelect Folders or Select Files to start.", delay=500)        

        # Pause/Resume button
        self.pause_resume_button = ttk.Button(
            action_buttons_frame,
            text="⏸ Pause",
            command= self.toggle_pause_resume,
            state="disabled"
        )
        self.pause_resume_button.pack(side="left", padx=5)
        ToolTip(self.pause_resume_button, "Pause/Resume OCR operation", delay=500)

        # Cancel button
        self.cancel_button = ttk.Button(
            action_buttons_frame,
            text="⏹ Cancel",
            command=self.cancel_ocr,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=5)
        ToolTip(self.cancel_button, "Cancel all OCR operations", delay=500)

    def setup_selected_label(self):
        # Selected files label
        self.selected_files_label = ttk.Label(self.ocr_frame, text="Select at least a PDF to OCR")
        self.selected_files_label.pack(pady=10)           

    def setup_text_and_sb_frame(self):
        # Create a frame to hold the text widget and scrollbar
        text_frame = ttk.Frame(self.ocr_frame)
        text_frame.pack(fill="both", expand=True, pady=15, padx=10)

        # Scrollable Text Widget for displaying messages
        self.message_text = CustomText(
            text_frame, 
            height=36, 
            width=46, 
            wrap="word", 
            state="disabled")
        self.message_text.pack(side="left", fill="both", pady=1, expand=True)

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.message_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.message_text.config(yscrollcommand=scrollbar.set)    

    def post_ocr_ops(self):
        # Add Open Folder button under the text area
        self.post_ocr_ops_frame = ttk.Frame(self.ocr_frame)
        self.post_ocr_ops_frame.pack(pady=5)

        # Open Output Folder button
        self.open_folder_btn = ttk.Button(
            self.post_ocr_ops_frame,
            text="Open Output Folder",
            state="disabled",
            command=self.open_output_folder
        )
        self.open_folder_btn.pack(side='left', pady=5, padx=5)
        ToolTip(self.open_folder_btn, "Open the output folder in file explorer")

        # Print button
        self.print_button = ttk.Button(
            self.post_ocr_ops_frame,
            text="Print OCR Results",
            command=self._handle_print_button,
            state="disabled"
        )
        self.print_button.pack(side='left', pady=5, padx=5)
        ToolTip(self.print_button, "Print OCR results")

    def _handle_print_button(self):
        """Open native print dialogs for OCR results with full user control."""
        if not self.ocr_output_files:
            messagebox.showwarning("No Files", "No OCR results available to print.")
            return

        for file_path in self.ocr_output_files:
            if not os.path.exists(file_path):
                self.update_message(f"File not found: {file_path}", "error")
                continue

            try:
                system = platform.system()
                if system == "Windows":
                    # Windows: Use system print dialog
                    if os.path.splitext(file_path)[1].lower() == '.docx':
                        # For Word documents use Word's print dialog
                        self._windows_word_print(file_path)
                    else:
                        # Generic method for other formats
                        ctypes.windll.shell32.ShellExecuteW(None, "print", file_path, None, None, 0)

                elif system == "Darwin":
                    # macOS: Use AppleScript to open print dialog
                    self._macos_print(file_path)

                else:  # Linux
                    # Linux: Use xdg-open with xdotool for Ctrl+P
                    self._linux_print(file_path)

                self.update_message(f"Print dialog opened for: {os.path.basename(file_path)}", "success")

            except Exception as e:
                self.update_message(f"Print error: {str(e)}", "error")

    def _windows_word_print(self, file_path):
        """Windows-specific Word document printing."""
        main_window = self.winfo_toplevel()
        try:
            import win32com.client
            # Minimize the main window before showing the print dialog
            main_window.iconify()
            
            word = win32com.client.Dispatch("Word.Application")
            doc = word.Documents.Open(file_path)
            word.Visible = True
            # Show print dialog (wdDialogFilePrint = 88)
            word.Dialogs(88).Show()
            
            # Restore the main window after the dialog is closed
            main_window.deiconify()
        except Exception as e:
            # Ensure the window is restored even if an error occurs
            main_window.deiconify()
            # Fallback to system print dialog
            ctypes.windll.shell32.ShellExecuteW(None, "print", file_path, None, None, 0)

    def _macos_print(self, file_path):
        """macOS-specific printing with AppleScript."""
        script = f'''
        tell application "Preview"
            activate
            open POSIX file "{file_path}"
            delay 1  -- Allow time for file to open
            tell application "System Events"
                keystroke "p" using command down
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script])

    def _linux_print(self, file_path):
        """Linux printing with xdotool."""
        try:
            # Try to print via LibreOffice first
            subprocess.run([
                "libreoffice",
                "--writer",
                "--nologo",
                "--norestore",
                "--headless",
                "--printer='Print Dialog'",
                file_path
            ])
        except FileNotFoundError:
            # Fallback to xdotool method
            subprocess.Popen(["xdg-open", file_path])
            time.sleep(1)  # Wait for document viewer to open
            subprocess.run([
                "xdotool", "search", "--name", os.path.basename(file_path),
                "windowactivate", "key", "ctrl+p"
            ])

    def select_output_folder(self):
        """Handle output directory selection."""
        initial_dir = self.output_dir or os.path.expanduser("~")
        folder_path = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Select Output Folder for OCR Results"
        )
        if folder_path:
            # Check if directory is writable
            writable, error_msg = is_directory_writable(folder_path)
            if not writable:
                messagebox.showerror(
                    "Directory Not Writable",
                    f"Cannot write to selected directory:\n{error_msg}"
                )
                return
            
            self.output_dir = folder_path
            self.last_output_dir = folder_path            
            self.update_message(f"\nOutput directory set to:\n{folder_path}", "success") # Show confirmation of change

            # Re-check existing files if any are selected
            if hasattr(self, 'file_paths') and self.file_paths:
                self.check_existing_outputs()
                self.update_file_display()

    def select_folder(self):
        """Open folder dialog and include subfolders"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            # Clear previous files
            self.file_paths = []
            
            # Recursively search for PDF files
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file)
                        self.file_paths.append(full_path)
            
            # Check for existing OCR files
            self.check_existing_outputs()
            self.update_file_display()

            # Check if Run OCR button should be enabled
            self.check_run_button_state()

    def check_existing_outputs(self):
        """Modified to check in selected output directory"""
        existing_files = []
        for pdf_path in self.file_paths:
            # Determine correct output directory
            output_dir = self.output_dir or os.path.dirname(pdf_path)
            output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.docx"
            output_path = os.path.join(output_dir, output_filename)
            
            if os.path.exists(output_path):
                existing_files.append(output_path)

        if existing_files:
            response = self.show_overwrite_warning(existing_files)
            if response is None:  # Cancel
                self.file_paths = []
                return
            elif not response:  # Skip existing
                self.file_paths = [
                    fp for fp in self.file_paths
                    if not os.path.exists(os.path.join(
                        self.output_dir or os.path.dirname(fp),
                        f"OCR_{os.path.splitext(os.path.basename(fp))[0]}.pdf.txt"
                    ))
                ]
            self.overwrite_files = response

        self.check_run_button_state()   

    # ---------------------------- Functionality Methods -------------------------------
    # ETA Functions    
    def get_elapsed_time(self):
        """Get actual processing time excluding paused periods"""
        if not self.processing_timers['start_time']:
            return 0.0
        total_elapsed = time.time() - self.processing_timers['start_time']
        return total_elapsed - self.processing_timers['total_paused_duration']

    def format_etr(self, seconds):
        """Convert seconds to human-readable time format"""
        if seconds < 0:
            return ""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def calculate_etr(self, processed_items, total_items, elapsed_time):
        """Safer ETR calculation with zero checks"""
        if processed_items <= 0 or elapsed_time <= 0 or total_items <= 0:
            return ""
        
        try:
            items_remaining = total_items - processed_items
            time_per_item = elapsed_time / processed_items
            return self.format_etr(time_per_item * items_remaining)
        except ZeroDivisionError:
            return "--:--"
    
    # Pause/Resume and Cancel OCR Functions
        
    def toggle_pause_resume(self):
        """Toggle between pause and resume states."""
        if self.pause_event.is_set():
            # Resume the processing
            pause_duration = time.time() - self.processing_timers['pause_start_time']
            self.processing_timers['total_paused_duration'] += pause_duration
            self.processing_timers['current_file_paused'] += pause_duration
            self.pause_event.clear()
            self.resume_event.set()
            self.pause_resume_button.config(text="⏸ Pause")
            self.update_message("Resuming OCR process...", "success")
        else:
            # Pause the processing
            self.processing_timers['pause_start_time'] = time.time()
            self.pause_event.set()
            self.pause_resume_button.config(text="▶ Resume")
            self.update_message("Pausing OCR process after current page...", "warning")
        
    def cancel_ocr(self):
        """Handle OCR cancellation request"""
        if self.currently_processing:
            self.cancelled = True
            # Ensure any paused thread is resumed to allow cancellation
            self.resume_event.set()
            self.run_button.config(state="disabled")
            self.cancel_button.config(state="disabled")
            self.after(0, self.update_message, 
                      "⚠️ Cancellation requested... Stopping after current file", 
                      "warning")            
            # Set a watchdog to force cleanup if thread doesn't respond
            self.after(5000, self.force_cancel_cleanup)

    def force_cancel_cleanup(self):
        """Force cleanup if thread doesn't respond to cancellation"""
        if self.currently_processing:
            self.after(0, self.update_message, 
                      "⚠️ Forced cancellation - some files might be incomplete", 
                      "error")
            self.finalize_ocr_cleanup()

    def finalize_ocr_cleanup(self):
        """Common cleanup tasks"""
        was_cancelled = self.cancelled  # Capture state before reset
        self.currently_processing = False
        self.cancelled = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="normal")
        self.pause_resume_button.config(state="disabled")  # Disable pause button
                
        # Reset progress bars
        self.per_file_progress_bar["value"] = 0
        self.total_progress_bar["value"] = 0
        self.per_file_progress_text.config(text="Cancelled")
        self.total_progress_text.config(text="Cancelled")

        # Disable print button if no results
        if not self.ocr_output_files:
            self.print_button.config(state="disabled")

        return was_cancelled  # Return whether it was cancelled

    def update_file_display(self):
        """Display files in a folder hierarchy with sizes"""
        self.message_text.config(state="normal")
        self.message_text.delete(1.0, tk.END)
        
        if not self.file_paths:
            self.selected_files_label.config(text="No files selected yet")
            self.message_text.config(state="disabled")
            return

        # Organize files by their directory
        file_tree = {}
        for fp in self.file_paths:
            dir_path = os.path.dirname(fp)
            file_name = os.path.basename(fp)
            if dir_path not in file_tree:
                file_tree[dir_path] = []
            file_tree[dir_path].append(file_name)

        # Display folder structure
        max_files_per_folder = 10
        for folder, files in file_tree.items():
            folder_name = os.path.basename(folder)
            self.message_text.insert(tk.END, f"📁 {folder_name}/\n")
            
            # Sort files naturally
            sorted_files = sorted(files, key=lambda x: [int(s) if s.isdigit() else s.lower() for s in re.split('(\d+)', x)])
            
            # Show first 10 files with sizes
            for file in sorted_files[:max_files_per_folder]:
                full_path = os.path.join(folder, file)
                try:
                    size_bytes = os.path.getsize(full_path)
                    size_mb = size_bytes / (1024 * 1024)
                    size_str = f"{size_mb:.2f} MB"
                except OSError:
                    size_str = "N/A"
                
                self.message_text.insert(tk.END, f"    • {file} ({size_str})\n")
            
            # Show "+ more" message if needed
            remaining = len(sorted_files) - max_files_per_folder
            if remaining > 0:
                self.message_text.insert(tk.END, f"    ...{remaining} more files\n")
            
            self.message_text.insert(tk.END, "\n")  # Add space between folders

        # Add total size information
        total_size = sum(os.path.getsize(fp) for fp in self.file_paths)
        total_size_mb = total_size / (1024 * 1024)
        self.message_text.insert(tk.END, 
            f"Selected {len(self.file_paths)} files ({total_size_mb:.2f} MB)\n"
        )

        self.message_text.config(state="disabled")
        self.selected_files_label.config(foreground="blue")
        self.selected_files_label.config(
            text=f"{len(self.file_paths)} file{'s' if len(self.file_paths) > 1 else ''} selected. Press Run OCR to start."
        )

    def check_run_button_state(self):
        """Enable the Run OCR and Cancel buttons and change their color if files are selected."""
        if hasattr(self, 'file_paths') and self.file_paths:
            # Enable the button and apply color style            
            self.run_button.config(state="normal", style="Ready.TButton")            
            self.cancel_button.config(state="normal", style="RedText.TButton")
        else:
            # Disable the button if no files are selected
            self.run_button.config(state="disabled", style="")
            self.cancel_button.config(state="normal", style="")

    def open_output_folder(self):
        """Open the output folder in system file explorer"""
        target_dir = None
        
        # Check in this priority:
        # 1. Explicitly set output directory
        # 2. Directory of last processed file
        # 3. Directory is protected and user chose another directory
        # 4. Directory of first selected file
        if self.output_dir:
            target_dir = self.output_dir
        elif self.last_output_dir:
            target_dir = self.last_output_dir
        elif self.alternative_dir_for_all is not None:
            target_dir = self.alternative_dir_for_all
        elif hasattr(self, 'file_paths') and self.file_paths:
            target_dir = os.path.dirname(self.file_paths[0])        

        if target_dir and os.path.isdir(target_dir):
            try:
                if platform.system() == "Windows":
                    os.startfile(target_dir)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", target_dir])
                else:
                    subprocess.run(["xdg-open", target_dir])
            except Exception as e:
                self.update_message(f"Could not open folder: {str(e)}", "error")
        else:
            self.update_message("No output folder available - process some files first", "warning")
    
    def select_pdf(self):
        """Open file dialog and store paths"""
        filepaths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if filepaths:
            self.file_paths = list(filepaths)
            self.check_existing_outputs()
            self.update_file_display()

            # Check if Run OCR button should be enabled
            self.check_run_button_state()

    def update_message(self, message, message_type="info"):
        """Thread-safe message update"""
        self.after(0, self._update_message_internal, message, message_type)

    def _update_message_internal(self, message, message_type):
        """Actual message update to be called via after()"""
        self.message_text.config(state="normal")
        
        # Configure tags
        self.message_text.tag_configure("file_header", foreground="blue", font=("Segoe UI", 10))
        self.message_text.tag_configure("progress", font=("Segoe UI", 9))
        self.message_text.tag_configure("success", font=("Segoe UI", 10))
        self.message_text.tag_configure("warning", foreground="red", font=("Segoe UI", 10))
        self.message_text.tag_configure("error", foreground="#d62728", font=("Segoe UI", 10))

        # Insert message with appropriate tag
        self.message_text.insert("end", f"{message}\n", message_type)
        self.message_text.see("end")
        self.message_text.config(state="disabled")

        # Cleanup old messages
        if int(self.message_text.index('end-1c').split('.')[0]) > 1000:
            self.message_text.delete(1.0, "end -800 lines")

    def run_ocr(self):
        self.alternative_dir_for_all = None  # Reset previous choice
        self.run_button.config(state="disabled")

        # Re-check existing outputs with current directory before processing
        if hasattr(self, 'file_paths') and self.file_paths:
            self.check_existing_outputs()  # Now checks against current self.output_dir
            self.update_file_display()     # Show potentially filtered list   

        # Validate output directory choice
        if not self.output_dir:
            response = messagebox.askyesno(
                "Output Location",
                "OCR results will be saved in the same directory as original files."
                "\n\nYes to proceed \nNo to select another folder",
                icon="question")
            
            if not response:
                self.ocr_frame.config(cursor="")
                self.run_button.config(state="normal")
                self.select_output_folder()                

        # Proceed with OCR only if files remain after re-check
        if hasattr(self, 'file_paths') and self.file_paths:
            language = self.lang_var.get()
            thread = threading.Thread(target=self.process_files, args=(self.file_paths, language))
            thread.start()
        else:
            self.update_message("No files to process after output directory check", "warning")
            self.run_button.config(state="normal") 

    def process_files(self, file_paths, language):
        self.ocr_output_files = []  # Reset previous results
        # Reset labels at start
        self.after(0, lambda: self.per_file_progress_text.config(
            text="| ETR:"
        ))
        self.after(0, lambda: self.total_progress_text.config(
            text="Total Progress: 0% | ETA:"
        ))
        self.processing_timers = {
            'start_time': time.time(),
            'total_paused_duration': 0.0,
            'pause_start_time': None,
            'current_file_start': None,
            'current_file_paused': 0.0
        }

        self.currently_processing = True
        self.cancelled = False  # Reset cancellation flag
        self.after(0, self.pause_resume_button.config, {'state': 'normal'})  # Enable pause button

        start_time = time.time()
        total_files = len(file_paths)
        processed_count = 0
        skipped_files = []
        permission_errors = []  # List for permission-related skips        

        # Initialize progress bars
        self.after(0, self.per_file_progress_bar.config, {"maximum": 100, "value": 0})
        self.after(0, self.total_progress_bar.config, {"maximum": total_files, "value": 0})

        try:
            for index, pdf_path in enumerate(file_paths):
                if self.cancelled:
                    self.after(0, self.update_message, 
                              "⏹ Processing cancelled by user", "warning")
                    break

                # Reset progress positions for new file
                self.current_progress_start = None
                self.current_progress_end = None
                
                # Show file header
                filename = os.path.basename(pdf_path)
                display_name = truncate_filename(filename, "...", 40)
                self.after(0, self.update_file_header, index+1, len(file_paths), display_name)

                # Determine output path
                output_dir = self.output_dir or os.path.dirname(pdf_path)

                # Check if we have a custom directory for this file
                if self.alternative_dir_for_all is not None:
                    output_dir = self.alternative_dir_for_all
                else:
                    # Check directory writability
                    writable, error_msg = is_directory_writable(output_dir)
                    if not writable:
                        response = self.prompt_alternative_directory(pdf_path, error_msg)
                        if response is None:  # User canceled
                            break
                        if response:  # User provided new directory
                            output_dir = response
                            self.alternative_dir_for_all = output_dir  # Apply to all subsequent
                        else:  # User chose to skip # Skip
                            permission_errors.append(pdf_path)
                            self.after(0, self.update_message, 
                                     f"⚠️ Skipped {filename}: {error_msg}", "error")
                            continue

                output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.docx"
                output_path = os.path.join(output_dir, output_filename)

                # Skip existing files if not overwriting
                if not self.overwrite_files and os.path.exists(output_path):
                    skipped_files.append(output_path)
                    continue

                # Process file with the determined output directory and cancellation support
                language = self.lang_var.get()
                output_format = self.format_var.get()  # Get selected format
                final_path = ocr_pdf(
                    pdf_path,
                    output_dir,
                    language,
                    lambda curr, total, name=filename: self.update_progress(curr, total, name) or (self.cancelled and 
                    self._handle_cancellation_during_processing(name)),
                    output_format  # Pass format to OCR function
                )
                self.ocr_output_files.append(final_path)  # Track output file
                
                processed_count += 1
                self.after(0, self.update_total_progress, processed_count, total_files)

                # After successful processing
                completion_text = (
                    f"Completed: {truncate_filename(filename, '...', 40)}\n"
                    f"📁 Saved to: {os.path.dirname(final_path)}"                    
                )
                self.after(0, self._update_message_internal, completion_text, "success")

                # Clear progress line positions
                self.current_progress_start = None
                self.current_progress_end = None

        except RuntimeError as e:
            if "cancelled" in str(e).lower():
                self.after(0, self.update_message, f"⏹ {str(e)}", "warning")
            else:
                raise

        except Exception as e:
            if "cancelled" in str(e).lower():
                self.after(0, self.update_message, 
                          f"⏹ {str(e)}", "warning")
            self.after(0, self.update_message, f"Error: {str(e)}", "error")

        finally:
            was_cancelled = self.finalize_ocr_cleanup()
            elapsed = datetime.timedelta(seconds=int(time.time()-start_time))
            
            # Show appropriate completion message
            if was_cancelled:
                self.after(0, messagebox.showinfo, "OCR Cancelled",
                        f"Processed {processed_count} files\n"
                        f"Skipped {len(file_paths) - processed_count} files\n"
                        f"Time elapsed: {elapsed}")
            else:
                # Only show completion message if not cancelled
                self.after(0, messagebox.showinfo, "OCR Complete", 
                    f"Processed {processed_count}/{total_files} files\n"
                    f"Skipped {len(skipped_files)} existing files\n"
                    f"Skipped {len(permission_errors)} files due to permission issues\n"
                    f"Time elapsed: {elapsed}")

            # Common cleanup
            self.run_button.config(state="normal")            
            
            # Show skipped files warnings
            if skipped_files:
                self.after(0, self.show_skipped_files_warning, skipped_files)
            if permission_errors:
                self.after(0, self.show_permission_errors_warning, permission_errors)

            # Initialize PrintManager if we have results
            if not was_cancelled and self.ocr_output_files:
                self.print_button.config(state="normal", style='Ready.TButton')
                self.open_folder_btn.config(state="normal", style='Ready.TButton')

            # Reset progress bars and labels
            self.per_file_progress_bar["value"] = 0
            self.total_progress_bar["value"] = 0
            self.per_file_progress_text.config(text=f"All done")
            self.total_progress_text.config(text=f"All done")
            self.per_file_percentage_label.config(text="0%", style = "")
            self.total_percentage_label.config(text="0%", style = "")
            
            self.selected_files_label.config(
                text=f"{processed_count} PDFs processed. Select new files to continue.")
            
    def _handle_cancellation_during_processing(self, filename):
        """Handle cancellation requests during active OCR processing"""
        self.cancelled = True
        raise RuntimeError(f"Processing of {filename} cancelled by user")
                
    def prompt_alternative_directory(self, pdf_path, error_msg):
        """Prompt user for alternative directory and return selected path"""
        result = []
        response = messagebox.askyesnocancel(
            "Directory Not Writable",
            f"Cannot write to original directory:\n{os.path.dirname(pdf_path)}\n\n"
            f"Error: {error_msg}\n\n"
            "Would you like to choose a different directory for this file?",
            detail="Click Yes to choose a different directory\n"
                   "No to skip this file\n"
                   "Cancel to abort all processing",
            icon="warning"
        )
        
        if response is None:  # Cancel
            return None
        if not response:  # No
            return False
        
        # User wants to choose directory - open dialog
        folder_path = filedialog.askdirectory(
            title=f"Select Output Folder for {os.path.basename(pdf_path)}",
            mustexist=True
        )
        if not folder_path:
            return False
        
        # Verify writability of new directory
        writable, error_msg = is_directory_writable(folder_path)
        if not writable:
            messagebox.showerror(
                "Directory Not Writable",
                f"Selected directory is not writable:\n{error_msg}"
            )
            return self.prompt_alternative_directory(pdf_path, error_msg)  # Recursive retry
        
        return folder_path

    def show_permission_errors_warning(self, permission_errors):
        """Show warning about files skipped due to permission issues"""
        warning_text = "\n⚠️ Permission Issues:\n" + "\n".join(
            f"• {os.path.basename(f)}" for f in permission_errors[:5]
        )
        if len(permission_errors) > 5:
            warning_text += f"\n...and {len(permission_errors)-5} more"
        self._update_message_with_tag(warning_text + "\n", "warning")

    def _update_message_with_tag(self, text, tag):
        """Thread-safe message update with tag formatting"""
        self.message_text.config(state="normal")
        
        # Configure tags for different message types
        self.message_text.tag_configure("file_header", foreground="#2c7fb8", font=("Segoe UI", 10, "bold"))
        self.message_text.tag_configure("progress", foreground="#636363", font=("Segoe UI", 9))
        self.message_text.tag_configure("success", foreground="#2ca02c", font=("Segoe UI", 10))
        
        # Insert message with appropriate tag
        self.message_text.insert("end", text, tag)
        
        # Auto-scroll and maintain history
        self.message_text.see("end")
        self.message_text.config(state="disabled")
        
        # Cleanup old messages after 1000 lines
        if int(self.message_text.index('end-1c').split('.')[0]) > 1000:
            self.message_text.delete(1.0, "end -800 lines")

    # Modified show_skipped_files_warning to maintain message flow
    def show_skipped_files_warning(self, skipped_files):
        warning_text = "\n⚠️ Skipped files:\n" + "\n".join(
            f"• {os.path.basename(f)}" for f in skipped_files[:5]
        )
        if len(skipped_files) > 5:
            warning_text += f"\n...and {len(skipped_files)-5} more"
        self._update_message_with_tag(warning_text + "\n", "warning")    

    def update_file_header(self, current_file: int, total_files: int, display_name: str):
        self.processing_timers['current_file_start'] = time.time()
        self.processing_timers['current_file_paused'] = 0.0

        self.selected_files_label.config(text=f"Progress: {current_file}/{total_files}: {display_name}")
        """Update file processing header and initialize progress line"""
        header_text = f"\n{current_file}/{total_files} {display_name}"
        self._update_message_internal(header_text, "file_header")
        
        # Initialize progress line position
        self.message_text.config(state="normal")
        self.current_progress_start = self.message_text.index("end-1c")
        self.message_text.insert("end", "\n", "progress")  # Empty line placeholder
        self.current_progress_end = self.message_text.index("end-1c")
        self.message_text.config(state="disabled")

    def show_overwrite_warning(self, existing_files):
        """Custom dialog with renamed buttons"""
        dialog = tk.Toplevel(self)
        dialog.title("Existing Files Found")
        dialog.transient(self)
        dialog.grab_set()

        # Create message content
        max_display = 10
        file_list = "\n".join(f"• {os.path.basename(f)}" for f in existing_files[:max_display])
        if len(existing_files) > max_display:
            remaining = len(existing_files) - max_display
            file_list += f"\n...and {remaining} more file{'s' if remaining > 1 else ''}"

        msg = ttk.Label(dialog, text=f"Found {len(existing_files)} existing files:\n\n{file_list}")
        msg.pack(padx=20, pady=10)

        # Response handling
        response = None
        
        def on_button_click(value):
            nonlocal response
            response = value
            dialog.destroy()

        # Button frame
        btn_frame = ttk.Frame(dialog)
        ttk.Button(btn_frame, text="Overwrite all files", command=lambda: on_button_click(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Skip existing files", command=lambda: on_button_click(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=lambda: on_button_click(None)).pack(side=tk.LEFT, padx=5)
        btn_frame.pack(pady=10)
        
        self.wait_window(dialog)
        return response

    # Updated update_progress with ETR
    def update_progress(self, current_page: int, total_pages: int, current_file: str):
        """Update progress display with ETR calculations"""
        # Calculate percentages and ETRs first
        percent = int((current_page / total_pages) * 100) if total_pages > 0 else 0
        file_elapsed = time.time() - self.processing_timers['current_file_start'] - self.processing_timers['current_file_paused']

        file_etr = self.calculate_etr(current_page, total_pages, file_elapsed)
        
        # Calculate total ETR
        total_processed = self.total_progress_bar['value']
        total_files = self.total_progress_bar['maximum']
        total_elapsed = self.get_elapsed_time()
        total_etr = self.calculate_etr(total_processed, total_files, total_elapsed)
        #total_percent = int((total_processed / total_files) * 100) if total_files > 0 else 0        

        # Update labels with captured values        
        self.after(0, lambda fe=file_etr: self.per_file_progress_text.config(
            text=f"{truncate_filename(current_file, '...', 30) } | ETR: {fe}"))
        self.after(0, lambda p=percent: self.per_file_percentage_label.config(style='Orange.TLabel', text=f"{p}%"))        
        
        # Update total progress text
        #total_percent = int((self.total_progress_bar['value']/self.total_progress_bar['maximum'])*100)
        self.after(0, lambda te=total_etr: self.total_progress_text.config(style='Blue.TLabel',
        text=f"Total Progress | ETA: {te}"))
        
        
        # Update progress text
        percent = int((current_page / total_pages) * 100) if total_pages > 0 else 0
        progress_text = (f"Page {current_page}/{total_pages} ({percent}%) - {truncate_filename(current_file, '...', 40)}\n"
                        f"File ETR: {file_etr} | Total ETR: {total_etr}")        
        
        # Update progress bar and text
        self.after(0, lambda: self.per_file_progress_bar.configure(value=percent))        
        
        # Update progress line in text area
        self.after(0, self._update_progress_text, progress_text)
        
        # Check for pause request
        if self.pause_event.is_set():
            self.after(0, self.update_message, "⏸ Processing paused. Click Resume to continue...", "warning")
            self.resume_event.wait()
            self.resume_event.clear()
            self.pause_event.clear()
            self.after(0, self.update_message, "▶ Processing resumed...", "success")
        
    def _update_progress_text(self, progress_text):
        """Replace progress line text"""
        if not self.current_progress_start or not self.current_progress_end:
            return

        self.message_text.config(state="normal")
        
        # Delete existing progress line
        self.message_text.delete(self.current_progress_start, self.current_progress_end)
        
        # Insert new progress text
        self.message_text.insert(self.current_progress_start, f"{progress_text}\n", "progress")
        
        # Update end position
        self.current_progress_end = self.message_text.index(
            f"{self.current_progress_start} + {len(progress_text)+1} chars"
        )
        
        self.message_text.see("end")
        self.message_text.config(state="disabled")    

    def update_total_progress(self, value, total_files):
        self.total_progress_bar["value"] = value
        total_percent = int((value / total_files) * 100) if total_files > 0 else 0
        self.total_progress_text.config(text=f"Total progress: {value}/{total_files} ({total_percent}%)")
        self.total_progress_bar.update_idletasks()  # Consistent with other updates
        self.after(0, lambda tp=total_percent: self.total_percentage_label.config(style='Blue.TLabel', text=f"{tp}%"))