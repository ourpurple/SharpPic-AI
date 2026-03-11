from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QComboBox,
    QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox, QLabel,
    QWidget,
)
from PyQt6.QtCore import Qt

from src.utils import config

_IMAGE_SIZES = ["512", "1K", "2K", "4K"]
_ASPECT_RATIOS = [
    "",  # empty = use original / default
    "1:1", "3:2", "2:3", "3:4", "4:3",
    "4:5", "5:4", "9:16", "16:9", "21:9",
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(676)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(21)
        layout.setContentsMargins(31, 31, 31, 26)

        header = QLabel("API 配置")
        header.setStyleSheet("font-size: 21px; font-weight: 700; color: #00D4AA; padding-bottom: 5px;")
        layout.addWidget(header)

        # -- Provider selector --
        provider_form = QFormLayout()
        provider_form.setSpacing(16)
        provider_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._provider = QComboBox()
        self._provider.addItem("OpenAI 兼容", "openai")
        self._provider.addItem("gmicloud (Gemini Flash Image)", "gmicloud")
        self._provider.currentIndexChanged.connect(self._on_provider_changed)
        provider_form.addRow("接口类型", self._provider)

        layout.addLayout(provider_form)

        # -- OpenAI section --
        self._openai_section = QWidget()
        openai_layout = QVBoxLayout(self._openai_section)
        openai_layout.setContentsMargins(0, 0, 0, 0)

        openai_form = QFormLayout()
        openai_form.setSpacing(16)
        openai_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._base_url = QLineEdit()
        self._base_url.setPlaceholderText("https://api.openai.com/v1")
        openai_form.addRow("接口地址", self._base_url)

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText("sk-...")
        openai_form.addRow("密钥", self._api_key)

        model_row = QHBoxLayout()
        self._model = QComboBox()
        self._model.setEditable(True)
        self._model.setPlaceholderText("gpt-4o")
        model_row.addWidget(self._model, 1)
        fetch_btn = QPushButton("获取模型")
        fetch_btn.setObjectName("compactBtn")
        fetch_btn.clicked.connect(self._fetch_models)
        model_row.addWidget(fetch_btn)
        openai_form.addRow("模型", model_row)

        openai_layout.addLayout(openai_form)
        layout.addWidget(self._openai_section)

        # -- gmicloud section --
        self._gmi_section = QWidget()
        gmi_layout = QVBoxLayout(self._gmi_section)
        gmi_layout.setContentsMargins(0, 0, 0, 0)

        gmi_form = QFormLayout()
        gmi_form.setSpacing(16)
        gmi_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._gmi_api_key = QLineEdit()
        self._gmi_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._gmi_api_key.setPlaceholderText("gmicloud API Key")
        gmi_form.addRow("密钥", self._gmi_api_key)

        self._gmi_image_size = QComboBox()
        self._gmi_image_size.addItems(_IMAGE_SIZES)
        gmi_form.addRow("输出尺寸", self._gmi_image_size)

        self._gmi_aspect_ratio = QComboBox()
        self._gmi_aspect_ratio.setEditable(True)
        for ar in _ASPECT_RATIOS:
            self._gmi_aspect_ratio.addItem(ar if ar else "自动（跟随原图）")
        gmi_form.addRow("宽高比", self._gmi_aspect_ratio)

        gmi_layout.addLayout(gmi_form)
        layout.addWidget(self._gmi_section)

        # -- Common: save directory --
        common_form = QFormLayout()
        common_form.setSpacing(16)
        common_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        dir_row = QHBoxLayout()
        self._save_dir = QLineEdit()
        self._save_dir.setPlaceholderText("选择默认保存目录")
        dir_row.addWidget(self._save_dir)
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("compactBtn")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)
        common_form.addRow("保存目录", dir_row)

        layout.addLayout(common_form)

        # Test connection
        test_row = QHBoxLayout()
        self._test_btn = QPushButton("测试连接")
        self._test_btn.setObjectName("compactBtn")
        self._test_btn.clicked.connect(self._test_connection)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 16px;")
        test_row.addWidget(self._test_btn)
        test_row.addWidget(self._status_label, 1)
        layout.addLayout(test_row)

        layout.addSpacing(10)

        # Save / Cancel
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_provider_changed(self):
        is_gmi = self._provider.currentData() == "gmicloud"
        self._openai_section.setVisible(not is_gmi)
        self._gmi_section.setVisible(is_gmi)

    def _load_values(self):
        # Provider
        provider = config.get("api_provider") or "openai"
        idx = self._provider.findData(provider)
        if idx >= 0:
            self._provider.setCurrentIndex(idx)

        # OpenAI
        self._base_url.setText(config.get("api_base_url"))
        self._api_key.setText(config.get("api_key"))
        model = config.get("model_name")
        if model:
            self._model.setCurrentText(model)

        # gmicloud
        self._gmi_api_key.setText(config.get("gmi_api_key") or "")
        gmi_size = config.get("gmi_image_size") or "4K"
        idx = self._gmi_image_size.findText(gmi_size)
        if idx >= 0:
            self._gmi_image_size.setCurrentIndex(idx)
        gmi_ar = config.get("gmi_aspect_ratio") or ""
        if gmi_ar:
            ar_idx = self._gmi_aspect_ratio.findText(gmi_ar)
            if ar_idx >= 0:
                self._gmi_aspect_ratio.setCurrentIndex(ar_idx)
            else:
                self._gmi_aspect_ratio.setCurrentText(gmi_ar)
        else:
            self._gmi_aspect_ratio.setCurrentIndex(0)

        # Common
        self._save_dir.setText(config.get("save_directory"))

        # Trigger visibility
        self._on_provider_changed()

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if path:
            self._save_dir.setText(path)

    def _test_connection(self):
        self._status_label.setText("正在连接...")
        self._status_label.setStyleSheet("color: #8B8D98; font-size: 16px;")
        self._apply_to_config()

        provider = self._provider.currentData()
        if provider == "gmicloud":
            self._test_gmi_connection()
        else:
            self._test_openai_connection()

    def _test_openai_connection(self):
        try:
            from src.api.client import test_connection
            result = test_connection()
            self._status_label.setText(f"连接成功: {result}")
            self._status_label.setStyleSheet("color: #00D4AA; font-size: 16px;")
        except Exception as e:
            self._status_label.setText(f"连接失败: {e}")
            self._status_label.setStyleSheet("color: #FF6B6B; font-size: 16px;")

    def _test_gmi_connection(self):
        try:
            import httpx
            key = self._gmi_api_key.text().strip()
            if not key:
                self._status_label.setText("请先填写 gmicloud API Key")
                self._status_label.setStyleSheet("color: #FF6B6B; font-size: 16px;")
                return
            resp = httpx.get(
                "https://console.gmicloud.ai/api/v1/apikey/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=15,
            )
            resp.raise_for_status()
            self._status_label.setText("连接成功")
            self._status_label.setStyleSheet("color: #00D4AA; font-size: 16px;")
        except Exception as e:
            self._status_label.setText(f"连接失败: {e}")
            self._status_label.setStyleSheet("color: #FF6B6B; font-size: 16px;")

    def _apply_to_config(self):
        config.set("api_provider", self._provider.currentData())
        # OpenAI
        config.set("api_base_url", self._base_url.text().strip())
        config.set("api_key", self._api_key.text().strip())
        config.set("model_name", self._model.currentText().strip())
        # gmicloud
        config.set("gmi_api_key", self._gmi_api_key.text().strip())
        config.set("gmi_image_size", self._gmi_image_size.currentText())
        ar_text = self._gmi_aspect_ratio.currentText()
        config.set("gmi_aspect_ratio", "" if ar_text.startswith("自动") else ar_text)
        # Common
        config.set("save_directory", self._save_dir.text().strip())

    def _fetch_models(self):
        self._apply_to_config()
        try:
            from src.api.client import list_models
            models = list_models()
            if not models:
                QMessageBox.information(self, "提示", "未获取到可用模型")
                return
            previous = self._model.currentText()
            self._model.clear()
            self._model.addItems(models)
            idx = self._model.findText(previous)
            if idx >= 0:
                self._model.setCurrentIndex(idx)
            else:
                self._model.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.warning(self, "获取失败", f"无法获取模型列表:\n{e}")

    def _save(self):
        provider = self._provider.currentData()
        if provider == "gmicloud":
            if not self._gmi_api_key.text().strip():
                QMessageBox.warning(self, "提示", "请填写 gmicloud API Key")
                return
        else:
            if not self._api_key.text().strip():
                QMessageBox.warning(self, "提示", "请填写 API Key")
                return
        self._apply_to_config()
        config.save()
        self.accept()
