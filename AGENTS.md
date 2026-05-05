# AGENTS.md

本文件给代码代理、自动化维护工具和未来维护者使用。优先级高于一般建议，但低于用户在当前会话中的明确指令。

## 项目定位

AISRT 是个人使用的多语言音视频字幕生成 CLI/GUI 工具。目标是简单、稳定、可维护。

明确不做：

- 不做 Web UI。
- 不做服务端。
- 不接数据库。
- 不引入账号、权限、多租户或在线任务队列。
- 不把第三方翻译 API 接进本地处理链路。

核心命令：

```powershell
ai-sub "movie.mp4" --overwrite
ai-sub-gui
```

## 本地环境

默认使用项目目录下的虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m aisrt --help
python -m aisrt doctor
python -m aisrt.gui --check
```

当前主要验证环境使用 CUDA 版 PyTorch：

```text
torch==2.11.0+cu130
torchaudio==2.11.0+cu130
```

不要把 `.venv/`、`.hf_cache/`、模型权重、测试媒体、截图、生成字幕或日志提交到 Git。

## 模型路线

必须走本地模型推理，不使用 DashScope API，也不调用 `qwen3-asr-toolkit`。

默认模型：

```text
Qwen/Qwen3-ASR-1.7B
Qwen/Qwen3-ForcedAligner-0.6B
```

可选轻量 ASR：

```text
Qwen/Qwen3-ASR-0.6B
```

模型名称只允许作为技术依赖、模型 ID 或排查信息出现。项目公开名称使用 AISRT 或“AI 大模型字幕助手”。

## 代码边界

```text
aisrt/
  cli.py           CLI 入口、输入收集、音频准备、单文件处理编排
  gui.py           PyQt 主窗口与用户交互
  gui_assets.py    GUI 图标、字体、资源路径和媒体扩展名
  gui_widgets.py   GUI 复用小组件
  gui_worker.py    GUI 后台处理线程
  gui_support.py   GUI 纯函数、文件收集、输出冲突和进度解析
  gui_i18n.py      GUI 多语言文案、普通日志和诊断信息本地化
  gui_theme.py     GUI QSS 样式、图标路径和控件视觉状态
  local_asr.py     本地 ASR 调用、分块识别、时间戳整理
  postprocess.py   SRT 解析、清洗、去重、断行和时间轴修复
  diagnostics.py   本地环境检查
  user_messages.py 用户可读错误提示
```

保持职责简单：

- UI 只负责交互和展示。
- Worker 只负责后台任务编排。
- 纯函数放到 `gui_support.py` 或对应业务模块。
- 不要继续把无关工具函数堆进 `MainWindow`。
- 不新增抽象层，除非能明显减少重复或降低维护成本。

## 编码原则

- 简洁优先，避免为了未来可能用到而提前抽象。
- 能用标准库解决的，不新增依赖。
- 错误处理保持基础清晰，不做复杂异常层级。
- 注释只解释关键原因，不复述代码。
- CLI 参数必须真实生效；无用兼容参数应删除。
- 新增用户可见文案时，同步补齐简体中文、繁体中文和英语。
- 新增或修改纯逻辑时，优先补单元测试。
- GUI 改动必须考虑高 DPI、中文/英文长度、空队列/处理中/完成/失败/取消状态。

## GUI 规则

- GUI 面向普通用户，只暴露高频选项。
- 常用设置保留识别字幕语言、是否启用翻译、翻译语言、运行模式和模型尺寸。
- 设备、音频分块、字幕样式、覆盖输出、本地缓存放到高级设置。
- 模型路径和对齐模型属于内部细节，不在 GUI 主界面暴露。
- 主界面按钮图标保持克制：只在“添加文件”和“开始处理”两个核心操作上使用图标。
- 翻译、高级设置、停止、清空日志和弹窗按钮默认只显示文字。
- 文件队列状态列承载单文件状态和进度，不恢复独立“准备就绪/处理中”大面板。
- GUI 多语言文案集中在 `gui_i18n.py`，样式集中在 `gui_theme.py`，图标资源集中在 `aisrt/assets/`。

## CLI 规则

- CLI 面向批处理和排查，可以保留比 GUI 更细的参数。
- 默认输出目录为输入文件所在目录；`--out-dir` 只在 CLI 中提供。
- 默认不覆盖已有输出；覆盖必须通过 `--overwrite` 或 GUI 确认。
- FFmpeg 调用必须使用参数数组，不使用 shell 字符串拼接。
- 处理路径时使用 `Path`，不要把用户输入拼进 shell 命令。

## 文档规则

- README 面向首次访问者，优先讲清楚用途、快速开始、GUI/CLI 用法、模型缓存、排查和隐私。
- `docs/engineering.md` 记录维护规则和模块边界。
- `docs/release-checklist.md` 记录发布前检查，不写具体个人环境。
- 文档示例使用 `<project-dir>`、`movie.mp4`、`sample.srt` 等占位值。
- 不写入个人用户名、邮箱、网盘目录、真实影片名、本机绝对路径或未脱敏截图。

## 隐私与安全

不要提交或公开：

```text
.env
.venv/
.hf_cache/
models/
video/
screenshots/
logs/
*.srt
*.raw.srt
*.vtt
*.ass
*.ssa
*.wav
*.mp4
*.log
```

不要在源码、测试、文档、Issue、PR 或日志中写入：

- 个人路径。
- 真实媒体文件名。
- 个人邮箱。
- Token、Cookie、API Key、鉴权头。
- 私有模型路径或私有资料库目录。

发布前运行：

```powershell
git status --short --ignored
python -m pytest tests/test_open_source_hygiene.py -q
```

## 验证矩阵

常规提交前至少运行：

```powershell
python -m pytest -q
python -m compileall -q aisrt tests
python -m pip check
python -m aisrt --help
python -m aisrt doctor
python -m aisrt.gui --check
git diff --check
```

GUI 改动额外关注：

- 简体中文、繁体中文、英语切换后无明显截断或重叠。
- 空队列、单文件、多文件状态正常。
- 处理中、停止、完成、失败、取消状态正常。
- 普通日志和技术日志切换正常。
- 高级设置、翻译字幕弹窗、右键菜单可用。

逻辑改动额外关注：

- `tests/test_postprocess.py`
- `tests/test_local_asr.py`
- `tests/test_gui.py`
- `tests/test_user_messages.py`

开源发布改动额外关注：

- `tests/test_open_source_hygiene.py`
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/release-checklist.md`

## Git 规则

- 不要使用 `git reset --hard`、`git checkout --` 等会丢弃用户改动的命令，除非用户明确要求。
- 提交前检查 `git status --short --ignored`，确认没有运行产物进入 Git。
- 如果需要公开 push，提交作者邮箱应适合公开；必要时使用 GitHub noreply 邮箱。
- 提交信息保持简洁，说明实际变更。
- 不要把无关重构和当前任务混在同一个提交里。

## 已知限制

- 停止任务是阶段边界取消，FFmpeg 单次提取和 `model.transcribe()` 单次调用中不能立即打断。
- GUI 进度依赖 ASR/音频日志映射，修改日志格式时必须同步更新 `gui_support.py`、`gui_i18n.py` 和测试。
- 完整长视频端到端验证耗时长，不作为每次提交前必跑项；正式发布前应使用可公开短视频跑通一次。
