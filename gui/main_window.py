#gui/main.window.py
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
# Local imports
from logic.log_viewer import view_logs
from logic.help_window import open_help
from .compression_ops import CompressionOps
from .merging_ops import MergingOps
from .splitting_ops import SplittingOps
from .ocr_ops import OCROpsFrame
from .utils import ToolTip
from gui.utils import configure_tooltip_styles

class MainWindow(tk.Tk):
    def __init__(self):        
        super().__init__()
        self.title("PDF Tools")
        
        # Set initial size based on screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{int(screen_width*0.8)}x{int(screen_height*0.8)}")
        self.minsize(800, 600)  # Minimum size

        try:
            self.iconbitmap('assets/PDFTools2.ico')
        except tk.TclError:
            pass  # Handle missing icon

        # Initialize style
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Start with light theme

        #available_themes = self.style.theme_names()
        #print("Available themes:", available_themes)        
        
        # FONTS
        self.fonts = {
        'base': ("Segoe UI", 9),
        'bold': ("Segoe UI", 10, "bold"),
        'mono': ("Consolas", 9),
        'header': ("Segoe UI", 12, "bold")
    }    
        
        # Define color schemes
        self.colors = {
            'light': {
                'background': '#F8F9FA',
                'surface': '#FFFFFF',
                'primary_accent': '#4A90E2',
                'secondary_accent': '#6C757D',
                'text': '#212529',                
                'hover': '#E9ECEF',
                'border': '#424242',
                'danger': '#DC3545',
                'success': '#28A745',
                'warning': '#FFC107'                     

            },
            'dark': {
                'background': '#0D0D0D',        # Even darker gray background
                'surface': '#2D2D2D',           # Dark gray for other elements
                'primary_accent': '#4A90E2',    # Keep original blue accent
                'secondary_accent': '#6C757D',  # Keep original gray accent
                'text': '#FFFFFF',              # White text
                'hover': '#373737',             # Dark gray hover
                'border': '#757575',             #Lighter border
                'danger': '#FF4444',
                'success': '#57D655',
                'warning': '#FFCA28'
            }
        }
        
        # Initialize operations
        self.compression_ops = CompressionOps(self)
        self.merging_ops = MergingOps(self)
        self.splitting_ops = SplittingOps(self)       
        self.ocr_ops = OCROpsFrame(self, controller=self)
        configure_tooltip_styles(self.style)
        
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

        # Column 1: Compress PDFs
        self.compression_ops.setup_compression_ui(self.main_frame)
        # Column 2: Merge / Split PDFs
        self.merging_ops.setup_merging_ui(self.main_frame)
        # Colum 3: Splitting Ops
        self.splitting_ops.setup_splitting_ui(self.main_frame)
        # Column 4: OCR ops
        self.ocr_ops.setup_ocr_ui(self.main_frame)

    def setup_top_right_buttons(self):
        """Set up the top-right buttons with modern styling."""
        self.top_right_frame = ttk.Frame(self, style='TopRight.TFrame')
        self.top_right_frame.pack(side="top", anchor="ne", padx=0, pady=0)

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
        
        # FRAMES
        self.style.configure('Main.TFrame',
            background=colors['background'],
            borderwidth=0,
            relief="flat",
            padding=(5, 5))

        self.style.configure('TopRight.TFrame',
            background=colors['background'],
            borderwidth=0,
            relief="ridge",
            padding=(5, 5))

        # Add a modern shadow effect to frames
        self.style.configure('Shadow.TFrame',
            background=colors['background'],
            borderwidth=2,
            relief="flat",
            padding=(5, 5))

        # Apply shadow effect to main frame
        self.main_frame.configure(style='Shadow.TFrame')

        # ---------------------------- HEADERS -----------------------------#
        # Green Theme
        self.style.configure('Green_Header.TLabel',
            foreground='green',
            background='lightgray' if self.current_theme == 'light' else 'gray',
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="solid",
            padding=(5, 5, 5, 5)
        )

        # Red Theme
        self.style.configure('Red_Header.TLabel',
            foreground='red',
            background='black',
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="solid",
            padding=(5, 5, 5, 5)
        )

        # Blue Theme
        self.style.configure('Blue_Header.TLabel',
            foreground='blue',
            #background='#E0F7FA',  # Very light blue
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            relief="solid",
            padding=(5, 5, 5, 5),
            bordercolor='#00ACC1'  # More intense blue
        )        

        # Orange Theme
        self.style.configure('Orange_Header.TLabel',
            foreground='orange',
            background='darkgray',
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="solid",
            padding=(5, 5, 5, 5)
        )

        # Headers Style - Purple Theme
        self.style.configure('Purple_Header.TLabel',
            foreground='purple',
            background='lavender',
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="solid",
            padding=(5, 5, 5, 5)
        )

        # ----------------------------- LABELS --------------------------- #
        self.style.configure('Normal.TLabel',            
            foreground=colors['text'] if self.current_theme == 'light' else 'black',
            font=("Segoe UI", 9))
        
        self.style.configure('Status.TLabel',            
            foreground='darkgreen',  # Green shades for status
            font=("Segoe UI Semibold", 9))
        
        self.style.configure('Blue.TLabel',
            foreground='blue',  
            font=("Segoe UI Semibold", 9))
        
        self.style.configure('Orange.TLabel',
            foreground='#E05232',
            bordercolor=colors['secondary_accent'],
            highlightbackground="#2C2C2C",
            #background='gray' if self.current_theme == 'light' else '#FF8C00',  # Orange shades
            font=("Segoe UI Semibold", 9))
        
        self.style.configure('Warning.TLabel',            
            foreground='#DC3545' if self.current_theme == 'light' else '#FF4C4C',  # Red shades for warnings
            font=("Segoe UI Semibold", 9))
        
        # ----------------------------- BUTTONS --------------------------- #
        
        self.style.configure('TButton',
            background=colors['surface'],
            foreground=colors['text'],
            bordercolor=colors['secondary_accent'],
            borderwidth=1,
            relief="flat",
            padding=(12, 4),
            font=("Segoe UI Semibold", 10),
            anchor="center",
            focusthickness=3,  
            focuscolor=colors['primary_accent'] + 'AA' # More visible alpha            
        )

        # Button mapping for hover and pressed states
        self.style.map('TButton',
            background=[
                ('disabled', colors['surface']),  # Disabled state
                ('pressed', colors['primary_accent']),
                ('active', colors['hover'])
            ],
            foreground=[
                ('disabled', colors['secondary_accent']),  # NEW: Disabled text
                ('pressed', colors['surface'])  # Changed: Better contrast when pressed
            ],
            bordercolor=[
                ('active', colors['primary_accent']),  # NEW: Border color on hover
                ('pressed', colors['primary_accent'])  # NEW: Border color on press
            ],
            relief=[
                ('active', 'groove'),  # NEW: Gives tactile feedback on hover
                ('pressed', 'sunken')  # NEW: Physical click feedback
            ]
        )
        
        # Warning button
        self.style.configure('RedText.TButton',
        background=colors['surface'],
        foreground='#DC3545',  # Bootstrap danger red
        bordercolor=colors['warning'],
        relief="flat",
        padding=(12, 4),
        font=("Segoe UI Semibold", 10),
        anchor="center")       

        # Map states for red text button
        self.style.map('RedText.TButton',
            background=[
                ('active', colors['hover']),
                ('pressed', colors['primary_accent'])
            ],
            foreground=[
                ('active', '#FF0000'),  # Brighter red on hover
                ('pressed', colors['surface'])
            ],
            bordercolor=[
                ('active', colors['danger']),  # NEW: Border color on hover
                ('pressed', colors['danger'])  # NEW: Border color on press
            ],
            relief=[
                ('active', 'groove'),  # NEW: Gives tactile feedback on hover
                ('pressed', 'sunken')  # NEW: Physical click feedback
            ]
        )

        # Ready button
        self.style.configure('Ready.TButton',
            background=colors['surface'],
            foreground='green' if self.current_theme == 'light' else 'yellow',
            bordercolor=colors['secondary_accent'],
            relief="flat",
            padding=(12, 4),
            font=("Segoe UI Semibold", 10),
            anchor="center")
        
        # Map states for Ready button
        self.style.map('Ready.TButton',
            background=[
                ('active', colors['hover']),
                ('pressed', colors['primary_accent'])
            ],
            foreground=[
                ('active', 'darkgreen'),  # Brighter green on hover
                ('pressed', colors['surface'])
            ],
            bordercolor=[
                ('active', colors['success']),  # NEW: Border color on hover
                ('pressed', colors['success'])  # NEW: Border color on press
            ],
            relief=[
                ('active', 'groove'),  # NEW: Gives tactile feedback on hover
                ('pressed', 'sunken')  # NEW: Physical click feedback
            ]
        )
        
        # Icon Buttons      
        self.style.configure('Icon.TButton',
            background=colors['surface'],
            foreground=colors['text'],
            bordercolor=colors['secondary_accent'],
            relief="flat",
            borderwidth=1,
            padding=2)               
        
        # ----------------------------- ENTRIES -----------------------------------#
        # Entry styles
        self.style.configure('TEntry',
            fieldbackground=colors['surface'],
            foreground=colors['text'],
            bordercolor=colors['secondary_accent'],
            insertcolor=colors['text'])

        # ----------------------------- CHECKBOXES --------------------------------#
        # Checkbox styles (Normal, Status, Warning)
        self.style.configure('Normal.TCheckbutton',            
            foreground=colors['text'],
            font=("Segoe UI", 9),
            indicatorcolor=colors['primary_accent'],
            padding=(10, 5))
        
        self.style.configure('Status.TCheckbutton',            
            foreground='#28A745' if self.current_theme == 'light' else '#57D655',  # Green for status
            font=("Segoe UI", 9),
            indicatorcolor='#28A745' if self.current_theme == 'light' else '#57D655',
            padding=(10, 5))
        
        self.style.configure('Warning.TCheckbutton',            
            foreground=colors['text'],
            font=("Segoe UI", 9),
            padding=(10, 5))

        self.style.map('Warning.TCheckbutton',
        foreground=[
            ('!selected', 'black'),  # Red color when unchecked
            ('selected', '#DC3545')  # Brighter red color when checked
        ])
        
        # --------------------------- PROGRESS BARS -------------------------------#
        # Progress bar styles
        self.style.configure('Normal.Horizontal.TProgressbar',
            troughcolor=colors['surface'],
            bordercolor=colors['secondary_accent'],
            background=colors['primary_accent'],
            thickness=8,
            troughrelief="flat")

        self.style.configure('Compress.Horizontal.TProgressbar',
            troughcolor=colors['surface'],
            bordercolor=colors['secondary_accent'],
            background='#FFA500' if self.current_theme == 'light' else '#FF8C00',  # Orange shades
            thickness=8,
            lightcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            darkcolor='#FFB74D' if self.current_theme == 'light' else '#FFB74D',
            troughrelief="sunken")

        self.style.configure('Working.Horizontal.TProgressbar',
            troughcolor=colors['surface'],
            bordercolor=colors['secondary_accent'],
            background='#6CA6CD' if self.current_theme == 'light' else '#6CA6CD',  # Orange shades
            thickness=8,
            lightcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            darkcolor='#FFA500' if self.current_theme == 'light' else '#FF8C00',
            troughrelief="flat")
        
        self.style.configure("Pulse.Horizontal.TProgressbar", 
            troughcolor=colors['surface'], 
            lightcolor=colors['primary_accent'], 
            darkcolor=colors['primary_accent'])

        # ----------------------------- TEXT AREA ------------------------------- #
        # Text widget styling
        text_config = {
            'background': colors['surface'],
            'foreground': colors['text'],
            'insertbackground': colors['text'],
            'borderwidth': 1,
            'highlightthickness': 1,
            'highlightbackground': colors['secondary_accent'],
            'highlightcolor': colors['secondary_accent'],
            'selectbackground': colors['primary_accent'],
            'selectforeground': colors['surface'],
            'font': self.fonts['mono'],
            'undo': True,  # Enable undo/redo
            'maxundo': -1  # Unlimited undo steps
        } 
        
        # Apply to all existing Text widgets
        self._update_text_widgets(self, text_config)

        # Scrollbar styling
        self.style.configure('TScrollbar',            
            troughcolor=colors['surface'],
            bordercolor=colors['surface'],
            arrowcolor=colors['text'],
            activerelief='flat',
            gripcount=0,  # Remove default grip
            arrowsize=14  # Larger arrows for better visibility
        )
        self.style.map('TScrollbar',
            background=[('active', colors['primary_accent'])],
            arrowcolor=[('disabled', colors['secondary_accent'])]
        )         

    def _update_text_widgets(self, widget: tk.Widget, config: Dict[str, Any]) -> None:
        """Recursively update all Text widgets with new styling."""
        try:
            for child in widget.winfo_children():
                if isinstance(child, tk.Text):
                    try:
                        # Apply base configuration
                        child.config(**config)

                        # Configure tag for selected text
                        child.tag_configure('sel', 
                        background=config['selectbackground'],
                        foreground=config['selectforeground'])

                        # Configure scrollbar colors
                        for sb in [child['xscrollcommand'], child['yscrollcommand']]:
                            if sb and hasattr(sb, 'widget') and isinstance(sb.widget, ttk.Scrollbar):
                                sb.widget.configure(style='TScrollbar')
                    except tk.TclError as e:
                        print(f"Text widget config error: {e}")
                elif isinstance(child, ttk.Scrollbar):
                    child.configure(style='TScrollbar')
                self._update_text_widgets(child, config)
        except Exception as e:
            print(f"Error updating widgets: {e}")
    
    def toggle_theme(self, event=None):        
        """Toggle between light and dark themes."""
        THEME_ICONS = {
            'light': ('\u263C', 'Dark Theme'),  # ☼
            'dark': ('\u263E', 'Light Theme')   # ☾
        }
        
        # Add smooth transition
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'

        icon, tooltip = THEME_ICONS[self.current_theme]
        self.theme_toggle_button.config(text=icon)
        ToolTip(self.theme_toggle_button, tooltip)
        
        # Update theme toggle button
        if self.theme_toggle_button:
            self.theme_toggle_button.config(
                text="\u263E" if self.current_theme == 'dark' else "\u263C"
            )
        
        self.apply_theme()
        self.update_idletasks()  # Force immediate UI update
        self._refresh_widgets(self)        

    def _refresh_widgets(self, widget: tk.Widget) -> None:
        try:
            widget.update_idletasks()
            for child in widget.winfo_children():
                if isinstance(child, ttk.Widget):
                    try:
                        style = child.cget('style')
                        child.configure(style=style)  # Force style re-application
                    except tk.TclError as e:
                        print(f"Style error in {child}: {e}")
                self._refresh_widgets(child)
        except Exception as e:
            print(f"Refresh error: {e}")

    def view_logs(self, event=None):
        """Open the log viewer."""
        view_logs(self)

    def open_help(self, event=None):
        """Open the help window."""
        open_help(self)

