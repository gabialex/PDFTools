#gui/ocr_ops.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from gui.utils import ToolTip
from logic.ocr import ocr_pdf
import os
import tkinter.messagebox as messagebox
import threading

class OCROpsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_variables()
        self.font = ("Segoe UI", 10)
        self.overwrite_files = False  # Flag for overwrite decision

    def setup_variables(self):
        """Initialize OCR variables."""
        self.input_pdf = ""
        self.lang_var = tk.StringVar(value="ron")

    def setup_ocr_ui(self, parent):
        """Set up the OCR UI components with better alignment."""
        self.ocr_frame = ttk.Frame(parent)
        self.ocr_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI Components
        self.setup_ocr_header()
        self.setup_ocr_file_selection()
        self.setup_ocr_language_selection()
        self.setup_action_buttons()

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.ocr_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=5, column=0, columnspan=3, pady=10)

        # Percentage Label
        self.percent_label = ttk.Label(self.ocr_frame, text="0%")
        self.percent_label.grid(row=5, column=1, pady=5, padx=5, sticky='e')

        # Selected files label
        self.selected_files_label = ttk.Label(self.ocr_frame, text="No files selected yet")
        self.selected_files_label.grid(row=7, column=0, columnspan=3, pady=5)

        # Scrollable Text Widget for displaying messages
        self.message_text = tk.Text(self.ocr_frame, height=34, width=45, wrap="word", state="disabled")
        self.message_text.grid(row=9, column=0, columnspan=3, pady=5)

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(self.ocr_frame, orient="vertical", command=self.message_text.yview)
        scrollbar.grid(row=9, column=3, sticky="ns")
        self.message_text.config(yscrollcommand=scrollbar.set)
        

    # --------------------- UI Setup Methods ---------------------
    def setup_ocr_header(self):
        self.ocr_label = ttk.Label(self.ocr_frame, text="OCR PDF", style="Blue.TLabel")
        self.ocr_label.grid(row=0, column=0, columnspan=3, pady=5, sticky="n")

    def setup_ocr_file_selection(self):
        """File selection for input PDF or directory for batch processing."""
        
        # Button for selecting folder        
        folder_button = ttk.Button(self.ocr_frame, text="Select Folder", command=self.select_folder)
        folder_button.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        # Button for selecting individual PDF
        browse_button = ttk.Button(self.ocr_frame, text="Select files", command=self.select_pdf)
        browse_button.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Entry box to show the selected PDF
        self.input_entry = ttk.Entry(self.ocr_frame, width=55)
        self.input_entry.grid(row=2, columnspan=2, padx=18, pady=5)
        
        ToolTip(self.input_entry, "Path to the PDF file or folder", delay=500)
        ToolTip(browse_button, "Browse and select the PDF file", delay=500)
        ToolTip(folder_button, "Browse and select a folder for batch OCR", delay=500)

    def select_folder(self):
        """Open folder dialog and include subfolders"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder_path)
            
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

    def check_existing_outputs(self):
        """Check for existing OCR result files"""
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

    def update_file_display(self):
        """Update file display with folder structure"""
        self.message_text.config(state="normal")
        self.message_text.delete(1.0, tk.END)
        
        if not self.file_paths:
            self.selected_files_label.config(text="No files selected yet")
            self.message_text.config(state="disabled")
            return
        
        max_display = 10  # Number of files to show before truncating
        common_root = os.path.commonpath(self.file_paths)
        
        # Display folder structure
        self.message_text.insert(tk.END, f"Selected folder: {common_root}\n\n")
        self.message_text.insert(tk.END, "Files found:\n")
        
        # Organize files by their relative path
        file_tree = {}
        for fp in self.file_paths:
            rel_path = os.path.relpath(fp, common_root)
            parts = os.path.split(rel_path)
            
            if len(parts) > 1:  # File is in a subfolder
                folder = parts[0]
                filename = parts[1]
                if folder not in file_tree:
                    file_tree[folder] = []
                file_tree[folder].append(filename)
            else:  # File is in root folder
                if "_root" not in file_tree:
                    file_tree["_root"] = []
                file_tree["_root"].append(rel_path)
        
        # Display the file tree
        displayed = 0
        for folder, files in file_tree.items():
            if folder != "_root":
                self.message_text.insert(tk.END, f"\n📁 {folder}/\n")
            
            for i, file in enumerate(sorted(files)):
                if displayed >= max_display:
                    remaining = len(self.file_paths) - max_display
                    self.message_text.insert(tk.END, f"\n...and {remaining} more files")
                    break
                
                display_text = f"  • {file}" if folder != "_root" else f"• {file}"
                self.message_text.insert(tk.END, f"{display_text}\n")
                displayed += 1
            
            if displayed >= max_display:
                break
        
        self.message_text.config(state="disabled")
        self.selected_files_label.config(
            text=f"{len(self.file_paths)} file{'s' if len(self.file_paths) > 1 else ''} found in folder and subfolders"
        )

    def setup_ocr_language_selection(self):
        """Language selection for OCR."""
        ttk.Label(self.ocr_frame, text="OCR Language:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        
        lang_combo = ttk.Combobox(self.ocr_frame, textvariable=self.lang_var, values=["ron", "eng", "fra", "deu", "spa"], width=5)
        lang_combo.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        ToolTip(lang_combo, "Language for OCR (Tesseract)", delay=500)

    def setup_action_buttons(self):
        """Run OCR button."""
        self.run_btn_frame = ttk.Frame(self.ocr_frame)
        self.run_btn_frame.grid(row=8, column=0, columnspan=3, pady=10)

        run_button = ttk.Button(self.run_btn_frame, text="Run OCR", command=self.run_ocr)
        run_button.pack(padx=5, pady=5)
        
        ToolTip(run_button, "Extract text from PDF using OCR", delay=500)

    # --------------------- Functionality Methods ---------------------
    def select_pdf(self):
        """Open file dialog for multiple PDF selection."""
        filepaths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if filepaths:
            # Display selected files in the entry box (not used for processing)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "; ".join(filepaths))  # Just for showing in the entry

            # Clear the message display area before showing new file names
            self.message_text.config(state="normal")  # Allow editing
            self.message_text.delete(1.0, tk.END)  # Clear the text area

            # Extract the folder path and file names
            folder_path = os.path.dirname(filepaths[0])
            file_names = [os.path.basename(file) for file in filepaths]

            # Add the folder path and file names to the text area
            self.message_text.insert(tk.END, f"Selected files for OCR:\n{folder_path}\n")
            for index, file_name in enumerate(file_names, start=1):
                self.message_text.insert(tk.END, f"{index}. {file_name}\n")
            
            self.message_text.config(state="disabled")  # Prevent further editing

            # Store the actual file paths for processing
            self.file_paths = filepaths

            # Update the label to show the number of selected files
            num_files = len(filepaths)
            self.selected_files_label.config(text=f"{num_files} file{'s' if num_files > 1 else ''} selected.")


    def update_message(self, message, message_type="info"):
        """Helper function to update the message in the text widget."""
        self.message_text.config(state="normal")
        
        # Set message type (you can style these messages as needed)
        if message_type == "success":
            self.message_text.insert(tk.END, f"{message}\n", "success")
        elif message_type == "warning":
            self.message_text.insert(tk.END, f"Warning: {message}\n", "warning")
        elif message_type == "error":
            self.message_text.insert(tk.END, f"Error: {message}\n", "error")
        
        self.message_text.config(state="disabled")
        self.message_text.yview(tk.END)  # Scroll to the latest message 

    def run_ocr(self):
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
        """Modified process_files with existing file check"""
        total_files = len(file_paths)
        self.progress_bar["maximum"] = total_files
        self.progress_bar["value"] = 0

        # First check for existing OCR files
        existing_files = []
        for pdf_path in file_paths:
            output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf.txt"
            output_path = os.path.join(os.path.dirname(pdf_path), output_filename)
            if os.path.exists(output_path):
                existing_files.append(output_path)

        # Show warning if any existing files found
        if existing_files:
            if not self.show_overwrite_warning(existing_files):
                self.update_message("OCR processing canceled by user", "warning")
                return

        # Process files with overwrite flag
        try:
            processed_count = 0
            for index, pdf_path in enumerate(file_paths):
                output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf.txt"
                output_path = os.path.join(os.path.dirname(pdf_path), output_filename)

                # Skip existing files if not overwriting
                if not self.overwrite_files and os.path.exists(output_path):
                    self.after(0, self.update_message, 
                              f"\nSkipped existing file: {output_filename}\n", "warning")
                    continue

                # Actual processing
                self.selected_files_label.config(text=f"Processing {os.path.basename(pdf_path)}...")
                final_path = ocr_pdf(pdf_path, os.path.dirname(output_path), language)

                processed_count += 1
                percent = int((processed_count / total_files) * 100)
                self.after(0, self.update_progress, processed_count, percent)
                self.after(0, self.update_message, 
                          f"Processed: {os.path.basename(pdf_path)}\nSaved to: {final_path}", "success")

        except Exception as e:
            self.after(0, self.update_message, f"Error: {str(e)}", "error")
        
        self.selected_files_label.config(text="OCR process complete")

    def process_files(self, file_paths, language):
        total_files = len(file_paths)
        self.progress_bar["maximum"] = total_files
        self.progress_bar["value"] = 0

        # First check for existing OCR files
        existing_files = []
        for pdf_path in file_paths:
            output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf.txt"
            output_path = os.path.join(os.path.dirname(pdf_path), output_filename)
            if os.path.exists(output_path):
                existing_files.append(output_path)

        # Show warning if any existing files found
        if existing_files:
            response = self.show_overwrite_warning(existing_files)
            if response is None:  # Cancel
                self.update_message("OCR processing canceled by user", "warning")
                return
            self.overwrite_files = response  # True=Overwrite, False=Skip

        # Process files with overwrite flag
        try:
            processed_count = 0
            for index, pdf_path in enumerate(file_paths):
                output_filename = f"OCR_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf.txt"
                output_path = os.path.join(os.path.dirname(pdf_path), output_filename)

                # Skip existing files if not overwriting
                if not self.overwrite_files and os.path.exists(output_path):
                    self.after(0, self.update_message, 
                              f"\nSkipped existing file: {output_filename}\n", "warning")
                    continue

                # Actual processing
                self.selected_files_label.config(text=f"Processing {os.path.basename(pdf_path)}...")
                final_path = ocr_pdf(pdf_path, os.path.dirname(output_path), language)

                processed_count += 1
                percent = int((processed_count / total_files) * 100)
                self.after(0, self.update_progress, processed_count, percent)
                self.after(0, self.update_message, 
                          f"\nProcessed: {os.path.basename(pdf_path)}\nSaved to: {final_path}", "success")

        except Exception as e:
            self.after(0, self.update_message, f"Error: {str(e)}", "error")
        
        self.selected_files_label.config(text="OCR process complete")

    def show_overwrite_warning(self, existing_files):
        """Custom dialog with renamed buttons"""
        dialog = tk.Toplevel(self)
        dialog.title("Existing Files Found")
        dialog.transient(self)  # Set to main window
        dialog.grab_set()  # Make dialog modal

        # Create message content
        max_display = 10
        file_list = "\n".join(f"• {os.path.basename(f)}" for f in existing_files[:max_display])
        if len(existing_files) > max_display:
            remaining = len(existing_files) - max_display
            file_list += f"\n...and {remaining} more file{'s' if remaining > 1 else ''}"

        msg = ttk.Label(dialog, text=f"Found {len(existing_files)} existing files:\n\n{file_list}")
        msg.pack(padx=20, pady=10)

        # Response variable: True=Overwrite, False=Skip, None=Cancel
        response = None

        # Custom buttons
        btn_frame = ttk.Frame(dialog)
        
        def set_response(value):
            nonlocal response
            response = value
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Overwrite", 
                command=lambda: set_response(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Skip", 
                command=lambda: set_response(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                command=lambda: set_response(None)).pack(side=tk.LEFT, padx=5)
        
        btn_frame.pack(pady=10)
        
        self.wait_window(dialog)
        return response
    
    def set_response(self, response, dialog):
        """Handle button clicks"""
        self.overwrite_response = response
        dialog.destroy()

    def update_progress(self, value, percent):
        """Update progress bar and percentage label"""
        self.progress_bar["value"] = value
        self.percent_label.config(text=f"{percent}%")