import os
import sys

from PySide6.QtWidgets import QApplication

from crafting.gui import CraftingWindow

app = QApplication(sys.argv)

style = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "style.qss")
if os.path.exists(style):
    with open(style, "r") as f:
        app.setStyleSheet(f.read())

window = CraftingWindow()
window.show()

sys.exit(app.exec())
