from __future__ import annotations

from pathlib import Path


CHEVRON_DOWN_ICON_PATH = Path(__file__).with_name("assets") / "chevron-down.svg"
CHECK_WHITE_ICON_PATH = Path(__file__).with_name("assets") / "check-white.svg"


APP_QSS = """
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    color: #1F2937;
    background: transparent;
}

#RootWidget {
    background-color: #F5F7FB;
}

#RootWidget QLabel,
#RootWidget QPushButton,
#RootWidget QToolButton,
#RootWidget QLineEdit,
#RootWidget QComboBox,
#RootWidget QTableWidget,
#RootWidget QHeaderView::section,
#RootWidget QPlainTextEdit,
#RootWidget QCheckBox {
    font-size: 14pt;
}

QLabel#WindowTitle {
    font-size: 18pt;
    font-weight: 600;
    color: #111827;
}

QLabel#WindowSubtitle,
QLabel#HintText {
    color: #6B7280;
}

QLabel#SectionTitle {
    font-size: 16pt;
    font-weight: 600;
    color: #111827;
}

QLabel#MutedText {
    color: #6B7280;
}

QFrame[role="card"] {
    background-color: #FFFFFF;
    border: 1px solid #E8ECF2;
    border-radius: 14px;
}

QFrame#HeaderPanel {
    background-color: #F5F7FB;
    border: none;
}

QLabel#AppLogo {
    color: #FFFFFF;
    background-color: #2F6BFF;
    border-radius: 12px;
    font-size: 18pt;
    font-weight: 700;
}

QPushButton,
QToolButton {
    min-height: 44px;
    padding: 0 16px;
    border-radius: 10px;
    font-weight: 500;
    color: #1F2937;
    background-color: #FFFFFF;
    border: 1px solid #D9DEE7;
}

QPushButton[variant="primary"],
QToolButton[variant="primary"] {
    color: #FFFFFF;
    background-color: #2F6BFF;
    border: 1px solid #2F6BFF;
}

QPushButton[variant="primary"]:hover,
QToolButton[variant="primary"]:hover {
    background-color: #4D82FF;
    border-color: #4D82FF;
}

QPushButton[variant="primary"]:pressed,
QToolButton[variant="primary"]:pressed {
    background-color: #1F55D6;
    border-color: #1F55D6;
}

QPushButton[variant="accent"],
QToolButton[variant="accent"] {
    color: #1F55D6;
    background-color: #EAF2FF;
    border: 1px solid #8FB1FF;
}

QPushButton[variant="accent"]:hover,
QToolButton[variant="accent"]:hover {
    color: #1747B8;
    background-color: #DCE9FF;
    border-color: #6D98FF;
}

QPushButton[variant="accent"]:pressed,
QToolButton[variant="accent"]:pressed {
    color: #FFFFFF;
    background-color: #2F6BFF;
    border-color: #2F6BFF;
}

QPushButton[variant="secondary"],
QToolButton[variant="secondary"] {
    color: #1F2937;
    background-color: #FFFFFF;
    border: 1px solid #D9DEE7;
}

QPushButton[variant="secondary"]:hover,
QToolButton[variant="secondary"]:hover {
    background-color: #F9FAFB;
    border-color: #C9D2E3;
}

QPushButton[variant="secondary"]:pressed,
QToolButton[variant="secondary"]:pressed {
    background-color: #EEF2F7;
    border-color: #B8C4D8;
}

QPushButton[variant="danger"] {
    color: #FFFFFF;
    background-color: #EF4444;
    border: 1px solid #EF4444;
}

QPushButton[variant="danger"]:hover {
    background-color: #F87171;
    border-color: #F87171;
}

QPushButton[variant="danger"]:pressed {
    background-color: #DC2626;
    border-color: #DC2626;
}

QPushButton#StopButton {
    min-width: 92px;
    padding: 0 14px;
}

QPushButton[variant="ghost"],
QToolButton[variant="ghost"] {
    color: #374151;
    background-color: transparent;
    border: 1px solid transparent;
}

QPushButton[variant="ghost"]:hover,
QToolButton[variant="ghost"]:hover {
    background-color: #F3F6FB;
    border-color: #E8ECF2;
}

QToolButton[variant="ghost"]:checked {
    color: #1F55D6;
    background-color: #EEF4FF;
    border-color: #C9D2E3;
}

QPushButton:focus,
QToolButton:focus {
    border: 1px solid #2F6BFF;
}

QPushButton:disabled,
QToolButton:disabled {
    color: #9CA3AF;
    background-color: #EEF2F7;
    border-color: #E5E7EB;
}

QLineEdit,
QComboBox {
    min-height: 44px;
    border: 1px solid #D9DEE7;
    border-radius: 10px;
    background-color: #FFFFFF;
    color: #1F2937;
}

QLineEdit {
    padding: 0 12px;
}

QComboBox {
    padding: 0 44px 0 12px;
}

QLineEdit:hover,
QComboBox:hover {
    border-color: #C9D2E3;
}

QLineEdit:focus,
QComboBox:focus {
    border: 1px solid #2F6BFF;
}

QLineEdit:disabled,
QComboBox:disabled {
    color: #9CA3AF;
    background-color: #F3F6FB;
    border-color: #E5E7EB;
}

QLabel:disabled,
QCheckBox:disabled {
    color: #9CA3AF;
}

QComboBox::drop-down {
    width: 42px;
    border: none;
    subcontrol-origin: padding;
    subcontrol-position: top right;
}

QComboBox::down-arrow {
    image: url("__CHEVRON_DOWN_ICON__");
    width: 16px;
    height: 16px;
}

QComboBox::down-arrow:on {
    top: 1px;
}

QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #D9DEE7;
    border-radius: 10px;
    gridline-color: transparent;
    show-decoration-selected: 0;
    selection-background-color: transparent;
    selection-color: #1F2937;
    outline: none;
}

QTableWidget::item {
    padding: 0 10px;
    border-bottom: 1px solid #F0F2F5;
}

QTableWidget::item:hover {
    background-color: #F8FAFF;
}

QTableWidget::item:selected {
    color: #1F2937;
    background-color: transparent;
    border-top: 1px solid #D8E4FF;
    border-bottom: 1px solid #D8E4FF;
}

QWidget#QueueStatusWidget {
    background-color: transparent;
}

QLabel#QueueStatusText,
QLabel#QueueStatusPercent {
    color: #1F2937;
}

QLabel#QueueStatusPercent {
    font-weight: 600;
}

QProgressBar#QueueStatusProgress {
    min-height: 6px;
    max-height: 6px;
    border: none;
    border-radius: 3px;
    background-color: #E1E6EF;
}

QProgressBar#QueueStatusProgress::chunk {
    border-radius: 3px;
    background-color: #2F6BFF;
}

QHeaderView::section {
    min-height: 44px;
    padding-left: 10px;
    padding-right: 10px;
    background-color: #F9FAFB;
    color: #374151;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid #E8ECF2;
}

QProgressBar {
    min-height: 10px;
    max-height: 10px;
    border: none;
    border-radius: 5px;
    background-color: #E1E6EF;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    border-radius: 5px;
    background-color: #2F6BFF;
}

QPlainTextEdit {
    background-color: #F9FAFB;
    border: 1px solid #D9DEE7;
    border-radius: 10px;
    padding: 10px;
    color: #374151;
    font-family: "Consolas", "Microsoft YaHei", monospace;
}

QCheckBox {
    color: #374151;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid #C9D2E3;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    image: url("__CHECK_WHITE_ICON__");
    background-color: #2F6BFF;
    border-color: #2F6BFF;
}

QCheckBox::indicator:disabled {
    background-color: #F3F6FB;
    border-color: #E5E7EB;
}

QLabel#StatusIcon {
    color: #35C759;
    border: 2px solid #35C759;
    border-radius: 18px;
    font-size: 16pt;
    font-weight: 700;
    background-color: #FFFFFF;
}

QLabel#StatusIcon[state="processing"] {
    color: #2F6BFF;
    border-color: #2F6BFF;
}

QLabel#StatusIcon[state="warning"] {
    color: #F59E0B;
    border-color: #F59E0B;
}

QLabel#StatusIcon[state="danger"] {
    color: #EF4444;
    border-color: #EF4444;
}

QLabel#StatusPercent {
    color: #374151;
    font-weight: 600;
}

#EmptyState {
    background-color: #FFFFFF;
    border: 1px dashed #C9D2E3;
    border-radius: 10px;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #D9DEE7;
    border-radius: 12px;
    padding: 8px;
}

QMenu::item {
    min-height: 40px;
    padding: 8px 36px 8px 34px;
    border-radius: 8px;
    border: 1px solid transparent;
    color: #1F2937;
}

QMenu::item:selected {
    background-color: #F3F7FF;
    border-color: #D8E4FF;
    color: #1F2937;
}

QMenu::icon {
    padding-left: 10px;
}

QMenu::item:disabled {
    color: #9CA3AF;
}

QMenu::separator {
    height: 1px;
    background-color: #E8ECF2;
    margin: 6px 8px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #D9DEE7;
    border-radius: 10px;
    padding: 6px;
    selection-background-color: #EEF4FF;
    selection-color: #1F2937;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 34px;
    padding: 6px 10px;
    border-radius: 8px;
}

QDialog,
QMessageBox {
    background-color: #F5F7FB;
}

QMessageBox QLabel {
    color: #1F2937;
    background: transparent;
}

QMessageBox QPushButton {
    min-width: 104px;
}

QToolTip {
    color: #1F2937;
    background-color: #FFFFFF;
    border: 1px solid #D9DEE7;
    border-radius: 8px;
    padding: 6px 8px;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px 2px 4px 0;
}

QScrollBar::handle:vertical {
    background: #C9D2E3;
    border-radius: 5px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #9CA3AF;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
""".replace("__CHEVRON_DOWN_ICON__", CHEVRON_DOWN_ICON_PATH.as_posix()).replace(
    "__CHECK_WHITE_ICON__", CHECK_WHITE_ICON_PATH.as_posix()
)
