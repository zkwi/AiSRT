from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from PyQt6.QtCore import QObject, pyqtSignal

from .errors import ProcessingCancelled
from .local_translate import (
    DEFAULT_CONTEXT_SIZE,
    DEFAULT_TRANSLATION_CHUNK_SIZE,
    load_translation_model,
    make_model_translator,
    resolve_translation_model,
    translate_srt_text,
)
from .translate_cli import ensure_output_can_be_written, ensure_srt_input
from .user_messages import friendly_error_message


TRANSLATE_PROGRESS_RE = re.compile(r"总进度\s+(\d+)%")


@dataclass
class TranslationOptions:
    input_path: Path
    output_path: Path
    target_language: str
    model_mode: str = "quality"
    model: str | None = None
    device: str = "auto"
    dtype: str = "auto"
    chunk_size: int = DEFAULT_TRANSLATION_CHUNK_SIZE
    context_size: int = DEFAULT_CONTEXT_SIZE
    max_new_tokens: int = 2048
    local_files_only: bool = False
    overwrite: bool = False


class SrtTranslationWorker(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, options: TranslationOptions) -> None:
        super().__init__()
        self.options = options
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def should_stop(self) -> bool:
        return self._stop_requested

    def run(self) -> None:
        try:
            ensure_srt_input(self.options.input_path)
            ensure_output_can_be_written(self.options.output_path, overwrite=self.options.overwrite)
            self.options.output_path.parent.mkdir(parents=True, exist_ok=True)

            if self.should_stop():
                raise ProcessingCancelled("用户已取消处理。")

            model_id = resolve_translation_model(self.options.model_mode, self.options.model)
            self.log.emit(f"[LOAD] Translate={model_id}")
            self.progress.emit(0, "正在加载翻译模型")
            runtime = load_translation_model(
                model_id=model_id,
                device=self.options.device,
                dtype=self.options.dtype,
                local_files_only=self.options.local_files_only,
            )
            translator = make_model_translator(runtime, max_new_tokens=self.options.max_new_tokens)

            source = self.options.input_path.read_text(encoding="utf-8-sig")

            def report(message: str) -> None:
                self.log.emit(message)
                match = TRANSLATE_PROGRESS_RE.search(message)
                if match:
                    percent = min(100, int(match.group(1)))
                    self.progress.emit(percent, f"翻译字幕 {percent}%")

            translated = translate_srt_text(
                source,
                target_language=self.options.target_language,
                translator=translator,
                chunk_size=self.options.chunk_size,
                context_size=self.options.context_size,
                progress=report,
                should_stop=self.should_stop,
            )
            if self.should_stop():
                raise ProcessingCancelled("用户已取消处理。")

            self.options.output_path.write_text(translated, encoding="utf-8")
            self.log.emit(f"[OK] {self.options.output_path}")
            self.progress.emit(100, "翻译完成")
            self.finished.emit(True, str(self.options.output_path))
        except ProcessingCancelled as exc:
            self.log.emit(f"[CANCEL] {exc}")
            self.finished.emit(False, "已取消")
        except Exception as exc:
            message = friendly_error_message(exc)
            self.log.emit(f"[ERROR] 翻译失败: {message}")
            self.finished.emit(False, message)
