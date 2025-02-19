import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from gui.utils import ToolTip
from logic.ocr import ocr_pdf
import os
import tkinter.messagebox as messagebox

class OCROpsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_variables()
        self.font = ("Segoe UI", 10)

    def setup_variables(self):
        """Initialize OCR variables."""
        self.input_pdf = ""
        self.lang_var = tk.StringVar(value="eng")

    def setup_ocr_ui(self, parent):
        """Set up the OCR UI components with better alignment."""
        self.left_frame = ttk.Frame(parent)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # UI Components
        self.setup_ocr_header()
        self.setup_ocr_file_selection()
        self.setup_ocr_language_selection()
        self.setup_action_buttons()

    # --------------------- UI Setup Methods ---------------------
    def setup_ocr_header(self):
        self.ocr_label = ttk.Label(self.left_frame, text="OCR PDF", style="Blue.TLabel")
        self.ocr_label.grid(row=0, column=0, columnspan=3, pady=5, sticky="n")

    def setup_ocr_file_selection(self):
        """File selection for input PDF."""

        browse_button = ttk.Button(self.left_frame, text="Select PDF", command=self.select_pdf)
        browse_button.grid(row=1, column=1, padx=5, pady=5)        
        
        self.input_entry = ttk.Entry(self.left_frame, width=55)
        self.input_entry.grid(row=2, columnspan=3, padx=18, pady=5)       
        
        
        ToolTip(self.input_entry, "Path to the PDF file to OCR")
        ToolTip(browse_button, "Browse and select the PDF file", delay=500)

    def setup_ocr_language_selection(self):
        """Language selection for OCR."""
        ttk.Label(self.left_frame, text="OCR Language:").grid(row=3, column=1, padx=5, pady=5)
        
        lang_combo = ttk.Combobox(self.left_frame, textvariable=self.lang_var, values=["eng", "fra", "deu", "spa"], width=5)
        lang_combo.grid(row=4, column=1, padx=5, pady=5)
        
        ToolTip(lang_combo, "Language for OCR (Tesseract)", delay=500)

    def setup_action_buttons(self):
        """Run OCR button."""
        self.run_btn_frame = ttk.Frame(self.left_frame)
        self.run_btn_frame.grid(row=5, column=0, columnspan=3, pady=10)

        run_button = ttk.Button(self.run_btn_frame, text="Run OCR", command=self.run_ocr)
        run_button.pack(padx=5, pady=5)
        
        ToolTip(run_button, "Extract text from PDF using OCR", delay=500)

    # --------------------- Functionality Methods ---------------------
    def select_pdf(self):
        """Open file dialog for PDF selection."""
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filepath)

    def run_ocr(self):
        input_pdf = self.input_entry.get()
        language = self.lang_var.get()

        if not input_pdf:
            messagebox.showerror("Error", "No PDF selected!")
            return

        try:
            output_dir = os.path.dirname(input_pdf)
            output_path = ocr_pdf(input_pdf, output_dir, language)
            messagebox.showinfo("Success", f"OCR complete!\nSaved to: {output_path}")
        except Exception as e:
            messagebox.showerror("OCR Failed", str(e))
