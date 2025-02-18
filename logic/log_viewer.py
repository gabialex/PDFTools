import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def view_logs(root):
    """Open a new window to display the content of compression_log.txt."""
    log_window = tk.Toplevel(root)
    log_window.title("Operations Logs")
    log_window.geometry("1000x800")  # Increased size for better readability
    log_window.resizable(True, True)
    

    # Add a label for the title
    title_label = ttk.Label(log_window, text="Compression and Merging Logs", font=("Segoe UI", 12, "bold"))
    title_label.pack(pady=10)

    # Add a frame for filter controls
    filter_frame = ttk.Frame(log_window)
    filter_frame.pack(pady=10)

    # Add a filter by keyword entry
    keyword_label = ttk.Label(filter_frame, text="Filter by Keyword:")
    keyword_label.pack(side="left", padx=5)
    keyword_entry = ttk.Entry(filter_frame, width=20)
    keyword_entry.pack(side="left", padx=5)

    # Add a filter by type dropdown
    type_label = ttk.Label(filter_frame, text="Filter by Type:")
    type_label.pack(side="left", padx=5)
    type_var = tk.StringVar(value="All")
    type_dropdown = ttk.Combobox(filter_frame, textvariable=type_var, values=["All", "Info", "Error"], state="readonly")
    type_dropdown.pack(side="left", padx=5)

    # Add a filter by date entry
    date_label = ttk.Label(filter_frame, text="Filter by Date (YYYY-MM-DD):")
    date_label.pack(side="left", padx=5)
    date_entry = ttk.Entry(filter_frame, width=15)
    date_entry.pack(side="left", padx=5)

    # Add a button to apply filters
    apply_filter_button = ttk.Button(filter_frame, text="Apply Filters", command=lambda: refresh_logs(log_text, keyword_entry.get(), type_var.get(), date_entry.get()))
    apply_filter_button.pack(side="left", padx=5)

    # Add a frame for the log text and scrollbar
    log_frame = ttk.Frame(log_window)
    log_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Add a text widget to display the log content
    log_text = tk.Text(log_frame, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
    log_text.pack(side="left", fill="both", expand=True)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    scrollbar.pack(side="right", fill="y")
    log_text.config(yscrollcommand=scrollbar.set)

    # Add a frame for buttons
    button_frame = ttk.Frame(log_window)
    button_frame.pack(pady=10)

    # Add a button to clear the logs
    clear_button = ttk.Button(button_frame, text="Clear Logs", command=lambda: clear_logs(log_text))
    clear_button.pack(side="left", padx=5)

    # Add a button to refresh the logs manually
    refresh_button = ttk.Button(button_frame, text="Refresh", command=lambda: refresh_logs(log_text, keyword_entry.get(), type_var.get(), date_entry.get()))
    refresh_button.pack(side="left", padx=5)

    # Start auto-refresh
    refresh_logs(log_text)  # Initial refresh
    auto_refresh(log_window, log_text, keyword_entry, type_var, date_entry)  # Start auto-refresh loop

def refresh_logs(log_text_widget, keyword="", log_type="All", date_filter=""):
    """Refresh the content of the log viewer with applied filters."""
    try:
        with open("compression_log.txt", "r") as log_file:
            log_lines = log_file.readlines()
    except FileNotFoundError:
        log_lines = ["No log file found."]

    filtered_logs = []
    for line in log_lines:
        # Apply keyword filter
        if keyword.lower() not in line.lower():
            continue

        # Apply type filter
        if log_type != "All" and log_type.lower() not in line.lower():
            continue

        # Apply date filter
        if date_filter:
            try:
                # Extract the date part from the log entry (first 10 characters: YYYY-MM-DD)
                log_date = line.split(" - ")[0][:10]  # Extract the date part
                if log_date != date_filter:
                    continue
            except (IndexError, ValueError):
                continue  # Skip if the log entry doesn't match the expected format

        filtered_logs.append(line)

    log_text_widget.config(state="normal")
    log_text_widget.delete("1.0", "end")
    log_text_widget.insert("1.0", "".join(filtered_logs))
    log_text_widget.config(state="disabled")

    # Scroll to the end of the log
    log_text_widget.see("end")

def auto_refresh(log_window, log_text_widget, keyword_entry, type_var, date_entry, interval=60000):
    """Automatically refresh the log viewer every `interval` milliseconds."""
    refresh_logs(log_text_widget, keyword_entry.get(), type_var.get(), date_entry.get())
    log_window.after(interval, auto_refresh, log_window, log_text_widget, keyword_entry, type_var, date_entry, interval)  # Schedule the next refresh

def clear_logs(log_text_widget=None):
    """Clear the content of compression_log.txt."""
    try:
        with open("compression_log.txt", "w") as log_file:
            log_file.write("")  # Clear the file
        if log_text_widget:
            refresh_logs(log_text_widget)  # Refresh the log viewer
        messagebox.showinfo("Success", "Logs cleared successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to clear logs: {e}")