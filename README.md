# SharpPic-AI V0.1.0

<div align="center">

**专业的教辅资料图像增强与超分辨率工具**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6.0+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 📖 简介

SharpPic-AI 是一款专为教辅资料（试卷、习题册、笔记）设计的图像增强工具。通过先进的 AI 技术，将模糊、低质量的文档图片转化为高清晰度的 4K 级别图像，同时严格保持原始几何比例和内容完整性。

### ✨ 核心特性

- 🎯 **几何保真超分辨率** - 放大至 4K 时严格保持像素级宽高比
- 🧹 **智能文档净化** - 自动去除纸张底灰、折痕、油墨渗透及阴影
- ✍️ **OCR 级文字锐化** - 针对汉字和公式进行边缘增强，防止笔画粘连
- 🎨 **墨色分层控制** - 文字保持深黑，图形区域自然柔和
- 🖥️ **现代化界面** - 基于 PyQt6 的专业暗色主题界面
- 🔄 **实时处理反馈** - 流式显示处理进度和状态信息
- 📋 **多种输入方式** - 支持文件选择、拖拽、剪贴板粘贴

### 🎨 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│  SharpPic-AI V0.1.0                              [设置]     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   原始图片        │         │   处理结果        │         │
│  │                  │         │                  │         │
│  │  [图片显示区域]   │         │  [图片显示区域]   │         │
│  │                  │         │                  │         │
│  ├──────────────────┤         ├──────────────────┤         │
│  │  [选择文件]      │         │  [保存图片]      │         │
│  │  [开始处理]      │         │                  │         │
│  ├──────────────────┤         │                  │         │
│  │  实时信息        │         │                  │         │
│  │  [处理日志...]   │         │                  │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/yourusername/SharpPic-AI.git
cd SharpPic-AI
```

2. **创建虚拟环境（推荐）**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **运行程序**

```bash
python main.py
```

### 首次配置

首次运行时，程序会自动打开设置对话框，请配置以下信息：

#### 方式一：使用 OpenAI 兼容接口

1. 选择接口类型：**OpenAI 兼容**
2. 填写接口地址（例如：`https://api.openai.com/v1`）
3. 填写 API Key
4. 选择或输入模型名称（推荐：`gpt-4o`）
5. 点击"测试连接"验证配置
6. 点击"保存"

#### 方式二：使用 gmicloud 接口

1. 选择接口类型：**gmicloud (Gemini Flash Image)**
2. 填写 gmicloud API Key
3. 选择输出尺寸（512 / 1K / 2K / 4K）
4. 选择宽高比（可选，默认跟随原图）
5. 点击"测试连接"验证配置
6. 点击"保存"

## 📚 使用指南

### 加载图片

支持三种方式加载图片：

1. **文件选择**：点击"选择文件"按钮，从文件浏览器中选择图片
2. **拖拽上传**：直接将图片文件拖拽到左侧显示区域
3. **剪贴板粘贴**：复制图片后按 `Ctrl+V`（Windows/Linux）或 `Cmd+V`（macOS）

支持的图片格式：PNG、JPG、JPEG、BMP、GIF、WEBP

### 处理图片

1. 加载图片后，点击"开始处理"按钮
2. 程序会在"实时信息"区域显示处理进度
3. 处理完成后，结果会自动显示在右侧面板
4. 点击"保存图片"按钮保存处理结果

### 保存结果

1. 处理完成后，"保存图片"按钮会自动启用
2. 点击按钮打开保存对话框
3. 选择保存位置和文件名
4. 支持保存为 PNG 或 JPEG 格式

## ⚙️ 配置说明

配置文件位置：`~/.sharppic/config.json`

### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api_provider` | API 接口类型 | `openai` |
| `api_base_url` | OpenAI 接口地址 | - |
| `api_key` | OpenAI API Key | - |
| `model_name` | 模型名称 | `gpt-4o` |
| `gmi_api_key` | gmicloud API Key | - |
| `gmi_image_size` | gmicloud 输出尺寸 | `4K` |
| `gmi_aspect_ratio` | gmicloud 宽高比 | 自动 |
| `save_directory` | 默认保存目录 | `~/Pictures/SharpPic` |

### 配置优先级

配置加载遵循以下优先级（从低到高）：

1. 硬编码默认值
2. 内置加密配置（如果存在）
3. 用户配置文件

## 🔧 技术架构

### 核心模块

```
SharpPic-AI/
├── main.py                 # 程序入口
├── src/
│   ├── api/               # API 客户端
│   │   ├── client.py      # OpenAI 兼容接口
│   │   └── gmi_client.py  # gmicloud 接口
│   ├── core/              # 核心逻辑
│   │   └── prompts.py     # 提示词系统
│   ├── gui/               # 图形界面
│   │   ├── main_window.py # 主窗口
│   │   ├── settings_dialog.py # 设置对话框
│   │   ├── widgets.py     # 自定义控件
│   │   └── theme.py       # 主题样式
│   └── utils/             # 工具函数
│       ├── config.py      # 配置管理
│       ├── crypto.py      # 加密工具
│       └── image_utils.py # 图像处理
└── tools/
    └── generate_builtin.py # 内置配置生成
```

### 处理流程

1. **图片加载** → 验证格式 → Base64 编码
2. **构建请求** → 添加提示词 → 调用 API
3. **流式处理** → 实时显示进度 → 接收结果
4. **结果展示** → Base64 解码 → 显示图片
5. **保存文件** → 用户选择路径 → 写入磁盘

### 提示词系统

SharpPic-AI 使用专业的提示词系统，确保处理质量：

- **几何保真**：严格保持原始宽高比，长边固定 3840px
- **内容安全**：文字不侵蚀，零篡改
- **墨色分层**：文字深黑（#0A0A0A ~ #1A1A1A），图形中灰（#3A3A3A ~ #606060）
- **智能净化**：去除纸张纹理、折痕、阴影
- **OCR 优化**：针对文字进行边缘锐化

## 🛠️ 打包发布

使用 PyInstaller 打包为独立可执行文件：

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包（使用提供的 spec 文件）
pyinstaller SharpPic-AI.spec

# 生成的可执行文件位于 dist/ 目录
```

打包后的程序无需 Python 环境即可运行。

## 📋 依赖项

- **PyQt6** (>= 6.6.0) - 图形界面框架
- **openai** (>= 1.0.0) - OpenAI API 客户端
- **Pillow** (>= 10.0.0) - 图像处理库
- **httpx** - HTTP 客户端（gmicloud 接口）

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢 OpenAI 提供强大的 AI 能力
- 感谢 PyQt6 提供优秀的 GUI 框架
- 感谢所有贡献者和用户的支持

## 📞 联系方式

- 项目主页：[GitHub](https://github.com/yourusername/SharpPic-AI)
- 问题反馈：[Issues](https://github.com/yourusername/SharpPic-AI/issues)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！**

Made with ❤️ by SharpPic-AI Team

</div>
