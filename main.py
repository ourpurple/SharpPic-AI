import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.utils import config
from src.gui.theme import APP_STYLESHEET
from src.gui.main_window import MainWindow
from src.gui.settings_dialog import SettingsDialog

__version__ = "0.1.0"


def _resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def main():
    config.load()

    app = QApplication(sys.argv)
    app.setApplicationName("SharpPic-AI")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(_resource_path(os.path.join("src", "icon.ico"))))
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    # First-run: open settings if API key is not configured
    if not config.get("api_key"):
        dlg = SettingsDialog(window)
        dlg.exec()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
