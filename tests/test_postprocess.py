from aisrt.postprocess import parse_srt, postprocess_srt_text


def test_parse_srt_ignores_bad_blocks():
    text = """1
00:00:01,000 --> 00:00:02,000
こんにちは

bad block

2
00:00:02,500 --> 00:00:03,000
またね
"""

    captions = parse_srt(text)

    assert len(captions) == 2
    assert captions[0].text == "こんにちは"
    assert captions[1].start_ms == 2500


def test_postprocess_drops_adjacent_duplicates_and_fixes_overlap():
    text = """1
00:00:01,000 --> 00:00:03,000
こ ん に ち は

2
00:00:02,500 --> 00:00:04,000
こんにちは

3
00:00:02,900 --> 00:00:05,000
今日はいい天気ですね
"""

    result = postprocess_srt_text(text)

    assert result.count("\n\n") == 1
    assert "00:00:03,030 -->" in result
    assert "こんにちは" in result


def test_postprocess_splits_long_caption_by_sentence_punctuation():
    text = """1
00:00:00,000 --> 00:00:06,000
これはとても長い字幕です。映画の会話としては少し長すぎます。だから分割します。
"""

    result = postprocess_srt_text(text, max_line_chars=40, max_caption_chars=24)

    assert "1\n00:00:00,000 -->" in result
    assert "\n\n2\n" in result
    assert "これはとても長い字幕です。" in result


def test_postprocess_wraps_long_line():
    text = """1
00:00:00,000 --> 00:00:03,000
今日は映画を見に行きますか
"""

    result = postprocess_srt_text(text, max_line_chars=8, max_caption_chars=44)

    assert "今日は映画を\n見に行きますか" in result
