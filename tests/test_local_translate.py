from __future__ import annotations

import pytest

from aisrt.local_translate import (
    build_translation_prompt,
    chunk_captions,
    parse_tagged_translations,
    translate_srt_text,
)
from aisrt.postprocess import Caption, format_timestamp, parse_srt


def test_chunk_captions_keeps_order_and_uses_caption_count() -> None:
    captions = [
        Caption(index=1, start_ms=0, end_ms=1000, text="one"),
        Caption(index=2, start_ms=1000, end_ms=2000, text="two"),
        Caption(index=3, start_ms=2000, end_ms=3000, text="three"),
    ]

    chunks = chunk_captions(captions, chunk_size=2)

    assert [[caption.index for caption in chunk] for chunk in chunks] == [[1, 2], [3]]


def test_build_translation_prompt_uses_stable_numbered_lines() -> None:
    prompt = build_translation_prompt(
        [
            Caption(index=1, start_ms=0, end_ms=1000, text="Hello."),
            Caption(index=2, start_ms=1000, end_ms=2000, text="How are you?"),
        ],
        target_language="简体中文",
    )

    assert "简体中文" in prompt
    assert "不要照抄原文" in prompt
    assert "编号<TAB>文本" in prompt
    assert "1\tHello." in prompt
    assert "2\tHow are you?" in prompt
    assert "时间轴" in prompt
    assert "<target>...</target>" not in prompt


def test_build_translation_prompt_uses_english_instruction_for_non_chinese_target() -> None:
    prompt = build_translation_prompt(
        [Caption(index=1, start_ms=0, end_ms=1000, text="你好，世界。")],
        target_language="English",
    )

    assert "Translate each numbered subtitle into English" in prompt
    assert "Do not copy the source" in prompt
    assert "1\t你好，世界。" in prompt


def test_parse_tagged_translations_requires_all_expected_ids() -> None:
    result = parse_tagged_translations(
        "1\t你好。\n2\t你好吗？",
        expected_ids=[1, 2],
    )

    assert result == {1: "你好。", 2: "你好吗？"}

    xml_result = parse_tagged_translations(
        '<target><sn id="1">你好。</sns><sn id="2">你好吗？</sn></target>',
        expected_ids=[1, 2],
    )
    assert xml_result == {1: "你好。", 2: "你好吗？"}

    with pytest.raises(ValueError, match="缺少字幕"):
        parse_tagged_translations("1\t你好。", expected_ids=[1, 2])


def test_parse_tagged_translations_tolerates_common_model_noise() -> None:
    result = parse_tagged_translations(
        """
下面是翻译结果：
```text
1: 你好，世界。
2：这个字幕保留时间轴。
3\t专有名词 AISRT 保留。
```
""",
        expected_ids=[1, 2, 3],
    )

    assert result == {
        1: "你好，世界。",
        2: "这个字幕保留时间轴。",
        3: "专有名词 AISRT 保留。",
    }


def test_parse_tagged_translations_accepts_space_after_id_for_single_item() -> None:
    result = parse_tagged_translations("3 AISRT 在本地运行。", expected_ids=[3])

    assert result == {3: "AISRT 在本地运行。"}


def test_parse_tagged_translations_uses_plain_output_for_single_item() -> None:
    result = parse_tagged_translations("AISRT 在本地运行。", expected_ids=[3])

    assert result == {3: "AISRT 在本地运行。"}


def test_translate_srt_text_preserves_numbering_and_timestamps() -> None:
    source = """1
00:00:00,000 --> 00:00:01,000
Hello.

2
00:00:01,100 --> 00:00:02,200
How are you?
"""

    prompts: list[str] = []

    def translator(prompt: str) -> str:
        prompts.append(prompt)
        return "1\t你好。\n2\t你好吗？"

    translated = translate_srt_text(
        source,
        target_language="简体中文",
        translator=translator,
        chunk_size=50,
    )

    captions = parse_srt(translated)
    assert [caption.index for caption in captions] == [1, 2]
    assert [(caption.start_ms, caption.end_ms) for caption in captions] == [(0, 1000), (1100, 2200)]
    assert [caption.text for caption in captions] == ["你好。", "你好吗？"]
    assert len(prompts) == 1


def test_translate_srt_text_handles_multiline_captions_and_chunk_context() -> None:
    source = """1
00:00:00,000 --> 00:00:01,000
Hello,
world.

2
00:00:01,100 --> 00:00:02,200
AISRT keeps subtitles local.

3
00:00:02,500 --> 00:00:03,500
Translate into Spanish.
"""
    prompts: list[str] = []

    def translator(prompt: str) -> str:
        prompts.append(prompt)
        if "3\tTranslate into Spanish." in prompt:
            assert "Source: Hello, world. / Translation: Hola, mundo." in prompt
            return "3\tTraducir al español."
        return "1\tHola, mundo.\n2\tAISRT mantiene los subtítulos locales."

    translated = translate_srt_text(
        source,
        target_language="Spanish",
        translator=translator,
        chunk_size=2,
    )

    captions = parse_srt(translated)
    assert [caption.text for caption in captions] == [
        "Hola, mundo.",
        "AISRT mantiene los subtítulos locales.",
        "Traducir al español.",
    ]
    assert [(caption.start_ms, caption.end_ms) for caption in captions] == [
        (0, 1000),
        (1100, 2200),
        (2500, 3500),
    ]
    assert len(prompts) == 2


def test_translate_srt_text_handles_long_srt_in_multiple_chunks() -> None:
    blocks: list[str] = []
    for index in range(1, 102):
        start_ms = (index - 1) * 1100
        end_ms = start_ms + 900
        blocks.append(
            f"{index}\n"
            f"{format_timestamp(start_ms)} --> {format_timestamp(end_ms)}\n"
            f"Line {index}.\n"
        )
    source = "\n".join(blocks)
    prompts: list[str] = []

    def translator(prompt: str) -> str:
        prompts.append(prompt)
        lines: list[str] = []
        for line in prompt.splitlines():
            if "\tLine " not in line:
                continue
            caption_id, _text = line.split("\t", 1)
            if caption_id.isdigit():
                lines.append(f"{caption_id}\t译文 {caption_id}")
        return "\n".join(lines)

    translated = translate_srt_text(
        source,
        target_language="简体中文",
        translator=translator,
        chunk_size=50,
        context_size=5,
    )

    captions = parse_srt(translated)
    assert len(captions) == 101
    assert captions[0].text == "译文 1"
    assert captions[49].text == "译文 50"
    assert captions[50].text == "译文 51"
    assert captions[-1].text == "译文 101"
    assert captions[-1].start_ms == 110000
    assert len(prompts) == 3
    assert "源文：Line 50. / 译文：译文 50" in prompts[1]
    assert "源文：Line 100. / 译文：译文 100" in prompts[2]


def test_translate_srt_text_splits_chunk_when_model_omits_an_id() -> None:
    source = """1
00:00:00,000 --> 00:00:01,000
Hello.

2
00:00:01,100 --> 00:00:02,200
How are you?
"""
    calls: list[str] = []

    def translator(prompt: str) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            return "1\t你好。"
        if "1\tHello." in prompt:
            return "1\t你好。"
        return "2\t你好吗？"

    translated = translate_srt_text(
        source,
        target_language="简体中文",
        translator=translator,
        chunk_size=2,
    )

    assert [caption.text for caption in parse_srt(translated)] == ["你好。", "你好吗？"]
    assert len(calls) == 3


def test_translate_srt_text_returns_empty_for_empty_or_invalid_srt() -> None:
    assert translate_srt_text("", translator=lambda _prompt: "") == ""
    assert translate_srt_text("not an srt", translator=lambda _prompt: "") == ""


def test_translate_cli_writes_translated_srt(tmp_path) -> None:
    from aisrt.translate_cli import main

    source = tmp_path / "sample.srt"
    source.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello.\n",
        encoding="utf-8",
    )
    output = tmp_path / "sample.zh.srt"

    def translator(_prompt: str) -> str:
        return "1\t你好。"

    exit_code = main(
        [
            str(source),
            "--output",
            str(output),
            "--to",
            "简体中文",
            "--chunk-size",
            "1",
        ],
        translator=translator,
    )

    assert exit_code == 0
    assert "你好。" in output.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,000" in output.read_text(encoding="utf-8")


def test_translate_cli_requires_existing_srt(tmp_path) -> None:
    from aisrt.translate_cli import main

    exit_code = main([str(tmp_path / "missing.srt")], translator=lambda _prompt: "")

    assert exit_code == 1


def test_translate_cli_refuses_output_conflict_without_overwrite(tmp_path) -> None:
    from aisrt.translate_cli import main

    source = tmp_path / "sample.srt"
    source.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello.\n",
        encoding="utf-8",
    )
    output = tmp_path / "sample.zh.srt"
    output.write_text("old", encoding="utf-8")

    exit_code = main(
        [str(source), "--output", str(output), "--to", "简体中文"],
        translator=lambda _prompt: "1\t你好。",
    )

    assert exit_code == 1
    assert output.read_text(encoding="utf-8") == "old"


def test_translate_cli_default_output_uses_target_language_suffix(tmp_path) -> None:
    from aisrt.translate_cli import default_output_path

    source = tmp_path / "sample.srt"

    assert default_output_path(source, "简体中文").name == "sample.zh.srt"
    assert default_output_path(source, "繁體中文").name == "sample.zh-Hant.srt"
    assert default_output_path(source, "English").name == "sample.en.srt"
    assert default_output_path(source, "Spanish").name == "sample.es.srt"
    assert default_output_path(source, "Klingon").name == "sample.klingon.srt"
