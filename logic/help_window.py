import tkinter as tk
from tkinter import ttk

def open_help(root):
    """Open a new window with help information."""
    help_window = tk.Toplevel(root)
    help_window.title("Help Section")
    help_window.geometry("600x600")
    help_window.resizable(False, False)

    # Add a label for the title
    title_label = ttk.Label(help_window, text="PDF Tools Help", font=("Segoe UI", 14, "bold"))
    title_label.pack(pady=10)

    # Add a text widget for the help content
    help_text = tk.Text(help_window, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
    help_text.pack(fill="both", expand=True)

    # Insert help content
    help_content = """
    Welcome to PDF Tools!

    This application allows you to compress and merge PDF files easily.

    --- Compression ---
    1. Select a directory or individual PDF files to compress.
    2. Choose the compression level (High, Medium, Low).
    3. Set the batch size and pause duration (optional).
    4. Click "Start Compression" to begin.

    --- Merging ---
    1. Select multiple PDF files to merge.
    2. Choose whether to compress files before merging.
    3. Select the output folder and enter a file name.
    4. Click "Start Merging" to begin.

    --- FAQs ---
    Q: Can I compress and merge files at the same time?
    A: No, these are separate operations. You can compress files before merging them.

    Q: What happens if I delete original files after compression/merging?
    A: The original files will be permanently deleted. Use this option with caution.

    Q: How do I cancel an operation?
    A: Click the "Cancel" button during compression or merging.    
    """
    help_text.insert("1.0", help_content)
    help_text.config(state="disabled")  # Make the text read-only

    # Add a close button
    close_button = ttk.Button(help_window, text="Close", command=help_window.destroy)
    close_button.pack(pady=10)