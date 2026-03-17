from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QContextMenuEvent, QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import QLabel, QMenu, QSizePolicy

from src.gui.theme import DROP_ZONE_DEFAULT, DROP_ZONE_HOVER, DROP_ZONE_IMAGE


class ImageDropLabel(QLabel):
    """A label that acts as a drag-and-drop zone and displays an image preview."""

    file_dropped = pyqtSignal(str)
    save_requested = pyqtSignal()  # Signal for save action

    def __init__(self, placeholder: str = "拖拽图片到此处\n或点击选择文件", parent=None, enable_context_menu: bool = False):
        super().__init__(parent)
        self._placeholder = placeholder
        self._pixmap: QPixmap | None = None
        self._enable_context_menu = enable_context_menu
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
        # Force-remove any previously rendered pixmap and repaint immediately.
        self.setPixmap(QPixmap())
        self.clear()
        self.setStyleSheet(DROP_ZONE_DEFAULT)
        self.setText(self._placeholder)
        self.update()
        self.repaint()

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

    # -- Context Menu --
    def contextMenuEvent(self, event: QContextMenuEvent):
        if not self._enable_context_menu or not self._pixmap:
            return

        menu = QMenu(self)

        save_action = QAction("另存为...", self)
        save_action.triggered.connect(self.save_requested.emit)
        menu.addAction(save_action)

        copy_action = QAction("复制图片", self)
        copy_action.triggered.connect(self._copy_image)
        menu.addAction(copy_action)

        menu.exec(event.globalPos())

    def _copy_image(self):
        """Copy the current image to clipboard."""
        if self._pixmap:
            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self._pixmap)
