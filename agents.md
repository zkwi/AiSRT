# AGENTS.md

## 项目定位

这是个人使用的多语言音视频字幕生成 CLI/GUI 工具。目标是简单、稳定、可维护，不做 Web UI、不做服务端、不接数据库。

核心命令：

```powershell
ai-sub "movie.mp4" --overwrite
```

## 本地环境

默认使用当前目录下的虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m aisrt --help
ai-sub --help
```

当前机器使用 CUDA 版 PyTorch：

```text
torch==2.11.0+cu130
torchaudio==2.11.0+cu130
```

## 模型路线

必须走本地模型推理，不使用 DashScope API，也不调用 `qwen3-asr-toolkit`。

默认模型：

```text
Qwen/Qwen3-ASR-1.7B
Qwen/Qwen3-ForcedAligner-0.6B
```

## 工程约束

- 保持代码直接、清晰，避免为了抽象而抽象。
- 能用标准库解决的，不新增依赖。
- 错误处理保持基础清晰，不做复杂异常层级。
- 注释只解释关键原因，不复述代码本身。
- CLI 参数必须真实生效；不要保留无用兼容参数。
- 生成文件、模型缓存、测试视频不要提交到 Git。
- 文档、日志和截图不要包含个人路径、真实媒体名、邮箱、Token、Cookie 或 API Key。

## Git 忽略约定

以下内容是运行产物或测试资产，应保持忽略：

```text
.venv/
.hf_cache/
models/
video/
screenshots/
logs/
.idea/
*.srt
*.raw.srt
*.vtt
*.ass
*.txt
```

`requirements.txt` 需要保留在 Git 中。
