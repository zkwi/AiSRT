from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import html
import re
import time
from typing import Any

from .errors import ProcessingCancelled
from .local_asr import estimate_remaining_time
from .postprocess import Caption, format_srt, parse_srt


DEFAULT_TARGET_LANGUAGE = "简体中文"
DEFAULT_TRANSLATION_CHUNK_SIZE = 50
DEFAULT_CONTEXT_SIZE = 5
DEFAULT_TRANSLATION_MODEL = "tencent/HY-MT1.5-1.8B"
FAST_TRANSLATION_MODEL = "AngelSlim/Hy-MT1.5-1.8B-1.25bit"
TRANSLATION_MODEL_MODES = {
    "quality": DEFAULT_TRANSLATION_MODEL,
    "fast": FAST_TRANSLATION_MODEL,
}
TARGET_LANGUAGE_OPTIONS = [
    ("简体中文", "zh"),
    ("繁體中文", "zh-Hant"),
    ("English", "en"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("Français", "fr"),
    ("Deutsch", "de"),
    ("Español", "es"),
    ("Português", "pt"),
    ("Русский", "ru"),
    ("العربية", "ar"),
]

SN_RE = re.compile(r"<sn\s+id=[\"']?(?P<id>\d+)[\"']?\s*>(?P<text>.*?)</sn[s]?>", re.DOTALL)
NUMBERED_LINE_RE = re.compile(r"^\s*(?P<id>\d+)(?:\t|[:：]|\s+)(?P<text>.+?)\s*$")
Translator = Callable[[str], str]


@dataclass
class TranslationRuntime:
    tokenizer: Any
    model: Any
    torch: Any


def resolve_translation_model(model_mode: str = "quality", model_id: str | None = None) -> str:
    custom_model = (model_id or "").strip()
    if custom_model:
        return custom_model
    if model_mode not in TRANSLATION_MODEL_MODES:
        choices = "、".join(TRANSLATION_MODEL_MODES)
        raise ValueError(f"不支持的翻译模型模式: {model_mode}。可选: {choices}")
    return TRANSLATION_MODEL_MODES[model_mode]


def resolve_translation_torch_options(device: str = "auto", dtype: str = "auto") -> tuple[str, Any]:
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

    return resolved_device, resolved_dtype


def load_translation_model(
    model_id: str = DEFAULT_TRANSLATION_MODEL,
    device: str = "auto",
    dtype: str = "auto",
    local_files_only: bool = False,
) -> TranslationRuntime:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    resolved_device, resolved_dtype = resolve_translation_torch_options(device=device, dtype=dtype)
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        trust_remote_code=True,
        local_files_only=local_files_only,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    device_map: str | dict[str, str] | None
    if resolved_device.startswith("cuda"):
        device_map = "auto" if resolved_device == "cuda:0" else {"": resolved_device}
    else:
        device_map = None
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=resolved_dtype,
        device_map=device_map,
        trust_remote_code=True,
        local_files_only=local_files_only,
    )
    if resolved_device == "cpu":
        model = model.to("cpu")
    model.eval()
    return TranslationRuntime(tokenizer=tokenizer, model=model, torch=torch)


def translation_model_device(model: Any) -> Any:
    device = getattr(model, "device", None)
    if device is not None:
        return device
    return next(model.parameters()).device


def clean_translation_output(text: str) -> str:
    text = text.strip()
    for marker in [
        "<｜hy_place▁holder▁no▁2｜>",
        "<｜hy_place▁holder▁no▁8｜>",
        "<｜hy_end▁of▁sentence｜>",
        "<|endoftext|>",
    ]:
        text = text.replace(marker, "")
    return text.strip()


def translate_prompt_with_model(
    runtime: TranslationRuntime,
    prompt: str,
    max_new_tokens: int = 2048,
) -> str:
    tokenizer = runtime.tokenizer
    model = runtime.model
    torch = runtime.torch
    input_ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    )
    device = translation_model_device(model)
    input_ids = input_ids.to(device)
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": False,
        "temperature": None,
        "top_k": None,
        "top_p": None,
        "pad_token_id": tokenizer.pad_token_id or tokenizer.eos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if getattr(device, "type", str(device)).startswith("cuda"):
        torch.cuda.synchronize()
    with torch.inference_mode():
        output_ids = model.generate(input_ids, **generation_kwargs)
    if getattr(device, "type", str(device)).startswith("cuda"):
        torch.cuda.synchronize()
    generated_ids = output_ids[0, input_ids.shape[-1] :]
    return clean_translation_output(tokenizer.decode(generated_ids, skip_special_tokens=True))


def make_model_translator(runtime: TranslationRuntime, max_new_tokens: int = 2048) -> Translator:
    def translator(prompt: str) -> str:
        return translate_prompt_with_model(runtime, prompt, max_new_tokens=max_new_tokens)

    return translator


def chunk_captions(captions: Sequence[Caption], chunk_size: int = DEFAULT_TRANSLATION_CHUNK_SIZE) -> list[list[Caption]]:
    size = max(1, int(chunk_size))
    return [list(captions[index : index + size]) for index in range(0, len(captions), size)]


def is_chinese_target(target_language: str) -> bool:
    value = target_language.lower()
    return any(marker in value for marker in ["中文", "chinese", "汉语", "漢語"])


def build_translation_prompt(
    captions: Sequence[Caption],
    target_language: str = DEFAULT_TARGET_LANGUAGE,
    previous_context: Sequence[tuple[int, str, str]] | None = None,
) -> str:
    if is_chinese_target(target_language):
        lines = [
            f"将以下编号字幕逐行翻译为{target_language}。每行格式为“编号<TAB>文本”。",
            "要求：",
            "1. 只输出编号<TAB>译文，不要解释，不要输出 Markdown。",
            "2. 不要照抄原文；专有名词、品牌名和无法确定的名称可以保留。",
            "3. 不需要输出原 SRT 编号和时间轴，程序会自动合并时间轴。",
        ]
        if previous_context:
            lines.append("上一段上下文仅供术语一致性参考，不要输出：")
            for _caption_id, source, translated in previous_context:
                source_text = source.strip().replace("\n", " ")
                translated_text = translated.strip().replace("\n", " ")
                lines.append(f"源文：{source_text} / 译文：{translated_text}")
        lines.append("待翻译字幕：")
    else:
        lines = [
            f"Translate each numbered subtitle into {target_language}.",
            "Output only lines in this format: number<TAB>translation.",
            "Do not explain. Do not output Markdown.",
            "Do not copy the source unless it is a proper noun, brand name, or uncertain name.",
        ]
        if previous_context:
            lines.append("Previous context for terminology only; do not output:")
            for _caption_id, source, translated in previous_context:
                source_text = source.strip().replace("\n", " ")
                translated_text = translated.strip().replace("\n", " ")
                lines.append(f"Source: {source_text} / Translation: {translated_text}")
        lines.append("Subtitles to translate:")

    for caption in captions:
        text = caption.text.strip().replace("\n", " ")
        lines.append(f"{caption.index}\t{text}")
    return "\n".join(lines)


def parse_tagged_translations(output: str, expected_ids: Sequence[int]) -> dict[int, str]:
    translations: dict[int, str] = {}
    for line in output.splitlines():
        match = NUMBERED_LINE_RE.match(line.strip())
        if not match:
            continue
        caption_id = int(match.group("id"))
        text = match.group("text").strip()
        if text:
            translations[caption_id] = text

    for match in SN_RE.finditer(output):
        caption_id = int(match.group("id"))
        text = html.unescape(match.group("text")).strip()
        if text:
            translations[caption_id] = text

    if not translations and len(expected_ids) == 1:
        plain_lines = [
            line.strip()
            for line in clean_translation_output(output).splitlines()
            if line.strip() and not line.strip().startswith("```")
        ]
        if len(plain_lines) == 1:
            translations[expected_ids[0]] = plain_lines[0]

    missing = [caption_id for caption_id in expected_ids if caption_id not in translations]
    if missing:
        missing_text = "、".join(str(caption_id) for caption_id in missing)
        raise ValueError(f"翻译输出缺少字幕: {missing_text}")

    return {caption_id: translations[caption_id] for caption_id in expected_ids}


def translate_caption_chunk(
    captions: Sequence[Caption],
    target_language: str,
    translator: Translator,
    previous_context: Sequence[tuple[int, str, str]] | None = None,
    context_size: int = DEFAULT_CONTEXT_SIZE,
    should_stop: Callable[[], bool] | None = None,
) -> dict[int, str]:
    if should_stop and should_stop():
        raise ProcessingCancelled("用户已取消处理。")
    prompt = build_translation_prompt(captions, target_language=target_language, previous_context=previous_context)
    output = translator(prompt)
    if should_stop and should_stop():
        raise ProcessingCancelled("用户已取消处理。")
    expected_ids = [caption.index for caption in captions]
    try:
        return parse_tagged_translations(output, expected_ids=expected_ids)
    except ValueError:
        if len(captions) <= 1:
            raise

    middle = len(captions) // 2
    left_captions = captions[:middle]
    right_captions = captions[middle:]
    left = translate_caption_chunk(
        left_captions,
        target_language=target_language,
        translator=translator,
        previous_context=previous_context,
        context_size=context_size,
        should_stop=should_stop,
    )
    left_context = list(previous_context or [])
    left_context.extend((caption.index, caption.text, left[caption.index]) for caption in left_captions)
    right = translate_caption_chunk(
        right_captions,
        target_language=target_language,
        translator=translator,
        previous_context=left_context[-context_size:],
        context_size=context_size,
        should_stop=should_stop,
    )
    return {**left, **right}


def translate_srt_text(
    srt_text: str,
    target_language: str = DEFAULT_TARGET_LANGUAGE,
    translator: Translator | None = None,
    chunk_size: int = DEFAULT_TRANSLATION_CHUNK_SIZE,
    context_size: int = DEFAULT_CONTEXT_SIZE,
    progress: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> str:
    if translator is None:
        raise ValueError("缺少 translator，无法执行翻译。")

    captions = parse_srt(srt_text)
    if not captions:
        return ""

    log = progress or (lambda _message: None)
    translated_by_id: dict[int, str] = {}
    previous_context: list[tuple[int, str, str]] = []
    chunks = chunk_captions(captions, chunk_size=chunk_size)
    started_at = time.perf_counter()

    for chunk_index, chunk in enumerate(chunks, start=1):
        if should_stop and should_stop():
            raise ProcessingCancelled("用户已取消处理。")
        log(f"[TRANSLATE] {chunk_index}/{len(chunks)} 开始")
        translated = translate_caption_chunk(
            chunk,
            target_language=target_language,
            translator=translator,
            previous_context=previous_context[-context_size:],
            context_size=context_size,
            should_stop=should_stop,
        )
        translated_by_id.update(translated)
        previous_context.extend((caption.index, caption.text, translated[caption.index]) for caption in chunk)
        percent = int(chunk_index / len(chunks) * 100)
        elapsed = time.perf_counter() - started_at
        remaining = estimate_remaining_time(elapsed, chunk_index, len(chunks))
        log(f"[TRANSLATE] {chunk_index}/{len(chunks)} 完成，总进度 {percent}%，剩余 {remaining}")

    translated_captions = [
        Caption(
            index=caption.index,
            start_ms=caption.start_ms,
            end_ms=caption.end_ms,
            text=translated_by_id[caption.index],
        )
        for caption in captions
    ]
    return format_srt(translated_captions)
