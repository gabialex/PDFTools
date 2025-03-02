#gui/main.window.py
import tkinter as tk
from tkinter import ttk
import time

# Local imports
from logic.log_viewer import view_logs
from logic.help_window import open_help
from .compression_ops import CompressionOps
from .merging_ops import MergingOps
from .splitting_ops import SplittingOps
from .utils import ToolTip
from gui.utils import configure_tooltip_styles
from .ocr_ops import OCROpsFrame

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Tools")
        self.geometry("1900x1200")
        self.minsize(1900, 1200)

        # Initialize style
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Start with light theme
        
        # Define color schemes
        self.colors = {
            'light': {
                'background': '#F8F9FA',
                'surface': '#FFFFFF',
                'primary_accent': '#4A90E2',
                'secondary_accent': '#6C757D',
                'text': '#212529',
                'hover': '#E9ECEF'
            },
            'dark': {
                'background': '#000000',      # Pure black for frames
                'surface': '#1E1E1E',         # Dark gray for other elements
                'primary_accent': '#4A90E2',   # Keep original blue accent
                'secondary_accent': '#6C757D', # Keep original gray accent
                'text': '#FFFFFF',            # White text
                'hover': '#373737'            # Dark gray hover
            }
        }
        
        # Initialize operations
        self.compression_ops = CompressionOps(self)
        self.merging_ops = MergingOps(self)
        self.splitting_ops = SplittingOps(self)
        configure_tooltip_styles(self.style)
        self.ocr_ops = OCROpsFrame(self, controller=self)
        
        # Set initial theme
        self.current_theme = 'light'
        self.theme_toggle_button = None  # Initialize as None
        
        # Build the UI
        self.setup_ui()
        
        # Apply theme after UI is built
        self.apply_theme()

    def setup_ui(self):
        """Set up the main UI components."""
        # Custom font
        self.font = ("Segoe UI", 10)
        
        # Top-Right Corner buttons
        self.setup_top_right_buttons()

        # Main Container Frame with modern styling
        self.main_frame = ttk.Frame(self, style='Main.TFrame')
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left Column: Compress PDFs
        self.compression_ops.setup_compression_ui(self.main_frame)

        # Right Column: Merge / Split PDFs
        self.merging_ops.setup_merging_ui(self.main_frame)
        self.splitting_ops.setup_splitting_ui(self.main_frame)

        # OCR Column
        self.ocr_ops.setup_ocr_ui(self.main_frame)

    def setup_top_right_buttons(self):
        """Set up the top-right buttons with modern styling."""
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
        """Apply the modern theme with enhanced styling."""
        colors = self.colors[self.current_theme]
        
        # Configure main styles
        self.configure(background=colors['background'])
        
        # Frame styles
        self.style.configure('Main.TFrame',
            background=colors['background'],
            borderwidth=1
        )
        
        self.style.configure('TopRight.TFrame',
            background=colors['background'],
            borderwidth=1
        )
        
        # Button styles
        self.style.configure('TButton',
            background=colors['surface'],
            foreground=colors['text'],
            bordercolor=colors['secondary_accent'],
            borderwidth=1,
            relief="flat",
            padding=(12, 4),
            font=("Segoe UI Semibold", 10),
            anchor="center"
        )
        
        self.style.configure('Icon.TButton',
            background=colors['surface'],
            foreground=colors['text'],
            bordercolor=colors['secondary_accent'],
            relief="flat",
            borderwidth=1,
            padding=2
        )
        
        # Button mapping for hover and pressed states
        self.style.map('TButton',
            background=[
                ('pressed', colors['primary_accent']),
                ('active', colors['hover'])
            ],
            foreground=[
                ('pressed', colors['text'])
            ]
        )
        
        # Entry styles
        self.style.configure('TEntry',
            fieldbackground=colors['surface'],
            foreground=colors['text'],
            bordercolor=colors['secondary_accent'],
            insertcolor=colors['text']
        )

        # Headers Style
        self.style.configure('Green_Header.TLabel',
            foreground='green' if self.current_theme == 'light' else 'black',
            font = ("Segoe UI", 10, "bold")
        )
                             

        # Label styles (Statuses: Normal, Status, Warning)
        self.style.configure('Normal.TLabel',            
            foreground=colors['text'] if self.current_theme == 'light' else 'black',
            font=("Segoe UI", 9)
        )
        
        self.style.configure('Status.TLabel',            
            foreground='#29A745' if self.current_theme == 'light' else '#57D655',  # Green shades for status
            font=("Segoe UI", 9)
        )
        
        self.style.configure('Warning.TLabel',
            background=colors['background'],
            foreground='#DC3545' if self.current_theme == 'light' else '#FF4C4C',  # Red shades for warnings
            font=("Segoe UI", 9)
        )

        # Checkbox styles (Normal, Status, Warning)
        self.style.configure('Normal.TCheckbutton',            
            foreground=colors['text'],
            font=("Segoe UI", 9),
            indicatorcolor=colors['primary_accent'],
            padding=(10, 5)
        )
        
        self.style.configure('Status.TCheckbutton',            
            foreground='#28A745' if self.current_theme == 'light' else '#57D655',  # Green for status
            font=("Segoe UI", 9),
            indicatorcolor='#28A745' if self.current_theme == 'light' else '#57D655',
            padding=(10, 5)
        )
        
        self.style.configure('Warning.TCheckbutton',            
            foreground=colors['text'],
            font=("Segoe UI", 9),
            padding=(10, 5)
        )

        self.style.map('Warning.TCheckbutton',
        foreground=[
            ('!selected', 'black'),  # Red color when unchecked
            ('selected', '#DC3545')  # Brighter red color when checked
        ]
    )
        
        # Progress bar styles
        self.style.configure('Normal.Horizontal.TProgressbar',
            troughcolor=colors['surface'],
            bordercolor=colors['secondary_accent'],
            background=colors['primary_accent'],
            thickness=8,
            troughrelief="flat"
        )

        self.style.configure('Compress.Horizontal.TProgressbar',
            troughcolor=colors['surface'],
            bordercolor=colors['secondary_accent'],
            background='#FFA500' if self.current_theme == 'light' else '#FF8C00',  # Orange shades
            thickness=8,
            lightcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            darkcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            troughrelief="flat"
        )

        self.style.configure('Working.Horizontal.TProgressbar',
            troughcolor=colors['surface'],
            bordercolor=colors['secondary_accent'],
            background='#6CA6CD' if self.current_theme == 'light' else '#6CA6CD',  # Orange shades
            thickness=8,
            lightcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            darkcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            troughrelief="flat"
        )
        
        # Update theme toggle button
        if self.theme_toggle_button is not None:
            self.theme_toggle_button.config(
                text="🌙" if self.current_theme == 'dark' else "🌞"  # Fixed condition
            )

    def toggle_theme(self, event=None):
        """Toggle between light and dark themes."""
        # Remove fade animation to prevent rendering issues
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme()
        
        # Force full UI refresh
        self._refresh_widgets(self)

    def _refresh_widgets(self, widget):
        """Recursively refresh widget styles."""
        try:
            widget.update_idletasks()
            for child in widget.winfo_children():
                # Re-apply styles to all widgets
                if isinstance(child, ttk.Widget):
                    child.configure(style=child.cget('style'))
                self._refresh_widgets(child)
        except Exception:
            pass

    def view_logs(self, event=None):
        """Open the log viewer."""
        view_logs(self)

    def open_help(self, event=None):
        """Open the help window."""
        open_help(self)