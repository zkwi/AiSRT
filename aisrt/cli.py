from __future__ import annotations

import argparse
from collections import deque
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Callable

from .diagnostics import blocking_messages, format_diagnostics, run_diagnostics
from .errors import ProcessingCancelled
from .local_asr import (
    ASR_MODEL_SIZES,
    DEFAULT_ALIGNER,
    DEFAULT_CHUNK_SECONDS,
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_MODEL_SIZE,
    SUPPORTED_ASR_LANGUAGES,
    load_local_model,
    resolve_asr_language,
    resolve_asr_model,
    transcribe_to_srt_text,
)
from .postprocess import postprocess_srt_text
from .translate_cli import default_output_path
from .user_messages import friendly_error_message


MEDIA_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".m4v",
    ".webm",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
}
MIN_VALID_WAV_BYTES = 44
AUDIO_BYTES_PER_SECOND = 16000 * 2
AUDIO_CACHE_VERSION = "v3"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
Progress = Callable[[str], None]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("必须是大于 0 的整数")
    return parsed


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def subprocess_no_window_kwargs(platform: str = os.name) -> dict[str, int]:
    if platform == "nt" and CREATE_NO_WINDOW:
        return {"creationflags": CREATE_NO_WINDOW}
    return {}


def is_media_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS


def collect_inputs(input_path: Path, recursive: bool) -> list[Path]:
    if input_path.is_file():
        if not is_media_file(input_path):
            raise ValueError(f"不支持的文件格式: {input_path}")
        return [input_path]

    if not input_path.is_dir():
        raise FileNotFoundError(f"输入不存在: {input_path}")

    iterator = input_path.rglob("*") if recursive else input_path.glob("*")
    files = sorted(path for path in iterator if is_media_file(path))
    if not files:
        raise FileNotFoundError(f"没有找到可处理的媒体文件: {input_path}")
    return files


def output_target_paths(
    media_path: Path,
    out_dir: Path,
    translation_target_language: str | None = None,
) -> list[Path]:
    stem = media_path.stem
    final_srt = out_dir / f"{stem}.srt"
    targets = [final_srt]
    if translation_target_language:
        targets.append(default_output_path(final_srt, translation_target_language))
    return targets


def ensure_outputs_can_be_written(
    media_path: Path,
    out_dir: Path,
    overwrite: bool,
    translation_target_language: str | None = None,
) -> None:
    targets = output_target_paths(media_path, out_dir, translation_target_language=translation_target_language)
    conflicts = [path for path in targets if path.exists()]

    if conflicts and not overwrite:
        conflict_list = "\n".join(f"  - {path}" for path in conflicts)
        raise FileExistsError(f"输出已存在，请加 --overwrite:\n{conflict_list}")


def remove_intermediate_outputs(media_path: Path, out_dir: Path) -> None:
    for suffix in (".raw.srt", ".txt"):
        path = out_dir / f"{media_path.stem}{suffix}"
        if path.exists():
            path.unlink()


def output_jobs(files: list[Path], out_dir: str | None) -> list[tuple[Path, Path]]:
    fixed_out_dir = Path(out_dir).expanduser().resolve() if out_dir else None
    return [(media_path, fixed_out_dir or media_path.parent) for media_path in files]


def cached_audio_path(media_path: Path, cache_dir: Path) -> Path:
    key_text = f"{AUDIO_CACHE_VERSION}:{media_path.resolve()}"
    key = hashlib.sha1(key_text.encode("utf-8")).hexdigest()[:10]
    return cache_dir / f"{media_path.stem}.{key}.wav"


def is_valid_cached_audio(wav_path: Path, media_path: Path, duration: float = 0.0) -> bool:
    if not wav_path.exists() or wav_path.stat().st_mtime < media_path.stat().st_mtime:
        return False

    actual_size = wav_path.stat().st_size
    if actual_size <= MIN_VALID_WAV_BYTES:
        return False

    if duration > 1:
        expected_size = duration * AUDIO_BYTES_PER_SECOND
        return expected_size * 0.9 <= actual_size <= expected_size * 1.05

    return True


def ffprobe_duration(media_path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    result = subprocess.run(command, text=True, capture_output=True, **subprocess_no_window_kwargs())
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def ffprobe_audio_channels(media_path: Path) -> int:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=channels",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    result = subprocess.run(command, text=True, capture_output=True, **subprocess_no_window_kwargs())
    if result.returncode != 0:
        return 0
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def audio_extract_filter(channels: int) -> str:
    resample = "aresample=16000"
    if channels >= 2:
        return f"pan=mono|c0=0.5*c0+0.5*c1,{resample}"
    return resample


def parse_ffmpeg_out_time(line: str) -> float | None:
    if not line.startswith("out_time_ms="):
        return None
    try:
        return int(line.split("=", 1)[1]) / 1_000_000
    except ValueError:
        return None


def prepare_audio_for_asr(media_path: Path, cache_dir: Path, progress: Progress = print) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    wav_path = cached_audio_path(media_path, cache_dir)
    duration = ffprobe_duration(media_path)
    if is_valid_cached_audio(wav_path, media_path, duration=duration):
        progress(f"[AUDIO] 使用缓存音频: {wav_path}")
        return wav_path
    if wav_path.exists():
        wav_path.unlink()

    if not shutil.which("ffmpeg"):
        raise RuntimeError("未找到 ffmpeg，请先安装 FFmpeg 并确认它在 PATH 中。")

    progress(f"[AUDIO] 提取 16k 单声道 WAV: {media_path.name}")
    channels = ffprobe_audio_channels(media_path)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostats",
        "-nostdin",
        "-y",
        "-i",
        str(media_path),
        "-map",
        "0:a:0",
        "-af",
        audio_extract_filter(channels),
        "-sample_fmt",
        "s16",
        "-progress",
        "pipe:1",
        str(wav_path),
    ]

    process = subprocess.Popen(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **subprocess_no_window_kwargs(),
    )
    last_percent = -1
    output_lines: deque[str] = deque(maxlen=20)
    if process.stdout:
        for line in process.stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
            seconds = parse_ffmpeg_out_time(line)
            if seconds is None or duration <= 0:
                continue
            percent = min(100, int(seconds / duration * 100))
            if percent >= last_percent + 5 or percent == 100:
                progress(f"[AUDIO] {percent}%")
                last_percent = percent

    return_code = process.wait()
    if return_code != 0:
        detail = "\n".join(output_lines)
        if wav_path.exists():
            wav_path.unlink()
        raise RuntimeError(f"FFmpeg 提取音频失败: {media_path}\n{detail}")
    if not is_valid_cached_audio(wav_path, media_path, duration=duration):
        if wav_path.exists():
            wav_path.unlink()
        raise RuntimeError(f"FFmpeg 没有生成有效音频文件: {wav_path}")
    progress(f"[AUDIO] 完成: {wav_path}")
    return wav_path


def process_one(
    model: Any,
    media_path: Path,
    out_dir: Path,
    audio_cache_dir: Path,
    context: str | None,
    language: str,
    max_line_chars: int,
    max_caption_chars: int,
    chunk_seconds: int,
    batch_size: int = 1,
    progress: Progress = print,
    should_stop: Callable[[], bool] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    final_srt = out_dir / f"{media_path.stem}.srt"
    if should_stop and should_stop():
        raise ProcessingCancelled("用户已取消处理。")

    audio_path = prepare_audio_for_asr(media_path, audio_cache_dir, progress=progress)
    if should_stop and should_stop():
        raise ProcessingCancelled("用户已取消处理。")

    progress(f"[ASR local] {media_path}")
    language_name, _transcript, raw_text = transcribe_to_srt_text(
        model=model,
        media_path=str(audio_path),
        context=context or "",
        language=language,
        max_caption_chars=max_caption_chars,
        chunk_seconds=chunk_seconds,
        batch_size=batch_size,
        progress=progress,
        should_stop=should_stop,
    )

    final_text = postprocess_srt_text(
        raw_text,
        max_line_chars=max_line_chars,
        max_caption_chars=max_caption_chars,
    )
    final_srt.write_text(final_text, encoding="utf-8")
    remove_intermediate_outputs(media_path, out_dir)

    suffix = f" ({language_name})" if language_name else ""
    progress(f"[OK] {final_srt}{suffix}")
    return final_srt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-sub",
        description="使用本地 ASR 大模型为音视频生成多语言 SRT 字幕。",
    )
    parser.add_argument("input", nargs="?", help="媒体文件或目录")
    parser.add_argument("-o", "--out-dir", help="输出目录，默认与输入文件同目录")
    parser.add_argument(
        "-j",
        "--batch-size",
        dest="batch_size",
        type=positive_int,
        default=1,
        help="本地推理批大小，默认 1；显存充足可设为 2 或 4",
    )
    parser.add_argument("-c", "--context", help="传给本地 ASR 模型的上下文提示")
    parser.add_argument(
        "-d",
        "--duration",
        "--chunk-seconds",
        dest="chunk_seconds",
        type=positive_int,
        default=DEFAULT_CHUNK_SECONDS,
        help=f"ASR 分块目标秒数，默认 {DEFAULT_CHUNK_SECONDS}；低声或稀疏对白可用 30",
    )
    parser.add_argument("--recursive", action="store_true", help="输入为目录时递归处理")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有输出")
    parser.add_argument("--max-line-chars", type=positive_int, default=22, help="字幕单行最大字符数")
    parser.add_argument("--max-caption-chars", type=positive_int, default=44, help="拆分字幕的最大字符数")
    parser.add_argument(
        "--model-size",
        choices=list(ASR_MODEL_SIZES),
        default=DEFAULT_MODEL_SIZE,
        help=f"ASR 模型尺寸，默认 {DEFAULT_MODEL_SIZE}；0.6B 更快，1.7B 质量更好",
    )
    parser.add_argument("--model", help="自定义 ASR 模型路径或 Hugging Face ID；设置后会覆盖 --model-size")
    parser.add_argument("--aligner", default=DEFAULT_ALIGNER, help=f"强制对齐模型路径或 Hugging Face ID，默认 {DEFAULT_ALIGNER}")
    parser.add_argument(
        "--language",
        choices=["auto", *SUPPORTED_ASR_LANGUAGES],
        default="auto",
        help="识别语言，默认 auto 自动识别；设置后会强制该语言",
    )
    parser.add_argument("--device", default="auto", help="推理设备：auto、cuda:0 或 cpu，默认 auto")
    parser.add_argument("--dtype", choices=["auto", "bfloat16", "float16", "float32"], default="auto", help="模型 dtype，默认 auto")
    parser.add_argument(
        "--max-new-tokens",
        type=positive_int,
        default=DEFAULT_MAX_NEW_TOKENS,
        help=f"每个音频块最大生成 token 数，默认 {DEFAULT_MAX_NEW_TOKENS}",
    )
    parser.add_argument("--local-files-only", action="store_true", help="只使用本地已下载模型，不联网下载权重")
    parser.add_argument("--flash-attn", action="store_true", help="启用 flash_attention_2，需要本机已安装且硬件支持")
    parser.add_argument("--doctor", action="store_true", help="检查 FFmpeg、CUDA、缓存和输出目录是否可用")
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] == "doctor":
        raw_argv = ["--doctor", *raw_argv[1:]]

    parser = build_parser()
    args = parser.parse_args(raw_argv)

    load_dotenv(Path.cwd() / ".env")

    try:
        if args.doctor:
            output_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else None
            results = run_diagnostics(Path.cwd(), output_dir=output_dir)
            print(format_diagnostics(results))
            return 1 if blocking_messages(results) else 0

        if not args.input:
            parser.error("请提供媒体文件/目录，或运行 ai-sub doctor 做环境检查。")

        input_path = Path(args.input).expanduser().resolve()
        files = collect_inputs(input_path, recursive=args.recursive)
        jobs = output_jobs(files, args.out_dir)

        for media_path, out_dir in jobs:
            out_dir.mkdir(parents=True, exist_ok=True)
            ensure_outputs_can_be_written(media_path, out_dir, overwrite=args.overwrite)

        model_path = resolve_asr_model(args.model_size, args.model)
        model_label = "custom" if args.model else f"size={args.model_size}"
        print(f"[LOAD] ASR={model_path} ({model_label})")
        print(f"[LOAD] Aligner={args.aligner}")
        model = load_local_model(
            model_path=model_path,
            aligner_path=args.aligner,
            device=args.device,
            dtype=args.dtype,
            batch_size=args.batch_size,
            max_new_tokens=args.max_new_tokens,
            local_files_only=args.local_files_only,
            flash_attention=args.flash_attn,
        )

        for media_path, out_dir in jobs:
            process_one(
                model=model,
                media_path=media_path,
                out_dir=out_dir,
                audio_cache_dir=Path.cwd() / ".hf_cache" / "audio_tmp",
                context=args.context,
                language=resolve_asr_language(args.language),
                max_line_chars=args.max_line_chars,
                max_caption_chars=args.max_caption_chars,
                chunk_seconds=args.chunk_seconds,
                batch_size=args.batch_size,
            )

    except ProcessingCancelled as exc:
        print(f"已取消: {exc}", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"错误: {friendly_error_message(exc)}", file=sys.stderr)
        return 1

    return 0
