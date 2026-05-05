from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from .local_translate import (
    DEFAULT_CONTEXT_SIZE,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_TRANSLATION_CHUNK_SIZE,
    TARGET_LANGUAGE_OPTIONS,
    Translator,
    load_translation_model,
    make_model_translator,
    resolve_translation_model,
    translate_srt_text,
)
from .user_messages import friendly_error_message


LANGUAGE_SUFFIX_ALIASES = {
    "simplified chinese": "zh",
    "chinese": "zh",
    "简体": "zh",
    "简体中文": "zh",
    "简體中文": "zh",
    "中文": "zh",
    "traditional chinese": "zh-Hant",
    "繁体": "zh-Hant",
    "繁體": "zh-Hant",
    "繁体中文": "zh-Hant",
    "繁體中文": "zh-Hant",
    "english": "en",
    "英语": "en",
    "英語": "en",
    "japanese": "ja",
    "日语": "ja",
    "日語": "ja",
    "日本语": "ja",
    "日本語": "ja",
    "korean": "ko",
    "韩语": "ko",
    "韓語": "ko",
    "한국어": "ko",
    "french": "fr",
    "法语": "fr",
    "法語": "fr",
    "german": "de",
    "德语": "de",
    "德語": "de",
    "spanish": "es",
    "西班牙语": "es",
    "西班牙語": "es",
    "portuguese": "pt",
    "葡萄牙语": "pt",
    "葡萄牙語": "pt",
    "russian": "ru",
    "俄语": "ru",
    "俄語": "ru",
    "arabic": "ar",
    "阿拉伯语": "ar",
    "阿拉伯語": "ar",
}


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必须是正整数")
    return number


def language_suffix(target_language: str) -> str:
    normalized = target_language.strip().lower()
    for label, suffix in TARGET_LANGUAGE_OPTIONS:
        if normalized == label.lower():
            return suffix
    if normalized in LANGUAGE_SUFFIX_ALIASES:
        return LANGUAGE_SUFFIX_ALIASES[normalized]
    safe = "".join(char for char in normalized if char.isascii() and char.isalnum())
    return safe or "translated"


def default_output_path(input_path: Path, target_language: str) -> Path:
    return input_path.with_name(f"{input_path.stem}.{language_suffix(target_language)}.srt")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-sub-translate",
        description="使用本地 HY-MT 大模型翻译 SRT 字幕。",
    )
    parser.add_argument("input", help="待翻译的 .srt 文件")
    parser.add_argument("--to", dest="target_language", default=DEFAULT_TARGET_LANGUAGE, help="目标语言，默认简体中文")
    parser.add_argument("--output", help="输出 SRT 路径，默认在原文件旁生成目标语言后缀")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有输出")
    parser.add_argument(
        "--model-mode",
        choices=["quality", "fast"],
        default="quality",
        help="翻译模型模式：quality 使用官方模型，fast 使用轻量量化模型",
    )
    parser.add_argument("--model", help="自定义翻译模型路径或 Hugging Face ID；设置后覆盖 --model-mode")
    parser.add_argument("--chunk-size", type=positive_int, default=DEFAULT_TRANSLATION_CHUNK_SIZE, help="每轮翻译的字幕条数")
    parser.add_argument("--context-size", type=positive_int, default=DEFAULT_CONTEXT_SIZE, help="传给下一轮的上下文条数")
    parser.add_argument("--device", default="auto", help="推理设备：auto、cuda:0 或 cpu，默认 auto")
    parser.add_argument("--dtype", choices=["auto", "bfloat16", "float16", "float32"], default="auto", help="模型 dtype，默认 auto")
    parser.add_argument("--max-new-tokens", type=positive_int, default=2048, help="每轮翻译最大生成 token 数")
    parser.add_argument("--local-files-only", action="store_true", help="只使用本地已下载模型，不联网下载权重")
    return parser


def ensure_srt_input(input_path: Path) -> None:
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(f"找不到 SRT 文件: {input_path}")
    if input_path.suffix.lower() != ".srt":
        raise ValueError(f"只支持 .srt 文件: {input_path}")


def ensure_output_can_be_written(output_path: Path, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"输出已存在，请加 --overwrite: {output_path}")


def run_translation(args: argparse.Namespace, translator: Translator | None = None) -> Path:
    input_path = Path(args.input).expanduser().resolve()
    ensure_srt_input(input_path)
    output_path = Path(args.output).expanduser().resolve() if args.output else default_output_path(input_path, args.target_language)
    ensure_output_can_be_written(output_path, overwrite=args.overwrite)

    if translator is None:
        model_id = resolve_translation_model(args.model_mode, args.model)
        print(f"[LOAD] Translate={model_id}")
        runtime = load_translation_model(
            model_id=model_id,
            device=args.device,
            dtype=args.dtype,
            local_files_only=args.local_files_only,
        )
        translator = make_model_translator(runtime, max_new_tokens=args.max_new_tokens)

    source = input_path.read_text(encoding="utf-8-sig")
    translated = translate_srt_text(
        source,
        target_language=args.target_language,
        translator=translator,
        chunk_size=args.chunk_size,
        context_size=args.context_size,
        progress=print,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(translated, encoding="utf-8")
    print(f"[OK] {output_path}")
    return output_path


def main(argv: Sequence[str] | None = None, translator: Translator | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))

    try:
        run_translation(args, translator=translator)
    except Exception as exc:
        print(f"错误: {friendly_error_message(exc)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
