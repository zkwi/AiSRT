# 工程治理说明

本项目是个人使用的多语言音视频字幕生成工具，治理目标是“稳定可用、容易回看、改动可控”。不追求企业级流程，但每次变更都应留下可验证的依据。

## 模块边界

```text
aisrt/
  cli.py           命令行入口、输入收集、音频准备、单文件处理编排
  gui.py           PyQt 主窗口与用户交互
  gui_assets.py    GUI 图标、字体、资源路径和媒体扩展名
  gui_widgets.py   GUI 复用小组件
  gui_worker.py    GUI 后台处理线程
  gui_support.py   GUI 纯函数、文件收集、输出冲突和进度解析
  gui_i18n.py      GUI 多语言文案、普通日志和诊断信息本地化
  gui_theme.py     GUI QSS 样式、图标路径和控件视觉状态
  local_asr.py     本地 ASR 调用、分块识别、时间戳整理
  local_translate.py 本地 SRT 翻译、分段、提示词和译文合并
  translate_cli.py  SRT 翻译命令行入口
  translate_worker.py GUI 本地翻译后台线程
  postprocess.py   SRT 解析、清洗、去重、断行和时间轴修复
  diagnostics.py   本地环境检查
  user_messages.py 用户可读错误提示
```

保持边界简单：UI 只负责交互，Worker 只负责后台任务，纯函数放到 `gui_support.py`，不要把新功能继续堆进 `MainWindow`。

## 变更原则

- CLI 参数必须真实生效；无用兼容参数应删除。
- 新增用户可见行为时，同步更新 README 或本文档。
- 新增纯逻辑时优先补单元测试，不依赖真实大模型。
- 不新增依赖，除非标准库或现有依赖无法直接解决。
- 错误提示优先给“原因 + 下一步”，技术细节放到日志。
- 长任务相关改动必须确认取消、失败、完成三种状态不会互相覆盖。
- 项目公开名称使用“AI 大模型字幕助手”；模型厂商名称只在技术依赖、模型 ID 或排查信息中出现。

## GUI 与 CLI 边界

- GUI 面向普通用户，只暴露高频选择和语义化预设，避免要求用户微调秒数、token、批大小等数字。
- CLI 面向排查和批处理，可以保留精确参数，但 README 需要说明哪些参数普通用户通常不需要碰。
- GUI 的预设值应集中在 `gui.py` 顶部常量，变更预设时同步更新 `tests/test_gui_window.py` 和 README。
- GUI 的样式集中在 `gui_theme.py`，使用轻量 QSS 和 objectName/property 管理卡片、按钮、右键菜单、下拉框、弹框、表格、日志等视觉状态。
- GUI 图标、字体和媒体扩展名集中在 `gui_assets.py`，可复用小组件放在 `gui_widgets.py`，避免继续放大主窗口文件。
- GUI 图标资源放在 `aisrt/assets/`，需要通过 `pyproject.toml` 的 package-data 一并打包。
- 主界面按钮图标保持克制：只在“添加文件”和“开始处理”两个核心操作上使用图标；识别并翻译、翻译、高级设置、停止、清空日志和弹窗按钮默认只显示文字。
- GUI 多语言文案集中在 `gui_i18n.py`。新增用户可见字段时必须补齐简体中文、繁体中文和英语，并更新 `tests/test_gui_window.py`。
- GUI 主界面只放高频操作；设备、音频分块和字幕样式放入高级设置弹窗，避免大字号和高 DPI 下挤压常用设置。模型路径和对齐模型属于内部细节，不在 GUI 中暴露给普通用户。
- 运行模式负责在后台调整批大小、token、dtype 等技术参数，不把这些技术细节重新放回界面。
- 识别语言默认自动识别；新增语言选项时应使用底层 ASR 支持的规范英文语言名作为内部值。
- GUI 默认把字幕保存到每个媒体文件所在目录；统一输出目录保留给 CLI 的 `--out-dir`，避免普通用户多做选择。
- SRT 翻译走本地 HY-MT 模型，只翻译字幕正文；编号、时间轴和输出 SRT 结构由程序保留并合并。不要接入云端翻译 API 或自动上传字幕文件。
- 主界面的“识别并翻译”是在 ASR 成功后串联本地翻译：保留 `movie.srt` 原始识别字幕，再生成 `movie.<语言后缀>.srt` 翻译字幕。覆盖检查必须同时覆盖两个输出文件。

## 提交前检查

每次提交前至少运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q aisrt tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m aisrt --help
.\.venv\Scripts\python.exe -m aisrt doctor
.\.venv\Scripts\python.exe -m aisrt.gui --check
git diff --check
```

涉及 GUI 时，建议额外跑一次 offscreen smoke，确认窗口能初始化、添加文件、切换日志：

```powershell
$env:QT_QPA_PLATFORM='offscreen'
@'
from pathlib import Path
from tempfile import TemporaryDirectory
from PyQt6.QtWidgets import QApplication
from aisrt.gui import MainWindow

app = QApplication([])
with TemporaryDirectory() as folder:
    media = Path(folder) / "movie.mp4"
    media.write_bytes(b"dummy")
    window = MainWindow()
    window.add_paths([media])
    assert len(window.files) == 1
    window.close()
print("gui offscreen smoke OK")
'@ | .\.venv\Scripts\python.exe -
```

## 开源发布前检查

- 确认 `.env`、模型缓存、音频缓存、测试视频、生成字幕、运行日志都未进入 Git。
- 文档和脚本不要写入个人用户名、个人邮箱、网盘目录、真实影片名、本机绝对路径或未脱敏截图。
- 发布前运行 `git status --short --ignored`，只允许源码、文档、测试和图标资源处于未忽略状态。
- 发布前运行敏感词扫描，重点查密钥、口令、鉴权头、用户目录、真实媒体文件名和本机盘符路径。
- 发布前运行 `python -m pytest tests/test_open_source_hygiene.py -q`，把开源卫生检查固化到测试里。
- 如果要保留当前 Git 历史，先确认提交作者邮箱适合公开；否则先重写历史或使用 GitHub noreply 邮箱重新整理发布分支。
- 发布前确认 `LICENSE` 文件与 README、`pyproject.toml` 中的许可证描述一致。

## 已知限制

- 停止任务是阶段边界取消：FFmpeg 单次提取和 `model.transcribe()` 单次调用中不能立即打断。
- GUI 进度仍基于 ASR/音频日志映射，后续如大改日志格式，应同步更新 `gui_support.py`、`gui_i18n.py` 和测试。
- 完整长视频端到端验证耗时长，不作为每次提交前必跑项；发布前应至少用一段可公开短视频跑通。
