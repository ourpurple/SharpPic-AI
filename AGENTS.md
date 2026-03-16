# Repository Guidelines

## 项目结构与模块组织
- `main.py`：桌面应用入口，负责加载配置、主题和主窗口。
- `src/gui/`：PyQt6 界面层（`main_window.py`、`settings_dialog.py`、`widgets.py`、`theme.py`）。
- `src/api/`：模型/服务提供方客户端与流式处理逻辑（`client.py`、`gmi_client.py`）。
- `src/core/`：核心领域逻辑与提示词构建（`prompts.py`）。
- `src/utils/`：通用工具（配置、加密、图像编解码与保存）。
- `tools/`：维护脚本，如 `generate_builtin.py`。
- `assets/`：静态资源；打包产物位于 `build/`、`dist/`。

## 构建、测试与开发命令
- `python -m venv .venv && .venv\\Scripts\\activate`：创建并激活本地虚拟环境（Windows）。
- `pip install -r requirements.txt`：安装运行依赖。
- `python main.py`：本地启动桌面应用。
- `pyinstaller SharpPic-AI.spec`：打包可执行文件到 `dist/`。
- `python tools/generate_builtin.py`：需要时重新生成内置加密配置。

## 代码风格与命名约定
- 遵循 PEP 8，使用 4 空格缩进，源码编码为 UTF-8。
- 函数/变量/模块使用 `snake_case`，Qt 类使用 `PascalCase`，常量使用 `UPPER_CASE`。
- 新增或修改函数请补充类型注解（仓库已采用如 `str | None` 的现代注解风格）。
- 界面文案尽量放在 UI 层维护，避免把 UI 字符串混入 API 或工具模块。

## 测试指南
- 当前仓库未提交完整自动化测试；新增测试请放在 `tests/`，推荐使用 `pytest`。
- 测试文件命名为 `test_*.py`，并尽量与源码目录结构对应（例如 `tests/utils/test_config.py`）。
- 涉及 API 调用或图像处理的变更，至少补一条回归测试，或在 PR 中提供清晰的手工验证步骤。

## 提交与合并请求规范
- 提交信息建议简短、祈使句、带范围，例如：`fix: handle empty streamed chunks`。
- 行为变更与重构尽量分离，避免一个提交混入多类改动。
- PR 至少包含：变更目的、关键修改点、手工验证步骤；UI 改动请附截图或录屏。
- 关联 Issue，并明确说明配置或安全影响（如 API Key、endpoint、文件路径）。

## 安全与配置提示
- 不要提交真实 API Key 或本地配置文件（`~/.sharppic/config.json`）。
- 合并前使用应用内“连接测试”验证 provider 配置是否可用。

##  交互尽可能使用中文。