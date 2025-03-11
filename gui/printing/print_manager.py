import os
import sys
import platform
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import time
try:
    import win32print
except ImportError:
    if sys.platform == 'win32':
        print("win32print module required for Windows printing")

from gui.utils import ToolTip, truncate_filename

class PrintManager:
    """Standalone printing component reusable across different operations."""
    
    def __init__(self, root, files_to_print, log_callback):
        """
        Args:
            root (Tk): Root window
            files_to_print (list): List of file paths to print
            log_callback (function): Callback for logging messages
        """
        self.root = root
        self.files_to_print = files_to_print
        self.log_callback = log_callback
        self._setup_variables()

    def _setup_variables(self):
        """Initialize printing-related variables"""
        self.page_range_var = tk.StringVar(value="all")
        self.page_filter_var = tk.StringVar(value="all")
        self.collate_var = tk.BooleanVar(value=True)
        self.duplex_var = tk.BooleanVar(value=False)
        self.printer_var = tk.StringVar()
        self.range_entry = None

    @staticmethod
    def get_available_printers():
        """Static method to get printers list"""
        system = platform.system()
        printers = []

        if system == "Windows":
            try:
                printer_info = win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                )
                printers = [printer[2] for printer in printer_info]
            except Exception as e:
                print(f"Error detecting printers on Windows: {e}")

        elif sys.platform in ["darwin", "linux"]: # macOS or Linux
            try:
                result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
                if result.returncode == 0:
                    printers = [line.split()[0] for line in result.stdout.splitlines()]
            except Exception as e:
                print(f"Error detecting printers on {system}: {e}")

        else:
            print(f"Unsupported OS: {system}")

        return printers    

    def show_print_dialog(self):
        """Entry point for printing operations"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Print Options")
        dialog.geometry("400x500")  # Adjusted for additional options
        dialog.resizable(False, False)

        # Ensure the dialog stays on top
        dialog.transient(self.root)
        dialog.grab_set()

        # Create variables for the dialog
        self.page_range_var = tk.StringVar(value="all")
        self.page_filter_var = tk.StringVar(value="all")
        self.collate_var = tk.BooleanVar(value=True)
        self.duplex_var = tk.BooleanVar(value=False)
        self.printer_var = tk.StringVar()

        # Get available printers
        printers = self.get_available_printers()
        if not printers:
            messagebox.showwarning("No Printers", "No printers found on this system.")
            dialog.destroy()
            return
        
        # Printer selection
        printer_frame = ttk.LabelFrame(dialog, text="Printer", padding=10)
        printer_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(printer_frame, text="Select Printer:").pack(anchor="w", pady=2)
        printer_combo = ttk.Combobox(
            printer_frame,
            textvariable=self.printer_var,
            values=printers,
            state="readonly"
        )
        printer_combo.pack(fill="x", padx=10, pady=5)
        printer_combo.current(1)  # Select the second printer by default

        # Range selection
        range_frame = ttk.LabelFrame(dialog, text="Page Range", padding=10)
        range_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Radiobutton(
            range_frame,
            text="All Pages",
            variable=self.page_range_var,
            value="all"
        ).pack(anchor="w", pady=2)

        range_radio_frame = ttk.Frame(range_frame)
        range_radio_frame.pack(anchor="w", pady=2)

        ttk.Radiobutton(
            range_radio_frame,
            text="Range:",
            variable=self.page_range_var,
            value="range"
        ).pack(side="left")

        self.range_entry = ttk.Entry(range_radio_frame, width=25)
        self.range_entry.pack(side="left", padx=5)
        ToolTip(self.range_entry, "Example: 1-5, 7, 9-12")

        # Odd/even filter
        filter_frame = ttk.LabelFrame(dialog, text="Page Filter", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Radiobutton(
            filter_frame,
            text="All Pages",
            variable=self.page_filter_var,
            value="all"
        ).pack(anchor="w", pady=2)

        ttk.Radiobutton(
            filter_frame,
            text="Odd Pages",
            variable=self.page_filter_var,
            value="odd"
        ).pack(anchor="w", pady=2)

        ttk.Radiobutton(
            filter_frame,
            text="Even Pages",
            variable=self.page_filter_var,
            value="even"
        ).pack(anchor="w", pady=2)

        # Additional options
        options_frame = ttk.LabelFrame(dialog, text="Additional Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(
            options_frame,
            text="Collate",
            variable=self.collate_var
        ).pack(anchor="w", pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Duplex Printing (Two-Sided)",
            variable=self.duplex_var
        ).pack(anchor="w", pady=2)

        # Action buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Print",
            command=lambda: self._handle_print(dialog)
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side="left", padx=5)

    def print_split_files(self, page_range="all", custom_range=None, page_filter="all", collate=True, duplex=False):
        """Print selected pages with options and validation checks."""
        if not self.files_to_print:
            messagebox.showwarning("Error", "No split files available for printing")
            return

        # Get selected printer
        printer = self.printer_var.get()
        if not printer:
            messagebox.showwarning("No Printer", "No printer selected.")
            self.show_print_dialog()  # Reopen dialog on no printer
            return
        
        if printer not in self.get_available_printers():
            messagebox.showerror("Printer Offline", f"{printer} is not available")
            return

        # Flag to control dialog reopening
        reopen_dialog = False

        # Parse page range with validation
        try:
            page_range = self._parse_page_range(page_range, custom_range)
            if page_range is None:
                reopen_dialog = True  # Set flag for invalid range

        except Exception as e:
            # Handle logging callback signature differences
            try:
                self.log_callback(f"Print error: {str(e)}", "error")
            except TypeError:
                # Fallback for callbacks without message_type parameter
                self.log_callback(f"Print error: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("Invalid Range", f"Error parsing page range: {str(e)}")
            reopen_dialog = True  # Set flag for parsing error

        # Validate page range against generated files
        if not reopen_dialog and not self._validate_page_range(page_range):
            messagebox.showerror("Invalid Range", "Page range exceeds the number of available files.")
            reopen_dialog = True  # Set flag for out-of-bounds range

        # Apply odd/even filter
        if not reopen_dialog:
            filtered_files = self._apply_page_filter(page_range, page_filter)
            if not filtered_files:
                messagebox.showwarning("No Pages", "No pages match the selected filter")
                reopen_dialog = True  # Set flag for no matching pages

        # Warn for large print jobs
        if not reopen_dialog and len(filtered_files) > 50:
            confirmed = messagebox.askyesno(
                "Large Print Job",
                f"Are you sure you want to print {len(filtered_files)} pages?"
            )
            if not confirmed:
                reopen_dialog = True  # Set flag if user cancels

        # Reopen dialog if any error occurred
        if reopen_dialog:
            self.show_print_dialog()
            return

        # Print the files
        successfully_printed = 0
        for file_path in filtered_files:
            if not os.path.exists(file_path):
                self.log_callback(f"⚠️ Missing: {os.path.basename(file_path)}", "error")
                continue

            try:
                if sys.platform == "win32":
                    # Windows: Use the selected printer
                    os.startfile(file_path, "print")
                else:
                    # macOS/Linux: Use the `lp` command with the selected printer
                    subprocess.run(["lp", "-d", printer, file_path], check=True)
                
                successfully_printed += 1
                filename = os.path.basename(file_path)
                self.log_callback(f" • {truncate_filename(filename, '...', 30)} sent to {printer}", "succes")
                time.sleep(0.5)
            except Exception as e:
                self.log_callback(f"❌ Failed {filename}: {str(e)}", "error")

        # Show summary
        msg = (
            f"Print Summary:\n"
            f"• Printer: {printer}\n"
            f"• Pages selected: {len(filtered_files)}\n"
            f"• Successfully printed: {successfully_printed}\n"
            f"• Errors: {len(filtered_files) - successfully_printed}\n"
            f"• Collate: {'Yes' if collate else 'No'}\n"
            f"• Duplex: {'Yes' if duplex else 'No'}"
        )
        messagebox.showinfo("Print Complete", msg)

    # ----------------------- Helper Methods ------------------------#
    def _handle_print(self, dialog):
        """Handle printing after options are selected."""
        # Get selected options from the dialog
        page_range = self.page_range_var.get()
        custom_range = self.range_entry.get() if page_range == "range" else None
        page_filter = self.page_filter_var.get()
        collate = self.collate_var.get()
        duplex = self.duplex_var.get()
        
        # Close the dialog
        dialog.destroy()
        
        # Call print_split_files with the selected options
        self.print_split_files(page_range, custom_range, page_filter, collate, duplex)

    def _parse_page_range(self, page_range, custom_range):
        """Parse and validate the page range input."""
        if page_range == "all":
            return list(range(len(self.files_to_print)))
        
        if not custom_range:
            messagebox.showwarning("Invalid Range", "Please enter a custom range.")
            return None  # Return None to indicate an error
        
        try:
            parts = custom_range.split(",")
            pages = set()
            for part in parts:
                part = part.strip()  # Remove any whitespace
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    if start > end:
                        messagebox.showwarning("Invalid Range", "Start page cannot be greater than end page.")
                        return None  # Return None to indicate an error
                    pages.update(range(start - 1, end))  # Convert to 0-based index
                else:
                    pages.add(int(part) - 1)  # Convert to 0-based index
            return sorted(pages)
        except ValueError:
            messagebox.showerror("Invalid Range", "Please enter a valid page range (e.g., 1-5, 7, 9-12).")
            return None  # Return None to indicate an error
        
    def _apply_page_filter(self, page_range, page_filter):
        """Apply odd/even filter to the page range."""
        if page_filter == "all":
            return [self.files_to_print[i] for i in page_range]
        
        filtered = []
        for i in page_range:
            if (page_filter == "odd" and i % 2 == 0) or \
            (page_filter == "even" and i % 2 == 1):
                filtered.append(self.files_to_print[i])
        return filtered
    
    def _validate_page_range(self, page_range):
        """Validate that the page range is within the bounds of generated files."""
        if not isinstance(page_range, (list, tuple)):
            return False
        return all(0 <= p < len(self.files_to_print) for p in page_range)  
