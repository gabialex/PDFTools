# logic/log_viewer.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

def view_logs(parent_window):
    """Open log viewer window with filtering capabilities."""
    log_window = tk.Toplevel(parent_window)
    log_window.title("Operations Logs")
    log_window.geometry("1200x1200")
    
    # Create main container
    main_frame = ttk.Frame(log_window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Filter controls
    filter_frame = ttk.Frame(main_frame)
    filter_frame.pack(fill="x", pady=5)
    
    # Filter components
    keyword_var = tk.StringVar()
    type_var = tk.StringVar(value="All")
    date_var = tk.StringVar()

    ttk.Label(filter_frame, text="Filter by Keyword:").pack(side="left", padx=5)
    ttk.Entry(filter_frame, textvariable=keyword_var, width=25).pack(side="left", padx=5)

    ttk.Label(filter_frame, text="Type:").pack(side="left", padx=5)
    type_combo = ttk.Combobox(filter_frame, textvariable=type_var, 
                            values=["All", "INFO", "ERROR", "WARNING"], state="readonly")
    type_combo.pack(side="left", padx=5)

    ttk.Label(filter_frame, text="Date (YYYY-MM-DD):").pack(side="left", padx=5)
    ttk.Entry(filter_frame, textvariable=date_var, width=12).pack(side="left", padx=5)

    # Log display area
    log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=("Consolas", 10))
    log_text.pack(fill="both", expand=True)

    # Control buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    ttk.Button(button_frame, text="Apply Filters",
              command=lambda: refresh_logs(log_text, keyword_var, type_var, date_var)).pack(side="left", padx=5)
    
    ttk.Button(button_frame, text="Refresh All",
              command=lambda: refresh_logs(log_text)).pack(side="left", padx=5)
    
    ttk.Button(button_frame, text="Clear Logs",
              command=lambda: clear_logs(log_text)).pack(side="left", padx=5)

    # Initial load
    refresh_logs(log_text)
    
    # Start auto-refresh
    log_window.after(30000, auto_refresh, log_window, log_text, keyword_var, type_var, date_var)

def refresh_logs(log_widget, keyword_var=None, type_var=None, date_var=None):
    """Load and display logs with current filters."""
    try:
        with open("compression_log.txt", "r") as f:
            logs = f.read()
    except FileNotFoundError:
        logs = "No log file found"
        log_widget.delete(1.0, tk.END)
        log_widget.insert(tk.END, logs)
        return

    # Apply filters
    if keyword_var or type_var or date_var:
        filtered = []
        for line in logs.split("\n"):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Keyword filter
            if keyword_var and keyword_var.get().lower() not in line.lower():
                continue
                
            # Type filter
            if type_var and type_var.get() != "All" and type_var.get() not in line:
                continue
                
            # Date filter
            if date_var and date_var.get():
                try:
                    if line.split()[0] != date_var.get():
                        continue
                except IndexError:
                    continue
                    
            filtered.append(line + "\n")
            
        logs = "".join(filtered)

    # Update display
    log_widget.config(state=tk.NORMAL)
    log_widget.delete(1.0, tk.END)
    log_widget.insert(tk.END, logs or "No matching entries")
    log_widget.config(state=tk.DISABLED)
    log_widget.see(tk.END)

def auto_refresh(window, log_widget, keyword_var, type_var, date_var):
    """Handle periodic refresh if window still exists."""
    if window.winfo_exists():
        refresh_logs(log_widget, keyword_var, type_var, date_var)
        window.after(30000, auto_refresh, window, log_widget, keyword_var, type_var, date_var)

def clear_logs(log_widget):
    """Clear log file and refresh display."""
    if messagebox.askyesno("Confirm", "Delete all logs permanently?"):
        try:
            with open("compression_log.txt", "w") as f:
                f.write("")
            refresh_logs(log_widget)
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear logs: {str(e)}")