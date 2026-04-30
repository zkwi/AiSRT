from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class QueueStatusWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("QueueStatusWidget")
        self.setMinimumWidth(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 8, 5)
        layout.setSpacing(4)

        text_row = QHBoxLayout()
        text_row.setContentsMargins(0, 0, 0, 0)
        text_row.setSpacing(6)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("QueueStatusIcon")
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel()
        self.text_label.setObjectName("QueueStatusText")

        self.percent_label = QLabel()
        self.percent_label.setObjectName("QueueStatusPercent")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        text_row.addWidget(self.icon_label)
        text_row.addWidget(self.text_label, 1)
        text_row.addWidget(self.percent_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("QueueStatusProgress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        self.percent_label.hide()

        layout.addLayout(text_row)
        layout.addWidget(self.progress_bar)

    def set_status(self, icon: QIcon, text: str, progress: int | None = None) -> None:
        if icon.isNull():
            self.icon_label.clear()
        else:
            self.icon_label.setPixmap(icon.pixmap(QSize(18, 18)))
        self.text_label.setText(text)
        if progress is None:
            self.progress_bar.hide()
            self.percent_label.hide()
            return
        value = max(0, min(100, int(progress)))
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")
        self.progress_bar.show()
        self.percent_label.show()
