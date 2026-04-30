from __future__ import annotations

from pathlib import Path
import sys

from PyQt6.QtCore import QSize, Qt, QThread, QTimer, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from .cli import MEDIA_EXTENSIONS
from .diagnostics import blocking_messages, run_diagnostics
from .gui_assets import (
    APP_DISPLAY_NAME,
    APP_FONT_POINT_SIZE,
    APP_ICON_PATH,
    APP_PRODUCT_SUBTITLE,
    AUDIO_EXTENSIONS,
    AUDIO_ICON_PATH,
    DEEPSEEK_CHAT_URL,
    FILE_ICON_PATH,
    FONT_FAMILY_CANDIDATES,
    PLAY_ICON_PATH,
    VIDEO_EXTENSIONS,
    VIDEO_ICON_PATH,
    apply_application_font,
    configure_high_dpi_scaling,
    load_add_file_icon,
    load_app_icon,
    load_svg_icon,
    resolve_ui_font_family,
)
from .gui_i18n import (
    DEFAULT_UI_LANGUAGE,
    UI_LANGUAGE_OPTIONS,
    format_diagnostics_for_ui,
    technical_log_text,
    tr,
    user_log_text,
)
from .gui_support import (
    GuiOptions,
    collect_media_paths,
    output_conflicts,
)
from .gui_theme import APP_QSS
from .gui_widgets import QueueStatusWidget
from .gui_worker import SubtitleWorker
from .local_asr import (
    ASR_MODEL_SIZES,
    DEFAULT_ALIGNER,
    DEFAULT_CHUNK_SECONDS,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL_SIZE,
    resolve_asr_model,
)


LANGUAGE_PRESETS = [
    ("asr_auto", DEFAULT_LANGUAGE),
    ("asr_chinese", "Chinese"),
    ("asr_english", "English"),
    ("asr_japanese", "Japanese"),
    ("asr_korean", "Korean"),
    ("asr_cantonese", "Cantonese"),
    ("asr_spanish", "Spanish"),
    ("asr_french", "French"),
    ("asr_german", "German"),
    ("asr_portuguese", "Portuguese"),
    ("asr_russian", "Russian"),
    ("asr_italian", "Italian"),
    ("asr_thai", "Thai"),
    ("asr_vietnamese", "Vietnamese"),
]
PROFILE_PRESETS = [
    ("profile_recommended", "recommended"),
    ("profile_low_vram", "low_vram"),
    ("profile_cpu_slow", "cpu_slow"),
]
DEVICE_PRESETS = [
    ("device_auto", "auto"),
    ("device_gpu", "cuda:0"),
    ("device_cpu", "cpu"),
]
CHUNK_PRESETS = [
    ("chunk_safe", 30),
    ("chunk_recommended", DEFAULT_CHUNK_SECONDS),
    ("chunk_long", 60),
]
CAPTION_PRESETS = [
    ("caption_short", (18, 36)),
    ("caption_recommended", (22, 44)),
    ("caption_long", (28, 56)),
]
STATUS_ROLE = Qt.ItemDataRole.UserRole


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        apply_application_font()
        self.files: list[Path] = []
        self.thread: QThread | None = None
        self.worker: SubtitleWorker | None = None
        self.ui_running = False
        self.full_log: list[str] = []
        self.ui_language = DEFAULT_UI_LANGUAGE
        self.status_phase_key = "status_ready"
        self.status_current_key = "status_add_files"
        self.status_current_values: dict[str, object] = {}
        self.last_progress_detail = ""
        self.current_processing_row: int | None = None
        self.translation_prompt_copied = False

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.app_icon = load_app_icon()
        self.add_file_icon = load_add_file_icon()
        self.video_file_icon = load_svg_icon(VIDEO_ICON_PATH)
        self.audio_file_icon = load_svg_icon(AUDIO_ICON_PATH)
        self.play_icon = load_svg_icon(PLAY_ICON_PATH)
        if not self.app_icon.isNull():
            self.setWindowIcon(self.app_icon)
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(self.app_icon)
        self.resize(1180, 820)
        self.setMinimumSize(960, 680)
        self.setAcceptDrops(True)
        self.setCentralWidget(self.build_ui())
        self.apply_style()
        self.apply_language()
        self.update_file_count()

    def build_ui(self) -> QWidget:
        root = QWidget()
        root.setObjectName("RootWidget")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        layout.addWidget(self.build_header())
        layout.addWidget(self.build_file_panel(), 5)
        layout.addWidget(self.build_settings_panel())
        self.progress_panel = self.build_progress_panel()
        # 进度显示已经合并到文件队列状态列，独立状态面板只保留给内部状态更新。
        self.progress_panel.hide()
        layout.addWidget(self.build_log_panel(), 1)

        self.add_files_button.clicked.connect(self.add_files)
        self.empty_add_files_button.clicked.connect(self.add_files)
        self.clear_action.triggered.connect(self.clear_files)
        self.remove_action.triggered.connect(self.remove_selected_files)
        self.clear_completed_action.triggered.connect(self.clear_completed_files)
        self.retry_failed_action.triggered.connect(self.retry_failed_files)
        self.open_folder_action.triggered.connect(self.open_output_folder)
        self.start_button.clicked.connect(self.start_processing)
        self.stop_button.clicked.connect(self.request_stop)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.itemSelectionChanged.connect(self.update_queue_actions)
        self.ui_language_combo.currentIndexChanged.connect(self.change_ui_language)
        self.translation_button.clicked.connect(self.show_translation_dialog)
        self.open_deepseek_button.clicked.connect(self.open_deepseek_chat)
        self.copy_prompt_button.clicked.connect(self.copy_translation_prompt)
        self.advanced_button.clicked.connect(self.show_advanced_settings)
        self.profile_combo.currentIndexChanged.connect(lambda _index: self.apply_profile())
        self.show_technical_log_check.toggled.connect(self.refresh_log_view)
        self.clear_log_button.clicked.connect(self.clear_log)
        self.table.itemDoubleClicked.connect(lambda _item: self.open_output_folder())

        return root

    def t(self, key: str, **values: object) -> str:
        return tr(self.ui_language, key, **values)

    def set_labeled_combo(
        self,
        combo: QComboBox,
        options: list[tuple[str, object]],
        default_data: object | None = None,
    ) -> None:
        current_data = combo.currentData()
        if current_data is None:
            current_data = default_data
        combo.blockSignals(True)
        combo.clear()
        for text_key, data in options:
            combo.addItem(self.t(text_key), data)
        if current_data is not None:
            self.set_combo_data(combo, current_data)
        combo.blockSignals(False)

    def set_status_text(self, phase_key: str, current_key: str, **values: object) -> None:
        self.status_phase_key = phase_key
        self.status_current_key = current_key
        self.status_current_values = values
        self.phase_label.setText(self.t(phase_key))
        self.current_label.setText(self.t(current_key, **values))

    def change_ui_language(self, _index: int | None = None) -> None:
        language = self.ui_language_combo.currentData()
        if not isinstance(language, str) or language == self.ui_language:
            return
        self.ui_language = language
        self.apply_language()

    def center_dialog_on_parent(self, dialog: QWidget) -> None:
        dialog.adjustSize()
        parent_rect = self.frameGeometry()
        if not parent_rect.isValid() or parent_rect.width() <= 0 or parent_rect.height() <= 0:
            screen = QGuiApplication.screenAt(self.geometry().center()) or QGuiApplication.primaryScreen()
            if screen is not None:
                parent_rect = screen.availableGeometry()
            else:
                parent_rect = self.geometry()

        dialog_rect = dialog.frameGeometry()
        hint = dialog.sizeHint()
        if dialog_rect.width() <= 0 or dialog_rect.height() <= 0:
            dialog_rect.setSize(hint)
        dialog_rect.moveCenter(parent_rect.center())
        dialog.move(dialog_rect.topLeft())

    def exec_centered_dialog(self, dialog: QDialog) -> int:
        self.center_dialog_on_parent(dialog)
        # QMessageBox lays out native decorations after show; center once more in the event loop.
        QTimer.singleShot(0, lambda: self.center_dialog_on_parent(dialog))
        return dialog.exec()

    def show_message(self, icon: QMessageBox.Icon, title: str, message: str) -> None:
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(message)
        ok_button = box.addButton(self.t("dialog_ok"), QMessageBox.ButtonRole.AcceptRole)
        box.setDefaultButton(ok_button)
        self.exec_centered_dialog(box)

    def ask_overwrite_outputs(self, preview: str) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(self.t("msg_output_exists"))
        box.setText(self.t("msg_output_exists_body", preview=preview))
        overwrite_button = box.addButton(
            self.t("dialog_overwrite"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        cancel_button = box.addButton(self.t("dialog_cancel"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel_button)
        self.exec_centered_dialog(box)
        return box.clickedButton() is overwrite_button

    def translation_prompt_text(self) -> str:
        return self.t("translation_prompt")

    def show_translation_dialog(self) -> None:
        self.translation_prompt_copied = False
        self.translation_feedback_label.clear()
        self.copy_prompt_button.setText(self.t("copy_prompt"))
        self.exec_centered_dialog(self.translation_dialog)

    def open_deepseek_chat(self) -> None:
        QDesktopServices.openUrl(QUrl(DEEPSEEK_CHAT_URL))

    def copy_translation_prompt(self) -> None:
        QApplication.clipboard().setText(self.translation_prompt_text())
        self.translation_prompt_copied = True
        self.copy_prompt_button.setText(self.t("translation_prompt_copied"))
        self.translation_feedback_label.setText(self.t("translation_prompt_copied"))

    def standard_icon(self, icon: QStyle.StandardPixmap) -> QIcon:
        return self.style().standardIcon(icon)

    def prepare_button(
        self,
        button: QPushButton | QToolButton,
        icon: QStyle.StandardPixmap | None = None,
    ) -> None:
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon is not None:
            button.setIcon(self.standard_icon(icon))
        else:
            button.setIcon(QIcon())

    def prepare_add_file_button(self, button: QPushButton) -> None:
        button.setProperty("iconRole", "add-file")
        self.prepare_button(button)
        if self.add_file_icon.isNull():
            button.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_FileIcon))
        else:
            button.setIcon(self.add_file_icon)

    def media_file_icon(self, path: Path) -> QIcon:
        suffix = path.suffix.lower()
        if suffix in VIDEO_EXTENSIONS and not self.video_file_icon.isNull():
            return self.video_file_icon
        if suffix in AUDIO_EXTENSIONS and not self.audio_file_icon.isNull():
            return self.audio_file_icon
        return self.standard_icon(QStyle.StandardPixmap.SP_FileIcon)

    def status_icon_for_key(self, key: str) -> QIcon:
        if key == "file_status_done":
            return self.standard_icon(QStyle.StandardPixmap.SP_DialogApplyButton)
        if key in {"file_status_failed", "file_status_model_failed"}:
            return self.standard_icon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        if key == "file_status_cancelled":
            return self.standard_icon(QStyle.StandardPixmap.SP_DialogCancelButton)
        if key == "file_status_processing":
            return self.standard_icon(QStyle.StandardPixmap.SP_BrowserReload)
        return self.standard_icon(QStyle.StandardPixmap.SP_MessageBoxInformation)

    def status_widget_for_row(self, row: int) -> QueueStatusWidget | None:
        widget = self.table.cellWidget(row, 1)
        return widget if isinstance(widget, QueueStatusWidget) else None

    def set_row_status_widget(self, row: int, key: str, progress: int | None = None) -> None:
        widget = self.status_widget_for_row(row)
        if widget is None:
            widget = QueueStatusWidget()
            self.table.setCellWidget(row, 1, widget)
        if key != "file_status_processing":
            progress = None
        widget.set_status(self.status_icon_for_key(key), self.t(key), progress)

    def prepare_combo(self, combo: QComboBox, max_visible_items: int = 12) -> None:
        combo.setMaxVisibleItems(max_visible_items)
        combo.view().setObjectName("ComboPopup")

    def build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("HeaderPanel")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(8)

        self.logo_label = QLabel("A")
        self.logo_label.setObjectName("AppLogo")
        self.logo_label.setFixedSize(44, 44)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not self.app_icon.isNull():
            self.logo_label.setPixmap(self.app_icon.pixmap(QSize(44, 44)))

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.title_label = QLabel(APP_DISPLAY_NAME)
        self.title_label.setObjectName("WindowTitle")
        self.subtitle_label = QLabel(APP_PRODUCT_SUBTITLE)
        self.subtitle_label.setObjectName("WindowSubtitle")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)

        self.ui_language_combo = QComboBox()
        self.ui_language_combo.setObjectName("LanguageSwitch")
        for code, label in UI_LANGUAGE_OPTIONS:
            self.ui_language_combo.addItem(label, code)
        self.ui_language_combo.setMinimumWidth(122)
        self.prepare_combo(self.ui_language_combo, max_visible_items=3)
        self.set_combo_data(self.ui_language_combo, self.ui_language)

        self.add_files_button = QPushButton("添加文件")
        self.add_files_button.setProperty("variant", "accent")
        self.prepare_add_file_button(self.add_files_button)
        self.translation_button = QPushButton("翻译字幕")
        self.translation_button.setProperty("variant", "secondary")
        self.prepare_button(self.translation_button)
        self.open_folder_action = QAction("打开输出文件夹", self)
        self.clear_action = QAction("清空队列", self)
        self.remove_action = QAction("移除选中", self)
        self.clear_completed_action = QAction("清除已完成", self)
        self.retry_failed_action = QAction("重试失败", self)
        self.open_folder_action.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.clear_action.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_TrashIcon))
        self.remove_action.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.clear_completed_action.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.retry_failed_action.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_BrowserReload))
        self.start_button = QPushButton("开始处理")
        self.start_button.setProperty("variant", "primary")
        self.start_button.setToolTip("开始处理当前文件队列")
        self.prepare_button(self.start_button)
        if self.play_icon.isNull():
            self.start_button.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.start_button.setIcon(self.play_icon)
        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setProperty("variant", "danger")
        self.stop_button.setToolTip("停止后会在当前步骤结束时退出")
        self.stop_button.setMinimumWidth(92)
        self.stop_button.setVisible(False)
        self.prepare_button(self.stop_button)

        layout.addWidget(self.logo_label)
        layout.addLayout(title_box, 1)
        layout.addWidget(self.ui_language_combo)
        layout.addWidget(self.translation_button)
        layout.addWidget(self.add_files_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        return header

    def build_file_panel(self) -> QWidget:
        panel = QFrame()
        panel.setProperty("role", "card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.file_queue_title_label = QLabel("文件队列")
        self.file_queue_title_label.setObjectName("SectionTitle")
        self.file_count_label = QLabel("0 个文件")
        self.file_count_label.setObjectName("MutedText")
        header.addWidget(self.file_queue_title_label)
        header.addWidget(self.file_count_label)
        header.addStretch()
        layout.addLayout(header)

        self.empty_state = QWidget()
        self.empty_state.setObjectName("EmptyState")
        self.empty_state.setMinimumHeight(44 + 58 * 4 + 16)
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(0, 28, 0, 28)
        empty_layout.setSpacing(8)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title_label = QLabel("还没有添加文件")
        self.empty_title_label.setObjectName("SectionTitle")
        self.empty_hint_label = QLabel("点击“添加文件”选择多个媒体文件，或直接把文件拖入窗口。")
        self.empty_hint_label.setObjectName("MutedText")
        self.empty_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_add_files_button = QPushButton("添加文件")
        self.empty_add_files_button.setProperty("variant", "primary")
        self.empty_add_files_button.setToolTip("选择一个或多个视频、音频文件")
        self.prepare_add_file_button(self.empty_add_files_button)
        empty_layout.addWidget(self.empty_title_label, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_hint_label, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_add_files_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.table = QTableWidget(0, 3)
        self.table.setObjectName("QueueTable")
        self.table.setHorizontalHeaderLabels(["文件", "状态", "字幕目录"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeader().setMinimumHeight(44)
        self.table.setColumnWidth(1, 220)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(64)
        self.table.setMinimumHeight(44 + 64 * 5 + 18)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.queue_context_menu = QMenu(self.table)
        self.queue_context_menu.setObjectName("ActionMenu")
        self.queue_context_menu.addAction(self.open_folder_action)
        self.queue_context_menu.addSeparator()
        self.queue_context_menu.addAction(self.remove_action)
        self.queue_context_menu.addAction(self.clear_completed_action)
        self.queue_context_menu.addAction(self.retry_failed_action)
        self.queue_context_menu.addSeparator()
        self.queue_context_menu.addAction(self.clear_action)

        layout.addWidget(self.empty_state, 1)
        layout.addWidget(self.table, 4)
        return panel

    def build_settings_panel(self) -> QWidget:
        panel = QFrame()
        panel.setProperty("role", "card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.settings_title_label = QLabel("常用设置")
        self.settings_title_label.setObjectName("SectionTitle")
        self.advanced_button = QToolButton()
        self.advanced_button.setText("高级设置")
        self.advanced_button.setProperty("variant", "ghost")
        self.advanced_button.setCheckable(False)
        self.advanced_button.setToolTip("设备、音频分块等不常改的选项")
        self.advanced_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.advanced_button.setArrowType(Qt.ArrowType.NoArrow)
        self.prepare_button(self.advanced_button)
        title_row.addWidget(self.settings_title_label)
        title_row.addStretch()
        title_row.addWidget(self.advanced_button)
        layout.addLayout(title_row)

        common = QGridLayout()
        common.setHorizontalSpacing(8)
        common.setVerticalSpacing(8)
        common.setColumnMinimumWidth(0, 72)
        common.setColumnMinimumWidth(2, 72)
        common.setColumnMinimumWidth(4, 72)
        common.setColumnStretch(1, 1)
        common.setColumnStretch(3, 0)
        common.setColumnStretch(5, 0)

        self.context_edit = QLineEdit()
        self.context_edit.setPlaceholderText("可选：片名、角色名、人名、地名；不确定时留空")
        self.context_edit.setToolTip("提供片名或角色名可帮助模型识别专有名词，不确定时留空")

        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(140)
        self.language_combo.setToolTip("默认自动识别；明确知道音频语言时可手动指定")
        self.prepare_combo(self.language_combo)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(120)
        self.profile_combo.setToolTip("推荐适合大多数情况，低显存会使用更保守的参数")
        self.prepare_combo(self.profile_combo)

        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(list(ASR_MODEL_SIZES))
        self.model_size_combo.setCurrentText(DEFAULT_MODEL_SIZE)
        self.model_size_combo.setMinimumWidth(100)
        self.model_size_combo.setToolTip("1.7B 质量更好；0.6B 更省显存、速度更快")
        self.prepare_combo(self.model_size_combo)

        self.context_label = QLabel("上下文")
        self.recognition_language_label = QLabel("识别语言")
        self.profile_label = QLabel("运行模式")
        self.model_size_label = QLabel("模型尺寸")

        common.addWidget(self.context_label, 0, 0)
        common.addWidget(self.context_edit, 0, 1, 1, 5)
        common.addWidget(self.recognition_language_label, 1, 0)
        common.addWidget(self.language_combo, 1, 1)
        common.addWidget(self.profile_label, 1, 2)
        common.addWidget(self.profile_combo, 1, 3)
        common.addWidget(self.model_size_label, 1, 4)
        common.addWidget(self.model_size_combo, 1, 5)
        layout.addLayout(common)

        self.advanced_dialog = self.build_advanced_settings_dialog()
        self.translation_dialog = self.build_translation_dialog()
        return panel

    def build_translation_dialog(self) -> QDialog:
        dialog = QDialog(self)
        dialog.setWindowTitle("SRT 字幕翻译")
        dialog.setModal(True)
        dialog.setMinimumWidth(820)
        if not self.app_icon.isNull():
            dialog.setWindowIcon(self.app_icon)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.translation_intro_label = QLabel("本功能不在软件内处理翻译，而是引导你使用 DeepSeek Chat 翻译已生成的 SRT 文件。")
        self.translation_intro_label.setObjectName("HintText")
        self.translation_intro_label.setWordWrap(True)
        layout.addWidget(self.translation_intro_label)

        steps = QFrame()
        steps.setProperty("role", "card")
        steps_layout = QVBoxLayout(steps)
        steps_layout.setContentsMargins(16, 14, 16, 16)
        steps_layout.setSpacing(8)

        self.translation_steps_title_label = QLabel("操作步骤")
        self.translation_steps_title_label.setObjectName("SectionTitle")
        steps_layout.addWidget(self.translation_steps_title_label)

        self.translation_step_open_label = QLabel()
        self.translation_step_upload_label = QLabel()
        self.translation_step_prompt_label = QLabel()
        for label in (
            self.translation_step_open_label,
            self.translation_step_upload_label,
            self.translation_step_prompt_label,
        ):
            label.setObjectName("HintText")
            label.setWordWrap(True)
            steps_layout.addWidget(label)
        layout.addWidget(steps)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.open_deepseek_button = QPushButton("打开 DeepSeek 官网")
        self.open_deepseek_button.setProperty("variant", "primary")
        self.prepare_button(self.open_deepseek_button)
        self.copy_prompt_button = QPushButton("复制提示词")
        self.copy_prompt_button.setProperty("variant", "accent")
        self.prepare_button(self.copy_prompt_button)
        self.translation_feedback_label = QLabel("")
        self.translation_feedback_label.setObjectName("HintText")
        action_row.addWidget(self.open_deepseek_button)
        action_row.addWidget(self.copy_prompt_button)
        action_row.addWidget(self.translation_feedback_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        self.translation_prompt_label = QLabel("预设提示词")
        self.translation_prompt_label.setObjectName("SectionTitle")
        layout.addWidget(self.translation_prompt_label)

        self.translation_prompt_box = QPlainTextEdit()
        self.translation_prompt_box.setReadOnly(True)
        self.translation_prompt_box.setMinimumHeight(190)
        layout.addWidget(self.translation_prompt_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        self.translation_close_button = close_button
        if close_button is not None:
            close_button.setText("关闭")
            close_button.setProperty("variant", "secondary")
            self.prepare_button(close_button)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        return dialog

    def build_advanced_settings_dialog(self) -> QDialog:
        dialog = QDialog(self)
        dialog.setWindowTitle("高级设置")
        dialog.setModal(True)
        dialog.setMinimumWidth(760)
        if not self.app_icon.isNull():
            dialog.setWindowIcon(self.app_icon)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.advanced_hint_label = QLabel("设备、音频分块和字幕样式属于低频选项，通常保持默认即可。")
        self.advanced_hint_label.setObjectName("HintText")
        layout.addWidget(self.advanced_hint_label)

        content = QFrame()
        content.setProperty("role", "card")
        grid = QGridLayout(content)
        grid.setContentsMargins(16, 14, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 96)
        grid.setColumnMinimumWidth(2, 96)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("一般保持自动；只有排查问题时再手动指定设备")
        self.prepare_combo(self.device_combo)

        self.batch_size_value = 1
        self.max_new_tokens_value = 2048
        self.dtype_value = "auto"

        self.chunk_seconds_combo = QComboBox()
        self.chunk_seconds_combo.setToolTip("只提供常用预设，避免无意义的秒级微调")
        self.prepare_combo(self.chunk_seconds_combo)

        self.caption_preset_combo = QComboBox()
        self.caption_preset_combo.setToolTip("控制字幕换行倾向；推荐适合大多数电影对白")
        self.prepare_combo(self.caption_preset_combo)

        self.overwrite_check = QCheckBox("覆盖已有输出")
        self.overwrite_check.setChecked(False)
        self.overwrite_check.setToolTip("未勾选时如字幕已存在，会在开始处理前询问是否覆盖")
        self.local_only_check = QCheckBox("只使用本地模型缓存")
        self.local_only_check.setToolTip("勾选后不会下载缺失模型")

        self.device_label = QLabel("设备")
        self.chunk_seconds_label = QLabel("音频分块")
        self.caption_preset_label = QLabel("字幕样式")

        grid.addWidget(self.device_label, 0, 0)
        grid.addWidget(self.device_combo, 0, 1)
        grid.addWidget(self.chunk_seconds_label, 0, 2)
        grid.addWidget(self.chunk_seconds_combo, 0, 3)
        grid.addWidget(self.caption_preset_label, 1, 0)
        grid.addWidget(self.caption_preset_combo, 1, 1)
        grid.addWidget(self.overwrite_check, 2, 1)
        grid.addWidget(self.local_only_check, 2, 3)
        layout.addWidget(content)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        self.advanced_close_button = close_button
        if close_button is not None:
            close_button.setText("关闭")
            close_button.setProperty("variant", "secondary")
            self.prepare_button(close_button)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        return dialog

    def build_progress_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("StatusCard")
        panel.setProperty("role", "card")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        self.status_icon_label = QLabel("✓")
        self.status_icon_label.setObjectName("StatusIcon")
        self.status_icon_label.setProperty("state", "ready")
        self.status_icon_label.setFixedSize(36, 36)
        self.status_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        self.phase_label = QLabel("准备就绪")
        self.phase_label.setObjectName("SectionTitle")
        self.current_label = QLabel("请先添加文件")
        self.current_label.setObjectName("HintText")
        text_box.addWidget(self.phase_label)
        text_box.addWidget(self.current_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumWidth(360)
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setObjectName("StatusPercent")
        self.progress_percent_label.setMinimumWidth(46)
        self.progress_percent_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.status_icon_label)
        layout.addLayout(text_box)
        layout.addStretch()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_percent_label)
        return panel

    def build_log_panel(self) -> QWidget:
        panel = QFrame()
        panel.setProperty("role", "card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.log_title_label = QLabel("运行日志")
        self.log_title_label.setObjectName("SectionTitle")
        self.show_technical_log_check = QCheckBox("显示技术日志")
        self.show_technical_log_check.setToolTip("默认只显示普通提示，勾选后查看完整技术日志")
        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.setProperty("variant", "secondary")
        self.clear_log_button.setToolTip("清空当前运行日志")
        self.clear_log_button.setEnabled(False)
        self.prepare_button(self.clear_log_button)
        header.addWidget(self.log_title_label)
        header.addStretch()
        header.addWidget(self.show_technical_log_check)
        header.addWidget(self.clear_log_button)
        layout.addLayout(header)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("处理日志会显示在这里。")
        layout.addWidget(self.log_box)
        return panel

    def apply_language(self) -> None:
        self.setWindowTitle(self.t("product_name"))
        self.title_label.setText(self.t("product_name"))
        self.subtitle_label.setText(self.t("product_subtitle"))
        self.ui_language_combo.setToolTip(self.t("ui_language_tooltip"))
        self.add_files_button.setText(self.t("add_files"))
        self.add_files_button.setToolTip(self.t("add_files"))
        self.translation_button.setText(self.t("translate_srt"))
        self.translation_button.setToolTip(self.t("translate_srt_tooltip"))
        self.empty_add_files_button.setText(self.t("add_files"))
        self.empty_add_files_button.setToolTip(self.t("add_files"))
        self.start_button.setText(self.t("start"))
        self.start_button.setToolTip(self.t("start"))
        self.stop_button.setText(self.t("stop"))
        self.stop_button.setToolTip(self.t("stop"))

        self.open_folder_action.setText(self.t("open_output_folder"))
        self.clear_action.setText(self.t("clear_queue"))
        self.remove_action.setText(self.t("remove_selected"))
        self.clear_completed_action.setText(self.t("clear_completed"))
        self.retry_failed_action.setText(self.t("retry_failed"))

        self.file_queue_title_label.setText(self.t("queue_title"))
        self.empty_title_label.setText(self.t("empty_title"))
        self.empty_hint_label.setText(self.t("empty_hint"))
        self.table.setHorizontalHeaderLabels(
            [self.t("table_file"), self.t("table_status"), self.t("table_subtitle_dir")]
        )

        self.settings_title_label.setText(self.t("settings_title"))
        self.advanced_button.setText(self.t("advanced_settings"))
        self.advanced_button.setToolTip(self.t("advanced_tooltip"))
        self.context_label.setText(self.t("context_label"))
        self.context_edit.setPlaceholderText(self.t("context_placeholder"))
        self.context_edit.setToolTip(self.t("context_tooltip"))
        self.recognition_language_label.setText(self.t("recognition_language"))
        self.language_combo.setToolTip(self.t("recognition_language_tooltip"))
        self.profile_label.setText(self.t("profile_label"))
        self.profile_combo.setToolTip(self.t("profile_tooltip"))
        self.model_size_label.setText(self.t("model_size"))
        self.model_size_combo.setToolTip(self.t("model_size_tooltip"))

        self.advanced_dialog.setWindowTitle(self.t("advanced_settings"))
        self.advanced_hint_label.setText(self.t("advanced_hint"))
        self.device_label.setText(self.t("device"))
        self.device_combo.setToolTip(self.t("device_tooltip"))
        self.chunk_seconds_label.setText(self.t("audio_chunk"))
        self.chunk_seconds_combo.setToolTip(self.t("chunk_tooltip"))
        self.caption_preset_label.setText(self.t("caption_style"))
        self.caption_preset_combo.setToolTip(self.t("caption_tooltip"))
        self.overwrite_check.setText(self.t("overwrite"))
        self.overwrite_check.setToolTip(self.t("overwrite_tooltip"))
        self.local_only_check.setText(self.t("local_only"))
        self.local_only_check.setToolTip(self.t("local_only_tooltip"))
        if self.advanced_close_button is not None:
            self.advanced_close_button.setText(self.t("close"))

        self.translation_dialog.setWindowTitle(self.t("translation_dialog_title"))
        self.translation_intro_label.setText(self.t("translation_intro"))
        self.translation_steps_title_label.setText(self.t("translation_steps_title"))
        self.translation_step_open_label.setText(self.t("translation_step_open"))
        self.translation_step_upload_label.setText(self.t("translation_step_upload"))
        self.translation_step_prompt_label.setText(self.t("translation_step_prompt"))
        self.open_deepseek_button.setText(self.t("open_deepseek"))
        self.open_deepseek_button.setToolTip(self.t("open_deepseek_tooltip"))
        self.copy_prompt_button.setText(
            self.t("translation_prompt_copied") if self.translation_prompt_copied else self.t("copy_prompt")
        )
        self.copy_prompt_button.setToolTip(self.t("copy_prompt_tooltip"))
        self.translation_feedback_label.setText(
            self.t("translation_prompt_copied") if self.translation_prompt_copied else ""
        )
        self.translation_prompt_label.setText(self.t("translation_prompt_label"))
        self.translation_prompt_box.setPlainText(self.translation_prompt_text())
        if self.translation_close_button is not None:
            self.translation_close_button.setText(self.t("close"))

        self.log_title_label.setText(self.t("log_title"))
        self.show_technical_log_check.setText(self.t("show_technical_log"))
        self.show_technical_log_check.setToolTip(self.t("show_technical_log_tooltip"))
        self.clear_log_button.setText(self.t("clear_log"))
        self.clear_log_button.setToolTip(self.t("clear_log_tooltip"))
        self.log_box.setPlaceholderText(self.t("log_placeholder"))

        self.set_labeled_combo(self.language_combo, LANGUAGE_PRESETS, DEFAULT_LANGUAGE)
        self.set_labeled_combo(self.profile_combo, PROFILE_PRESETS, "recommended")
        self.set_labeled_combo(self.device_combo, DEVICE_PRESETS, "auto")
        self.set_labeled_combo(self.chunk_seconds_combo, CHUNK_PRESETS, DEFAULT_CHUNK_SECONDS)
        self.set_labeled_combo(self.caption_preset_combo, CAPTION_PRESETS, (22, 44))

        for row in range(self.table.rowCount()):
            self.update_row_status_text(row)
        self.set_status_text(
            self.status_phase_key,
            self.status_current_key,
            **self.status_current_values,
        )
        self.update_file_count()
        self.refresh_log_view()

    def apply_style(self) -> None:
        app = QApplication.instance()
        if app is not None and app.styleSheet() != APP_QSS:
            app.setStyleSheet(APP_QSS)
        self.setStyleSheet(APP_QSS)

    def add_files(self) -> None:
        extensions = " ".join(f"*{suffix}" for suffix in sorted(MEDIA_EXTENSIONS))
        selected, _ = QFileDialog.getOpenFileNames(
            self,
            self.t("select_media_files"),
            str(Path.cwd()),
            self.t("media_files_filter", extensions=extensions),
        )
        if not selected:
            return

        self.add_paths([Path(value) for value in selected])

    def add_paths(self, paths: list[Path]) -> None:
        if self.is_running():
            return

        media_paths = collect_media_paths(paths)
        if not media_paths:
            self.show_message(
                QMessageBox.Icon.Information,
                self.t("msg_no_media_title"),
                self.t("msg_no_media_body"),
            )
            return

        known = {path.resolve() for path in self.files}
        added = 0
        for path in media_paths:
            if path not in known:
                self.files.append(path)
                known.add(path)
                self.add_file_row(path)
                added += 1

        self.update_file_count()
        self.set_status_text("status_ready", "status_ready_with_files", count=len(self.files))
        self.set_status_icon("✓")

    def add_file_row(self, path: Path) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        file_item = QTableWidgetItem(path.name)
        file_item.setIcon(self.media_file_icon(path))
        file_item.setToolTip(str(path))
        status_item = QTableWidgetItem("")
        status_item.setData(STATUS_ROLE, "file_status_waiting")
        status_item.setToolTip(self.t("file_status_waiting"))
        out_dir = str(path.parent)
        output_item = QTableWidgetItem(out_dir)
        output_item.setIcon(self.standard_icon(QStyle.StandardPixmap.SP_DirIcon))
        output_item.setToolTip(out_dir)

        self.table.setItem(row, 0, file_item)
        self.table.setItem(row, 1, status_item)
        self.table.setItem(row, 2, output_item)
        self.set_row_status_widget(row, "file_status_waiting")

    def status_key_from_text(self, status: str) -> str:
        if "模型加载失败" in status or "Model load failed" in status or "模型載入失敗" in status:
            return "file_status_model_failed"
        if "完成" in status or status == "Done":
            return "file_status_done"
        if "失败" in status or "失敗" in status or "Failed" in status:
            return "file_status_failed"
        if "取消" in status or "Cancelled" in status:
            return "file_status_cancelled"
        if "处理" in status or "處理" in status or "Processing" in status:
            return "file_status_processing"
        return "file_status_waiting"

    def row_status_key(self, row: int) -> str:
        item = self.table.item(row, 1)
        if item is None:
            return "file_status_waiting"
        key = item.data(STATUS_ROLE)
        if isinstance(key, str):
            return key
        return self.status_key_from_text(item.text())

    def update_row_status_text(self, row: int) -> None:
        item = self.table.item(row, 1)
        if item is None:
            return
        key = self.row_status_key(row)
        item.setData(STATUS_ROLE, key)
        item.setText("")
        item.setIcon(QIcon())
        item.setToolTip(self.t(key))
        progress = self.progress_bar.value() if self.current_processing_row == row else None
        self.set_row_status_widget(row, key, progress)

    def clear_files(self) -> None:
        if self.is_running():
            return
        self.files.clear()
        self.table.setRowCount(0)
        self.current_processing_row = None
        self.set_progress_value(0)
        self.set_status_text("status_ready", "status_add_files")
        self.set_status_icon("✓")
        self.log_box.clear()
        self.full_log.clear()
        self.clear_log_button.setEnabled(False)
        self.update_file_count()

    def remove_selected_files(self) -> None:
        if self.is_running():
            return
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        if not rows and self.table.currentRow() >= 0:
            rows = [self.table.currentRow()]
        for row in rows:
            self.table.removeRow(row)
            del self.files[row]
        self.update_file_count()
        if not self.files:
            self.set_status_text("status_ready", "status_add_files")
            self.set_status_icon("✓")

    def clear_completed_files(self) -> None:
        if self.is_running():
            return
        rows = [
            row
            for row in range(self.table.rowCount())
            if self.row_status_key(row) == "file_status_done"
        ]
        for row in reversed(rows):
            self.table.removeRow(row)
            del self.files[row]
        self.update_file_count()

    def retry_failed_files(self) -> None:
        if self.is_running():
            return
        failed_rows = [
            row
            for row in range(self.table.rowCount())
            if self.row_status_key(row) in {"file_status_failed", "file_status_model_failed"}
        ]
        if not failed_rows:
            self.show_message(
                QMessageBox.Icon.Information,
                self.t("msg_no_failed_title"),
                self.t("msg_no_failed_body"),
            )
            return

        self.files = [self.files[row] for row in failed_rows]
        failed_files = list(self.files)
        self.table.setRowCount(0)
        for path in failed_files:
            self.add_file_row(path)
        self.update_file_count()
        self.set_status_text("status_ready", "status_kept_failed", count=len(self.files))

    def show_table_context_menu(self, position) -> None:
        if self.is_running() or not self.files:
            return

        row = self.table.indexAt(position).row()
        if row >= 0:
            self.table.selectRow(row)

        self.update_queue_actions()
        self.queue_context_menu.exec(self.table.viewport().mapToGlobal(position))

    def set_combo_data(self, combo: QComboBox, value: object) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def apply_profile(self, profile: str | None = None) -> None:
        profile = profile or self.profile_combo.currentData() or "recommended"
        if profile == "低显存":
            self.set_combo_data(self.device_combo, "cuda:0")
            self.set_combo_data(self.chunk_seconds_combo, 30)
            self.batch_size_value = 1
            self.max_new_tokens_value = 1536
            self.dtype_value = "auto"
        elif profile == "low_vram":
            self.set_combo_data(self.device_combo, "cuda:0")
            self.set_combo_data(self.chunk_seconds_combo, 30)
            self.batch_size_value = 1
            self.max_new_tokens_value = 1536
            self.dtype_value = "auto"
        elif profile == "CPU 慢速" or profile == "cpu_slow":
            self.set_combo_data(self.device_combo, "cpu")
            self.set_combo_data(self.chunk_seconds_combo, 30)
            self.batch_size_value = 1
            self.max_new_tokens_value = 1536
            self.dtype_value = "float32"
        else:
            self.set_combo_data(self.device_combo, "auto")
            self.set_combo_data(self.chunk_seconds_combo, DEFAULT_CHUNK_SECONDS)
            self.batch_size_value = 1
            self.max_new_tokens_value = 2048
            self.dtype_value = "auto"

    def show_advanced_settings(self) -> None:
        self.exec_centered_dialog(self.advanced_dialog)

    def options(self) -> GuiOptions:
        max_line_chars, max_caption_chars = self.caption_preset_combo.currentData()
        return GuiOptions(
            out_dir=None,
            context=self.context_edit.text().strip(),
            language=self.language_combo.currentData() or DEFAULT_LANGUAGE,
            model=resolve_asr_model(self.model_size_combo.currentText()),
            aligner=DEFAULT_ALIGNER,
            device=self.device_combo.currentData() or "auto",
            dtype=self.dtype_value,
            batch_size=self.batch_size_value,
            max_new_tokens=self.max_new_tokens_value,
            max_line_chars=max_line_chars,
            max_caption_chars=max_caption_chars,
            chunk_seconds=self.chunk_seconds_combo.currentData() or DEFAULT_CHUNK_SECONDS,
            overwrite=self.overwrite_check.isChecked(),
            local_files_only=self.local_only_check.isChecked(),
        )

    def start_processing(self) -> None:
        if self.is_running():
            return
        if not self.files:
            self.show_message(
                QMessageBox.Icon.Information,
                self.t("msg_no_files_title"),
                self.t("msg_no_files_body"),
            )
            return

        options = self.options()
        diagnostics_output = options.out_dir or self.files[0].parent
        diagnostics = run_diagnostics(Path.cwd(), output_dir=diagnostics_output)
        blocked = blocking_messages(diagnostics)
        if blocked:
            self.show_message(
                QMessageBox.Icon.Critical,
                self.t("msg_diagnostics_failed"),
                format_diagnostics_for_ui(diagnostics, self.ui_language),
            )
            return

        if not options.overwrite:
            conflicts = output_conflicts(self.files, options.out_dir)
            if conflicts:
                preview = "\n".join(f"  - {path}" for path in conflicts[:8])
                if len(conflicts) > 8:
                    preview += f"\n  - {self.t('msg_more_files', count=len(conflicts) - 8)}"
                if not self.ask_overwrite_outputs(preview):
                    return
                options.overwrite = True
                self.overwrite_check.setChecked(True)

        self.set_running(True)
        self.set_progress_value(0)
        self.set_status_text("status_processing", "status_loading_model")
        self.set_status_icon("...", "processing")
        self.log_box.clear()
        self.full_log.clear()
        self.clear_log_button.setEnabled(False)
        self.append_log("[START] 开始处理")

        self.thread = QThread(self)
        self.worker = SubtitleWorker(list(self.files), options)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.file_status.connect(self.update_file_status)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.processing_finished)
        self.thread.start()

    def append_log(self, message: str) -> None:
        self.full_log.append(message)
        self.clear_log_button.setEnabled(True)
        shown = self.display_log_text(message)
        if not shown:
            return
        self.log_box.appendPlainText(shown)
        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_log_view(self, _checked: bool | None = None) -> None:
        self.log_box.clear()
        for message in self.full_log:
            shown = self.display_log_text(message)
            if shown:
                self.log_box.appendPlainText(shown)
        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def display_log_text(self, message: str) -> str | None:
        if self.show_technical_log_check.isChecked():
            return technical_log_text(message, self.ui_language)
        return user_log_text(message, self.ui_language)

    def clear_log(self) -> None:
        if not self.full_log:
            return
        self.full_log.clear()
        self.log_box.clear()
        self.clear_log_button.setEnabled(False)

    def set_status_icon(self, text: str, state: str = "ready") -> None:
        self.status_icon_label.setText(text)
        self.status_icon_label.setProperty("state", state)
        self.status_icon_label.style().unpolish(self.status_icon_label)
        self.status_icon_label.style().polish(self.status_icon_label)
        self.status_icon_label.update()

    def update_file_status(self, row: int, status: str, out_dir: str) -> None:
        key = self.status_key_from_text(status)
        status_item = self.table.item(row, 1)
        status_item.setData(STATUS_ROLE, key)
        status_item.setText("")
        status_item.setIcon(QIcon())
        status_item.setToolTip(self.t(key))
        if key == "file_status_processing":
            self.current_processing_row = row
            self.set_row_status_widget(row, key, self.progress_bar.value())
        else:
            if self.current_processing_row == row:
                self.current_processing_row = None
            self.set_row_status_widget(row, key)
        self.table.item(row, 2).setText(out_dir)
        self.table.item(row, 2).setToolTip(out_dir)
        self.update_queue_actions()

    def set_progress_value(self, percent: int) -> None:
        value = max(0, min(100, percent))
        self.progress_bar.setValue(value)
        self.progress_percent_label.setText(f"{value}%")
        if self.current_processing_row is not None:
            self.set_row_status_widget(self.current_processing_row, "file_status_processing", value)

    def progress_detail_text(self, detail: str) -> str:
        if detail == "正在加载模型，首次运行可能需要下载模型":
            return self.t("status_loading_model")
        if detail == "模型加载失败":
            return self.t("progress_model_failed")
        if detail == "已取消后续任务":
            return self.t("progress_cancel_remaining")
        if detail == "已取消处理":
            return self.t("progress_cancelled")
        if detail.startswith("正在处理 "):
            prefix, _, name = detail.partition(": ")
            count_text = prefix.replace("正在处理 ", "")
            index, _, total = count_text.partition("/")
            return self.t("progress_processing_file", index=index, total=total, name=name)
        if detail.startswith("已完成 "):
            count_text = detail.replace("已完成 ", "")
            index, _, total = count_text.partition("/")
            return self.t("progress_done_count", index=index, total=total)

        filename, separator, progress = detail.partition(" - ")
        if separator:
            return f"{filename} - {self.progress_detail_text(progress)}"
        if detail == "使用缓存音频":
            return self.t("progress_cached_audio")
        if detail == "音频准备完成":
            return self.t("progress_audio_ready")
        if detail == "准备识别":
            return self.t("progress_prepare_asr")
        if detail == "完成":
            return self.t("progress_done")
        if detail.startswith("提取音频 "):
            return self.t("progress_extract_audio", percent=detail.replace("提取音频 ", "").rstrip("%"))
        if detail.startswith("识别字幕 "):
            return self.t("progress_recognize", percent=detail.replace("识别字幕 ", "").rstrip("%"))
        return detail

    def update_progress(self, percent: int, detail: str) -> None:
        self.set_progress_value(percent)
        self.last_progress_detail = detail
        self.current_label.setText(self.progress_detail_text(detail))
        if percent < 100:
            self.status_phase_key = "status_processing"
            self.phase_label.setText(self.t("status_processing"))
            self.set_status_icon("...", "processing")

    def processing_finished(self) -> None:
        self.set_running(False)
        self.thread = None
        self.worker = None
        status_keys = [self.row_status_key(row) for row in range(self.table.rowCount())]
        success = sum(key == "file_status_done" for key in status_keys)
        failed = sum(key in {"file_status_failed", "file_status_model_failed"} for key in status_keys)
        cancelled = sum(key == "file_status_cancelled" for key in status_keys)
        if cancelled:
            self.set_status_text(
                "status_cancelled",
                "status_summary",
                success=success,
                failed=failed,
                cancelled=cancelled,
            )
            self.set_status_icon("!", "warning")
        elif failed:
            self.set_status_text("status_done_with_failed", "status_failed_detail", failed=failed)
            self.set_status_icon("!", "danger")
        else:
            self.set_status_text("status_done", "status_open_output")
            self.set_status_icon("✓")
            self.set_progress_value(100)
        self.append_log("[DONE] 处理结束")

        self.show_message(
            QMessageBox.Icon.Information,
            self.t("msg_finished_title"),
            self.t("msg_finished_body", success=success, failed=failed, cancelled=cancelled),
        )

    def set_running(self, running: bool) -> None:
        self.ui_running = running
        self.add_files_button.setEnabled(not running)
        self.empty_add_files_button.setEnabled(not running)
        self.start_button.setVisible(not running)
        self.stop_button.setVisible(running)
        self.stop_button.setEnabled(running)
        self.progress_panel.hide()
        if not running:
            self.current_processing_row = None
        self.update_file_count()

    def request_stop(self) -> None:
        if self.worker is None:
            return
        self.worker.request_stop()
        self.stop_button.setEnabled(False)
        self.set_status_text("status_processing", "status_stopping")
        self.set_status_icon("...", "processing")
        self.append_log("[CANCEL] 已请求停止处理")

    def is_running(self) -> bool:
        return self.ui_running or (self.thread is not None and self.thread.isRunning())

    def open_output_folder(self) -> None:
        path: Path | None = None
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            path = Path(self.table.item(selected_row, 2).text())
        elif self.files:
            path = self.files[0].parent

        if not path:
            self.show_message(
                QMessageBox.Icon.Information,
                self.t("msg_no_dir_title"),
                self.t("msg_no_dir_body"),
            )
            return

        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def update_file_count(self) -> None:
        has_files = bool(self.files)
        running = self.is_running()
        count = len(self.files)
        if self.ui_language == "en":
            self.file_count_label.setText(f"{count} {'file' if count == 1 else 'files'}")
        elif self.ui_language == "zh-Hant":
            self.file_count_label.setText(f"{count} 個檔案")
        else:
            self.file_count_label.setText(f"{count} 个文件")
        self.empty_state.setVisible(not has_files)
        self.table.setVisible(has_files)
        self.start_button.setEnabled(has_files and not running)
        self.update_queue_actions()

    def update_queue_actions(self) -> None:
        has_files = bool(self.files)
        running = self.is_running()
        statuses = [self.row_status_key(row) for row in range(self.table.rowCount())]
        has_selection = self.table.currentRow() >= 0
        self.open_folder_action.setEnabled(has_files and not running)
        self.clear_action.setEnabled(has_files and not running)
        self.remove_action.setEnabled(has_files and has_selection and not running)
        self.clear_completed_action.setEnabled(
            has_files and any(status == "file_status_done" for status in statuses) and not running
        )
        self.retry_failed_action.setEnabled(
            has_files
            and any(status in {"file_status_failed", "file_status_model_failed"} for status in statuses)
            and not running
        )

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.is_running():
            self.show_message(
                QMessageBox.Icon.Information,
                self.t("msg_running_title"),
                self.t("msg_running_body"),
            )
            event.ignore()
            return
        event.accept()


def main() -> int:
    if "--check" in sys.argv:
        print("ai-sub-gui OK")
        return 0

    configure_high_dpi_scaling()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
