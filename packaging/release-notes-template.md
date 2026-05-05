# AISRT v$Version

## 简体中文

本次发布提供轻量 Windows portable 源码包和 Python wheel，重点改进本地 SRT 翻译、GUI 多语言体验和日志提示。

### 主要变化

- 新增本地 SRT 翻译能力，可在 GUI 中翻译已有 SRT，也可通过 `ai-sub-translate` 在命令行批处理。
- GUI 主流程支持“识别并翻译”，会先保留原始 ASR 字幕，再输出翻译语言字幕；翻译失败时不会删除原始字幕。
- 识别和翻译进度增加预估剩余时间，运行日志默认展示关键进度和问题提示，详细日志用于排查底层细节。
- 界面语言扩展为简体中文、繁体中文、英语、日语、韩语和西班牙语；首次启动默认跟随系统语言，手动切换后会记住。
- 优化 CUDA/GPU、模型下载、FFmpeg、权限和磁盘空间等常见问题的用户提示。
- 更新中英文 README、Wiki 文档和预览截图，明确本地 AI 字幕生成、SRT 翻译、GUI/CLI 和隐私边界。

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

This release provides a lightweight Windows portable source package and a Python wheel, with improvements focused on local SRT translation, GUI multilingual UX, and clearer logs.

### Highlights

- Added local SRT translation for both the GUI and the `ai-sub-translate` CLI.
- The main GUI flow can now recognize and translate in one run, keeping the original ASR subtitles before writing translated subtitles; translation failures no longer remove the original subtitles.
- Recognition and translation progress now include estimated remaining time. The default run log shows key progress and issue hints, while detailed logs remain available for troubleshooting.
- UI copy now supports Simplified Chinese, Traditional Chinese, English, Japanese, Korean, and Spanish. First launch follows the system language when supported, and manual changes are remembered.
- Improved user-facing hints for CUDA/GPU, model download, FFmpeg, permission, and disk-space problems.
- Refreshed the Chinese and English README files, Wiki docs, and preview screenshots around local AI subtitle generation, SRT translation, GUI/CLI usage, and privacy boundaries.

### Assets

- `AiSRT-v$Version-windows-portable.zip`: lightweight Windows package with source code, launch scripts and dependency files.
- `aisrt-$Version-py3-none-any.whl`: Python wheel for users who prefer manual Python installation.
- `SHA256SUMS.txt`: SHA256 checksums for release assets.

### Notes

- Python, PyTorch/CUDA runtime libraries, model weights, model caches, FFmpeg, media files, generated subtitles, screenshots, tests and logs are not included.
- Run `install_runtime.bat` after extracting the ZIP to create `.venv` and install Python dependencies.
- When remote model IDs are used, AISRT downloads model weights to the configured Hugging Face cache on first use.
- FFmpeg and ffprobe must be installed separately and available in `PATH`.
