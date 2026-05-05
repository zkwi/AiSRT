from __future__ import annotations

from pathlib import Path

from aisrt.gui_support import GuiOptions
from aisrt.gui_worker import SubtitleWorker
from aisrt.postprocess import parse_srt


def make_options(tmp_path: Path, translate_after_asr: bool = False) -> GuiOptions:
    return GuiOptions(
        out_dir=tmp_path,
        context="",
        language="English",
        model="Qwen/Qwen3-ASR-0.6B",
        aligner="Qwen/Qwen3-ForcedAligner-0.6B",
        device="cpu",
        dtype="float32",
        batch_size=1,
        max_new_tokens=512,
        max_line_chars=22,
        max_caption_chars=44,
        chunk_seconds=30,
        overwrite=True,
        local_files_only=True,
        translate_after_asr=translate_after_asr,
        translation_target_language="简体中文",
        translation_model_mode="fast",
        translation_max_new_tokens=128,
    )


def test_subtitle_worker_translates_after_asr_and_keeps_original(tmp_path, monkeypatch) -> None:
    import aisrt.gui_worker as worker_module

    media = tmp_path / "speech.mp4"
    media.write_bytes(b"media")

    monkeypatch.setattr(worker_module, "load_local_model", lambda **_kwargs: object())
    monkeypatch.setattr(worker_module, "load_translation_model", lambda **_kwargs: object())

    def fake_make_translator(_runtime: object, max_new_tokens: int):
        assert max_new_tokens == 128

        def translator(_prompt: str) -> str:
            return "1\t你好，世界。"

        return translator

    monkeypatch.setattr(worker_module, "make_model_translator", fake_make_translator)

    def fake_process_one(**kwargs) -> Path:
        output = tmp_path / "speech.srt"
        output.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nHello, world.\n",
            encoding="utf-8",
        )
        kwargs["progress"]("[ASR] 1/1 完成，用时 1.0s，总进度 100%")
        kwargs["progress"](f"[OK] {output} (English)")
        return output

    monkeypatch.setattr(worker_module, "process_one", fake_process_one)

    worker = SubtitleWorker([media], make_options(tmp_path, translate_after_asr=True))
    logs: list[str] = []
    progress: list[tuple[int, str]] = []
    statuses: list[tuple[int, str, str]] = []
    finished: list[bool] = []
    worker.log.connect(logs.append)
    worker.progress.connect(lambda percent, detail: progress.append((percent, detail)))
    worker.file_status.connect(lambda row, status, out_dir: statuses.append((row, status, out_dir)))
    worker.finished.connect(lambda: finished.append(True))

    worker.run()

    original = tmp_path / "speech.srt"
    translated = tmp_path / "speech.zh.srt"
    assert original.exists()
    assert translated.exists()
    assert parse_srt(original.read_text(encoding="utf-8"))[0].text == "Hello, world."
    assert parse_srt(translated.read_text(encoding="utf-8"))[0].text == "你好，世界。"
    assert any("[LOAD] Translate=AngelSlim/Hy-MT1.5-1.8B-1.25bit" in log for log in logs)
    assert any("[TRANSLATE] 1/1 完成，总进度 100%" in log for log in logs)
    assert any(detail.endswith("翻译字幕 100%") for _percent, detail in progress)
    assert statuses[-1] == (0, "完成", str(tmp_path))
    assert finished == [True]
