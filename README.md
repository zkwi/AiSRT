# AI 大模型字幕助手

本项目是一个本地运行的音视频字幕生成工具。它使用本地大模型 ASR 从视频或音频中识别语音，并生成带时间轴的 SRT 字幕。

项目定位很明确：个人桌面/命令行工具，优先保证简单、稳定、可维护。不做 Web UI，不做服务端，不接数据库。

## 功能速览

| 能力 | 说明 |
| --- | --- |
| 多语言识别 | 支持自动识别，也可以手动指定常用语种。 |
| 时间轴对齐 | 使用本地强制对齐模型生成更贴近语音节奏的字幕时间轴。 |
| 本地推理 | 默认在本机运行模型，不调用 DashScope API，不依赖 `qwen3-asr-toolkit`。 |
| 批量处理 | GUI 支持多文件队列；CLI 支持单文件和目录批处理。 |
| 字幕后处理 | 自动去重、修复时间重叠、整理长行、清理 CJK 空格并重新编号。 |
| SRT 翻译指引 | 不内置翻译服务，只提供外部 DeepSeek Chat 手动翻译 SRT 的操作指引。 |

> 说明：项目公开名称不使用模型厂商商标；Qwen3-ASR 与 Qwen3-ForcedAligner 只作为模型 ID 和技术依赖出现。

## 适用与不适用场景

适合：

- 在本机为视频、音频生成 `.srt` 字幕。
- 处理个人媒体文件或离线批量任务。
- 需要 GUI 给普通用户操作，同时保留 CLI 便于排查和脚本化。
- 希望模型、缓存、日志和生成文件都留在本机。

不适合：

- 在线字幕服务、多人协作后台或 Web 应用。
- 需要云端 API 自动翻译或自动上传字幕文件的场景。
- 没有 FFmpeg、磁盘空间或可用模型下载渠道的环境。
- 希望在 CPU 上快速处理长视频的场景。

## 工作流程

```text
视频/音频文件
  -> FFmpeg 提取 16k 单声道临时 WAV
  -> 本地 ASR 模型识别语音文本
  -> 本地强制对齐模型生成时间戳
  -> 字幕后处理
  -> 输出 .srt 文件
```

## 快速开始

Windows 10/11 是主要支持环境。Linux 和 macOS 可自行验证。

```powershell
git clone https://github.com/zkwi/AiSRT.git
cd AiSRT
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
ai-sub doctor
ai-sub-gui --check
```

启动图形界面：

```powershell
ai-sub-gui
```

命令行处理单个文件：

```powershell
ai-sub "movie.mp4" --overwrite
```

也可以双击：

- `activate_env.bat`：进入项目虚拟环境，并设置项目内模型缓存目录。
- `open_ui.bat`：用当前虚拟环境启动 GUI。

## 环境要求

- Python 3.10 或更高版本，推荐 Python 3.11。
- FFmpeg 与 ffprobe 已安装，并可在命令行中直接运行。
- 推荐 NVIDIA GPU。CPU 可以运行，但长视频会明显变慢。
- 首次使用远程模型 ID 时需要下载模型权重，请预留足够磁盘空间。

当前默认安装使用 CUDA 版 PyTorch，具体固定项放在 `requirements-torch-cu130.txt`：

```text
torch==2.11.0+cu130
torchaudio==2.11.0+cu130
```

如果你的 CUDA/PyTorch 环境不同，请先按 PyTorch 官方安装方式调整 `requirements-torch-cu130.txt`，或手动安装匹配版本后再安装本项目依赖。

## 图形界面

GUI 面向普通用户，主界面只保留高频操作：

- 添加文件：选择一个或多个视频/音频文件，也支持拖拽文件进入窗口。
- 开始处理：按文件队列逐个生成字幕。
- 文件队列：显示文件、状态、进度和字幕目录。
- 常用设置：上下文、识别语言、运行模式、模型尺寸。
- 高级设置：设备、音频分块、字幕样式、覆盖输出、本地缓存。
- 运行日志：默认显示友好提示；勾选“显示技术日志”后显示更完整的底层日志。
- 翻译字幕：打开说明页，引导用户手动前往 DeepSeek Chat 上传 SRT 并复制预设提示词。

默认行为：

- 字幕保存到每个媒体文件所在目录。
- 不覆盖已有 `.srt`，发现同名输出会先询问。
- 支持简体中文、繁体中文、英语三种界面语言。
- 本次运行内会记住上次添加媒体文件的位置，下一次添加文件会从该目录打开。
- 添加文件和开始处理是核心按钮，保留图标；其他按钮默认只显示文字，避免界面噪声。

推荐设置：

| 设置 | 默认值 | 建议 |
| --- | --- | --- |
| 识别语言 | 自动识别 | 不确定时保持默认；明确语言时手动指定更稳定。 |
| 运行模式 | 推荐 | 显存不足时切换到低显存。 |
| 模型尺寸 | 1.7B | 质量优先用 1.7B；速度或显存优先用 0.6B。 |
| 音频分块 | 推荐（45 秒） | 识别不稳定时改为稳妥（30 秒）。 |
| 字幕样式 | 推荐 | 想让每条字幕更短时使用短句。 |

## SRT 字幕翻译

软件不内置第三方翻译服务，也不会自动上传字幕文件。主界面的“翻译字幕”按钮只提供一个独立指引页，帮助你手动完成：

1. 打开 DeepSeek Chat。
2. 将生成的 `.srt` 文件拖入网页对话框。
3. 点击“复制提示词”，把预设提示词粘贴到 DeepSeek。

预设提示词会要求保留 SRT 编号、时间轴、分段和换行结构，只翻译字幕正文，并且只输出翻译后的 SRT 内容。

## 命令行

单文件处理：

```powershell
ai-sub "movie.mp4" --overwrite
```

使用轻量模型：

```powershell
ai-sub "movie.mp4" --model-size 0.6B --overwrite
```

批量处理目录：

```powershell
ai-sub ".\media" -o ".\subtitles" --recursive --overwrite
```

使用本地已下载模型：

```powershell
ai-sub "movie.mp4" `
  --model .\models\Qwen3-ASR-1.7B `
  --aligner .\models\Qwen3-ForcedAligner-0.6B `
  --local-files-only `
  --overwrite
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--model-size` | ASR 模型尺寸，默认 `1.7B`，可选 `1.7B` 或 `0.6B`。 |
| `--model` | 自定义 ASR 模型路径或 Hugging Face ID；设置后覆盖 `--model-size`。 |
| `--aligner` | 强制对齐模型路径或 Hugging Face ID。 |
| `--language` | 识别语言，默认 `auto`；可设置为 `English`、`Chinese`、`Korean` 等模型支持的语言名。 |
| `-c, --context` | 可选上下文提示，适合填写片名、角色名、人名、地名等具体词。 |
| `-d, --duration` | ASR 分块目标秒数，默认 45；低声、稀疏对白或识别为空时可改为 30。 |
| `--device` | 推理设备，默认 `auto`；常用值为 `auto`、`cuda:0`、`cpu`。 |
| `--local-files-only` | 只读取本地模型，不联网下载。 |

完整参数：

```powershell
ai-sub --help
```

## 模型与缓存

默认模型：

```text
Qwen/Qwen3-ASR-1.7B
Qwen/Qwen3-ForcedAligner-0.6B
```

可选 ASR 尺寸：

```text
1.7B  默认，质量更好，显存占用更高
0.6B  更轻量，速度更快，适合低显存或快速预览
```

首次运行如果使用 Hugging Face ID，会自动下载模型权重。建议把缓存放在项目目录 `.hf_cache/`，便于清理和开源发布时忽略。

手动下载示例：

```powershell
mkdir models
huggingface-cli download Qwen/Qwen3-ASR-1.7B --local-dir .\models\Qwen3-ASR-1.7B
huggingface-cli download Qwen/Qwen3-ASR-0.6B --local-dir .\models\Qwen3-ASR-0.6B
huggingface-cli download Qwen/Qwen3-ForcedAligner-0.6B --local-dir .\models\Qwen3-ForcedAligner-0.6B
```

运行时会在 `.hf_cache/audio_tmp/` 下生成临时 WAV。该目录属于运行缓存，不应提交到 Git。

## 输出文件

默认输出：

```text
movie.srt
```

生成后会删除中间文件：

```text
movie.raw.srt
movie.txt
```

## 常见问题

### 找不到 FFmpeg

运行：

```powershell
ai-sub doctor
```

如果 ffmpeg 或 ffprobe 不可用，请先安装 FFmpeg，并确认 `ffmpeg`、`ffprobe` 能在命令行中直接运行。

### 首次运行很慢

首次运行可能会下载模型权重，并进行模型加载。模型体积较大，耗时取决于网络、磁盘和显卡环境。

### 显存不足

优先尝试：

- GUI 中切换到“低显存”运行模式。
- 模型尺寸改为 `0.6B`。
- CLI 中使用 `--device cpu` 作为兜底，但速度会明显变慢。

### 不想联网下载模型

提前把模型下载到 `models/` 目录，然后使用 `--local-files-only` 和本地模型路径。

### 生成字幕不够稳定

可尝试：

- 明确指定识别语言。
- 在上下文里填写片名、人名、地名或专有名词。
- 把音频分块从 45 秒改为 30 秒。
- 使用 1.7B 模型而不是 0.6B。

## 项目结构

```text
aisrt/
  cli.py           CLI 入口、音频准备、单文件处理编排
  gui.py           PyQt 主窗口与用户交互
  gui_worker.py    GUI 后台处理线程
  gui_i18n.py      GUI 多语言文案和日志本地化
  gui_theme.py     GUI QSS 样式
  local_asr.py     本地 ASR 调用、分块识别、时间戳整理
  postprocess.py   SRT 解析、清洗、去重、断行和时间轴修复
  diagnostics.py   本地环境检查
tests/             单元测试和 GUI offscreen 测试
docs/              工程治理、发布检查和维护文档
```

## 开发与验证

安装开发、测试和打包依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

依赖文件分工：

- `requirements.txt`：普通运行环境，安装默认 CUDA PyTorch 栈和 AISRT 包。
- `requirements-dev.txt`：开发环境，复用默认 CUDA PyTorch 栈，并以 editable 模式安装开发工具。
- `requirements-torch-cu130.txt`：默认 CUDA PyTorch 固定项；切换 CUDA/CPU 版本时优先改这里。

常用检查：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q aisrt tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m aisrt --help
.\.venv\Scripts\python.exe -m aisrt doctor
.\.venv\Scripts\python.exe -m aisrt.gui --check
git diff --check
```

## 发布构建

Windows portable 包是轻量源码包，不包含 Python、PyTorch/CUDA 运行库、模型权重、FFmpeg、`.venv`、缓存、媒体、字幕、截图或日志。目标产物为：

```text
dist/release/AiSRT-v0.1.1-windows-portable.zip
dist/release/aisrt-0.1.1-py3-none-any.whl
dist/release/SHA256SUMS.txt
```

构建命令：

```powershell
.\scripts\build_portable.ps1 -InstallDeps
```

约束：

- Portable ZIP 不包含模型权重、模型缓存、测试媒体、截图、日志或生成字幕。
- Portable ZIP 不包含 Python 解释器、PyTorch/CUDA DLL 或其他本地运行环境。
- 解压后运行 `install_runtime.bat`，脚本会在当前目录创建 `.venv` 并安装 `requirements.txt` 中的 Python 依赖。
- 使用远程模型 ID 时，模型权重会在首次运行时下载到 Hugging Face 缓存目录。
- FFmpeg 和 ffprobe 需要用户单独安装，并确保可在 `PATH` 中直接运行。
- Release asset 上传前应保留 ZIP、wheel 和 `SHA256SUMS.txt` 三个文件。
- `packaging/aisrt_portable.spec` 仅保留给维护者本地试验完整运行时打包，默认 Release 不使用它。

## 文档导航

- [AGENTS.md](AGENTS.md)：给代码代理和维护者看的项目约束、验证命令和协作规则。
- [贡献指南](CONTRIBUTING.md)：开发原则、提交前检查、Issue 与 PR 要求。
- [支持说明](SUPPORT.md)：Issue 范围、提问前检查和隐私提醒。
- [安全说明](SECURITY.md)：敏感信息、日志脱敏和安全问题报告。
- [行为准则](CODE_OF_CONDUCT.md)：公开协作中的基本沟通规则。
- [工程治理说明](docs/engineering.md)：源码模块边界、GUI/CLI 约定和发布前检查。
- [开源发布检查清单](docs/release-checklist.md)：发布前逐项核对。
- [变更日志](CHANGELOG.md)：版本变更记录。

## 隐私与开源发布

发布到 GitHub 前请确认：

- `.env`、模型缓存、音频缓存、测试媒体、截图、生成字幕、运行日志没有进入 Git。
- 文档、脚本、测试样例只使用占位路径和占位文件名，不包含个人用户名、邮箱、网盘目录、真实影片名或本机绝对路径。
- 公开 Issue、PR 和日志前先脱敏，删除用户目录、完整媒体文件名、访问令牌、Cookie、鉴权头和第三方服务密钥。
- Git 作者邮箱适合公开，必要时使用 GitHub noreply 邮箱重新整理发布分支。
- 发布前至少用一段可公开的短视频完成端到端验证，不要使用受版权或隐私限制的媒体文件。

建议发布前额外执行：

```powershell
git status --short --ignored
.\.venv\Scripts\python.exe -m pytest tests/test_open_source_hygiene.py -q
```

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
