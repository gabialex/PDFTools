# logic/split.py
import os
import subprocess
from PyPDF2 import PdfReader, PdfWriter
import time

from gui.utils import truncate_filename

def split_pdf(input_pdf, 
              output_dir, 
              compress=False, 
              compression_level="medium", 
              update_callback=None, 
              log_callback=None):
    
    filename = os.path.splitext(os.path.basename(input_pdf))[0]
    generated_files = []
    total_pages = 0
    compression_stats = {
        'success': 0, 
        'skipped': 0, 
        'errors': 0,
        'total_original': 0,  # bytes
        'total_compressed': 0  # bytes
    }

    try:
        if log_callback:
            filename = truncate_filename(filename, '...', 45)
            #log_callback(f"Processing: {filename}")

        with open(input_pdf, 'rb') as infile:
            reader = PdfReader(infile)
            total_pages = len(reader.pages)
            log_callback(f"\n▶ Processing {filename} ({total_pages} pages)")

            for i in range(total_pages):
                output_path = os.path.join(output_dir, f"{filename}_page_{i + 1}.pdf")
                generated_files.append(output_path)

                # Split page
                with PdfWriter() as writer:
                    writer.add_page(reader.pages[i])
                    with open(output_path, 'wb') as outfile:
                        writer.write(outfile)

                # Get size before compression
                original_size = os.path.getsize(output_path)
                final_size = original_size

                # Handle compression
                if compress:
                    try:
                        compression_worked, new_size = _compress_with_ghostscript(
                            output_path, 
                            compression_level
                        )
                        
                        if compression_worked:
                            compression_stats['success'] += 1
                        else:
                            compression_stats['skipped'] += 1
                            
                        final_size = new_size
                    except Exception as e:
                        compression_stats['errors'] += 1
                        final_size = original_size  # File remains unchanged
                        if log_callback:
                            log_callback(f"⚠️ Compression error on page {i+1}: {str(e)}")

                    # Update size tracking
                    compression_stats['total_original'] += original_size
                    compression_stats['total_compressed'] += final_size

                # Update split progress
                if log_callback:
                    log_callback(f"SPLIT_PROGRESS:{i+1}/{total_pages}")

                if update_callback:
                    update_callback(i + 1, total_pages)
                time.sleep(0.01)

            # Final messages
            if log_callback:
                message = f"\n  • {filename} split into {total_pages} files."
                if not compress:
                    log_callback(message + '\n  - Split pages status: Uncompressed') 

                if compress:                    
                    _log_compression_summary(compression_stats, log_callback)
                    log_callback(message + '\n  - Split pages status: Compressed')

        return True, f"\n{filename} split into {total_pages} files", generated_files

    except Exception as e:
        for f in generated_files:
            try: os.remove(f)
            except: pass
        return False, f"Failed to split PDF: {str(e)}", []
    
def _log_compression_summary(stats, log_callback):
    """Helper to format compression statistics"""
    try:
        total_original = stats['total_original']
        total_compressed = stats['total_compressed']
        saved = total_original - total_compressed
        
        # Convert bytes to MB
        mb_original = total_original / (1024 * 1024)
        mb_compressed = total_compressed / (1024 * 1024)
        mb_saved = saved / (1024 * 1024)
        
        # Calculate percentage saved
        ratio = (saved / total_original * 100) if total_original > 0 else 0
        
        summary = (
            "\n\nCompression Summary:\n"
            f"• Successfully compressed: {stats['success']} pages\n"
            f"• Skipped (no gain): {stats['skipped']} pages\n"
            f"• Errors: {stats['errors']} pages\n"
            f"• Total size before: {mb_original:.2f} MB\n"
            f"• Total size after: {mb_compressed:.2f} MB\n"
            f"• Space saved: {mb_saved:.2f} MB ({ratio:.1f}% reduction)"
        )
        log_callback(summary)
    except Exception as e:
        log_callback(f"\n⚠️ Failed to generate compression summary: {str(e)}")

def _compress_with_ghostscript(pdf_path, level="medium"):
    """Returns tuple: (compression_applied: bool, new_size: int)"""
    try:
        gs_cmd = 'gswin64c' if os.name == 'nt' else 'gs'
        subprocess.run(
            [gs_cmd, "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise RuntimeError("Ghostscript not found")

    levels = {
        "high": "/printer",
        "medium": "/ebook",
        "low": "/screen"
    }
    
    temp_path = f"{pdf_path}_temp"
    original_size = os.path.getsize(pdf_path)
    size_threshold = 0.99  # Require 1% reduction

    try:
        subprocess.run(
            [
                gs_cmd,
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

        new_size = os.path.getsize(temp_path)
        
        if new_size < (original_size * size_threshold):
            os.replace(temp_path, pdf_path)
            return True, new_size
        else:
            os.remove(temp_path)
            return False, original_size

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip() or "Unknown error"
        raise RuntimeError(f"Ghostscript failed: {error_msg}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)    