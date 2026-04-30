from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication

from .gui_i18n import DEFAULT_UI_LANGUAGE, tr


APP_FONT_POINT_SIZE = 12
APP_DISPLAY_NAME = tr(DEFAULT_UI_LANGUAGE, "product_name")
APP_PRODUCT_SUBTITLE = tr(DEFAULT_UI_LANGUAGE, "product_subtitle")
DEEPSEEK_CHAT_URL = "https://chat.deepseek.com/"

APP_ICON_PATH = Path(__file__).with_name("assets") / "app.svg"
FILE_ICON_PATH = Path(__file__).with_name("assets") / "file-yellow.svg"
VIDEO_ICON_PATH = Path(__file__).with_name("assets") / "video-file.svg"
AUDIO_ICON_PATH = Path(__file__).with_name("assets") / "audio-file.svg"
PLAY_ICON_PATH = Path(__file__).with_name("assets") / "play-white.svg"

FONT_FAMILY_CANDIDATES = [
    "Microsoft YaHei",
    "Microsoft YaHei UI",
    "微软雅黑",
    "PingFang SC",
    "Noto Sans CJK SC",
    "Noto Sans SC",
    "SimHei",
    "Segoe UI",
]

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".m4v", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}


def configure_high_dpi_scaling() -> None:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def apply_application_font() -> None:
    app = QApplication.instance()
    if app is not None:
        font = app.font()
        font.setFamily(resolve_ui_font_family())
        font.setPointSize(APP_FONT_POINT_SIZE)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
        app.setFont(font)


def resolve_ui_font_family() -> str:
    available = set(QFontDatabase.families())
    for family in FONT_FAMILY_CANDIDATES:
        if not available or family in available:
            return family
    return QApplication.font().family()


def load_app_icon() -> QIcon:
    return QIcon(str(APP_ICON_PATH)) if APP_ICON_PATH.exists() else QIcon()


def load_add_file_icon() -> QIcon:
    return QIcon(str(FILE_ICON_PATH)) if FILE_ICON_PATH.exists() else QIcon()


def load_svg_icon(path: Path) -> QIcon:
    return QIcon(str(path)) if path.exists() else QIcon()
