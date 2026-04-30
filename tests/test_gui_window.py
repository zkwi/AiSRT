import os
import re

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QToolButton,
)

from aisrt.diagnostics import CheckResult
from aisrt.gui import (
    AUDIO_ICON_PATH,
    APP_DISPLAY_NAME,
    APP_FONT_POINT_SIZE,
    APP_ICON_PATH,
    APP_PRODUCT_SUBTITLE,
    DEEPSEEK_CHAT_URL,
    FILE_ICON_PATH,
    FONT_FAMILY_CANDIDATES,
    MainWindow,
    PLAY_ICON_PATH,
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
    assert "#RootWidget QLabel," in APP_QSS
    assert "#RootWidget QComboBox," in APP_QSS
    assert "font-size: 14pt;" in APP_QSS
    assert "QLabel {\n    font-size:" not in APP_QSS
    assert "font-size: 20pt;" not in APP_QSS
    assert QT_APP.font().hintingPreference() == QFont.HintingPreference.PreferFullHinting
    assert window.table.horizontalHeader().defaultAlignment() & Qt.AlignmentFlag.AlignLeft
    assert window.table.horizontalHeader().minimumHeight() >= 44
    assert window.table.horizontalHeader().sectionResizeMode(1) == QHeaderView.ResizeMode.Fixed
    assert window.table.columnWidth(1) >= 200
    assert window.table.verticalHeader().defaultSectionSize() >= 64
    assert window.table.minimumHeight() >= 44 + 64 * 5
    assert window.empty_state.minimumHeight() >= 44 + 58 * 4
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
    assert [
        window.ui_language_combo.itemData(index)
        for index in range(window.ui_language_combo.count())
    ] == ["zh-Hans", "zh-Hant", "en"]

    window.language_combo.setCurrentText("英语")
    assert window.language_combo.currentData() == "English"

    window.ui_language_combo.setCurrentText("English")
    assert window.windowTitle() == "AI Subtitle Assistant"
    assert window.title_label.text() == "AI Subtitle Assistant"
    assert "Multilingual recognition" in window.subtitle_label.text()
    assert window.add_files_button.text() == "Add Files"
    assert window.translation_button.text() == "Translate SRT"
    assert window.start_button.text() == "Start"
    assert window.file_queue_title_label.text() == "File Queue"
    assert window.empty_title_label.text() == "No files added"
    assert window.table.horizontalHeaderItem(2).text() == "Subtitle Folder"
    assert window.settings_title_label.text() == "Common Settings"
    assert window.advanced_dialog.windowTitle() == "Advanced Settings"
    assert window.translation_dialog.windowTitle() == "SRT Translation"
    assert window.clear_log_button.text() == "Clear Log"
    assert window.current_label.text() == "Add files to begin"
    assert window.file_count_label.text() == "0 files"
    assert "Optional:" in window.context_edit.placeholderText()
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
    assert window.translation_button.text() == "翻譯字幕"
    assert window.table.horizontalHeaderItem(2).text() == "字幕目錄"
    assert window.table.item(0, 1).text() == ""
    assert queue_status_text(window) == "等待"
    assert window.language_combo.currentData() == "English"

    window.close()


def test_i18n_dictionaries_have_complete_keys():
    languages = [language for language, _label in UI_LANGUAGE_OPTIONS]
    reference = set(TEXT["zh-Hans"])

    assert languages == ["zh-Hans", "zh-Hant", "en"]
    for language in languages:
        assert set(TEXT[language]) == reference


def test_english_ui_has_no_untranslated_visible_copy(tmp_path):
    window = MainWindow()
    media_path = tmp_path / "movie.mp4"
    media_path.write_bytes(b"")
    window.add_paths([media_path])

    window.ui_language_combo.setCurrentText("English")

    assert_no_simplified_or_traditional_chinese(widget_texts(window))
    assert window.language_combo.currentText() == "Auto"
    assert window.profile_combo.currentText() == "Recommended"
    assert window.chunk_seconds_combo.itemText(0) == "Stable (30s)"
    assert window.caption_preset_combo.itemText(1) == "Recommended"
    assert window.progress_detail_text("模型加载失败") == "Model load failed"

    window.append_log("[START] 开始处理")
    window.append_log("[CANCEL] 已请求停止处理")
    window.append_log("[ERROR] 模型加载失败")
    window.append_log("[ERROR] movie.mp4: 显存不足。建议使用“低显存”运行模式，或切换到 0.6B 模型后重试。")

    log_text = window.log_box.toPlainText()
    assert "Processing started." in log_text
    assert "Cancelled: Stop requested" in log_text
    assert "Error: Model load failed" in log_text
    assert "movie.mp4: Not enough VRAM." in log_text
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
    window.append_log("[ASR] 4/52 开始 2.2-3.0 分钟")
    window.append_log("[ASR] 5/52 无时间戳，使用该识别块时间范围生成粗略字幕")
    window.append_log("[ASR] 6/52 无识别文本，跳过字幕生成")

    log_text = window.log_box.toPlainText()
    assert "[INFO] Preparing models. First run may download models; time depends on network and disk speed." in log_text
    assert "[AUDIO] Extracting 16k mono WAV: movie.mp4" in log_text
    assert "[ASR] Audio duration about 4.5 min; split into 7 recognition chunks" in log_text
    assert "[ASR] 3/52 completed in 2.2s; overall progress 5%" in log_text
    assert "[ASR] 4/52 started: 2.2-3.0 min" in log_text
    assert "[ASR] 5/52 has no timestamps; using the chunk time range for rough subtitles" in log_text
    assert "[ASR] 6/52 has no recognized text; skipping subtitle generation" in log_text
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


def test_subtitle_translation_dialog_guides_deepseek_flow():
    window = MainWindow()

    assert DEEPSEEK_CHAT_URL == "https://chat.deepseek.com/"
    assert window.translation_button.text() == "翻译字幕"
    assert window.translation_button.property("variant") == "secondary"
    assert window.translation_dialog.isModal()
    assert window.translation_dialog.minimumWidth() >= 820
    assert window.open_deepseek_button.text() == "打开 DeepSeek 官网"
    assert window.copy_prompt_button.text() == "复制提示词"
    assert window.translation_button.icon().isNull()
    assert window.open_deepseek_button.icon().isNull()
    assert window.copy_prompt_button.icon().isNull()
    assert window.translation_close_button.icon().isNull()
    assert "将生成的 SRT 文件拖入" in window.translation_step_upload_label.text()

    prompt = window.translation_prompt_text()
    assert "目标语言：简体中文" in prompt
    assert "保留 SRT 编号和时间轴" in prompt
    assert "只输出翻译后的 SRT 内容" in prompt
    assert window.translation_prompt_box.toPlainText() == prompt

    window.copy_translation_prompt()
    assert QT_APP.clipboard().text() == prompt
    assert window.copy_prompt_button.text() == "提示词已复制"
    assert window.translation_feedback_label.text() == "提示词已复制"

    window.ui_language_combo.setCurrentText("English")
    assert window.translation_button.text() == "Translate SRT"
    assert window.open_deepseek_button.text() == "Open DeepSeek"
    assert window.copy_prompt_button.text() == "Prompt copied"
    assert "Preserve SRT numbering" in window.translation_prompt_text()
    assert not HAN_RE.search(window.translation_prompt_box.toPlainText())

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
    assert window.clear_log_button.text() == "清空日志"
    assert window.clear_log_button.icon().isNull()
    assert not window.clear_log_button.isEnabled()
    assert not hasattr(window, "log_action_button")

    window.append_log("[START] 开始处理")
    assert window.clear_log_button.isEnabled()
    window.clear_log()
    assert not window.clear_log_button.isEnabled()
    assert window.log_box.toPlainText() == ""

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
        "粤语",
        "西班牙语",
        "法语",
        "德语",
        "葡萄牙语",
        "俄语",
        "意大利语",
        "泰语",
        "越南语",
    ]
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

    assert "完整技术日志" in window.show_technical_log_check.toolTip()
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
