from __future__ import annotations

from pathlib import Path
import re

from PyQt6.QtCore import QObject, pyqtSignal

from .cli import ensure_outputs_can_be_written, load_dotenv, process_one
from .errors import ProcessingCancelled
from .gui_support import GuiOptions, file_progress_from_log_message
from .local_asr import load_local_model
from .local_translate import (
    load_translation_model,
    make_model_translator,
    resolve_translation_model,
    translate_srt_text,
)
from .translate_cli import default_output_path, ensure_output_can_be_written
from .user_messages import friendly_error_message


TRANSLATE_PROGRESS_RE = re.compile(r"总进度\s+(\d+)%")


class SubtitleWorker(QObject):
    log = pyqtSignal(str)
    file_status = pyqtSignal(int, str, str)
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, files: list[Path], options: GuiOptions) -> None:
        super().__init__()
        self.files = files
        self.options = options
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def should_stop(self) -> bool:
        return self._stop_requested

    def run(self) -> None:
        total = len(self.files)
        self.progress.emit(0, "正在加载模型，首次运行可能需要下载模型")

        try:
            load_dotenv(Path.cwd() / ".env")
            self.log.emit("[INFO] 正在准备模型；首次运行会下载模型，耗时取决于网络和硬盘。")
            self.log.emit(f"[LOAD] ASR={self.options.model}")
            self.log.emit(f"[LOAD] Aligner={self.options.aligner}")
            model = load_local_model(
                model_path=self.options.model,
                aligner_path=self.options.aligner,
                device=self.options.device,
                dtype=self.options.dtype,
                batch_size=self.options.batch_size,
                max_new_tokens=self.options.max_new_tokens,
                local_files_only=self.options.local_files_only,
            )
            translator = None
        except Exception as exc:
            self.log.emit(f"[ERROR] 模型加载失败: {friendly_error_message(exc)}")
            for index, media_path in enumerate(self.files):
                out_dir = self.options.out_dir or media_path.parent
                self.file_status.emit(index, "模型加载失败", str(out_dir))
            self.progress.emit(0, "模型加载失败")
            self.finished.emit()
            return

        for index, media_path in enumerate(self.files):
            if self.should_stop():
                for remaining in range(index, total):
                    out_dir = self.options.out_dir or self.files[remaining].parent
                    self.file_status.emit(remaining, "已取消", str(out_dir))
                self.progress.emit(int(index / total * 100), "已取消后续任务")
                break

            out_dir = self.options.out_dir or media_path.parent
            self.file_status.emit(index, "处理中", str(out_dir))
            self.progress.emit(int(index / total * 100), f"正在处理 {index + 1}/{total}: {media_path.name}")

            def report(message: str) -> None:
                self.log.emit(message)
                parsed = file_progress_from_log_message(message)
                if not parsed:
                    return
                file_percent, detail = parsed
                if self.options.translate_after_asr:
                    file_percent = min(90, file_percent)
                    if detail == "完成":
                        detail = "识别完成"
                overall = int(((index + file_percent / 100) / total) * 100)
                self.progress.emit(overall, f"{media_path.name} - {detail}")

            try:
                ensure_outputs_can_be_written(
                    media_path,
                    out_dir,
                    overwrite=self.options.overwrite,
                    translation_target_language=(
                        self.options.translation_target_language if self.options.translate_after_asr else None
                    ),
                )
                final_srt = process_one(
                    model=model,
                    media_path=media_path,
                    out_dir=out_dir,
                    audio_cache_dir=Path.cwd() / ".hf_cache" / "audio_tmp",
                    context=self.options.context,
                    language=self.options.language,
                    max_line_chars=self.options.max_line_chars,
                    max_caption_chars=self.options.max_caption_chars,
                    chunk_seconds=self.options.chunk_seconds,
                    batch_size=self.options.batch_size,
                    progress=report,
                    should_stop=self.should_stop,
                )
                translation_failed = False
                if self.options.translate_after_asr:
                    translated_srt = default_output_path(final_srt, self.options.translation_target_language)
                    try:
                        ensure_output_can_be_written(translated_srt, overwrite=self.options.overwrite)
                        if translator is None:
                            translation_model = resolve_translation_model(self.options.translation_model_mode)
                            self.log.emit(f"[LOAD] Translate={translation_model}")
                            self.progress.emit(
                                int(((index + 0.9) / total) * 100),
                                f"{media_path.name} - 加载翻译模型",
                            )
                            translation_runtime = load_translation_model(
                                model_id=translation_model,
                                device=self.options.device,
                                dtype=self.options.dtype,
                                local_files_only=self.options.local_files_only,
                            )
                            translator = make_model_translator(
                                translation_runtime,
                                max_new_tokens=self.options.translation_max_new_tokens,
                            )
                        self.progress.emit(
                            int(((index + 0.9) / total) * 100),
                            f"{media_path.name} - 翻译字幕",
                        )

                        def translate_report(message: str) -> None:
                            self.log.emit(message)
                            match = TRANSLATE_PROGRESS_RE.search(message)
                            if not match:
                                return
                            translate_percent = min(100, int(match.group(1)))
                            file_percent = 90 + round(translate_percent * 0.1)
                            overall = int(((index + file_percent / 100) / total) * 100)
                            self.progress.emit(overall, f"{media_path.name} - 翻译字幕 {translate_percent}%")

                        translated = translate_srt_text(
                            final_srt.read_text(encoding="utf-8-sig"),
                            target_language=self.options.translation_target_language,
                            translator=translator,
                            chunk_size=50,
                            context_size=5,
                            progress=translate_report,
                            should_stop=self.should_stop,
                        )
                        if self.should_stop():
                            raise ProcessingCancelled("用户已取消处理。")
                        translated_srt.write_text(translated, encoding="utf-8")
                        self.log.emit(f"[OK] {translated_srt}")
                    except ProcessingCancelled:
                        raise
                    except Exception as exc:
                        translation_failed = True
                        self.log.emit(
                            f"[ERROR] {media_path.name}: 翻译失败，已保留原始字幕: {friendly_error_message(exc)}"
                        )
                        self.file_status.emit(index, "翻译失败，已保留原字幕", str(final_srt.parent))
                if not translation_failed:
                    self.file_status.emit(index, "完成", str(final_srt.parent))
            except ProcessingCancelled as exc:
                self.log.emit(f"[CANCEL] {exc}")
                self.file_status.emit(index, "已取消", str(out_dir))
                for remaining in range(index + 1, total):
                    remaining_out_dir = self.options.out_dir or self.files[remaining].parent
                    self.file_status.emit(remaining, "已取消", str(remaining_out_dir))
                self.progress.emit(int(index / total * 100), "已取消处理")
                break
            except Exception as exc:
                self.log.emit(f"[ERROR] {media_path.name}: {friendly_error_message(exc)}")
                self.file_status.emit(index, "失败，详见日志", str(out_dir))

            done = int(((index + 1) / total) * 100)
            self.progress.emit(done, f"已完成 {index + 1}/{total}")

        self.finished.emit()
