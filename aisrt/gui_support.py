from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cli import MEDIA_EXTENSIONS, output_target_paths


AUDIO_PROGRESS_RE = re.compile(r"^\[AUDIO\]\s+(\d+)%")
ASR_PROGRESS_RE = re.compile(r"总进度\s+(\d+)%")
REMAINING_TIME_RE = re.compile(r"剩余\s+(\d+:\d{2})")


@dataclass
class GuiOptions:
    out_dir: Path | None
    context: str
    language: str
    model: str
    aligner: str
    device: str
    dtype: str
    batch_size: int
    max_new_tokens: int
    max_line_chars: int
    max_caption_chars: int
    chunk_seconds: int
    overwrite: bool
    local_files_only: bool
    translate_after_asr: bool = False
    translation_target_language: str = "简体中文"
    translation_model_mode: str = "quality"
    translation_max_new_tokens: int = 2048


def collect_media_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()

    for path in paths:
        path = path.expanduser().resolve()
        candidates = [path]
        if path.is_dir():
            candidates = sorted(item for item in path.rglob("*") if item.is_file())

        for candidate in candidates:
            candidate = candidate.resolve()
            if candidate.suffix.lower() not in MEDIA_EXTENSIONS or not candidate.is_file():
                continue
            if candidate in seen:
                continue
            result.append(candidate)
            seen.add(candidate)

    return result


def output_conflicts(
    files: list[Path],
    out_dir: Path | None,
    translation_target_language: str | None = None,
) -> list[Path]:
    conflicts: list[Path] = []
    for media_path in files:
        target_dir = out_dir or media_path.parent
        for target in output_target_paths(media_path, target_dir, translation_target_language=translation_target_language):
            if target.exists():
                conflicts.append(target)
    return conflicts


def file_progress_from_log_message(message: str) -> tuple[int, str] | None:
    if "[AUDIO] 使用缓存音频" in message:
        return 10, "使用缓存音频"
    if "[AUDIO] 完成" in message:
        return 10, "音频准备完成"
    if "[ASR local]" in message:
        return 10, "准备识别"
    if "[OK]" in message:
        return 100, "完成"

    audio_match = AUDIO_PROGRESS_RE.search(message)
    if audio_match:
        percent = min(100, int(audio_match.group(1)))
        return min(10, round(percent * 0.1)), f"提取音频 {percent}%"

    asr_match = ASR_PROGRESS_RE.search(message)
    if asr_match:
        percent = min(100, int(asr_match.group(1)))
        remaining_match = REMAINING_TIME_RE.search(message)
        detail = f"识别字幕 {percent}%"
        if remaining_match:
            detail += f" 剩余 {remaining_match.group(1)}"
        return 10 + round(percent * 0.9), detail

    return None
