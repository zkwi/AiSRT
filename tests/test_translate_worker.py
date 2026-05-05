from __future__ import annotations

from aisrt.postprocess import parse_srt
from aisrt.translate_worker import SrtTranslationWorker, TranslationOptions


def test_translation_worker_emits_progress_and_writes_output(tmp_path, monkeypatch) -> None:
    import aisrt.translate_worker as worker_module

    source = tmp_path / "movie.srt"
    source.write_text(
        """1
00:00:00,000 --> 00:00:01,000
Hello.

2
00:00:01,100 --> 00:00:02,000
World.

3
00:00:02,100 --> 00:00:03,000
Again.
""",
        encoding="utf-8",
    )
    output = tmp_path / "movie.zh.srt"

    monkeypatch.setattr(worker_module, "load_translation_model", lambda **_kwargs: object())

    def fake_make_translator(_runtime: object, max_new_tokens: int):
        assert max_new_tokens == 128

        def translator(prompt: str) -> str:
            translated_lines: list[str] = []
            for line in prompt.splitlines():
                if "\t" not in line:
                    continue
                caption_id, _text = line.split("\t", 1)
                if caption_id.isdigit():
                    translated_lines.append(f"{caption_id}\t译文 {caption_id}")
            return "\n".join(translated_lines)

        return translator

    monkeypatch.setattr(worker_module, "make_model_translator", fake_make_translator)

    worker = SrtTranslationWorker(
        TranslationOptions(
            input_path=source,
            output_path=output,
            target_language="简体中文",
            chunk_size=2,
            context_size=1,
            max_new_tokens=128,
            overwrite=True,
        )
    )
    logs: list[str] = []
    progress: list[tuple[int, str]] = []
    finished: list[tuple[bool, str]] = []
    worker.log.connect(logs.append)
    worker.progress.connect(lambda percent, detail: progress.append((percent, detail)))
    worker.finished.connect(lambda success, message: finished.append((success, message)))

    worker.run()

    assert finished == [(True, str(output))]
    assert [percent for percent, _detail in progress] == [0, 50, 100, 100]
    assert progress[0][1] == "正在加载翻译模型"
    assert progress[-1][1] == "翻译完成"
    assert any("[TRANSLATE] 1/2 完成，总进度 50%" in log for log in logs)
    assert any(log.startswith("[TRANSLATE OK]") for log in logs)
    captions = parse_srt(output.read_text(encoding="utf-8"))
    assert [caption.text for caption in captions] == ["译文 1", "译文 2", "译文 3"]
    assert [(caption.start_ms, caption.end_ms) for caption in captions] == [
        (0, 1000),
        (1100, 2000),
        (2100, 3000),
    ]
