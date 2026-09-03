from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.core.models import Student


class StudentSettingsDialog(QDialog):
    def __init__(self, student: Student, parent=None):
        super().__init__(parent)
        self.setWindowTitle("学习设置")
        self.setMinimumWidth(430)
        self.setModal(True)

        title = QLabel("调整你的学习目标")
        title.setObjectName("DialogTitle")
        description = QLabel("这些信息会用于生成更合适的练习建议。")
        description.setObjectName("MutedText")

        self.name_input = QLineEdit(student.name)
        self.name_input.setMaxLength(30)
        self.goal_input = QLineEdit(student.goal)
        self.goal_input.setMaxLength(120)
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(5, 180)
        self.minutes_input.setSuffix(" 分钟")
        self.minutes_input.setValue(student.practice_minutes)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)
        form.addRow("称呼", self.name_input)
        form.addRow("学习目标", self.goal_input)
        form.addRow("每日练习", self.minutes_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, int]:
        return (
            self.name_input.text().strip(),
            self.goal_input.text().strip(),
            self.minutes_input.value(),
        )

