import fitz  # PyMuPDF
import os
from datetime import datetime

def ocr_pdf(input_path: str, output_dir: str, language: str = "eng") -> str:
    """OCR a PDF and save the result to a new file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input PDF {input_path} not found")

    doc = fitz.open(input_path)
    output_path = os.path.join(output_dir, f"OCR_{os.path.basename(input_path)}")

    for page in doc:
        page.get_text("ocr", language=language)  # OCR the page

    doc.save(output_path)
    doc.close()
    return output_path