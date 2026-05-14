import sys
from PyQt5 import QtWidgets
from GUI.main_window import MainWindow

def main() -> None:
    """Entry point for the GUI application."""
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()