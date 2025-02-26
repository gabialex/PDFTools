# logic/compression.py
import os
import logging
from pikepdf import Pdf, PasswordError, ObjectStreamMode, Name 

# Configure logging
logging.basicConfig(
    filename="compression_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def find_pdfs(directory):
    """Recursively find all PDF files in a directory."""
    pdf_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))
        logging.info(f"Found {len(pdf_files)} PDFs in {directory}")
    except Exception as e:
        logging.error(f"Error scanning {directory}: {str(e)}")
    return pdf_files

def compress_pdf(input_path, output_path, level="medium", overwrite=False):
    """
    Compress a PDF file with safety checks and image optimization.
    Returns: (success: bool, compressed_size: int | error_message: str)
    """
    try:
        # --- Input Validation ---
        if not os.path.exists(input_path):
            logging.error(f"Input file not found: {input_path}")
            return False, "Input file not found."
        
        original_size = os.path.getsize(input_path)
        if original_size == 0:
            logging.error(f"Empty file skipped: {input_path}")
            return False, "File is empty"

        # --- PDF Processing ---
        with Pdf.open(input_path, allow_overwriting_input=overwrite) as pdf:
            # Remove unused resources
            pdf.remove_unreferenced_resources()
            
            # --- Image Compression (JPEG at 50% quality) ---
            for page in pdf.pages:
                for name, image in page.images.items():
                    filters = image.Filter
                    if filters is None or (isinstance(filters, (list, str)) and "/DCTDecode" not in filters):
                        image.compress(Name.DeviceRGB, quality=50)
            
            # --- Compression Level Settings ---
            compress_streams = True
            object_stream_mode = ObjectStreamMode.preserve
            
            if level == "high":
                object_stream_mode = ObjectStreamMode.generate
            elif level == "low":
                compress_streams = False

            # Save with settings
            pdf.save(
                output_path,
                compress_streams=compress_streams,
                object_stream_mode=object_stream_mode
            )

        # --- Post-Compression Validation ---
        compressed_size = os.path.getsize(output_path)
        if compressed_size >= original_size:
             compression_ratio = 0.0  # Treat as 0% reduction
             logging.warning(f"Compression ineffective: {input_path} (larger than original)")
        else:
            compression_ratio = ((original_size - compressed_size) / original_size) * 100
        logging.info(
            f"Success: {input_path} | "
            f"Original: {original_size} B | "
            f"Compressed: {compressed_size} B | "
            f"Ratio: {compression_ratio:.2f}%"
        )
        return True, compressed_size

    except PasswordError:
        logging.error(f"Encrypted PDF skipped: {input_path}")
        return False, "PDF is password-protected"
    except Exception as e:
        logging.error(f"Error in {input_path}: {str(e)}", exc_info=True)
        return False, str(e)