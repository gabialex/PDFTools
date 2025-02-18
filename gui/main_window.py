# gui/main_window.py
import tkinter as tk
from tkinter import ttk

# Local imports
from logic.log_viewer import view_logs
from logic.help_window import open_help
from .compression_ops import CompressionOps
from .merging_ops import MergingOps
from .utils import ToolTip
from gui.utils import configure_tooltip_styles

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Tools")
        self.geometry("900x900")
        self.minsize(900, 900)
        

        # Apply a theme
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Default light theme
        
        # Initialize compression and merging operations
        self.compression_ops = CompressionOps(self)
        self.merging_ops = MergingOps(self)
        configure_tooltip_styles(self.style)  # Add this line

        # Build the UI
        self.setup_ui()

    def setup_ui(self):
        """Set up the main UI components."""
        
        # Custom font
        self.font = ("Segoe UI", 10)
        
        # Top-Right Corner: Log Viewer, Help, and Theme Toggle Buttons
        self.setup_top_right_buttons()

        # Main Container Frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Column: Compress PDFs
        self.compression_ops.setup_compression_ui(self.main_frame)

        # Vertical Separator
        self.separator = ttk.Separator(self.main_frame, orient="vertical")
        self.separator.pack(side="left", fill="y", padx=10)

        # Right Column: Merge PDFs
        self.merging_ops.setup_merging_ui(self.main_frame)

    def setup_top_right_buttons(self):
        """Set up the top-right buttons (Log Viewer, Help, Theme Toggle)."""
        self.top_right_frame = ttk.Frame(self)
        self.top_right_frame.pack(side="top", anchor="ne", padx=10, pady=5)

        # Log Viewer Button
        self.log_viewer_button = ttk.Button(
            self.top_right_frame,
            text="📄",
            command=self.view_logs,
            width=2
        )
        self.log_viewer_button.pack(side="left", padx=5)
        ToolTip(self.log_viewer_button, "View Logs")

        # Help Button
        self.help_button = ttk.Button(
            self.top_right_frame,
            text="?",
            command=self.open_help,
            width=2
        )
        self.help_button.pack(side="left", padx=5)
        ToolTip(self.help_button, "Open Help Section")

        # Theme Toggle Button
        self.theme_toggle_button = ttk.Button(
            self.top_right_frame,
            text="🌞",
            command=self.toggle_theme,
            width=2
        )
        self.theme_toggle_button.pack(side="right")
        ToolTip(self.theme_toggle_button, "Toggle between light/dark themes")

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current_theme = self.style.theme_use()
        
        if current_theme == "clam":
            # Dark theme
            self.style.theme_use("alt")
            self.configure(background="#2d2d2d")
            self.style.configure(".", background="#2d2d2d", foreground="white")
            self.style.map("TButton", background=[("active", "#404040")])
            self.theme_toggle_button.config(text="🌙")
        else:
            # Light theme
            self.style.theme_use("clam")
            self.configure(background="SystemButtonFace")  # Default background
            self.theme_toggle_button.config(text="🌞")
    
        # Force refresh of all widgets
        self._refresh_widgets(self)

    def _refresh_widgets(self, widget):
        """Recursively refresh widget styles to apply theme changes."""
        try:
            widget.update_idletasks()  # Force geometry updates
            children = widget.winfo_children()
            for child in children:
                child.configure(style="TButton" if isinstance(child, ttk.Button) else None)
                self._refresh_widgets(child)  # Recursively refresh children
        except Exception as e:
            pass  # Skip widgets that can't be configured

    def view_logs(self):
        """Open the log viewer."""
        #from logic.log_viewer import view_logs
        view_logs(self)

    def open_help(self):
        """Open the help window."""
        #from logic.help_window import open_help
        open_help(self)