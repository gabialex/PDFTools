# logic/ocr.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

# logic/ocr.py
def ocr_pdf(input_path: str, output_dir: str, language: str, progress_callback=None) -> str:
    """OCR a PDF and save the result to a new file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input PDF {input_path} not found")

    doc = fitz.open(input_path)
    output_text = ""
    total_pages = len(doc)

    # Initial callback with 0 pages processed
    if progress_callback:
        progress_callback(0, total_pages)  # current, total

    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=language)
        output_text += text

        # Update callback with current page +1 and total
        if progress_callback:
            progress_callback(page_num + 1, total_pages)

    output_path = os.path.join(output_dir, f"OCR_{os.path.basename(input_path)}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    doc.close()

    # Final completion update
    if progress_callback:
        progress_callback(total_pages, total_pages)

    return output_path
