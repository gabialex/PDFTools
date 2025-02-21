import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_pdf, output_dir, split_type="all", update_callback=None):
    """Split a PDF file into multiple files.
    
    Args:
        input_pdf (str): Path to the input PDF file.
        output_dir (str): Directory to save the split files.
        split_type (str): Split type ("all" for every page, or custom ranges).
        update_callback (callable): Callback function to update progress.
        
    Returns:
        bool, str: Success status and summary message.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(input_pdf, 'rb') as infile:
            reader = PdfReader(infile)
            total_pages = len(reader.pages)  # PdfReader uses 'pages' attribute now
            
            if split_type == "all":
                for i in range(total_pages):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])  # 'add_page' and 'pages[i]' in PdfReader
                    
                    output_filename = f"split_page_{i + 1}.pdf"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    with open(output_path, 'wb') as outfile:
                        writer.write(outfile)
                    
                    if update_callback:
                        update_callback(i + 1, total_pages)  # Progress update callback
            
            # You can extend logic here for custom split types (e.g., ranges, odd/even pages)
            
        return True, f"Successfully split into {total_pages} files."
    
    except Exception as e:
        return False, str(e)
