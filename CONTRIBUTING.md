# 贡献指南

感谢关注 AI 大模型字幕助手。当前项目保持个人工具定位，优先接受能提升稳定性、易用性和可维护性的改动。

## 开发环境

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

安装完成后先运行：

```powershell
python -m pytest -q
python -m aisrt --help
python -m aisrt.gui --check
```

## 代码原则

- 保持实现直接清晰，不为了“未来可能用到”提前抽象。
- 能用标准库解决的，不新增依赖。
- GUI 面向普通用户，只暴露高频选项；低频选项放到高级设置。
- CLI 可以保留精确参数，但必须真实生效。
- 新增用户可见文案时，同步补齐简体中文、繁体中文和英语。
- 新增或修改纯逻辑时，优先补单元测试。

## 提交前检查

```powershell
python -m pytest -q
python -m compileall -q aisrt tests
python -m pip check
python -m aisrt --help
python -m aisrt doctor
python -m aisrt.gui --check
git diff --check
```

涉及 GUI 时，至少确认：

- 窗口可初始化。
- 简体中文、繁体中文、英语切换后无明显截断。
- 添加文件、右键菜单、高级设置、日志区可正常使用。

## 不应提交

- `.env` 或任何密钥配置。
- 模型权重、模型缓存、音频缓存。
- 测试视频、真实媒体文件、截图、生成的字幕。
- 个人路径、个人邮箱、网盘目录或真实影片名。

## 隐私与脱敏

- Issue、PR、截图和日志中只保留定位问题所需的最小信息。
- 用 `<project-dir>`、`movie.mp4`、`sample.srt` 这类占位符替代本机目录和真实文件名。
- 不粘贴访问令牌、Cookie、鉴权头、第三方服务 API Key 或完整 `.env` 内容。
- 如需提供日志，先删除用户名、邮箱、网盘目录、完整媒体路径和模型缓存路径。

## Issue 与 Pull Request

提交问题时请包含：

- 操作系统、Python 版本、是否使用 GPU。
- 运行命令或界面操作步骤。
- 关键日志。请先删除个人路径、真实文件名和任何敏感信息。

提交 PR 时请说明：

- 改动目的。
- 影响范围。
- 已运行的验证命令。
