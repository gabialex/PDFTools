# main.py
from gui.main_window import MainWindow
import traceback

if __name__ == "__main__":
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()  # Print stack trace for debugging