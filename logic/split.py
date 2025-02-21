# logic/split.py
import os
import subprocess
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_pdf, output_dir, split_type="all", compress=False, 
             compression_level="medium", update_callback=None):
    """Split PDF into multiple files with optional Ghostscript compression."""
    try:
        if not os.path.exists(input_pdf):
            raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

        os.makedirs(output_dir, exist_ok=True)  # Safer directory creation

        with open(input_pdf, 'rb') as infile:
            reader = PdfReader(infile)
            total_pages = len(reader.pages)

            for i in range(total_pages):
                output_path = os.path.join(output_dir, f"split_page_{i + 1}.pdf")
                
                # Split page
                with PdfWriter() as writer:
                    writer.add_page(reader.pages[i])
                    with open(output_path, 'wb') as outfile:
                        writer.write(outfile)

                # Compress if requested
                if compress:
                    try:
                        compression_worked = _compress_with_ghostscript(output_path, compression_level)
                        if not compression_worked:
                            print(f"Skipped compression for page {i+1} (insufficient size reduction)")
                    except Exception as e:
                        print(f"Compression error on page {i+1}: {str(e)}")

                if update_callback:
                    update_callback(i + 1, total_pages)

        return True, f"Split into {total_pages} files. Compressed: {compress}"

    except Exception as e:
        return False, f"Failed to split PDF: {str(e)}"

# logic/split.py
def _compress_with_ghostscript(pdf_path, level="medium"):
    """Compress PDF only if it reduces size by at least 5%."""
    levels = {
        "high": "/printer",
        "medium": "/ebook",
        "low": "/screen"
    }
    
    temp_path = f"{pdf_path}_temp"
    original_size = os.path.getsize(pdf_path)
    size_threshold = 0.99  # Require at least 1% size reduction
    
    try:
        # Run Ghostscript compression
        subprocess.run(
            [
                "gswin64c",
                "-q",
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=pdfwrite",
                f"-dPDFSETTINGS={levels.get(level, '/ebook')}",
                "-sOutputFile=" + temp_path,
                pdf_path
            ],
            check=True,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # Check if compression was beneficial
        new_size = os.path.getsize(temp_path)
        
        if new_size < (original_size * size_threshold):
            os.replace(temp_path, pdf_path)  # Keep compressed version
            return True
        else:
            return False  # Compression didn't help enough

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip() or "Unknown Ghostscript error"
        raise RuntimeError(f"Compression failed: {error_msg}")
    finally:
        # Cleanup temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)