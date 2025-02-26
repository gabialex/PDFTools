# gui/utils.py
import tkinter as tk
from tkinter import ttk
import os
import uuid
from pathlib import Path

def truncate_path(
    path: str,
    max_folders: int = 2,
    ellipsis: str = "-->",
    max_length: int = 50
) -> str:
    """
    Enhanced path truncation with mixed separator support.
    Forces forward slashes for consistency in display.
    """
    # Normalize path to handle mixed separators
    normalized = Path(path).as_posix()  # Convert all separators to /
    
    # Split into components
    parts = normalized.split('/')
    parts = [p for p in parts if p]  # Remove empty strings
    
    # Extract drive/root for Windows
    if os.name == 'nt' and len(parts) > 0 and ':' in parts[0]:
        root = parts[0] + '/'
        parts = parts[1:]
    else:
        root = '/'
    
    if not parts:
        return normalized
    
    # Separate filename and directories
    filename = parts[-1]
    directories = parts[:-1]
    
    # Truncate logic
    if len(directories) <= max_folders:
        return normalized  # No truncation needed
    
    preserved_dirs = directories[:max_folders]
    truncated = f"{root}{'/'.join(preserved_dirs)}/{ellipsis}/{filename}"
    
    # Final length check
    return truncated if len(truncated) <= max_length else f"{root}{ellipsis}/{filename}"

def is_directory_writable(directory: str) -> tuple[bool, str]:
    """
    Checks if a directory is writable by attempting to create/delete a test file.
    Returns: (success: bool, error_message: str)
    """
    try:
        # Generate unique filename to avoid collisions
        test_file = os.path.join(directory, f"temp_write_test_{uuid.uuid4().hex}.tmp")
        
        # Attempt to write/delete a test file
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        
        return True, ""
    
    except Exception as e:
        return False, str(e)

class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # Milliseconds before tooltip appears
        self.tooltip = None
        self.id = None  # To track the delayed tooltip
        
        # Bind events
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<ButtonPress>", self.hide_tooltip)  # Hide on click

    def schedule_tooltip(self, event=None):
        """Schedule tooltip to appear after a short delay."""
        self.cancel_scheduled()
        self.id = self.widget.after(self.delay, self.show_tooltip)

    def cancel_scheduled(self):
        """Cancel any pending tooltip display."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tooltip(self, event=None):
        """Display the tooltip."""
        self.cancel_scheduled()
        
        # Get widget position
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        # Styled frame for tooltip
        frame = ttk.Frame(self.tooltip, style="Tooltip.TFrame")
        frame.pack()
        
        # Tooltip label
        label = ttk.Label(frame, text=self.text, style="Tooltip.TLabel")
        label.pack(padx=1, pady=1)

        # Prevent tooltip from lingering if mouse leaves quickly
        self.tooltip.bind("<Enter>", self.cancel_scheduled)
        self.tooltip.bind("<Leave>", self.hide_tooltip)

    def hide_tooltip(self, event=None):
        """Hide the tooltip."""
        self.cancel_scheduled()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Add styles for theme consistency (called once during GUI setup)
def configure_tooltip_styles(style: ttk.Style):
    style.configure("Tooltip.TFrame", background="#333333", borderwidth=1)
    style.configure("Tooltip.TLabel", background="#333333", foreground="white")