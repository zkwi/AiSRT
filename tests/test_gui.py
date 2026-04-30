from aisrt.gui_support import (
    collect_media_paths,
    file_progress_from_log_message,
)


def test_file_progress_from_audio_log():
    assert file_progress_from_log_message("[AUDIO] 50%") == (5, "提取音频 50%")
    assert file_progress_from_log_message("[AUDIO] 完成: movie.wav") == (10, "音频准备完成")


def test_file_progress_from_asr_log():
    assert file_progress_from_log_message("[ASR] 10/20 完成，用时 1.0s，总进度 50%") == (
        55,
        "识别字幕 50%",
    )


def test_file_progress_from_ok_log():
    assert file_progress_from_log_message("[OK] movie.srt (Japanese)") == (100, "完成")


def test_collect_media_paths_accepts_files_and_directories(tmp_path):
    movie = tmp_path / "movie.mp4"
    movie.write_bytes(b"movie")
    nested = tmp_path / "nested"
    nested.mkdir()
    second = nested / "second.mkv"
    second.write_bytes(b"movie")
    ignored = tmp_path / "note.txt"
    ignored.write_text("ignore", encoding="utf-8")

    assert collect_media_paths([tmp_path]) == [movie, second]
