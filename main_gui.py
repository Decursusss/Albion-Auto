import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

app = QApplication(sys.argv)

with open("gui/style.qss", "r") as f:
    app.setStyleSheet(f.read())

window = MainWindow()
window.show()

sys.exit(app.exec())
