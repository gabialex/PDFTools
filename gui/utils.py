# gui/utils.py
import tkinter as tk
from tkinter import ttk

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

# Optional: Add styles for theme consistency (called once during GUI setup)
def configure_tooltip_styles(style: ttk.Style):
    style.configure("Tooltip.TFrame", background="#333333", borderwidth=1)
    style.configure("Tooltip.TLabel", background="#333333", foreground="white")