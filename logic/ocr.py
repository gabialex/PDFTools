#logic/ocr.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

def ocr_pdf(input_path: str, output_dir: str, language: str = "eng") -> str:
    """OCR a PDF and save the result to a new file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input PDF {input_path} not found")

    # Open the PDF
    doc = fitz.open(input_path)
    output_text = ""

    # Loop through the pages and extract images for OCR
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Render the page as a pixmap (image)
        pix = page.get_pixmap()

        # Convert the pixmap to an image using Pillow
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Perform OCR on the image using pytesseract
        text = pytesseract.image_to_string(img, lang=language)
        output_text += text

    # Save the output text to a file
    output_path = os.path.join(output_dir, f"OCR_{os.path.basename(input_path)}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    doc.close()
    return output_path
