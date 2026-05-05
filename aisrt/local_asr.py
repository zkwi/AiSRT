from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from .errors import ProcessingCancelled
from .postprocess import Caption, format_srt


DEFAULT_ALIGNER = "Qwen/Qwen3-ForcedAligner-0.6B"
DEFAULT_MODEL_SIZE = "1.7B"
ASR_MODEL_SIZES = {
    "1.7B": "Qwen/Qwen3-ASR-1.7B",
    "0.6B": "Qwen/Qwen3-ASR-0.6B",
}
DEFAULT_MODEL = ASR_MODEL_SIZES[DEFAULT_MODEL_SIZE]
DEFAULT_LANGUAGE = ""
DEFAULT_MAX_NEW_TOKENS = 1536
SUPPORTED_ASR_LANGUAGES = [
    "Chinese",
    "English",
    "Cantonese",
    "Arabic",
    "German",
    "French",
    "Spanish",
    "Portuguese",
    "Indonesian",
    "Italian",
    "Korean",
    "Russian",
    "Thai",
    "Vietnamese",
    "Japanese",
    "Turkish",
    "Hindi",
    "Malay",
    "Dutch",
    "Swedish",
    "Danish",
    "Finnish",
    "Polish",
    "Czech",
    "Filipino",
    "Persian",
    "Greek",
    "Romanian",
    "Hungarian",
    "Macedonian",
]
DEFAULT_CHUNK_SECONDS = 45
BREAK_PUNCTUATION = "。！？!?"
Progress = Callable[[str], None]


@dataclass
class TextPiece:
    text: str
    start_ms: int
    end_ms: int


@dataclass
class MatchedItem:
    token: str
    text_start: int | None
    text_end: int | None
    start_ms: int
    end_ms: int


def resolve_asr_model(model_size: str = DEFAULT_MODEL_SIZE, model_path: str | None = None) -> str:
    custom_model = (model_path or "").strip()
    if custom_model:
        return custom_model

    if model_size not in ASR_MODEL_SIZES:
        choices = "、".join(ASR_MODEL_SIZES)
        raise ValueError(f"不支持的 ASR 模型尺寸: {model_size}。可选: {choices}")
    return ASR_MODEL_SIZES[model_size]


def resolve_asr_language(language: str | None = DEFAULT_LANGUAGE) -> str:
    value = (language or "").strip()
    if not value or value.lower() == "auto" or value in {"自动", "自动识别"}:
        return DEFAULT_LANGUAGE

    normalized = value[:1].upper() + value[1:].lower()
    if normalized not in SUPPORTED_ASR_LANGUAGES:
        choices = "、".join(["auto", *SUPPORTED_ASR_LANGUAGES])
        raise ValueError(f"不支持的识别语言: {value}。可选: {choices}")
    return normalized


def resolve_torch_options(
    device: str = "auto",
    dtype: str = "auto",
    local_files_only: bool = False,
    flash_attention: bool = False,
) -> dict[str, Any]:
    import torch

    if device == "auto":
        resolved_device = "cuda:0" if torch.cuda.is_available() else "cpu"
    elif device == "cuda":
        resolved_device = "cuda:0"
    else:
        resolved_device = device

    if resolved_device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("当前 PyTorch 环境未检测到 CUDA，请改用 --device cpu 或安装 CUDA 版 PyTorch。")

    if dtype == "auto":
        if resolved_device.startswith("cuda"):
            resolved_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            resolved_dtype = torch.float32
    else:
        dtype_map = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        if dtype not in dtype_map:
            raise ValueError(f"不支持的 dtype: {dtype}")
        resolved_dtype = dtype_map[dtype]

    options: dict[str, Any] = {
        "device_map": resolved_device,
        "dtype": resolved_dtype,
        "local_files_only": local_files_only,
    }
    if flash_attention:
        options["attn_implementation"] = "flash_attention_2"
    return options


def load_local_model(
    model_path: str = DEFAULT_MODEL,
    aligner_path: str = DEFAULT_ALIGNER,
    device: str = "auto",
    dtype: str = "auto",
    batch_size: int = 1,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    local_files_only: bool = False,
    flash_attention: bool = False,
) -> Any:
    from qwen_asr import Qwen3ASRModel

    model_options = resolve_torch_options(
        device=device,
        dtype=dtype,
        local_files_only=local_files_only,
        flash_attention=flash_attention,
    )
    aligner_options = dict(model_options)

    return Qwen3ASRModel.from_pretrained(
        model_path,
        forced_aligner=aligner_path,
        forced_aligner_kwargs=aligner_options,
        max_inference_batch_size=batch_size,
        max_new_tokens=max_new_tokens,
        **model_options,
    )


def seconds_to_ms(value: float) -> int:
    return round(float(value) * 1000)


def safe_item_text(item: Any) -> str:
    return str(getattr(item, "text", "") or "").strip()


def match_align_items(text: str, align_result: Any) -> list[MatchedItem]:
    items = list(getattr(align_result, "items", []) or [])
    matched: list[MatchedItem] = []
    cursor = 0

    for item in items:
        token = safe_item_text(item)
        if not token:
            continue

        start = text.find(token, cursor)
        if start >= 0:
            end = start + len(token)
            cursor = end
        else:
            start = None
            end = None

        matched.append(
            MatchedItem(
                token=token,
                text_start=start,
                text_end=end,
                start_ms=seconds_to_ms(getattr(item, "start_time", 0)),
                end_ms=seconds_to_ms(getattr(item, "end_time", 0)),
            )
        )

    return matched


def next_text_start(matched: list[MatchedItem], index: int, default: int) -> int:
    for later in matched[index + 1 :]:
        if later.text_start is not None:
            return later.text_start
    return default


def align_items_to_text_pieces(text: str, align_result: Any) -> list[TextPiece]:
    matched = match_align_items(text, align_result)
    pieces: list[TextPiece] = []
    for index, current in enumerate(matched):
        if current.text_start is None or current.text_end is None:
            piece_text = current.token
        else:
            next_start = next_text_start(matched, index, len(text))
            piece_text = text[current.text_start : next_start]
            if index == 0 and current.text_start > 0:
                piece_text = text[: current.text_start] + piece_text

        piece_text = piece_text.strip()
        if piece_text:
            pieces.append(TextPiece(piece_text, current.start_ms, current.end_ms))

    return pieces


def fallback_pieces_from_items(align_result: Any) -> list[TextPiece]:
    pieces: list[TextPiece] = []
    for item in list(getattr(align_result, "items", []) or []):
        text = safe_item_text(item)
        if not text:
            continue
        pieces.append(
            TextPiece(
                text=text,
                start_ms=seconds_to_ms(getattr(item, "start_time", 0)),
                end_ms=seconds_to_ms(getattr(item, "end_time", 0)),
            )
        )
    return pieces


def offset_align_result(align_result: Any, offset_sec: float) -> Any:
    if align_result is None:
        return None

    items = []
    for item in list(getattr(align_result, "items", []) or []):
        items.append(
            type(item)(
                text=getattr(item, "text", ""),
                start_time=round(float(getattr(item, "start_time", 0)) + offset_sec, 3),
                end_time=round(float(getattr(item, "end_time", 0)) + offset_sec, 3),
            )
        )
    return type(align_result)(items=items)


def pieces_to_captions(pieces: list[TextPiece], max_caption_chars: int = 44) -> list[Caption]:
    captions: list[Caption] = []
    current_text = ""
    current_start = 0
    current_end = 0

    def flush() -> None:
        nonlocal current_text, current_start, current_end
        text = current_text.strip()
        if text:
            captions.append(
                Caption(
                    index=len(captions) + 1,
                    start_ms=current_start,
                    end_ms=max(current_end, current_start + 500),
                    text=text,
                )
            )
        current_text = ""
        current_start = 0
        current_end = 0

    for piece in pieces:
        if not current_text:
            current_start = piece.start_ms

        if current_text and len(current_text) + len(piece.text) > max_caption_chars:
            flush()
            current_start = piece.start_ms

        current_text += piece.text
        current_end = piece.end_ms

        if current_text.endswith(tuple(BREAK_PUNCTUATION)) or len(current_text) >= max_caption_chars:
            flush()

    flush()
    return captions


def transcription_to_srt(text: str, align_result: Any, max_caption_chars: int = 44) -> str:
    return format_srt(transcription_to_captions(text, align_result, max_caption_chars=max_caption_chars))


def transcription_to_captions(text: str, align_result: Any, max_caption_chars: int = 44) -> list[Caption]:
    pieces = align_items_to_text_pieces(text, align_result)
    if not pieces:
        pieces = fallback_pieces_from_items(align_result)
    return pieces_to_captions(pieces, max_caption_chars=max_caption_chars)


def fallback_captions_for_chunk(
    text: str,
    offset_sec: float,
    chunk_seconds: float,
    max_caption_chars: int = 44,
) -> list[Caption]:
    text = text.strip()
    if not text:
        return []

    # 对齐器偶尔会对长静音或噪声片段返回空结果；保留文本比中断整部电影更实用。
    piece = TextPiece(
        text=text,
        start_ms=seconds_to_ms(offset_sec),
        end_ms=seconds_to_ms(offset_sec + chunk_seconds),
    )
    return pieces_to_captions([piece], max_caption_chars=max_caption_chars)


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    size = max(1, int(size))
    return [items[index : index + size] for index in range(0, len(items), size)]


def merge_language_names(languages: list[str]) -> str:
    result: list[str] = []
    previous = ""
    for language in languages:
        language = language.strip()
        if language and language != previous:
            result.append(language)
            previous = language
    return ",".join(result)


def format_remaining_time(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def estimate_remaining_time(elapsed_seconds: float, completed: int, total: int) -> str:
    if completed <= 0 or total <= 0 or completed >= total:
        return "00:00"
    average_seconds = elapsed_seconds / completed
    return format_remaining_time(average_seconds * (total - completed))


def transcribe_to_srt_text(
    model: Any,
    media_path: str,
    context: str = "",
    language: str = DEFAULT_LANGUAGE,
    max_caption_chars: int = 44,
    chunk_seconds: int = DEFAULT_CHUNK_SECONDS,
    batch_size: int = 1,
    progress: Progress | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> tuple[str, str, str]:
    from qwen_asr.inference.utils import SAMPLE_RATE, normalize_audio_input, split_audio_into_chunks

    log = progress or (lambda _message: None)
    wav = normalize_audio_input(media_path)
    chunks = split_audio_into_chunks(
        wav,
        SAMPLE_RATE,
        max_chunk_sec=chunk_seconds,
    )
    total = len(chunks)
    audio_minutes = len(wav) / SAMPLE_RATE / 60
    log(f"[ASR] 音频时长约 {audio_minutes:.1f} 分钟，分为 {total} 个识别块")

    transcript_parts: list[str] = []
    languages: list[str] = []
    captions: list[Caption] = []

    indexed_chunks = list(enumerate(chunks, start=1))
    overall_started_at = time.perf_counter()
    for batch in chunked(indexed_chunks, batch_size):
        if should_stop and should_stop():
            raise ProcessingCancelled("用户已取消处理。")

        for index, (chunk_wav, offset_sec) in batch:
            chunk_duration = len(chunk_wav) / SAMPLE_RATE
            start_min = offset_sec / 60
            end_min = (offset_sec + chunk_duration) / 60
            log(f"[ASR] {index}/{total} 开始 {start_min:.1f}-{end_min:.1f} 分钟")

        started_at = time.perf_counter()
        if len(batch) == 1:
            audio_input: Any = (batch[0][1][0], SAMPLE_RATE)
        else:
            audio_input = [(chunk_wav, SAMPLE_RATE) for _, (chunk_wav, _offset_sec) in batch]
        results = model.transcribe(
            audio=audio_input,
            context=context or "",
            language=language,
            return_time_stamps=True,
        )
        if should_stop and should_stop():
            raise ProcessingCancelled("用户已取消处理。")

        if not results:
            first_index = batch[0][0]
            raise RuntimeError(f"本地 Qwen3-ASR 没有返回识别结果，块 {first_index}/{total}。")
        if len(results) != len(batch):
            raise RuntimeError(f"本地 Qwen3-ASR 返回数量异常: 预期 {len(batch)}，实际 {len(results)}。")

        elapsed = time.perf_counter() - started_at
        for result, (index, (chunk_wav, offset_sec)) in zip(results, batch):
            chunk_duration = len(chunk_wav) / SAMPLE_RATE
            text = str(getattr(result, "text", "") or "").strip()
            language_name = str(getattr(result, "language", "") or "").strip()
            align_result = getattr(result, "time_stamps", None)

            transcript_parts.append(text)
            languages.append(language_name)

            if align_result is None:
                if text:
                    log(f"[ASR] {index}/{total} 无时间戳，使用该识别块时间范围生成粗略字幕")
                    captions.extend(
                        fallback_captions_for_chunk(
                            text,
                            offset_sec,
                            chunk_duration,
                            max_caption_chars=max_caption_chars,
                        )
                    )
                else:
                    log(f"[ASR] {index}/{total} 无识别文本，跳过字幕生成")
            else:
                shifted_align_result = offset_align_result(align_result, offset_sec)
                captions.extend(
                    transcription_to_captions(
                        text,
                        shifted_align_result,
                        max_caption_chars=max_caption_chars,
                    )
            )

            percent = int(index / total * 100)
            remaining = estimate_remaining_time(time.perf_counter() - overall_started_at, index, total)
            log(f"[ASR] {index}/{total} 完成，用时 {elapsed:.1f}s，总进度 {percent}%，剩余 {remaining}")

    return merge_language_names(languages), "".join(transcript_parts), format_srt(captions)
