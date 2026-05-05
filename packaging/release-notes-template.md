# AISRT v$Version

## 简体中文

本次发布提供轻量 Windows portable 源码包和 Python wheel，重点优化本地 ASR 默认参数，在不切换模型、不提高批大小的前提下改善常规处理速度。

### 主要变化

- 将 ASR 每个音频块的默认 `max_new_tokens` 从 2048 降到 1536，减少异常长生成带来的耗时。
- 保留稳定的默认组合：`1.7B` ASR 模型、45 秒音频分块和 batch size 1。
- CLI 帮助、GUI 推荐模式和底层模型加载默认值已统一使用新的生成上限。
- 中英文 README 增加 `--max-new-tokens` 说明，长对白被截断时仍可临时调高。
- 增加 CLI 和 GUI 默认参数测试，降低后续改动误改推荐档位的风险。

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

This release provides a lightweight Windows portable source package and a Python wheel, focused on tuning local ASR defaults for better everyday speed without changing the model or raising batch size.

### Highlights

- Lowered the default ASR `max_new_tokens` per audio chunk from 2048 to 1536 to reduce time spent on unusually long generations.
- Kept the stable default combination: `1.7B` ASR model, 45-second audio chunks and batch size 1.
- Unified the CLI help, GUI recommended profile and model-loading default around the new generation limit.
- Documented `--max-new-tokens` in both README files; users can still raise it temporarily if long dialogue is truncated.
- Added CLI and GUI default-parameter tests to keep the recommended profile from drifting accidentally.

### Assets

- `AiSRT-v$Version-windows-portable.zip`: lightweight Windows package with source code, launch scripts and dependency files.
- `aisrt-$Version-py3-none-any.whl`: Python wheel for users who prefer manual Python installation.
- `SHA256SUMS.txt`: SHA256 checksums for release assets.

### Notes

- Python, PyTorch/CUDA runtime libraries, model weights, model caches, FFmpeg, media files, generated subtitles, screenshots, tests and logs are not included.
- Run `install_runtime.bat` after extracting the ZIP to create `.venv` and install Python dependencies.
- When remote model IDs are used, AISRT downloads model weights to the configured Hugging Face cache on first use.
- FFmpeg and ffprobe must be installed separately and available in `PATH`.
