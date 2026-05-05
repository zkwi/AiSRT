from dataclasses import dataclass
from pathlib import Path
import sys
import types

import pytest

from aisrt import cli as cli_module
from aisrt.cli import (
    audio_extract_filter,
    build_parser,
    cached_audio_path,
    ensure_outputs_can_be_written,
    is_valid_cached_audio,
    parse_ffmpeg_out_time,
    remove_intermediate_outputs,
    subprocess_no_window_kwargs,
)
from aisrt.local_asr import (
    ASR_MODEL_SIZES,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_MODEL_SIZE,
    SUPPORTED_ASR_LANGUAGES,
    align_items_to_text_pieces,
    estimate_remaining_time,
    fallback_captions_for_chunk,
    format_remaining_time,
    resolve_asr_language,
    resolve_asr_model,
    transcribe_to_srt_text,
    transcription_to_srt,
)
from aisrt.postprocess import parse_srt


@dataclass
class Item:
    text: str
    start_time: float
    end_time: float


@dataclass
class AlignResult:
    items: list[Item]


def test_align_items_keep_punctuation_from_transcript():
    text = "今日はいい天気ですね。映画を見ます。"
    align = AlignResult(
        [
            Item("今日", 0.0, 0.2),
            Item("は", 0.2, 0.3),
            Item("いい", 0.3, 0.6),
            Item("天気", 0.6, 1.0),
            Item("です", 1.0, 1.3),
            Item("ね", 1.3, 1.5),
            Item("映画", 2.0, 2.3),
            Item("を", 2.3, 2.4),
            Item("見ます", 2.4, 2.8),
        ]
    )

    pieces = align_items_to_text_pieces(text, align)

    assert "".join(piece.text for piece in pieces) == text
    assert pieces[5].text == "ね。"
    assert pieces[-1].text == "見ます。"


def test_transcription_to_srt_groups_by_cjk_punctuation():
    text = "今日はいい天気ですね。映画を見ます。"
    align = AlignResult(
        [
            Item("今日", 0.0, 0.2),
            Item("は", 0.2, 0.3),
            Item("いい", 0.3, 0.6),
            Item("天気", 0.6, 1.0),
            Item("です", 1.0, 1.3),
            Item("ね", 1.3, 1.5),
            Item("映画", 2.0, 2.3),
            Item("を", 2.3, 2.4),
            Item("見ます", 2.4, 2.8),
        ]
    )

    result = transcription_to_srt(text, align, max_caption_chars=44)
    captions = parse_srt(result)

    assert len(captions) == 2
    assert captions[0].text == "今日はいい天気ですね。"
    assert captions[0].start_ms == 0
    assert captions[0].end_ms == 1500
    assert captions[1].text == "映画を見ます。"


def test_fallback_captions_cover_chunk_when_timestamps_are_missing():
    captions = fallback_captions_for_chunk("今日はいい天気ですね。", 10.0, 5.0)

    assert len(captions) == 1
    assert captions[0].text == "今日はいい天気ですね。"
    assert captions[0].start_ms == 10000
    assert captions[0].end_ms == 15000


def test_fallback_captions_skip_empty_text():
    assert fallback_captions_for_chunk("", 10.0, 5.0) == []


def test_remaining_time_helpers_format_minutes_and_seconds():
    assert format_remaining_time(65.4) == "01:05"
    assert estimate_remaining_time(30.0, completed=1, total=3) == "01:00"
    assert estimate_remaining_time(30.0, completed=3, total=3) == "00:00"


def install_fake_qwen_utils(monkeypatch, chunks):
    qwen_package = types.ModuleType("qwen_asr")
    qwen_package.__path__ = []
    inference_package = types.ModuleType("qwen_asr.inference")
    inference_package.__path__ = []
    utils_module = types.ModuleType("qwen_asr.inference.utils")
    utils_module.SAMPLE_RATE = 16000
    utils_module.normalize_audio_input = lambda _path: [0] * 32000
    utils_module.split_audio_into_chunks = lambda _wav, _sample_rate, **_kwargs: chunks

    monkeypatch.setitem(sys.modules, "qwen_asr", qwen_package)
    monkeypatch.setitem(sys.modules, "qwen_asr.inference", inference_package)
    monkeypatch.setitem(sys.modules, "qwen_asr.inference.utils", utils_module)


def test_transcribe_to_srt_text_falls_back_when_timestamps_are_missing(monkeypatch):
    install_fake_qwen_utils(monkeypatch, [([0] * 32000, 10.0)])

    @dataclass
    class Result:
        language: str = "Japanese"
        text: str = "今日はいい天気ですね。"
        time_stamps: object | None = None

    class Model:
        def transcribe(self, **_kwargs):
            return [Result()]

    messages: list[str] = []
    language, transcript, srt_text = transcribe_to_srt_text(Model(), "dummy.wav", progress=messages.append)
    captions = parse_srt(srt_text)

    assert language == "Japanese"
    assert transcript == "今日はいい天気ですね。"
    assert any("无时间戳" in message for message in messages)
    assert any("总进度 100%，剩余 00:00" in message for message in messages)
    assert len(captions) == 1
    assert captions[0].start_ms == 10000
    assert captions[0].end_ms == 12000


def test_transcribe_to_srt_text_batches_chunks_without_changing_order(monkeypatch):
    install_fake_qwen_utils(
        monkeypatch,
        [
            ([0] * 16000, 0.0),
            ([0] * 16000, 1.0),
            ([0] * 16000, 2.0),
        ],
    )

    @dataclass
    class Result:
        language: str
        text: str
        time_stamps: object | None = None

    class Model:
        def __init__(self):
            self.batch_sizes: list[int] = []
            self.count = 0

        def transcribe(self, **kwargs):
            audio = kwargs["audio"]
            audio_items = [audio] if isinstance(audio, tuple) else audio
            self.batch_sizes.append(len(audio_items))
            results = []
            for _item in audio_items:
                self.count += 1
                results.append(Result(language="Japanese", text=f"字幕{self.count}。"))
            return results

    model = Model()
    language, transcript, srt_text = transcribe_to_srt_text(model, "dummy.wav", batch_size=2)
    captions = parse_srt(srt_text)

    assert model.batch_sizes == [2, 1]
    assert language == "Japanese"
    assert transcript == "字幕1。字幕2。字幕3。"
    assert [caption.text for caption in captions] == ["字幕1。", "字幕2。", "字幕3。"]


def test_cached_audio_path_uses_source_path_hash():
    first = cached_audio_path(Path("a/movie.mp4"), Path(".cache"))
    second = cached_audio_path(Path("b/movie.mp4"), Path(".cache"))

    assert first != second
    assert first.suffix == ".wav"
    assert first.name.startswith("movie.")


def test_stale_intermediate_outputs_do_not_block_and_are_removed(tmp_path):
    media = tmp_path / "movie.mp4"
    media.write_bytes(b"input")
    raw_srt = tmp_path / "movie.raw.srt"
    txt = tmp_path / "movie.txt"
    raw_srt.write_text("raw", encoding="utf-8")
    txt.write_text("txt", encoding="utf-8")

    ensure_outputs_can_be_written(media, tmp_path, overwrite=False)
    remove_intermediate_outputs(media, tmp_path)

    assert not raw_srt.exists()
    assert not txt.exists()


def test_parse_ffmpeg_out_time_reads_seconds():
    assert parse_ffmpeg_out_time("out_time_ms=12500000") == 12.5
    assert parse_ffmpeg_out_time("progress=continue") is None


def test_windows_subprocesses_hide_console(monkeypatch):
    monkeypatch.setattr(cli_module, "CREATE_NO_WINDOW", 0x08000000)

    assert subprocess_no_window_kwargs("nt") == {"creationflags": 0x08000000}
    assert subprocess_no_window_kwargs("posix") == {}


def test_audio_extract_filter_downmixes_stereo_and_keeps_mono():
    assert "pan=mono" in audio_extract_filter(2)
    assert "pan=mono" not in audio_extract_filter(1)
    assert "aresample=16000" in audio_extract_filter(2)


def test_invalid_zero_byte_cached_audio_is_rejected(tmp_path):
    media = tmp_path / "movie.mp4"
    wav = tmp_path / "movie.wav"
    media.write_bytes(b"input")
    wav.write_bytes(b"")

    assert not is_valid_cached_audio(wav, media)


def test_partial_cached_audio_is_rejected_when_duration_is_known(tmp_path):
    media = tmp_path / "movie.mp4"
    wav = tmp_path / "movie.wav"
    media.write_bytes(b"input")
    wav.write_bytes(b"0" * 1000)

    assert not is_valid_cached_audio(wav, media, duration=60)


def test_cli_rejects_non_positive_numeric_options():
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["movie.mp4", "-j", "0"])


def test_asr_model_size_presets_resolve_to_official_model_ids():
    assert DEFAULT_MODEL_SIZE == "1.7B"
    assert ASR_MODEL_SIZES["1.7B"] == "Qwen/Qwen3-ASR-1.7B"
    assert ASR_MODEL_SIZES["0.6B"] == "Qwen/Qwen3-ASR-0.6B"
    assert resolve_asr_model("0.6B") == "Qwen/Qwen3-ASR-0.6B"


def test_custom_model_path_overrides_size_preset():
    assert resolve_asr_model("0.6B", "models/custom-asr") == "models/custom-asr"


def test_cli_accepts_model_size_and_custom_model_override():
    parser = build_parser()

    args = parser.parse_args(["movie.mp4", "--model-size", "0.6B"])
    assert args.model_size == "0.6B"
    assert args.model is None

    args = parser.parse_args(["movie.mp4", "--model-size", "0.6B", "--model", "models/custom"])
    assert args.model_size == "0.6B"
    assert args.model == "models/custom"


def test_language_defaults_to_auto_and_normalizes_supported_names():
    assert DEFAULT_LANGUAGE == ""
    assert "Japanese" in SUPPORTED_ASR_LANGUAGES
    assert "English" in SUPPORTED_ASR_LANGUAGES
    assert resolve_asr_language("auto") == ""
    assert resolve_asr_language("自动识别") == ""
    assert resolve_asr_language("english") == "English"

    with pytest.raises(ValueError):
        resolve_asr_language("Klingon")


def test_cli_language_option_defaults_to_auto():
    parser = build_parser()

    args = parser.parse_args(["movie.mp4"])
    assert args.language == "auto"

    args = parser.parse_args(["movie.mp4", "--language", "English"])
    assert args.language == "English"


def test_cli_uses_balanced_asr_generation_limit_by_default():
    parser = build_parser()

    args = parser.parse_args(["movie.mp4"])

    assert DEFAULT_MAX_NEW_TOKENS == 1536
    assert args.max_new_tokens == DEFAULT_MAX_NEW_TOKENS


def test_cli_load_message_marks_custom_model(monkeypatch, capsys, tmp_path):
    media = tmp_path / "movie.mp4"
    media.write_bytes(b"input")

    monkeypatch.setattr(cli_module, "collect_inputs", lambda _path, recursive=False: [media])
    monkeypatch.setattr(cli_module, "output_jobs", lambda files, _out_dir=None: [(files[0], tmp_path)])
    monkeypatch.setattr(cli_module, "ensure_outputs_can_be_written", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli_module, "process_one", lambda **_kwargs: None)

    loaded: dict[str, object] = {}

    def fake_load_local_model(**kwargs):
        loaded.update(kwargs)
        return object()

    monkeypatch.setattr(cli_module, "load_local_model", fake_load_local_model)

    exit_code = cli_module.main(["movie.mp4", "--model-size", "0.6B", "--model", "models/custom"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "[LOAD] ASR=models/custom (custom)" in output
    assert "size=0.6B" not in output
    assert loaded["model_path"] == "models/custom"


def test_cli_passes_resolved_language_to_processor(monkeypatch, tmp_path):
    media = tmp_path / "movie.mp4"
    media.write_bytes(b"input")

    monkeypatch.setattr(cli_module, "collect_inputs", lambda _path, recursive=False: [media])
    monkeypatch.setattr(cli_module, "output_jobs", lambda files, _out_dir=None: [(files[0], tmp_path)])
    monkeypatch.setattr(cli_module, "ensure_outputs_can_be_written", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli_module, "load_local_model", lambda **_kwargs: object())

    processed: dict[str, object] = {}

    def fake_process_one(**kwargs):
        processed.update(kwargs)

    monkeypatch.setattr(cli_module, "process_one", fake_process_one)

    assert cli_module.main(["movie.mp4"]) == 0
    assert processed["language"] == ""

    processed.clear()
    assert cli_module.main(["movie.mp4", "--language", "English"]) == 0
    assert processed["language"] == "English"
