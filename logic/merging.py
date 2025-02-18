# logic/merging.py
import os
import logging
from PyPDF2 import PdfMerger
from .compression import compress_pdf

def merge_pdfs(
    file_paths: list,
    output_path: str,
    compress_before_merge: bool = False,
    compression_level: str = "medium",
    update_callback: callable = None
) -> tuple:
    """
    Merge PDF files with optional compression and progress updates.
    Returns: (success: bool, summary: str | None, error: str | None)
    """
    merger = PdfMerger()
    temp_files = []
    total_original = 0
    total_compressed = 0
    summary = []

    try:
        for idx, file in enumerate(file_paths):
            # Update progress via callback
            if update_callback:
                update_callback(file, idx + 1)

            # Handle compression if enabled
            if compress_before_merge:
                temp_file = file.replace(".pdf", "_temp_compressed.pdf")
                success, result = compress_pdf(file, temp_file, compression_level)
                
                if success:
                    temp_files.append(temp_file)
                    merger.append(temp_file)
                    total_original += os.path.getsize(file)
                    total_compressed += result
                else:
                    merger.append(file)  # Fallback to original
                    logging.warning(f"Compression failed for {file}, using original")
            else:
                merger.append(file)

        merger.write(output_path)
        merger.close()

        # Generate summary
        summary = _generate_summary(
            file_paths,
            total_original,
            total_compressed,
            compress_before_merge
        )
        return True, summary, None

    except Exception as e:
        logging.error(f"Merge failed: {str(e)}", exc_info=True)
        return False, None, str(e)
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                logging.error(f"Failed to delete {temp_file}: {str(e)}")

def _generate_summary(file_list, original, compressed, used_compression):
    """Generate merge summary text."""
    if used_compression:
        reduction = original - compressed
        ratio = (reduction / original * 100) if original > 0 else 0
        return (
            f"Merged {len(file_list)} files\n"
            f"Original Size: {original / 1024 / 1024:.2f} MB\n"
            f"Compressed Size: {compressed / 1024 / 1024:.2f} MB\n"
            f"Reduction: {reduction / 1024 / 1024:.2f} MB ({ratio:.1f}%)"
        )
    else:
        return f"Merged {len(file_list)} files (Total: {original / 1024 / 1024:.2f} MB)"