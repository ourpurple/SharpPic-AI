import datetime
import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
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

GEN_ASPECT_RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16", "21:9"]
GEN_STYLES = ["写实", "动漫", "插画", "电影感", "极简", "赛博朋克", "自定义"]
GEN_RESOLUTIONS = ["1K", "2K", "4K"]
GEN_COLOR_MODES = ["彩色图", "灰度图"]


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


class GenerateWorker(QThread):
    """Worker thread for text-to-image generation via API."""

    text_chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        prompt: str,
        color_mode: str,
        resolution: str,
        aspect_ratio: str,
        style: str,
        custom_style: str,
    ):
        super().__init__()
        self._prompt = prompt
        self._color_mode = color_mode
        self._resolution = resolution
        self._aspect_ratio = aspect_ratio
        self._style = style
        self._custom_style = custom_style

    def run(self):
        try:
            from src.api.client import generate_image_stream

            result = generate_image_stream(
                prompt=self._prompt,
                on_text=self.text_chunk.emit,
                color_mode=self._color_mode,
                resolution=self._resolution,
                aspect_ratio=self._aspect_ratio,
                style=self._style,
                custom_style=self._custom_style,
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
        self._gen_result_b64: str | None = None

        self._worker: ProcessWorker | None = None
        self._gen_worker: GenerateWorker | None = None

        self._build_ui()

    def _build_ui(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)

        title = QLabel("SharpPic-AI")
        title.setObjectName("appTitle")
        toolbar.addWidget(title)

        subtitle = QLabel("AI 图像增强与生成工作台")
        subtitle.setObjectName("toolbarMeta")
        toolbar.addWidget(subtitle)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred,
        )
        toolbar.addWidget(spacer)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)
        self.addToolBar(toolbar)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 10)

        self._tabs = QTabWidget()
        main_layout.addWidget(self._tabs)

        self._edit_tab = self._build_edit_tab()
        self._gen_tab = self._build_generate_tab()

        self._tabs.addTab(self._edit_tab, "修图")
        self._tabs.addTab(self._gen_tab, "生图")

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("就绪")

    def _build_edit_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left = QWidget()
        left.setObjectName("panelCard")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        left_layout.addWidget(_section_label("原始图片"))

        self._source_label = ImageDropLabel("拖拽图片到此处\n\n点击下方按钮选择文件\n或使用 Ctrl+V 粘贴")
        self._source_label.file_dropped.connect(self._on_file_dropped)
        self._source_label.setMinimumSize(280, 200)
        left_layout.addWidget(self._source_label, 3)

        select_btn = QPushButton("选择文件")
        select_btn.setObjectName("compactBtn")
        select_btn.clicked.connect(self._select_file)
        left_layout.addWidget(select_btn)

        source_hint = QLabel("支持 PNG/JPG/BMP/GIF/WEBP，建议上传清晰原图以获得更好效果。")
        source_hint.setObjectName("hintText")
        left_layout.addWidget(source_hint)

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
        right.setObjectName("panelCard")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 14, 14, 14)
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
        splitter.setChildrenCollapsible(False)

        return page

    def _build_generate_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left = QWidget()
        left.setObjectName("panelCard")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        left_layout.addWidget(_section_label("提示词"))

        self._gen_prompt_input = QTextEdit()
        self._gen_prompt_input.setPlaceholderText("请输入提示词，例如：一只在雨夜街头打伞的猫，电影感光影")
        self._gen_prompt_input.setMinimumHeight(210)
        left_layout.addWidget(self._gen_prompt_input, 3)

        prompt_hint = QLabel("建议包含：主体 + 场景 + 光线 + 构图 + 风格关键词。")
        prompt_hint.setObjectName("hintText")
        left_layout.addWidget(prompt_hint)

        left_layout.addWidget(_section_label("生成参数"))

        self._gen_color_mode = QComboBox()
        self._gen_color_mode.addItems(GEN_COLOR_MODES)
        self._gen_color_mode.setCurrentText(config.get("gen_color_mode") or "彩色图")

        self._gen_resolution = QComboBox()
        self._gen_resolution.addItems(GEN_RESOLUTIONS)
        self._gen_resolution.setCurrentText(config.get("gen_resolution") or "1K")

        self._gen_aspect_ratio = QComboBox()
        self._gen_aspect_ratio.addItems(GEN_ASPECT_RATIOS)
        self._gen_aspect_ratio.setCurrentText(config.get("gen_aspect_ratio") or "1:1")

        self._gen_style = QComboBox()
        self._gen_style.addItems(GEN_STYLES)
        self._gen_style.setCurrentText(config.get("gen_style") or "写实")
        self._gen_style.currentTextChanged.connect(self._on_gen_style_changed)

        self._gen_custom_style = QLineEdit()
        self._gen_custom_style.setPlaceholderText("当选择“自定义”时输入风格描述")
        self._gen_custom_style.setText(config.get("gen_custom_style") or "")

        params_grid = QGridLayout()
        params_grid.setHorizontalSpacing(12)
        params_grid.setVerticalSpacing(8)

        params_grid.addWidget(QLabel("色彩模式"), 0, 0)
        params_grid.addWidget(self._gen_color_mode, 0, 1)
        params_grid.addWidget(QLabel("分辨率"), 0, 2)
        params_grid.addWidget(self._gen_resolution, 0, 3)

        params_grid.addWidget(QLabel("宽高比"), 1, 0)
        params_grid.addWidget(self._gen_aspect_ratio, 1, 1)
        params_grid.addWidget(QLabel("图片风格"), 1, 2)
        params_grid.addWidget(self._gen_style, 1, 3)

        params_grid.setColumnStretch(1, 1)
        params_grid.setColumnStretch(3, 1)
        left_layout.addLayout(params_grid)

        self._custom_style_row = self._form_row("自定义风格", self._gen_custom_style)
        left_layout.addLayout(self._custom_style_row)

        self._gen_btn = QPushButton("开始生成")
        self._gen_btn.setObjectName("primaryBtn")
        self._gen_btn.clicked.connect(self._start_generate)
        left_layout.addWidget(self._gen_btn)

        left_layout.addWidget(_section_label("实时信息"))

        self._gen_output_text = QTextEdit()
        self._gen_output_text.setReadOnly(True)
        self._gen_output_text.setPlaceholderText("生图过程信息将在此处实时显示...")
        left_layout.addWidget(self._gen_output_text, 2)

        splitter.addWidget(left)

        right = QWidget()
        right.setObjectName("panelCard")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        right_layout.addWidget(_section_label("生成结果"))

        self._gen_result_label = ImageDropLabel("生成后的图片将显示在此处", enable_context_menu=True)
        self._gen_result_label.setAcceptDrops(False)
        self._gen_result_label.save_requested.connect(self._save_generated_result)
        right_layout.addWidget(self._gen_result_label, 1)

        self._gen_save_btn = QPushButton("保存图片")
        self._gen_save_btn.setObjectName("successBtn")
        self._gen_save_btn.setEnabled(False)
        self._gen_save_btn.clicked.connect(self._save_generated_result)
        right_layout.addWidget(self._gen_save_btn)

        splitter.addWidget(right)
        splitter.setSizes([420, 780])
        splitter.setChildrenCollapsible(False)

        self._on_gen_style_changed(self._gen_style.currentText())
        return page

    def _form_row(self, label_text: str, field_widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(70)
        row.addWidget(label)
        row.addWidget(field_widget, 1)
        return row

    def _on_gen_style_changed(self, style: str):
        is_custom = style == "自定义"
        self._gen_custom_style.setEnabled(is_custom)
        for i in range(self._custom_style_row.count()):
            item = self._custom_style_row.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                widget.setVisible(is_custom)

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
        self._result_label.clear_image()
        self._result_label.repaint()
        self._result_b64 = None
        self._save_btn.setEnabled(False)
        self._status.showMessage("正在处理图片，请稍候...")

        color_mode = "color" if self._color_checkbox.isChecked() else "grayscale"
        self._worker = ProcessWorker(self._source_path, color_mode=color_mode)
        self._worker.text_chunk.connect(self._on_text_chunk)
        self._worker.finished.connect(self._on_process_done)
        self._worker.error.connect(self._on_process_error)
        self._worker.start()

    def _start_generate(self):
        prompt = self._gen_prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.information(self, "提示", "请输入提示词")
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

        style = self._gen_style.currentText()
        custom_style = self._gen_custom_style.text().strip()
        if style == "自定义" and not custom_style:
            QMessageBox.information(self, "提示", "选择自定义风格时，请填写风格描述")
            return

        color_mode = self._gen_color_mode.currentText()
        resolution = self._gen_resolution.currentText()
        aspect_ratio = self._gen_aspect_ratio.currentText()

        config.set("gen_color_mode", color_mode)
        config.set("gen_resolution", resolution)
        config.set("gen_aspect_ratio", aspect_ratio)
        config.set("gen_style", style)
        config.set("gen_custom_style", custom_style)
        config.save()

        self._set_generating(True)
        self._gen_output_text.clear()
        self._gen_result_label.clear_image()
        self._gen_result_label.repaint()
        self._gen_result_b64 = None
        self._gen_save_btn.setEnabled(False)
        self._status.showMessage("正在生成图片，请稍候...")

        self._gen_worker = GenerateWorker(
            prompt=prompt,
            color_mode=color_mode,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            style=style,
            custom_style=custom_style,
        )
        self._gen_worker.text_chunk.connect(self._on_gen_text_chunk)
        self._gen_worker.finished.connect(self._on_generate_done)
        self._gen_worker.error.connect(self._on_generate_error)
        self._gen_worker.start()

    def _on_text_chunk(self, text: str):
        cursor = self._output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self._output_text.setTextCursor(cursor)
        self._output_text.ensureCursorVisible()

    def _on_gen_text_chunk(self, text: str):
        cursor = self._gen_output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self._gen_output_text.setTextCursor(cursor)
        self._gen_output_text.ensureCursorVisible()

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

    def _on_generate_done(self, b64_data: str):
        self._set_generating(False)
        self._gen_result_b64 = b64_data
        pixmap = base64_to_qpixmap(b64_data)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法解析返回的图片数据")
            self._status.showMessage("生图失败：图片数据无效")
            return
        self._gen_result_label.set_image(pixmap)
        self._gen_save_btn.setEnabled(True)
        self._status.showMessage("生图完成")

    def _on_process_error(self, msg: str):
        self._set_processing(False)
        QMessageBox.critical(self, "处理失败", msg)
        self._status.showMessage("处理失败")

    def _on_generate_error(self, msg: str):
        self._set_generating(False)
        QMessageBox.critical(self, "生图失败", msg)
        self._status.showMessage("生图失败")

    def _set_processing(self, busy: bool):
        self._process_btn.setEnabled(not busy)
        self._process_btn.setText("处理中..." if busy else "开始处理")

    def _set_generating(self, busy: bool):
        self._gen_btn.setEnabled(not busy)
        self._gen_btn.setText("生成中..." if busy else "开始生成")

    def _save_result(self):
        self._save_image_from_b64(self._result_b64)

    def _save_generated_result(self):
        self._save_image_from_b64(self._gen_result_b64)

    def _save_image_from_b64(self, image_b64: str | None):
        if not image_b64:
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
            pil_image = base64_to_pil(image_b64)
            save_image(pil_image, path)
            self._status.showMessage(f"已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
