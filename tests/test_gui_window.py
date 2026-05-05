import os
from pathlib import Path
import re

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QToolButton,
    QWidget,
)

from aisrt.diagnostics import CheckResult
from aisrt.gui import (
    AUDIO_ICON_PATH,
    APP_DISPLAY_NAME,
    APP_FONT_POINT_SIZE,
    APP_ICON_PATH,
    APP_PRODUCT_SUBTITLE,
    FILE_ICON_PATH,
    FONT_FAMILY_CANDIDATES,
    LANGUAGE_PRESETS,
    MainWindow,
    PLAY_ICON_PATH,
    TRANSLATION_TARGET_PRESETS,
    VIDEO_ICON_PATH,
    configure_high_dpi_scaling,
    load_add_file_icon,
    load_app_icon,
    load_svg_icon,
    resolve_ui_font_family,
)
from aisrt.gui_i18n import TEXT, UI_LANGUAGE_OPTIONS, format_diagnostics_for_ui
from aisrt.gui_theme import APP_QSS, CHEVRON_DOWN_ICON_PATH


configure_high_dpi_scaling()
QT_APP = QApplication.instance() or QApplication([])
HAN_RE = re.compile(r"[\u4e00-\u9fff]")


def widget_texts(window: MainWindow) -> list[str]:
    texts = [window.windowTitle(), window.advanced_dialog.windowTitle(), window.translation_dialog.windowTitle()]
    for widget_class in (QLabel, QPushButton, QToolButton, QCheckBox):
        for widget in window.findChildren(widget_class):
            texts.append(widget.text())
            texts.append(widget.toolTip())
    for widget in window.findChildren(QLineEdit):
        texts.append(widget.text())
        texts.append(widget.placeholderText())
        texts.append(widget.toolTip())
    for widget in window.findChildren(QPlainTextEdit):
        texts.append(widget.toPlainText())
        texts.append(widget.placeholderText())
        texts.append(widget.toolTip())
    for widget in window.findChildren(QComboBox):
        texts.append(widget.currentText())
        texts.append(widget.toolTip())
        if widget is window.ui_language_combo:
            continue
        texts.extend(widget.itemText(index) for index in range(widget.count()))
    for column in range(window.table.columnCount()):
        item = window.table.horizontalHeaderItem(column)
        if item is not None:
            texts.append(item.text())
    texts.extend(action.text() for action in window.queue_context_menu.actions())
    return [text for text in texts if text]


def assert_no_simplified_or_traditional_chinese(texts: list[str]) -> None:
    leftovers = sorted({text for text in texts if HAN_RE.search(text)})
    assert leftovers == []


def assert_widget_fits_text(widget: QWidget) -> None:
    if widget.isHidden():
        return
    text = widget.text() if hasattr(widget, "text") else ""
    required_width = widget.fontMetrics().horizontalAdvance(text) + 18
    if isinstance(widget, QCheckBox):
        required_width = widget.sizeHint().width()
    elif isinstance(widget, QPushButton) and not widget.icon().isNull():
        required_width += widget.iconSize().width() + 8
    assert widget.width() + 2 >= required_width, (
        widget.objectName(),
        text,
        widget.width(),
        required_width,
    )


def queue_status_text(window: MainWindow, row: int = 0) -> str:
    widget = window.table.cellWidget(row, 1)
    assert widget is not None
    label = widget.findChild(QLabel, "QueueStatusText")
    assert label is not None
    return label.text()


def test_main_window_uses_native_styles_and_system_font():
    window = MainWindow()

    assert window.styleSheet() == APP_QSS
    assert window.centralWidget().objectName() == "RootWidget"
    assert APP_ICON_PATH.exists()
    assert FILE_ICON_PATH.exists()
    assert VIDEO_ICON_PATH.exists()
    assert AUDIO_ICON_PATH.exists()
    assert PLAY_ICON_PATH.exists()
    assert CHEVRON_DOWN_ICON_PATH.exists()
    check_icon_path = CHEVRON_DOWN_ICON_PATH.with_name("check-white.svg")
    assert check_icon_path.exists()
    assert check_icon_path.as_posix() in APP_QSS
    assert not load_app_icon().isNull()
    assert not load_add_file_icon().isNull()
    assert not load_svg_icon(VIDEO_ICON_PATH).isNull()
    assert not load_svg_icon(AUDIO_ICON_PATH).isNull()
    assert not load_svg_icon(PLAY_ICON_PATH).isNull()
    assert not window.windowIcon().isNull()
    assert window.minimumWidth() >= 1180
    assert window.minimumHeight() >= 820
    assert window.logo_label.pixmap() is not None
    assert resolve_ui_font_family() in FONT_FAMILY_CANDIDATES
    assert QT_APP.font().family() == resolve_ui_font_family()
    assert QT_APP.font().pointSize() == APP_FONT_POINT_SIZE == 12
    assert APP_FONT_POINT_SIZE % 2 == 0
    qss_font_sizes = [int(value) for value in re.findall(r"font-size:\s*(\d+)pt", APP_QSS)]
    assert qss_font_sizes
    assert all(value % 2 == 0 for value in qss_font_sizes)
    assert "QLabel#WindowTitle {\n    font-size: 18pt;" in APP_QSS
    assert "QLabel#SectionTitle {\n    font-size: 16pt;" in APP_QSS
    assert "QLabel#HeaderFieldLabel" in APP_QSS
    assert "QComboBox:disabled" in APP_QSS
    assert "#RootWidget QLabel," in APP_QSS
    assert "#RootWidget QComboBox," in APP_QSS
    assert "font-size: 14pt;" in APP_QSS
    assert "QLabel {\n    font-size:" not in APP_QSS
    assert "font-size: 20pt;" not in APP_QSS
    assert QT_APP.font().hintingPreference() == QFont.HintingPreference.PreferFullHinting
    assert window.table.horizontalHeader().defaultAlignment() & Qt.AlignmentFlag.AlignLeft
    assert window.table.horizontalHeader().minimumHeight() >= 44
    assert window.table.horizontalHeader().sectionResizeMode(1) == QHeaderView.ResizeMode.Fixed
    assert window.table.columnWidth(1) >= 300
    assert window.table.verticalHeader().defaultSectionSize() >= 64
    assert window.table.minimumHeight() >= 44 + 64 * 5
    assert window.empty_state.minimumHeight() >= 220
    assert window.table.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert (
        QGuiApplication.highDpiScaleFactorRoundingPolicy()
        == Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    window.close()


def test_window_uses_language_neutral_product_copy():
    window = MainWindow()

    assert window.windowTitle() == APP_DISPLAY_NAME
    assert APP_DISPLAY_NAME == "AI 大模型字幕助手"
    assert window.title_label.text() == APP_DISPLAY_NAME
    assert window.title_label.objectName() == "WindowTitle"
    assert "日语" not in window.title_label.text()
    assert "千问" not in window.title_label.text()
    assert window.subtitle_label.text() == APP_PRODUCT_SUBTITLE
    assert "大模型 ASR" in window.subtitle_label.text()
    assert "多语言" in window.subtitle_label.text()
    assert "精准时间对齐" in window.subtitle_label.text()
    assert "详细错误" not in window.subtitle_label.text()

    window.close()


def test_ui_language_switch_supports_simplified_traditional_and_english(tmp_path):
    window = MainWindow()

    assert window.ui_language_combo.currentData() == "zh-Hans"
    assert window.ui_language_label.text() == "界面语言"
    assert "不影响识别字幕语言或翻译语言" in window.ui_language_combo.toolTip()
    assert [
        window.ui_language_combo.itemData(index)
        for index in range(window.ui_language_combo.count())
    ] == ["zh-Hans", "zh-Hant", "en", "ja", "ko", "es"]

    window.language_combo.setCurrentText("英语")
    assert window.language_combo.currentData() == "English"

    window.ui_language_combo.setCurrentText("English")
    assert window.windowTitle() == "AI Subtitle Assistant"
    assert window.title_label.text() == "AI Subtitle Assistant"
    assert "Multilingual recognition" in window.subtitle_label.text()
    assert window.add_files_button.text() == "Add Files"
    assert window.ui_language_label.text() == "UI language"
    assert "not recognition or translation languages" in window.ui_language_combo.toolTip()
    assert window.translation_button.text() == "Translate SRT"
    assert window.start_button.text() == "Start"
    assert window.file_queue_title_label.text() == "File Queue"
    assert window.empty_title_label.text() == "No files added"
    assert window.table.horizontalHeaderItem(2).text() == "Subtitle Folder"
    assert window.settings_title_label.text() == "Common Settings"
    assert window.recognition_language_label.text() == "Subtitle source language"
    assert window.advanced_dialog.windowTitle() == "Advanced Settings"
    assert window.translation_dialog.windowTitle() == "SRT Translation"
    assert window.show_technical_log_check.text() == "Show detailed log"
    assert "troubleshooting" in window.show_technical_log_check.toolTip()
    assert not hasattr(window, "clear_log_button")
    assert window.current_label.text() == "Add files to begin"
    assert window.file_count_label.text() == "0 files"
    assert not hasattr(window, "context_edit")
    assert not hasattr(window, "context_label")
    assert window.language_combo.currentData() == "English"
    assert window.language_combo.currentText() == "English"

    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    assert window.file_count_label.text() == "1 file"
    assert window.table.item(0, 1).text() == ""
    assert queue_status_text(window) == "Waiting"
    assert window.current_label.text() == "1 file(s) added. Ready to start."
    assert [action.text() for action in window.queue_context_menu.actions() if not action.isSeparator()] == [
        "Open Subtitle Folder",
        "Remove Selected",
        "Clear Completed",
        "Retry Failed",
        "Clear Queue",
    ]

    window.ui_language_combo.setCurrentText("繁體中文")
    assert window.windowTitle() == "AI 大模型字幕助手"
    assert "多語言辨識" in window.subtitle_label.text()
    assert window.add_files_button.text() == "新增檔案"
    assert window.ui_language_label.text() == "介面語言"
    assert window.recognition_language_label.text() == "辨識字幕語言"
    assert window.translation_button.text() == "翻譯既有 SRT"
    assert window.table.horizontalHeaderItem(2).text() == "字幕目錄"
    assert window.table.item(0, 1).text() == ""
    assert queue_status_text(window) == "等待"
    assert window.language_combo.currentData() == "English"

    window.close()


def test_i18n_dictionaries_have_complete_keys():
    languages = [language for language, _label in UI_LANGUAGE_OPTIONS]
    reference = set(TEXT["zh-Hans"])

    assert languages == ["zh-Hans", "zh-Hant", "en", "ja", "ko", "es"]
    for language in languages:
        assert set(TEXT[language]) == reference


def test_additional_ui_language_presets_localize_main_copy():
    window = MainWindow()

    window.ui_language_combo.setCurrentText("日本語")
    assert window.ui_language_label.text() == "表示言語"
    assert window.add_files_button.text() == "ファイルを追加"
    assert window.show_technical_log_check.text() == "詳細ログを表示"
    assert window.translation_button.text() == "既存 SRT を翻訳"
    assert "フランス語" in [window.translation_target_combo.itemText(index) for index in range(window.translation_target_combo.count())]

    window.ui_language_combo.setCurrentText("한국어")
    assert window.ui_language_label.text() == "화면 언어"
    assert window.start_button.text() == "시작"
    assert window.file_queue_title_label.text() == "파일 대기열"
    assert window.show_technical_log_check.text() == "상세 로그 표시"
    assert window.translation_model_mode_combo.itemText(0) == "품질 우선"

    window.ui_language_combo.setCurrentText("Español")
    assert window.ui_language_label.text() == "Idioma de la interfaz"
    assert window.add_files_button.text() == "Añadir"
    assert window.start_button.text() == "Iniciar"
    assert window.translation_dialog.windowTitle() == "Traducción SRT"
    assert "Francés" in [window.translation_target_combo.itemText(index) for index in range(window.translation_target_combo.count())]

    window.close()


def test_ui_language_presets_keep_core_layout_stable():
    window = MainWindow()
    window.resize(window.minimumSize())
    window.show()

    media_path = Path.cwd() / "layout-smoke.mp4"
    for language, _label in UI_LANGUAGE_OPTIONS:
        window.set_combo_data(window.ui_language_combo, language)
        QT_APP.processEvents()

        for widget in [
            window.add_files_button,
            window.translation_button,
            window.advanced_button,
            window.start_button,
            window.stop_button,
            window.show_technical_log_check,
            window.enable_translation_check,
        ]:
            assert_widget_fits_text(widget)

        window.translation_source_edit.setText(str(media_path.with_suffix(".srt")))
        window.refresh_translation_output_preview()
        window.translation_dialog.adjustSize()
        QT_APP.processEvents()

        for widget in [
            window.translation_browse_button,
            window.translation_start_button,
            window.translation_stop_button,
        ]:
            assert_widget_fits_text(widget)

        assert window.translation_dialog.sizeHint().width() <= window.translation_dialog.maximumWidth()
        assert window.translation_dialog.sizeHint().width() <= max(window.translation_dialog.minimumWidth(), 980)

    window.close()


def test_gui_language_presets_use_asr_translation_intersection():
    assert [value for _label_key, value in LANGUAGE_PRESETS] == [
        "",
        "Chinese",
        "English",
        "Japanese",
        "Korean",
        "Spanish",
        "French",
        "German",
        "Portuguese",
        "Russian",
        "Arabic",
    ]
    assert [value for _label_key, value in TRANSLATION_TARGET_PRESETS] == [
        "简体中文",
        "繁體中文",
        "English",
        "Japanese",
        "Korean",
        "Spanish",
        "French",
        "German",
        "Portuguese",
        "Russian",
        "Arabic",
    ]


def test_english_ui_has_no_untranslated_visible_copy(tmp_path):
    window = MainWindow()
    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    window.ui_language_combo.setCurrentText("English")

    assert_no_simplified_or_traditional_chinese(widget_texts(window))
    assert window.language_combo.currentText() == "Auto"
    assert window.profile_combo.currentText() == "Balanced"
    assert window.chunk_seconds_combo.itemText(0) == "Stable (30s)"
    assert window.caption_preset_combo.itemText(1) == "Recommended"
    assert window.progress_detail_text("模型加载失败") == "Model load failed"
    assert window.progress_detail_text("加载翻译模型") == "Loading translation model"
    assert window.progress_detail_text("已处理 2/3") == "Processed 2/3"
    assert window.translation_progress_detail_text("正在加载翻译模型") == "Loading translation model"
    assert window.translation_progress_detail_text("翻译字幕 45%") == "Translating subtitles 45%"
    assert window.progress_detail_text("识别字幕 45% 剩余 01:20") == "Recognizing subtitles 45% (01:20 remaining)"
    assert window.translation_progress_detail_text("翻译字幕 45% 剩余 01:20") == "Translating subtitles 45% (01:20 remaining)"
    assert window.translation_progress_detail_text("翻译完成") == "Translation complete"

    window.append_log("[START] 开始处理")
    window.append_log("[START] 开始识别并翻译")
    window.append_log("[START] 开始翻译字幕")
    window.append_log("[INFO] 正在准备模型；首次运行会下载模型，耗时取决于网络和硬盘。")
    window.append_log("[LOAD] Translate=AngelSlim/Hy-MT1.5-1.8B-1.25bit")
    window.append_log("[ASR] 4/52 完成，用时 2.1s，总进度 8%，剩余 01:20")
    window.append_log("[TRANSLATE] 1/2 完成，总进度 50%，剩余 00:30")
    window.append_log("[TRANSLATE OK] movie.zh.srt")
    window.append_log("[CANCEL] 已请求停止处理")
    window.append_log("[ERROR] 模型加载失败")
    window.append_log("[ERROR] movie.mp4: 显存不足。建议使用“低显存”运行模式，或切换到 0.6B 模型后重试。")
    window.append_log("[ERROR] movie.mp4: 模型下载失败。请检查网络或 Hugging Face 访问是否可用；也可以提前下载模型后勾选“只使用本地模型缓存”。")
    window.append_log("[ERROR] movie.mp4: 翻译失败，已保留原始字幕: mock error")

    log_text = window.log_box.toPlainText()
    assert "Processing started." in log_text
    assert "Recognition and translation started." in log_text
    assert "Translation started." in log_text
    assert "Preparing recognition models. First run may download model files" in log_text
    assert "Loading translation model. First run may download model files." in log_text
    assert "Recognizing subtitles: 8% (01:20 remaining)" in log_text
    assert "Translating subtitles: 50% (00:30 remaining)" in log_text
    assert "Translation complete" in log_text
    assert "Cancelled: Stop requested" in log_text
    assert "Error: Model load failed" in log_text
    assert "movie.mp4: Not enough VRAM." in log_text
    assert "movie.mp4: Model download failed." in log_text
    assert "movie.mp4: Translation failed; original subtitles kept: mock error" in log_text
    assert not HAN_RE.search(log_text)

    window.close()


def test_english_technical_log_localizes_known_worker_messages():
    window = MainWindow()
    window.ui_language_combo.setCurrentText("English")
    window.show_technical_log_check.setChecked(True)

    window.append_log("[INFO] 正在准备模型；首次运行会下载模型，耗时取决于网络和硬盘。")
    window.append_log("[AUDIO] 提取 16k 单声道 WAV: movie.mp4")
    window.append_log("[ASR] 音频时长约 4.5 分钟，分为 7 个识别块")
    window.append_log("[ASR] 3/52 完成，用时 2.2s，总进度 5%")
    window.append_log("[ASR] 4/52 完成，用时 2.1s，总进度 8%，剩余 01:20")
    window.append_log("[ASR] 4/52 开始 2.2-3.0 分钟")
    window.append_log("[ASR] 5/52 无时间戳，使用该识别块时间范围生成粗略字幕")
    window.append_log("[ASR] 6/52 无识别文本，跳过字幕生成")
    window.append_log("[TRANSLATE] 1/2 完成，总进度 50%，剩余 00:30")
    window.append_log("[ERROR] movie.mp4: 翻译失败，已保留原始字幕: mock error")

    log_text = window.log_box.toPlainText()
    assert "[INFO] Preparing models. First run may download models; time depends on network and disk speed." in log_text
    assert "[AUDIO] Extracting 16k mono WAV: movie.mp4" in log_text
    assert "[ASR] Audio duration about 4.5 min; split into 7 recognition chunks" in log_text
    assert "[ASR] 3/52 completed in 2.2s; overall progress 5%" in log_text
    assert "[ASR] 4/52 completed in 2.1s; overall progress 8%; 01:20 remaining" in log_text
    assert "[ASR] 4/52 started: 2.2-3.0 min" in log_text
    assert "[ASR] 5/52 has no timestamps; using the chunk time range for rough subtitles" in log_text
    assert "[ASR] 6/52 has no recognized text; skipping subtitle generation" in log_text
    assert "Translating subtitles: 50% (00:30 remaining)" in log_text
    assert "movie.mp4: Translation failed; original subtitles kept: mock error" in log_text
    assert not HAN_RE.search(log_text)

    window.close()


def test_diagnostics_messages_are_localized_for_ui():
    results = [
        CheckResult("ffmpeg", "error", "没有找到 FFmpeg，请先安装 FFmpeg 并确认 ffmpeg 在 PATH 中。"),
        CheckResult("cuda", "warn", "PyTorch 2.11.0，没有检测到 CUDA；可以运行 CPU 模式，但会很慢。"),
        CheckResult("output", "ok", "输出目录可写: /media"),
        CheckResult("cache", "warn", "模型缓存目录尚不存在，首次运行会创建并下载模型: /.hf_cache"),
    ]

    english = format_diagnostics_for_ui(results, "en")
    traditional = format_diagnostics_for_ui(results, "zh-Hant")

    assert "FFmpeg was not found" in english
    assert "CUDA was not detected" in english
    assert "Subtitle folder is writable" in english
    assert "Model cache folder does not exist yet" in english
    assert not HAN_RE.search(english)
    assert "沒有找到 FFmpeg" in traditional
    assert "沒有偵測到 CUDA" in traditional


def test_subtitle_translation_dialog_uses_local_hymt_flow(tmp_path):
    window = MainWindow()

    assert window.translation_button.text() == "翻译已有 SRT"
    assert window.translation_button.property("variant") == "ghost"
    assert window.translation_dialog.isModal()
    assert window.translation_dialog.minimumWidth() >= 820
    assert window.translation_source_label.text() == "SRT 文件"
    assert window.translation_browse_button.text() == "选择 SRT"
    assert window.translation_output_label.text() == "输出文件"
    assert window.translation_target_label.text() == "翻译语言"
    assert not window.translation_target_combo.isEditable()
    assert window.translation_target_combo.currentData() == "简体中文"
    assert "英语" in [window.translation_target_combo.itemText(index) for index in range(window.translation_target_combo.count())]
    assert window.translation_model_mode_combo.currentData() == "quality"
    assert window.translation_start_button.text() == "开始翻译"
    assert window.translation_stop_button.text() == "停止"
    assert not window.translation_stop_button.isEnabled()
    assert window.translation_button.icon().isNull()
    assert window.translation_browse_button.icon().isNull()
    assert window.translation_start_button.icon().isNull()
    assert window.translation_stop_button.icon().isNull()
    assert window.translation_close_button.icon().isNull()
    assert "不会上传字幕" in window.translation_intro_label.text()
    assert "下载权重" in window.translation_intro_label.text()
    assert "缺失模型不会自动下载" in window.local_only_check.toolTip()
    assert "加载失败" in window.local_only_check.toolTip()
    assert "DeepSeek" not in window.translation_intro_label.text()
    assert not hasattr(window, "translation_prompt_box")
    window.translation_source_edit.setText(str(tmp_path / "movie.srt"))
    window.set_combo_data(window.translation_target_combo, "Spanish")
    assert window.translation_output_edit.text().endswith("movie.es.srt")

    window.ui_language_combo.setCurrentText("English")
    assert window.translation_button.text() == "Translate SRT"
    assert window.translation_browse_button.text() == "Choose SRT"
    assert window.translation_target_label.text() == "Translation language"
    assert window.translation_start_button.text() == "Start Translation"
    assert window.translation_model_mode_combo.itemText(0) == "Quality"
    assert "without uploading subtitles" in window.translation_intro_label.text()
    assert "loading may fail" in window.local_only_check.toolTip()

    window.close()


def test_translation_dialog_handles_targets_and_progress_state(tmp_path):
    window = MainWindow()
    source = tmp_path / "movie.srt"
    source.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello.\n", encoding="utf-8")

    window.translation_source_edit.setText(str(source))
    for target, suffix in [("English", "en"), ("Spanish", "es"), ("Japanese", "ja")]:
        window.set_combo_data(window.translation_target_combo, target)
        window.refresh_translation_output_preview()
        assert window.current_translation_target() == target
        assert window.translation_output_edit.text().endswith(f"movie.{suffix}.srt")

    assert window.translation_progress_bar.isHidden()
    window.set_translation_running(True)
    assert not window.translation_progress_bar.isHidden()
    assert not window.translation_start_button.isEnabled()
    assert window.translation_stop_button.isEnabled()

    window.update_translation_progress(45, "翻译字幕 45%")
    assert window.translation_progress_bar.value() == 45
    assert "45%" in window.translation_feedback_label.text()

    output = tmp_path / "movie.en.srt"
    window.translation_finished(True, str(output))
    assert window.translation_progress_bar.isHidden()
    assert window.translation_start_button.isEnabled()
    assert not window.translation_stop_button.isEnabled()
    assert window.translation_feedback_label.text() == "翻译完成"

    window.close()


def test_main_window_integrates_translation_into_main_flow(tmp_path):
    window = MainWindow()

    assert window.enable_translation_label.text() == "是否启用翻译"
    assert window.enable_translation_check.text() == "启用"
    assert window.recognition_language_label.text() == "识别字幕语言"
    assert not window.enable_translation_check.isChecked()
    assert window.start_button.text() == "开始处理"
    assert window.output_language_label.text() == "翻译语言"
    assert not window.output_language_combo.isEnabled()
    assert not window.output_language_combo.isEditable()
    assert window.output_language_combo.currentData() == "简体中文"
    assert "英语" in [window.output_language_combo.itemText(index) for index in range(window.output_language_combo.count())]
    assert not hasattr(window, "start_translate_button")
    assert not hasattr(window, "context_edit")

    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    asr_options = window.options()
    assert not asr_options.translate_after_asr
    assert asr_options.context == ""

    window.enable_translation_check.setChecked(True)
    assert window.start_button.text() == "识别并翻译"
    assert "识别原始字幕" in window.start_button.toolTip()
    assert window.output_language_combo.isEnabled()
    window.set_combo_data(window.output_language_combo, "Spanish")

    translate_options = window.options()
    assert translate_options.translate_after_asr
    assert translate_options.translation_target_language == "Spanish"

    window.ui_language_combo.setCurrentText("English")
    assert window.output_language_combo.currentText() == "Spanish"
    assert window.options().translation_target_language == "Spanish"
    assert window.enable_translation_label.text() == "Enable translation?"
    assert window.enable_translation_check.text() == "Enable"
    assert window.output_language_label.text() == "Translation language"
    assert window.start_button.text() == "Recognize + Translate"

    window.set_running(True)
    assert window.start_button.isHidden()
    assert not window.enable_translation_check.isEnabled()
    assert not window.output_language_combo.isEnabled()
    assert not window.stop_button.isHidden()

    window.set_running(False)
    assert not window.start_button.isHidden()
    assert window.enable_translation_check.isEnabled()
    assert window.output_language_combo.isEnabled()
    assert window.start_button.text() == "Recognize + Translate"

    window.close()


def test_low_frequency_actions_are_available_from_table_context_menu():
    window = MainWindow()

    assert not hasattr(window, "more_button")
    assert window.table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
    assert [action.text() for action in window.queue_context_menu.actions() if not action.isSeparator()] == [
        "打开输出文件夹",
        "移除选中",
        "清除已完成",
        "重试失败",
        "清空队列",
    ]
    assert all(
        not action.icon().isNull()
        for action in window.queue_context_menu.actions()
        if not action.isSeparator()
    )
    assert not hasattr(window, "queue_action_button")
    assert not hasattr(window, "clear_log_button")
    assert not hasattr(window, "clear_log")
    assert not hasattr(window, "log_action_button")

    window.append_log("[START] 开始处理")
    assert window.log_box.toPlainText() == "开始处理。"

    window.close()


def test_primary_actions_are_simplified_and_contextual():
    window = MainWindow()

    assert window.add_files_button.text() == "添加文件"
    assert window.add_files_button.property("variant") == "accent"
    assert window.add_files_button.property("iconRole") == "add-file"
    assert window.empty_add_files_button.property("iconRole") == "add-file"
    assert not window.add_files_button.icon().isNull()
    assert not window.empty_add_files_button.icon().isNull()
    assert 'QPushButton[variant="accent"]' in APP_QSS
    assert not hasattr(window, "add_folder_button")
    assert window.start_button.parentWidget().objectName() == "HeaderPanel"
    assert window.start_button.text() == "开始处理"
    assert window.start_button.property("variant") == "primary"
    assert not window.start_button.icon().isNull()
    assert window.start_button.icon().cacheKey() == window.play_icon.cacheKey()
    assert window.stop_button.text() == "停止"
    assert window.stop_button.objectName() == "StopButton"
    assert window.stop_button.property("variant") == "danger"
    assert window.stop_button.minimumWidth() >= 92
    assert window.stop_button.icon().isNull()
    assert "QPushButton#StopButton" in APP_QSS
    assert not window.start_button.isHidden()
    assert not window.start_button.isEnabled()
    assert not hasattr(window, "start_translate_button")
    assert window.stop_button.isHidden()
    assert window.progress_panel.isHidden()
    assert window.progress_panel.parent() is None

    window.set_running(True)
    assert window.start_button.isHidden()
    assert not window.stop_button.isHidden()
    assert window.stop_button.isEnabled()
    assert window.progress_panel.isHidden()

    window.set_running(False)
    assert not window.start_button.isHidden()
    assert window.stop_button.isHidden()
    assert window.progress_panel.isHidden()

    window.close()


def test_modal_dialogs_center_on_main_window():
    window = MainWindow()
    window.setGeometry(120, 80, 1000, 700)
    box = QMessageBox(window)
    box.setText("Done")

    window.center_dialog_on_parent(box)

    offset = box.frameGeometry().center() - window.frameGeometry().center()
    assert abs(offset.x()) <= 2
    assert abs(offset.y()) <= 2

    window.close()


def test_output_directory_setting_is_removed_and_uses_media_parent(tmp_path):
    window = MainWindow()
    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")

    window.add_paths([media_path])

    assert not hasattr(window, "out_dir_edit")
    assert window.options().out_dir is None
    assert window.table.horizontalHeaderItem(2).text() == "字幕目录"
    assert window.table.item(0, 2).text() == str(tmp_path)

    window.close()


def test_add_files_dialog_reuses_last_media_directory(tmp_path, monkeypatch):
    window = MainWindow()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first_file = first_dir / "movie.mp4"
    second_file = second_dir / "voice.mp3"
    first_file.write_bytes(b"")
    second_file.write_bytes(b"")

    calls: list[str] = []
    selections = [
        ([str(first_file)], ""),
        ([str(second_file)], ""),
        ([], ""),
    ]

    def fake_get_open_file_names(parent, title, directory, file_filter):
        calls.append(directory)
        return selections.pop(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", fake_get_open_file_names)

    window.add_files()
    assert calls[-1] == str(Path.cwd())
    assert window.last_file_dialog_dir == first_dir.resolve()

    window.add_files()
    assert calls[-1] == str(first_dir.resolve())
    assert window.last_file_dialog_dir == second_dir.resolve()

    window.add_files()
    assert calls[-1] == str(second_dir.resolve())
    assert window.last_file_dialog_dir == second_dir.resolve()

    window.close()


def test_add_files_dialog_falls_back_when_last_directory_is_missing(tmp_path, monkeypatch):
    window = MainWindow()
    missing_dir = tmp_path / "missing"
    window.last_file_dialog_dir = missing_dir
    calls: list[str] = []

    def fake_get_open_file_names(parent, title, directory, file_filter):
        calls.append(directory)
        return [], ""

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", fake_get_open_file_names)

    window.add_files()

    assert calls == [str(Path.cwd())]
    assert window.last_file_dialog_dir == Path.cwd()

    window.close()


def test_queue_uses_distinct_media_type_icons(tmp_path):
    window = MainWindow()
    video_path = tmp_path / "movie.mp4"
    audio_path = tmp_path / "voice.mp3"
    video_path.write_bytes(b"")
    audio_path.write_bytes(b"")

    window.add_paths([video_path, audio_path])

    assert window.table.item(0, 0).icon().cacheKey() == window.video_file_icon.cacheKey()
    assert window.table.item(1, 0).icon().cacheKey() == window.audio_file_icon.cacheKey()

    window.close()


def test_queue_status_column_embeds_processing_progress(tmp_path):
    window = MainWindow()
    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    window.update_file_status(0, "处理中", str(tmp_path))
    window.update_progress(42, "movie.mp4 - 识别字幕 42%")

    status_widget = window.table.cellWidget(0, 1)
    assert status_widget is not None
    status_progress = status_widget.findChild(QProgressBar, "QueueStatusProgress")
    assert status_progress is not None
    assert not status_progress.isHidden()
    assert status_progress.value() == 42
    assert window.table.item(0, 1).text() == ""
    assert window.table.item(0, 1).icon().isNull()
    assert window.table.item(0, 1).toolTip() == "处理中"
    assert queue_status_text(window) == "处理中"
    assert status_widget.minimumWidth() >= 200

    window.update_file_status(0, "完成", str(tmp_path))
    assert status_progress.isHidden()
    assert window.table.item(0, 1).text() == ""
    assert window.table.item(0, 1).icon().isNull()
    assert window.table.item(0, 1).toolTip() == "完成"
    assert queue_status_text(window) == "完成"

    window.close()


def test_empty_queue_guides_user_and_hides_blank_table(tmp_path):
    window = MainWindow()

    assert not window.empty_state.isHidden()
    assert window.table.isHidden()
    assert window.empty_title_label.text() == "还没有添加文件"
    assert "拖入窗口" in window.empty_hint_label.text()

    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    assert window.empty_state.isHidden()
    assert not window.table.isHidden()
    assert window.start_button.isEnabled()
    assert window.open_folder_action.isEnabled()
    assert window.clear_action.isEnabled()
    assert not window.remove_action.isEnabled()

    window.table.selectRow(0)
    window.update_queue_actions()
    assert window.remove_action.isEnabled()
    window.clear_files()
    assert not window.empty_state.isHidden()
    assert window.table.isHidden()
    assert not window.start_button.isEnabled()
    assert window.current_label.text() == "请先添加文件"

    window.close()


def test_model_size_combo_controls_internal_model_path():
    window = MainWindow()

    assert not hasattr(window, "model_edit")
    assert not hasattr(window, "aligner_edit")
    window.model_size_combo.setCurrentText("0.6B")
    assert window.options().model == "Qwen/Qwen3-ASR-0.6B"
    assert window.options().aligner == "Qwen/Qwen3-ForcedAligner-0.6B"

    window.model_size_combo.setCurrentText("1.7B")
    assert window.options().model == "Qwen/Qwen3-ASR-1.7B"

    window.close()


def test_language_combo_controls_asr_language():
    window = MainWindow()

    assert window.language_combo.window() is window
    assert window.language_combo.currentText() == "自动识别"
    assert window.language_combo.maxVisibleItems() == 12
    assert window.language_combo.view().objectName() == "ComboPopup"
    assert window.options().language == ""

    labels = [window.language_combo.itemText(index) for index in range(window.language_combo.count())]
    assert labels == [
        "自动识别",
        "中文",
        "英语",
        "日语",
        "韩语",
        "西班牙语",
        "法语",
        "德语",
        "葡萄牙语",
        "俄语",
        "阿拉伯语",
    ]
    assert "粤语" not in labels
    assert "意大利语" not in labels
    assert "泰语" not in labels
    assert "越南语" not in labels
    assert "马其顿语" not in labels
    assert "波斯语" not in labels

    window.language_combo.setCurrentText("英语")
    assert window.options().language == "English"

    window.close()


def test_technical_settings_open_in_advanced_dialog():
    window = MainWindow()

    assert window.advanced_button.isCheckable() is False
    assert window.advanced_dialog.windowTitle() == "高级设置"
    assert window.advanced_dialog.isModal()
    assert window.advanced_dialog.minimumWidth() >= 760
    assert window.model_size_combo.window() is window
    assert window.chunk_seconds_combo.window() is window.advanced_dialog
    assert window.overwrite_check.window() is window.advanced_dialog
    labels = [label.text() for label in window.advanced_dialog.findChildren(QLabel)]
    assert "ASR 模型" not in labels
    assert "Aligner" not in labels
    assert window.advanced_dialog.findChildren(QLineEdit) == []
    button_box = window.advanced_dialog.findChild(QDialogButtonBox)
    close_button = button_box.button(QDialogButtonBox.StandardButton.Close)
    assert close_button.text() == "关闭"
    assert close_button.property("variant") == "secondary"
    assert close_button.icon().isNull()
    assert window.advanced_button.icon().isNull()

    window.close()


def test_secondary_explanations_use_tooltips():
    window = MainWindow()

    assert window.show_technical_log_check.text() == "显示详细日志"
    assert "关键进度" in window.show_technical_log_check.toolTip()
    assert "完整细节" in window.show_technical_log_check.toolTip()
    assert "技术日志" not in window.show_technical_log_check.text()
    assert "技术日志" not in window.show_technical_log_check.toolTip()
    assert "1.7B" in window.model_size_combo.toolTip()
    assert "0.6B" in window.model_size_combo.toolTip()
    assert "QMenu::item:selected" in APP_QSS
    assert "QMenu::icon" in APP_QSS
    assert "QTableWidget::item:selected" in APP_QSS
    assert "show-decoration-selected: 0;" in APP_QSS
    assert "selection-background-color: transparent;" in APP_QSS
    assert "QComboBox QAbstractItemView" in APP_QSS
    assert "QComboBox::down-arrow" in APP_QSS
    assert CHEVRON_DOWN_ICON_PATH.as_posix() in APP_QSS
    assert "QScrollBar::handle:vertical" in APP_QSS
    assert "QMessageBox" in APP_QSS
    assert "QToolTip" in APP_QSS
    assert "background-color: #FFFFFF;" in APP_QSS

    window.close()


def test_queue_actions_follow_file_statuses(tmp_path):
    window = MainWindow()
    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    assert not window.clear_completed_action.isEnabled()
    assert not window.retry_failed_action.isEnabled()

    window.update_file_status(0, "完成", str(tmp_path))
    assert window.clear_completed_action.isEnabled()
    assert not window.retry_failed_action.isEnabled()

    window.update_file_status(0, "失败，详见日志", str(tmp_path))
    assert window.retry_failed_action.isEnabled()

    window.update_file_status(0, "翻译失败，已保留原字幕", str(tmp_path))
    assert window.retry_failed_action.isEnabled()
    assert window.table.item(0, 1).toolTip() == "翻译失败，已保留原字幕"

    window.set_running(True)
    assert not window.open_folder_action.isEnabled()
    assert not window.clear_action.isEnabled()
    assert not window.retry_failed_action.isEnabled()

    window.set_running(False)
    window.close()


def test_status_icon_styles_cover_processing_warning_and_error():
    window = MainWindow()

    window.set_status_icon("...", "processing")
    assert window.status_icon_label.property("state") == "processing"

    window.set_status_icon("!", "warning")
    assert window.status_icon_label.property("state") == "warning"

    window.set_status_icon("!", "danger")
    assert window.status_icon_label.property("state") == "danger"

    window.set_status_icon("✓")
    assert window.status_icon_label.property("state") == "ready"

    window.close()


def test_gui_uses_presets_instead_of_precise_numeric_tuning():
    window = MainWindow()

    assert window.advanced_dialog.findChildren(QSpinBox) == []
    assert [window.chunk_seconds_combo.itemText(index) for index in range(window.chunk_seconds_combo.count())] == [
        "稳妥（30 秒）",
        "推荐（45 秒）",
        "长分块（60 秒）",
    ]

    window.chunk_seconds_combo.setCurrentText("稳妥（30 秒）")
    assert window.options().chunk_seconds == 30
    window.chunk_seconds_combo.setCurrentText("推荐（45 秒）")
    assert window.options().chunk_seconds == 45

    window.close()


def test_caption_style_preset_controls_line_lengths():
    window = MainWindow()

    window.caption_preset_combo.setCurrentText("短句")
    options = window.options()
    assert options.max_line_chars == 18
    assert options.max_caption_chars == 36

    window.caption_preset_combo.setCurrentText("推荐")
    options = window.options()
    assert options.max_line_chars == 22
    assert options.max_caption_chars == 44

    window.close()
