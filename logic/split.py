# logic/split.py
import os
import subprocess
from PyPDF2 import PdfReader, PdfWriter
import time
import sys

def split_pdf(input_pdf, output_dir, split_type="all", compress=False, 
             compression_level="medium", update_callback=None, log_callback=None):
    filename = os.path.splitext(os.path.basename(input_pdf))[0]
    generated_files = []
    total_pages = 0  # Needed for final message

    try:
        if log_callback:
            # Initial split start message
            log_callback(f"Starting split of {filename}\n")  # Newline for separation

        if not os.path.exists(input_pdf):
            raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

        os.makedirs(output_dir, exist_ok=True)

        with open(input_pdf, 'rb') as infile:
            reader = PdfReader(infile)
            total_pages = len(reader.pages)

            for i in range(total_pages):
                output_path = os.path.join(output_dir, f"{filename}_page_{i + 1}.pdf")
                generated_files.append(output_path)

                # Split page
                with PdfWriter() as writer:
                    writer.add_page(reader.pages[i])
                    with open(output_path, 'wb') as outfile:
                        writer.write(outfile)

                # Send progress update (REPLACED individual messages)
                if log_callback:
                    log_callback(f"SPLIT_PROGRESS:{i+1}/{total_pages}")

                # Compress if requested (ONCE per page)
                if compress:
                    if log_callback:
                        log_callback(f"\nCompressing page {i+1} from {filename} PDF")
                    try:
                        compression_worked = _compress_with_ghostscript(output_path, compression_level)
                        if not compression_worked and log_callback:
                            log_callback(f"Skipped compression for page {i+1} (Insufficient size reduction)")
                        elif log_callback:
                            log_callback(f"\nPage {i+1} compressed successfully")
                    except Exception as e:
                        if log_callback:
                            log_callback(f"Compression error on page {i+1} ({filename}): {str(e)}")

                # Update progress after split+compress
                if update_callback:
                    update_callback(i + 1, total_pages)
                time.sleep(0.01)  # Allow UI updates

            # Final completion message (ADDED NEWLINE AT START)
            if log_callback:
                log_callback(f"\nSplit {filename} into {total_pages} files. Compressed: {compress}\n")

        return True, f"Split {filename} into {total_pages} files", generated_files 
        #return True, f"Splited {filename} into {total_pages} files. Compressed: {compress}"    

    except Exception as e:
        return False, f"Failed to split PDF: {str(e)}", []  # Empty list on failure
    
    except Exception as e:
        for f in generated_files:
            try: os.remove(f)
            except: pass
        return False, f"Failed to split PDF: {str(e)}", []

def _compress_with_ghostscript(pdf_path, level="medium"):
    """Compress PDF only if it reduces size by at least 1%."""
    try:
        # Single Ghostscript check
        gs_cmd = 'gswin64c' if sys.platform == 'win32' else 'gs'
        subprocess.run(
            [gs_cmd, "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise RuntimeError("Ghostscript not found. Install from https://www.ghostscript.com/")
    
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