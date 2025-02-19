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
from .ocr_ops import OCROpsFrame

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Tools")
        self.geometry("1250x900")
        self.minsize(1250, 900)

        # Initialize style
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Start with light theme
        
        # Define color schemes
        self.colors = {
            'light': {
                'bg': 'white',
                'fg': 'black',
                'button': '#ffffff',
                'button_pressed': '#e0e0e0',
                'accent': '#007acc',
                'border': '#cccccc',
                'hover': '#e8e8e8'
            },
            'dark': {
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'button': '#2d2d2d',
                'button_pressed': '#404040',
                'accent': '#0098ff',
                'border': '#555555',
                'hover': '#383838'
            }
        }
        
        # Initialize operations
        self.compression_ops = CompressionOps(self)
        self.merging_ops = MergingOps(self)
        configure_tooltip_styles(self.style)
        self.ocr_ops = OCROpsFrame(self, controller=self)
        
        # Set initial theme
        self.current_theme = 'light'
        self.theme_toggle_button = None  # Initialize as None
        
        # Build the UI
        self.setup_ui()
        
        # Apply theme after UI is built
        self.apply_theme()

    def view_logs(self, event=None):
        """Open the log viewer."""
        view_logs(self)

    def open_help(self, event=None):
        """Open the help window."""
        open_help(self)

    def setup_ui(self):
        """Set up the main UI components."""
        # Custom font
        self.font = ("Segoe UI", 10)
        
        # Top-Right Corner buttons
        self.setup_top_right_buttons()

        # Main Container Frame with custom styling
        self.main_frame = ttk.Frame(self, style='Main.TFrame')
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left Column: Compress PDFs
        self.compression_ops.setup_compression_ui(self.main_frame)

        # Vertical Separator with themed color
        self.separator = ttk.Separator(self.main_frame, orient="vertical")
        self.separator.pack(side="left", fill="y", padx=20)

        # Right Column: Merge PDFs
        self.merging_ops.setup_merging_ui(self.main_frame)

        # Vertical Separator after merging
        self.separator2 = ttk.Separator(self.main_frame, orient="vertical")
        self.separator2.pack(side="left", fill="y", padx=20)

        # OCR Column        
        #self.ocr_ops.pack(side="left", fill="y", expand=True)
        self.ocr_ops.setup_ocr_ui(self.main_frame)

    def setup_top_right_buttons(self):
        """Set up the top-right buttons with improved styling."""
        self.top_right_frame = ttk.Frame(self, style='TopRight.TFrame')
        self.top_right_frame.pack(side="top", anchor="ne", padx=20, pady=10)

        # Button configurations with bound methods
        button_configs = [
            ("📄", lambda: self.view_logs(), "View Logs"),
            ("?", lambda: self.open_help(), "Open Help Section"),
            ("🌞", lambda: self.toggle_theme(), "Toggle Theme")
        ]

        for text, command, tooltip in button_configs:
            btn = ttk.Button(
                self.top_right_frame,
                text=text,
                command=command,
                style='Icon.TButton',
                width=3
            )
            btn.pack(side="left", padx=5)
            ToolTip(btn, tooltip)
            
            if text == "🌞":
                self.theme_toggle_button = btn

    def apply_theme(self):
        """Apply the current theme with enhanced styling."""
        colors = self.colors[self.current_theme]
        
        # Configure main styles
        self.configure(background=colors['bg'])
        
        # Frame styles
        self.style.configure('Main.TFrame',
            background=colors['bg'],
            borderwidth=0
        )
        
        self.style.configure('TopRight.TFrame',
            background=colors['bg'],
            borderwidth=0
        )
        
        # Button styles
        self.style.configure('TButton',
            background=colors['button'],
            foreground=colors['fg'],
            bordercolor=colors['border'],
            lightcolor=colors['button'],
            darkcolor=colors['button'],
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padding=5
        )
        
        # Special style for icon buttons
        self.style.configure('Icon.TButton',
            background=colors['button'],
            foreground=colors['fg'],
            bordercolor=colors['border'],
            relief="solid",
            borderwidth=1,
            padding=2
        )
        
        # Button mapping for hover and pressed states
        self.style.map('TButton',
            background=[
                ('pressed', colors['button_pressed']),
                ('active', colors['hover'])
            ],
            bordercolor=[
                ('pressed', colors['accent']),
                ('active', colors['accent'])
            ],
            relief=[('pressed', 'solid')]
        )
        
        # Entry styles
        self.style.configure('TEntry',
            fieldbackground=colors['button'],
            foreground=colors['fg'],
            bordercolor=colors['border'],
            lightcolor=colors['button'],
            darkcolor=colors['button'],
            insertcolor=colors['fg']
        )
        
        # Separator style
        self.style.configure('TSeparator',
            background=colors['border']
        )
        
        # Update theme toggle button
        if self.theme_toggle_button is not None:
            self.theme_toggle_button.config(
                text="🌙" if self.current_theme == 'light' else "🌞"
            )

    def toggle_theme(self, event=None):
        """Toggle between light and dark themes."""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme()
        self._refresh_widgets(self)

    def _refresh_widgets(self, widget):
        """Recursively refresh widget styles."""
        try:
            widget.update_idletasks()
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(style='Icon.TButton' if child is self.theme_toggle_button else 'TButton')
                self._refresh_widgets(child)
        except Exception:
            pass