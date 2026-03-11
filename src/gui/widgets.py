from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from src.gui.theme import DROP_ZONE_DEFAULT, DROP_ZONE_HOVER, DROP_ZONE_IMAGE


class ImageDropLabel(QLabel):
    """A label that acts as a drag-and-drop zone and displays an image preview."""

    file_dropped = pyqtSignal(str)

    def __init__(self, placeholder: str = "拖拽图片到此处\n或点击选择文件", parent=None):
        super().__init__(parent)
        self._placeholder = placeholder
        self._pixmap: QPixmap | None = None
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(364, 312)
        self.setStyleSheet(DROP_ZONE_DEFAULT)
        self.setText(self._placeholder)

    def set_image(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.setStyleSheet(DROP_ZONE_IMAGE)
        self._update_display()

    def clear_image(self) -> None:
        self._pixmap = None
        self.setStyleSheet(DROP_ZONE_DEFAULT)
        self.setText(self._placeholder)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap:
            self._update_display()

    def _update_display(self):
        if self._pixmap:
            available = self.contentsRect().size()
            scaled = self._pixmap.scaled(
                available,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)

    # -- Drag & Drop --
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(DROP_ZONE_HOVER)

    def dragLeaveEvent(self, event):
        if not self._pixmap:
            self.setStyleSheet(DROP_ZONE_DEFAULT)

    def dropEvent(self, event: QDropEvent):
        if not self._pixmap:
            self.setStyleSheet(DROP_ZONE_DEFAULT)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")):
                self.file_dropped.emit(path)
