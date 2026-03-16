import datetime
import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.gui.settings_dialog import SettingsDialog
from src.gui.widgets import ImageDropLabel
from src.utils import config
from src.utils.image_utils import base64_to_pil, base64_to_qpixmap, save_image
from src.version import APP_VERSION


class ProcessWorker(QThread):
    """Worker thread for streaming image processing via API."""

    text_chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, image_path: str, color_mode: str = "grayscale"):
        super().__init__()
        self._image_path = image_path
        self._color_mode = color_mode

    def run(self):
        try:
            from src.api.client import process_image_stream

            result = process_image_stream(
                self._image_path,
                on_text=self.text_chunk.emit,
                color_mode=self._color_mode,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionLabel")
    return label


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"SharpPic-AI V{APP_VERSION}")
        self.setMinimumSize(1248, 832)
        self._source_path: str | None = None
        self._result_b64: str | None = None
        self._worker: ProcessWorker | None = None
        self._build_ui()

    def _build_ui(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)

        title = QLabel("  SharpPic-AI")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #00D4AA; padding-right: 16px;")
        toolbar.addWidget(title)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred,
        )
        toolbar.addWidget(spacer)

        settings_action = QAction("  设置  ", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)
        self.addToolBar(toolbar)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(5, 0, 10, 0)
        left_layout.setSpacing(10)

        left_layout.addWidget(_section_label("原始图片"))

        self._source_label = ImageDropLabel(
            "拖拽图片到此处\n\n点击下方按钮选择文件\n或使用 Ctrl+V 粘贴"
        )
        self._source_label.file_dropped.connect(self._on_file_dropped)
        self._source_label.setMinimumSize(280, 200)
        left_layout.addWidget(self._source_label, 3)

        select_btn = QPushButton("选择文件")
        select_btn.setObjectName("compactBtn")
        select_btn.clicked.connect(self._select_file)
        left_layout.addWidget(select_btn)

        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self._paste_from_clipboard)

        self._color_checkbox = QCheckBox("生成彩图")
        self._color_checkbox.setChecked(False)
        left_layout.addWidget(self._color_checkbox)

        self._process_btn = QPushButton("开始处理")
        self._process_btn.setObjectName("primaryBtn")
        self._process_btn.clicked.connect(self._start_process)
        left_layout.addWidget(self._process_btn)

        left_layout.addWidget(_section_label("实时信息"))

        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText("模型输出将在此处实时显示...")
        left_layout.addWidget(self._output_text, 2)

        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(10, 0, 5, 0)
        right_layout.setSpacing(10)

        right_layout.addWidget(_section_label("处理结果"))

        self._result_label = ImageDropLabel("处理后的图片将显示在此处", enable_context_menu=True)
        self._result_label.setAcceptDrops(False)
        self._result_label.save_requested.connect(self._save_result)
        right_layout.addWidget(self._result_label, 1)

        self._save_btn = QPushButton("保存图片")
        self._save_btn.setObjectName("successBtn")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_result)
        right_layout.addWidget(self._save_btn)

        splitter.addWidget(right)
        splitter.setSizes([420, 780])

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("就绪")

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*)",
        )
        if path:
            self._load_source(path)

    def _on_file_dropped(self, path: str):
        self._load_source(path)

    def _paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mimedata = clipboard.mimeData()

        if mimedata.hasUrls():
            for url in mimedata.urls():
                path = url.toLocalFile()
                if path and path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")):
                    self._load_source(path)
                    return

        if mimedata.hasImage():
            pixmap = QPixmap(clipboard.pixmap())
            if pixmap.isNull():
                return
            tmp_dir = Path(tempfile.gettempdir()) / "sharppic"
            tmp_dir.mkdir(exist_ok=True)
            tmp_path = str(tmp_dir / f"paste_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            pixmap.save(tmp_path, "PNG")
            self._source_path = tmp_path
            self._source_label.set_image(pixmap)
            self._status.showMessage("已从剪贴板粘贴图片")
            self._result_label.clear_image()
            self._result_b64 = None
            self._save_btn.setEnabled(False)

    def _load_source(self, path: str):
        self._source_path = path
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法加载图片文件")
            return
        self._source_label.set_image(pixmap)
        self._status.showMessage(f"已加载: {os.path.basename(path)}")
        self._result_label.clear_image()
        self._result_b64 = None
        self._save_btn.setEnabled(False)

    def _start_process(self):
        if not self._source_path:
            QMessageBox.information(self, "提示", "请先选择一张图片")
            return

        provider = config.get("api_provider") or "openai"
        if provider == "gmicloud":
            if not config.get("gmi_api_key"):
                QMessageBox.warning(self, "提示", "请先在设置中配置 gmicloud API Key")
                self._open_settings()
                return
        else:
            if not config.get("api_key"):
                QMessageBox.warning(self, "提示", "请先在设置中配置 API Key")
                self._open_settings()
                return

        self._set_processing(True)
        self._output_text.clear()
        self._status.showMessage("正在处理图片，请稍候...")

        color_mode = "color" if self._color_checkbox.isChecked() else "grayscale"
        self._worker = ProcessWorker(self._source_path, color_mode=color_mode)
        self._worker.text_chunk.connect(self._on_text_chunk)
        self._worker.finished.connect(self._on_process_done)
        self._worker.error.connect(self._on_process_error)
        self._worker.start()

    def _on_text_chunk(self, text: str):
        cursor = self._output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self._output_text.setTextCursor(cursor)
        self._output_text.ensureCursorVisible()

    def _on_process_done(self, b64_data: str):
        self._set_processing(False)
        self._result_b64 = b64_data
        pixmap = base64_to_qpixmap(b64_data)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法解析返回的图片数据")
            self._status.showMessage("处理失败：图片数据无效")
            return
        self._result_label.set_image(pixmap)
        self._save_btn.setEnabled(True)
        self._status.showMessage("处理完成")

    def _on_process_error(self, msg: str):
        self._set_processing(False)
        QMessageBox.critical(self, "处理失败", msg)
        self._status.showMessage("处理失败")

    def _set_processing(self, busy: bool):
        self._process_btn.setEnabled(not busy)
        self._process_btn.setText("处理中..." if busy else "开始处理")

    def _save_result(self):
        if not self._result_b64:
            return

        save_dir = config.get("save_directory")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"sharppic_{timestamp}.png"
        default_path = str(Path(save_dir) / default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图片",
            default_path,
            "PNG (*.png);;JPEG (*.jpg);;所有文件 (*)",
        )
        if not path:
            return

        try:
            pil_image = base64_to_pil(self._result_b64)
            save_image(pil_image, path)
            self._status.showMessage(f"已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
