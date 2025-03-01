# logic/compression.py
import os
import logging
from pikepdf import Pdf, PasswordError, ObjectStreamMode, Name, PdfError
from typing import Tuple

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

def compress_pdf(input_path, output_path, level="medium", overwrite=False) -> Tuple[bool, str, int, int]:
    """
    Returns tuple:
    (success: bool, message: str, original_size: int, compressed_size: int)
    """
    original_size = 0
    compressed_size = 0
    
    try:
        # --- Input Validation ---
        if not os.path.exists(input_path):
            logging.error(f"Input file not found: {input_path}")
            return False, "Input file not found", 0, 0

        original_size = os.path.getsize(input_path)
        if original_size == 0:
            logging.error(f"Empty file skipped: {input_path}")
            return False, "File is empty", 0, 0

        # --- PDF Processing ---
        with Pdf.open(input_path, allow_overwriting_input=overwrite) as pdf:
            # Remove unused resources
            pdf.remove_unreferenced_resources()
            
            # --- Safer Image Compression ---
            for page in pdf.pages:
                for name, image in page.images.items():
                    try:
                        # Handle different filter types
                        filters = image.Filter
                        if isinstance(filters, Name):
                            filters = str(filters)
                        
                        # Only compress non-JPEG images
                        if not filters or ("/DCTDecode" not in str(filters)):
                            # Use lossless compression for non-JPEG
                            image.compress(Name.FlateDecode, quality=50)
                    except Exception as img_error:
                        logging.warning(
                            f"Could not compress image in {input_path}: {str(img_error)}"
                        )
                        continue  # Skip problematic images
            
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
        compression_ratio = max(0, ((original_size - compressed_size) / original_size) * 100)
        
        logging.info(f"Success: {input_path} | Ratio: {compression_ratio:.2f}%")
        return True, output_path, original_size, compressed_size

    except PdfError as pe:
        logging.error(f"PDF structure error: {input_path} - {str(pe)}")
        return False, "Corrupted PDF file", original_size, 0
    except PasswordError as pe:
        logging.error(f"Encrypted PDF skipped: {input_path}")
        return False, "Password protected", original_size, 0
    except Exception as e:
        logging.error(f"Error in {input_path}: {str(e)}", exc_info=True)
        return False, str(e), original_size, 0
    except (TypeError, ValueError, AttributeError) as e:
        logging.error(f"PDF structure error in {input_path}: {str(e)}")
        return False, "Invalid PDF structure", original_size, 0
