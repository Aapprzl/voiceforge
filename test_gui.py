import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

def main():
    try:
        print("Creating QApplication...")
        app = QApplication(sys.argv)
        print("Creating MainWindow...")
        window = QMainWindow()
        window.setWindowTitle("Test")
        label = QLabel("Hello World", window)
        window.setCentralWidget(label)
        print("Showing window...")
        window.show()
        print("Starting exec loop (5 seconds timeout)...")
        # Exit after 5 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(5000, app.quit)
        sys.exit(app.exec())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
