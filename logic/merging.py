# logic/merging.py (revised)
import os
import logging
from PyPDF2 import PdfMerger
from .compression import compress_pdf
import tempfile

def merge_pdfs(
    file_paths: list,
    output_path: str,
    compress_before_merge: bool = False,
    compression_level: str = "medium",
    update_callback: callable = None,
    log_callback: callable = None
) -> tuple:
    """
    Merge PDF files with optional compression and progress updates.
    Returns: (success: bool, summary: dict | None, error: str | None)
    """
    merger = PdfMerger()
    temp_files = []
    total_original = 0
    total_compressed = 0
    log_messages = []  # Store merge log messages during process

    def add_log(message):
        if log_callback:
            log_callback(message)
        log_messages.append(message)

    try:
        add_log(f"Starting merge of {len(file_paths)} files")
        add_log(f"Output destination: {output_path}\n")

        for idx, file in enumerate(file_paths):
            if update_callback:
                update_callback(file, idx + 1)

            file_size = os.path.getsize(file)
            add_log(f"Processing: {os.path.basename(file)} ({file_size/1024:.1f} KB)")

            if compress_before_merge:
                # Create temp file in system temp directory
                temp_dir = tempfile.gettempdir()
                temp_filename = f"compressed_{os.path.basename(file)}"
                temp_file = os.path.join(temp_dir, temp_filename)
                
                success, result = compress_pdf(file, temp_file, compression_level)
                
                if success:
                    temp_files.append(temp_file)
                    merger.append(temp_file)
                    compressed_size = os.path.getsize(temp_file)
                    total_original += file_size
                    total_compressed += compressed_size
                    ratio = max((1 - (compressed_size / file_size)) * 100, 0)
                    if ratio > 0:
                        add_log(f"  ✓ Compressed: {ratio:.2f}% reduction")
                    else:
                        ratio <= 0
                        add_log(f"  ⚠️ Compression ineffective (0%)")
                else:
                    merger.append(file)
                    add_log(f"  ✗ Compression failed; using original file")
                    total_original += file_size
                    total_compressed += file_size
            else:
                merger.append(file)
                total_original += file_size
                total_compressed += file_size  # Fix: Track as uncompressed

        merger.write(output_path)
        merger.close()

        summary_data = {
            "file_count": len(file_paths),
            "total_original": total_original,
            "total_compressed": total_compressed,
            "used_compression": compress_before_merge,
            "output_path": output_path,
            "log_messages": log_messages
        }

        return True, summary_data, None

    except Exception as e:
        error_msg = f"Merge failed: {str(e)}"
        add_log(error_msg)
        logging.error(error_msg, exc_info=True)
        return False, None, str(e)
    finally:
        if temp_files:
            add_log("\nCleaning up temporary files...")
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    add_log(f"  Deleted: {os.path.basename(temp_file)}")
                except Exception as e:
                    error = f"Failed to delete {temp_file}: {str(e)}"
                    add_log(f"  ✗ {error}")
                    logging.error(error)