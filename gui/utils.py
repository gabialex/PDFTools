# gui/utils.py
import tkinter as tk
from tkinter import ttk
import os
import uuid
from pathlib import Path

def format_time(seconds):
        """Convert seconds to H:MM:SS format"""
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes:02d}m"
            elif minutes > 0:
                return f"{minutes}m {seconds:02d}s  "
            return f"{seconds}s"
        except:
            return "--:--"     

def truncate_path(
    path: str,
    max_folders: int = 2,
    ellipsis: str = "-->",
    max_length: int = 50
) -> str:
    """
    Path truncation with mixed separator support. Forces forward slashes for consistency in display.
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

def truncate_filename(file: str, 
                      ellipsis: str = "-->", 
                      max_length: int = 50) -> str:
    
    if len(file) <= max_length:
        return file
    
    # Calculate available space for the beginning and the end of the filename
    space_for_parts = max_length - len(ellipsis)
    if space_for_parts <= 0:
        raise ValueError("max_length must be greater than the length of the ellipsis.")
    
    # Divide the available space between the beginning and end of the filename
    part_length = space_for_parts // 2
    
    # Truncate the filename and add the ellipsis in the middle
    truncated_file = file[:part_length] + ellipsis + file[-part_length:]
    
    return truncated_file

# Example usage:
#filename = "this_is_a_really_long_filename_that_needs_to_be_shortened.txt"
#print(truncate_filename(filename, "-->", 30))

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

# Add this to your gui/utils.py
class CustomText(tk.Text):
    """Text widget with theme-aware right-click context menu"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_window = parent.winfo_toplevel()  # Reference to MainWindow
        self._create_context_menu()
        self.bind("<Button-3>", self._show_context_menu)  # Right-click binding

        # Enable keyboard shortcuts
        self.bind("<Control-c>", lambda e: self.event_generate("<<Copy>>"))
        self.bind("<Control-x>", lambda e: self.event_generate("<<Cut>>"))
        self.bind("<Control-v>", lambda e: self.event_generate("<<Paste>>"))
        self.bind("<Control-a>", self._select_all)

    def _create_context_menu(self):
        """Create the context menu structure"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Cut", 
            command=lambda: self.event_generate("<<Cut>>"),
            accelerator="Ctrl+X",
            state="disabled" # forn now
        )
        self.context_menu.add_command(
            label="Copy", 
            command=lambda: self.event_generate("<<Copy>>"),
            accelerator="Ctrl+C"
        )
        self.context_menu.add_command(
            label="Paste", 
            command=lambda: self.event_generate("<<Paste>>"),
            accelerator="Ctrl+V",
            state="disabled" # for now
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Select All", 
            command=self._select_all,
            accelerator="Ctrl+A"
        )

    def _show_context_menu(self, event):
        """Show the context menu with proper theming"""
        try:
            # Update menu colors based on current theme
            colors = self.main_window.colors[self.main_window.current_theme]
            self.context_menu.configure(
                bg=colors['surface'],
                fg=colors['text'],
                activebackground=colors['primary_accent'],
                activeforeground=colors['surface'],
                relief='flat',
                borderwidth=1,
                font=self.main_window.font
            )
            
            # Update paste availability
            try:
                self.clipboard_get()
                self.context_menu.entryconfig("Paste", state="disable") # Force disable for now
            except tk.TclError:
                self.context_menu.entryconfig("Paste", state="disabled")

            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _select_all(self, event=None):
        """Select all text in the widget"""
        self.focus_set()  # Ensure widget has focus
        self.tag_remove("sel", "1.0", "end")  # Clear existing selection
        self.tag_add("sel", "1.0", "end")
        self.mark_set("insert", "1.0")  # Move cursor to start
        self.see("1.0")  # Scroll to top if needed
        return "break"