# 开源发布检查清单

发布到 GitHub 前按此清单核对。

## 仓库内容

- [ ] `README.md` 和 `README.en.md` 描述与当前功能一致，并互相提供语言切换链接。
- [ ] `CONTRIBUTING.md`、`SUPPORT.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md` 已存在并无个人联系方式。
- [ ] `.editorconfig` 与 `.gitattributes` 覆盖常见文本文件、批处理脚本和 PowerShell 脚本的换行规则。
- [ ] `.github/` 中包含 Issue 模板、PR 模板、轻量 CI 和 GitHub Actions 依赖更新配置。
- [ ] `CHANGELOG.md` 已记录本次面向用户或维护者的重要变化。
- [ ] `docs/README.md` 能正确引导到开发、发布和安全文档。
- [ ] `LICENSE`、README 和 `pyproject.toml` 中的许可证描述一致。
- [ ] `.gitignore` 覆盖模型、缓存、媒体、字幕、日志和本地环境。
- [ ] 没有提交 `.env`、`.venv/`、`.hf_cache/`、`models/`、`video/`、`screenshots/` 或 `dist/` 产物。

## 隐私与敏感信息

- [ ] 扫描密钥、Token、鉴权头、个人邮箱、用户目录和本机绝对路径。
- [ ] README、README.en、脚本、测试中不包含真实影片名或网盘目录。
- [ ] README 和 docs 中的相对链接、图片路径均指向仓库内已跟踪文件。
- [ ] Git 作者邮箱适合公开；必要时使用 GitHub noreply 邮箱整理发布分支。
- [ ] 技术日志或截图已脱敏。
- [ ] README 预览图放在 `docs/assets/` 等可跟踪路径；`screenshots/` 只用于本地临时截图。
- [ ] 样例路径使用 `<project-dir>`、`movie.mp4`、`sample.srt` 等占位值。

## 功能验证

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q aisrt tests
python -m pip check
python -m aisrt --help
python -m aisrt doctor
python -m aisrt.gui --check
python -m pytest tests/test_open_source_hygiene.py -q
git diff --check
```

GUI 相关改动额外确认：

- [ ] 简体中文、繁体中文、英语切换正常。
- [ ] 添加文件、拖拽文件、右键菜单、高级设置可用。
- [ ] 普通日志和技术日志切换正常。
- [ ] 高 DPI Windows 缩放下没有明显重叠或截断。

## Windows portable 发布包

构建命令：

```powershell
.\scripts\build_portable.ps1 -Version 0.1.1
```

产物应位于 `dist/release/`：

- [ ] `AiSRT-v0.1.1-windows-portable.zip`
- [ ] `aisrt-0.1.1-py3-none-any.whl`
- [ ] `SHA256SUMS.txt`

打包约束：

- [ ] ZIP 中包含 `install_runtime.bat`、`start_gui.bat`、`open_shell.bat`、`README_PORTABLE.txt`、`README.md`、`SUPPORT.md`、`LICENSE`、`CHANGELOG.md`、`requirements.txt` 和 `requirements-torch-cu130.txt`。
- [ ] ZIP 中不包含 Python 解释器、PyTorch/CUDA DLL、`.venv/`、模型权重、`.hf_cache/`、`models/`、测试媒体、截图、运行日志、生成字幕或本机绝对路径。
- [ ] 模型权重依赖程序首次运行时按远程模型 ID 下载，不随 Release asset 分发。
- [ ] Python 依赖由 `install_runtime.bat` 在用户本地 `.venv` 中安装，不随 Release asset 分发。
- [ ] FFmpeg 和 ffprobe 不随当前 ZIP 分发，Release notes 需提醒用户手动安装并加入 `PATH`。
- [ ] 解压 ZIP 后运行 `install_runtime.bat` 可完成依赖安装，随后 `start_gui.bat` 可启动 GUI。
- [ ] GitHub Actions CI 在 PR 上通过，至少覆盖轻量单元测试、compileall、入口检查、wheel 构建和空白字符检查。
- [ ] `RELEASE_NOTES.md` 包含简体中文和英文说明，且中文按 UTF-8 正常显示。

GitHub Release：

```powershell
git tag v0.1.1
git push origin v0.1.1
gh release create v0.1.1 `
  dist/release/AiSRT-v0.1.1-windows-portable.zip `
  dist/release/aisrt-0.1.1-py3-none-any.whl `
  dist/release/SHA256SUMS.txt `
  --title "AISRT v0.1.1" `
  --notes-file dist/release/RELEASE_NOTES.md
```

## 发布前备注

- 完整长视频处理耗时较长，不要求每次提交都跑；正式发布前应使用可公开短视频完成一次端到端验证。
- 如果使用默认远程模型 ID，首次运行会下载模型权重，README 中应保留相关说明。
