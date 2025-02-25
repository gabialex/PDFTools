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
    update_callback: callable = None,
    log_callback: callable = None  # Added log callback
) -> tuple:
    """
    Merge PDF files with optional compression and progress updates.
    Returns: (success: bool, summary: str | None, error: str | None)
    """
    merger = PdfMerger()
    temp_files = []
    total_original = 0
    total_compressed = 0    
    log_messages = []  # Store splitting log messages during proces

    def add_log(message):
        if log_callback:
            log_callback(message)
        log_messages.append(message)

    try:
        add_log(f"Starting merge of {len(file_paths)} files")
        add_log(f"Output destination: {output_path}\n")

        for idx, file in enumerate(file_paths):
            # Update progress via callback
            if update_callback:
                update_callback(file, idx + 1)

            file_size = os.path.getsize(file)
            add_log(f"Processing: {os.path.basename(file)} ({file_size/1024:.1f} KB)")

            # Handle compression if enabled
            if compress_before_merge:
                temp_file = file.replace(".pdf", "_temp_compressed.pdf")
                success, result = compress_pdf(file, temp_file, compression_level)
                
                if success:
                    temp_files.append(temp_file)
                    merger.append(temp_file)
                    compressed_size = os.path.getsize(temp_file)
                    total_original += file_size
                    total_compressed += compressed_size
                    ratio = max((1 - (compressed_size / file_size)) * 100, 0)
                    add_log(f"  ✓ Compressed: {ratio:.1f}% reduction")
                else:
                    merger.append(file)
                    if ratio > 0:
                        add_log(f"  ✓ Compressed: {ratio:.1f}% reduction")
                    else:
                        add_log(f"  ⚠️ No meaningful reduction (0%)", "warning")
                    total_original += file_size
                    total_compressed += file_size
            else:
                merger.append(file)
                total_original += file_size

        merger.write(output_path)
        merger.close()
        #add_log("____________________________")
        #add_log("Merge completed successfully")

        # Generate detailed summary data
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
        # Cleanup temporary files with logging
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

