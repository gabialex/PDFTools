PDF Tools

Overview

PDF Tools is a Python-based application that provides functionality for handling PDF files. It includes features such as compressing PDFs and merging multiple PDFs into a single file. The application offers a graphical user interface (GUI) built using Tkinter, allowing users to easily perform these operations without command-line interaction.

Features
- PDF Compression: Reduce the size of PDF files to save space.
- PDF Merging: Combine multiple PDF documents into a single file.
- User-friendly GUI: Intuitive interface for performing file operations with minimal effort.

Installation
Requirements
- Python 3.7 or higher
- The following Python libraries:
  - tkinter (included with most Python distributions)
  - Pillow (for handling images in PDFs)
  - PyPDF2 (for working with PDF files)
  - ttkbootstrap (optional for modern GUI themes)

Installation Steps
1. Clone the repository:
git clone https://github.com/gabialex/PDFTools.git
2. Navigate to the project directory:
cd PDFTools
3. Install the required Python libraries:
pip install -r requirements.txt

Usage
1. Run the application:
python main.py
2. Once the GUI opens, you will have options to:
- Compress PDFs: Select a PDF file to reduce its size.
- Merge PDFs: Choose multiple PDFs to combine into a single file.
3. Use the "Help" button for detailed instructions on each feature.

File Structure
- main.py: The entry point for the application.
- gui/: Contains the GUI components such as main_window.py, which sets up the main window.
- logic/: Contains the core logic for operations like compression and merging.
- utils.py: Contains utility functions and tooltip configurations.
- logs/: Logs of application actions and errors.
  
Contributions are welcome! Feel free to submit a pull request with any improvements or bug fixes.
