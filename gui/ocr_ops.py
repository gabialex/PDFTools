#gui/ocr_ops.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from gui.utils import ToolTip
from logic.ocr import ocr_pdf
import os
import tkinter.messagebox as messagebox
import threading
import re
import platform
import subprocess
import time
import datetime

class OCROpsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_variables()
        self.font = ("Segoe UI", 10)
        self.overwrite_files = False  # Flag for overwrite decision
        self.last_output_dir = None
        self.page_progress_tag = "page_progress"

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
        self.setup_selected_label()        
        self.setup_action_buttons()
        self.setup_per_file_pb_frame_and_label()
        self.setup_total_files_pb_frame_and_label()
        self.setup_text_and_sb_frame()
        self.setup_open_folder_btn()        

    # --------------------- UI Setup Methods ---------------------

    def setup_ocr_header(self):
        self.ocr_label = ttk.Label(self.ocr_frame, text="OCR PDF Files", style="Blue.TLabel")
        self.ocr_label.pack(pady=3)

    def setup_ocr_file_selection(self): 
        """File selection for input PDF or directory for batch processing."""
        
        # Create a frame for the buttons
        button_frame = ttk.Frame(self.ocr_frame)
        button_frame.pack(pady=5)

        # Button for selecting folder        
        folder_button = ttk.Button(button_frame, text="Select Folder", command=self.select_folder)
        folder_button.pack(side="left", padx=5, pady=5)

        # Button for selecting individual PDF
        browse_button = ttk.Button(button_frame, text="Select Files", command=self.select_pdf)
        browse_button.pack(side="left", padx=5, pady=5)               

        # Tooltips for user guidance        
        ToolTip(browse_button, "Browse and select the PDF file", delay=500)
        ToolTip(folder_button, "Browse and select a folder for batch OCR", delay=500)

    def setup_selected_label(self):
        # Selected files label
        self.selected_files_label = ttk.Label(self.ocr_frame, text="No files selected yet")
        self.selected_files_label.pack(pady=5)        

    def setup_ocr_language_selection(self):
        """Language selection for OCR."""
        lang_frame = ttk.Frame(self.ocr_frame)
        lang_frame.pack(pady=5)
        
        ttk.Label(lang_frame, text="Select OCR Language:").pack(side="left", padx=5)

        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=["ron", "eng", "fra", "deu", "spa"], width=5)
        lang_combo.pack(side="left", padx=5)

        ToolTip(lang_combo, "Language for OCR (Tesseract)", delay=500)

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
        """Check for existing OCR result files."""
        existing_files = []
        for pdf_path in self.file_paths:
            output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf.txt"
            output_path = os.path.join(os.path.dirname(pdf_path), output_filename)
            if os.path.exists(output_path):
                existing_files.append(output_path)

        if existing_files:
            response = self.show_overwrite_warning(existing_files)
            if response is None:  # Cancel
                self.file_paths = []
                return
            elif not response:  # Skip existing
                # Filter out files with existing outputs
                self.file_paths = [
                    fp for fp in self.file_paths
                    if not os.path.exists(
                        os.path.join(os.path.dirname(fp),
                        f"OCR_{os.path.splitext(os.path.basename(fp))[0]}.pdf.txt")
                    )]
            # Store the overwrite decision
            self.overwrite_files = response

        # Check if Run OCR button should be enabled after handling overwrite
        self.check_run_button_state()

    def setup_per_file_pb_frame_and_label(self):
        per_file_pb_frame = ttk.Frame(self.ocr_frame)
        per_file_pb_frame.pack(fill="both", pady=0, padx=5)
        # Text Label for PB1 (Progress text overlay)
        self.per_file_progress_text = ttk.Label(per_file_pb_frame, text="Progress for individual files 0%", style="Blue.TLabel")
        self.per_file_progress_text.pack(pady=0)

        # Progress Bar for File Completion (Per-File)
        self.per_file_progress_bar = ttk.Progressbar(per_file_pb_frame, orient="horizontal", length=360, mode="determinate")
        self.per_file_progress_bar.pack(pady=0)

    def setup_total_files_pb_frame_and_label(self):
        total_progress_pb_frame = ttk.Frame(self.ocr_frame)
        total_progress_pb_frame.pack(fill="both", pady=0, padx=5)
        # Text Label for PB2 (Progress text overlay)
        self.total_progress_text = ttk.Label(total_progress_pb_frame, text="Total progress across all files 0%", style="Blue.TLabel")
        self.total_progress_text.pack(pady=0)

        # Progress Bar for Total Completion (Across All Files)
        self.total_progress_bar = ttk.Progressbar(total_progress_pb_frame, orient="horizontal", length=360, mode='determinate')
        self.total_progress_bar.pack(pady=0, padx=5)

    def setup_text_and_sb_frame(self):
        # Create a frame to hold the text widget and scrollbar
        text_frame = ttk.Frame(self.ocr_frame)
        text_frame.pack(fill="both", expand=True, pady=15, padx=10)

        # Scrollable Text Widget for displaying messages
        self.message_text = tk.Text(text_frame, height=30, width=46, wrap="word", state="disabled")
        self.message_text.pack(side="left", fill="both", pady=1, expand=True)

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.message_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.message_text.config(yscrollcommand=scrollbar.set)

    def setup_open_folder_btn(self):
        # Add Open Folder button under the text area
        self.open_folder_btn = ttk.Button(
            self.ocr_frame,
            text="Open Output Folder",
            command=self.open_output_folder
        )
        self.open_folder_btn.pack(pady=5)

    # --------------------- Functionality Methods ---------------------

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

    def setup_action_buttons(self):
        """Run OCR button setup with an initial disabled state."""
        self.run_btn_frame = ttk.Frame(self.ocr_frame)
        self.run_btn_frame.pack(pady=10)

        # Style for blue button
        style = ttk.Style()
        style.configure("Blue.TButton", foreground="blue")

        # Initialize button in disabled state
        self.run_button = ttk.Button(
            self.run_btn_frame,
            text="Run OCR",
            command=self.run_ocr,
            state="disabled"  # Button is disabled initially
        )
        self.run_button.pack(padx=5, pady=5)
        ToolTip(self.run_button, "Extract text from PDF using OCR", delay=500)

    def check_run_button_state(self):
        """Enable the Run OCR button and change its color if files are selected."""
        if hasattr(self, 'file_paths') and self.file_paths:
            # Enable the button and apply the blue color style
            style = ttk.Style()
            style.configure("Blue.TButton", foreground="red", background="lightgrey")
            self.run_button.config(state="normal", style="Blue.TButton")
            
        else:
            # Disable the button if no files are selected
            self.run_button.config(state="disabled", style="")

    def open_output_folder(self):
        """Open the output folder in system file explorer"""
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            try:
                if platform.system() == "Windows":
                    os.startfile(self.last_output_dir)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", self.last_output_dir])
                else:
                    subprocess.run(["xdg-open", self.last_output_dir])
            except Exception as e:
                self.update_message(f"Could not open folder: {str(e)}", "error")
        else:
            self.update_message("No output folder available", "warning")
    
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
        """Helper function to update the message in the text widget."""
        if int(self.message_text.index('end-1c').split('.')[0]) > 500:
            self.message_text.delete(1.0, "end -500 lines")

        self.message_text.config(state="normal")
        
        # Configure tags for different message types
        self.message_text.tag_configure("file_header", foreground="#FF4500", font=("Segoe UI", 8, "bold"))
        self.message_text.tag_configure("success", foreground="black", font=("Segoe UI", 10))
        self.message_text.tag_configure("warning", foreground="orange", font=("Segoe UI", 10))
        self.message_text.tag_configure("error", foreground="red", font=("Segoe UI", 10))
        
        # Insert message with appropriate formatting
        if message_type == "file_header":
            self.message_text.insert("end", f"\n{message}\n", message_type)
        else:
            self.message_text.insert("end", f"{message}\n", message_type)
        
        self.message_text.config(state="disabled")
        self.message_text.see("end")  # Scroll to the latest message

    def run_ocr(self):
        # Disable the Run OCR button and show busy cursor
        self.run_button.config(state="disabled")
        self.ocr_frame.config(cursor="watch")  # Change cursor to busy

        # Get the selected language
        language = self.lang_var.get()

        # Check if files were selected
        if not hasattr(self, 'file_paths') or not self.file_paths:
            self.update_message("Error: No PDF or folder selected!", "error")
            return

        # Start the OCR processing in a separate thread
        thread = threading.Thread(target=self.process_files, args=(self.file_paths, language))
        thread.start()    

    def process_files(self, file_paths, language):
        start_time = time.time()
        total_files = len(file_paths)
        
        # Initialize progress bars
        self.after(0, self.per_file_progress_bar.config, {"maximum": 100, "value": 0})
        self.per_file_progress_bar["value"] = 0
        self.per_file_progress_bar.config(style='Compress.Horizontal.TProgressbar')
        self.total_progress_bar["maximum"] = total_files
        self.total_progress_bar["value"] = 0
        self.total_progress_bar.config(style='Normal.Horizontal.TProgressbar')

        try:
            processed_count = 0

            for index, pdf_path in enumerate(file_paths):
                # At the start of processing, remove any progress tracking
                if hasattr(self, 'progress_line_start'):
                    del self.progress_line_start
                if hasattr(self, 'file_header_start'):
                    del self.file_header_start
                    del self.file_header_end
                    
                # Store the output directory
                self.last_output_dir = os.path.dirname(pdf_path)
                output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf.txt"
                output_path = os.path.join(os.path.dirname(pdf_path), output_filename)

                # Skip existing files if not overwriting
                if not self.overwrite_files and os.path.exists(output_path):
                    self.after(0, self.update_message, 
                            f"\nSkipped existing file: {output_filename}\n", "warning")
                    continue

                # Get file info
                filename = os.path.basename(pdf_path)
                display_name = filename if len(filename) <= 30 else f"{filename[:27]}..."
                

                # Update file processing header
                self.after(0, self.update_file_header,
                        index + 1, total_files, display_name)

                # OCR processing with page number callback
                final_path = ocr_pdf(
                    pdf_path,
                    os.path.dirname(pdf_path),
                    language,
                    lambda curr, total, name=filename: self.update_progress(curr, total, name)
                )

                # Update completion status
                processed_count += 1
                self.after(0, self.update_message,
                        f"\nCompleted: {filename}\nSaved to: {final_path}",
                        "success")
                
                # Update total progress
                self.after(0, self.update_total_progress, processed_count, total_files)

        except Exception as e:
            self.after(0, self.update_message, f"Error: {str(e)}", "error")        
        finally:
            # Final cleanup
            self.ocr_frame.config(cursor="")
            self.run_button.config(state="disabled", style="")            
            messagebox.showinfo("OCR Complete", 
                f"Processed {processed_count} files successfully!\n"
                f"Total time: {datetime.timedelta(seconds=int(time.time()-start_time))}"            
            )
            self.selected_files_label.config(text=f"{processed_count} PDFs processed successfully!\nSelect Folder or Select Files for another operation")

    def update_file_header(self, current_file: int, total_files: int, display_name: str):
        """Update the current file processing header in place"""
        self.message_text.config(state="normal")
        
        # Check if we have an existing header
        if hasattr(self, 'file_header_start'):
            # Delete only the header line
            self.message_text.delete(self.file_header_start, self.file_header_end)
        else:
            # First time - insert a new line and remember its position
            self.file_header_start = self.message_text.index("end-1c")
            self.message_text.insert("end", "\n")
            self.file_header_end = self.message_text.index("end-1c")
        
        # Insert updated header
        self.selected_files_label.config(text=f"PROGRESS: {current_file}/{total_files}: {display_name}")
        percent = int((current_file / total_files) * 100) if total_files > 0 else 0
        header_text = f"Processing file {current_file}/{total_files}: {display_name}"
        self.message_text.insert("end", header_text, "file_header")
        
        # Update header position markers
        self.file_header_start = self.message_text.index(f"end - {len(header_text) + 1}c")
        self.file_header_end = self.message_text.index("end-1c")
        
        self.message_text.config(state="disabled")
        self.message_text.see("end")

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

    def update_progress(self, current_page: int, total_pages: int, current_file: str):
        """Update progress display with live page numbers"""
        # Calculate percentage
        percent = int((current_page / total_pages) * 100) if total_pages > 0 else 0
        
        # Update progress bar
        self.per_file_progress_bar["value"] = percent
        
        # Update file name display
        display_name = (current_file if len(current_file) <= 30 
                    else f"{current_file[:27]}...")
        self.per_file_progress_text.config(
            text=f"Processing {display_name}: {percent}%"
        )
        
        # Update page numbers in text area (single line)
        self.message_text.config(state="normal")
        
        # Check if we have an existing progress line
        if hasattr(self, 'progress_line_start'):
            # Delete only the progress line
            self.message_text.delete(self.progress_line_start, "end-1c")
        else:
            # First time - insert a new line and remember its position
            self.progress_line_start = self.message_text.index("end-1c")
            self.message_text.insert("end", "\n")
        
        # Insert updated progress
        self.message_text.insert("end", f"\nPage {current_page}/{total_pages} processed: {percent}%", "progress", )
        
        # Keep view scrolled to bottom
        self.message_text.see("end")
        self.message_text.config(state="disabled")
        
        self.per_file_progress_bar.update_idletasks()

    def update_total_progress(self, value, total_files):
        self.total_progress_bar["value"] = value
        total_percent = int((value / total_files) * 100) if total_files > 0 else 0
        self.total_progress_text.config(text=f"Total progress: {value}/{total_files} ({total_percent}%)")
        self.total_progress_bar.update_idletasks()  # Consistent with other updates