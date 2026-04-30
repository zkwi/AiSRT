from pathlib import Path

from aisrt.diagnostics import CheckResult, blocking_messages, format_diagnostics, run_diagnostics


def test_run_diagnostics_reports_missing_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda _name: None)

    results = run_diagnostics(project_dir=tmp_path, output_dir=tmp_path)

    messages = blocking_messages(results)
    assert any("FFmpeg" in message for message in messages)
    assert any("ffprobe" in message for message in messages)


def test_format_diagnostics_uses_user_facing_statuses():
    results = [
        CheckResult("ffmpeg", "ok", "FFmpeg 可用"),
        CheckResult("cuda", "warn", "没有检测到 CUDA，将使用 CPU"),
        CheckResult("output", "error", "输出目录不可写"),
    ]

    text = format_diagnostics(results)

    assert "[OK] FFmpeg 可用" in text
    assert "[WARN] 没有检测到 CUDA，将使用 CPU" in text
    assert "[ERROR] 输出目录不可写" in text


def test_output_dir_check_does_not_create_target(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda _name: str(Path("tool.exe")))
    target = tmp_path / "new-output"

    run_diagnostics(project_dir=tmp_path, output_dir=target)

    assert not target.exists()
