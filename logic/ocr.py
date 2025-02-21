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

    # Open the PDF
    doc = fitz.open(input_path)
    output_text = ""
    total_pages = len(doc)  # Get the total number of pages

    # Ensure progress starts at 0% when we begin processing a new PDF
    if progress_callback:
        progress_callback(0, 0)

    # Loop through the pages and extract images for OCR
    for page_num in range(total_pages):
        page = doc.load_page(page_num)

        # Render the page as a pixmap (image)
        pix = page.get_pixmap()

        # Convert the pixmap to an image using Pillow
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Perform OCR on the image using pytesseract
        text = pytesseract.image_to_string(img, lang=language)
        output_text += text

        # Calculate progress percentage and update the progress bar
        progress_value = page_num + 1
        progress_percent = int((progress_value / total_pages) * 100)
        
        # Logging for debugging
        print(f"Page {page_num + 1}/{total_pages} processed. Progress: {progress_percent}%")

        if progress_callback:
            progress_callback(progress_value, progress_percent)

    # Save the output text to a file
    output_path = os.path.join(output_dir, f"OCR_{os.path.basename(input_path)}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    doc.close()

    # Ensure progress is 100% after the last page
    if progress_callback:
        progress_callback(total_pages, 100)

    return output_path

