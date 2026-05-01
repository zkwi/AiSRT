# AISRT v$Version

## 简体中文

本次发布提供轻量 Windows portable 源码包和 Python wheel。

### 主要变化

- 补齐 GitHub 开源协作文件：Issue 模板、PR 模板、行为准则、支持说明、轻量 CI 和 Dependabot 配置。
- 优化 Python 环境配置，将默认 CUDA PyTorch 固定项拆分到 `requirements-torch-cu130.txt`，运行环境和开发环境复用同一套配置。
- 增强开源卫生检查，覆盖社区文件、requirements 文件、Markdown 相对链接和常见隐私信息模式。
- 修复 Windows portable 打包脚本，避免 Windows PowerShell 兼容性问题和空 ZIP 包误发布。
- 移除 README 中指向本地截图目录的引用，因为截图属于发布前应忽略的运行产物。

### 发布资产

- `AiSRT-v$Version-windows-portable.zip`：轻量 Windows 包，包含源码、启动脚本和依赖文件。
- `aisrt-$Version-py3-none-any.whl`：Python wheel，适合手动安装的用户。
- `SHA256SUMS.txt`：发布资产 SHA256 校验值。

### 注意事项

- 发布包不包含 Python、PyTorch/CUDA 运行库、模型权重、模型缓存、FFmpeg、媒体文件、生成字幕、截图、测试文件或日志。
- 解压 ZIP 后运行 `install_runtime.bat`，脚本会创建 `.venv` 并安装 Python 依赖。
- 使用远程模型 ID 时，AISRT 会在首次运行时下载模型权重到配置的 Hugging Face 缓存目录。
- FFmpeg 和 ffprobe 需要单独安装，并确保可在 `PATH` 中直接运行。

## English

This release provides a lightweight Windows portable source package and a Python wheel.

### Highlights

- Added GitHub open-source collaboration files: issue templates, pull request template, code of conduct, support guide, lightweight CI and Dependabot configuration.
- Improved Python environment setup by moving the default CUDA PyTorch pins into `requirements-torch-cu130.txt`, shared by runtime and development installs.
- Strengthened open-source hygiene checks for community files, requirements files, Markdown relative links and common private data patterns.
- Fixed the Windows portable packaging script to avoid Windows PowerShell compatibility issues and prevent empty ZIP releases.
- Removed the README reference to local screenshots because screenshots are runtime artifacts ignored before release.

### Assets

- `AiSRT-v$Version-windows-portable.zip`: lightweight Windows package with source code, launch scripts and dependency files.
- `aisrt-$Version-py3-none-any.whl`: Python wheel for users who prefer manual Python installation.
- `SHA256SUMS.txt`: SHA256 checksums for release assets.

### Notes

- Python, PyTorch/CUDA runtime libraries, model weights, model caches, FFmpeg, media files, generated subtitles, screenshots, tests and logs are not included.
- Run `install_runtime.bat` after extracting the ZIP to create `.venv` and install Python dependencies.
- When remote model IDs are used, AISRT downloads model weights to the configured Hugging Face cache on first use.
- FFmpeg and ffprobe must be installed separately and available in `PATH`.
