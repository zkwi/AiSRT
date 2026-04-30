# 开源发布检查清单

发布到 GitHub 前按此清单核对。

## 仓库内容

- [ ] `README.md` 描述与当前功能一致。
- [ ] `CONTRIBUTING.md`、`SECURITY.md` 已存在并无个人联系方式。
- [ ] `CHANGELOG.md` 已记录本次面向用户或维护者的重要变化。
- [ ] `docs/README.md` 能正确引导到开发、发布和安全文档。
- [ ] `LICENSE`、README 和 `pyproject.toml` 中的许可证描述一致。
- [ ] `.gitignore` 覆盖模型、缓存、媒体、字幕、日志和本地环境。
- [ ] 没有提交 `.env`、`.venv/`、`.hf_cache/`、`models/`、`video/`、`screenshots/`。

## 隐私与敏感信息

- [ ] 扫描密钥、Token、鉴权头、个人邮箱、用户目录和本机绝对路径。
- [ ] README、脚本、测试中不包含真实影片名或网盘目录。
- [ ] Git 作者邮箱适合公开；必要时使用 GitHub noreply 邮箱整理发布分支。
- [ ] 技术日志或截图已脱敏。
- [ ] 样例路径使用 `<project-dir>`、`movie.mp4`、`sample.srt` 等占位值。

## 功能验证

```powershell
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

## 发布前备注

- 完整长视频处理耗时较长，不要求每次提交都跑；正式发布前应使用可公开短视频完成一次端到端验证。
- 如果使用默认远程模型 ID，首次运行会下载模型权重，README 中应保留相关说明。
