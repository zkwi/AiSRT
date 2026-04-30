from __future__ import annotations

from dataclasses import dataclass
import re


TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2},\d{3})"
)
CJK_CHAR_RE = r"一-龯ぁ-んァ-ン々〆〤ー"


@dataclass
class Caption:
    index: int
    start_ms: int
    end_ms: int
    text: str


def parse_timestamp(value: str) -> int:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return (
        int(hours) * 60 * 60 * 1000
        + int(minutes) * 60 * 1000
        + int(seconds) * 1000
        + int(millis)
    )


def format_timestamp(ms: int) -> str:
    ms = max(0, int(ms))
    millis = ms % 1000
    total_seconds = ms // 1000
    seconds = total_seconds % 60
    total_minutes = total_seconds // 60
    minutes = total_minutes % 60
    hours = total_minutes // 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def parse_srt(text: str) -> list[Caption]:
    captions: list[Caption] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue

        time_line_index = 1 if lines[0].isdigit() and len(lines) > 1 else 0
        match = TIME_RE.search(lines[time_line_index])
        if not match:
            continue

        body = "\n".join(lines[time_line_index + 1 :]).strip()
        if not body:
            continue

        captions.append(
            Caption(
                index=len(captions) + 1,
                start_ms=parse_timestamp(match.group("start")),
                end_ms=parse_timestamp(match.group("end")),
                text=body,
            )
        )

    return captions


def format_srt(captions: list[Caption]) -> str:
    blocks: list[str] = []
    for index, caption in enumerate(captions, start=1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_timestamp(caption.start_ms)} --> {format_timestamp(caption.end_ms)}",
                    caption.text.strip(),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(rf"([{CJK_CHAR_RE}])\s+([{CJK_CHAR_RE}])", r"\1\2", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return text.strip()


def normalize_for_compare(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[。．、，,.!?！？…・「」『』（）()\[\]【】\-ー~〜]", "", text)
    return text


def drop_adjacent_duplicates(captions: list[Caption]) -> list[Caption]:
    result: list[Caption] = []
    previous_key = ""

    for caption in captions:
        key = normalize_for_compare(caption.text)
        if key and key == previous_key:
            continue
        result.append(caption)
        previous_key = key

    return result


def split_by_sentence_punctuation(text: str) -> list[str]:
    parts = re.findall(r"[^。！？!?]+[。！？!?]?", text)
    return [part.strip() for part in parts if part.strip()]


def chunk_text(text: str, size: int) -> list[str]:
    return [text[index : index + size].strip() for index in range(0, len(text), size) if text[index : index + size].strip()]


def split_caption(caption: Caption, max_caption_chars: int) -> list[Caption]:
    text = clean_text(caption.text)
    if len(text) <= max_caption_chars:
        return [Caption(caption.index, caption.start_ms, caption.end_ms, text)]

    parts = split_by_sentence_punctuation(text)
    if len(parts) <= 1 or any(len(part) > max_caption_chars for part in parts):
        parts = chunk_text(text, max_caption_chars)

    if len(parts) <= 1:
        return [Caption(caption.index, caption.start_ms, caption.end_ms, text)]

    duration = max(1, caption.end_ms - caption.start_ms)
    # 太短的片段强行拆分会闪得太快，保留为一条只做换行。
    if duration < len(parts) * 600:
        return [Caption(caption.index, caption.start_ms, caption.end_ms, text)]

    total_chars = sum(max(1, len(part)) for part in parts)
    current = caption.start_ms
    result: list[Caption] = []

    for part in parts[:-1]:
        part_duration = max(600, round(duration * len(part) / total_chars))
        end = min(caption.end_ms, current + part_duration)
        result.append(Caption(caption.index, current, end, part))
        current = end

    result.append(Caption(caption.index, current, caption.end_ms, parts[-1]))
    return result


def split_long_captions(captions: list[Caption], max_caption_chars: int) -> list[Caption]:
    result: list[Caption] = []
    for caption in captions:
        result.extend(split_caption(caption, max_caption_chars))
    return result


def fix_overlaps(captions: list[Caption], min_gap_ms: int = 30) -> list[Caption]:
    result: list[Caption] = []
    previous_end = 0

    for caption in captions:
        start = max(caption.start_ms, previous_end + min_gap_ms if result else caption.start_ms)
        end = max(caption.end_ms, start + 500)
        fixed = Caption(caption.index, start, end, caption.text)
        result.append(fixed)
        previous_end = fixed.end_ms

    return result


def best_wrap_position(text: str, max_line_chars: int) -> int:
    middle = len(text) // 2
    start = max(1, middle - max_line_chars // 2)
    end = min(len(text) - 1, middle + max_line_chars // 2)
    candidates = [index for index in range(start, end + 1) if text[index - 1] in "、，。.!！?？"]
    if candidates:
        return min(candidates, key=lambda index: abs(index - middle))
    return min(max_line_chars, middle)


def wrap_caption_text(text: str, max_line_chars: int) -> str:
    text = clean_text(text)
    if len(text) <= max_line_chars:
        return text

    if len(text) <= max_line_chars * 2:
        pos = best_wrap_position(text, max_line_chars)
        return text[:pos].strip() + "\n" + text[pos:].strip()

    return "\n".join(chunk_text(text, max_line_chars))


def postprocess_captions(
    captions: list[Caption],
    max_line_chars: int = 22,
    max_caption_chars: int = 44,
    min_gap_ms: int = 30,
) -> list[Caption]:
    cleaned = [
        Caption(caption.index, caption.start_ms, caption.end_ms, clean_text(caption.text))
        for caption in captions
        if clean_text(caption.text)
    ]
    deduped = drop_adjacent_duplicates(cleaned)
    split = split_long_captions(deduped, max_caption_chars=max_caption_chars)
    fixed = fix_overlaps(split, min_gap_ms=min_gap_ms)

    return [
        Caption(index, caption.start_ms, caption.end_ms, wrap_caption_text(caption.text, max_line_chars))
        for index, caption in enumerate(fixed, start=1)
    ]


def postprocess_srt_text(
    text: str,
    max_line_chars: int = 22,
    max_caption_chars: int = 44,
    min_gap_ms: int = 30,
) -> str:
    captions = parse_srt(text)
    processed = postprocess_captions(
        captions,
        max_line_chars=max_line_chars,
        max_caption_chars=max_caption_chars,
        min_gap_ms=min_gap_ms,
    )
    return format_srt(processed)
