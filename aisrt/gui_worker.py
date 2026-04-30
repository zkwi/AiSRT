from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from .cli import ensure_outputs_can_be_written, load_dotenv, process_one
from .errors import ProcessingCancelled
from .gui_support import GuiOptions, file_progress_from_log_message
from .local_asr import load_local_model
from .user_messages import friendly_error_message


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
                overall = int(((index + file_percent / 100) / total) * 100)
                self.progress.emit(overall, f"{media_path.name} - {detail}")

            try:
                ensure_outputs_can_be_written(media_path, out_dir, overwrite=self.options.overwrite)
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
