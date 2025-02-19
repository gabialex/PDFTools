# gui/merging_ops.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import logging
import subprocess  # For cross-platform file opening

from logic.merging import merge_pdfs
from .utils import ToolTip

class MergingOps:
    def __init__(self, root):
        self.root = root
        self.setup_variables()

        # Custom font
        self.font = ("Segoe UI", 10)

    def setup_variables(self):
        """Initialize variables for merging."""
        self.merge_files = []
        self.output_folder = ""
        self.merged_file_path = None

    def setup_merging_ui(self, parent):
        """Set up the merging UI."""
        self.right_frame = ttk.Frame(parent)
        self.right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # Merge Label
        self.merge_label = ttk.Label(self.right_frame, text="Merge PDF Files", style="Blue.TLabel")
        self.merge_label.pack(pady=3)

        # Select PDFs to Merge Button
        self.select_merge_files_button = ttk.Button(self.right_frame, text="Select PDFs to Merge", command=self.select_merge_files)
        self.select_merge_files_button.pack(pady=5)
        ToolTip(self.select_merge_files_button, "Select multiple PDF files to merge.")

        # Label for the number of files selected
        self.setup_files_number()

        # Option to compress files befor merging
        self.setup_compress_before_merge()

        # Setup output folder
        self.setup_output_folder_button()

        # Setup output File Name and Label
        self.entry_for_output_filename()

        # Setup Start Merging button
        self.setup_start_merging_button()

        # Progress bar and labels
        self.setup_merging_progress()

        # Current file status
        self.setup_current_merging_file()

        # Current merger status
        self.setup_current_merger_status() 

        # Open / Print merged file
        self.setup_open_or_print()

        # Show merging summary()
        #self.setup_show_merging_summary()

    def setup_files_number(self):
        #Add a label to show the number of files selected for merging
        self.merge_status_label_selected = ttk.Label(self.right_frame, text="0 PDF files selected to merge", font=self.font, wraplength=400)
        self.merge_status_label_selected.pack(pady=10)

    def setup_compress_before_merge(self):
         # --- Add Compression Level Options ---
        self.merge_compression_level_var = tk.StringVar(value="high")  # Default compression level
        self.merge_compression_frame = ttk.Frame(self.right_frame)
        self.merge_compression_frame.pack(pady=5)

        # Add a checkbox for compressing before merging
        self.compress_before_merge_var = tk.BooleanVar(value=False)
        self.compress_before_merge_checkbox = ttk.Checkbutton(
            self.right_frame,
            text="Compress  files  before  merging",
            variable=self.compress_before_merge_var,
            command=self.toggle_compress_options  # Enable/disable compression options
        )
        self.compress_before_merge_checkbox.pack(pady=5)
        ToolTip(self.compress_before_merge_checkbox, "Compress PDFs before merging them into a single file.")

        # Default compression level
        self.merge_compression_frame = ttk.Frame(self.right_frame)
        self.merge_compression_frame.pack(pady=5)

        # --- Add Compression Level Options ---
        self.merge_compression_level_var = tk.StringVar(value="high")  # Default compression level
        self.merge_compression_frame = ttk.Frame(self.right_frame)
        self.merge_compression_frame.pack(pady=5)

        # Add radio buttons for compression levels
        ttk.Radiobutton(self.merge_compression_frame, text="High", variable=self.merge_compression_level_var, value="high").pack(side="left", padx=5)
        ttk.Radiobutton(self.merge_compression_frame, text="Medium", variable=self.merge_compression_level_var, value="medium").pack(side="left", padx=5)
        ttk.Radiobutton(self.merge_compression_frame, text="Low",  variable=self.merge_compression_level_var, value="low").pack(side="left", padx=5)

        # Disable compression options by default
        self.toggle_compress_options()

        # Add a checkbox for deleting original files after merging
        self.delete_after_merge_var = tk.BooleanVar(value=False)
        self.delete_after_merge_checkbox = ttk.Checkbutton(
            self.right_frame,
            text="Delete original files after merging",
            variable=self.delete_after_merge_var
        )
        self.delete_after_merge_checkbox.pack(pady=10)
        ToolTip(self.delete_after_merge_checkbox, "Delete the original files after successful merging.")

    def toggle_compress_options(self):
        """Enable or disable the compression level options based on the checkbox state."""
        if self.compress_before_merge_var.get():
            for widget in self.merge_compression_frame.winfo_children():
                widget.config(state=tk.NORMAL)
        else:
            for widget in self.merge_compression_frame.winfo_children():
                widget.config(state=tk.DISABLED)

    def setup_output_folder_button(self):
        # Select Folder for merged PDFs
        self.select_output_folder_button = ttk.Button(self.right_frame, text="Select Output Folder", command=self.select_output_folder)
        self.select_output_folder_button.pack(pady=10)
        ToolTip(self.select_output_folder_button, "Choose the folder to save the merged PDF.")

    def entry_for_output_filename(self):
        # --- Create a frame for the Output File Name label and entry ---
        self.output_name_frame = ttk.Frame(self.right_frame)
        self.output_name_frame.pack(pady=5)

        # Add the Output File Name label to the frame
        self.output_name_label = ttk.Label(
            self.output_name_frame,
            text="Output File Name:",
            font=self.font
        )
        self.output_name_label.pack(side="left", padx=5)

        # Add the Output File Name entry to the frame
        self.output_name_var = tk.StringVar(value="enter_file_name.pdf")
        self.output_name_entry = ttk.Entry(
            self.output_name_frame,
            textvariable=self.output_name_var,
            width=20,
            font=self.font
        )
        self.output_name_entry.pack(side="left", padx=5)
        ToolTip(self.output_name_entry, "Enter the name for the merged PDF file.")

    def setup_start_merging_button(self):
        # Use the custom style for the Start Merging button
        self.start_merge_button = ttk.Button(
            self.right_frame,
            text="Start Merging",
            command=self.start_merge,
            style="Red.TButton",  # Apply the custom style
            state=tk.DISABLED  # Initially disabled
        )
        self.start_merge_button.pack(pady=10)
        ToolTip(self.start_merge_button, "Merge the selected PDF files.")

    def setup_merging_progress(self):        
        # Add a frame for the merging progress bar and percentage label
        self.merge_progress_frame = ttk.Frame(self.right_frame)
        self.merge_progress_frame.pack(pady=20)

        # Add the merging progress bar to the frame
        self.merge_progress = ttk.Progressbar(self.merge_progress_frame, orient="horizontal", length=300, mode="determinate")
        self.merge_progress.pack(side="left", padx=5, pady=10)

        # Add the percentage label to the frame
        self.merge_progress_percentage_label = ttk.Label(self.merge_progress_frame, text="0%", font=self.font)
        self.merge_progress_percentage_label.pack(side="left", padx=5)

    def setup_current_merging_file(self):
        # Add a label to show the current file being merged
        self.current_merge_file_label = ttk.Label(self.right_frame, text="Current File: None", font=self.font, wraplength=400)
        self.current_merge_file_label.pack(pady=10)

    def setup_current_merger_status(self):
        # Add a status label for the merging process
        self.merge_status_label = ttk.Label(self.right_frame, text="Waiting to start...", font=self.font, wraplength=400)
        self.merge_status_label.pack(pady=10)

    def setup_open_or_print(self):
        # --- Create a frame for the Open Merged File and Print Merged File buttons ---
        self.merged_file_buttons_frame = ttk.Frame(self.right_frame)
        self.merged_file_buttons_frame.pack(pady=10)

        # Add the Open Merged File button to the frame
        self.open_merged_file_button = ttk.Button(
            self.merged_file_buttons_frame,
            text="Open Merged File",
            command=self.open_merged_file,
            state=tk.DISABLED  # Disabled by default
        )
        self.open_merged_file_button.pack(side="left", padx=5)
        ToolTip(self.open_merged_file_button, "Open the merged PDF file in your default PDF viewer.")

        # Add the Print Merged File button to the frame
        self.print_merged_file_button = ttk.Button(
            self.merged_file_buttons_frame,
            text="Print Merged File",
            command=self.print_merged_file,
            state=tk.DISABLED  # Disabled by default
        )
        self.print_merged_file_button.pack(side="left", padx=5)
        ToolTip(self.print_merged_file_button, "Print the merged PDF file using your default printer.")

    def show_merging_summary(self, title, message):
        dialog = tk.Toplevel()
        dialog.title(title)

        # Configure custom font
        custom_font = ('Segoe UI', 10)
        
        # Create scrolled text widget
        text_area = scrolledtext.ScrolledText(dialog, width=50, height=40, font=custom_font)
        text_area.pack(padx=10, pady=10, expand=True, fill='both')
        
        # Insert the message and make it read-only
        text_area.insert('1.0', message)
        text_area.configure(state='disabled')
        
        # Add OK button to close
        ok_button = tk.Button(dialog, text="OK", command=dialog.destroy, font=custom_font)
        ok_button.pack(pady=5)
        
        # Make dialog modal
        dialog.transient()
        dialog.grab_set()
        dialog.wait_window()

    # Function to select PDFs to merge
    def select_merge_files(self):
        files = filedialog.askopenfilenames(title="Select PDF Files to Merge", filetypes=[("PDF files", "*.pdf")])
        if files:
            self.merge_files = list(files)
            self.merge_status_label_selected.config(text=f"{len(self.merge_files)} PDF files selected to merge")
            self.start_merge_button.config(state=tk.NORMAL)

    # Function to select output folder for merged PDF
    def select_output_folder(self):
        self.output_folder = filedialog.askdirectory(title="Select Output Folder")
        if self.output_folder:
            self.merge_status_label.config(text=f"Output folder: {self.output_folder}")

    # Function to start merging
    def start_merge(self):
        if not self.merge_files:
            messagebox.showwarning("No Files", "No PDF files selected to merge.")
            return
        
        # Add validation for output filename
        if not self.output_name_var.get().endswith(".pdf"):
            messagebox.showerror("Invalid Name", "Output file must end with .pdf")
            return

        # Check if the user has chosen an output folder
        if not self.output_folder:
            # If no output folder is chosen, use the folder of the first file
            first_file = self.merge_files[0]
            default_output_folder = os.path.dirname(first_file)
            
            # Ask the user if they want to proceed with the default folder or cancel
            use_default = messagebox.askokcancel(
                "No Output Folder",
                f"No output folder selected.\n"
                f"Files will be merged into the folder of the original files:\n{default_output_folder}\n\n"
                "Do you want to continue?"
            )

            # If the user clicks "Cancel", stop the process and let them choose an output folder
            if not use_default:
                return  # User can go back and choose an output folder
            
            # Proceed with the default folder
            output_folder = default_output_folder
        else:
            # Use the user-specified output folder
            output_folder = self.output_folder        

        # Create the full output file path and add overwrite protection
        output_file = os.path.join(output_folder, self.output_name_var.get())
        if os.path.exists(output_file):
            if not messagebox.askyesno("Overwrite?", f"{output_file} already exists. Overwrite?"):
                return        
        self.merged_file_path = output_file  # Store the merged file path

        # Disable the Start Merging button
        self.start_merge_button.config(state=tk.DISABLED)        

        # Reset the progress bar and labels
        self.merge_progress["value"] = 0
        self.merge_progress["maximum"] = len(self.merge_files)
        self.current_merge_file_label.config(text="Current File: None")
        self.merge_status_label.config(text="Starting merging process...")

        # Start the merging process in a separate thread
        threading.Thread(target=self.merge_files_thread, args=(output_file,), daemon=True).start()

    def merge_files_thread(self, output_file):
        """Thread function to handle the merging process."""
        try:
            # Initialize progress
            self.root.after(0, lambda: self.merge_progress.config(maximum=len(self.merge_files)))
            # Get the compression option from the checkbox
            compress_before_merge = self.compress_before_merge_var.get()

            # Call the updated merge_pdfs function
            success, summary_message, error_message = merge_pdfs(
                self.merge_files,
                output_file,
                compress_before_merge=compress_before_merge,
                compression_level=self.merge_compression_level_var.get(),  # Use the selected compression level
                update_callback=self.update_merge_progress  # Pass the callback for progress updates
            )

            if success:
                # Show the summary in a messagebox                
                self.show_merging_summary(
                    "Merge Successful",
                    f"Merged PDF saved to {output_file}\n\n"
                    f"Summary:\n{summary_message}"
                )                

                # Enable the "Open Merged File" and "Print Merged File" buttons
                self.open_merged_file_button.config(state=tk.NORMAL)
                self.print_merged_file_button.config(state=tk.NORMAL)

                # Delete original files if the option is enabled
                if self.delete_after_merge_var.get():
                    confirm = messagebox.askyesno(
                        "Confirm Deletion",
                        f"Permanently delete {len(self.merge_files)} original files?")
                    if not confirm:
                        return
                    
                    deleted_files = []
                    failed_deletions = []
                    for file in self.merge_files:
                        try:
                            os.remove(file)
                            deleted_files.append(file)
                        except Exception as e:
                            failed_deletions.append(f"{file}: {str(e)}")

                    # Show a messagebox with deletion results
                    deletion_summary = []
                    if deleted_files:
                        deletion_summary.append("Deleted files:\n" + "\n".join(deleted_files))
                    if failed_deletions:
                        deletion_summary.append("\nFailed to delete:\n" + "\n".join(failed_deletions))

                    if deletion_summary:
                        self.show_merging_summary(
                            "Deletion Summary",
                            "\n".join(deletion_summary)                        
                        )
                        logging.info("\n" + "\n".join(deletion_summary)) 
            else:
                messagebox.showerror("Merge Failed", f"Error: {error_message}")
                logging.info(f"Merge Failed. Error: {error_message}")                
        finally:
            # Re-enable the Start Merging button and disable the Cancel button
            self.start_merge_button.config(state=tk.DISABLED)

    def update_merge_progress(self, current_file, progress):
        """Callback function to update the progress bar and labels."""
        # Limit the length of the displayed file name to a maximum of 30 characters
        max_length = 32
        file_name = os.path.basename(current_file)
        if len(file_name) > max_length:
            file_name = f"{file_name[:max_length]}..."

        # Update the current file label
        self.current_merge_file_label.config(text=f"Current File: {file_name}")

        # Update the progress bar
        self.merge_progress["value"] = progress

        # Update the percentage label
        progress_percentage = int((progress / len(self.merge_files)) * 100)
        self.merge_progress_percentage_label.config(text=f"{progress_percentage}%")

        # Update the status label
        self.merge_status_label.config(text=f"Merging file {progress} of {len(self.merge_files)}")

        # Refresh the GUI
        self.root.update_idletasks()

    def open_merged_file(self):
        if not self.merged_file_path:
            return
            
        try:
            if os.name == 'nt':
                os.startfile(self.merged_file_path)
            else:
                subprocess.run(['xdg-open', self.merged_file_path])
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Open Failed", 
                f"Could not open file: {str(e)}\n\nFile location: {self.merged_file_path}"
            ))

    def print_merged_file(self):
        """Cross-platform printing using default system handler"""
        if not self.merged_file_path or not os.path.exists(self.merged_file_path):
            messagebox.showwarning("Error", "Merged file not found")
            return

        try:
            if os.name == 'nt':
                os.startfile(self.merged_file_path, "print")
            else:
                subprocess.run(["lp", self.merged_file_path])
            messagebox.showinfo("Print", "File sent to default printer")
        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print file: {str(e)}")

    