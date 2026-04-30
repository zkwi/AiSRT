# AI 大模型字幕助手

本项目是一个本地运行的字幕生成工具，用大模型 ASR 从视频或音频中识别语音，并生成带时间轴的 SRT 字幕。

核心能力：

- 多语言识别：支持自动识别，也可以手动指定常用语种。
- 精准时间对齐：使用强制对齐模型生成更贴合语音节奏的时间轴。
- 本地推理：默认在本机运行模型，不调用 DashScope API，不依赖 `qwen3-asr-toolkit`。
- 桌面界面：提供 PyQt 图形界面，适合普通用户批量处理媒体文件。
- 命令行：保留 CLI，适合批处理、排查问题和脚本化使用。

> 说明：项目名称不使用模型厂商商标；当前默认模型路线使用 Qwen3-ASR 与 Qwen3-ForcedAligner，相关名称仅用于说明技术依赖和模型 ID。

## 工作流程

```text
视频/音频文件
  -> FFmpeg 提取 16k 单声道临时 WAV
  -> 本地 ASR 模型识别语音文本
  -> 本地强制对齐模型生成时间戳
  -> 字幕后处理
  -> 输出 .srt 文件
```

## 文档导航

- [贡献指南](CONTRIBUTING.md)：开发原则、提交前检查、Issue 与 PR 要求。
- [安全说明](SECURITY.md)：敏感信息、日志脱敏和安全问题报告。
- [工程治理说明](docs/engineering.md)：源码模块边界、GUI/CLI 约定和发布前检查。
- [开源发布检查清单](docs/release-checklist.md)：发布前逐项核对。
- [变更日志](CHANGELOG.md)：版本变更记录。

## 环境要求

- Windows 10/11 优先支持；Linux/macOS 可自行验证。
- Python 3.10 或更高版本，推荐 Python 3.11。
- FFmpeg 与 ffprobe 已安装，并在命令行中可直接运行。
- 推荐 NVIDIA GPU。CPU 可以运行，但速度会明显变慢。
- 本项目底层依赖千问 Qwen 大模型，模型体积和推理开销较高，对显存、内存、磁盘空间和首次下载网络连通性有一定要求。

当前 `requirements.txt` 固定为 CUDA 版 PyTorch：

```text
torch==2.11.0+cu130
torchaudio==2.11.0+cu130
```

如果你的环境不是 CUDA 13.0，请先按 PyTorch 官方说明调整安装命令，再安装项目依赖。

## 安装

建议在项目目录创建本地虚拟环境：

```powershell
cd <project-dir>
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

Windows 下也可以双击 `activate_env.bat` 进入项目环境。脚本会设置项目内模型缓存目录和 UTF-8 输出环境。

安装完成后检查环境：

```powershell
ai-sub doctor
ai-sub-gui --check
```

## 图形界面

启动：

```powershell
ai-sub-gui
```

也可以双击 `open_ui.bat`。

界面适合普通用户直接使用：

- 点击“添加文件”选择一个或多个视频/音频文件。
- 支持把文件直接拖入窗口。
- 字幕默认保存在每个媒体文件所在目录。
- 默认不覆盖已有字幕；发现同名 `.srt` 时会先询问。
- 支持简体中文、繁体中文、英语三种界面语言。
- 常用设置只保留上下文、识别语言、运行模式和模型尺寸。
- 低频设置放在“高级设置”：设备、音频分块、字幕样式、覆盖输出、本地缓存。
- 文件队列表格支持右键菜单，可打开字幕目录、移除文件、重试失败任务或清空队列。
- 普通日志默认显示友好提示；勾选“显示技术日志”可查看完整底层日志。
- “翻译字幕”入口会打开独立说明页，引导用户前往 DeepSeek 官网上传 SRT 并复制预设提示词翻译字幕。

推荐设置：

| 设置 | 默认值 | 建议 |
| --- | --- | --- |
| 识别语言 | 自动识别 | 不确定时保持默认；明确语言时手动指定更稳定 |
| 运行模式 | 推荐 | 显存不足时再切换到低显存 |
| 模型尺寸 | 1.7B | 质量优先用 1.7B；速度或显存优先用 0.6B |
| 音频分块 | 推荐（45 秒） | 识别不稳定时改为稳妥（30 秒） |
| 字幕样式 | 推荐 | 想让每条字幕更短时使用短句 |

### SRT 字幕翻译

软件不内置第三方翻译服务，也不会自动上传字幕文件。主界面的“翻译字幕”按钮只提供一个独立指引页，帮助你手动完成以下操作：

1. 打开 DeepSeek 官网的 Chat 页面。
2. 将生成的 `.srt` 文件拖入网页对话框。
3. 点击“复制提示词”，把预设提示词粘贴到 DeepSeek，让它按 SRT 格式翻译。

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

```text
--model-size
ASR 模型尺寸，默认 1.7B。可选 1.7B 或 0.6B。

--model
自定义 ASR 模型路径或 Hugging Face ID；设置后会覆盖 --model-size。

--aligner
强制对齐模型路径或 Hugging Face ID。

--language
识别语言，默认 auto。可设置为 English、Japanese、Chinese 等模型支持的语言名。

-c / --context
可选上下文提示。适合填写片名、角色名、人名、地名等具体词。

-d / --duration
ASR 分块目标秒数，默认 45。低声、稀疏对白或识别为空时可改为 30。

--device
推理设备，默认 auto。常用值为 auto、cuda:0、cpu。

--local-files-only
只读取本地模型，不联网下载。适合模型已提前下载后的离线运行。
```

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

第一次运行如果使用 Hugging Face ID，会自动下载模型权重。默认建议把缓存放在项目目录 `.hf_cache/`，便于清理和开源发布时忽略。

由于依赖千问 Qwen 大模型，首次运行通常需要从 Hugging Face 或其他模型源下载权重。请确保网络能访问相应模型仓库，并预留足够磁盘空间；网络不稳定或需要离线使用时，建议提前手动下载模型到 `models/` 目录后配合 `--local-files-only` 使用。

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

## 后处理规则

- 去掉相邻重复字幕。
- 修复时间轴重叠。
- 按常见标点拆分过长字幕。
- 整理长行换行。
- 清理 CJK 字符之间不必要的空格。
- 重新编号 SRT。

## 开发与验证

常用检查：

```powershell
python -m pytest -q
python -m compileall -q aisrt tests
python -m pip check
python -m aisrt --help
python -m aisrt doctor
python -m aisrt.gui --check
git diff --check
```

更多工程约定见 [docs/engineering.md](docs/engineering.md)。

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
python -m pytest tests/test_open_source_hygiene.py -q
```

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
