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

        # Scrollable Text Widget for displaying messages
        self.message_text = tk.Text(self.ocr_frame, height=30, width=45, wrap="word", state="disabled")
        self.message_text.grid(row=6, column=0, columnspan=3, pady=5)

        # Adding a vertical scrollbar for the text area
        scrollbar = ttk.Scrollbar(self.ocr_frame, orient="vertical", command=self.message_text.yview)
        scrollbar.grid(row=6, column=3, sticky="ns")
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
        """Open folder dialog for selecting a folder of PDFs."""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder_path)


    def setup_ocr_language_selection(self):
        """Language selection for OCR."""
        ttk.Label(self.ocr_frame, text="OCR Language:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        
        lang_combo = ttk.Combobox(self.ocr_frame, textvariable=self.lang_var, values=["ron", "eng", "fra", "deu", "spa"], width=5)
        lang_combo.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        ToolTip(lang_combo, "Language for OCR (Tesseract)", delay=500)

    def setup_action_buttons(self):
        """Run OCR button."""
        self.run_btn_frame = ttk.Frame(self.ocr_frame)
        self.run_btn_frame.grid(row=5, column=0, columnspan=3, pady=10)

        run_button = ttk.Button(self.run_btn_frame, text="Run OCR", command=self.run_ocr)
        run_button.pack(padx=5, pady=5)
        
        ToolTip(run_button, "Extract text from PDF using OCR", delay=500)

    # --------------------- Functionality Methods ---------------------
    def select_pdf(self):
        """Open file dialog for selecting multiple PDFs."""
        filepaths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if filepaths:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "; ".join(filepaths))  # Display the selected files (or directories)

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
        input_path = self.input_entry.get()
        language = self.lang_var.get()

        if not input_path:
            self.update_message("Error: No PDF or folder selected!", "error")
            return

        # Split input_path into a list if multiple files were selected (separated by semicolons)
        file_paths = input_path.split(";")

        # Start the OCR processing in a separate thread
        thread = threading.Thread(target=self.process_files, args=(file_paths, language))
        thread.start()

    def process_files(self, file_paths, language):
        # Check if the selected path is a directory (process all PDFs in that folder)
        if os.path.isdir(file_paths[0]):  # If the first entry is a directory
            try:
                pdf_files = [f for f in os.listdir(file_paths[0]) if f.endswith('.pdf')]
                if not pdf_files:
                    self.after(0, self.update_message, "Warning: No PDF files found in the selected folder.", "warning")
                    return

                # Process each file one by one
                for pdf_file in pdf_files:
                    full_pdf_path = os.path.join(file_paths[0], pdf_file)
                    output_dir = os.path.dirname(full_pdf_path)

                    # Perform OCR and get the output path
                    output_path = ocr_pdf(full_pdf_path, output_dir, language)

                    # Update the message for the current file after it's processed
                    self.after(0, self.update_message, f"OCR complete for: {pdf_file}\nSaved to: {output_path}", "success")

            except Exception as e:
                self.after(0, self.update_message, f"Error: {str(e)}", "error")

        else:
            # Process individual files (if not a folder)
            try:
                for pdf_path in file_paths:
                    pdf_path = pdf_path.strip()  # Remove any extra spaces
                    if os.path.isfile(pdf_path) and pdf_path.endswith('.pdf'):
                        output_dir = os.path.dirname(pdf_path)
                        output_path = ocr_pdf(pdf_path, output_dir, language)

                        # Update the message for each processed file
                        self.after(0, self.update_message, f"OCR complete for: {os.path.basename(pdf_path)}\nSaved to: {output_path}", "success")
                    else:
                        self.after(0, self.update_message, f"Warning: Skipping invalid file: {pdf_path}", "warning")
            except Exception as e:
                self.after(0, self.update_message, f"Error: {str(e)}", "error")

         


